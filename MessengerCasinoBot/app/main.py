from threading import Thread
from queue import Queue
from app_cache import AppCache
from command_worker import command_worker
from file_worker import file_worker
from message_handlers import start_monitoring_messegases

def main():
    cache = AppCache(autosave_interval=60)
    command_queue = Queue()
    file_queue = Queue()

    cmd_thread = Thread(target=command_worker, args=(command_queue, file_queue, cache), daemon=True)
    file_thread = Thread(target=file_worker, args=(file_queue,), daemon=True)

    cmd_thread.start()
    file_thread.start()

    try:
        start_monitoring_messegases(command_queue)
    except KeyboardInterrupt:
        print("Stopping...")
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