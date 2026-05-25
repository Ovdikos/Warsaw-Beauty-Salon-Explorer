from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from playwright.async_api import BrowserContext, Page, Route, async_playwright

from database import DatabaseManager, SalonRecord, ServiceRecord

log = logging.getLogger(__name__)

# Constants logically grouped at the top
LISTING_URL = "https://booksy.com/en-pl/s/salon-kosmetyczny/3_warszawa"
TARGET_COUNT = 100
MAX_CONCURRENT_PAGES = 5
NAV_TIMEOUT = 45_000
ELEMENT_TIMEOUT = 5_000
SALON_LINK_RE = re.compile(r"/en-pl/\d+_[^/#?]+")
BLOCKED_RESOURCES = {"image", "media", "font"}
WARSAW_DISTRICTS = {
    "Bemowo", "Białołęka", "Bielany", "Mokotów", "Ochota",
    "Praga-Południe", "Praga-Północ", "Rembertów", "Śródmieście",
    "Targówek", "Ursus", "Ursynów", "Wawer", "Wesoła",
    "Wilanów", "Włochy", "Wola", "Żoliborz",
}


async def run(db_manager: DatabaseManager) -> None:
    """Initialize Playwright and coordinate the scraping process."""
    if db_manager.count_salons() >= TARGET_COUNT:
        return

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

        # Limit concurrency to 5 to avoid overwhelming the system
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_PAGES)
        saved_count = db_manager.count_salons()

        for i in range(0, len(salon_urls), MAX_CONCURRENT_PAGES):
            if saved_count >= TARGET_COUNT:
                break
            batch = salon_urls[i : i + MAX_CONCURRENT_PAGES]
            tasks = [
                asyncio.create_task(scrape_and_save_salon(context, url, db_manager, semaphore))
                for url in batch
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
    """Iterate through the paginated listing URL to gather salon detail links."""
    seen: dict[str, None] = {}
    page = await context.new_page()
    await block_unnecessary_resources(page)

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
) -> bool:
    """Extract individual salon details and save them to the database."""
    async with semaphore:
        page = await context.new_page()
        await block_unnecessary_resources(page)
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT)
            await page.locator("h1").first.wait_for(timeout=NAV_TIMEOUT)

            await page.mouse.wheel(0, 800)
            await page.wait_for_timeout(1500)

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

            website = await extract_website(schema, page)
            services = await extract_services(schema, page)
            price_range = derive_price_range(services)

            record = SalonRecord(
                name=name,
                address=full_address,
                district=district,
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


async def block_unnecessary_resources(page: Page) -> None:
    """Abort requests for media and styling assets to minimize payload."""
    async def handle_route(route: Route) -> None:
        # Block images and fonts to speed up the scraper
        if route.request.resource_type in BLOCKED_RESOURCES:
            await route.abort()
        else:
            await route.continue_()

    await page.route("**/*", handle_route)


def parse_json_ld(html: str) -> dict[str, Any] | None:
    """Extract and parse the JSON-LD schema from the raw HTML content."""
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


def _find_services_in_nuxt(data: Any, services: list[ServiceRecord]) -> None:
    """Recursively traverse the Nuxt dictionary state to find service records."""
    if isinstance(data, dict):
        name = data.get("name")
        price = data.get("price")
        if isinstance(name, str) and isinstance(price, (int, float)):
            if len(name) > 3 and price > 0:
                services.append(ServiceRecord(name=name.strip(), price=float(price)))
        for value in data.values():
            _find_services_in_nuxt(value, services)
    elif isinstance(data, list):
        for item in data:
            _find_services_in_nuxt(item, services)


async def extract_services(schema: dict[str, Any], page: Page) -> list[ServiceRecord]:
    """Extract salon services from JSON-LD or fallback to the injected Nuxt state."""
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

    if not services:
        try:
            # Extract Nuxt state directly via JS evaluation for stability
            nuxt_state = await page.evaluate("() => window.__NUXT__")
            if nuxt_state:
                _find_services_in_nuxt(nuxt_state, services)
        except Exception:
            pass

    return services


async def extract_website(schema: dict[str, Any], page: Page) -> str | None:
    """Extract the salon's primary website or social media URL."""
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
    """Identify the Warsaw district based on the address string."""
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
    """Calculate the overall price range string based on average service price."""
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
    """Attempt to clear common cookie consent banners from the UI."""
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
