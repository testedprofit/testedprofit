
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Navigate to the page
    page.goto("http://localhost:8080/pages/things%20to%20do%20in%20vail%20colorado/index.html")

    # Wait for React to mount and content to be visible
    page.wait_for_selector('text="VAIL LOCAL"')

    # Check if key elements are present
    if page.is_visible('text="The Free Bus System"'):
        print("Content is visible")
    else:
        print("Content not found")

    # Take a screenshot
    page.screenshot(path="verification/vail_page.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
