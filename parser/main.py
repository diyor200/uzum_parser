import json
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError

import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs

from utils import extract_num, to_safe_url, send_to_telegram

BASE_URL = "https://uzum.uz"
start_url = "https://uzum.uz/uz"
category_links = []


def wait_for_variant_update_by_selector(wrapper_selector, expected_label: str):
    for _ in range(30):  # Retry for ~3 seconds
        try:
            is_active = wrapper_selector.evaluate("el => el.classList.contains('active')")
            if is_active:
                return True
        except Exception as e:
            print("exception: ", e)
            pass
        time.sleep(0.1)
    raise TimeoutError(f"❌ Timeout waiting for characteristic '{expected_label}' to activate.")

def extract_price(page):
    # First try default selector
    selectors = [
        ".TitleLBold.discount-price .currency.price",
        '[data-test-id="text__product-price"]'
    ]
    for selector in selectors:
        try:
            price_loc = page.locator(selector)
            price_loc.wait_for(state="visible", timeout=2000)
            return extract_num(price_loc.inner_text())
        except:
            continue
    return None


def parse_product(url: str, ctx) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    variants: List[Dict[str, Any]] = []

    page = ctx.new_page()
    page.goto(to_safe_url(url), wait_until="load")

    def safe_inner_text(selector: str, default=None) -> Optional[str]:
        try:
            loc = page.locator(selector)
            if loc.count() == 0:
                return default
            loc.wait_for(state="visible", timeout=4000)
            return loc.inner_text().strip()
        except Exception as e:
            print(f"exception getting: {selector}", e)
            return default

    print("🔍 Parsing static product data...")
    result["title"] = safe_inner_text("h1", "N/A")
    result["with_uzum_card_price"] = extract_price(page)
    result["with_another_card_price"] = extract_num(
        safe_inner_text(".BodyMRegular.payment-option .currency.alternative-price"))
    result["discount"] = safe_inner_text(".TitleLBold.discount-price .BodySRegular.discount")
    result["rating"] = (safe_inner_text(".stats .rating .rating-value") or "")[:3]

    try:
        banner = page.locator('.banner [data-test-id="text__product-banner"]')
        result["sold_count"] = extract_num(banner.first.inner_text()) if banner.count() > 0 else 0
    except Exception as e:
        print("exception:", e)
        result["sold_count"] = None

    try:
        images = page.locator("swiper-slide img")
        result["images"] = [
            img.get_attribute("src")
            for img in images.all()
            if img.get_attribute("src") and not img.get_attribute("src").endswith(".svg") and img.get_attribute("src").startswith("https://static.uzum.uz")
        ]
    except Exception as e:
        print("exception:", e)
        result["images"] = []

    try:
        seller = page.locator(".seller .info")
        seller.scroll_into_view_if_needed()
        seller.wait_for(state="visible", timeout=8000)
        result["seller"] = {
            "title": seller.locator(".info-container h3").inner_text().strip(),
            "img": seller.locator("img").get_attribute("src"),
            "rating": seller.locator('[data-test-id="text__shop-rating-value"]').inner_text().strip()
        }
    except Exception as e:
        print("exception:", e)
        result["seller"] = {}

    print("\n🔁 Parsing variant options (text and image)...")
    variant_items_text = page.locator('div[data-test-id="text_characteristic"]')
    variant_items_image = page.locator('div[data-test-id="image_characteristic"]')
    variant_items = [("text", variant_items_text.nth(i)) for i in range(variant_items_text.count())] + \
                    [("image", variant_items_image.nth(i)) for i in range(variant_items_image.count())]

    current_selected = safe_inner_text('[data-test-id="text__selected-sku-value"]', "")

    for index, (variant_type, el) in enumerate(variant_items):
        try:
            if variant_type == "text":
                label = el.locator("span.text").inner_text().strip()
                wrapper = el.locator('.radio-text-wrapper')
            else:
                label = el.locator("img").get_attribute("alt") or "image-option"
                wrapper = el.locator('.radio-image-wrapper')

            wrapper_class = wrapper.get_attribute("class") or ""
            is_disabled = "disabled" in wrapper_class

            if is_disabled is not None and is_disabled:
                print(f"🚫 Sold out: {label}")
                variants.append({
                    "characteristic_type": variant_type,
                    "characteristic_text": label,
                    "sku_id": None,
                    "selected_value_from_ui": label,
                    "price_with_uzum_card": None,
                    "available_count": 0,
                })
                continue

            is_active = wrapper.evaluate("el => el.classList.contains('active')")

            if index == 0:
                print(f"✔ Already selected: {label}")
            elif not is_active or label != current_selected:
                print(f"👉 Clicking: {label}")
                el.scroll_into_view_if_needed()
                el.click(force=True)
                wait_for_variant_update_by_selector(wrapper, label)
            else:
                print(f"✔ Already selected: {label}")

            parsed = parse_qs(urlparse(page.url).query)
            sku_id = int(parsed["skuId"][0]) if "skuId" in parsed else None

            available = None
            price = None
            if not is_disabled:
                price = extract_num(safe_inner_text(".TitleLBold.discount-price .currency.price") or safe_inner_text('[data-test-id="text__product-price"]'))

                try:
                    banners = page.locator('.banners .banner')
                    banner_text = banners.nth(0).locator('[data-test-id="text__product-banner"]').inner_text().strip()
                    available = extract_num(banner_text)
                except Exception as e:
                    print("exception:", e)


            selected_ui_value = safe_inner_text('[data-test-id="text__selected-sku-value"]')

            variants.append({
                "characteristic_type": variant_type,
                "characteristic_text": label,
                "sku_id": sku_id,
                "selected_value_from_ui": selected_ui_value,
                "price_with_uzum_card": price,
                "available_count": available,
            })

            print(f"✅ {label}: price={price}, available={available}, sku={sku_id}")

        except Exception as e:
            print(f"❌ Error on option {index} ({variant_type}):", e)
            continue

    result["products_by_characteristic"] = variants
    page.close()
    return result

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)

        context = browser.new_context()
        page = context.new_page()
        page.goto(start_url)

        page.wait_for_selector("div.bottom-header-wrapper")

        # Get all category <li> elements
        category_items = page.query_selector_all("div.bottom-header ul.categories li.category")

        for i in range(len(category_items)):
            try:
                category_items = page.query_selector_all("div.bottom-header ul.categories li.category")
                item = category_items[i]
                a = item.query_selector("a")
                if a:
                    href = a.get_attribute("href")
                    if href:
                        full_url = urljoin(BASE_URL, href)
                        category_links.append(full_url)
                        print(f"\n[{i+1}] Scraping category: {full_url}")
                        scrape_category_with_pagination(page, full_url, context)
                        break
            except Exception as e:
                print("Error clicking category:", e)

        browser.close()

