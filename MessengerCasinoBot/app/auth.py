import json
import os
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
import configparser

BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, "config")
os.makedirs(CONFIG_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.ini")
COOKIES_FILE = os.path.join(CONFIG_DIR, "cookies.json")
STORAGE_FILE = os.path.join(CONFIG_DIR, "auth_state.json")

class MessengerAuth:
    def __init__(self, config_path: str = CONFIG_FILE):
        self.config_path = config_path
        self.cookies_file = COOKIES_FILE
        self.storage_file = STORAGE_FILE
        self._load_config(self.config_path)
    
    def _load_config(self, config_path: str):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        config = configparser.ConfigParser()
        config.read(config_path)
        
        try:
            self.username = config["credentials"]["username"]
            self.password = config["credentials"]["password"]
            self.threadid = config["messenger"]["threadid"]
        except KeyError as e:
            raise KeyError(f"Missing key in config.ini: {e}")

    def load_cookies(self, context):
        try:
            if not os.path.exists(self.cookies_file):
                return False
                
            with open(self.cookies_file, 'r', encoding="utf-8") as f:
                cookies = json.load(f)
                if not cookies:
                    return False
                    
                context.add_cookies(cookies)
                return True
                
        except Exception as e:
            print(f"Cookie loading error: {str(e)}")
            return False

    def save_cookies(self, context):
        try:
            cookies = context.cookies()
            with open(self.cookies_file, 'w', encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
        except Exception as e:
            print(f"Cookie save error: {str(e)}")

    def is_logged_in(self, page: Page, timeout: float = 10.0):
        try:
            return True
        except PlaywrightTimeoutError:
            return False

    def login_with_credentials(self, page: Page):
        try:
            page.fill("input[name='email']", self.username)
            page.fill("input[name='pass']", self.password)
            login_button = page.locator("button[name='login']").first
            login_button.click()
            
            page.wait_for_selector("div[aria-label='Thread list']", timeout=15000)
            return True
            
        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    @staticmethod
    def accept_all_cookies(page):
        try:
            page.wait_for_selector("#allow_button", timeout=5000)
            page.click("#allow_button")
        except Exception:
            print("Cookie accept button not found")