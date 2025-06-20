# import time
# from playwright.sync_api import sync_playwright, TimeoutError
#
# url = "https://uzum.uz/uz"
# category_links = []
#
# def main():
#     with sync_playwright() as pw:
#         browser = pw.chromium.launch(headless=False, slow_mo=100)
#         page = browser.new_page()
#         page.goto(url)
#
#         page.wait_for_selector("div.bottom-header-wrapper")
#
#         # Find all category elements
#         category_items = page.query_selector_all("div.bottom-header ul.categories li.category")
#
#         for i in range(len(category_items)):
#             try:
#                 # Re-fetch elements inside the loop to avoid stale element references
#                 category_items = page.query_selector_all("div.bottom-header ul.categories li.category")
#                 item = category_items[i]
#
#                 # Get link
#                 a = item.query_selector("a")
#                 if a:
#                     href = a.get_attribute("href")
#                     if href:
#                         category_links.append(href)
#
#                 print(f"[{i+1}] Clicking category: ", item.inner_text())
#                 item.click()
#
#                 # Wait for product block
#                 try:
#                     page.wait_for_selector("div#category-products", timeout=5000)
#                 except TimeoutError:
#                     print("category-products not found")
#
#                 # Handle optional notification
#                 try:
#                     button = page.query_selector("#notification button.ui-button.solid--red")
#                     if button:
#                         print("Clicking notification close button...")
#                         button.click()
#                 except Exception as e:
#                     print("Notification button error:", e)
#
#                 time.sleep(2)
#
#             except Exception as e:
#                 print(f"Error in category {i+1}:", e)
#
#         print("Collected category links:")
#         print(category_links)
#
#         browser.close()
#
# if __name__ == "__main__":
#     main()
import time
from itertools import product
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright, TimeoutError

base_url = "https://uzum.uz"
start_url = "https://uzum.uz/uz"
category_links = []

def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()
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
                        full_url = urljoin(base_url, href)
                        category_links.append(full_url)
                        print(f"\n[{i+1}] Scraping category: {full_url}")
                        scrape_category_with_pagination(page, full_url)
                        break
            except Exception as e:
                print("Error clicking category:", e)

        print("\nAll category links:")
        for link in category_links:
            print(link)

        browser.close()

def scrape_category_with_pagination(page, category_url):
    products = []
    current_page = 1
    while True:
        paginated_url = f"{category_url}?currentPage={current_page}"
        print(f" → Page {current_page}: {paginated_url}")
        page.goto(paginated_url)

        # check notification button
        try:
            button = page.query_selector("#notification button.ui-button.solid--red")
            if button:
                print("Clicking notification close button...")
                button.click()
        except Exception as e:
            print("Notification button error:", e)

        # Check for the "no products" block
        try:
            page.wait_for_selector('div[data-test-id="block__empty-page"]', timeout=3000)
            print(" ⚠️ No more products on this page. Ending pagination.")
            break
        except TimeoutError:
            pass  # No empty block, continue

        # Extract product cards
        product_cards = page.query_selector_all("div.catalog-product")
        for card in product_cards:
            try:
                title = card.query_selector("h3").inner_text() if card.query_selector("h3") else "No title"
                img_tag = card.query_selector("img")
                image = img_tag.get_attribute("src") if img_tag else "No image"
                products.append({
                    "title": title,
                    "image": image,
                    "img_tag": img_tag
                })
                print(f"   • Product: {title}, Image: {image}")
            except Exception as e:
                print("   • Error reading product:", e)

        current_page += 1
        if current_page == 3:
            break
        time.sleep(1)

    print("products = ", products)

if __name__ == "__main__":
    main()