def scrape_category_with_pagination(page, category_url, ctx):
    products = []
    current_page = 1
    adult_button = False

    print("beginning parsing products ...")
    while True:
        if current_page == 2:
            break

        paginated_url = f"{category_url}?currentPage={current_page}"
        print(f" → Page {current_page}: {paginated_url}")
        page.goto(paginated_url, wait_until="load")
        print("page fully loaded!")
        # Check for the "no products" block
        try:
            page.wait_for_selector('div[data-test-id="block__empty-page"]', timeout=3000)
            print(" ⚠️ No more products on this page. Ending pagination.")
            break
        except TimeoutError:
            pass  # No empty block, continue

        # Handle optional notification
        if not adult_button:
            try:
                button = page.query_selector("#notification button.ui-button.solid--red")
                if button:
                    print("Clicking notification close button...")
                    button.click()
                    adult_button = True
                    continue
            except Exception as e:
                print("Notification button error:", e)

        # Extract product cards
        try:
            page.wait_for_selector(selector='div#category-products a[data-test-id="product-card--default"]', timeout=3000)
        except Exception as e:
            print("exception: ", e)

        product_cards = page.query_selector_all('div#category-products a[data-test-id="product-card--default"]')
        print(f"🛒 Found {len(product_cards)} products.")

        for i, card in enumerate(product_cards):
            try:
                href = card.get_attribute("href")
                if href:
                    product_url = urljoin(BASE_URL, href)
                    # print()(f" → Parsing product: {product_url}")
                    detail = parse_product(url=product_url, ctx=ctx)
                    products.append({i+1: detail})
            except Exception as e:
                print("Error parsing product:", e)
                continue

            if i == 4:
                break

        current_page += 1
        time.sleep(1)

    with open("product.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)


    send_to_telegram()

if __name__ == "__main__":
    main()
