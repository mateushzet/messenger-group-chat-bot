import json
import os
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

class MessengerAuth:
    def __init__(self, config_path: str = "MessengerCasinoBot\config.ini"):
        self.cookies_file = "cookies.json"
        self.storage_file = "auth_state.json"
        self._load_config(config_path)
    
    def _load_config(self, config_path: str):
        import configparser
        config = configparser.ConfigParser()
        config.read(config_path)
        self.username = config["credentials"]["username"]
        self.password = config["credentials"]["password"]
        self.threadid = config["messenger"]["threadid"]

    def load_cookies(self, context):
        try:
            if not os.path.exists(self.cookies_file):
                return False
                
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
                if not cookies:
                    return False
                    
                context.add_cookies(cookies)
                print("[AUTH] Loaded cookies successfully")
                return True
                
        except Exception as e:
            print(f"[AUTH] Cookie loading error: {str(e)}")
            return False

    def save_cookies(self, context):
        try:
            cookies = context.cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            print("[AUTH] Saved cookies successfully")
        except Exception as e:
            print(f"[AUTH] Cookie save error: {str(e)}")

    def is_logged_in(self, page: Page, timeout: float = 10.0):
        try:
            page.wait_for_selector("div[aria-label='Chats']", timeout=timeout*10000)
            return True
        except PlaywrightTimeoutError:
            return False

    def login_with_credentials(self, page: Page):
        print("[AUTH] Attempting login with credentials...")
        try:
            # Enter login data
            page.fill("input[name='email']", self.username)
            page.fill("input[name='pass']", self.password)
            
            # Click the login button
            login_button = page.locator("button[name='login']").first
            login_button.click()
            
            # Wait for login confirmation
            page.wait_for_selector("div[aria-label='Chats']", timeout=15000)
            print("[AUTH] Login successful")
            return True
            
        except Exception as e:
            print(f"[AUTH] Login failed: {str(e)}")
            page.screenshot(path="login_error.png")
            return False

    @staticmethod
    def accept_all_cookies(page):
        try:
            page.wait_for_selector("#allow_button", timeout=5000)
            page.click("#allow_button")
            print("[AUTH] Clicked 'Allow all cookies' button.")
        except Exception as e:
            print(f"[AUTH] Cookie accept button not found or failed to click: {e}")
