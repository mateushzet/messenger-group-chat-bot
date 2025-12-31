import os
import random
import time
from datetime import datetime, timedelta
from base_game_plugin import BaseGamePlugin
from logger import logger
from PIL import Image, ImageDraw, ImageFont
from utils import _get_unique_id

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

    def _get_random_reward(self):
        rewards, probs = zip(*self._calculate_probabilities())
        return random.choices(rewards, weights=probs, k=1)[0]

    def _get_hourly_animation_path(self, reward_amount):
        if not os.path.exists(self.hourly_anim_folder):
            logger.error(f"Hourly animation folder not found: {self.hourly_anim_folder}")
            return None
        
        reward_str = f"{reward_amount:03d}"
        
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
        
        logger.error(f"No webp animation found in: {self.hourly_anim_folder}")
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
        
        reward_amount = self._get_random_reward()
        logger.info(f"Hourly reward for user {user_id}: {reward_amount} coins")
        
        self.cache.update_balance(user_id, reward_amount)
        
        now = datetime.now().isoformat()
        self.cache.update_user(user_id, last_hourly_claim=now)
        
        user["balance"] = user.get("balance", 0) + reward_amount
        user["last_hourly_claim"] = now
        
        return reward_amount, None

    def _modify_animation_for_last_frames(self, anim_path, reward_amount, output_path, 
                                         user_id, user_info_before, user_info_after):
        try:
            anim = Image.open(anim_path)
            n_frames = getattr(anim, "n_frames", 1)
            
            if n_frames == 1:
                return self.generate_animation(
                    anim_path, 
                    user_id, 
                    {},
                    user_info_before, 
                    user_info_after,
                    animated=False
                )
            
            avatar_path = self.cache.get_avatar_path(user_id)
            bg_path = self.cache.get_background_path(user_id)
            
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            frames = []
            durations = []
            
            start_new_balance = max(0, n_frames - self.new_balance_frames)
            
            for frame_idx in range(n_frames):
                anim.seek(frame_idx)
                frame = anim.convert("RGBA")
                
                if frame_idx < start_new_balance:
                    current_user_info = user_info_before
                    balance_text = f"${user_info_before['balance']}"
                else:
                    current_user_info = user_info_after
                    balance_text = f"${user_info_after['balance']}"
                
                try:
                    temp_result = self.apply_user_overlay(
                        anim_path,
                        user_id,
                        current_user_info["username"],
                        0,
                        current_user_info["balance"] - user_info_before["balance"],
                        current_user_info["balance"],
                        {"level": current_user_info["level"], "level_progress": current_user_info.get("level_progress", 0.1)}
                    )
                    
                    if temp_result and os.path.exists(temp_result[0]):
                        overlay_img = Image.open(temp_result[0]).convert("RGBA")
                        frames.append(overlay_img)
                    else:
                        draw = ImageDraw.Draw(frame)
                        text_width = font.getbbox(balance_text)[2] - font.getbbox(balance_text)[0]
                        x = frame.width - text_width - 20
                        y = 20
                        draw.rectangle([x-5, y-5, x+text_width+5, y+20], fill=(0,0,0,180))
                        draw.text((x, y), balance_text, font=font, fill=(0,255,0,255))
                        frames.append(frame)
                        
                except Exception as e:
                    logger.error(f"Error applying user overlay: {e}")
                    draw = ImageDraw.Draw(frame)
                    text_width = font.getbbox(balance_text)[2] - font.getbbox(balance_text)[0]
                    x = frame.width - text_width - 20
                    y = 20
                    draw.rectangle([x-5, y-5, x+text_width+5, y+20], fill=(0,0,0,180))
                    draw.text((x, y), balance_text, font=font, fill=(0,255,0,255))
                    frames.append(frame)
                
                durations.append(anim.info.get("duration", 100))
            
            anim.close()
            
            if len(frames) > 1:
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=durations,
                    loop=0,
                    format="WEBP",
                    quality=85
                )
            else:
                frames[0].save(output_path, format="WEBP", quality=85)
            
            return output_path, None
            
        except Exception as e:
            logger.error(f"Error modifying animation: {e}")
            return None, str(e)

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
        
        can_claim, message = self._can_claim_hourly(user_id)

        if not can_claim:
            self._send_error_image("hourly_not_available", nickname, file_queue, message)
            return ""

        balance_before = user.get("balance", 0)
        logger.info(f"Balance before for {nickname}: {balance_before}")
        
        reward_amount = self._get_random_reward()
        logger.info(f"Hourly reward for {nickname}: {reward_amount}")
        
        self.cache.update_balance(user_id, reward_amount)
        
        now = datetime.now().isoformat()
        self.cache.update_user(user_id, last_hourly_claim=now)
        
        user = self.cache.get_user(user_id)
        balance_after = user["balance"]
        
        logger.info(f"Reward amount for {nickname}: {reward_amount}")
        logger.info(f"Balance after for {nickname}: {balance_after}")
        
        if balance_after > balance_before + reward_amount:
            logger.warning(f"Correcting double reward: {balance_after} -> {balance_before + reward_amount}")
            correct_balance = balance_before + reward_amount
            self.cache.update_user(user_id, balance=correct_balance)
            user["balance"] = correct_balance
            balance_after = correct_balance
        
        user_info_before = self.create_user_info(
            nickname, 0, 0, balance_before, user.copy()
        )
        
        newLevel, newLevelProgress = self.cache.add_experience(
            user_id, reward_amount, nickname, file_queue
        )
        
        user["level"] = newLevel
        user["level_progress"] = newLevelProgress
        
        user_info_after = self.create_user_info(
            nickname, 0, 0, balance_after, user
        )
        
        anim_path = self._get_hourly_animation_path(reward_amount)
        if not anim_path:
            logger.error(f"No animation found for reward {reward_amount}")
            self._send_error_image("animation_error", nickname, file_queue)
            return ""
        
        logger.info(f"Using animation: {os.path.basename(anim_path)}")
        
        result_path, error = self.generate_animation(
            anim_path, 
            user_id, 
            user, 
            user_info_before, 
            user_info_after,
            animated=True,
            game_type="hourly"
        )
        
        if not result_path or error:
            logger.error(f"Animation generation error: {error}")
            self._send_error_image("animation_error", nickname, file_queue, error)
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
        "description": "Claim hourly reward (full hour ±1 minute)",
        "execute": plugin.execute_game
    }