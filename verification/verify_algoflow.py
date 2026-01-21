from playwright.sync_api import sync_playwright
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the file directly
        cwd = os.getcwd()
        filepath = f"file://{cwd}/pages/algoflow/index.html"
        print(f"Navigating to: {filepath}")

        page.goto(filepath)

        # Wait for the page to load (check for a key element)
        page.wait_for_selector("h1")

        # Take a screenshot
        screenshot_path = "verification/algoflow_verification.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

        browser.close()

if __name__ == "__main__":
    run()
