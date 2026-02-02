import logging
import os
import glob
from datetime import datetime, timedelta

def cleanup_old_logs(logs_dir, days_to_keep=2):
    if not os.path.exists(logs_dir):
        return
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    log_files = glob.glob(os.path.join(logs_dir, "*.log"))
    
    deleted_count = 0
    for log_file in log_files:
        try:
            file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
            
            if file_time < cutoff_date:
                os.remove(log_file)
                deleted_count += 1
                print(f"Deleted old log: {os.path.basename(log_file)}")
                
        except Exception as e:
            print(f"Error deleting {log_file}: {e}")
    
    if deleted_count > 0:
        print(f"Cleaned up {deleted_count} old log files")
    else:
        print("No old log files to clean up")

def setup_logging(days_to_keep=2, enable_console=True):
    logs_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    cleanup_old_logs(logs_dir, days_to_keep)
    
    log_filename = datetime.now().strftime("log_%Y%m%d_%H_%M.log")
    log_path = os.path.join(logs_dir, log_filename)
    
    handlers = []
    
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    handlers.append(file_handler)
    
    if enable_console:
        console_handler = logging.StreamHandler()
        handlers.append(console_handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    logger = logging.getLogger(__name__)
    
    logger.info(f"[Logger] Logging initialized, Log file: {log_path}, Keeping logs for {days_to_keep} days")
    
    return logger

logger = setup_logging(days_to_keep=2)