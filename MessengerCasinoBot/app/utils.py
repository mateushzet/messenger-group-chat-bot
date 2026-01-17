import time
import uuid
from datetime import datetime
from logger import logger
from datetime import datetime, timedelta
import os
import re
import logging
import os
import glob

BASE_DIR = os.path.dirname(__file__)
INFO_DIR = os.path.join(BASE_DIR, "screenshots","error")
ERROR_DIR = os.path.join(BASE_DIR, "screenshots","info")

_last_cleanup_time = 0
_CLEANUP_INTERVAL = 3600

def _sanitize(name):
    return re.sub(r'[<>:"/\\|?*]', '_', str(name or "unknown")).strip('_')

def _take_screenshot(page, name, prefix="screenshot"):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = _sanitize(name)
        filename = f"{prefix}_{safe_name}_{timestamp}.png"
        
        folder = "screenshots"
        if prefix == "error":
            folder = os.path.join(folder, "errors")
        elif prefix == "info":
            folder = os.path.join(folder, "info")
        
        os.makedirs(folder, exist_ok=True)
        full_path = os.path.join(folder, filename)
        
        page.screenshot(path=full_path, full_page=True)
        
        cleanup_old_files(INFO_DIR)
        cleanup_old_files(ERROR_DIR)
        return full_path
    except Exception as e:
        logger.error(f"Failed to take {prefix} screenshot", exc_info=True)
        return None

def take_error_screenshot(page, name):
    return _take_screenshot(page, name, "error")

def take_info_screenshot(page, name):
    return _take_screenshot(page, name, "info")

def _get_unique_id():
    return f"{int(time.time() * 1000000)}_{uuid.uuid4().hex[:8]}"

def _try_cleanup():
    global _last_cleanup_time
    
    current_time = time.time()
    if current_time - _last_cleanup_time >= _CLEANUP_INTERVAL:
        try:
            deleted_info = cleanup_old_files(INFO_DIR, days_to_keep=1, file_pattern="*.png")
            deleted_error = cleanup_old_files(ERROR_DIR, days_to_keep=1, file_pattern="*.png")
            
            if deleted_info > 0 or deleted_error > 0:
                logger.info(f"[Cleanup] Auto-cleaned {deleted_info} info + {deleted_error} error screenshots")
            
            _last_cleanup_time = current_time
        except Exception as e:
            logger.error(f"[Cleanup] Failed: {e}")

def cleanup_old_files(directory, days_to_keep=1, file_pattern="*"):
    if not os.path.exists(directory):
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)

    if file_pattern:
        files_to_check = glob.glob(os.path.join(directory, file_pattern))
    else:
        files_to_check = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                files_to_check.append(os.path.join(root, file))
    
    deleted_count = 0
    for file_path in files_to_check:
        try:
            if os.path.isfile(file_path):
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_time < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
                    logging.debug(f"Deleted old file: {os.path.basename(file_path)}")
                    
        except Exception as e:
            logging.warning(f"Error deleting {file_path}: {e}")
    
    return deleted_count