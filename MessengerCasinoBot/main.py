import time
from datetime import datetime as dt
from playwright.sync_api import sync_playwright
from auth import MessengerAuth
from utils import Utils
from message_handlers import extract_messages_fix_unknown_sender

def main():
    with sync_playwright() as p:
        auth = MessengerAuth()
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(viewport={"width": 1000, "height": 900}, locale="en-US")
        page = context.new_page()

        if not auth.load_cookies(context):
            print("No cookies found, login required")

        try:
            page.goto("https://www.messenger.com/t/"+auth.threadid, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"Loading error: {e}")
            Utils.take_error_screenshot(page)
            browser.close()
            return

        if not auth.is_logged_in(page):
            auth.accept_all_cookies(page)
            if not auth.login_with_credentials(page):
                print("Login error")
                browser.close()
                return
            auth.save_cookies(context)

        time.sleep(8)
        Utils.remove_unwanted_aria_labels(page)

        while True:
            extract_messages_fix_unknown_sender(page)
            time.sleep(1)
            print(dt.now().isoformat())
            page.screenshot(path="error_latest.png")

if __name__ == "__main__":
    main()