
import json
import asyncio
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse, parse_qs

from playwright.async_api import async_playwright, TimeoutError

from utils import extract_num, to_safe_url

BASE_URL = "https://uzum.uz"
START_URL = "https://uzum.uz/uz"
MAX_CONCURRENT_TABS = 10
OUTPUT_FILE = "all_products.json"

semaphore = asyncio.Semaphore(MAX_CONCURRENT_TABS)
all_products: List[Dict[str, Any]] = []

async def get_inner_text_safe(locator, default=None):
    try:
        await locator.wait_for(state="visible", timeout=3000)
        return (await locator.inner_text()).strip()
    except:
        return default

async def get_attribute_safe(locator, attr: str):
    try:
        return await locator.get_attribute(attr)
    except:
        return None

async def extract_price(page) -> int:
    selectors = [
        ".TitleLBold.discount-price .currency.price",
        '[data-test-id="text__product-price"]'
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel)
            await loc.wait_for(state="visible", timeout=2000)
            return extract_num(await loc.inner_text())
        except:
            continue
    return None

async def parse_product(ctx, url: str) -> Dict[str, Any]:
    async with semaphore:
        page = await ctx.new_page()
        await page.goto(to_safe_url(url), wait_until="load")
        result: Dict[str, Any] = {"url": url}

        result["title"] = await get_inner_text_safe(page.locator("h1"), "N/A")
        result["with_uzum_card_price"] = await extract_price(page)
        result["with_another_card_price"] = extract_num(
            await get_inner_text_safe(page.locator(".BodyMRegular.payment-option .currency.alternative-price"))
        )
        result["rating"] = (await get_inner_text_safe(page.locator(".stats .rating .rating-value")) or "")[:3]

        try:
            banner = page.locator('.banner [data-test-id="text__product-banner"]')
            result["sold_count"] = extract_num(await banner.first.inner_text()) if await banner.count() > 0 else 0
        except:
            result["sold_count"] = None

        try:
            images = page.locator("swiper-slide img")
            result["images"] = [
                await get_attribute_safe(img, "src")
                for img in await images.all()
                if (await get_attribute_safe(img, "src") or "").startswith("https://static.uzum.uz")
            ]
        except:
            result["images"] = []

        await page.close()
        return result

async def parse_category_products(ctx, category_url: str):
    page = await ctx.new_page()
    current_page = 1
    while True:
        paginated_url = f"{category_url}?currentPage={current_page}"
        print(f"🔄 Page {current_page}: {paginated_url}")
        await page.goto(paginated_url, wait_until="load")

        try:
            await page.wait_for_selector('div[data-test-id="block__empty-page"]', timeout=3000)
            print("⚠️ No more products.")
            break
        except TimeoutError:
            pass

        try:
            await page.wait_for_selector('div#category-products a[data-test-id="product-card--default"]', timeout=3000)
        except:
            break

        cards = await page.query_selector_all('div#category-products a[data-test-id="product-card--default"]')
        product_urls = []
        for card in cards:
            href = await card.get_attribute("href")
            if href:
                full_url = urljoin(BASE_URL, href)
                product_urls.append(full_url)

        results = await asyncio.gather(*[parse_product(ctx, url) for url in product_urls])
        all_products.extend(results)

        current_page += 1
        if current_page > 3:
            break

    await page.close()

async def get_all_category_urls(ctx) -> List[str]:
    page = await ctx.new_page()
    await page.goto(START_URL)
    await page.wait_for_selector("div.bottom-header-wrapper")

    category_items = await page.query_selector_all("div.bottom-header ul.categories li.category a")
    urls = []
    for item in category_items:
        href = await item.get_attribute("href")
        if href:
            urls.append(urljoin(BASE_URL, href))
    await page.close()
    return urls

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context()

        category_urls = await get_all_category_urls(context)
        print(f"🔗 Found {len(category_urls)} categories.")

        category_urls = [category_urls[0]]
        for i, cat_url in enumerate(category_urls):
            print(f"📁 Category {i + 1}/{len(category_urls)}: {cat_url}")
            await parse_category_products(context, cat_url)


        await browser.close()

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_products, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved {len(all_products)} products to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
