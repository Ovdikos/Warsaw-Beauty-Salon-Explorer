from __future__ import annotations

import asyncio
import json
import logging
import re
import threading
from dataclasses import dataclass, field
from typing import Any, Final

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from database import DatabaseManager, SalonRecord, ServiceRecord

log: logging.Logger = logging.getLogger(__name__)

_TARGET_COUNT: Final[int] = 100
_SCROLL_PAUSE_MS: Final[int] = 2_000
_NAV_TIMEOUT_MS: Final[int] = 45_000
_ELEMENT_TIMEOUT_MS: Final[int] = 5_000
_CONCURRENCY: Final[int] = 3

_BOOKSY_WARSAW_CATEGORIES: Final[tuple[str, ...]] = (
    "https://booksy.com/en-pl/s/fryzjer/3_warszawa",
    "https://booksy.com/en-pl/s/salon-kosmetyczny/3_warszawa",
    "https://booksy.com/en-pl/s/paznokcie/3_warszawa",
    "https://booksy.com/en-pl/s/brwi-i-rzesy/3_warszawa",
    "https://booksy.com/en-pl/s/barber-shop/3_warszawa",
    "https://booksy.com/en-pl/s/masaz/3_warszawa",
    "https://booksy.com/en-pl/s/depilacja/3_warszawa",
    "https://booksy.com/en-pl/s/fizjoterapia/3_warszawa",
    "https://booksy.com/en-pl/s/medycyna-estetyczna/3_warszawa",
    "https://booksy.com/en-pl/s/makijaz/3_warszawa",
    "https://booksy.com/en-pl/s/spa-i-wellness/3_warszawa",
    "https://booksy.com/en-pl/s/tatuaz-i-piercing/3_warszawa",
)

_STEALTH_USER_AGENT: Final[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_COOKIE_ACCEPT_SELECTORS: Final[tuple[str, ...]] = (
    "#onetrust-accept-btn-handler",
    "button[id*='accept']",
    "button[class*='accept']",
    "#CybotCookiebotDialogBodyButtonAccept",
)

_PRICE_TIERS: Final[tuple[tuple[float, str], ...]] = (
    (80.0,          "$"),
    (200.0,         "$$"),
    (float("inf"),  "$$$"),
)

_SALON_LINK_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"/en-pl/\d+_[^/#?]+"
)

_WARSAW_DISTRICTS: Final[frozenset[str]] = frozenset({
    "Bemowo", "Białołęka", "Bielany", "Mokotów", "Ochota",
    "Praga-Południe", "Praga-Północ", "Rembertów", "Śródmieście",
    "Targówek", "Ursus", "Ursynów", "Wawer", "Wesoła",
    "Wilanów", "Włochy", "Wola", "Żoliborz",
})


class ScrapingAbortedError(RuntimeError):
    pass


