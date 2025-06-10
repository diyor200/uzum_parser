from playwright.sync_api import sync_playwright

from helpers import extract_num


def get_info_by_size() -> list:
    res = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=100)
        page = browser.new_page()
        page.goto("https://uzum.uz/uz/product/new-balance-erkaklar-krossovkalari-1552187?skuId=5109824")

        # Wait for sizes to load
        page.wait_for_selector('.sku-radio-text')
        size_elements = page.locator('.sku-radio-text')
        size_count = size_elements.count()

        # Loop through each size
        for i in range(size_count):
            size_el = size_elements.nth(i)
            size_text = size_el.locator('span').inner_text().strip()

            size_el.scroll_into_view_if_needed()
            size_el.click(timeout=5000)
            page.wait_for_timeout(2000)

            # Get banner data for this size
            banners = page.locator('.banners .banner')
            banner_count = banners.count()

            data = {
                "size": size_text,
                "available_count": extract_num(
                    banners.nth(0).locator('[data-test-id="text__product-banner"]').inner_text().strip()
                )
            }
            res.append(data)
        browser.close()

    return res