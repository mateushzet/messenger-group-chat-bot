import time
import uuid
import datetime

def take_error_screenshot(page, name):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"error_{name}_{timestamp}.png"
    page.screenshot(path=filename)

def take_info_screenshot(page, name):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"info_{name}_{timestamp}.png"
    page.screenshot(path=filename)

def _get_unique_id():
    timestamp = int(time.time() * 1000000)
    random_id = uuid.uuid4().hex[:8]
    unique_id = f"{timestamp}_{random_id}"
    return f"{unique_id}"