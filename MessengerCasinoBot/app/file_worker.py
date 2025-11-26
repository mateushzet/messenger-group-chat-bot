import time
import os
from queue import Queue
from playwright.sync_api import sync_playwright
from auth import MessengerAuth

BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, "config")


def file_worker(file_queue: Queue):
    with sync_playwright() as p:
        auth = MessengerAuth()
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            viewport={"width": 1000, "height": 900},
            locale="en-US"
        )

        if not auth.load_cookies(context):
            print("No cookies - cannot send file")
            browser.close()
            return

        page = context.new_page()
        try:
            page.goto(
                f"https://www.messenger.com/t/{auth.threadid}",
                wait_until="domcontentloaded",
                timeout=60000
            )
        except Exception as e:
            print(f"Load error: {e}")
            browser.close()
            return

        print("Ready to send files")

        while True:
            file_path = file_queue.get()
            if file_path is None:
                break

            try:
                print(f"Sending file: {file_path}")
                page.wait_for_selector("input.x1s85apg", state="attached", timeout=30000)
                page.set_input_files("input.x1s85apg", file_path)
                time.sleep(1)
                page.keyboard.press("Enter")

            except Exception as e:
                print(f"Send error: {e}")
            finally:
                file_queue.task_done()

        print("Closing browser")
        browser.close()