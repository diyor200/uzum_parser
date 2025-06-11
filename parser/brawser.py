from playwright.sync_api import sync_playwright

from helpers import extract_num


def get_info_by_size(url: str) -> list:
    from playwright.sync_api import sync_playwright
    res = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Opening browser...")
        page.goto(url)
        page.wait_for_selector('.sku-radio-text')

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
    return res
