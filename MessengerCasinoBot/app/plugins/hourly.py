import os
import random
from datetime import datetime, timedelta
from base_game_plugin import BaseGamePlugin
from logger import logger

class HourlyPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="hourly"
        )
        
        self.hourly_anim_folder = self.get_asset_path("reward/hourly")
        
        self.min_reward = 10
        self.max_reward = 100
        self.avg_target = 30

    def _calculate_probabilities(self, max_reward=None):
        if max_reward is None:
            max_reward = self.max_reward
        
        rewards = list(range(self.min_reward, max_reward + 1, 10))
        avg = self.avg_target
        
        probs = []
        for reward in rewards:
            distance = abs(reward - avg)
            prob = max(0.05, 0.3 * (1 - distance / max((max_reward - self.min_reward),10)))
            probs.append(prob)
        
        total = sum(probs)
        normalized_probs = [p/total for p in probs]
        
        return list(zip(rewards, normalized_probs))

    def _get_random_reward(self, max_reward=None):
        if max_reward is None:
            max_reward = self.max_reward
            
        rewards, probs = zip(*self._calculate_probabilities(max_reward))
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
                return False, ""
        
        current_minute = now.minute
        if current_minute > 1:
            return False, ""
        
        return True, "Available"

    def _update_claim_time(self, user_id, claim_time):
        self.cache.update_user(user_id, last_hourly_claim=claim_time.isoformat())
        
        user = self.cache.get_user(user_id)
        if user:
            user["last_hourly_claim"] = claim_time.isoformat()

    def _claim_hourly_reward(self, user_id):
        user = self.cache.get_user(user_id)
        if not user:
            return None
        
        reward_amount = self._get_random_reward()
        
        logger.info(f"[Hourly] Hourly reward for user {user_id}: {reward_amount} coins")
        
        current_time = datetime.now()
        
        self._update_claim_time(user_id, current_time)
        
        self.cache.update_balance(user_id, reward_amount)
        
        user["balance"] = user.get("balance", 0) + reward_amount
        
        return reward_amount

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

        if not can_claim:
            self.send_message_image(sender, file_queue, f"Hourly reward not available!\n Hourly reward can only be claimed once at full hour.", "Hourly Reward", cache, user_id)
            return ""

        balance_before = user.get("balance", 0)
        
        reward_amount = self._claim_hourly_reward(user_id)
        
        logger.info(f"[Hourly] Hourly reward for {nickname}: {reward_amount}, balance before: {balance_before}")
        
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
            avatar_size=48,
            font_scale=0.7,
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
        
        message = f"Hourly Reward! +{reward_amount} coins\nNext: {next_time}"
        
        return message

def register():
    plugin = HourlyPlugin()
    return {
        "name": "hourly",
        "aliases": ["/hourly", "/h", "/hour"],
        "description": "Claim hourly reward at full hour ±1 minute\nHourly can only be claimed once per hour",
        "execute": plugin.execute_game
    }