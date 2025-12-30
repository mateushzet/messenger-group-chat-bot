import os
import time
from datetime import datetime, timedelta
from PIL import Image
from base_game_plugin import BaseGamePlugin
from logger import logger

class DailyPlugin(BaseGamePlugin):
    def __init__(self):
        results_folder = self.get_app_path("temp")
        super().__init__(
            game_name="daily",
            results_folder=results_folder,
        )
        
        self.daily_rewards_folder = self.get_asset_path("reward/daily_rewards")
        error_folder = self.get_asset_path("errors")
        self.error_folder = error_folder
        
        os.makedirs(self.results_folder, exist_ok=True)
        
        self.daily_rewards = {
            1: 10,
            2: 20,
            3: 30,
            4: 40,
            5: 50,
            6: 75,
            7: 100
        }

    def _get_daily_reward_image_path(self, day, claimed=False):
        status = "claimed" if claimed else "available"
        filename = f"day_{day}_{status}.webp"
        path = os.path.join(self.daily_rewards_folder, filename)
        
        if os.path.exists(path):
            return path
        
        fallback = f"day_1_{status}.webp"
        fallback_path = os.path.join(self.daily_rewards_folder, fallback)
        
        if os.path.exists(fallback_path):
            return fallback_path
        
        return None

    def _can_claim_daily(self, user_id):
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"
        
        now = datetime.now().date()
        last_daily_date = user.get("last_daily_date")
        
        if not last_daily_date:
            return True, "first"
        
        if isinstance(last_daily_date, str):
            last_daily_date_str = last_daily_date.strip()
            if last_daily_date_str in ["", "None", "none", "null"]:
                return True, "first"
        
        try:
            if isinstance(last_daily_date, str):
                last_date = datetime.fromisoformat(last_daily_date).date()
            elif isinstance(last_daily_date, datetime):
                last_date = last_daily_date.date()
            else:
                return True, "first"
            
            if last_date == now:
                return False, "already_claimed"
            
            yesterday = now - timedelta(days=1)
            if last_date == yesterday:
                return True, "continue"
            
            days_diff = (now - last_date).days
            
            if days_diff > 1:
                return True, "reset"
            else:
                return True, "continue"
                
        except Exception as e:
            return True, "first"

    def _claim_daily_reward(self, user_id):
        user = self.cache.get_user(user_id)
        if not user:
            return None, 1, "User not found"
        
        now = datetime.now()
        today = now.date()
        
        last_daily_date = user.get("last_daily_date")
        current_streak = user.get("daily_streak_day", 0)
        
        if last_daily_date:
            try:
                if isinstance(last_daily_date, str):
                    last_date = datetime.fromisoformat(last_daily_date).date()
                elif isinstance(last_daily_date, datetime):
                    last_date = last_daily_date.date()
                else:
                    last_date = today - timedelta(days=2)
                
                if last_date < today - timedelta(days=1):
                    current_streak = 0
                    
            except Exception as e:
                current_streak = 0
        else:
            current_streak = 0
        
        new_streak = min(current_streak + 1, 7)
        reward_amount = self.daily_rewards.get(new_streak, self.daily_rewards[7])
        
        old_balance = user.get("balance", 0)
        new_balance = old_balance + reward_amount
        self.cache.update_balance(user_id, reward_amount)
        
        self.cache.update_user(
            user_id,
            last_daily_date=now.isoformat(),
            daily_streak_day=new_streak
        )
        
        user["balance"] = new_balance
        user["last_daily_date"] = now.isoformat()
        user["daily_streak_day"] = new_streak
        
        return reward_amount, new_streak, None

    def _get_daily_status_image(self, user_id, claimed=False, just_claimed=False):
        user = self.cache.get_user(user_id)
        if not user:
            return None
        
        streak_day = user.get("daily_streak_day", 0)
        
        if just_claimed:
            day_to_show = streak_day + 1
            if day_to_show > 7:
                day_to_show = 7
            img_path = self._get_daily_reward_image_path(day_to_show, claimed=False)
        elif streak_day == 0 or not claimed:
            day_to_show = max(1, min(streak_day + 1, 7))
            img_path = self._get_daily_reward_image_path(day_to_show, claimed=False)
        else:
            img_path = self._get_daily_reward_image_path(streak_day, claimed=True)
        
        if not img_path or not os.path.exists(img_path):
            return None
        
        try:
            daily_img = Image.open(img_path).convert('RGBA')
        except Exception as e:
            return None
        
        try:
            bg_path = self.cache.get_background_path(user_id)
            if bg_path and os.path.exists(bg_path):
                bg_img = Image.open(bg_path)
                bg_img = bg_img.resize(daily_img.size, Image.LANCZOS)
                final_img = bg_img.convert('RGBA')
                final_img.paste(daily_img, (0, 0), daily_img)
                return final_img
            else:
                return daily_img
        except Exception as e:
            return daily_img

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 0)
        
        if error == "Invalid user":
            self._send_error_image("validation_error", sender, file_queue)
            return ""
        elif error:
            self._send_error_image("insufficient_funds", sender, file_queue)
            return ""
        
        nickname = sender
        
        can_claim, claim_status = self._can_claim_daily(user_id)
        
        if not can_claim:
            daily_img = self._get_daily_status_image(user_id, claimed=True)
            if daily_img:
                img_path = os.path.join(self.results_folder, f"daily_status_{user_id}.webp")
                daily_img.save(img_path, format='WEBP', quality=85, optimize=True)
                
                overlay_path, error = self.apply_user_overlay(
                    img_path, user_id, nickname, 0, 0, user["balance"], user
                )
                if overlay_path:
                    file_queue.put(overlay_path)
            
            streak_day = user.get("daily_streak_day", 0)
            tomorrow = datetime.now() + timedelta(days=1)
            
            if claim_status == "already_claimed":
                return f"Daily Reward (Already claimed today)\nStreak: Day {streak_day}/7\nNext: {tomorrow.strftime('%d/%m')}"
            else:
                return f"Daily Reward\nCannot claim\nStreak: Day {streak_day}/7"
        
        reward_amount, new_streak, error = self._claim_daily_reward(user_id)
        if error:
            self._send_error_image("reward_error", nickname, file_queue, error)
            return ""
        
        day_to_show = new_streak
        
        img_path = self._get_daily_reward_image_path(day_to_show, claimed=False)
        if not img_path or not os.path.exists(img_path):
            img_path = self._get_daily_reward_image_path(1, claimed=False)
        
        if not img_path:
            self._send_error_image("image_generation_error", nickname, file_queue)
            return ""
        
        try:
            daily_img = Image.open(img_path).convert('RGBA')
            
            try:
                bg_path = self.cache.get_background_path(user_id)
                if bg_path and os.path.exists(bg_path):
                    bg_img = Image.open(bg_path)
                    bg_img = bg_img.resize(daily_img.size, Image.LANCZOS)
                    final_img = bg_img.convert('RGBA')
                    final_img.paste(daily_img, (0, 0), daily_img)
                    daily_img = final_img
            except Exception as e:
                pass
                
        except Exception as e:
            self._send_error_image("image_generation_error", nickname, file_queue)
            return ""
        
        output_path = os.path.join(self.results_folder, f"daily_{user_id}_{int(time.time())}.webp")
        daily_img.save(output_path, format='WEBP', quality=85, optimize=True)
        
        user = self.cache.get_user(user_id)
        
        overlay_path, error = self.apply_user_overlay(
            output_path, user_id, nickname, reward_amount, reward_amount, 
            user.get("balance", 0) if user else 0, user
        )
        if overlay_path:
            file_queue.put(overlay_path)
        
        if claim_status == "first":
            return f"First Daily Reward!\n+{reward_amount} coins\nNew streak: Day {new_streak}/7"
        elif claim_status == "continue":
            return f"Daily Reward Claimed!\n+{reward_amount} coins\nStreak: Day {new_streak}/7"
        else:
            return f"Daily Reward (Streak Reset)\n+{reward_amount} coins\nNew streak: Day 1/7"

    def check_daily_images(self):
        if not os.path.exists(self.daily_rewards_folder):
            return
        
        files = os.listdir(self.daily_rewards_folder)
        
        for day in range(1, 8):
            for claimed in [False, True]:
                status = "claimed" if claimed else "available"
                filename = f"day_{day}_{status}.webp"
                path = os.path.join(self.daily_rewards_folder, filename)
                exists = os.path.exists(path)

def register():
    plugin = DailyPlugin()
    return {
        "name": "daily",
        "aliases": ["/daily", "/d"],
        "description": "Claim your daily reward and maintain streak",
        "execute": plugin.execute_game
    }