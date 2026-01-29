import os
import sys
import signal
import subprocess
import time
from user_manager import UserManager
from logger import logger
from base_game_plugin import BaseGamePlugin


class AdminPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="admin_system")

    def execute(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        
        if not cache:
            logger.error("[Admin] Cache not available")
            self.send_message_image(sender, file_queue, "Cache not available", "Admin - System Error", cache, None)
            return ""

        user_manager = UserManager(cache)

        if not self.check_admin_permissions(user_manager, sender, avatar_url):
            self.send_message_image(sender, file_queue, "Access denied!\n\nAdmin privileges required.", "Admin - Access Denied", cache, None)
            return ""
            
        if len(args) < 1:
            self.send_message_image(sender, file_queue, 
                            "Available Admin Commands:\n\n" \
                            "1. setAvatar <old_url> <new_url> <name_or_id>\n" \
                            "2. addUser <avatar_url> <name> [is_admin]\n" \
                            "3. userInfo <name_or_id>\n" \
                            "4. makeAdmin <avatar_url> <name_or_id>\n" \
                            "5. removeAdmin <avatar_url> <name_or_id>\n" \
                            "6. addMoney <amount> <name_or_id>\n" \
                            "7. kill\n" \
                            "8. restart\n\n" \
                            "Admin access only",
                            "Admin Commands", cache, None)
            return ""

        subcommand = args[0].lower()

        try:
            if subcommand == "setavatar":
                if len(args) < 4:
                    self.send_message_image(sender, file_queue, 
                                    "Usage: /admin setAvatar <old_avatar_url> <new_avatar_url> <name_or_id>\n\n" \
                                    "Examples:\n" \
                                    "/admin setAvatar old.jpg new.jpg John\n" \
                                    "/admin setAvatar old.jpg new.jpg 123",
                                    "Admin - Set Avatar", cache, None)
                    return ""
                
                old_avatar_url = args[1]
                new_avatar_url = args[2]
                name_or_id = " ".join(args[3:])
                
                if name_or_id.isdigit():
                    user_id = int(name_or_id)
                    user_data = user_manager.cache.users.get(user_id)
                    if not user_data:
                        self.send_message_image(sender, file_queue, f"User with ID {user_id} not found", 
                                        "Admin - Error", cache, None)
                        return ""
                    name_or_id = user_data.get('name', str(user_id))
                
                success, message = user_manager.admin_set_avatar(name_or_id, old_avatar_url, new_avatar_url)
                if success:
                    self.send_message_image(sender, file_queue, f"SUCCESS: {message}", "Admin - Success", cache, None)
                else:
                    self.send_message_image(sender, file_queue, f"ERROR: {message}", "Admin - Error", cache, None)
                return ""
                
            elif subcommand == "adduser":
                if len(args) < 3:
                    self.send_message_image(sender, file_queue, 
                                    "Usage: /admin addUser <avatar_url> <name> [true/false]\n\n" \
                                    "Examples:\n" \
                                    "/admin addUser avatar.jpg John\n" \
                                    "/admin addUser avatar.jpg John true (as admin)",
                                    "Admin - Add User", cache, None)
                    return ""
                
                if len(args) > 2 and args[-1].lower() in ['true', 'false']:
                    avatar_url_param = args[1]
                    name_parts = args[2:-1]
                    name = " ".join(name_parts) if name_parts else args[2]
                    admin_flag = args[-1].lower() == "true"
                else:
                    avatar_url_param = args[1]
                    raw_name = " ".join(args[2:]).strip()
                    name = raw_name[1:].strip() if raw_name.startswith("@") else raw_name
                    admin_flag = False
                
                success, message = user_manager.admin_add_user(name, avatar_url_param, admin_flag)
                if success:
                    self.send_message_image(sender, file_queue, f"SUCCESS: {message}", "Admin - User Added", cache, None)
                else:
                    logger.error(f"[Admin] User not added correctly: {name} - {avatar_url_param}")
                    self.send_message_image(sender, file_queue, f"ERROR: {message}", "Admin - Error", cache, None)
                return ""
                
            elif subcommand == "listusers":
                users_text = self.list_users(cache)
                self.send_message_image(sender, file_queue, users_text, "Admin - User List", cache, None)
                return ""
                
            elif subcommand == "userinfo":
                
                if len(args) < 2:
                    self.send_message_image(sender, file_queue, 
                                    "Usage: /admin userInfo <name_or_id>\n\n" \
                                    "Examples:\n" \
                                    "/admin userInfo John\n" \
                                    "/admin userInfo 123",
                                    "Admin - User Info", cache, None)
                    return ""
                
                name_or_id = " ".join(args[1:])
                
                if name_or_id.isdigit():
                    user_id = int(name_or_id)
                    user_data = user_manager.cache.users.get(user_id)
                    if user_data:
                        actual_name = user_data.get('name', str(user_id))
                        user_info_text = self.show_user_info_by_id(cache, user_id, actual_name)
                    else:
                        user_info_text = f"User with ID {user_id} not found"
                else:
                    user_info_text = self.show_user_info(cache, name_or_id)
                
                title = f"Admin - Info: {name_or_id}"
                self.send_message_image(sender, file_queue, user_info_text, title, cache, None)
                return ""
                
            elif subcommand == "makeadmin":
                if len(args) < 3:
                    self.send_message_image(sender, file_queue, 
                                    "Usage: /admin makeAdmin <avatar_url> <name_or_id>\n\n" \
                                    "Examples:\n" \
                                    "/admin makeAdmin avatar.jpg John\n" \
                                    "/admin makeAdmin avatar.jpg 123",
                                    "Admin - Make Admin", cache, None)
                    return ""
                
                avatar_url_param = args[1]
                raw_name_or_id = " ".join(args[2:]).strip()
                
                if raw_name_or_id.isdigit():
                    user_id = int(raw_name_or_id)
                    user_data = user_manager.cache.users.get(user_id)
                    if not user_data:
                        logger.error(f"[Admin] Failed to grant admin rights, user not found: {user_id}")
                        self.send_message_image(sender, file_queue, f"User with ID {user_id} not found", 
                                        "Admin - Error", cache, None)
                        return ""
                    name = user_data.get('name', str(user_id))
                else:
                    name = raw_name_or_id[1:].strip() if raw_name_or_id.startswith("@") else raw_name_or_id
                
                success, message = user_manager.set_user_admin(name, avatar_url_param, True)
                if success:
                    self.send_message_image(sender, file_queue, f"SUCCESS: {message}", "Admin - Success", cache, None)
                else:
                    logger.error(f"[Admin] Failed to grant admin rights: {raw_name_or_id}")
                    self.send_message_image(sender, file_queue, f"ERROR: {message}", "Admin - Error", cache, None)
                return ""
                
            elif subcommand == "removeadmin":
                if len(args) < 3:
                    self.send_message_image(sender, file_queue, 
                                    "Usage: /admin removeAdmin <avatar_url> <name_or_id>\n\n" \
                                    "Examples:\n" \
                                    "/admin removeAdmin avatar.jpg John\n" \
                                    "/admin removeAdmin avatar.jpg 123",
                                    "Admin - Remove Admin", cache, None)
                    return ""
                
                avatar_url_param = args[1]
                raw_name_or_id = " ".join(args[2:]).strip()
                
                if raw_name_or_id.isdigit():
                    user_id = int(raw_name_or_id)
                    user_data = user_manager.cache.users.get(user_id)
                    if not user_data:
                        self.send_message_image(sender, file_queue, f"User with ID {user_id} not found", 
                                        "Admin - Error", cache, None)
                        return ""
                    name = user_data.get('name', str(user_id))
                else:
                    name = raw_name_or_id[1:].strip() if raw_name_or_id.startswith("@") else raw_name_or_id
                
                success, message = user_manager.set_user_admin(name, avatar_url_param, False)
                if success:
                    self.send_message_image(sender, file_queue, f"SUCCESS: {message}", "Admin - Success", cache, None)
                else:
                    logger.error(f"[Admin] Failed to revoke admin rights: {user_id}")
                    self.send_message_image(sender, file_queue, f"ERROR: {message}", "Admin - Error", cache, None)
                return ""

            elif subcommand == "addmoney":
                if len(args) < 3:
                    self.send_message_image(sender, file_queue, 
                                    "Usage: /admin addMoney <amount> <name_or_id>\n\n" \
                                    "Examples:\n" \
                                    "/admin addMoney 1000 John\n" \
                                    "/admin addMoney 1000 123",
                                    "Admin - Add Money", cache, None)
                    return ""
                
                amount_str = args[1]
                raw_name_or_id = " ".join(args[2:]).strip()
                
                try:
                    amount = int(amount_str)
                except ValueError:
                    self.send_message_image(sender, file_queue, 
                                    "Invalid amount!\n\nPlease provide a valid number.",
                                    "Admin - Error", cache, None)
                    return ""
                
                success, message = self.add_money_to_user(user_manager, raw_name_or_id, amount)
                if success:
                    logger.info(f"[Admin] Added {amount} to {raw_name_or_id} balance")
                    self.send_message_image(sender, file_queue, f"SUCCESS: {message}", "Admin - Money Added", cache, None)
                else:
                    logger.error(f"[Admin] Failed to add {amount} money: {raw_name_or_id}")
                    self.send_message_image(sender, file_queue, f"ERROR: {message}", "Admin - Error", cache, None)
                return ""

            elif subcommand == "kill":
                try:
                    cache.save_to_disk()
                    self.send_message_image(sender, file_queue, 
                                    "Bot shutdown initiated!\n\nSaving data and stopping...",
                                    "Admin - Shutdown", cache, None)
                    logger.critical(f"[Admin] Bot shutdown initiated by {sender}")
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"[Admin] Failed to save cache to disk before Kill command", exc_info=True)
                    pass
                
                os.kill(os.getpid(), signal.SIGTERM)
                return ""
                
            elif subcommand == "restart":
                try:
                    cache.save_to_disk()
                    self.send_message_image(sender, file_queue, 
                                    "Bot restart initiated!\n\nSaving data and restarting...",
                                    "Admin - Restart", cache, None)
                    logger.critical(f"[Admin] Bot restart initiated by {sender}")
                    time.sleep(1)
                except Exception as e:
                    logger.error(f"[Admin] Failed to save cache to disk before restart", exc_info=True)
                    pass
                
                script_path = os.path.abspath(sys.argv[0])
                python_executable = sys.executable
                
                try:
                    subprocess.Popen([python_executable, script_path] + sys.argv[1:])
                    os.kill(os.getpid(), signal.SIGTERM)
                except Exception as e:
                    logger.error(f"[Admin] Restart command not processed successfully", exc_info=True)
                    pass
                return ""
                
            else:
                self.send_message_image(sender, file_queue, 
                                f"Unknown command: {subcommand}\n\n" \
                                "Use /admin without arguments to see available commands.",
                                "Admin - Unknown Command", cache, None)
                return ""
                
        except Exception as e:
            logger.critical(f"[Admin] Plugin failed executing command {e}", exc_info=True)
            import traceback
            traceback.print_exc()
            self.send_message_image(sender, file_queue, 
                            f"Error executing command: {str(e)}\n\n" \
                            "Please check the command syntax.",
                            "Admin - System Error", cache, None)
            return ""

    def check_admin_permissions(self, user_manager, sender_name, avatar_url):
        if not sender_name or not avatar_url:
            return False
        
        result = user_manager.find_user_by_name_avatar(sender_name, avatar_url)
        
        if not result:
            return False
        
        user_data = result[1] if len(result) > 1 else None
        is_admin = user_data and user_data.get('is_admin', False)
        return is_admin

    def list_users(self, cache):
        if not hasattr(cache, 'users'):
            return "No users found"
        
        users_info = []
        for user_id, user_data in cache.users.items():
            admin_status = "ADMIN" if user_data.get('is_admin') else "USER"
            users_info.append(f"ID: {user_id}\nName: {user_data.get('name', 'unknown')} - {admin_status}\nBalance: ${user_data.get('balance', 0)}")
        
        if users_info:
            users_text = "\n\n" + "\n".join(users_info)
            return f"Total Users: {len(cache.users)}\n{users_text}"
        else:
            return "No users in database"

    def show_user_info(self, cache, name):
        
        if not hasattr(cache, 'users'):
            return "No users found"
        
        users_with_name = []
        for user_id, user_data in cache.users.items():
            user_name = user_data.get("name", "")
            if user_name == name:
                users_with_name.append((user_id, user_data))
        
        if not users_with_name:
            return f"User not found: {name}\n\nAvailable users:\n{self.list_user_names(cache)}"
        
        user_info = []
        for user_id, user_data in users_with_name:
            admin_status = "YES" if user_data.get('is_admin') else "NO"
            level = user_data.get('level', 1)
            level_progress = int(user_data.get('level_progress', 0.1) * 100)
            
            balance = user_data.get('balance', 0)
            avatar = user_data.get('avatar', 'default')
            background = user_data.get('background', 'default')
            experience = user_data.get('experience', 0)
            avatar_url = user_data.get('avatar_url', 'N/A')
            created_at = user_data.get('created_at', 'N/A')
            
            user_info.append(f"""
User: {name} (ID: {user_id})
Balance: ${balance}
Level: {level} ({level_progress}%)
Admin: {admin_status}
Avatar: {avatar}
Background: {background}
Experience: {experience}
Avatar URL: {avatar_url}
Created: {created_at}
------------------------""")
        
        info_text = "\n".join(user_info)
        return info_text

    def show_user_info_by_id(self, cache, user_id, name=None):
        
        if not hasattr(cache, 'users'):
            return "No users found"
        
        user_data = cache.users.get(user_id)
        if not user_data:
            return f"User with ID {user_id} not found"
        
        actual_name = name or user_data.get('name', str(user_id))
        admin_status = "YES" if user_data.get('is_admin') else "NO"
        level = user_data.get('level', 1)
        level_progress = int(user_data.get('level_progress', 0.1) * 100)
        
        balance = user_data.get('balance', 0)
        avatar = user_data.get('avatar', 'default')
        background = user_data.get('background', 'default')
        experience = user_data.get('experience', 0)
        avatar_url = user_data.get('avatar_url', 'N/A')
        created_at = user_data.get('created_at', 'N/A')
        
        return f"""
User: {actual_name}
ID: {user_id}
Balance: ${balance}
Level: {level} ({level_progress}%)
 Admin: {admin_status}
Avatar: {avatar}
Background: {background}
Experience: {experience}
Avatar URL: {avatar_url}
Created: {created_at}
"""

    def list_user_names(self, cache):
        if not hasattr(cache, 'users'):
            return "No users"
        
        names = []
        for user_id, user_data in cache.users.items():
            name = user_data.get('name', 'NO_NAME')
            names.append(f"- {name} (ID: {user_id})")
        
        return "\n".join(names) if names else "No users found"

    def add_money_to_user(self, user_manager, name_or_id, amount):

        if isinstance(name_or_id, str) and name_or_id.startswith('@'):
            name_or_id = name_or_id[1:].strip()

        if name_or_id.isdigit():
            user_id = int(name_or_id)
            user_data = user_manager.cache.users.get(user_id)
            
            if not user_data:
                return False, f"User with ID {user_id} not found"
            
            old_balance = user_data.get('balance', 0)
            new_balance = old_balance + amount
            user_manager.cache.update_user(user_id, balance=new_balance)
            
            user_name = user_data.get('name', str(user_id))
            return True, f"Added ${amount} to user {user_name} (ID: {user_id}). New balance: ${new_balance}"

        users_with_same_name = user_manager.find_users_by_name(name_or_id)
        
        if not users_with_same_name:
            return False, f"User not found: {name_or_id}"
        
        if len(users_with_same_name) > 1:
            users_list = "\n".join([f"- ID: {user_id} (balance: ${user_data.get('balance', 0)})" 
                                for user_id, user_data in users_with_same_name])
            return False, f"Multiple users found with name '{name_or_id}'. Please use ID:\n{users_list}"
        
        user_id, user_data = users_with_same_name[0]
        old_balance = user_data.get('balance', 0)
        new_balance = old_balance + amount
        
        user_manager.cache.update_user(user_id, balance=new_balance)
        
        logger.info(f"[Admin] Added {amount} balance to {name_or_id}")

        return True, f"Added ${amount} to user {name_or_id} (ID: {user_id}). New balance: ${new_balance}"
    
def register():
    plugin = AdminPlugin()
    return {
        "name": "admin",
        "description": "Admin Commands\n" \
                    "/admin setAvatar <old_url> <new_url> <name_or_id> - Change user avatar\n" \
                    "/admin addUser <avatar_url> <name> [is_admin] - Add new user\n" \
                    "/admin userInfo <name_or_id> - Show user details\n" \
                    "/admin makeAdmin <avatar_url> <name_or_id> - Grant admin privileges\n" \
                    "/admin removeAdmin <avatar_url> <name_or_id> - Remove admin privileges\n" \
                    "/admin addMoney <amount> <name_or_id> - Add coins to user\n" \
                    "/admin kill - Stop the bot\n" \
                    "/admin restart - Restart the bot",
        "execute": plugin.execute
    }