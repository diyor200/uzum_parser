import time
import re
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError
from typing import Optional

BASE_URL = "https://uzum.uz"

def extract_num(text: str) -> Optional[int]:
    if isinstance(text, (int, float)):
        return int(text)
    if not isinstance(text, str):
        return None
    match = re.search(r'\d+', text.replace(' ', ''))
    return int(match.group(0)) if match else None

def parse_product(page, url: str):
    page.goto(url, wait_until="load")
    result = {}

    result["url"] = url
    result["title"] = page.locator("h1").inner_text().strip()

    try:
        price = page.locator('.TitleLBold.discount-price .currency.price').inner_text()
        result["with_uzum_card_price"] = extract_num(price)
    except Exception:
        result["with_uzum_card_price"] = None

    try:
        alt_price = page.locator('.BodyMRegular.payment-option .currency.alternative-price').inner_text()
        result["with_another_card_price"] = extract_num(alt_price)
    except Exception:
        result["with_another_card_price"] = None

    try:
        discount = page.locator('.TitleLBold.discount-price .BodySRegular.discount').inner_text().strip()
        result["discount"] = discount
    except Exception:
        result["discount"] = None

    try:
        rating = page.locator(".stats .rating .rating-value").inner_text().strip()
        result["rating"] = rating
    except Exception:
        result["rating"] = None

    # Sold count
    try:
        banners = page.locator('.banners .banner')
        banner_text = banners.nth(0).locator('[data-test-id="text__product-banner"]').inner_text().strip()
        result["available_count"] = extract_num(banner_text)
    except Exception:
        result["available_count"] = None

    # Images
    try:
        image_tags = page.locator("swiper-slide img")
        result["images"] = [
            img.get_attribute("src") for img in image_tags.all()
            if img.get_attribute("src") and not img.get_attribute("src").endswith(".svg")
        ]
    except Exception:
        result["images"] = []

    return result

def scrape_category_with_pagination(page, category_url):
    all_products = []
    current_page = 1

    while True:
        paginated_url = f"{category_url}?currentPage={current_page}"
        print(f"\n📄 Page {current_page}: {paginated_url}")
        page.goto(paginated_url)

        try:
            page.wait_for_selector('div#category-products', timeout=5000)
        except TimeoutError:
            print("❌ No product section found.")
            break

        # Check empty page
        try:
            page.wait_for_selector('div[data-test-id="block__empty-page"]', timeout=3000)
            print("⚠️ Reached end of products.")
            break
        except TimeoutError:
            pass

        product_cards = page.query_selector_all('div#category-products a[data-test-id="product-card--default"]')
        print(f"🛒 Found {len(product_cards)} products.")

        for card in product_cards:
            try:
                href = card.get_attribute("href")
                if href:
                    product_url = urljoin(BASE_URL, href)
                    print(f" → Parsing product: {product_url}")
                    detail = parse_product(page, product_url)
                    all_products.append(detail)
            except Exception as e:
                print("Error parsing product:", e)
                continue

        current_page += 1
        # For test purposes, stop early
        # if current_page > 2:
        #     break

    return all_products

def main():
    category_url = "https://uzum.uz/uz/category/elektronika-10020"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        products = scrape_category_with_pagination(page, category_url)

        print("\n🟢 Finished scraping.")
        for i, p in enumerate(products):
            print(f"\n[{i+1}] {p['title']}")
            print(p)

        browser.close()

if __name__ == "__main__":
    main()
