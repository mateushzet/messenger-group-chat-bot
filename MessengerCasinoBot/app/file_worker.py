import time
import os
import random
from queue import Queue
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
from auth import MessengerAuth

BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, "config")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def file_worker(file_queue: Queue):
    while True:
        time.sleep(20)
        try:
            auth = MessengerAuth()
            page, browser, playwright = auth.log_in_to_messenger()
    
            if not page:
                print("Failed to log in")
                continue

            print("Ready to send files")

            try:
                auth._take_screenshot(page, "ready_to_send_files")
            except Exception as e:
                print(f"Failed to take screenshot: {e}")

            while True:
                file_path = file_queue.get()

                if file_path is None:
                    print("Received shutdown signal")
                    break

                try:
                    if not os.path.exists(file_path):
                        print(f"File does not exist: {file_path}")
                        continue

                    print(f"Sending file: {file_path}")
                    auth._take_screenshot(page, "before_sending_file")

                    file_input_found = False
                    file_selectors = [
                        "input.x1s85apg",
                        "input[type='file']",
                        "div[aria-label='Attach'] input"
                    ]

                    for selector in file_selectors:
                        try:
                            page.wait_for_selector(selector, state="attached", timeout=5000)
                            page.set_input_files(selector, file_path)
                            file_input_found = True
                            break
                        except:
                            continue

                    if not file_input_found:
                        print("Could not find file input")
                        continue

                    page.wait_for_selector(
                        "div[aria-label='Remove attachment']",
                        timeout=20000
                    )

                    time.sleep(1)

                    auth._take_screenshot(page, "file_sent_check_previous")

                    page.wait_for_selector(
                        "div[aria-label='Press enter to send']",
                        timeout=10000
                    )
                    page.click("div[aria-label='Press enter to send']")

                    auth._take_screenshot(page, "file_sent_check_after")
                    print(f"File sent: {os.path.basename(file_path)}")

                except Exception as e:
                    print(f"Send error: {e}")

                    if browser.is_connected():
                        try:
                            auth._take_screenshot(page, "send_error")
                        except:
                            pass
                    else:
                        print("Browser disconnected, will reconnect...")
                        break

                finally:
                    file_queue.task_done()

            try:
                browser.close()
            except:
                pass

            try:
                playwright.stop()
            except:
                pass

            if file_path is None:
                break

        except KeyboardInterrupt:
            print("File worker interrupted")
            break
        except Exception as e:
            print(f"File worker error: {e}")
            time.sleep(10)

    print("File worker stopped")
