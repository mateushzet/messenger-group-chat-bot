import importlib
import os
import time
from queue import Queue
from user_manager import UserManager

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
                print(f"Loaded: {command_name}")
                
                if "aliases" in info:
                    for alias in info["aliases"]:
                        PLUGINS[alias] = info
                        print(f"  Alias: {alias}")
                        
            except Exception as e:
                print(f"Error loading {filename}: {e}")

def execute_command(command_data, file_queue, cache):
    message_text = command_data.get("message").lower()
    sender_name = command_data.get("sender").lower()
    avatar_url = command_data.get("avatar_url")

    user_manager = UserManager(cache)
    success, message = user_manager.create_user(sender_name, avatar_url)

    if not success:
        print(f"Security: {message}")
        return

    if not message_text:
        print("No 'message' field in command")
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
            print(f"Error in plugin {plugin['name']}: {e}")
    else:
        print(f"Unknown command: {command_name}")


def command_worker(command_queue: Queue, file_queue: Queue, cache):
    print("Command worker starting...")
    load_plugins()

    while True:
        command_data = command_queue.get()
        if command_data is None:
            break
        try:
            if command_data.get("message"):
                execute_command(command_data, file_queue, cache)
            else:
                print("No 'message' field in command object")
        except Exception as e:
            print(f"Command worker error: {e}")
        finally:
            command_queue.task_done()
            time.sleep(0.1)

    print("Command worker stopped.")