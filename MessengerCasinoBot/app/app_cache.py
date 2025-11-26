import json
import threading
import time
import os
from datetime import datetime, timedelta

class AppCache:
    def __init__(self, backup_file="cache_backup.json", autosave_interval=900):
        self.backup_file = backup_file
        self.backup_dir = "backups"
        self.lock = threading.Lock()
        self.autosave_interval = autosave_interval
        self.last_daily_backup = None

        self.users = {}
        self.games = {}
        self.settings = {}

        os.makedirs(self.backup_dir, exist_ok=True)

        self._load_backup()

        threading.Thread(target=self._autosave_loop, daemon=True).start()

    def _load_backup(self):
        if not os.path.exists(self.backup_file):
            return
        try:
            with open(self.backup_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.users = data.get("users", {})
                
                for user_id, user_data in self.users.items():
                    if "avatar_path" in user_data and "avatar" not in user_data:
                        old_path = user_data["avatar_path"]
                        user_data["avatar"] = os.path.basename(old_path) if old_path else "default-avatar.png"
                        del user_data["avatar_path"]
                    
                    if "background_path" in user_data and "background" not in user_data:
                        old_path = user_data["background_path"]
                        user_data["background"] = os.path.basename(old_path) if old_path else "default-bg.png"
                        del user_data["background_path"]
                    
                    if "avatar_url" not in user_data:
                        user_data["avatar_url"] = None
                    
                    if "is_admin" not in user_data:
                        user_data["is_admin"] = False
                
                self.games = data.get("games", {})
                self.settings = data.get("settings", {})
        except Exception as e:
            print(f"Cache load error: {e}")

    def _autosave_loop(self):
        while True:
            time.sleep(self.autosave_interval)
            self.save_to_disk()
            self._check_daily_backup()

    def _check_daily_backup(self):
        now = datetime.now()
        
        if (self.last_daily_backup is None or 
            now - self.last_daily_backup >= timedelta(days=1)):
            
            self._create_daily_backup()
            self.last_daily_backup = now

    def _create_daily_backup(self):
        try:
            with self.lock:
                date_str = datetime.now().strftime("%Y-%m-%d")
                backup_filename = f"cache_backup_{date_str}.json"
                backup_path = os.path.join(self.backup_dir, backup_filename)
                
                data = {
                    "users": self.users,
                    "games": self.games,
                    "settings": self.settings
                }
                
                with open(backup_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                self._cleanup_old_backups()
                
        except Exception as e:
            print(f"Daily backup error: {e}")

    def _cleanup_old_backups(self, keep_days=7):
        try:
            now = datetime.now()
            for filename in os.listdir(self.backup_dir):
                if filename.startswith("cache_backup_") and filename.endswith(".json"):
                    date_str = filename[13:-5]
                    try:
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        if (now - file_date) > timedelta(days=keep_days):
                            file_path = os.path.join(self.backup_dir, filename)
                            os.remove(file_path)
                    except ValueError:
                        continue
        except Exception as e:
            print(f"Backup cleanup error: {e}")

    def save_to_disk(self):
        with self.lock:
            try:
                data = {
                    "users": self.users,
                    "games": self.games,
                    "settings": self.settings
                }
                with open(self.backup_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Cache save error: {e}")

    def get_user(self, user_id):
        with self.lock:
            return self.users.get(str(user_id))

    def set_user(self, user_id, name, balance=0, level=1, level_progress=0.0,
                 avatar="default-avatar.png", background="default-bg.png", 
                 avatar_url=None, is_admin=False, **kwargs):
        with self.lock:
            self.users[str(user_id)] = {
                "name": name,
                "balance": balance,
                "level": level,
                "level_progress": level_progress,
                "avatar": avatar,
                "background": background,
                "avatar_url": avatar_url,
                "is_admin": is_admin,
                **kwargs
            }

    def update_user(self, user_id, **fields):
        with self.lock:
            uid = str(user_id)
            if uid not in self.users:
                self.users[uid] = {
                    "name": f"User {uid}", 
                    "balance": 0, 
                    "level": 1, 
                    "level_progress": 0.0,
                    "avatar": "default-avatar.png", 
                    "background": "default-bg.png",
                    "avatar_url": None,
                    "is_admin": False
                }
            self.users[uid].update(fields)
            return self.users[uid]

    def update_balance(self, user_id, delta):
        with self.lock:
            uid = str(user_id)
            if uid not in self.users:
                self.users[uid] = {
                    "name": f"User {uid}", 
                    "balance": 0, 
                    "level": 1, 
                    "level_progress": 0.0,
                    "avatar": "default-avatar.png", 
                    "background": "default-bg.png",
                    "avatar_url": None,
                    "is_admin": False
                }
            self.users[uid]["balance"] += delta
            return self.users[uid]["balance"]

    def get_avatar_path(self, user_id):
        user = self.get_user(user_id)
        if user and user.get("avatar"):
            return self._resolve_relative_path(os.path.join("assets", "avatars", user["avatar"]))
        return self._resolve_relative_path(os.path.join("assets", "avatars", "default-avatar.png"))

    def get_background_path(self, user_id):
        user = self.get_user(user_id)
        if user and user.get("background"):
            return self._resolve_relative_path(os.path.join("assets", "backgrounds", user["background"]))
        return self._resolve_relative_path(os.path.join("assets", "backgrounds", "default-bg.png"))

    def get_game_state(self, game_id):
        with self.lock:
            return self.games.get(str(game_id))

    def set_game_state(self, game_id, state):
        with self.lock:
            self.games[str(game_id)] = state

    def get_setting(self, key, default=None):
        with self.lock:
            return self.settings.get(key, default)

    def set_setting(self, key, value):
        with self.lock:
            self.settings[key] = value

    def _resolve_relative_path(self, relative_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(current_dir, relative_path)
        
        if os.path.exists(full_path):
            return full_path
        else: 
            backup_path = os.path.join(current_dir, os.path.join("assets", "backgrounds", "default-bg.png"))
            return backup_path
        
    def add_experience(self, user_id, win_amount):
        with self.lock:
            uid = str(user_id)
            
            if uid not in self.users:
                self.users[uid] = {
                    "name": f"User {uid}", 
                    "balance": 0, 
                    "level": 1, 
                    "level_progress": 0.0,
                    "avatar": "default-avatar.png", 
                    "background": "default-bg.png",
                    "avatar_url": None,
                    "is_admin": False
                }
            
            user = self.users[uid]
            
            if win_amount >= 0:
                return user["level"], user["level_progress"]
            
            loose_amount = abs(win_amount)
            progress_increase = int(loose_amount / user["level"] / 2)
            
            if progress_increase == 0:
                return user["level"], user["level_progress"]
            
            progress_to_add = progress_increase / 100.0
            new_progress = user["level_progress"] + progress_to_add
            level_gained = 0
            
            if new_progress >= 1.0:
                level_gained = 1
                user["level"] += 1
                user["level_progress"] = new_progress = 0.1
            else:
                user["level_progress"] = new_progress
            
            return user["level"], user["level_progress"]