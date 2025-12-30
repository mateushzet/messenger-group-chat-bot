import time
from playwright.sync_api import Page
import uuid
import os
import datetime

def take_error_screenshot(page):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"error_{timestamp}.png"
    page.screenshot(path=filename)

def _get_unique_id():
    timestamp = int(time.time() * 1000000)
    random_id = uuid.uuid4().hex[:8]
    unique_id = f"{timestamp}_{random_id}"
    return f"{unique_id}"