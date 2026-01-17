import importlib
import os
import time
from queue import Queue
from user_manager import UserManager
from logger import logger

PLUGINS = {}

def load_plugins():
    plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
    for filename in os.listdir(plugins_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            module_name = f"plugins.{filename[:-3]}"
            try:
                module = importlib.import_module(module_name)
                info = module.register()
                
                command_name = f"/{info['name']}"
                PLUGINS[command_name] = info
                logger.info(f"[CommandWorker] Loaded: {command_name}")
                
                if "aliases" in info:
                    for alias in info["aliases"]:
                        PLUGINS[alias] = info
                        logger.info(f"[CommandWorker] Alias: {alias}")
                        
            except Exception as e:
                logger.critical(f"[CommandWorker] Error loading {filename}: {e}", exc_info=True)

def execute_command(command_data, file_queue, cache):
    message_text = command_data.get("message").lower()
    sender_name = command_data.get("sender").lower()
    avatar_url = command_data.get("avatar_url")

    user_manager = UserManager(cache)
    success, message = user_manager.create_user(sender_name, avatar_url)

    if not success:
        logger.warning(f"[CommandWorker] Security: {message}")
        return

    if not message_text:
        logger.info("[CommandWorker] No 'message' field in command")
        return

    parts = message_text.strip().split()
    if not parts:
        return

    command_name = parts[0]
    args = parts[1:]

    if command_name in PLUGINS:
        plugin = PLUGINS[command_name]
        try:
            plugin["execute"](
                command_name, 
                args, 
                file_queue, 
                cache=cache, 
                sender=sender_name,
                avatar_url=avatar_url
            )
        except Exception as e:
            logger.critical(f"Error in plugin {plugin['name']}: {e}", exc_info=True)
    else:
        logger.info(f"[CommandWorker] Unknown command: {command_name}")


def command_worker(command_queue: Queue, file_queue: Queue, cache):
    logger.info("[CommandWorker] Command worker starting")
    load_plugins()

    while True:
        command_data = command_queue.get()
        if command_data is None:
            break
        try:
            if command_data.get("message"):
                execute_command(command_data, file_queue, cache)
            else:
                logger.warning(f"[CommandWorker] No 'message' field in command object")
        except Exception as e:
            logger.critical(f"[CommandWorker] Command worker error: {e}", exc_info=True)
        finally:
            command_queue.task_done()
            time.sleep(0.1)

    logger.critical("[CommandWorker] Command worker stopped.")