import time
import os
from queue import Queue
from logger import logger
from auth import MessengerAuth
from utils import take_info_screenshot
from utils import take_error_screenshot

def file_worker(file_queue: Queue):
    while True:
        time.sleep(20)
        try:
            auth = MessengerAuth()
            page, browser, playwright = auth.log_in_to_messenger()
    
            if not page:
                logger.critical("[FileWorker] Failed to log in")
                continue

            logger.info("[FileWorker] Ready to send files")

            try:
                take_info_screenshot(page, "ready_to_send_files")
            except Exception as e:
                logger.error(f"[FileWorker] Failed to take screenshot: {e}")

            while True:
                file_path = file_queue.get()

                if file_path is None:
                    logger.critical("[FileWorker] Received shutdown signal")
                    break

                try:
                    if not os.path.exists(file_path):
                        logger.error(f"[FileWorker] File does not exist: {file_path}")
                        continue

                    logger.info(f"[FileWorker] Sending file: {file_path}")

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
                        logger.critical("[FileWorker] Could not find file input")
                        continue

                    page.wait_for_selector(
                        "div[aria-label='Remove attachment']",
                        timeout=20000
                    )

                    page.wait_for_selector(
                        "div[aria-label='Press enter to send']",
                        timeout=10000
                    )
                    page.click("div[aria-label='Press enter to send']")

                    logger.info(f"[FileWorker] File sent: {os.path.basename(file_path)}")

                except Exception as e:
                    logger.critical(f"[FileWorker] Send error: {e}",exc_info=True)

                    if browser.is_connected():
                        try:
                            take_error_screenshot(page, "file_send")
                        except:
                            pass
                    else:
                        logger.critical("[FileWorker] Browser disconnected, will reconnect")
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
            logger.critical("[FileWorker] File worker interrupted")
            break
        except Exception as e:
            logger.critical(f"[FileWorker] File worker error: {e}", exc_info=True)
            time.sleep(10)

    logger.critical("[FileWorker] File worker stopped")
