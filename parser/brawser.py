import re

from playwright.sync_api import sync_playwright

from helpers import extract_num


def parse(url: str) -> dict:
    res = []
    result = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Opening browser...")
        page.goto(url)
        page.wait_for_timeout(5000)

        # parse static data
        page.wait_for_selector("h1")
        result["title"] = page.locator("h1").inner_text().strip()

        page.wait_for_selector('.TitleLBold.discount-price .currency.price', timeout=10000)
        price = page.locator('.TitleLBold.discount-price .currency.price').inner_text()
        result["price"] = re.sub(r'\s+', '', price)

        # Wait and get discount
        discount = page.locator('.TitleLBold.discount-price .BodySRegular.discount').inner_text()
        result["discount"] = discount.strip()


        rating = page.locator(".stats .rating .rating-value").inner_text()
        result["rating"] = rating.strip()[:3]

        banners = page.locator(".banner")
        banner_count = banners.count()
        for i in range(1, banner_count):  # skip first if needed
            text = banners.nth(i).locator('[data-test-id="text__product-banner"]').inner_text().strip()
            result["sold_count"] = extract_num(text)

        images = page.locator("swiper-slide img")
        img_links = [img.get_attribute("src") for img in images.all()]
        result["images"] = img_links

        seller_section = page.locator(".seller .info")
        result["seller"] = {
            "title": seller_section.locator(".info-container h3").inner_text().strip(),
            "img": seller_section.locator("img").get_attribute("src"),
            "rating": seller_section.locator('[data-test-id="text__shop-rating-value"]').inner_text().strip()
        }

        size_elements = page.locator('.sku-radio-text')
        size_count = size_elements.count()
        print(f"Found {size_count} sizes")

        for i in range(size_count):
            try:
                size_el = size_elements.nth(i)
                size_text = size_el.locator('span').inner_text().strip()

                size_el.scroll_into_view_if_needed()
                size_el.click(timeout=5000, force=True)
                page.wait_for_selector('.banners .banner')

                banners = page.locator('.banners .banner')
                banner_text = banners.nth(0).locator('[data-test-id="text__product-banner"]').inner_text().strip()

                data = {
                    "size": size_text,
                    "available_count": extract_num(banner_text)
                }
                res.append(data)

            except Exception as e:
                print(f"Error on size {i}: {e}")

        browser.close()

    result["products"] = res
    return result

