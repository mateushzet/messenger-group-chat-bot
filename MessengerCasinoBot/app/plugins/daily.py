import os
import time
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
from dataclasses import dataclass
from typing import Tuple, List
from base_game_plugin import BaseGamePlugin

@dataclass
class DailyConfig:
    width: int = 600
    height: int = 250
    tile_size: int = 75
    tile_spacing: int = 12
    tile_radius: int = 10
    webp_quality: int = 90
    glow_size: int = 10
    glow_intensity: float = 0.8

@dataclass
class DailyColors:
    background_top: int = 20
    background_bottom_offset: int = 20
    
    background: Tuple[int, int, int, int] = (0, 0, 0, 200)
    tile_available: Tuple[int, int, int, int] = (70, 70, 90, 255)
    tile_claimed: Tuple[int, int, int, int] = (50, 120, 50, 255)
    tile_current: Tuple[int, int, int, int] = (255, 200, 50, 255)
    tile_just_claimed: Tuple[int, int, int, int] = (100, 100, 120, 255)
    tile_border: Tuple[int, int, int, int] = (120, 120, 140, 255)
    title_color: Tuple[int, int, int, int] = (255, 220, 100, 255)
    reward_color: Tuple[int, int, int, int] = (255, 200, 50, 255)
    text_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    status_color: Tuple[int, int, int, int] = (200, 200, 220, 255)
    glow_color: Tuple[int, int, int, int] = (255, 220, 80, 180)

