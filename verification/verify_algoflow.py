
from playwright.sync_api import sync_playwright
import time

def verify_algoflow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Listen for console errors
        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda exc: errors.append(str(exc)))

        print("Navigating to page...")
        page.goto("http://localhost:8080/pages/algoflow/index.html")

        # Wait for some animation frames
        print("Waiting for animation...")
        time.sleep(2)

        # Check if canvas exists
        if page.locator("#simCanvas").count() > 0:
            print("Canvas found.")
        else:
            print("Error: Canvas not found.")
            errors.append("Canvas not found")

        # Take screenshot
        print("Taking screenshot...")
        page.screenshot(path="verification/algoflow.png")

        browser.close()

        if errors:
            print("Errors detected:")
            for e in errors:
                print(e)
            exit(1)
        else:
            print("No errors detected.")

if __name__ == "__main__":
    verify_algoflow()
