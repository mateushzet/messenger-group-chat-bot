import time
import os
from queue import Queue
from logger import logger
from auth import MessengerAuth
from utils import take_info_screenshot
from utils import take_error_screenshot
import time
def file_worker(file_queue: Queue):
    max_retries = 3
    retry_delay = 1
    
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

                file_sent = False
                
                for attempt in range(max_retries):
                    try:
                        if not os.path.exists(file_path):
                            logger.error(f"[FileWorker] File does not exist: {file_path}")
                            break
   
                        file_input_found = False
                        file_selectors = [
                            "input.x1s85apg",
                            "input[type='file']",
                            "div[aria-label='Attach'] input"
                        ]

                        for selector in file_selectors:
                            try:
                                page.wait_for_selector(selector, state="attached", timeout=10000)
                                page.set_input_files(selector, file_path)
                                file_input_found = True
                                break
                            except Exception as e:
                                continue

                        if not file_input_found:
                            logger.critical("[FileWorker] Could not find file input")
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                continue
                            else:
                                break

                        try:
                            page.wait_for_selector(
                                "div[aria-label='Remove attachment']",
                                timeout=5000
                            )
                        except Exception as upload_error:
                            logger.warning(f"[FileWorker] Attachment load timeout/error: {upload_error}")

                        try:
                            page.wait_for_selector(
                                "div[aria-label='Press enter to send']",
                                timeout=5000
                            )
                            
                            page.click("div[aria-label='Press enter to send']")

                            try:
                                page.wait_for_selector(
                                    "div[aria-label='Remove attachment']",
                                    state="hidden",
                                    timeout=3000
                                )
                            except:
                                pass
                            
                            file_sent = True
                            logger.info(f"[FileWorker] File sent successfully: {os.path.basename(file_path)}")
                            break
                            
                        except Exception as send_error:
                            logger.error(f"[FileWorker] Send attempt {attempt + 1} failed: {send_error}")
                            
                            alternative_send_selectors = [
                                "div[aria-label='Send']",
                                "div[aria-label*='send']",
                                "div[data-testid='send-button']",
                            ]
                            
                            for send_selector in alternative_send_selectors:
                                try:
                                    if page.is_visible(send_selector, timeout=1000):
                                        page.click(send_selector)
                                        logger.info(f"[FileWorker] Clicked alternative send button: {send_selector}")
                                        file_sent = True
                                        break
                                except:
                                    continue
                            
                            if file_sent:
                                break
                            
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                
                                try:
                                    page.click("div[aria-label='Remove attachment']")
                                    logger.info("[FileWorker] Removed old attachment before retry")
                                except:
                                    pass

                    except Exception as e:
                        logger.critical(f"[FileWorker] Error in attempt {attempt + 1}: {e}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        else:
                            logger.critical(f"[FileWorker] All {max_retries} attempts failed for: {file_path}")
                            break

                if not file_sent:
                    logger.critical(f"[FileWorker] Failed to send file after all attempts: {file_path}")
                    
                    if browser.is_connected():
                        try:
                            take_error_screenshot(page, f"send_failed_{os.path.basename(file_path)}")
                        except Exception as screenshot_error:
                            logger.error(f"[FileWorker] Failed to take error screenshot: {screenshot_error}")

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