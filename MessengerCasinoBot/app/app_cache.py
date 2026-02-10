import json
import threading
import time
import os
from datetime import datetime, timedelta
from logger import logger
from message_handler import get_last_message_time

class AppCache:
    def __init__(self, backup_file="cache_backup.json", autosave_interval=60):
        self.backup_file = backup_file
        self.backup_dir = "backups"
        self.lock = threading.Lock()
        self.autosave_interval = autosave_interval
        self.last_daily_backup = None

        self.users = {}
        self.games = {}
        self.settings = {}
        
        self.market_items = []
        self.auctions = []
        
        self.active_math_challenge = None

        os.makedirs(self.backup_dir, exist_ok=True)

        self._load_backup()

        threading.Thread(target=self._autosave_loop, daemon=True).start()

    def _load_backup(self):
        if not os.path.exists(self.backup_file):
            logger.info(f"[AppCache] No backup file found at {self.backup_file}")
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
                    
                    if "backgrounds" not in user_data:
                        user_data["backgrounds"] = ["default-bg.png"]
                    
                    if "avatars" not in user_data:
                        user_data["avatars"] = ["default-avatar.png"]
                    
                    if "purchase_history" not in user_data:
                        user_data["purchase_history"] = []
                
                self.games = data.get("games", {})
                self.settings = data.get("settings", {})
                
                market_data = data.get("market_items", [])
                self.auctions = data.get("auctions", [])
                
                converted_items = []
                for item in market_data:
                    if isinstance(item, dict):
                        if "type" in item and "file" in item:
                            if "id" not in item:
                                item["id"] = f"market_{len(converted_items)}"
                            if "listed_at" not in item:
                                item["listed_at"] = time.time()
                            if "status" not in item:
                                item["status"] = "for_sale"
                            
                            converted_items.append(item)
                        elif "file" in item and "type" not in item:
                            converted_items.append({
                                "type": "background",
                                "file": item.get("file", ""),
                                "price": item.get("price", 100),
                                "seller_id": item.get("seller_id"),
                                "seller_name": item.get("seller_name", "Unknown"),
                                "listed_at": item.get("listed_at", time.time()),
                                "status": "for_sale",
                                "id": f"market_{len(converted_items)}"
                            })
                    elif isinstance(item, str):
                        converted_items.append({
                            "type": "background",
                            "file": item,
                            "price": 100,
                            "seller_id": None,
                            "seller_name": "Unknown",
                            "listed_at": time.time(),
                            "status": "for_sale",
                            "id": f"market_{len(converted_items)}"
                        })
                
                self.market_items = converted_items
                
                if "ranking_leader_record" not in self.settings:
                    old_money_record = self.settings.get("money_leader_record")
                    if old_money_record and "user_id" in old_money_record:
                        self.settings["ranking_leader_record"] = old_money_record
                
                self.active_math_challenge = data.get("active_math_challenge")
                if self.active_math_challenge is None:
                    self.active_math_challenge = None
                
                logger.info(f"[AppCache] Cache loaded: {len(self.users)} users, {len(self.market_items)} market items, {len(self.auctions)} auctions")

        except Exception as e:
            logger.critical(f"[AppCache] Cache load error: {e}", exc_info=True)

    def _autosave_loop(self):
        while True:
            time.sleep(self.autosave_interval)
            last_msg_time = get_last_message_time()
            time_diff = (datetime.now() - last_msg_time).total_seconds()   
            if time_diff > (self.autosave_interval * 1.5):
                continue
            else:
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
                    "settings": self.settings,
                    "market_items": self.market_items,
                    "auctions": self.auctions,
                }
                
                with open(backup_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"[AppCache] Daily backup saved: {len(self.market_items)} market items, {len(self.auctions)} auctions")

                self._cleanup_old_backups()
                
        except Exception as e:
            logger.critical(f"[AppCache] Daily backup error: {e}")

    def _cleanup_old_backups(self, keep_days=3):
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
            logger.info(f"[AppCache] Backup cleanup completed")
        except Exception as e:
            logger.error(f"[AppCache] Backup cleanup error: {e}", exc_info=True)

    def save_to_disk(self):
        with self.lock:
            try:
                data = {
                    "users": self.users,
                    "games": self.games,
                    "settings": self.settings,
                    "market_items": self.market_items,
                    "auctions": self.auctions,
                    "active_math_challenge": self.active_math_challenge
                }
                with open(self.backup_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                logger.info(f"[AppCache] Autosave completed: {len(self.market_items)} market items, {len(self.auctions)} auctions")
            except Exception as e:
                logger.critical(f"Cache save error: {e}", exc_info=True)
    
    def add_market_item(self, item):
        with self.lock:
            if "id" not in item:
                item["id"] = f"market_{len(self.market_items)}_{int(time.time())}"
            
            if "listed_at" not in item:
                item["listed_at"] = time.time()
            
            if "status" not in item:
                item["status"] = "for_sale"
            
            self.market_items.append(item)
            return True
    
    def remove_market_item(self, item_file):
        with self.lock:
            for i, item in enumerate(self.market_items):
                if item.get("file") == item_file:
                    del self.market_items[i]
                    return True
            return False
    
    def get_market_items(self):
        return self.market_items.copy()
    
    def add_auction(self, auction):
        with self.lock:
            if "id" not in auction:
                auction["id"] = f"auction_{len(self.auctions)}_{int(time.time())}"
            
            if "created_at" not in auction:
                auction["created_at"] = time.time()
            
            if "status" not in auction:
                auction["status"] = "active"
            
            if "bids" not in auction:
                auction["bids"] = []
            
            self.auctions.append(auction)
            logger.info(f"[AppCache] Auction added: {auction.get('type')} {auction.get('file')} by {auction.get('seller_name', 'Unknown')}")
            return True
    
    def update_auction(self, index, auction):
        with self.lock:
            if 0 <= index < len(self.auctions):
                self.auctions[index] = auction
                return True
            return False
    
    def get_auctions(self):
        return self.auctions.copy()
    
    def remove_auction(self, auction_id):
        with self.lock:
            for i, auction in enumerate(self.auctions):
                if auction.get("id") == auction_id:
                    del self.auctions[i]
                    return True
            return False

    
    def get_user(self, user_id):
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
                "backgrounds": kwargs.get("backgrounds", ["default-bg.png"]),
                "avatars": kwargs.get("avatars", ["default-avatar.png"]),
                **kwargs
            }

    def update_user(self, user_id, **fields):
        with self.lock:
            uid = str(user_id)
            if uid not in self.users:
                self.users[uid] = {
                    "name": f"User {uid}", 
                    "balance": 50, 
                    "level": 1, 
                    "level_progress": 0.1,
                    "avatar": "default-avatar.png", 
                    "background": "default-bg.png",
                    "avatar_url": None,
                    "is_admin": False,
                    "backgrounds": ["default-bg.png"],
                    "avatars": ["default-avatar.png"]
                }
            self.users[uid].update(fields)
            return self.users[uid]

    def update_balance(self, user_id, delta):
        with self.lock:
            uid = str(user_id)
            if uid not in self.users:
                self.users[uid] = {
                    "name": f"User {uid}", 
                    "balance": 50, 
                    "level": 1, 
                    "level_progress": 0.1,
                    "avatar": "default-avatar.png", 
                    "background": "default-bg.png",
                    "avatar_url": None,
                    "is_admin": False,
                    "backgrounds": ["default-bg.png"],
                    "avatars": ["default-avatar.png"]
                }
            
            new_balance = self.users[uid]["balance"] + delta
            self.users[uid]["balance"] = new_balance
            return new_balance

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
        
    def add_experience(self, user_id, win_amount, sender, file_queue):
        with self.lock:
            uid = str(user_id)

            if uid not in self.users:
                logger.info(f"[AppCache] User {uid} not found, creating new user")
                self.users[uid] = {
                    "name": f"User {uid}", 
                    "balance": 50, 
                    "level": 1, 
                    "level_progress": 0.1,
                    "avatar": "default-avatar.png", 
                    "background": "default-bg.png",
                    "avatar_url": None,
                    "is_admin": False,
                    "avatars": ["default-avatar.png"],
                    "backgrounds": ["default-bg.png"]
                }

            user = self.users[uid]

            if win_amount >= 0:
                return user["level"], user["level_progress"]

            loose_amount = abs(win_amount)
            level = user["level"]
            multiplier = 2 + 2 * (level // 20)
            
            progress_increase = round(loose_amount / (multiplier * level), 2)
            
            if progress_increase == 0:
                return user["level"], user["level_progress"]
            
            progress_to_add = progress_increase / 100.0
            
            new_progress = user["level_progress"] + progress_to_add
            
            level_changed = False
            new_level = user["level"]
            
            if new_progress >= 1.0:
                new_level += 1
                level_changed = True
                
                excess_progress = new_progress - 1.0
                
                new_progress = min(excess_progress, 0.99)
                
                logger.info(f"[AppCache] Level up! New level: {new_level}, excess progress: {excess_progress}, new progress: {new_progress}")
            else:
                new_progress = min(new_progress, 0.999)
                logger.info(f"[AppCache] Progress increased to {new_progress}")

            user["level"] = new_level
            user["level_progress"] = new_progress

            if level_changed:
                try:
                    from plugins.avatar import AvatarPlugin

                    plugin = AvatarPlugin()
                    plugin.cache = self

                    import threading
                    def run_level_up():
                        try:
                            result = plugin.on_level_up(user_id, sender, file_queue)
                        except Exception as e:
                            logger.critical(f"[AppCache] ERROR in level up thread: {e}", exc_info=True)

                    thread = threading.Thread(target=run_level_up)
                    thread.daemon = True
                    thread.start()
                    logger.info(f"[AppCache] Avatar roll started in background")

                except Exception as e:
                    logger.critical(f"[EXP] ERROR calling Avatar roll: {e}", exc_info=True)

            return new_level, new_progress
        
    def set_active_math_challenge(self, challenge_data):
        with self.lock:
            self.active_math_challenge = challenge_data

    def get_active_math_challenge(self):
        with self.lock:
            return self.active_math_challenge

    def clear_active_math_challenge(self):
        with self.lock:
            challenge = self.active_math_challenge
            self.active_math_challenge = None
            return challenge