@dataclass(slots=True)
class BooksyScraper:
    db_manager: DatabaseManager
    categories: tuple[str, ...] = field(default=_BOOKSY_WARSAW_CATEGORIES)
    _db_lock: threading.Lock = field(init=False, default_factory=threading.Lock)

    async def run(self) -> None:
        async with async_playwright() as playwright:
            browser = await self._launch_stealth_browser(playwright)
            context = await self._create_hardened_context(browser)
            try:
                await self._orchestrate_scraping(context)
            finally:
                await context.close()
                await browser.close()

    async def _orchestrate_scraping(self, context: BrowserContext) -> None:
        search_page = await context.new_page()
        all_salon_links: dict[str, None] = {}

        for category_url in self.categories:
            log.info("Collecting links from category page: %s", category_url)
            try:
                await search_page.goto(category_url, timeout=_NAV_TIMEOUT_MS, wait_until="domcontentloaded")
                await search_page.locator("a[href*='/en-pl/']").first.wait_for(timeout=_NAV_TIMEOUT_MS)
                await self._dismiss_cookie_banner(search_page)
                
                for _ in range(3):
                    await self._scroll_and_wait(search_page)
                
                found_links = await self._extract_salon_links(search_page)
                log.info("Found %d Warsaw salon links in this category.", len(found_links))
                for link in found_links:
                    all_salon_links[link] = None
                    
            except Exception as exc:
                log.warning("Failed to collect links from category %s: %s", category_url, exc)
                continue

        log.info("Total unique Warsaw salon links discovered: %d", len(all_salon_links))
        await search_page.close()

        collected_count: int = 0
        semaphore = asyncio.Semaphore(_CONCURRENCY)
        
        active_tasks = [
            asyncio.create_task(self._process_single_salon(context, url, semaphore))
            for url in all_salon_links.keys()
        ]

        try:
            for completed_task in asyncio.as_completed(active_tasks):
                try:
                    result = await completed_task
                    collected_count += result
                    if collected_count >= _TARGET_COUNT:
                        log.info("Reached target collection count of %d salons.", _TARGET_COUNT)
                        break
                except Exception as exc:
                    log.warning("Task execution error: %s", exc)
        finally:
            for t in active_tasks:
                if not t.done():
                    t.cancel()
            if active_tasks:
                await asyncio.gather(*active_tasks, return_exceptions=True)

        log.info("Orchestration finished. Total salons persisted: %d.", collected_count)

    async def _process_single_salon(
        self, context: BrowserContext, url: str, semaphore: asyncio.Semaphore
    ) -> int:
        async with semaphore:
            detail_page = await context.new_page()
            try:
                await detail_page.goto(url, timeout=_NAV_TIMEOUT_MS, wait_until="domcontentloaded")
                await detail_page.locator("h1").first.wait_for(timeout=_NAV_TIMEOUT_MS)
                
                html = await detail_page.content()
                schema_data = self._parse_json_ld_schema(html)
                if not schema_data:
                    return 0

                name = schema_data.get("name")
                if not name:
                    return 0

                address_dict = schema_data.get("address", {})
                street_address = address_dict.get("streetAddress", "Warsaw")
                resolved_address = street_address.strip()
                
                aggregate_rating = schema_data.get("aggregateRating", {})
                rating = aggregate_rating.get("ratingValue")
                review_count = aggregate_rating.get("reviewCount")

                phone = schema_data.get("telephone")
                if not phone:
                    phone_href = await self._safe_attribute(detail_page, "a[href^='tel:']", "href")
                    if phone_href:
                        phone = phone_href.removeprefix("tel:").strip()

                website = None
                same_as_list = schema_data.get("sameAs", [])
                for item in same_as_list:
                    if isinstance(item, str) and not any(
                        domain in item.lower()
                        for domain in ("facebook.com", "instagram.com", "twitter.com", "youtube.com", "booksy.com")
                    ):
                        website = item
                        break

                if not website:
                    website = await self._safe_attribute(detail_page, "a[data-testid='website-link']", "href")

                services = self._extract_services_from_schema(schema_data)
                price_range = self._derive_price_range(services)

                persisted_record = SalonRecord(
                    name=name.strip(),
                    address=resolved_address,
                    district=self._infer_district(resolved_address),
                    phone=phone,
                    website=website,
                    price_range=price_range,
                    rating=float(rating) if rating is not None else None,
                    review_count=int(review_count) if review_count is not None else None,
                )

                with self._db_lock:
                    salon_id = self.db_manager.insert_salon(persisted_record)
                    self.db_manager.insert_services(salon_id, services)

                log.info("Successfully persisted: '%s' in %s", persisted_record.name, persisted_record.district)
                return 1
            except Exception as exc:
                log.warning("Failed to process %s: %s", url, exc)
                return 0
            finally:
                await detail_page.close()

    async def _extract_salon_links(self, page: Page) -> list[str]:
        anchors = page.locator("a[href]")
        raw_hrefs: list[str] = await anchors.evaluate_all(
            "els => els.map(el => el.getAttribute('href') || '')"
        )
        unique_salon_urls: dict[str, None] = {}
        for href in raw_hrefs:
            if not href:
                continue
            absolute = href if href.startswith("http") else f"https://booksy.com{href}"
            if _SALON_LINK_PATTERN.search(absolute) and "warszawa" in absolute.lower():
                unique_salon_urls[absolute] = None
        return list(unique_salon_urls)

    @staticmethod
    def _parse_json_ld_schema(html: str) -> dict[str, Any] | None:
        ld_json_scripts = re.findall(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        )
        for script_content in ld_json_scripts:
            try:
                data = json.loads(script_content.strip())
                if isinstance(data, dict):
                    schema_type = data.get("@type", "")
                    if schema_type in ("HairSalon", "BeautySalon", "LocalBusiness") or "Salon" in schema_type:
                        return data
            except Exception:
                continue
        return None

    @staticmethod
    def _extract_services_from_schema(schema_data: dict[str, Any]) -> list[ServiceRecord]:
        services: list[ServiceRecord] = []
        offers = schema_data.get("makesOffer", [])
        if isinstance(offers, list):
            for offer in offers:
                if isinstance(offer, dict) and offer.get("@type") == "Offer":
                    name = offer.get("name")
                    price = offer.get("price")
                    if name and price is not None:
                        try:
                            services.append(ServiceRecord(name=name.strip(), price=float(price)))
                        except ValueError:
                            continue
        return services

    @staticmethod
    def _infer_district(address: str) -> str:
        postal_pattern = re.compile(r"^\d{2}-\d{3}$")
        noise_words = frozenset({"warsaw", "warszawa", "poland", "polska"})
        parts = [segment.strip() for segment in address.split(",")]
        meaningful_parts = [
            part for part in parts
            if not postal_pattern.match(part) and part.lower() not in noise_words
        ]

        for part in meaningful_parts:
            for district in _WARSAW_DISTRICTS:
                if district.lower() in part.lower():
                    return district

        match meaningful_parts:
            case [*_, penultimate, _]:
                return penultimate
            case [single]:
                return single
            case _:
                return "Warsaw"

    @staticmethod
    def _derive_price_range(services: list[ServiceRecord]) -> str | None:
        priced_values = [svc.price for svc in services if svc.price > 0.0]
        if not priced_values:
            return None
        average_price = sum(priced_values) / len(priced_values)
        return next(tier for threshold, tier in _PRICE_TIERS if average_price < threshold)

    @staticmethod
    async def _safe_attribute(page: Page, selector: str, attribute: str) -> str | None:
        try:
            return await page.locator(selector).first.get_attribute(attribute, timeout=_ELEMENT_TIMEOUT_MS)
        except Exception:
            return None

    @staticmethod
    async def _dismiss_cookie_banner(page: Page) -> None:
        for selector in _COOKIE_ACCEPT_SELECTORS:
            try:
                button = page.locator(selector).first
                if await button.is_visible(timeout=3_000):
                    await button.click()
                    await page.wait_for_timeout(1_000)
                    return
            except Exception:
                continue

    @staticmethod
    async def _scroll_and_wait(page: Page) -> None:
        previous_height: int = await page.evaluate("document.body.scrollHeight")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(_SCROLL_PAUSE_MS)
        new_height: int = await page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            await page.wait_for_timeout(_SCROLL_PAUSE_MS)

    @staticmethod
    async def _launch_stealth_browser(playwright: Playwright) -> Browser:
        return await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )

    @staticmethod
    async def _create_hardened_context(browser: Browser) -> BrowserContext:
        context = await browser.new_context(
            user_agent=_STEALTH_USER_AGENT,
            locale="en-PL",
            viewport={"width": 1280, "height": 900},
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return context
