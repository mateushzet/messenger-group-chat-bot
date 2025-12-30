import random
import os
import time
from base_game_plugin import BaseGamePlugin
from logger import logger
from collections import deque
from PIL import Image, ImageDraw, ImageFont

class ColorsPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="colors",
            results_folder=self.get_asset_path("colors", "colors_results"),
            valid_bets=["black", "red", "blue", "gold"]
        )
        
        self.error_folder = self.get_asset_path("errors")
        os.makedirs(self.error_folder, exist_ok=True)
        
        self.color_order = [
            0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 
            0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 
            0, 1, 0, 2, 3, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1
        ]
        
        self.color_map = {
            0: "black",
            1: "red", 
            2: "blue",
            3: "gold"
        }
        
        self.multipliers = {
            "black": 2,
            "red": 3,
            "blue": 5, 
            "gold": 50
        }
        
        self.color_counts = {
            "black": self.color_order.count(0),
            "red": self.color_order.count(1),
            "blue": self.color_order.count(2), 
            "gold": self.color_order.count(3)
        }
        
        self.history_colors = {
            "black": (68, 70, 72),
            "red": (207, 57, 64),
            "blue": (53, 172, 254),
            "gold": (255, 204, 48)
        }

    def get_color_at_position(self, position):
        if 0 <= position < len(self.color_order):
            color_number = self.color_order[position]
            return self.color_map[color_number]
        return "black"

    def calculate_win(self, bet_info, result_position):
        result_color = self.get_color_at_position(result_position)
        bet_type, color_or_bets, amount_str = bet_info
        
        if bet_type == "single":
            color = color_or_bets
            bet_amount = int(amount_str) if amount_str else 0
            
            if color == result_color:
                payout = bet_amount * self.multipliers[result_color]
                net_win = payout - bet_amount
                return payout, net_win
            else:
                return 0, -bet_amount
        
        elif bet_type == "multiple":
            bets = color_or_bets
            colors = ["black", "red", "blue", "gold"]
            total_payout = 0
            total_bet = sum(bets)
            
            for i, bet_amount in enumerate(bets):
                if colors[i] == result_color and bet_amount > 0:
                    total_payout += bet_amount * self.multipliers[result_color]
            
            net_win = total_payout - total_bet
            return total_payout, net_win
        
        return 0, 0

    def get_base_animation_path(self, result_position, result_color):
        animation_variant = random.randint(0, 2)
        base_path = os.path.join(
            self.results_folder, 
            f"colors_wheel_{result_color}_{result_position}_{animation_variant}.webp"
        )
        
        return base_path

    def parse_bet(self, args):
        
        if len(args) == 4:
            try:
                bets = [int(arg) for arg in args]
                if any(bet < 0 for bet in bets):
                    return None, "All bets must be positive numbers"
                return ("multiple", bets, None), None
            except ValueError:
                return None, "All bets must be numbers"
        
        elif len(args) >= 2:
            amount_str = args[0]
            color = args[1].lower()
            
            if color not in self.valid_bets:
                return None, f"Invalid color. Use: {', '.join(self.valid_bets)}"
            
            return ("single", color, amount_str), None
        
        else:
            return None, "Invalid bet format. Use: /colors <amount> <color> OR /colors <black_bet> <red_bet> <blue_bet> <gold_bet>"

    def validate_bet_amount(self, bet_info, user_balance):
        bet_type, color_or_bets, amount_str = bet_info
        
        if bet_type == "single":
            try:
                amount = int(amount_str)
            except ValueError:
                return None, "Bet amount must be a number"
            
            if amount <= 0:
                return None, "Bet amount must be positive"
            
            if amount > user_balance:
                return None, f"Insufficient balance. You have: {user_balance}"
            
            return amount, None
        
        elif bet_type == "multiple":
            bets = color_or_bets
            total_bet = sum(bets)
            
            if total_bet <= 0:
                return None, "Total bet must be positive"
            
            if total_bet > user_balance:
                return None, f"Insufficient balance. Total bet: {total_bet}, you have: {user_balance}"
            
            return total_bet, None
        
        return None, "Invalid bet type"

    def add_to_history(self, result_color, result_position):
        if not hasattr(self, 'cache'):
            return
        
        history_key = "colors_history"
        max_history = 25
        
        history = self.cache.get_setting(history_key, [])
        history.insert(0, {
            "color": result_color,
            "position": result_position,
            "timestamp": time.time()
        })
        
        if len(history) > max_history:
            history = history[:max_history]
        
        self.cache.set_setting(history_key, history)
        
        print(f"[COLORS HISTORY] Added {result_color} at position {result_position}")
        print(f"[COLORS HISTORY] Total history entries: {len(history)}")

    def get_history(self, include_current=False, current_result=None):
        if not hasattr(self, 'cache'):
            return []
        
        history_key = "colors_history"
        history = self.cache.get_setting(history_key, [])
        
        if include_current and current_result:
            temp_history = history.copy()
            temp_history.insert(0, current_result)
            
            while len(temp_history) < 25:
                temp_history.append({"color": "black", "position": 0, "timestamp": 0})
            
            return temp_history[:25]
        else:
            while len(history) < 25:
                history.append({"color": "black", "position": 0, "timestamp": 0})
            
            return history[:25]

    def generate_history_overlay(self, width=400, height=50, include_current=False, current_result=None):
        history = self.get_history(include_current=include_current, current_result=current_result)
        
        try:
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            total_items = 25
            bar_width = 12
            spacing = 3
            bar_height = 36
            
            total_width_needed = (total_items * bar_width) + ((total_items - 1) * spacing)
            start_x = (width - total_width_needed) // 2
            bar_y_start = (height - bar_height) // 2
            
            for i in range(total_items):
                history_index = total_items - 1 - i
                
                if history_index < len(history):
                    item = history[history_index]
                    color_name = item.get("color", "black")
                else:
                    color_name = "black"
                
                color_rgb = self.history_colors.get(color_name, self.history_colors["black"])
                
                alpha = int(255 * (0.3 + (i * 0.04)))
                if alpha > 255:
                    alpha = 255
                
                bar_color = color_rgb + (alpha,)
                
                x_start = start_x + (i * (bar_width + spacing))
                x_end = x_start + bar_width
                draw.rectangle([(x_start, bar_y_start), (x_end - 1, bar_y_start + bar_height - 1)], 
                              fill=bar_color)
            
            return overlay
            
        except Exception as e:
            print(f"Error generating history overlay: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _create_multipliers_overlay(self, width, height):
        try:
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
            except:
                font = ImageFont.load_default()
            
            colors_info = [
                ("black", self.multipliers["black"]),
                ("red", self.multipliers["red"]),
                ("blue", self.multipliers["blue"]),
                ("gold", self.multipliers["gold"])
            ]
            
            total_text_width = 0
            multipliers = []
            
            for color_key, multiplier in colors_info:
                text = f"x{multiplier}"
                color = self.history_colors[color_key]
                multipliers.append((text, color))
                bbox = font.getbbox(text)
                total_text_width += bbox[2] - bbox[0]
            
            spacing = 40
            total_width_needed = total_text_width + (len(multipliers) - 1) * spacing
            
            x_start = (width - total_width_needed) // 2
            y = (height - 28) // 2
            
            for text, color in multipliers:
                bbox = font.getbbox(text)
                text_width = bbox[2] - bbox[0]
                
                draw.text(
                    (x_start + 2, y + 2),
                    text,
                    font=font,
                    fill=(0, 0, 0, 180),
                    stroke_width=2,
                    stroke_fill=(0, 0, 0, 255)
                )
                
                draw.text(
                    (x_start, y),
                    text,
                    font=font,
                    fill=color + (255,),
                    stroke_width=2,
                    stroke_fill=(0, 0, 0, 255)
                )
                
                x_start += text_width + spacing
            
            return overlay
            
        except Exception as e:
            print(f"Error creating multipliers overlay: {e}")
            return None

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache

        animated = True
        if len(args) >= 2 and args[-1].lower() == "x":
            animated = False
            args = args[:-1]

        if len(args) < 1:
            self._send_error_image("invalid_usage_colors", sender, file_queue)
            return ""

        bet_info, error = self.parse_bet(args)
        if error:
            self._send_error_image("invalid_usage_colors", sender, file_queue)
            return ""

        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 1)
        if error:
            if "Insufficient balance" in error:
                self._send_error_image("insufficient_funds", sender, file_queue)
            else:
                self._send_error_image("validation_error", sender, file_queue)
            return ""

        balance_before = user["balance"]

        total_bet, error = self.validate_bet_amount(bet_info, balance_before)
        if error:
            self._send_error_image("invalid_usage_colors", sender, file_queue)
            return ""

        result_position = random.randint(0, 53)
        result_color = self.get_color_at_position(result_position)

        payout, net_win = self.calculate_win(bet_info, result_position)
        new_balance = balance_before + net_win

        self.update_user_balance(user_id, new_balance)

        user_info_before = self.create_user_info(sender, total_bet, 0, balance_before, user.copy())
        newLevel, newLevelProgress = self.cache.add_experience(user_id, net_win, sender, file_queue)
        base_animation_path = self.get_base_animation_path(result_position, result_color)
        
        user["level"] = newLevel
        user["level_progress"] = newLevelProgress
        
        if net_win > 0:
            win_display = payout
            user_info_after = self.create_user_info(sender, total_bet, win_display, new_balance, user)
        elif net_win < 0:
            loss_display = abs(net_win)
            user_info_after = self.create_user_info(sender, total_bet, -loss_display, new_balance, user)
        else:
            user_info_after = self.create_user_info(sender, total_bet, 0, new_balance, user)

        result_path, error = self.generate_animation_with_background_box(
            base_animation_path, 
            user_id, 
            user, 
            user_info_before, 
            user_info_after,
            result_color,
            result_position,
            animated=animated
        )
        
        if error:
            self._send_error_image("animation_error", sender, file_queue )
            return ""
        
        file_queue.put(result_path)
        
        bet_type, color_or_bets, amount_str = bet_info
        
        if bet_type == "single":
            color = color_or_bets
            bet_amount = int(amount_str) if amount_str else 0
            bet_info_str = f"{bet_amount} on {color}"
            win_str = f"WIN: {payout} (+{net_win})" if color == result_color else f"LOSE: {bet_amount}"
        else:
            bets = color_or_bets
            bet_info_str = f"multiple bets: black={bets[0]}, red={bets[1]}, blue={bets[2]}, gold={bets[3]}"
            win_str = f"WIN: {payout} (+{net_win})" if net_win > 0 else f"LOSE: {abs(net_win)}" if net_win < 0 else "DRAW"
        
        print(f"COLORS: {sender} bet {bet_info_str} | Result: {result_color} (pos {result_position}) | {win_str} | Balance: {balance_before} -> {new_balance}")
        
        return None

    def generate_animation_with_background_box(self, base_animation_path, user_id, user, user_info_before, 
                                             user_info_after, result_color, result_position, animated=True):
        try:
            from AnimationGenerator import AnimationGenerator
            from utils import _get_unique_id
            
            user_avatar_path = self.cache.get_avatar_path(user_id)
            user_background_path = self.cache.get_background_path(user_id)
            timestamp = _get_unique_id()
            temp_dir = self.get_app_path("temp")
            output_path = os.path.join(temp_dir, f"{self.game_name}_with_background_box_{timestamp}.webp")
            
            if animated:
                result_path = self._generate_with_background_box(
                    anim_path=base_animation_path,
                    avatar_path=user_avatar_path,
                    bg_path=user_background_path,
                    user_info_before=user_info_before,
                    user_info_after=user_info_after,
                    result_color=result_color,
                    result_position=result_position,
                    output_path=output_path
                )
            else:
                result_path = self._generate_static_with_background_box(
                    anim_path=base_animation_path,
                    avatar_path=user_avatar_path,
                    bg_path=user_background_path,
                    user_info_after=user_info_after,
                    result_color=result_color,
                    result_position=result_position,
                    output_path=output_path
                )
            
            return result_path, None
            
        except Exception as e:
            print(f"Error generating animation with background box: {e}")
            import traceback
            traceback.print_exc()
            self.add_to_history(result_color, result_position)
            return self.generate_animation(
                base_animation_path, user_id, user, 
                user_info_before, user_info_after, 
                animated=animated
            )

    def _generate_with_background_box(self, anim_path, avatar_path, bg_path, 
                                    user_info_before, user_info_after, 
                                    result_color, result_position, output_path):
        img = Image.open(anim_path)
        n_frames = getattr(img, "n_frames", 1)
        is_animated = n_frames > 1
        img.seek(0)
        first_frame = img.convert("RGBA")
        
        frame_width, frame_height = first_frame.size
        
        print(f"[DEBUG] Frame size: {frame_width}x{frame_height}")
        
        user_bar_height = 25
        
        margin = 20
        bg_frame_width = frame_width + (2 * margin)
        
        bg_frame_height = frame_height + (2 * margin) + user_bar_height
        
        section_width = int(frame_width * 0.8)
        history_height = 50
        multipliers_height = 50
        section_height = history_height + multipliers_height + 40
        
        section_x = margin + (frame_width - section_width) // 2
        
        history_y_offset = 220
        section_y = margin + history_y_offset
        
        history_y = 20
        multipliers_y = history_y + history_height + 25
        
        current_result = {
            "color": result_color,
            "position": result_position,
            "timestamp": time.time()
        }
        
        multipliers_overlay = self._create_multipliers_overlay(section_width, multipliers_height)
        
        history_overlay = self.generate_history_overlay(
            width=section_width, 
            height=history_height,
            include_current=False
        )
        
        bg_img = Image.open(bg_path).convert("RGBA").resize((bg_frame_width, bg_frame_height))
        
        avatar_size = 90
        avatar = Image.open(avatar_path).convert("RGBA")
        avatar = avatar.resize((avatar_size, avatar_size))
        
        avatar_mask = Image.new("L", (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(avatar_mask)
        mask_draw.rounded_rectangle((0, 0, avatar_size, avatar_size), radius=5, fill=255)
        
        try:
            from AnimationGenerator import AnimationGenerator
            generator = AnimationGenerator()
            bet_icon = generator._load_and_preprocess_image(generator.BET_ICON_PATH, resize=(25, 25))
            balance_icon = generator._load_and_preprocess_image(generator.BALANCE_ICON_PATH, resize=(25, 25))
        except:
            bet_icon = Image.new("RGBA", (25, 25), (255, 255, 255, 255))
            balance_icon = Image.new("RGBA", (25, 25), (255, 255, 255, 255))
        
        try:
            font_small = ImageFont.truetype("DejaVuSans-Bold.ttf", frame_width // 26)
            font_result = ImageFont.truetype("DejaVuSans-Bold.ttf", frame_width // 10)
        except:
            font_small = font_result = ImageFont.load_default()
        
        def create_bars(user_info, font, bet_icon_img, balance_icon_img):
            bars = []
            bar_height = 40
            min_bar_width = 80
            
            nick_lines = user_info["username"].split(" ")
            max_width = max([self._get_text_width(w, font) for w in nick_lines])
            width = max(max_width + 20, min_bar_width)
            nick_bar = Image.new("RGBA", (width, bar_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(nick_bar)
            draw.rounded_rectangle((0, 0, width, bar_height), radius=7, fill=(40, 40, 40, 255))
            
            total_height = sum([font.getbbox(w)[3] - font.getbbox(w)[1] for w in nick_lines])
            y_offset = (bar_height - total_height) // 2 - 5
            for w in nick_lines:
                bbox = font.getbbox(w)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                draw.text(
                    (x, y_offset),
                    w,
                    font=font,
                    fill=(255, 255, 255, 255),
                    stroke_width=2,
                    stroke_fill=(0, 0, 0, 255),
                )
                y_offset += bbox[3] - bbox[1]
            bars.append(nick_bar)
            
            bet_text = f"{user_info['bet']}"
            bet_text_width = self._get_text_width(bet_text, font)
            width = max(bet_icon_img.width + 5 + bet_text_width + 10, min_bar_width)
            bet_bar = Image.new("RGBA", (width, bar_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(bet_bar)
            draw.rounded_rectangle((0, 0, width, bar_height), radius=7, fill=(40, 40, 40, 255))
            y_icon = (bar_height - bet_icon_img.height) // 2
            bet_bar.paste(bet_icon_img, (5, y_icon), bet_icon_img)
            x_text = bet_icon_img.width + 10
            y_text = (bar_height - (font.getbbox(bet_text)[3] - font.getbbox(bet_text)[1])) // 2 - 5
            draw.text(
                (x_text, y_text),
                bet_text,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=2,
                stroke_fill=(0, 0, 0, 255),
            )
            bars.append(bet_bar)
            
            balance_text = f"{user_info['balance']}"
            balance_text_width = self._get_text_width(balance_text, font)
            width = max(balance_icon_img.width + 5 + balance_text_width + 10, min_bar_width)
            balance_bar = Image.new("RGBA", (width, bar_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(balance_bar)
            draw.rounded_rectangle((0, 0, width, bar_height), radius=7, fill=(40, 40, 40, 255))
            y_icon = (bar_height - balance_icon_img.height) // 2
            balance_bar.paste(balance_icon_img, (5, y_icon), balance_icon_img)
            x_text = balance_icon_img.width + 10
            y_text = (bar_height - (font.getbbox(balance_text)[3] - font.getbbox(balance_text)[1])) // 2 - 5
            draw.text(
                (x_text, y_text),
                balance_text,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=2,
                stroke_fill=(0, 0, 0, 255),
            )
            bars.append(balance_bar)
            
            return bars
        
        def create_avatar_bar(avatar_img, avatar_mask_img, user_info, font):
            bar = Image.new("RGBA", (avatar_size, avatar_size), (0, 0, 0, 0))
            bar.paste(avatar_img, (0, 0), avatar_mask_img)
            draw = ImageDraw.Draw(bar)
            
            level_text = str(user_info["level"])
            level_width = self._get_text_width(level_text, font)
            level_x = avatar_size - level_width - 3
            draw.text(
                (level_x, 3),
                level_text,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=2,
                stroke_fill=(0, 0, 0, 255),
            )
            
            bar_height_px = 6
            bar_x0 = 3
            bar_y0 = avatar_size - bar_height_px - 3
            bar_width_full = avatar_size - 6
            progress = user_info.get("level_progress", 0.1)
            bar_x1 = int(bar_width_full * progress)
            bar_y1 = bar_y0 + bar_height_px
            draw.rectangle((bar_x0, bar_y0, bar_x1, bar_y1), fill=(0, 120, 255, 255))
            draw.rectangle(
                (bar_x0, bar_y0, bar_width_full, bar_y1),
                outline=(255, 255, 255, 255),
                width=1,
            )
            
            return bar
        
        def _get_text_width(text, font):
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0]
        
        self._get_text_width = _get_text_width
        
        bars_before = create_bars(user_info_before, font_small, bet_icon, balance_icon)
        bars_after = create_bars(user_info_after, font_small, bet_icon, balance_icon)
        avatar_bar_before = create_avatar_bar(avatar, avatar_mask, user_info_before, font_small)
        avatar_bar_after = create_avatar_bar(avatar, avatar_mask, user_info_after, font_small)
        
        win_value = user_info_after["win"]
        if win_value > 0:
            label, color = "Win:", (0, 255, 0, 255)
        elif win_value < 0:
            label, color = "Lose:", (255, 0, 0, 255)
        else:
            label, color = "Win:", (200, 200, 200, 255)
        win_text = f"{label} {abs(win_value)}$"
        
        bbox = font_result.getbbox(win_text)
        win_text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        text_x = margin + (frame_width - win_text_width) // 2
        text_y = margin + (frame_height - text_height) // 2 - 100
        
        new_width = bg_frame_width
        new_height = bg_frame_height
        
        user_bar_start_y = margin + frame_height
        dark_bar_start_y = user_bar_start_y + user_bar_height
        
        frames, durations = [], []
        frame_skip = 2
        
        included_frames = list(range(0, n_frames, frame_skip))
        
        last_frame_index = n_frames - 1
        if is_animated and last_frame_index not in included_frames:
            included_frames.append(last_frame_index)
        
        included_frames.sort()
        
        history_added = False
        
        for i in included_frames:
            if is_animated:
                img.seek(i)
                frame = img.convert("RGBA")
            else:
                frame = first_frame.copy()
            
            combined = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
            
            combined.paste(bg_img, (0, 0))
            
            combined.paste(frame, (margin, margin), frame)
            
            if history_overlay:
                combined.alpha_composite(history_overlay, (section_x, section_y + history_y))
            
            if multipliers_overlay:
                combined.alpha_composite(multipliers_overlay, (section_x, section_y + multipliers_y))
            
            draw = ImageDraw.Draw(combined)
            
            draw.rectangle([0, user_bar_start_y, new_width, dark_bar_start_y + 20], 
                        fill=(40, 40, 40, 255))
            
            if i < n_frames - 1 or not is_animated:
                avatar_bar, bars = avatar_bar_before, bars_before
            else:
                avatar_bar, bars = avatar_bar_after, bars_after
            
            avatar_x = margin + frame_width - avatar_bar.width - 15
            avatar_overlap = 45
            avatar_y = user_bar_start_y - avatar_overlap
            
            combined.paste(avatar_bar, (avatar_x, avatar_y), avatar_bar)
            
            total_bars_width = sum([b.width for b in bars])
            x = margin + (frame_width - total_bars_width - avatar_bar.width - 30) // (len(bars) + 1)
            y = user_bar_start_y + 5
            
            for b in bars:
                combined.paste(b, (x, y), b)
                x += b.width + 10
            
            if (i == last_frame_index or not is_animated) and not history_added:
                self.add_to_history(result_color, result_position)
                history_added = True
                
                history_overlay = self.generate_history_overlay(
                    width=section_width, 
                    height=history_height,
                    include_current=True,
                    current_result=current_result
                )
            
            if (i >= n_frames - 1 or not is_animated):
                draw_center = ImageDraw.Draw(combined)
                draw_center.text(
                    (text_x, text_y),
                    win_text,
                    font=font_result,
                    fill=color,
                    stroke_width=2,
                    stroke_fill=(0, 0, 0, 255),
                )
            
            frames.append(combined)
            
            if is_animated:
                base_duration = img.info.get("duration", 100)
                is_last_frame = (i == last_frame_index)
                duration = base_duration * 1.4 if is_last_frame else base_duration * 1.4
            else:
                duration = 100
            
            durations.append(duration)
        
        if is_animated and len(frames) > 1:
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=0,
                format="WEBP",
                quality=60,
                method=5,
                lossless=False,
                minimize_size=True,
            )
        else:
            frames[0].save(output_path, format="WEBP", quality=60, method=5)
        
        print(f"[DEBUG] Animation saved to: {output_path}")
        print(f"[DEBUG] Final image size: {new_width}x{new_height}")
        print(f"[DEBUG] User bar position: {user_bar_start_y} to {dark_bar_start_y}")
        print(f"[DEBUG] Avatar overlap: {avatar_overlap}px")
        
        return output_path

    def _generate_static_with_background_box(self, anim_path, avatar_path, bg_path, 
                                        user_info_after, result_color, result_position, output_path):
        img = Image.open(anim_path)
        
        if getattr(img, "is_animated", False):
            img.seek(img.n_frames - 1)
        
        base_frame = img.convert("RGBA")
        frame_width, frame_height = base_frame.size
        
        user_bar_height = 25
        
        margin = 20
        bg_frame_width = frame_width + (2 * margin)
        
        bg_frame_height = frame_height + (2 * margin) + user_bar_height
        
        section_width = int(frame_width * 0.8)
        history_height = 50
        multipliers_height = 50
        section_height = history_height + multipliers_height + 40
        
        section_x = margin + (frame_width - section_width) // 2
        
        history_y_offset = 220
        section_y = margin + history_y_offset
        
        history_y = 20
        multipliers_y = history_y + history_height + 25
        
        multipliers_overlay = self._create_multipliers_overlay(section_width, multipliers_height)
        
        self.add_to_history(result_color, result_position)
        
        current_result = {
            "color": result_color,
            "position": result_position,
            "timestamp": time.time()
        }
        
        history_overlay = self.generate_history_overlay(
            width=section_width, 
            height=history_height,
            include_current=True,
            current_result=current_result
        )
        
        bg_img = Image.open(bg_path).convert("RGBA").resize((bg_frame_width, bg_frame_height))
        
        avatar_size = 90
        avatar = Image.open(avatar_path).convert("RGBA")
        avatar = avatar.resize((avatar_size, avatar_size))
        
        avatar_mask = Image.new("L", (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(avatar_mask)
        mask_draw.rounded_rectangle((0, 0, avatar_size, avatar_size), radius=5, fill=255)
        
        try:
            from AnimationGenerator import AnimationGenerator
            generator = AnimationGenerator()
            bet_icon = generator._load_and_preprocess_image(generator.BET_ICON_PATH, resize=(25, 25))
            balance_icon = generator._load_and_preprocess_image(generator.BALANCE_ICON_PATH, resize=(25, 25))
        except:
            bet_icon = Image.new("RGBA", (25, 25), (255, 255, 255, 255))
            balance_icon = Image.new("RGBA", (25, 25), (255, 255, 255, 255))
        
        try:
            font_small = ImageFont.truetype("DejaVuSans-Bold.ttf", frame_width // 26)
            font_result = ImageFont.truetype("DejaVuSans-Bold.ttf", frame_width // 10)
        except:
            font_small = font_result = ImageFont.load_default()
        
        def create_bars(user_info, font, bet_icon_img, balance_icon_img):
            bars = []
            bar_height = 40
            min_bar_width = 80
            
            nick_lines = user_info["username"].split(" ")
            max_width = max([self._get_text_width(w, font) for w in nick_lines])
            width = max(max_width + 20, min_bar_width)
            nick_bar = Image.new("RGBA", (width, bar_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(nick_bar)
            draw.rounded_rectangle((0, 0, width, bar_height), radius=7, fill=(40, 40, 40, 255))
            
            total_height = sum([font.getbbox(w)[3] - font.getbbox(w)[1] for w in nick_lines])
            y_offset = (bar_height - total_height) // 2 - 5
            for w in nick_lines:
                bbox = font.getbbox(w)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                draw.text(
                    (x, y_offset),
                    w,
                    font=font,
                    fill=(255, 255, 255, 255),
                    stroke_width=2,
                    stroke_fill=(0, 0, 0, 255),
                )
                y_offset += bbox[3] - bbox[1]
            bars.append(nick_bar)
            
            bet_text = f"{user_info['bet']}"
            bet_text_width = self._get_text_width(bet_text, font)
            width = max(bet_icon_img.width + 5 + bet_text_width + 10, min_bar_width)
            bet_bar = Image.new("RGBA", (width, bar_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(bet_bar)
            draw.rounded_rectangle((0, 0, width, bar_height), radius=7, fill=(40, 40, 40, 255))
            y_icon = (bar_height - bet_icon_img.height) // 2
            bet_bar.paste(bet_icon_img, (5, y_icon), bet_icon_img)
            x_text = bet_icon_img.width + 10
            y_text = (bar_height - (font.getbbox(bet_text)[3] - font.getbbox(bet_text)[1])) // 2 - 5
            draw.text(
                (x_text, y_text),
                bet_text,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=2,
                stroke_fill=(0, 0, 0, 255),
            )
            bars.append(bet_bar)
            
            balance_text = f"{user_info['balance']}"
            balance_text_width = self._get_text_width(balance_text, font)
            width = max(balance_icon_img.width + 5 + balance_text_width + 10, min_bar_width)
            balance_bar = Image.new("RGBA", (width, bar_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(balance_bar)
            draw.rounded_rectangle((0, 0, width, bar_height), radius=7, fill=(40, 40, 40, 255))
            y_icon = (bar_height - balance_icon_img.height) // 2
            balance_bar.paste(balance_icon_img, (5, y_icon), balance_icon_img)
            x_text = balance_icon_img.width + 10
            y_text = (bar_height - (font.getbbox(balance_text)[3] - font.getbbox(balance_text)[1])) // 2 - 5
            draw.text(
                (x_text, y_text),
                balance_text,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=2,
                stroke_fill=(0, 0, 0, 255),
            )
            bars.append(balance_bar)
            
            return bars
        
        def create_avatar_bar(avatar_img, avatar_mask_img, user_info, font):
            bar = Image.new("RGBA", (avatar_size, avatar_size), (0, 0, 0, 0))
            bar.paste(avatar_img, (0, 0), avatar_mask_img)
            draw = ImageDraw.Draw(bar)
            
            level_text = str(user_info["level"])
            level_width = self._get_text_width(level_text, font)
            level_x = avatar_size - level_width - 3
            draw.text(
                (level_x, 3),
                level_text,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=2,
                stroke_fill=(0, 0, 0, 255),
            )
            
            bar_height_px = 6
            bar_x0 = 3
            bar_y0 = avatar_size - bar_height_px - 3
            bar_width_full = avatar_size - 6
            progress = user_info.get("level_progress", 0.1)
            bar_x1 = int(bar_width_full * progress)
            bar_y1 = bar_y0 + bar_height_px
            draw.rectangle((bar_x0, bar_y0, bar_x1, bar_y1), fill=(0, 120, 255, 255))
            draw.rectangle(
                (bar_x0, bar_y0, bar_width_full, bar_y1),
                outline=(255, 255, 255, 255),
                width=1,
            )
            
            return bar
        
        def _get_text_width(text, font):
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0]
        
        self._get_text_width = _get_text_width
        
        bars = create_bars(user_info_after, font_small, bet_icon, balance_icon)
        avatar_bar = create_avatar_bar(avatar, avatar_mask, user_info_after, font_small)
        
        win_value = user_info_after["win"]
        if win_value > 0:
            label, color = "Win:", (0, 255, 0, 255)
        elif win_value < 0:
            label, color = "Lose:", (255, 0, 0, 255)
        else:
            label, color = "Win:", (200, 200, 200, 255)
        
        win_text = f"{label} {abs(win_value)}$"
        bbox = font_result.getbbox(win_text)
        win_text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        text_x = margin + (frame_width - win_text_width) // 2
        text_y = margin + (frame_height - text_height) // 2 - 100
        
        new_width = bg_frame_width
        new_height = bg_frame_height
        
        user_bar_start_y = margin + frame_height
        dark_bar_start_y = user_bar_start_y + user_bar_height
        
        final_img = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
        
        final_img.paste(bg_img, (0, 0))
        
        final_img.paste(base_frame, (margin, margin), base_frame)
        
        if history_overlay:
            final_img.alpha_composite(history_overlay, (section_x, section_y + history_y))
        
        if multipliers_overlay:
            final_img.alpha_composite(multipliers_overlay, (section_x, section_y + multipliers_y))
        
        draw = ImageDraw.Draw(final_img)
        
        draw.rectangle([0, user_bar_start_y, new_width, dark_bar_start_y + 20], 
                    fill=(40, 40, 40, 255))
        
        avatar_x = margin + frame_width - avatar_bar.width - 15
        avatar_overlap = 45
        avatar_y = user_bar_start_y - avatar_overlap
        
        final_img.paste(avatar_bar, (avatar_x, avatar_y), avatar_bar)
        
        total_bars_width = sum([b.width for b in bars])
        x = margin + (frame_width - total_bars_width - avatar_bar.width - 30) // (len(bars) + 1)
        y = user_bar_start_y + 5
        
        for b in bars:
            final_img.paste(b, (x, y), b)
            x += b.width + 10
        
        draw_center = ImageDraw.Draw(final_img)
        draw_center.text(
            (text_x, text_y),
            win_text,
            font=font_result,
            fill=color,
            stroke_width=2,
            stroke_fill=(0, 0, 0, 255)
        )
        
        final_img.save(output_path, format="WEBP")
        
        print(f"[DEBUG STATIC] Final image size: {new_width}x{new_height}")
        print(f"[DEBUG STATIC] User bar position: {user_bar_start_y} to {dark_bar_start_y}")
        print(f"[DEBUG STATIC] Avatar overlap: {avatar_overlap}px")
        
        return output_path

def register():
    plugin = ColorsPlugin()
    return {
        "name": "colors",
        "aliases": ["/c"],
        "description": "Colors game: /colors <amount> <color> (black/red/blue/gold) OR /colors <black_bet> <red_bet> <blue_bet> <gold_bet>",
        "execute": plugin.execute_game
    }