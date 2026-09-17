# plugins/wheel.py

import hashlib
import math
import os
import random
from datetime import datetime

from PIL import Image, ImageDraw, ImageFilter

from base_game_plugin import BaseGamePlugin
from logger import logger
from plugins.monthly import record_monthly_win
from plugins.weekly import record_weekly_win


class WheelPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="wheel")
        self.backgrounds_folder = self.get_asset_path("backgrounds")
        self.avatars_folder = self.get_asset_path("avatars")
        self.spin_cost = 100

        self.background_prices = {
            "cheap": 100,
            "medium": 300,
            "expensive": 800,
        }

        self.avg_background_value = 230

        self.spawn_chance = {
            "avatar": 0.02,
            "background": 0.20,
        }

        self.background_rarity_weights = {
            "cheap": 60,
            "medium": 30,
            "expensive": 10,
        }

        self.color_ranges = [
            (0, 25, (176, 195, 217)),
            (25, 50, (94, 152, 217)),
            (50, 100, (75, 105, 255)),
            (100, 200, (136, 71, 255)),
            (200, 350, (211, 44, 230)),
            (350, float('inf'), (235, 75, 75)),
        ]

        self.hardcoded_prizes = {}
        ev_values = [round(0.75 + i * 0.01, 2) for i in range(36)]
        
        for ev in ev_values:
            prizes = self._generate_balanced_prizes(ev)
            self.hardcoded_prizes[ev] = prizes

    def _generate_balanced_prizes(self, ev):
        """Generuje nagrody - dla EV >= 1.00 skumulowane, dla reszty mieszane"""
        
        # Jeśli EV >= 1.00 - zawsze skumulowane, ale różne warianty
        if ev >= 1.00:
            return self._generate_concentrated_prizes(ev)
        
        # Jeśli EV < 1.00 - 30% szans na skumulowane, 70% dowolne
        if random.random() < 0.30:
            # Lekko skumulowane dla niskiego EV
            return self._generate_light_concentrated_prizes(ev)
        
        # Dowolny rozkład (oryginalny kod)
        style = random.choice([
            "huge_jackpot",
            "medium_spread",
            "low_no_zero",
            "two_big",
            "gradual",
            "extreme",
            "three_big",
            "cluster",
            "top_heavy",
            "bottom_heavy",
        ])
        
        prizes = self._generate_prizes_for_style(style, ev)
        
        has_low = any(p < 100 for p in prizes)
        has_high = any(p > 100 for p in prizes)
        
        if not has_low:
            min_idx = prizes.index(min(prizes))
            prizes[min_idx] = random.randint(10, 90)
            prizes[min_idx] = round(prizes[min_idx] / 5) * 5
        
        if not has_high:
            max_idx = prizes.index(max(prizes))
            prizes[max_idx] = random.randint(150, 500)
            prizes[max_idx] = round(prizes[max_idx] / 5) * 5
        
        for i in range(len(prizes)):
            if random.random() < 0.3:
                change = random.choice([-5, 5, -10, 10, -15, 15])
                new_val = max(0, prizes[i] + change)
                new_val = round(new_val / 5) * 5
                if not (new_val < 100 and any(p > 100 for p in prizes)) and not (new_val > 100 and any(p < 100 for p in prizes)):
                    prizes[i] = new_val
        
        prizes.sort()
        
        if not any(p < 100 for p in prizes):
            prizes[0] = random.randint(10, 90)
            prizes[0] = round(prizes[0] / 5) * 5
        if not any(p > 100 for p in prizes):
            prizes[-1] = random.randint(150, 500)
            prizes[-1] = round(prizes[-1] / 5) * 5
        
        prizes.sort()
        return prizes

    def _generate_light_concentrated_prizes(self, ev):
        """Lekko skumulowane dla EV < 1.00 (30% szans)"""
        strength = (ev - 0.75) / 0.25  # 0-1 dla EV 0.75-1.00
        
        # Wybierz styl - tylko łagodne warianty
        style = random.choice([
            "two_small_big",
            "three_small_big",
            "small_jackpot"
        ])
        
        if style == "two_small_big":
            # 2 średnie, reszta mała
            small = [5, 10, 15, 20, 25, 30]
            big1 = int(40 + strength * 80)
            big2 = int(60 + strength * 100)
            prizes = small + [big1, big2]
            
        elif style == "three_small_big":
            # 3 średnie, reszta mała
            small = [5, 10, 15, 20, 25]
            big1 = int(30 + strength * 60)
            big2 = int(50 + strength * 80)
            big3 = int(70 + strength * 100)
            prizes = small + [big1, big2, big3]
            
        else:  # small_jackpot
            # 1 średnia, reszta mała
            small = [5, 10, 15, 20, 25, 30, 35]
            big = int(50 + strength * 120)
            prizes = small + [big]
        
        # Upewnij się że mamy 8 nagród
        while len(prizes) < 8:
            prizes.append(0)
        prizes = prizes[:8]
        
        # Zaokrąglij do 5
        prizes = [round(p / 5) * 5 for p in prizes]
        prizes = [max(0, p) for p in prizes]
        
        prizes.sort()
        return prizes

    def _generate_concentrated_prizes(self, ev):
        strength = (ev - 1.00) / 0.05  # 0-1

        style = random.choice([
            "one_big_concentrated",
            "two_big_concentrated",
            "three_big_concentrated",
            "jackpot_concentrated",
            "extreme_concentrated",
        ])

        if style == "one_big_concentrated":
            small = [0, 5, 10, 15, 20, 25, 30]
            big = int(250 + strength * 750)
            prizes = small + [big]

        elif style == "two_big_concentrated":
            small = [0, 5, 10, 15, 20, 25]
            big1 = int(150 + strength * 350) 
            big2 = int(300 + strength * 700) 
            prizes = small + [big1, big2]

        elif style == "three_big_concentrated":
            small = [0, 5, 10, 15, 20]
            big1 = int(100 + strength * 200)   
            big2 = int(200 + strength * 400)      
            big3 = int(350 + strength * 650)  
            prizes = small + [big1, big2, big3]

        elif style == "jackpot_concentrated":
            small = [0, 5, 10, 15, 20, 25]
            medium = int(60 + strength * 90)  
            jackpot = int(400 + strength * 1100) 
            prizes = small + [medium, jackpot]

        else: 
            small = [0, 0, 5, 5, 10, 10, 15]
            big = int(300 + strength * 1200)
            prizes = small + [big]

        while len(prizes) < 8:
            prizes.append(0)
        prizes = prizes[:8]

        prizes = [round(p / 5) * 5 for p in prizes]
        prizes = [max(0, p) for p in prizes]

        prizes.sort()
        median = prizes[len(prizes) // 2]
        max_val = prizes[-1]

        if median <= 0:
            median = prizes[-2] if len(prizes) >= 2 else 0

        if median > 0 and max_val < median * 8:
            prizes[-1] = max(prizes[-1], int(median * 8))
            prizes[-1] = round(prizes[-1] / 5) * 5

        prizes.sort()
        return prizes

    def _generate_prizes_for_style(self, style, ev):
        if style == "huge_jackpot":
            base = [5, 10, 15, 20, 25, 30, 40]
            jackpot = int(30 + (ev - 0.75) * 800)
            prizes = base + [jackpot]
            
        elif style == "medium_spread":
            start = int(10 + (ev - 0.75) * 30)
            step = int(5 + (ev - 0.75) * 25)
            prizes = [start + i * step for i in range(8)]
            
        elif style == "low_no_zero":
            base = [20, 25, 30, 35, 40, 45, 50]
            max_val = int(30 + (ev - 0.75) * 300)
            prizes = base + [max_val]
            
        elif style == "two_big":
            small = [10, 15, 20, 25, 30, 35]
            big1 = int(60 + (ev - 0.75) * 250)
            big2 = int(100 + (ev - 0.75) * 250)
            prizes = small + [big1, big2]
            
        elif style == "gradual":
            start = int(5 + (ev - 0.75) * 20)
            step = int(5 + (ev - 0.75) * 30)
            prizes = [start + i * step for i in range(8)]
            
        elif style == "extreme":
            small = [0, 5, 10, 15, 20, 25, 30]
            big = int(40 + (ev - 0.75) * 400)
            prizes = small + [big]
            
        elif style == "three_big":
            small = [10, 15, 20, 25, 30]
            big1 = int(80 + (ev - 0.75) * 200)
            big2 = int(120 + (ev - 0.75) * 200)
            big3 = int(160 + (ev - 0.75) * 200)
            prizes = small + [big1, big2, big3]
            
        elif style == "cluster":
            mean = int(40 + (ev - 0.75) * 150)
            prizes = []
            for i in range(8):
                deviation = random.randint(-25, 25)
                prizes.append(max(0, mean + deviation))
                
        elif style == "top_heavy":
            prizes = []
            for i in range(8):
                val = int(10 + (i / 7) * (80 + (ev - 0.75) * 350))
                prizes.append(val)
                
        elif style == "bottom_heavy":
            prizes = []
            for i in range(8):
                val = int(80 + (ev - 0.75) * 350 - (i / 7) * 70)
                prizes.append(max(0, val))
                
        else:
            prizes = [random.randint(0, int(80 + (ev - 0.75) * 350)) for _ in range(8)]
        
        while len(prizes) < 8:
            prizes.append(0)
        prizes = prizes[:8]
        
        prizes = [round(p / 5) * 5 for p in prizes]
        prizes = [max(0, p) for p in prizes]
        
        return prizes

    def get_color_for_amount(self, amount):
        for min_val, max_val, color in self.color_ranges:
            if min_val <= amount < max_val:
                return color
        return self.color_ranges[-1][2]

    def parse_bet(self, args):
        if args:
            return None, "Usage: /wheel\nSpin price is fixed at 100 coins."
        return self.spin_cost, None

    def get_slot_key(self, now=None):
        now = now or datetime.now()
        ten_minute_slot = now.minute // 10
        return now.strftime(f"%Y%m%d%H{ten_minute_slot}")

    def get_target_ev(self, now=None):
        slot_key = self.get_slot_key(now)
        digest = hashlib.sha256(f"wheel:{slot_key}".encode("utf-8")).hexdigest()
        ev_points = int(digest[:8], 16) % 100
        
        if ev_points < 55:  # 55% - EV 0.75-0.94
            index = ev_points % 20
            ev = 0.75 + (index / 100.0)
        elif ev_points < 97:  # 42% - EV 0.95-0.99 (55+42=97)
            index = (ev_points - 55) % 5
            ev = 0.95 + (index / 100.0)
        else:  # 3% - EV 1.00-1.05
            index = (ev_points - 97) % 6
            ev = 1.00 + (index / 100.0)
        
        return round(ev, 2)

    def get_next_ev_change_text(self, now=None):
        now = now or datetime.now()
        next_minute = ((now.minute // 10) + 1) * 10
        if next_minute >= 60:
            return f"{(now.hour + 1) % 24:02d}:00"
        return f"{now.hour:02d}:{next_minute:02d}"

    def _weighted_choice(self, weights):
        values = list(weights.keys())
        chances = list(weights.values())
        return random.choices(values, weights=chances, k=1)[0]

    def get_random_background_rarity(self):
        return self._weighted_choice(self.background_rarity_weights)

    def get_background_value(self, rarity):
        return self.background_prices.get(rarity, 100)

    def get_money_prizes(self, target_ev):
        closest_ev = min(self.hardcoded_prizes.keys(), key=lambda x: abs(x - target_ev))
        return self.hardcoded_prizes[closest_ev]

    def _is_avatar_won(self, slot_key):
        if not self.cache:
            return False
        try:
            saved_slot = self.cache.get_setting("wheel_avatar_won_slot")
            return saved_slot == slot_key
        except:
            return False

    def _set_avatar_won(self, slot_key):
        if not self.cache:
            return
        try:
            self.cache.set_setting("wheel_avatar_won_slot", slot_key)
        except:
            pass

    def _is_background_won(self, slot_key):
        if not self.cache:
            return False
        try:
            saved_slot = self.cache.get_setting("wheel_bg_won_slot")
            return saved_slot == slot_key
        except:
            return False

    def _set_background_won(self, slot_key):
        if not self.cache:
            return
        try:
            self.cache.set_setting("wheel_bg_won_slot", slot_key)
        except:
            pass

    def get_wheel_segments(self, target_ev, slot_key, selected_index=None, prize_type=None, prize_name=None, background_rarity=None, shift=0):
        money_prizes = self.get_money_prizes(target_ev)
        segments = []

        for idx, amount in enumerate(money_prizes):
            color = self.get_color_for_amount(amount)
            segments.append({
                "type": "money",
                "label": f"{amount}",
                "color": color,
                "weight": 1,
                "payout": amount,
                "prize_name": None,
                "image_path": None,
                "rarity": None,
            })

        seed = int(hashlib.md5(f"{slot_key}_wheel".encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        avatar_won = self._is_avatar_won(slot_key)
        bg_won = self._is_background_won(slot_key)

        has_avatar = False
        if avatar_won:
            segments.append({
                "type": "money",
                "label": "100",
                "color": self.get_color_for_amount(100),
                "weight": 1,
                "payout": 100,
                "prize_name": None,
                "image_path": None,
                "rarity": None,
            })
        else:
            if rng.random() < self.spawn_chance["avatar"]:
                has_avatar = True

        has_background = False
        if bg_won:
            segments.append({
                "type": "money",
                "label": "230",
                "color": self.get_color_for_amount(230),
                "weight": 1,
                "payout": 230,
                "prize_name": None,
                "image_path": None,
                "rarity": None,
            })
        else:
            if rng.random() < self.spawn_chance["background"]:
                has_background = True

        if not has_avatar and not has_background:
            while len(segments) < 10:
                extra_amount = rng.choice(money_prizes)
                color = self.get_color_for_amount(extra_amount)
                segments.append({
                    "type": "money",
                    "label": f"{extra_amount}",
                    "color": color,
                    "weight": 1,
                    "payout": extra_amount,
                    "prize_name": None,
                    "image_path": None,
                    "rarity": None,
                })

        rng.shuffle(segments)

        if has_avatar:
            avatar_segment = {
                "type": "avatar",
                "label": "AVATAR",
                "color": (255, 215, 0),
                "weight": 1,
                "payout": 100,
                "prize_name": None,
                "image_path": None,
                "rarity": None,
            }
            avatar_pos = rng.randint(0, len(segments))
            segments.insert(avatar_pos, avatar_segment)

        if has_background:
            if background_rarity is None:
                background_rarity = self.get_random_background_rarity()
            
            bg_value = self.get_background_value(background_rarity)
            
            bg_segment = {
                "type": "background",
                "label": "BG",
                "color": (255, 215, 0),
                "weight": 1,
                "payout": bg_value,
                "prize_name": None,
                "image_path": None,
                "rarity": background_rarity,
            }
            bg_pos = rng.randint(0, len(segments))
            segments.insert(bg_pos, bg_segment)

        if shift > 0:
            shift = shift % len(segments)
            segments = segments[shift:] + segments[:shift]

        if selected_index is not None and prize_name and 0 <= selected_index < len(segments):
            segment = segments[selected_index]
            if prize_type == "avatar" and segment["type"] == "avatar":
                segment["prize_name"] = prize_name
                segment["image_path"] = os.path.join(self.avatars_folder, prize_name)
            elif prize_type == "background" and segment["type"] == "background":
                segment["prize_name"] = prize_name
                segment["image_path"] = os.path.join(self.backgrounds_folder, prize_name)
                segment["rarity"] = background_rarity

        return segments

    def roll_wheel_outcome(self, segments):
        segment_index = random.randint(0, len(segments) - 1)
        return segment_index, segments[segment_index]

    def roll_money_fallback_outcome(self, segments):
        money_indices = [idx for idx, segment in enumerate(segments) if segment["type"] == "money"]
        segment_index = random.choice(money_indices)
        return segment_index, segments[segment_index]

    def get_segment_index(self, prize_type):
        matching = [
            idx for idx, segment in enumerate(self.get_wheel_segments(self.get_target_ev()))
            if segment["type"] == prize_type
        ]
        return random.choice(matching) if matching else 0

    def get_user_avatars_for_display(self, user_id):
        user = self.cache.get_user(user_id)
        if not user:
            return ["default-avatar.png"]

        display_avatars = ["default-avatar.png"]
        for avatar_file in user.get("avatars", []):
            if avatar_file not in display_avatars:
                display_avatars.append(avatar_file)
        return display_avatars

    def get_random_avatar(self, user_id):
        owned = set(self.get_user_avatars_for_display(user_id))
        candidates = []

        if os.path.exists(self.avatars_folder):
            for filename in os.listdir(self.avatars_folder):
                if filename.lower().endswith(".png") and filename not in owned:
                    candidates.append(filename)

        return random.choice(candidates) if candidates else None

    def add_user_avatar(self, user_id, avatar_file):
        user = self.cache.get_user(user_id)
        if not user or not avatar_file:
            return False

        avatars = list(user.get("avatars", []))
        if avatar_file not in avatars:
            avatars.append(avatar_file)
            self.cache.update_user(user_id, avatars=avatars)
            return True
        return False

    def get_user_backgrounds_for_display(self, user_id):
        user = self.cache.get_user(user_id)
        if not user:
            return ["default-bg.png"]

        display_backgrounds = ["default-bg.png"]
        for background_file in user.get("backgrounds", []):
            if background_file not in display_backgrounds:
                display_backgrounds.append(background_file)
        return display_backgrounds

    def get_random_background(self, user_id, rarity=None):
        owned = set(self.get_user_backgrounds_for_display(user_id))
        candidates = []
        
        if rarity and rarity in ["cheap", "medium", "expensive"]:
            prefix = rarity + "_"
            if os.path.exists(self.backgrounds_folder):
                for filename in os.listdir(self.backgrounds_folder):
                    if filename.lower().startswith(prefix) and filename not in owned:
                        candidates.append(filename)
        else:
            if os.path.exists(self.backgrounds_folder):
                for filename in os.listdir(self.backgrounds_folder):
                    if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) and filename not in owned:
                        candidates.append(filename)

        return random.choice(candidates) if candidates else None

    def add_user_background(self, user_id, background_file):
        user = self.cache.get_user(user_id)
        if not user or not background_file:
            return False

        backgrounds = list(user.get("backgrounds", []))
        if background_file not in backgrounds:
            backgrounds.append(background_file)
            self.cache.update_user(user_id, backgrounds=backgrounds)
            return True
        return False

    def create_wheel_animation_with_segments(self, user_id, segment_index, target_ev, slot_key, prize_type=None, prize_name=None, background_rarity=None, shift=0, image_path=None, payout=None, segments=None):
        width, height = 240, 270
        frames = []
        frame_count = 50
        
        user = self.cache.get_user(user_id)
        background_path = None
        if user and user.get("background"):
            bg_file = user.get("background")
            if bg_file in user.get("backgrounds", []):
                background_path = os.path.join(self.backgrounds_folder, bg_file)
            else:
                background_path = os.path.join(self.avatars_folder, bg_file)
        
        wheel_segments = segments if segments is not None else self.get_wheel_segments(target_ev, slot_key, segment_index, prize_type, prize_name, background_rarity, shift)
        
        segment_size = 360 / len(wheel_segments)
        target_center = segment_index * segment_size + (segment_size / 2)
        target_rotation = 270 - target_center
        start_rotation = target_rotation - (360 * 2) - random.randint(5, 15)

        for frame_idx in range(frame_count):
            progress = frame_idx / (frame_count - 1)
            
            if progress < 0.4:
                eased = progress / 0.4 * 0.7
            else:
                p = (progress - 0.4) / 0.6
                eased = 0.7 + 0.3 * (1 - ((1 - p) ** 6))
            
            eased = min(1.0, max(0.0, eased))
            
            rotation = start_rotation + ((target_rotation - start_rotation) * eased)
            frame = self._draw_wheel_frame(
                width, height, rotation, wheel_segments, frame_idx, frame_count, 
                segment_index, background_path, target_ev,
                prize_type=prize_type,
                prize_name=prize_name,
                image_path=image_path,
                payout=payout
            )
            frames.append(frame.convert("RGBA"))

        final_frame = frames[-1].copy()
        frames.append(final_frame.copy())
        frames.append(final_frame.copy())
        frames.append(final_frame.copy())

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        output_path = os.path.join(self.results_folder, f"wheel_base_{user_id}_{timestamp}.webp")
        
        durations = [35 if i / (len(frames) - 1) < 0.4 else 50 if i / (len(frames) - 1) < 0.7 else 80 for i in range(len(frames))]
        
        frames[0].save(
            output_path,
            format="WEBP",
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
            quality=85,
            method=2,
            optimize=True,
        )
        return output_path

    def _draw_wheel_frame(self, width, height, rotation, wheel_segments, frame_idx, frame_count, selected_index, background_path=None, target_ev=None, prize_type=None, prize_name=None, image_path=None, payout=None):
        if background_path and os.path.exists(background_path):
            try:
                bg = Image.open(background_path).convert("RGBA")
                bg = bg.resize((width, height), Image.LANCZOS)
                img = bg
            except Exception as e:
                logger.error(f"[Wheel] Background error: {e}")
                img = Image.new("RGBA", (width, height), (20, 22, 32, 255))
        else:
            img = Image.new("RGBA", (width, height), (20, 22, 32, 255))
        
        shade = Image.new("RGBA", (width, height), (0, 0, 0, 180))
        img.alpha_composite(shade)
        
        draw = ImageDraw.Draw(img)

        center = (width // 2, height // 2 - 10)
        radius = min(width, height - 40) // 2 - 4
        segment_size = 360 / len(wheel_segments)

        draw.ellipse(
            [center[0] - radius - 4, center[1] - radius - 4, center[0] + radius + 4, center[1] + radius + 4],
            fill=None,
            outline=(255, 215, 0, 200),
            width=2,
        )
        
        draw.ellipse(
            [center[0] - radius - 2, center[1] - radius - 2, center[0] + radius + 2, center[1] + radius + 2],
            fill=(20, 22, 32, 255),
            outline=(180, 180, 190, 255),
            width=1,
        )
        
        draw.ellipse(
            [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
            fill=(20, 22, 32, 255),
            outline=(100, 100, 110, 255),
            width=1,
        )

        for idx, segment in enumerate(wheel_segments):
            start = rotation + (idx * segment_size)
            end = start + segment_size
            
            draw.pieslice(
                [center[0] - radius + 1, center[1] - radius + 1, center[0] + radius - 1, center[1] + radius - 1],
                start=start,
                end=end,
                fill=segment["color"],
                outline=(0, 0, 0, 100),
                width=1,
            )

            mid_angle = math.radians(start + (segment_size / 2))
            text_radius = radius * 0.68
            text_x = center[0] + int(math.cos(mid_angle) * text_radius)
            text_y = center[1] + int(math.sin(mid_angle) * text_radius)
            
            text = segment["label"] if segment["label"] else ""
            if text:
                self._draw_horizontal_text_on_segment(draw, text, text_x, text_y, radius)

        center_radius = int(radius * 0.28)
        draw.ellipse(
            [center[0] - center_radius - 3, center[1] - center_radius - 3, center[0] + center_radius + 3, center[1] + center_radius + 3],
            fill=None,
            outline=(255, 215, 0, 150),
            width=2,
        )
        draw.ellipse(
            [center[0] - center_radius, center[1] - center_radius, center[0] + center_radius, center[1] + center_radius],
            fill=(20, 22, 32, 255),
            outline=(180, 180, 190, 255),
            width=1,
        )

        arrow_y = center[1] - radius - 8
        arrow_size = 18
        
        draw.polygon(
            [
                (center[0] + 2, arrow_y + arrow_size + 2),
                (center[0] - arrow_size + 2, arrow_y - 4 + 2),
                (center[0] + arrow_size + 2, arrow_y - 4 + 2),
            ],
            fill=(0, 0, 0, 80),
        )
        
        draw.polygon(
            [
                (center[0], arrow_y + arrow_size),
                (center[0] - arrow_size, arrow_y - 4),
                (center[0] + arrow_size, arrow_y - 4),
            ],
            fill=(255, 215, 0, 230),
            outline=(255, 255, 255, 180),
            width=1,
        )
        
        draw.polygon(
            [
                (center[0], arrow_y + arrow_size - 4),
                (center[0] - 5, arrow_y - 1),
                (center[0] + 5, arrow_y - 1),
            ],
            fill=(255, 240, 150, 150),
        )

        selected_segment = wheel_segments[selected_index] if 0 <= selected_index < len(wheel_segments) else None

        if image_path and frame_idx > frame_count * 0.70:
            reveal = min(1.0, (frame_idx - (frame_count * 0.70)) / (frame_count * 0.20))
            self._draw_prize_thumbnail(
                img,
                image_path,
                prize_type or "avatar",
                center[0],
                center[1],
                large=True,
                scale=reveal,
                max_size=int(center_radius * 1.2)
            )
        elif prize_type == "money" and payout is not None and frame_idx > frame_count * 0.70:
            reveal = min(1.0, (frame_idx - (frame_count * 0.70)) / (frame_count * 0.20))
            font_size = int(center_radius * 0.5 * reveal)
            if font_size > 4:
                self._draw_centered_text(
                    draw, 
                    f"{payout}$", 
                    font_size, 
                    center[1] - font_size//2, 
                    width, 
                    (255, 215, 0, int(255 * reveal)), 
                    center_x=center[0]
                )
        elif selected_segment and selected_segment.get("image_path") and frame_idx > frame_count * 0.70:
            reveal = min(1.0, (frame_idx - (frame_count * 0.70)) / (frame_count * 0.20))
            self._draw_prize_thumbnail(
                img,
                selected_segment["image_path"],
                selected_segment["type"],
                center[0],
                center[1],
                large=True,
                scale=reveal,
                max_size=int(center_radius * 1.2)
            )
        elif selected_segment and selected_segment["type"] == "money" and frame_idx > frame_count * 0.70:
            reveal = min(1.0, (frame_idx - (frame_count * 0.70)) / (frame_count * 0.20))
            font_size = int(center_radius * 0.5 * reveal)
            if font_size > 4:
                self._draw_centered_text(
                    draw, 
                    f"{selected_segment['payout']}$", 
                    font_size, 
                    center[1] - font_size//2, 
                    width, 
                    (255, 215, 0, int(255 * reveal)), 
                    center_x=center[0]
                )

        footer_text = "Prizes change every 10 minutes"
        footer_font_size = int(radius * 0.09)
        if footer_font_size > 4:
            self._draw_centered_text(
                draw, 
                footer_text, 
                footer_font_size, 
                height - int(radius * 0.12) - 17,
                width, 
                (255, 255, 255, 200)
            )

        return img

    def _draw_horizontal_text_on_segment(self, draw, text, x, y, radius):
        font_size = int(radius * 0.09) if len(text) > 6 else int(radius * 0.11)
        font_size = max(4, min(font_size, 10))
        font = self.text_renderer.get_font(font_size) if hasattr(self, "text_renderer") else None
        
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        offset_x = text_width // 2
        offset_y = text_height // 2
        
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((x - offset_x + dx, y - offset_y + dy), text, font=font, fill=(0, 0, 0, 150))
        draw.text((x - offset_x, y - offset_y), text, font=font, fill=(255, 255, 255, 255))

    def _draw_prize_thumbnail(self, canvas, image_path, prize_type, center_x, center_y, large=False, scale=1.0, max_size=60):
        if not os.path.exists(image_path):
            return

        try:
            thumb = Image.open(image_path).convert("RGBA")
            if prize_type == "avatar":
                size = int(max_size * 0.9 * scale)
                size = max(6, size)
                thumb = thumb.resize((size, size), Image.LANCZOS)
                mask = Image.new("L", (size, size), 0)
                ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
                frame = Image.new("RGBA", (size + 4, size + 4), (0, 0, 0, 0))
                frame_draw = ImageDraw.Draw(frame)
                frame_draw.ellipse([0, 0, size + 3, size + 3], fill=(40, 42, 52, 245))
                frame_draw.ellipse([2, 2, size + 1, size + 1], fill=(60, 62, 72, 245))
                frame.paste(thumb, (2, 2), mask)
            else:
                size = (
                    int(max_size * 1.2 * scale),
                    int(max_size * 0.75 * scale)
                )
                size = (max(8, size[0]), max(5, size[1]))
                thumb = thumb.resize(size, Image.LANCZOS)
                frame = Image.new("RGBA", (size[0] + 4, size[1] + 4), (0, 0, 0, 0))
                frame_draw = ImageDraw.Draw(frame)
                frame_draw.rounded_rectangle([0, 0, size[0] + 3, size[1] + 3], radius=4, fill=(40, 42, 52, 245))
                frame_draw.rounded_rectangle([2, 2, size[0] + 1, size[1] + 1], radius=3, fill=(60, 62, 72, 245))
                frame.alpha_composite(thumb, (2, 2))

            canvas.alpha_composite(frame, (int(center_x - frame.width / 2), int(center_y - frame.height / 2)))
        except Exception as e:
            logger.error(f"[Wheel] Prize thumbnail error: {e}")

    def _draw_centered_text(self, draw, text, size, y, width, fill, center_x=None):
        font = self.text_renderer.get_font(size) if hasattr(self, "text_renderer") else None
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = int((center_x if center_x is not None else width / 2) - (text_width / 2))
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 150))
        draw.text((x, y), text, font=font, fill=fill)

    def get_custom_overlay(self, **kwargs):
        return None

    def _format_result(self, prize_type, payout, prize_name, rarity=None):
        if prize_type == "money":
            return f"{payout} coins"
        if prize_type == "avatar":
            return f"avatar {prize_name}"
        if prize_type == "background":
            rarity_text = {
                "cheap": "Common",
                "medium": "Rare",
                "expensive": "Legendary"
            }.get(rarity, "")
            return f"background {prize_name} ({rarity_text})"
        return "no prize"

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache

        animated = True
        if args and args[-1].lower() == "x":
            animated = False
            args = args[:-1]

        bet, error = self.parse_bet(args)
        if error:
            self.send_message_image(sender, file_queue, error, "Wheel - Invalid Usage", cache, None)
            return None

        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, bet)
        if error:
            if "Insufficient balance" in error:
                self.send_message_image(
                    sender,
                    file_queue,
                    f"Insufficient funds!\n\nBet: {bet}\nBalance: {user.get('balance', 0) if user else 0}",
                    "Wheel - Insufficient Funds",
                    cache,
                    user_id,
                )
            else:
                self.send_message_image(sender, file_queue, "User validation failed.", "Wheel - Validation Error", cache, user_id)
            return None

        now = datetime.now()
        target_ev = self.get_target_ev(now)
        slot_key = self.get_slot_key(now)
        next_change = self.get_next_ev_change_text(now)
        balance_before = user["balance"]
        
        background_rarity = self.get_random_background_rarity()
        shift = random.randint(0, 50)
        
        original_segments = self.get_wheel_segments(target_ev, slot_key, shift=shift)
        
        segment_index, outcome = self.roll_wheel_outcome(original_segments)
        prize_type = outcome["type"]
        payout = outcome["payout"]
        prize_name = outcome["prize_name"]
        rarity = outcome.get("rarity")

        win_image_path = None
        win_prize_name = None
        win_prize_type = prize_type
        win_payout = payout
        won_bg_or_avatar = False

        if prize_type == "avatar":
            prize_name = self.get_random_avatar(user_id)
            if prize_name:
                self.add_user_avatar(user_id, prize_name)
                payout = 0
                win_payout = 0
                win_prize_name = prize_name
                win_image_path = os.path.join(self.avatars_folder, prize_name)
                won_bg_or_avatar = True
            else:
                segment_index, outcome = self.roll_money_fallback_outcome(original_segments)
                prize_type = outcome["type"]
                payout = outcome["payout"]
                prize_name = outcome["prize_name"]
                rarity = None
                win_prize_type = prize_type
                win_payout = payout

        elif prize_type == "background":
            prize_name = self.get_random_background(user_id, background_rarity)
            if prize_name:
                self.add_user_background(user_id, prize_name)
                payout = 0
                win_payout = 0
                win_prize_name = prize_name
                win_image_path = os.path.join(self.backgrounds_folder, prize_name)
                won_bg_or_avatar = True
            else:
                prize_name = self.get_random_background(user_id, None)
                if prize_name:
                    self.add_user_background(user_id, prize_name)
                    payout = 0
                    win_payout = 0
                    win_prize_name = prize_name
                    win_image_path = os.path.join(self.backgrounds_folder, prize_name)
                    won_bg_or_avatar = True
                else:
                    segment_index, outcome = self.roll_money_fallback_outcome(original_segments)
                    prize_type = outcome["type"]
                    payout = outcome["payout"]
                    prize_name = outcome["prize_name"]
                    rarity = None
                    win_prize_type = prize_type
                    win_payout = payout

        if won_bg_or_avatar:
            outcome["image_path"] = win_image_path
            outcome["prize_name"] = win_prize_name
            prize_type = win_prize_type
            payout = win_payout

        net_win = payout - bet
        new_balance = balance_before + net_win
        user_before = user.copy()
        self.update_user_balance(user_id, new_balance)

        if net_win < 0:
            try:
                new_level, new_progress = self.cache.add_experience(user_id, abs(net_win), sender, file_queue)
                user["level"] = new_level
                user["level_progress"] = new_progress
            except Exception as e:
                logger.error(f"[Wheel] Error adding experience: {e}")

        if net_win > 0:
            record_weekly_win(self.cache, user_id, "wheel", net_win)
            record_monthly_win(self.cache, user_id, "wheel", net_win)

        try:
            user["balance"] = new_balance
            
            base_animation_path = self.create_wheel_animation_with_segments(
                user_id=user_id,
                segment_index=segment_index,
                target_ev=target_ev,
                slot_key=slot_key,
                prize_type=prize_type,
                prize_name=prize_name,
                background_rarity=background_rarity if prize_type == "background" else None,
                shift=shift,
                image_path=outcome.get("image_path"),
                payout=payout,
                segments=original_segments,
            )
            
            if won_bg_or_avatar and prize_type == "background":
                self._set_background_won(slot_key)
            elif won_bg_or_avatar and prize_type == "avatar":
                self._set_avatar_won(slot_key)
            
            user_info_before = self.create_user_info(sender, bet, 0, balance_before, user_before)
            user_info_after = self.create_user_info(sender, bet, net_win, new_balance, user)
            result_path, error = self.generate_animation(
                base_animation_path=base_animation_path,
                user_id=user_id,
                user=user,
                user_info_before=user_info_before,
                user_info_after=user_info_after,
                animated=animated,
                frame_duration=55,
                last_frame_multiplier=10,
                final_frames_start_index=69,
                custom_overlay_kwargs=None,
                show_win_text=False,
                font_scale=0.50,
                avatar_size=35,
                show_bet_amount=True,
                overlay_position="bottom",
                quality=88,
            )
            if error or not result_path:
                raise RuntimeError(error or "Animation generation failed")
            file_queue.put(result_path)
        except Exception as e:
            logger.error(f"[Wheel] Result image error: {e}", exc_info=True)
            self.send_message_image(
                sender,
                file_queue,
                f"Wheel result saved, but image generation failed.\nNet: {net_win:+d}\nBalance: {new_balance}",
                "Wheel - Result",
                cache,
                user_id,
            )

        logger.info(
            f"WHEEL: {sender} bet {bet} | prize={prize_type}:{prize_name or payout} | "
            f"EV={target_ev:.2f} | net={net_win:+d} | balance={balance_before}->{new_balance}"
        )
        return None


def register():
    plugin = WheelPlugin()
    return {
        "name": "wheel",
        "aliases": ["/w"],
        "description": """Fortune Wheel

Commands:
- /wheel - Spin for 100 coins
- /wheel x - Static result (no animation)

Rules:
- EV changes every 10 minutes (0.75x - 1.10x)
- Avatar: 2% | Background: 20% spawn chance
- Avatar and Background can be won only once per 10-minute slot
- Background rarities: Common (100), Rare (300), Legendary (800)
- EV Distribution: 50% (0.75-0.95), 45% (0.95-1.00), 5% (1.00-1.10)""",
        "execute": plugin.execute_game,
    }