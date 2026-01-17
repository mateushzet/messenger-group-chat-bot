import requests
import os
from logger import logger
from urllib.parse import urlparse

BASE_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
AVATARS_FOLDER = os.path.join(ASSETS_DIR, "avatars")

os.makedirs(AVATARS_FOLDER, exist_ok=True)

class UserManager:
    def __init__(self, cache):
        self.cache = cache
        self.next_user_id = self._get_next_user_id()
    
    def _get_next_user_id(self):
        max_id = 0
        if hasattr(self.cache, 'users'):
            for user_id in self.cache.users.keys():
                try:
                    user_id_num = int(user_id)
                    if user_id_num > max_id:
                        max_id = user_id_num
                except ValueError:
                    continue
        return max_id + 1
    
    def _extract_filename_from_url(self, url):
        if not url:
            return ""
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        return filename.lower()
    
    def download_avatar(self, avatar_url):
        try:
            filename = self._extract_filename_from_url(avatar_url)
            filepath = os.path.join(AVATARS_FOLDER, filename)
            
            if os.path.exists(filepath):
                return filename
            
            response = requests.get(avatar_url, timeout=10)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return filename
            
        except Exception as e:
            logger.error(f"[UserManager] Error downloading avatar from {avatar_url}: {e}", exc_info=True)
            return None

    def find_user_by_name_avatar(self, name, avatar_url):
        if not self.cache:
            return None, None
        
        avatar_filename = self._extract_filename_from_url(avatar_url)
        
        for user_id, user_data in self.cache.users.items():
            if user_data.get("name") == name and user_data.get("avatar_url") == avatar_filename:
                return user_id, user_data
        
        logger.warning(f"[UserManager] No user found with name {name} and avatar {avatar_filename}")
        return None, None
    
    def find_users_by_name(self, name, exclude_avatar_filename=None):
        if not self.cache:
            return []

        users_with_same_name = []
        
        for user_id, user_data in self.cache.users.items():
            if user_data.get("name") == name:
                if exclude_avatar_filename:
                    if user_data.get("avatar_url") != exclude_avatar_filename:
                        users_with_same_name.append((user_id, user_data))
                else:
                    users_with_same_name.append((user_id, user_data))
        
        return users_with_same_name

    def _create_new_user(self, name, avatar_url, is_admin=False):
        avatar_filename = self.download_avatar(avatar_url)
        
        if not avatar_filename:
            return False, f"Failed to download avatar for {name}"
        
        user_id = str(self.next_user_id)
        
        self.cache.set_user(
            user_id,
            name=name,
            balance=50,
            level=1, 
            level_progress=0.1,
            avatar=avatar_filename,
            avatar_url=avatar_filename,
            avatars=[avatar_filename],
            background="default-bg.png",
            is_admin=is_admin
        )
        
        self.next_user_id += 1
        
        logger.info(f"[UserManager] User created successfully")
        return True, "User created successfully"

    def create_user(self, name, avatar_url, is_admin=False):
        if not self.cache or not name or not avatar_url:
            logger.warning(f"[UserManager] Create User: Missing required data ")
            return False, "Missing required data"
        
        avatar_filename = self._extract_filename_from_url(avatar_url)

        try:
            existing_user_id, existing_user = self.find_user_by_name_avatar(name, avatar_url)
            if existing_user:
                return True, "User exists"
            
            existing_users_with_same_name = self.find_users_by_name(name, avatar_filename)
            
            if existing_users_with_same_name and len(existing_users_with_same_name) > 0:
                users_info = []
                for user_id, user_data in existing_users_with_same_name:
                    avatar = user_data.get('avatar', 'unknown') if user_data else 'unknown'
                    balance = user_data.get('balance', 0) if user_data else 0
                    
                    users_info.append(f"- ID: {user_id} (avatar: {avatar}, balance: {balance})")
                
                users_list = "\n".join(users_info)

                logger.warning(f"[UserManager] Different avatar detected for user '{name}'. Existing users with same name: {users_list}")
                return False, f"Different avatar detected for user '{name}'. Existing users with same name: {users_list}"
            else:
                return self._create_new_user(name, avatar_url, is_admin)
                
        except Exception as e:
            logger.error(f"[UserManager] Error creating user {name}: {e}", exc_info=True)
            return False, f"Error: {str(e)}"

    def get_user_avatar_path(self, user_id):
        user = self.cache.get_user(user_id) if self.cache else None
        if user and user.get("avatar"):
            avatar_filename = user["avatar"]
            return os.path.join(AVATARS_FOLDER, avatar_filename)
        return None

    def admin_set_avatar(self, name, old_avatar_filename, new_avatar_url):
        user_id = None
        user_data = None
        
        for uid, data in self.cache.users.items():
            if data.get("name") == name and data.get("avatar_url") == old_avatar_filename:
                user_id, user_data = uid, data
                break
        
        if not user_data:
            logger.warning(f"[UserManager] No user found with name: {name} and avatar: {old_avatar_filename}")
            return False, f"No user found with name: {name} and avatar: {old_avatar_filename}"
        
        new_avatar_filename = self.download_avatar(new_avatar_url)
        if not new_avatar_filename:
            return False, f"Failed to download new avatar"
        
        self.cache.update_user(
            user_id,
            avatar=new_avatar_filename
        )
        
        return True, f"Avatar updated for user: {name} (ID: {user_id})"

    def admin_add_user(self, name, avatar_url, is_admin=False):
        if not self.cache or not name or not avatar_url:
            return False, "Missing required data"
        
        try:
            return self._create_new_user(name, avatar_url, is_admin)
        except Exception as e:
            logger.error(f"[UserManager] Error creating user {name}: {e}",exc_info=True)
            return False, f"Error: {str(e)}"
        
    def set_user_admin(self, name, avatar_url, is_admin=True):
        user_id, user_data = self.find_user_by_name_avatar(name, avatar_url)
        
        if not user_data:
            return False, f"User not found: {name}"
        
        self.cache.update_user(user_id, is_admin=is_admin)
        
        action = "granted" if is_admin else "revoked"
        return True, f"Admin privileges {action} for user: {name}"