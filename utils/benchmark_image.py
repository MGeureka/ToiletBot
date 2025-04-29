import asyncio
from playwright.async_api import async_playwright


async def get_voltaic_image(username: str):
    url = f"https://beta.voltaic.gg/aimlabs/{username}"
    share_xpath = "/html/body/div[2]/div/div[2]/div/div/div/div[2]/div[1]/div[1]/button"
    button_selector = f"xpath={share_xpath}"
    img_xpath = """/html/body/div[4]/div/div/div/div[2]/div/div/div/div[1]/img[starts-with(@src, "data:image/jpeg;base64,")]"""
    img_selector = f"xpath={img_xpath}"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        # Selector based on current site behavior
        analytics_xpath = "/html/body/div[4]/div/div/div/div[2]/div/div/div/div[3]/div/button[2]"
        analytics_decline_selector = f"xpath={analytics_xpath}"

        # Try to click the analytics popup button if it shows up
        try:
            await page.wait_for_selector(analytics_decline_selector, timeout=3000)
            await page.click(analytics_decline_selector)
        except Exception:
            pass  # Popup didn’t show, probably already accepted or dismissed

        # Click "Share Image" button
        await page.click(button_selector)

        # Wait for the base64 image to appear
        await page.wait_for_selector(img_selector)

        # Get the base64 image data from the img src
        image_data_url = await page.eval_on_selector(img_selector, "el => el.src")

        await browser.close()
        return image_data_url

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    base = loop.run_until_complete(get_voltaic_image("mgeureka"))
    print(base)
