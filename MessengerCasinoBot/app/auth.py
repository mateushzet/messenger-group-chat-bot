import json
import os
from playwright.sync_api import Page, sync_playwright
import configparser
import time
from logger import logger
from utils import take_error_screenshot, take_info_screenshot

BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.ini")
COOKIES_FILE = os.path.join(CONFIG_DIR, "cookies.json")

class MessengerAuth:
    def __init__(self, config_path: str = CONFIG_FILE):
        self.config_path = config_path
        self.cookies_file = COOKIES_FILE
        self._load_config(self.config_path)
    
    def _load_config(self, config_path: str):
        if not os.path.exists(config_path):
            logger.critical(f"[AUTH] Config file not found: {config_path}")
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        config = configparser.ConfigParser()
        config.read(config_path)
        
        try:
            self.threadid = config["messenger"]["threadid"]
            self.pin = config["credentials"]["pin"]
        except KeyError as e:
            logger.critical(f"[AUTH] Missing key in config.ini: {e}")
            raise KeyError(f"Missing key in config.ini: {e}")

    def load_cookies(self, context):
        try:
            if not os.path.exists(self.cookies_file):
                logger.critical("[AUTH] No cookies file found")
                return False
                
            with open(self.cookies_file, 'r', encoding="utf-8") as f:
                cookies_raw = json.load(f)
                if not cookies_raw:
                    logger.critical("[AUTH] Cookies file is empty")
                    return False

                cleaned_cookies = []
                for cookie in cookies_raw:
                    try:
                        sameSite_raw = cookie.get('sameSite', '').lower()
                        sameSite_map = {
                            'no_restriction': 'None',
                            'unspecified': 'Lax',
                            'lax': 'Lax',
                            'strict': 'Strict',
                            'none': 'None'
                        }
                        cookie['sameSite'] = sameSite_map.get(sameSite_raw, 'Lax')
                        
                        cleaned_cookies.append(cookie)
                    except Exception as e:
                        logger.critical(f"[AUTH] Could not clean cookie: {e}", exc_info=True)
                        continue
                
                logger.info(f"[AUTH] Loaded {len(cleaned_cookies)} cookies")
                context.add_cookies(cleaned_cookies)
                return True
                
        except json.JSONDecodeError as e:
            logger.critical(f"[AUTH] Cookie loading error: Invalid JSON: {str(e)}")
            return False
        except Exception as e:
            logger.critical(f"[AUTH] Cookie loading error: {str(e)}")
            return False

    def check_pin_dialog(self, page: Page) -> bool:
        try:
            pin_selectors = [
                "h2:has-text('PIN')",
                "input[aria-label='PIN']",
                "input[maxlength='6']",
                "//div[contains(text(), 'Enter your PIN')]",
                "//span[contains(text(), 'Enter your PIN')]",
            ]
            
            for selector in pin_selectors:
                try:
                    if selector.startswith("//"):
                        element = page.locator(f"xpath={selector}")
                    else:
                        element = page.locator(selector)
                    
                    if element.count() > 0 and element.first.is_visible(timeout=1000):
                        logger.info(f"[AUTH] PIN dialog detected")
                        return True
                except:
                    continue
            
            return False
        except:
            return False

    def handle_pin_dialog(self, page: Page) -> bool:
        try:
            logger.info(f"[AUTH] Handling PIN dialog")

            try:
                page.wait_for_selector("input[maxlength='6']", timeout=5000)
            except:
                logger.critical(f"[AUTH] PIN input not found")
                take_error_screenshot(page, "pin_input_not_found")
                return False
            
            pin_input = None
            selectors = [
                "input[maxlength='6']",
                "input[aria-label='PIN']",
                "#mw-numeric-code-input-prevent-composer-focus-steal"
            ]
            
            for selector in selectors:
                try:
                    pin_input = page.locator(selector)
                    if pin_input.count() > 0 and pin_input.first.is_visible(timeout=1000):
                        pin_input = pin_input.first
                        break
                except:
                    continue
            
            if not pin_input:
                logger.critical(f"[AUTH] PIN input not found")
                take_error_screenshot(page, "pin_input_not_found")
                return False
            
            pin_input.click()
            page.wait_for_timeout(500)
            pin_input.fill("")
            page.wait_for_timeout(500)
            
            for char in self.pin:
                pin_input.press(char)
                page.wait_for_timeout(100)
            
            page.wait_for_timeout(1000)
            
            entered_value = pin_input.input_value()
            if entered_value == self.pin:
                logger.info(f"[AUTH] PIN entered correctly")
            else:
                logger.critical(f"[AUTH] PIN mismatch: expected {self.pin}, got {entered_value}")
                pin_input.fill(self.pin)
            
            pin_input.press("Enter")
            page.wait_for_timeout(3000)
            
            try:
                page.wait_for_selector("input[maxlength='6']", state="hidden", timeout=5000)
                return True
            except:
                if page.locator("text=Incorrect").count() > 0 or page.locator("text=Wrong").count() > 0:
                    logger.critical("[AUTH] Incorrect PIN")
                    return False
                
                logger.warning("[AUTH] PIN dialog may still be visible, but continuing")
                return True
                
        except Exception as e:
            logger.critical(f"[AUTH] Error in handle_pin_dialog: {e}", exc_info=True)
            take_error_screenshot(page, "pin_submit")
            return False

    def check_and_handle_browser_notice(self, page: Page) -> bool:
        try:
            close_selectors = [
                "button[aria-label='Close']",
                "button[aria-label='Zamknij']",
                "div[role='button'][aria-label='Close']",
                "div[role='button'][aria-label='Zamknij']",
                "button:has-text('×')",
                "button:has-text('✕')",
                "button:has-text('X')",
                "[role='button']:has-text('×')",
                "svg[aria-label='Close']",
                "//button[contains(@aria-label, 'Close')]",
                "//div[contains(@aria-label, 'Close')]",
                "//*[contains(@class, 'close')]",
                "//*[contains(@class, 'Close')]"
            ]
            
            for selector in close_selectors:
                try:
                    if selector.startswith("//"):
                        element = page.locator(f"xpath={selector}")
                    else:
                        element = page.locator(selector)
                    
                    if element.count() > 0 and element.first.is_visible(timeout=2000):
                        element.first.click(force=True)
                        page.wait_for_timeout(1000)
                        
                        logger.info("[AUTH] Dialog closed")
                        return True
                except Exception as e:
                    continue
            
            try:
                result = page.evaluate("""
                    () => {
                        // Szukaj elementów z 'close' w aria-label
                        const elements = document.querySelectorAll('[aria-label*="close" i], [aria-label*="zamknij" i]');
                        for (const el of elements) {
                            if (el.click) {
                                el.click();
                                return 'clicked by aria-label';
                            }
                        }
                        
                        // Szukaj elementów z tekstem X, ×, ✕
                        const xElements = Array.from(document.querySelectorAll('button, div[role="button"]'))
                            .filter(el => {
                                const text = el.innerText || '';
                                return text === '×' || text === '✕' || text === 'X' || text === 'x';
                            });
                        
                        if (xElements.length > 0) {
                            xElements[0].click();
                            return 'clicked by X text';
                        }
                        
                        // Szukaj elementów w prawym górnym rogu
                        const rightTopElements = Array.from(document.querySelectorAll('button, div[role="button"]'))
                            .filter(el => {
                                const rect = el.getBoundingClientRect();
                                return rect.top < 100 && rect.right > window.innerWidth - 100;
                            });
                        
                        if (rightTopElements.length > 0) {
                            rightTopElements[0].click();
                            return 'clicked by position';
                        }
                        
                        return 'no close button found';
                    }
                """)
                logger.info(f"[AUTH] JavaScript result: {result}")
                
                if "clicked" in result:
                    page.wait_for_timeout(1000)
                    return True
                    
            except Exception as e:
                logger.error(f"[AUTH] JavaScript error: {e}")
            
            return True
            
        except Exception as e:
            logger.critical(f"[AUTH] error in check_and_handle_browser_notice: {e}", exc_info=True)
            take_error_screenshot(page, "handle_browser_notice")
            return False

    def remove_unwanted_aria_labels(self, page: Page):
        aria_labels_to_remove = [
            "Inbox switcher",
            "Chats",
            "Marketplace",
            "Requests",
            "Archive",
            "Settings, help and more",
            "Expand inbox sidebar",
            "New message",
            "Close",
            "Fix now",
            "Start a voice call",
            "Start a video call",
            "Conversation information",
            "Details and actions",
            "Send a voice clip",
            "Choose a sticker",
            "Choose a GIF",
            "Choose an emoji",
            "Send a like",
            "Profile",
            "Unmute notifications",
            "Search",
            "Chat info",
            "Customize chat",
            "Media & files",
            "Thread composer"
        ]

        classes_to_remove = [
            "some-class-to-remove",
            "x1ey2m1c",
        ]

        js_labels = ','.join([f'"{label}"' for label in aria_labels_to_remove])
        js_classes = ','.join([f'"{cls}"' for cls in classes_to_remove])

        page.evaluate(f"""
            (() => {{
                const labels = [{js_labels}];
                const classes = [{js_classes}];

                const elements = document.querySelectorAll('[aria-label]');
                elements.forEach(el => {{
                    const label = el.getAttribute('aria-label');
                    if (!label) return;

                    for (const target of labels) {{
                        if (label === target || label.startsWith(target)) {{
                            el.remove();
                            break;
                        }}
                    }}
                }});

                classes.forEach(cls => {{
                    document.querySelectorAll(`div.${{cls}}`).forEach(el => el.remove());
                }});
            }})();
        """)

    def log_in_to_messenger(self):
        p = sync_playwright().start()
        
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            viewport={"width": 1200, "height": 800},
            locale="en-US",
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"}
        )
        page = context.new_page()

        self.load_cookies(context)

        try:
            page.goto(
                f"https://www.messenger.com/t/{self.threadid}",
                wait_until="domcontentloaded",
                timeout=30000
            )
        except Exception as e:
            logger.critical(f"[AUTH] Loading error: {e}")
            browser.close()
            p.stop()
            return None, None, None

        time.sleep(5)
        
        self.check_and_handle_browser_notice(page)
        
        time.sleep(10)
        
        if self.check_pin_dialog(page):
            
            if not self.handle_pin_dialog(page):
                logger.critical("[AUTH] Failed to handle PIN dialog")
                
                browser.close()
                p.stop()
                return None, None, None
        
        time.sleep(5)
        take_info_screenshot(page, "after_log_in")
        
        return page, browser, p