class DailyImageGenerator:
    def __init__(self, text_renderer):
        self.config = DailyConfig()
        self.colors = DailyColors()
        self.text_renderer = text_renderer
    
    def draw_strong_glow(self, draw, x, y, size):
        glow_color = self.colors.glow_color
        
        for i in range(self.config.glow_size, 0, -1):
            alpha = int(glow_color[3] * (i / self.config.glow_size) * self.config.glow_intensity)
            current_glow = (glow_color[0], glow_color[1], glow_color[2], alpha)
            
            glow_rect = [
                x - i, y - i,
                x + size + i, y + size + i
            ]
            
            draw.rounded_rectangle(
                glow_rect,
                radius=self.config.tile_radius + i//2,
                fill=current_glow
            )
        
        draw.rounded_rectangle(
            [x - 2, y - 2, x + size + 2, y + size + 2],
            radius=self.config.tile_radius + 2,
            outline=(255, 240, 150, 200),
            width=1
        )
    
    def generate_daily_image(self, 
                           current_day: int,
                           claimed_days: List[int],
                           reward_amount: int,
                           streak: int,
                           level: int = 1,
                           claimed_today: bool = False,
                           just_claimed: bool = False) -> Image.Image:
        bg_height = self.config.height - 2 * self.colors.background_top
        img = Image.new("RGBA", (self.config.width, self.config.height), 
                       (0, 0, 0, 0))
        
        draw = ImageDraw.Draw(img)
        draw.rectangle(
            [0, self.colors.background_top, 
             self.config.width, self.config.height - self.colors.background_top],
            fill=self.colors.background
        )
        
        if claimed_today:
            title = "ALREADY CLAIMED"
            title_y = 35
        else:
            title = "DAILY REWARD"
            title_y = 35
        
        title_img = self.text_renderer.render_text(
            text=title,
            font_size=30,
            color=self.colors.title_color,
            stroke_width=2,
            stroke_color=(0, 0, 0, 200),
            shadow=True,
            shadow_color=(0, 0, 0, 180),
            shadow_offset=(1, 1)
        )
        
        title_x = (self.config.width - title_img.width) // 2
        img.paste(title_img, (title_x, title_y), title_img)
        
        if not claimed_today and reward_amount > 0:
            reward_text = f"+${reward_amount}"
            reward_img = self.text_renderer.render_text(
                text=reward_text,
                font_size=36,
                color=self.colors.reward_color,
                stroke_width=2,
                stroke_color=(0, 0, 0, 200),
                shadow=True,
                shadow_color=(0, 0, 0, 180),
                shadow_offset=(1, 1)
            )
            
            reward_x = (self.config.width - reward_img.width) // 2
            reward_y = title_y + title_img.height + 10
            img.paste(reward_img, (reward_x, reward_y), reward_img)
        
        if claimed_today:
            status_text = "COMEBACK TOMORROW"
            status_img = self.text_renderer.render_text(
                text=status_text,
                font_size=22,
                color=self.colors.status_color,
                stroke_width=1,
                stroke_color=(0, 0, 0, 200)
            )
            
            status_x = (self.config.width - status_img.width) // 2
            status_y = title_y + title_img.height + 15
            img.paste(status_img, (status_x, status_y), status_img)
        
        tiles_start_y = 120
        total_tiles_width = 7 * self.config.tile_size + 6 * self.config.tile_spacing
        tiles_start_x = (self.config.width - total_tiles_width) // 2
        
        if just_claimed and not claimed_today:
            for day in range(1, 8):
                tile_x = tiles_start_x + (day - 1) * (self.config.tile_size + self.config.tile_spacing)
                tile_y = tiles_start_y
                
                if day == current_day:
                    self.draw_strong_glow(draw, tile_x, tile_y, self.config.tile_size)
        
        for day in range(1, 8):
            tile_x = tiles_start_x + (day - 1) * (self.config.tile_size + self.config.tile_spacing)
            tile_y = tiles_start_y
            
            day_reward = self._calculate_day_reward(day, level)
            
            if day in claimed_days:
                if just_claimed and day == current_day and not claimed_today:
                    tile_color = self.colors.tile_just_claimed
                else:
                    tile_color = self.colors.tile_claimed
                day_text = f"DAY {day}"
                reward_text = f"${day_reward}"
            elif day == current_day:
                if claimed_today:
                    tile_color = self.colors.tile_claimed
                else:
                    tile_color = self.colors.tile_current
                day_text = f"DAY {day}"
                reward_text = f"${reward_amount}" if not claimed_today else f"${day_reward}"
            else:
                tile_color = self.colors.tile_available
                day_text = f"DAY {day}"
                reward_text = f"${day_reward}"
            
            draw.rounded_rectangle(
                [tile_x, tile_y, 
                 tile_x + self.config.tile_size, 
                 tile_y + self.config.tile_size],
                radius=self.config.tile_radius,
                fill=tile_color,
                outline=self.colors.tile_border,
                width=2
            )
            
            day_img = self.text_renderer.render_text(
                text=day_text,
                font_size=20,
                color=self.colors.text_color,
                stroke_width=1,
                stroke_color=(0, 0, 0, 150)
            )
            
            day_text_x = tile_x + (self.config.tile_size - day_img.width) // 2
            day_text_y = tile_y + 18
            img.paste(day_img, (day_text_x, day_text_y), day_img)
            
            reward_img = self.text_renderer.render_text(
                text=reward_text,
                font_size=18,
                color=self.colors.text_color,
                stroke_width=1,
                stroke_color=(0, 0, 0, 150)
            )
            
            reward_text_x = tile_x + (self.config.tile_size - reward_img.width) // 2
            reward_text_y = tile_y + self.config.tile_size - reward_img.height - 8
            img.paste(reward_img, (reward_text_x, reward_text_y), reward_img)
        
        return img
    
    def _calculate_day_reward(self, day: int, level: int) -> int:
        base_rewards = {
            1: 10, 2: 20, 3: 30, 4: 40, 
            5: 50, 6: 75, 7: 100
        }
        
        if day not in base_rewards:
            return 0
        
        base = base_rewards[day]
        
        if level <= 1:
            multiplier = 1.0
        elif level <= 50:
            multiplier = 1.0 + (level - 1) * 0.02
        elif level <= 100:
            multiplier = 2.0 + (level - 50) * 0.04
        else:
            multiplier = 4.0 + (level - 100) * 0.02
        
        reward = int(base * multiplier)
        
        if reward <= 10:
            return int(round(reward))
        
        if reward < 50:
            return int(round(reward / 5) * 5)
        else:
            return int(round(reward / 10) * 10)

class DailyPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="daily")
        
        text_renderer = self.generator.text_renderer
        self.image_generator = DailyImageGenerator(text_renderer=text_renderer)
        
        self.BASE_DAILY_REWARDS = {
            1: 10, 2: 20, 3: 30, 4: 40, 
            5: 50, 6: 75, 7: 100
        }
        
        self.LEVEL_MAX_REWARDS = {
            1: 100, 10: 120, 20: 140, 30: 160, 40: 180,
            50: 200, 60: 240, 70: 280, 80: 320, 90: 360,
            100: 400, 150: 500, 200: 600, 250: 700
        }
    
    def _get_max_reward_for_level(self, level: int) -> int:
        if level <= 1:
            return self.LEVEL_MAX_REWARDS[1]
        
        defined_levels = sorted(self.LEVEL_MAX_REWARDS.keys())
        
        if level >= defined_levels[-1]:
            if level > 250:
                extra_levels = level - 250
                extra_bonus = (extra_levels // 25) * 50
                base = self.LEVEL_MAX_REWARDS[250]
                return self._round_reward(base + extra_bonus)
            return self.LEVEL_MAX_REWARDS[defined_levels[-1]]
        
        lower_level = max([l for l in defined_levels if l <= level])
        upper_level = min([l for l in defined_levels if l > level])
        
        lower_reward = self.LEVEL_MAX_REWARDS[lower_level]
        upper_reward = self.LEVEL_MAX_REWARDS[upper_level]
        
        progress = (level - lower_level) / (upper_level - lower_level)
        interpolated = lower_reward + (upper_reward - lower_reward) * progress
        
        return self._round_reward(interpolated)
    
    def _round_reward(self, amount: float) -> int:
        amount = float(amount)
        
        if amount <= 10:
            return int(round(amount))
        
        if amount < 50:
            return int(round(amount / 5) * 5)
        else:
            return int(round(amount / 10) * 10)
    
    def _calculate_reward_for_day(self, day: int, level: int) -> int:
        if day < 1 or day > 7:
            day = min(max(day, 1), 7)
        
        base_reward = self.BASE_DAILY_REWARDS.get(day, self.BASE_DAILY_REWARDS[7])
        
        if level <= 1:
            multiplier = 1.0
        elif level <= 50:
            multiplier = 1.0 + (level - 1) * 0.02
        elif level <= 100:
            multiplier = 2.0 + (level - 50) * 0.04
        else:
            multiplier = 4.0 + (level - 100) * 0.02
        
        calculated = base_reward * multiplier
        return self._round_reward(calculated)
    
    def _parse_date(self, date_value):
        if not date_value:
            return None
        try:
            if isinstance(date_value, str):
                date_value = date_value.strip()
                if date_value in ["", "None", "none", "null"]:
                    return None
                return datetime.fromisoformat(date_value).date()
            elif isinstance(date_value, datetime):
                return date_value.date()
            return None
        except Exception:
            return None
    
    def _can_claim_daily(self, user_id):
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"
        
        today = datetime.now().date()
        last_daily_date = self._parse_date(user.get("last_daily_date"))
        
        if not last_daily_date:
            return True, "first"
        
        if last_daily_date == today:
            return False, "already_claimed"
        
        yesterday = today - timedelta(days=1)
        if last_daily_date == yesterday:
            return True, "continue"
        
        days_diff = (today - last_daily_date).days
        
        if days_diff == 1:
            return True, "continue"
        elif days_diff > 1:
            return True, "reset"
        else:
            return True, "first"
    
    def _claim_daily_reward(self, user_id):
        user = self.cache.get_user(user_id)
        if not user:
            return None, 1, 1, "User not found"
        
        today = datetime.now().date()
        last_daily_date = self._parse_date(user.get("last_daily_date"))
        current_streak = user.get("daily_streak_day", 0)
        
        if last_daily_date and (today - last_daily_date).days > 1:
            current_streak = 0
        
        new_streak = min(current_streak + 1, 7)
        user_level = user.get("level", 1)
        
        reward_amount = self._calculate_reward_for_day(new_streak, user_level)
        
        self.cache.update_balance(user_id, reward_amount)
        
        now = datetime.now()
        self.cache.update_user(
            user_id,
            last_daily_date=now.isoformat(),
            daily_streak_day=new_streak
        )
        
        return reward_amount, new_streak, user_level, None
    
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 0)
        if error:
            self.send_message_image(sender, file_queue, error, "Error", cache, user_id)
            return ""
        
        nickname = sender
        
        can_claim, claim_status = self._can_claim_daily(user_id)
        
        user = self.cache.get_user(user_id)
        streak_day = user.get("daily_streak_day", 0)
        user_level = user.get("level", 1)
        claimed_days = list(range(1, streak_day + 1))
        
        if not can_claim:
            if claim_status == "already_claimed":
                current_day = streak_day
                reward_amount = self._calculate_reward_for_day(current_day, user_level)
                
                img = self.image_generator.generate_daily_image(
                    current_day=current_day,
                    claimed_days=claimed_days,
                    reward_amount=reward_amount,
                    streak=streak_day,
                    level=user_level,
                    claimed_today=True,
                    just_claimed=False
                )
                
                if img:
                    img_path = os.path.join(self.results_folder, f"daily_{user_id}_{int(time.time())}.webp")
                    img.save(img_path, format='WEBP', quality=self.image_generator.config.webp_quality)
                    
                    overlay_path, _ = self.apply_user_overlay(
                        img_path, user_id, nickname, 0, 0, 
                        user["balance"], user,
                        show_bet_amount=False,
                        show_win_text=False,
                        avatar_size=50,
                        font_scale=0.6
                    )
                    
                    if overlay_path:
                        file_queue.put(overlay_path)
                
                tomorrow = datetime.now() + timedelta(days=1)
                return f"Daily Reward (Already claimed today)\nStreak: Day {streak_day}/7\nNext: {tomorrow.strftime('%d/%m')}"
            else:
                return f"Daily Reward\nCannot claim\nStreak: Day {streak_day}/7"
        
        reward_amount, new_streak, user_level, error = self._claim_daily_reward(user_id)
        if error:
            self.send_message_image(sender, file_queue, error, "Error", cache, user_id)
            return ""
        
        claimed_days = list(range(1, new_streak + 1))
        
        img = self.image_generator.generate_daily_image(
            current_day=new_streak,
            claimed_days=claimed_days,
            reward_amount=reward_amount,
            streak=new_streak,
            level=user_level,
            claimed_today=False,
            just_claimed=True
        )
        
        if img:
            img_path = os.path.join(self.results_folder, f"daily_{user_id}_{int(time.time())}.webp")
            img.save(img_path, format='WEBP', quality=self.image_generator.config.webp_quality)
            
            user = self.cache.get_user(user_id)
            balance = user.get("balance", 0) if user else 0
            
            overlay_path, _ = self.apply_user_overlay(
                img_path, user_id, nickname, reward_amount, reward_amount,
                balance, user,
                show_bet_amount=False,
                show_win_text=False,
                avatar_size=50,
                font_scale=0.6
            )
            
            if overlay_path:
                file_queue.put(overlay_path)
        
        messages = {
            "first": f"First Daily Reward!\n+${reward_amount} coins\nNew streak: Day {new_streak}/7",
            "continue": f"Daily Reward Claimed!\n+${reward_amount} coins\nStreak: Day {new_streak}/7",
            "reset": f"Daily Reward (Streak Reset)\n+${reward_amount} coins\nNew streak: Day 1/7"
        }
        
        return messages.get(claim_status, f"Daily Reward Claimed!\n+${reward_amount} coins")

def register():
    plugin = DailyPlugin()
    return {
        "name": "daily",
        "aliases": ["/daily", "/d"],
        "description": "Claim daily reward and maintain streak\nRewards scale with your level!",
        "execute": plugin.execute_game
    }