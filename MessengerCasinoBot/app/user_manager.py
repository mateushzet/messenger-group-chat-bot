import requests
import os
from logger import logger
from urllib.parse import urlparse
from PIL import Image

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
    
    def _is_url(self, value):
        if not value:
            return False
        parsed = urlparse(str(value))
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    def _remote_image_available(self, avatar_url):
        try:
            response = requests.get(avatar_url, timeout=5, stream=True)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if content_type and not content_type.startswith("image/"):
                logger.warning(f"[UserManager] Avatar URL is not an image: {avatar_url} ({content_type})")
                return False

            return True
        except Exception as e:
            logger.info(f"[UserManager] Stored avatar URL is not reachable: {avatar_url} ({e})")
            return False

    def _stored_avatar_available(self, user_data):
        avatar_url = user_data.get("avatar_url")
        if self._is_url(avatar_url):
            return self._remote_image_available(avatar_url)
        return False

    def _update_user_avatar(self, user_id, name, avatar_url):
        default_filename = f"default_{user_id}.png"

        downloaded = self.download_avatar_as(avatar_url, default_filename)
        if not downloaded:
            return False, f"Failed to download new avatar for user {name}"

        update_fields = {
            "avatar_url": avatar_url,
        }

        self.cache.update_user(user_id, **update_fields)
        return True, f"Avatar updated for existing user: {name}"

    def find_user_by_name_avatar(self, name, avatar_url):
        if not self.cache:
            return None, None

        name_lower = name.lower()
        avatar_filename = self._extract_filename_from_url(avatar_url)

        for user_id, user_data in self.cache.users.items():
            if user_data.get("name", "").lower() != name_lower:
                continue

            stored_url = user_data.get("avatar_url", "")
            if stored_url and self._extract_filename_from_url(stored_url) == avatar_filename:
                return user_id, user_data

            if user_data.get("avatar") == avatar_filename:
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
        user_id = str(self.next_user_id)
        default_filename = f"default_{user_id}.png"

        downloaded = self.download_avatar_as(avatar_url, default_filename)
        if not downloaded:
            return False, f"Failed to download avatar for {name}"

        self.cache.set_user(
            user_id,
            name=name,
            balance=50,
            level=1,
            level_progress=0.1,
            avatar=default_filename,
            avatar_url=avatar_url,
            avatars=[],
            background="default-bg.png",
            is_admin=is_admin
        )
        self.next_user_id += 1
        return True, "User created successfully"

    def download_avatar_as(self, avatar_url, filename):
        filepath = os.path.join(AVATARS_FOLDER, filename)
        try:
            response = requests.get(avatar_url, timeout=10)
            response.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return filename
        except Exception as e:
            logger.error(f"[UserManager] Error downloading avatar as {filename}: {e}")
            return None

    def create_user(self, name, avatar_url, is_admin=False):
        if not self.cache or not name or not avatar_url:
            logger.warning(f"[UserManager] Create User: Missing required data ")
            return False, "Missing required data"

        try:
            existing_user_id, existing_user = self.find_user_by_name_avatar(name, avatar_url)
            if existing_user:
                if existing_user.get("avatar_url") != avatar_url:
                    self.cache.update_user(existing_user_id, avatar_url=avatar_url)
                    logger.info(
                        f"[UserManager] Refreshed avatar_url for user '{name}' (ID: {existing_user_id})"
                    )
                return True, "User exists"
            
            existing_users_with_same_name = self.find_users_by_name(name)
            
            if existing_users_with_same_name and len(existing_users_with_same_name) > 0:
                user_to_update = None
                users_info = []
                
                for user_id, user_data in existing_users_with_same_name:
                    avatar = user_data.get('avatar', 'unknown')
                    avatar_url_field = user_data.get('avatar_url', 'unknown')
                    balance = user_data.get('balance', 0)
                    
                    users_info.append(f"- ID: {user_id} (avatar: {avatar}, balance: {balance})")
                    
                    if avatar == "TO_BE_UPDATED" or avatar_url_field == "TO_BE_UPDATED":
                        user_to_update = (user_id, user_data)
                        logger.info(f"[UserManager] Found user {user_id} marked for avatar update")
                
                if user_to_update:
                    user_id, user_data = user_to_update
                    return self._update_user_avatar(user_id, name, avatar_url)
                else:
                    stale_avatar_users = []
                    for user_id, user_data in existing_users_with_same_name:
                        if not self._stored_avatar_available(user_data):
                            stale_avatar_users.append((user_id, user_data))

                    if len(stale_avatar_users) == 1:
                        user_id, user_data = stale_avatar_users[0]
                        logger.info(
                            f"[UserManager] Existing avatar for '{name}' (ID: {user_id}) is unavailable; "
                            "assuming avatar was changed"
                        )
                        return self._update_user_avatar(user_id, name, avatar_url)

                    if len(stale_avatar_users) > 1:
                        stale_ids = ", ".join(user_id for user_id, _ in stale_avatar_users)
                        logger.warning(
                            f"[UserManager] Multiple users named '{name}' have unavailable avatars: {stale_ids}. "
                            "Manual avatar update is required."
                        )
                        return False, f"Multiple users named '{name}' have unavailable avatars: {stale_ids}"

                    logger.info(
                        f"[UserManager] Name '{name}' exists with a live avatar, but a new avatar URL arrived. "
                        f"Treating as a NEW user with the same name."
                    )
                    return self._create_new_user(name, avatar_url, is_admin=False)
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

    def admin_set_avatar(self, name, old_avatar_url, new_avatar_url):
        user_id = None
        user_data = None

        name_lower = name.lower()
        old_filename = self._extract_filename_from_url(old_avatar_url)

        for uid, data in self.cache.users.items():
            if (data.get("name", "").lower() == name_lower
                and (data.get("avatar_url") == old_avatar_url
                    or data.get("avatar") == old_filename)):
                user_id, user_data = uid, data
                break

        if not user_data:
            logger.warning(f"[UserManager] No user found with name: {name} and avatar: {old_avatar_url}")
            return False, f"No user found with name: {name} and avatar: {old_avatar_url}"

        default_filename = f"default_{user_id}.png"
        downloaded = self.download_avatar_as(new_avatar_url, default_filename)
        if not downloaded:
            return False, f"Failed to download new avatar"

        self.cache.update_user(
            user_id,
            avatar_url=new_avatar_url
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

    def admin_mark_avatar_for_update(self, user_id):
        
        if user_id not in self.cache.users:
            logger.warning(f"[UserManager] User not found: {user_id}")
            return False, f"User not found: {user_id}"
        
        self.cache.update_user(user_id, avatar_url="TO_BE_UPDATED")
        logger.info(f"[UserManager] User ID: {user_id} marked for avatar update")
        return True, f"User {user_id} marked for avatar update"

    def set_user_admin(self, name, avatar_url, is_admin=True):
        user_id, user_data = self.find_user_by_name_avatar(name, avatar_url)
        
        if not user_data:
            return False, f"User not found: {name}"
        
        self.cache.update_user(user_id, is_admin=is_admin)
        
        action = "granted" if is_admin else "revoked"
        return True, f"Admin privileges {action} for user: {name}"
    
    def find_user_by_id(self, user_id_input):
        user_id_str = str(user_id_input)
        if user_id_str in self.cache.users:
            return user_id_str, self.cache.users[user_id_str]
        
        return None, None
