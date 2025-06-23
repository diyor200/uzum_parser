import re
from playwright.sync_api import sync_playwright, Page, Locator
from typing import Dict, List, Optional, Any

# Assuming helpers.py exists and extract_num is defined there
# For demonstration, I'll include a simple extract_num if you don't have helpers.py

import re
import json
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, parse_qs

# Fallback extract_num if helpers.py isn't used
def extract_num(text: str) -> Optional[int]:
    if isinstance(text, (int, float)):
        return int(text)
    if not isinstance(text, str):
        return None
    match = re.search(r'\d+', text.replace(' ', ''))
    return int(match.group(0)) if match else None

def to_safe_url(url: str) -> str:
    parsed = urlparse(url)
    parts = parsed.path.split("/")
    if "product" in parts:
        product_part = parts[-1]
        if "-" in product_part:
            product_id = product_part.split("-")[-1]
        else:
            product_id = product_part
        query = parsed.query
        return f"https://uzum.uz/uz/product/{product_id}?{query}" if query else f"https://uzum.uz/uz/product/{product_id}"
    return url

def wait_for_variant_update_by_selector(wrapper_selector, expected_label: str):
    for _ in range(30):  # Retry for ~3 seconds
        try:
            is_active = wrapper_selector.evaluate("el => el.classList.contains('active')")
            if is_active:
                return True
        except:
            pass
        time.sleep(0.1)
    raise TimeoutError(f"❌ Timeout waiting for characteristic '{expected_label}' to activate.")

def parse_product(page, url: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    variants: List[Dict[str, Any]] = []
    page.goto(to_safe_url(url), wait_until="load")

    def safe_inner_text(selector: str, default=None) -> Optional[str]:
        try:
            loc = page.locator(selector)
            loc.wait_for(state="visible", timeout=8000)
            return loc.inner_text().strip()
        except:
            return default

    print("🔍 Parsing static product data...")
    result["title"] = safe_inner_text("h1", "N/A")
    result["with_uzum_card_price"] = extract_num(safe_inner_text(".TitleLBold.discount-price .currency.price"))
    result["with_another_card_price"] = extract_num(safe_inner_text(".BodyMRegular.payment-option .currency.alternative-price"))
    result["discount"] = safe_inner_text(".TitleLBold.discount-price .BodySRegular.discount")
    result["rating"] = (safe_inner_text(".stats .rating .rating-value") or "")[:3]

    try:
        banner = page.locator('.banner [data-test-id="text__product-banner"]')
        result["sold_count"] = extract_num(banner.first.inner_text()) if banner.count() > 0 else 0
    except:
        result["sold_count"] = None

    try:
        images = page.locator("swiper-slide img")
        result["images"] = [
            img.get_attribute("src")
            for img in images.all()
            if img.get_attribute("src") and not img.get_attribute("src").endswith(".svg")
        ]
    except:
        result["images"] = []

    try:
        seller = page.locator(".seller .info")
        seller.wait_for(state="visible", timeout=8000)
        result["seller"] = {
            "title": seller.locator(".info-container h3").inner_text().strip(),
            "img": seller.locator("img").get_attribute("src"),
            "rating": seller.locator('[data-test-id="text__shop-rating-value"]').inner_text().strip()
        }
    except:
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

            is_active = wrapper.evaluate("el => el.classList.contains('active')")

            if index == 0:
                print(f"✔ Already selected: {label}")
            elif not is_active or label != current_selected:
                print(f"👉 Clicking: {label}")
                el.scroll_into_view_if_needed()
                el.click(timeout=8000, force=True)
                wait_for_variant_update_by_selector(wrapper, label)
            else:
                print(f"✔ Already selected: {label}")

            parsed = parse_qs(urlparse(page.url).query)
            sku_id = int(parsed["skuId"][0]) if "skuId" in parsed else None

            price = extract_num(safe_inner_text(".TitleLBold.discount-price .currency.price"))

            try:
                banners = page.locator('.banners .banner')
                banner_text = banners.nth(0).locator('[data-test-id="text__product-banner"]').inner_text().strip()
                available = extract_num(banner_text)
            except:
                available = None

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
            print(f"❌ Error on option {index} ({variant_type}): {e}")
            continue

    result["products_by_characteristic"] = variants
    return result

if __name__ == "__main__":
    data = parse_product(None, url="https://uzum.uz/uz/product/1641058")
    with open("product.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n--- Final Parsed Data ---")
    print(json.dumps(data, indent=2, ensure_ascii=False))
