import os
import random
import time
from datetime import datetime, timedelta
from base_game_plugin import BaseGamePlugin
from logger import logger
from PIL import Image, ImageDraw, ImageFont

class HourlyPlugin(BaseGamePlugin):
    def __init__(self):
        results_folder = self.get_app_path("temp")
        super().__init__(
            game_name="hourly",
            results_folder=results_folder,
        )
        
        self.hourly_anim_folder = self.get_asset_path("reward/hourly")
        error_folder = self.get_asset_path("errors")
        self.error_folder = error_folder

        os.makedirs(self.results_folder, exist_ok=True)
        
        self.min_reward = 10
        self.max_reward = 100
        self.avg_target = 30
        
        self.new_balance_frames = 20

    def _calculate_probabilities(self):
        rewards = list(range(self.min_reward, self.max_reward + 1, 10))
        avg = self.avg_target
        
        probs = []
        for reward in rewards:
            distance = abs(reward - avg)
            prob = max(0.05, 0.3 * (1 - distance / (self.max_reward - self.min_reward)))
            probs.append(prob)
        
        total = sum(probs)
        normalized_probs = [p/total for p in probs]
        
        return list(zip(rewards, normalized_probs))

    def _get_random_reward(self, user_id=None):
        rewards, probs = zip(*self._calculate_probabilities())
        return random.choices(rewards, weights=probs, k=1)[0]

    def _get_hourly_animation_path(self, reward_amount):
        if not os.path.exists(self.hourly_anim_folder):
            logger.error(f"[Hourly] Hourly animation folder not found: {self.hourly_anim_folder}")
            return None
        
        target_files = []
        for file in os.listdir(self.hourly_anim_folder):
            if file.lower().endswith('.webp'):
                if f"_{reward_amount:03d}" in file or f"_{reward_amount}" in file:
                    target_files.append(file)
                elif f"_{reward_amount}" in file:
                    target_files.append(file)
        
        if target_files:
            return os.path.join(self.hourly_anim_folder, target_files[0])
        
        for file in os.listdir(self.hourly_anim_folder):
            if file.lower().endswith('.webp') and file.startswith('reward_'):
                return os.path.join(self.hourly_anim_folder, file)
        
        for file in os.listdir(self.hourly_anim_folder):
            if file.lower().endswith('.webp'):
                return os.path.join(self.hourly_anim_folder, file)
        
        logger.error(f"[Hourly] No webp animation found in: {self.hourly_anim_folder}")
        return None

    def _can_claim_hourly(self, user_id):
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"
        
        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        last_hourly = user.get("last_hourly_claim")
        if last_hourly:
            last_claim_time = datetime.fromisoformat(last_hourly)
            if last_claim_time >= current_hour:
                next_hour = current_hour + timedelta(hours=1)
                wait_time = next_hour - now
                wait_minutes = int(wait_time.total_seconds() / 60)
                return False, f"Wait {wait_minutes} min"
        
        current_minute = now.minute
        if current_minute > 1:
            next_full_hour = current_hour + timedelta(hours=1)
            time_to_next = next_full_hour - now
            minutes_to_next = int(time_to_next.total_seconds() / 60)
            return False, f"Available in {minutes_to_next} min"
        
        return True, "Available"

    def _claim_hourly_reward(self, user_id):
        user = self.cache.get_user(user_id)
        if not user:
            return None, "User not found"
        
        reward_amount = self._get_random_reward(user_id)
        logger.info(f"[Hourly] Hourly reward for user {user_id}: {reward_amount} coins")
        
        self.cache.update_balance(user_id, reward_amount)
        
        now = datetime.now().isoformat()
        self.cache.update_user(user_id, last_hourly_claim=now)
        
        user["balance"] = user.get("balance", 0) + reward_amount
        user["last_hourly_claim"] = now
        
        return reward_amount, None

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 0)
        
        if error == "Invalid user":
            self.send_message_image(sender, file_queue, "Invalid user!", "Validation Error", cache, user_id)
            return ""
        elif error:
            self.send_message_image(sender, file_queue, "Insufficient funds!", "Error", cache, user_id)
            return ""
        
        nickname = sender
        
        can_claim, message = self._can_claim_hourly(user_id)

        can_claim = True

        if not can_claim:
            self.send_message_image(sender, file_queue, f"Hourly reward not available!\n{message}\n Hourly reward can only be claimed once at full hour.", "Hourly Reward", cache, user_id)
            return ""

        balance_before = user.get("balance", 0)
        
        reward_amount = self._get_random_reward(user_id)
        logger.info(f"[Hourly] Hourly reward for {nickname}: {reward_amount}, balance before: {balance_before}")
        
        self.cache.update_balance(user_id, reward_amount)
        
        now = datetime.now().isoformat()
        self.cache.update_user(user_id, last_hourly_claim=now)
        
        user = self.cache.get_user(user_id)
        balance_after = user["balance"]
        
        if balance_after > balance_before + reward_amount:
            logger.warning(f"Correcting double reward: {balance_after} -> {balance_before + reward_amount}")
            correct_balance = balance_before + reward_amount
            self.cache.update_user(user_id, balance=correct_balance)
            user["balance"] = correct_balance
            balance_after = correct_balance
        
        user_info_before = self.create_user_info(
            nickname, 0, 0, balance_before, user
        )
        
        user_info_after = self.create_user_info(
            nickname, 0, 0, balance_after, user
        )
        
        anim_path = self._get_hourly_animation_path(reward_amount)
        if not anim_path:
            logger.error(f"[Hourly] No animation found for reward {reward_amount}")
            self.send_message_image(sender, file_queue, "Animation error!\nPlease try again later.", "Error", cache, user_id)
            return ""
        
        logger.info(f"Using animation: {os.path.basename(anim_path)}")
        
        result_path, error = self.generate_animation(
            anim_path, 
            user_id, 
            user, 
            user_info_before, 
            user_info_after,
            animated=True,
            game_type="hourly",
            avatar_size=80,
            show_bet_amount=False,
            frame_duration=60,
            last_frame_multiplier=30.0,
            show_win_text=False
        )
        
        if not result_path or error:
            logger.error(f"[Hourly] Animation generation error: {error}")
            self.send_message_image(sender, file_queue, f"Animation generation failed!\nError: {error}", "Error", cache, user_id)
            return ""
        
        file_queue.put(result_path)
        
        now = datetime.now()
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        next_time = next_hour.strftime("%H:%M")
        
        return f"Hourly Reward! +{reward_amount} coins, Next: {next_time}"

def register():
    plugin = HourlyPlugin()
    return {
        "name": "hourly",
        "aliases": ["/hourly", "/h"],
        "description": "Claim hourly reward at full hour ±1 minute\nHourly can only be claimed once per hour",
        "execute": plugin.execute_game
    }