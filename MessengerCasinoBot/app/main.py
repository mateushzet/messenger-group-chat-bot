from queue import Queue
from threading import Thread
from app_cache import AppCache
from command_worker import command_worker
from file_worker import file_worker
from logger import logger
from message_handler import start_monitoring_messages
from plugins.math_challenge import get_math_plugin_instance

def main():
    cache = AppCache(autosave_interval=60)
    command_queue = Queue()
    file_queue = Queue()

    cmd_thread = Thread(target=command_worker, args=(command_queue, file_queue, cache), daemon=True)
    file_thread = Thread(target=file_worker, args=(file_queue,), daemon=True)

    cmd_thread.start()
    file_thread.start()
    
    math_plugin = get_math_plugin_instance().initialize_math_scheduler(cache, file_queue)

    try:
        start_monitoring_messages(command_queue)
    except KeyboardInterrupt:
        logger.critical("[MAIN] KeyboardInterrupt")
        if hasattr(math_plugin, 'stop_scheduler'):
            math_plugin.stop_scheduler()
    except Exception as e:
        logger.critical(f"[MAIN] Unexpected error: {e}", exc_info=True)
    finally:
        if hasattr(math_plugin, 'stop_scheduler'):
            math_plugin.stop_scheduler()
        
        command_queue.put(None)
        file_queue.put(None)
        command_queue.join()
        file_queue.join()
        cmd_thread.join()
        file_thread.join()
        cache.save_to_disk()
        logger.critical("[MAIN] All workers stopped.")

if __name__ == "__main__":
    main()