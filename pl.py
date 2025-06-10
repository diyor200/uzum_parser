import asyncio
from playwright.async_api import async_playwright

async def click_specific_size_get_by_text():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("Navigating to the product page...")
        await page.goto("https://uzum.uz/uz/product/new-balance-erkaklar-krossovkalari-1552187?skuId=5109824")
        print("Page loaded.")

        # --- Handle potential pop-ups (if any) ---
        # Look for a common pop-up close button selector, e.g., '[aria-label="Close"]' or a specific class.
        # This is speculative, you might need to find the actual selector.
        # try:
        #     await page.click('[aria-label="Close"]', timeout=5000) # Adjust selector and timeout
        #     print("Closed a pop-up.")
        # except Exception:
        #     pass # No pop-up or couldn't close it

        desired_size = "42"

        try:
            print(f"Attempting to click size: {desired_size} using get_by_text")
            # This is more direct for clicking by visible text
            size_element = page.get_by_text(desired_size).first # Use .first if multiple elements contain "42"

            # Ensure the element is visible and interactive before clicking
            await size_element.wait_for(state='visible', timeout=15000)
            await size_element.click()

            print(f"Successfully clicked size {desired_size}!")

            await asyncio.sleep(21)
            await page.screenshot(path=f"size_{desired_size}_clicked_get_by_text.png")
            print(f"Screenshot taken: size_{desired_size}_clicked_get_by_text.png")

        except Exception as e:
            print(f"Could not click size {desired_size} using get_by_text. Error: {e}")
            await page.screenshot(path="error_get_by_text.png")
            print("Screenshot of error page taken: error_get_by_text.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(click_specific_size_get_by_text())