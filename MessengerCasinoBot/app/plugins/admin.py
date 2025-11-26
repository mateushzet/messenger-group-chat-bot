import os
import sys
import signal
import subprocess
from user_manager import UserManager

def register():
    return {
        "name": "admin",
        "description": "Admin commands: /admin setAvatar <old_avatar_url> <new_avatar_url> <name>, addUser <avatar_url> <name> [is_admin], listUsers, userInfo <name>, makeAdmin <avatar_url> <name>, removeAdmin <avatar_url> <name>, addMoney <amount> <name>, kill, restart",
        "execute": execute
    }

def execute(command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
    if not cache:
        return

    user_manager = UserManager(cache)
    
    if not check_admin_permissions(user_manager, sender, avatar_url):
        return

    if len(args) < 1:
        return

    subcommand = args[0].lower()

    try:
        if subcommand == "setavatar":
            if len(args) < 4:
                return
            
            old_avatar_url = args[1]
            new_avatar_url = args[2]
            name = " ".join(args[3:])
            
            success, message = user_manager.admin_set_avatar(name, old_avatar_url, new_avatar_url)
            
        elif subcommand == "adduser":
            if len(args) < 3:
                return
            
            if len(args) > 2 and args[-1].lower() in ['true', 'false']:
                avatar_url_param = args[1]
                name_parts = args[2:-1]
                name = " ".join(name_parts) if name_parts else args[2]
                admin_flag = args[-1].lower() == "true"
            else:
                avatar_url_param = args[1]
                name = " ".join(args[2:])
                admin_flag = False
            
            success, message = user_manager.admin_add_user(name, avatar_url_param, admin_flag)
            
        elif subcommand == "listusers":
            list_users(cache, file_queue)
            
        elif subcommand == "userinfo":
            if len(args) < 2:
                return
            
            name = " ".join(args[1:])
            show_user_info(cache, name, file_queue)
            
        elif subcommand == "makeadmin":
            if len(args) < 3:
                return
            
            avatar_url_param = args[1]
            name = " ".join(args[2:])
            
            success, message = user_manager.set_user_admin(name, avatar_url_param, True)
            
        elif subcommand == "removeadmin":
            if len(args) < 3:
                return
            
            avatar_url_param = args[1]
            name = " ".join(args[2:])
            
            success, message = user_manager.set_user_admin(name, avatar_url_param, False)

        elif subcommand == "addmoney":
            if len(args) < 3:
                return
            
            amount_str = args[1]
            name = " ".join(args[2:])
            
            try:
                amount = int(amount_str)
                if amount <= 0:
                    return
            except ValueError:
                return
            
            success, message = add_money_to_user(user_manager, name, amount)

        elif subcommand == "kill":
            try:
                cache.save_to_disk()
            except Exception as e:
                return
            
            os.kill(os.getpid(), signal.SIGTERM)
            
        elif subcommand == "restart":
            try:
                cache.save_to_disk()
            except Exception as e:
                return
            
            script_path = os.path.abspath(sys.argv[0])
            python_executable = sys.executable
            
            try:
                subprocess.Popen([python_executable, script_path] + sys.argv[1:])
                os.kill(os.getpid(), signal.SIGTERM)
            except Exception as e:
                pass
            
        else:
            pass
            
    except Exception as e:
        pass

def check_admin_permissions(user_manager, sender_name, avatar_url):
    if not sender_name or not avatar_url:
        return False
    
    user_data = user_manager.find_user_by_name_avatar(sender_name, avatar_url)[1]
    return user_data and user_data.get('is_admin', False)

def list_users(cache, file_queue):
    if not hasattr(cache, 'users'):
        return
    
    users_info = []
    for user_id, user_data in cache.users.items():
        admin_status = " (ADMIN)" if user_data.get('is_admin') else ""
        users_info.append(f"ID: {user_id} | Name: {user_data.get('name', 'unknown')}{admin_status} | Balance: {user_data.get('balance', 0)}")
    
    if users_info:
        users_text = "\n".join(users_info)

def show_user_info(cache, name, file_queue):
    if not hasattr(cache, 'users'):
        return
    
    users_with_name = []
    for user_id, user_data in cache.users.items():
        if user_data.get("name") == name:
            users_with_name.append((user_id, user_data))
    
    if not users_with_name:
        return
    
    user_info = []
    for user_id, user_data in users_with_name:
        admin_status = "YES" if user_data.get('is_admin') else "NO"
        user_info.append(f"""
User: {name} (ID: {user_id})
Balance: {user_data.get('balance', 0)}
Level: {user_data.get('level', 1)}
Level Progress: {user_data.get('level_progress', 0.1)}
Admin: {admin_status}
Avatar URL: {user_data.get('avatar_url', 'none')}
Avatar File: {user_data.get('avatar', 'none')}
Background: {user_data.get('background', 'none')}
------------------------""")
    
    info_text = "\n".join(user_info)

def add_money_to_user(user_manager, name, amount):
    users_with_same_name = user_manager.find_users_by_name(name)
    
    if not users_with_same_name:
        return False, f"User not found: {name}"
    
    if len(users_with_same_name) > 1:
        users_list = "\n".join([f"- ID: {user_id} (balance: {user_data.get('balance', 0)})" 
                              for user_id, user_data in users_with_same_name])
        return False, f"Multiple users found with name '{name}'. Use ID:\n{users_list}"
    
    user_id, user_data = users_with_same_name[0]
    old_balance = user_data.get('balance', 0)
    new_balance = old_balance + amount
    
    user_manager.cache.update_user(user_id, balance=new_balance)
    
    return True, f"Added {amount} to user {name} (ID: {user_id}). New balance: {new_balance}"