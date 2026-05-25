from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from playwright.async_api import BrowserContext, Page, Route, async_playwright

from database import DatabaseManager, SalonRecord, ServiceRecord

log = logging.getLogger(__name__)

LISTING_URL = "https://booksy.com/en-pl/s/salon-kosmetyczny/3_warszawa"
TARGET_COUNT = 3
NAV_TIMEOUT = 45_000
ELEMENT_TIMEOUT = 5_000
CONCURRENCY = 5
SALON_LINK_RE = re.compile(r"/en-pl/\d+_[^/#?]+")

WARSAW_DISTRICTS = {
    "Bemowo", "Białołęka", "Bielany", "Mokotów", "Ochota",
    "Praga-Południe", "Praga-Północ", "Rembertów", "Śródmieście",
    "Targówek", "Ursus", "Ursynów", "Wawer", "Wesoła",
    "Wilanów", "Włochy", "Wola", "Żoliborz",
}


async def run(db_manager: DatabaseManager) -> None:


    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-PL",
            viewport={"width": 1280, "height": 900},
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        salon_urls = await collect_salon_urls(context)
        log.info("Collected %d unique salon URLs to process.", len(salon_urls))

        semaphore = asyncio.Semaphore(CONCURRENCY)
        saved_count = db_manager.count_salons()

        for i in range(0, len(salon_urls), CONCURRENCY):
            if saved_count >= TARGET_COUNT:
                break
            batch = salon_urls[i : i + CONCURRENCY]
            tasks = [
                asyncio.create_task(scrape_and_save_salon(context, url, db_manager, semaphore, i + idx + 1))
                for idx, url in enumerate(batch)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if result is True:
                    saved_count += 1
                    log.info("Progress: %d/%d salons saved.", saved_count, TARGET_COUNT)

        log.info("Scraping complete. Total salons in DB: %d", db_manager.count_salons())
        await context.close()
        await browser.close()


async def collect_salon_urls(context: BrowserContext) -> list[str]:
    seen: dict[str, None] = {}
    page = await context.new_page()

    page_num = 1
    consecutive_empty = 0

    while len(seen) < TARGET_COUNT + 20:
        paginated_url = f"{LISTING_URL}?businessesPage={page_num}"
        log.info("Scanning page %d: %s", page_num, paginated_url)

        try:
            await page.goto(paginated_url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
            await page.locator("a[href*='/en-pl/']").first.wait_for(timeout=NAV_TIMEOUT)
            await page.wait_for_timeout(1_500)

            if page_num == 1:
                await dismiss_cookie_banner(page)

            hrefs = await page.locator("a[href]").evaluate_all(
                "els => els.map(el => el.getAttribute('href') || '')"
            )

            new_on_page = 0
            for href in hrefs:
                if not href:
                    continue
                full_url = href if href.startswith("http") else f"https://booksy.com{href}"
                canonical = full_url.split("#")[0]
                if SALON_LINK_RE.search(canonical) and "warszawa" in canonical.lower():
                    if canonical not in seen:
                        seen[canonical] = None
                        new_on_page += 1

            log.info("Page %d: %d new links found (total: %d).", page_num, new_on_page, len(seen))

            if new_on_page == 0:
                consecutive_empty += 1
            else:
                consecutive_empty = 0

            if consecutive_empty >= 2:
                log.info("Two consecutive pages with no new links — end of listing.")
                break

            page_num += 1

        except Exception as exc:
            log.warning("Failed to load listing page %d: %s", page_num, exc)
            consecutive_empty += 1
            if consecutive_empty >= 2:
                break
            page_num += 1

    await page.close()
    return list(seen)


async def scrape_and_save_salon(
    context: BrowserContext,
    url: str,
    db_manager: DatabaseManager,
    semaphore: asyncio.Semaphore,
    index: int = 1,
) -> bool:
    async with semaphore:
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
            await page.locator("h1").first.wait_for(timeout=NAV_TIMEOUT)

            await page.mouse.wheel(0, 800)
            await page.wait_for_timeout(1500)
            try:
                await page.wait_for_selector('div[data-testid="business-contact-info"]', timeout=10000)
            except Exception:
                pass

            html = await page.content()
            schema = parse_json_ld(html)
            if not schema:
                return False

            name = schema.get("name", "").strip()
            if not name:
                return False

            if db_manager.salon_exists(name):
                log.info("Skipping '%s' — already in database.", name)
                return False

            address_obj = schema.get("address", {})
            street = address_obj.get("streetAddress", "").strip()
            postal = address_obj.get("postalCode", "").strip()
            locality = address_obj.get("addressLocality", "Warszawa").split(",")[0].strip()
            if postal and postal in street:
                postal = ""
            if locality and (locality in street or locality.lower() in ("mazowieckie", "poland", "polska")):
                locality = ""
            full_address = ", ".join(part for part in [street, postal, locality] if part)
            district = infer_district(full_address)

            aggregate = schema.get("aggregateRating", {})
            rating = aggregate.get("ratingValue")
            review_count = aggregate.get("reviewCount")

            await page.screenshot(path=f"../debug_screenshot_{index}.png", full_page=True)
            phone = schema.get("telephone")
            if not phone:
                try:
                    phone_loc = page.get_by_test_id("business-contact-info-phone")
                    await phone_loc.wait_for(state="visible", timeout=5000)
                    raw_phone = await phone_loc.inner_text()
                    phone = " ".join(raw_phone.split())
                except Exception:
                    phone_match = re.search(r'"phone(?:Number)?"\s*:\s*"([^"]+)"', html)
                    if phone_match:
                        phone = " ".join(phone_match.group(1).split())
                    else:
                        phone = None

            website = await extract_website(schema, page)
            services = extract_services(schema)
            price_range = derive_price_range(services)

            record = SalonRecord(
                name=name,
                address=full_address,
                district=district,
                phone=phone,
                website=website,
                price_range=price_range,
                rating=float(rating) if rating is not None else None,
                review_count=int(review_count) if review_count is not None else None,
            )

            salon_id = db_manager.insert_salon(record)
            db_manager.insert_services(salon_id, services)
            log.info("Saved: '%s' (%s)", record.name, record.district)
            return True

        except Exception as exc:
            log.warning("Skipped %s — %s", url, exc)
            return False
        finally:
            await page.close()


def parse_json_ld(html: str) -> dict[str, Any] | None:
    blocks = re.findall(
        r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    )
    for block in blocks:
        try:
            data = json.loads(block.strip())
            if isinstance(data, dict):
                schema_type = data.get("@type", "")
                if schema_type in ("HairSalon", "BeautySalon", "LocalBusiness") or "Salon" in schema_type:
                    return data
        except Exception:
            continue
    return None


def extract_services(schema: dict[str, Any]) -> list[ServiceRecord]:
    services = []
    for offer in schema.get("makesOffer", []):
        if not isinstance(offer, dict) or offer.get("@type") != "Offer":
            continue
        name = offer.get("name", "").strip()
        price = offer.get("price")
        if name and price is not None:
            try:
                services.append(ServiceRecord(name=name, price=float(price)))
            except (ValueError, TypeError):
                continue
    return services


async def extract_website(schema: dict[str, Any], page: Page) -> str | None:
    for item in schema.get("sameAs", []):
        if isinstance(item, str) and not any(
            domain in item.lower()
            for domain in ("facebook.com", "instagram.com", "twitter.com", "youtube.com", "booksy.com")
        ):
            return item
    for sel in ["social-media-website-button", "social-media-instagram-button", "social-media-facebook-button"]:
        try:
            href = await page.get_by_test_id(sel).first.get_attribute("href", timeout=ELEMENT_TIMEOUT)
            if href:
                return href
        except Exception:
            continue
    return None


def infer_district(address: str) -> str:
    postal_re = re.compile(r"^\d{2}-\d{3}$")
    numeric_re = re.compile(r"^\d+$")
    noise = {"warsaw", "warszawa", "poland", "polska", "mazowieckie"}
    parts = [p.strip() for p in address.split(",")]
    meaningful = [
        p for p in parts
        if not postal_re.match(p)
        and not numeric_re.match(p)
        and p.lower() not in noise
    ]

    for part in meaningful:
        for district in WARSAW_DISTRICTS:
            if district.lower() in part.lower():
                return district

    if len(meaningful) >= 2:
        return meaningful[-2]
    if meaningful:
        return meaningful[0]
    return "Warsaw"


def derive_price_range(services: list[ServiceRecord]) -> str | None:
    prices = [s.price for s in services if s.price > 0]
    if not prices:
        return None
    avg = sum(prices) / len(prices)
    if avg < 80:
        return "$"
    if avg < 200:
        return "$$"
    return "$$$"


async def dismiss_cookie_banner(page: Page) -> None:
    selectors = [
        "#onetrust-accept-btn-handler",
        "button[id*='accept']",
        "#CybotCookiebotDialogBodyButtonAccept",
    ]
    for selector in selectors:
        try:
            button = page.locator(selector).first
            if await button.is_visible(timeout=3_000):
                await button.click()
                await page.wait_for_timeout(1_000)
                return
        except Exception:
            continue
