from queue import Queue
from threading import Thread
from app_cache import AppCache
from command_worker import command_worker
from file_worker import file_worker
from message_handlers import start_monitoring_messages
import time

def initialize_math_scheduler(cache, file_queue):
    from plugins.math_challenge import MathChallengePlugin
    
    plugin = MathChallengePlugin()
    plugin.cache = cache
    
    success = plugin.start_scheduler(file_queue)
    
    if success:
        print(f"[MATH] Scheduler started. First challenge will be sent at random time.")
    else:
        print(f"[MATH] Failed to start scheduler")
    
    return plugin

def main():
    cache = AppCache(autosave_interval=60)
    command_queue = Queue()
    file_queue = Queue()

    cmd_thread = Thread(target=command_worker, args=(command_queue, file_queue, cache), daemon=True)
    file_thread = Thread(target=file_worker, args=(file_queue,), daemon=True)

    cmd_thread.start()
    file_thread.start()
    
    print("[MATH] Initializing challenge scheduler...")
    math_plugin = initialize_math_scheduler(cache, file_queue)
    print("[MATH] Bot started. Waiting for first random math challenge...")

    try:
        start_monitoring_messages(command_queue)
    except KeyboardInterrupt:
        print("Stopping...")
        if hasattr(math_plugin, 'stop_scheduler'):
            math_plugin.stop_scheduler = True
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        command_queue.put(None)
        file_queue.put(None)
        command_queue.join()
        file_queue.join()
        cmd_thread.join()
        file_thread.join()
        cache.save_to_disk()
        print("All workers stopped.")

if __name__ == "__main__":
    main()