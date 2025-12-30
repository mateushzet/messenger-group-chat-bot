import random
import os
import time
import math
from base_game_plugin import BaseGamePlugin
from logger import logger
from PIL import Image, ImageDraw, ImageFont

class CrashPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="crash",
            results_folder=self.get_asset_path("crash", "crash_results"),
            valid_bets=[]
        )
        
        self.error_folder = self.get_asset_path("errors")
        os.makedirs(self.error_folder, exist_ok=True)
        
        self.multipliers = [
            1.00, 1.01, 1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09,
            1.10, 1.11, 1.12, 1.13, 1.14, 1.15, 1.16, 1.17, 1.18, 1.19,
            1.20, 1.21, 1.22, 1.23, 1.24, 1.25, 1.26, 1.27, 1.28, 1.29,
            1.30, 1.31, 1.32, 1.33, 1.34, 1.35, 1.36, 1.37, 1.38, 1.39,
            1.40, 1.41, 1.42, 1.43, 1.44, 1.45, 1.46, 1.47, 1.48, 1.49,
            1.50, 1.51, 1.52, 1.53, 1.54, 1.55, 1.56, 1.57, 1.58, 1.59,
            1.60, 1.61, 1.62, 1.63, 1.64, 1.65, 1.66, 1.67, 1.68, 1.69,
            1.70, 1.71, 1.72, 1.73, 1.74, 1.75, 1.76, 1.77, 1.78, 1.79,
            1.80, 1.81, 1.82, 1.83, 1.84, 1.85, 1.86, 1.87, 1.88, 1.89,
            1.90, 1.91, 1.92, 1.93, 1.94, 1.95, 1.96, 1.97, 1.98, 1.99,
            2.00, 2.01, 2.02, 2.03, 2.04, 2.05, 2.06, 2.07, 2.08, 2.09,
            2.10, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16, 2.17, 2.18, 2.19,
            2.20, 2.21, 2.22, 2.23, 2.24, 2.25, 2.26, 2.27, 2.28, 2.29,
            2.30, 2.31, 2.32, 2.33, 2.34, 2.35, 2.36, 2.37, 2.38, 2.39,
            2.40, 2.41, 2.42, 2.43, 2.44, 2.45, 2.46, 2.47, 2.48, 2.49,
            2.50, 2.51, 2.52, 2.53, 2.54, 2.55, 2.56, 2.57, 2.58, 2.59,
            2.60, 2.61, 2.62, 2.63, 2.64, 2.65, 2.66, 2.67, 2.68, 2.69,
            2.70, 2.71, 2.72, 2.73, 2.74, 2.75, 2.76, 2.77, 2.78, 2.79,
            2.80, 2.81, 2.82, 2.83, 2.84, 2.85, 2.86, 2.87, 2.88, 2.89,
            2.90, 2.91, 2.92, 2.93, 2.94, 2.95, 2.96, 2.97, 2.98, 2.99,
            3.00, 3.00, 3.05, 3.10, 3.15, 3.20, 3.25, 3.30, 3.35, 3.40,
            3.45, 3.50, 3.55, 3.60, 3.65, 3.70, 3.75, 3.80, 3.85, 3.90,
            3.95, 4.00, 4.05, 4.10, 4.15, 4.20, 4.25, 4.31, 4.36, 4.40,
            4.45, 4.51, 4.55, 4.60, 4.66, 4.70, 4.75, 4.80, 4.85, 4.90,
            4.95, 5.00, 5.05, 5.11, 5.15, 5.20, 5.25, 5.30, 5.35, 5.41,
            5.45, 5.50, 5.55, 5.61, 5.66, 5.71, 5.76, 5.81, 5.86, 5.90,
            5.95, 6.00, 6.06, 6.10, 6.15, 6.21, 6.25, 6.31, 6.35, 6.41,
            6.45, 6.50, 6.56, 6.61, 6.65, 6.70, 6.76, 6.81, 6.86, 6.91,
            6.96, 7.01, 7.06, 7.11, 7.16, 7.21, 7.25, 7.30, 7.36, 7.41,
            7.45, 7.50, 7.56, 7.60, 7.66, 7.71, 7.75, 7.81, 7.85, 7.91,
            7.96, 8.00, 8.06, 8.10, 8.16, 8.21, 8.25, 8.30, 8.36, 8.41,
            8.46, 8.50, 8.55, 8.61, 8.66, 8.71, 8.76, 8.81, 8.86, 8.91,
            8.96, 9.01, 9.06, 9.11, 9.16, 9.20, 9.25, 9.30, 9.36, 9.41,
            9.46, 9.50, 9.56, 9.61, 9.66, 9.70, 9.76, 9.81, 9.85, 9.91,
            9.96, 10.01, 10.01, 10.10, 10.20, 10.30, 10.40, 10.50, 10.61, 10.71,
            10.81, 10.90, 11.01, 11.10, 11.21, 11.30, 11.41, 11.51, 11.60, 11.71,
            11.81, 11.91, 12.01, 12.11, 12.21, 12.31, 12.41, 12.51, 12.61, 12.72,
            12.80, 12.91, 13.01, 13.10, 13.21, 13.32, 13.41, 13.52, 13.61, 13.70,
            13.81, 13.91, 14.00, 14.12, 14.21, 14.31, 14.40, 14.50, 14.62, 14.72,
            14.82, 14.92, 15.02, 15.12, 15.20, 15.30, 15.41, 15.51, 15.61, 15.72,
            15.80, 15.91, 16.01, 16.10, 16.21, 16.32, 16.40, 16.51, 16.60, 16.71,
            16.80, 16.91, 17.00, 17.12, 17.21, 17.32, 17.41, 17.51, 17.62, 17.72,
            17.81, 17.91, 18.00, 18.12, 18.22, 18.31, 18.41, 18.51, 18.60, 18.70,
            18.80, 18.90, 19.02, 19.10, 19.20, 19.30, 19.40, 19.51, 19.61, 19.71,
            19.82, 19.92, 20.02, 20.02, 21.02, 22.02, 23.02, 24.02, 25.03, 26.01,
            27.03, 28.01, 29.02, 30.03, 31.04, 32.03, 33.01, 34.02, 35.01, 36.03,
            37.04, 38.02, 39.02, 40.05, 41.05, 42.02, 43.02, 44.04, 45.02, 46.03,
            47.05, 48.04, 49.05, 50.01, 51.06, 52.06, 53.02, 54.06, 55.05, 56.05,
            57.01, 58.05, 59.04, 60.04, 61.06, 62.02, 63.07, 64.06, 65.07, 66.01,
            67.04, 68.01, 69.07, 70.07, 71.08, 72.01, 73.05, 74.01, 75.07, 76.05,
            77.05, 78.06, 79.08, 80.02, 81.07, 82.03, 83.00, 84.09, 85.08, 86.09,
            87.00, 88.03, 89.07, 90.02, 91.08, 92.05, 93.02, 94.01, 95.00, 96.01,
            97.02, 98.05, 99.08, 100.00,
        ]
        
        self.crash_animation_path = os.path.join(self.get_asset_path("crash"), "crash_animation.webp")
        
        self.history_multipliers = []
        self.max_history = 20
        
        self.house_edge = 0.01

    def generate_crash_multiplier(self):

        r = random.random()
        
        multiplier = (1 - self.house_edge) / (1 - r)
        
        closest_multiplier = min(self.multipliers, key=lambda x: abs(x - multiplier))
        
        if closest_multiplier < 1.00:
            closest_multiplier = 1.00
            
        return closest_multiplier

    def get_multiplier_index(self, multiplier):
        for i, m in enumerate(self.multipliers):
            if abs(m - multiplier) < 0.001:
                return i
        return 0

    def calculate_win(self, bet_amount, cashout_multiplier, crash_multiplier):

        if cashout_multiplier is None:
            return 0, -bet_amount, crash_multiplier
        
        if cashout_multiplier < crash_multiplier:
            payout_float = bet_amount * cashout_multiplier
            payout = int(math.floor(payout_float))
            net_win = payout - bet_amount
            return payout, net_win, cashout_multiplier
        else:
            return 0, -bet_amount, crash_multiplier

    def parse_bet(self, args):
        if len(args) < 2:
            return None, "Usage: /crash <amount> <cashout_multiplier>\nExample: /crash 100 2.5 - Bet 100 and auto-cashout at 2.5x"
        
        static_mode = False
        if args[-1].lower() == 'x':
            static_mode = True
            args = args[:-1]
        
        try:
            amount = int(args[0])
            if amount <= 0:
                return None, "Bet amount must be positive"
            
            try:
                cashout = float(args[1])
                if cashout < 1.0:
                    return None, "Invalid cashout multiplier"
                if cashout > 100.0:
                    return None, "Invalid cashout multiplier"
            except ValueError:
                return None, "Cashout multiplier must be a number (e.g., 2.5)"
            
            return ("single", amount, cashout, static_mode), None
        except ValueError:
            return None, "Bet amount must be a number"

    def validate_bet_amount(self, bet_info, user_balance):
        bet_type, amount, cashout, static_mode = bet_info
        
        if amount > user_balance:
            return None, f"Insufficient balance. You have: {user_balance}"
        
        return amount, None

    def add_to_history(self, multiplier):
        if not hasattr(self, 'cache'):
            return
        
        history_key = "crash_history"
        history = self.cache.get_setting(history_key, [])
        
        history.insert(0, {
            "multiplier": multiplier,
            "timestamp": time.time()
        })
        
        if len(history) > self.max_history:
            history = history[:self.max_history]
        
        self.cache.set_setting(history_key, history)
        self.history_multipliers = history

    def get_history(self):
        if not hasattr(self, 'cache'):
            return []
        
        history = self.cache.get_setting("crash_history", [])
        
        while len(history) < self.max_history:
            history.append({"multiplier": 1.0, "timestamp": 0})
        
        return history[:self.max_history]

    def generate_vertical_history_overlay(self, width=60, height=300):
        history = self.get_history()
        
        try:
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            total_items = min(len(history), self.max_history)
            
            line_height = 16
            top_padding = 4 
            
            try:
                font_history = ImageFont.truetype("DejaVuSans-Bold.ttf", 12)
            except:
                font_history = ImageFont.load_default()
            
            for i in range(total_items):
                history_item = history[i]
                multiplier = history_item.get("multiplier", 1.0)
                
                if multiplier >= 100:
                    text = f"{multiplier:.0f}x"
                elif multiplier >= 10:
                    text = f"{multiplier:.1f}x"
                else:
                    text = f"{multiplier:.2f}x"
                
                bbox = font_history.getbbox(text)
                text_width = bbox[2] - bbox[0]
                
                text_y = top_padding + i * line_height
                
                if multiplier < 2.0:
                    color = (255, 50, 50, 255)
                elif multiplier <= 3.0:
                    color = (150, 150, 150, 255)
                else:
                    color = (0, 255, 0, 255)
                
                darken_factor = 1.0 - (i * 0.1)
                darken_factor = max(0.5, darken_factor)
                
                dark_color = tuple(int(c * darken_factor) for c in color[:3]) + (255,)
                
                text_x = (width - text_width) // 2
                
                draw.text((text_x, text_y), text, font=font_history, fill=dark_color)
            
            return overlay
            
        except Exception as e:
            print(f"Error generating vertical crash history overlay: {e}")
            import traceback
            traceback.print_exc()
            return Image.new('RGBA', (width, height), (0, 0, 0, 0))

    def _get_frame_for_multiplier(self, img, multiplier):

        n_frames = getattr(img, "n_frames", 1)
        
        if n_frames == 1:
            return 0
        
        multiplier_index = self.get_multiplier_index(multiplier)
        
        max_index = len(self.multipliers) - 1
        
        if n_frames <= max_index + 1:
            frame_index = int((multiplier_index / max_index) * (n_frames - 2))
        else:
            frame_index = multiplier_index
        
        return min(frame_index, n_frames - 2)

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        if not os.path.exists(self.crash_animation_path):
            self._send_error_image("animation_fatal_error", sender, file_queue)
            return ""
        
        if len(args) < 1:
            self._send_error_image("invalid_usage_crash", sender, file_queue)
            return ""
        
        bet_info, error = self.parse_bet(args)
        if error:
            if "Invalid cashout multiplier" in error:
                self._send_error_image("invalid_cashout_multiplier_crash", sender, file_queue)
            else:
                self._send_error_image("invalid_usage_crash", sender, file_queue)
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
            if "Insufficient balance" in error:
                self._send_error_image("insufficient_funds", sender, file_queue)
            else:
                self._send_error_image("invalid_usage_crash", sender, file_queue)
            return ""
        
        bet_type, amount, cashout_multiplier, static_mode = bet_info
        crash_multiplier = self.generate_crash_multiplier()
        
        payout, net_win, effective_multiplier = self.calculate_win(
            amount, cashout_multiplier, crash_multiplier
        )
        
        new_balance = balance_before + net_win
        
        self.update_user_balance(user_id, new_balance)
        
        user_info_before = self.create_user_info(sender, total_bet, 0, balance_before, user.copy())
        
        newLevel, newLevelProgress = self.cache.add_experience(user_id, net_win, sender, file_queue)
        
        user["level"], user["level_progress"] = newLevel, newLevelProgress
        
        if net_win > 0:
            win_display = payout
            user_info_after = self.create_user_info(sender, total_bet, win_display, new_balance, user)
        elif net_win < 0:
            loss_display = abs(net_win)
            user_info_after = self.create_user_info(sender, total_bet, -loss_display, new_balance, user)
        else:
            user_info_after = self.create_user_info(sender, total_bet, 0, new_balance, user)
        
        result_path, error = self.generate_animation_with_history(
            crash_multiplier, user_id, user, user_info_before, user_info_after, 
            effective_multiplier, cashout_multiplier, payout, net_win,
            static_mode=static_mode
        )
        
        if error:
            self._send_error_image("animation_error", sender, file_queue, error)
            return ""
        
        file_queue.put(result_path)
        
        cashout_str = f" (cashout at {cashout_multiplier}x)"
        result_str = f"CRASH at {crash_multiplier:.2f}x"
        win_str = f"WIN: {payout} (+{net_win})" if net_win > 0 else f"LOSE: {abs(net_win)}"
        
        print(f"CRASH: {sender} bet {amount}{cashout_str} | Result: {result_str} | {win_str} | Balance: {balance_before} -> {new_balance}")
        
        return None

    def generate_animation_with_history(self, crash_multiplier, user_id, user, user_info_before, user_info_after, effective_multiplier, cashout_multiplier, payout_amount, net_win, static_mode=False):
        try:
            from AnimationGenerator import AnimationGenerator
            from utils import _get_unique_id
            
            user_avatar_path = self.cache.get_avatar_path(user_id)
            user_background_path = self.cache.get_background_path(user_id)
            timestamp = _get_unique_id()
            temp_dir = self.get_app_path("temp")
            output_path = os.path.join(temp_dir, f"crash_with_history_{timestamp}.webp")
            
            img = Image.open(self.crash_animation_path)
            n_frames = getattr(img, "n_frames", 1)
            is_animated = n_frames > 1
            
            if static_mode or not is_animated:
                result_path = self._generate_static_crash(
                    img=img,
                    crash_multiplier=crash_multiplier,
                    effective_multiplier=effective_multiplier,
                    cashout_multiplier=cashout_multiplier,
                    payout_amount=payout_amount,
                    net_win=net_win,
                    avatar_path=user_avatar_path,
                    bg_path=user_background_path,
                    user_info_after=user_info_after,
                    output_path=output_path
                )
            else:
                result_path = self._generate_animated_crash(
                    img=img,
                    crash_multiplier=crash_multiplier,
                    effective_multiplier=effective_multiplier,
                    cashout_multiplier=cashout_multiplier,
                    payout_amount=payout_amount,
                    net_win=net_win,
                    avatar_path=user_avatar_path,
                    bg_path=user_background_path,
                    user_info_before=user_info_before,
                    user_info_after=user_info_after,
                    output_path=output_path
                )
            
            self.add_to_history(crash_multiplier)
            
            return result_path, None
            
        except Exception as e:
            print(f"Error generating crash animation: {e}")
            import traceback
            traceback.print_exc()
            self.add_to_history(crash_multiplier)
            return None, f"Error generating animation: {str(e)}"

    def _generate_animated_crash(self, img, crash_multiplier, effective_multiplier, cashout_multiplier,
                                payout_amount, net_win, avatar_path, bg_path, user_info_before, 
                                user_info_after, output_path):
        n_frames = getattr(img, "n_frames", 1)
        img.seek(0)
        first_frame = img.convert("RGBA")
        frame_width, frame_height = first_frame.size
        
        margin = 20
        bg_frame_width = frame_width + (2 * margin)
        bg_frame_height = frame_height + (2 * margin)
        
        history_width = 60
        history_height = frame_height
        history_overlay = self.generate_vertical_history_overlay(width=history_width, height=history_height)
        history_x = margin + frame_width - history_width
        history_y = margin
        
        bg_img = Image.open(bg_path).convert("RGBA").resize((bg_frame_width, bg_frame_height))
        avatar_size = 90
        avatar = Image.open(avatar_path).convert("RGBA").resize((avatar_size, avatar_size))
        
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
            font_result_small = ImageFont.truetype("DejaVuSans-Bold.ttf", frame_width // 20)
            font_result_medium = ImageFont.truetype("DejaVuSans-Bold.ttf", frame_width // 15)
            font_result_large = ImageFont.truetype("DejaVuSans-Bold.ttf", frame_width // 8)
        except:
            font_small = font_result_small = font_result_medium = font_result_large = ImageFont.load_default()
        
        def _get_text_width(text, font):
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0]
        
        self._get_text_width = _get_text_width
        
        def create_avatar_bar(avatar_img, user_info, font):
            avatar_size_local = avatar_img.size[0]
            bar = Image.new("RGBA", (avatar_size_local, avatar_size_local), (0, 0, 0, 0))
            
            avatar_mask = Image.new("L", (avatar_size_local, avatar_size_local), 0)
            mask_draw = ImageDraw.Draw(avatar_mask)
            mask_draw.rounded_rectangle((0, 0, avatar_size_local, avatar_size_local), radius=5, fill=255)
            
            bar.paste(avatar_img, (0, 0), avatar_mask)
            draw = ImageDraw.Draw(bar)
            
            level_text = str(user_info["level"])
            level_width = self._get_text_width(level_text, font)
            level_x = avatar_size_local - level_width - 3
            draw.text((level_x, 3), level_text, font=font, fill=(255,255,255,255), 
                     stroke_width=2, stroke_fill=(0,0,0,255))
            
            bar_height_px = 6
            bar_x0 = 3
            bar_y0 = avatar_size_local - bar_height_px - 3
            bar_width_full = avatar_size_local - 6
            progress = user_info.get("level_progress", 0.1)
            bar_x1 = int(bar_width_full * progress)
            bar_y1 = bar_y0 + bar_height_px
            draw.rectangle((bar_x0, bar_y0, bar_x1, bar_y1), fill=(0, 120, 255, 255))
            draw.rectangle((bar_x0, bar_y0, bar_width_full, bar_y1), 
                          outline=(255,255,255,255), width=1)
            
            return bar
        
        def create_bars(user_info, font, bet_icon_img, balance_icon_img):
            bars, bar_height, min_bar_width = [], 40, 80
            
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
                draw.text((x, y_offset), w, font=font, fill=(255,255,255,255), 
                         stroke_width=2, stroke_fill=(0,0,0,255))
                y_offset += bbox[3] - bbox[1]
            bars.append(nick_bar)
            
            for icon, text_key, icon_img in [(bet_icon_img, "bet", bet_icon_img), 
                                            (balance_icon_img, "balance", balance_icon_img)]:
                text = f"{user_info[text_key]}"
                text_width = self._get_text_width(text, font)
                width = max(icon_img.width + 5 + text_width + 10, min_bar_width)
                bar = Image.new("RGBA", (width, bar_height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(bar)
                draw.rounded_rectangle((0, 0, width, bar_height), radius=7, fill=(40, 40, 40, 255))
                y_icon = (bar_height - icon_img.height) // 2
                bar.paste(icon_img, (5, y_icon), icon_img)
                x_text, y_text = icon_img.width + 10, (bar_height - (font.getbbox(text)[3] - font.getbbox(text)[1])) // 2 - 5
                draw.text((x_text, y_text), text, font=font, fill=(255,255,255,255), 
                         stroke_width=2, stroke_fill=(0,0,0,255))
                bars.append(bar)
            
            return bars
        
        bars_before = create_bars(user_info_before, font_small, bet_icon, balance_icon)
        bars_after = create_bars(user_info_after, font_small, bet_icon, balance_icon)
        avatar_bar_before = create_avatar_bar(avatar, user_info_before, font_small)
        avatar_bar_after = create_avatar_bar(avatar, user_info_after, font_small)
        
        did_win = cashout_multiplier < crash_multiplier
        
        cashout_text = f"CASHOUT: {cashout_multiplier:.2f}x"
        win_amount_text = f"WON: {payout_amount}$" if did_win else f"LOST: {abs(net_win)}$"
        
        crash_text = "CRASHED!"
        result_text = f"LOSE: {abs(net_win)}$" if net_win < 0 else ""
        
        crash_frame = self._get_frame_for_multiplier(img, crash_multiplier)
        
        cashout_frame = self._get_frame_for_multiplier(img, cashout_multiplier) if did_win else crash_frame
        
        extra_bottom = 50
        bar_height = 40
        new_height = bg_frame_height
        
        frames, durations = [], []
        frame_skip = 1
        
        target_frame = crash_frame
        
        included_frames = list(range(0, min(target_frame + 1, n_frames), frame_skip))
        
        included_frames.sort()
        
        cashout_reached = False
        crash_shown = False
        
        for i, frame_idx in enumerate(included_frames):
            img.seek(frame_idx)
            frame = img.convert("RGBA")
            
            combined = Image.new("RGBA", (bg_frame_width, new_height), (0, 0, 0, 0))
            
            combined.paste(bg_img, (0, 0))
            
            combined.paste(frame, (margin, margin), frame)
            
            if history_overlay:
                combined.alpha_composite(history_overlay, (history_x, history_y))
            
            draw = ImageDraw.Draw(combined)
            draw.rectangle([0, 400, 440, 440],
                         fill=(30, 30, 30, 255))
            
            if not crash_shown:
                avatar_bar, bars = avatar_bar_before, bars_before
            else:
                avatar_bar, bars = avatar_bar_after, bars_after
            
            avatar_x = margin + frame_width - avatar_bar.width - 15
            avatar_y = new_height - avatar_bar.height - 5
            combined.paste(avatar_bar, (avatar_x, avatar_y), avatar_bar)
            
            total_bars_width = sum([b.width for b in bars])
            x = margin + (frame_width - total_bars_width - avatar_bar.width - 30) // (len(bars) + 1)
            y = new_height - bar_height - 5
            for b in bars:
                combined.paste(b, (x, y), b)
                x += b.width + 10
            
            draw_center = ImageDraw.Draw(combined)
            
            if did_win and not cashout_reached and frame_idx >= cashout_frame:
                cashout_reached = True
            
            if cashout_reached:
                bbox_cashout = font_result_medium.getbbox(cashout_text)
                text_x_cashout = (bg_frame_width - (bbox_cashout[2] - bbox_cashout[0])) // 2
                text_y_cashout = margin + 100
                
                draw_center.text((text_x_cashout, text_y_cashout), cashout_text, font=font_result_medium,
                               fill=(0, 255, 0, 255), stroke_width=2, stroke_fill=(0,0,0,255))
                
                bbox_win_amount = font_result_small.getbbox(win_amount_text)
                text_x_win = (bg_frame_width - (bbox_win_amount[2] - bbox_win_amount[0])) // 2
                text_y_win = text_y_cashout + 30
                
                win_amount_color = (0, 255, 0, 255)
                draw_center.text((text_x_win, text_y_win), win_amount_text, font=font_result_small,
                               fill=win_amount_color, stroke_width=2, stroke_fill=(0,0,0,255))
            
            if not crash_shown and frame_idx >= crash_frame:
                bbox_crash = font_result_large.getbbox(crash_text)
                text_x_crash = (bg_frame_width - (bbox_crash[2] - bbox_crash[0])) // 2
                text_y_crash = margin + (frame_height // 2) - 20
                
                crash_color = (255, 50, 50, 255)
                draw_center.text((text_x_crash, text_y_crash), crash_text, font=font_result_large,
                               fill=crash_color, stroke_width=2, stroke_fill=(0,0,0,255))
                
                if net_win < 0:
                    bbox_result = font_result_medium.getbbox(result_text)
                    text_x_result = (bg_frame_width - (bbox_result[2] - bbox_result[0])) // 2
                    text_y_result = text_y_crash + 50
                    
                    draw_center.text((text_x_result, text_y_result), result_text, font=font_result_medium,
                                   fill=(255, 50, 50, 255), stroke_width=2, stroke_fill=(0,0,0,255))
                
                crash_shown = True
            
            frames.append(combined)
            
            base_duration = img.info.get("duration", 100)
            
            if frame_idx == crash_frame:
                duration = 3000
            elif cashout_reached and not crash_shown:
                duration = base_duration * 1.2
            elif frame_idx > 0 and frame_idx % 15 == 0:
                duration = base_duration * 1.1
            else:
                duration = base_duration
            
            durations.append(duration)
        
        if len(frames) > 1:
            frames[0].save(output_path, save_all=True, append_images=frames[1:], 
                         duration=durations, loop=0, format="WEBP", quality=60, 
                         method=5, lossless=False, minimize_size=True)
        else:
            frames[0].save(output_path, format="WEBP", quality=60, method=5)
        
        return output_path

    def _generate_static_crash(self, img, crash_multiplier, effective_multiplier, cashout_multiplier,
                            payout_amount, net_win, avatar_path, bg_path, user_info_after, output_path):
        crash_frame_index = self._get_frame_for_multiplier(img, crash_multiplier)
        
        if getattr(img, "is_animated", False):
            img.seek(crash_frame_index)
        base_frame = img.convert("RGBA")
        
        frame_width, frame_height = base_frame.size
        
        margin = 20
        bg_frame_width = frame_width + (2 * margin)
        bg_frame_height = frame_height + (2 * margin)
        
        history_width = 60 
        history_height = frame_height
        history_overlay = self.generate_vertical_history_overlay(width=history_width, height=history_height)
        history_x = margin + frame_width - history_width
        history_y = margin
        
        bg_img = Image.open(bg_path).convert("RGBA").resize((bg_frame_width, bg_frame_height))
        
        final_img = Image.new("RGBA", (bg_frame_width, bg_frame_height), (0,0,0,0))
        final_img.paste(bg_img, (0,0))
        final_img.paste(base_frame, (margin, margin), base_frame)
        
        if history_overlay:
            final_img.alpha_composite(history_overlay, (history_x, history_y))
        
        draw = ImageDraw.Draw(final_img)
        try:
            font_large = ImageFont.truetype("DejaVuSans-Bold.ttf", frame_width // 8)
            font_medium = ImageFont.truetype("DejaVuSans-Bold.ttf", frame_width // 15)
            font_small = ImageFont.truetype("DejaVuSans-Bold.ttf", frame_width // 20)
        except:
            font_large = font_medium = font_small = ImageFont.load_default()
        
        did_win = cashout_multiplier < crash_multiplier
        
        crash_text = "CRASHED!"
        result_text = f"LOSE: {abs(net_win)}$" if net_win < 0 else ""
        
        cashout_text = f"CASHOUT: {cashout_multiplier:.2f}x"
        win_amount_text = f"WON: {payout_amount}$" if did_win else f"LOST: {abs(net_win)}$"
        
        bbox_crash = font_large.getbbox(crash_text)
        text_x_crash = (bg_frame_width - (bbox_crash[2] - bbox_crash[0])) // 2
        text_y_crash = margin + (frame_height // 2) - 20
        draw.text((text_x_crash, text_y_crash), crash_text, font=font_large,
                fill=(255, 50, 50, 255), stroke_width=2, stroke_fill=(0,0,0,255))
        
        if net_win < 0:
            bbox_result = font_medium.getbbox(result_text)
            text_x_result = (bg_frame_width - (bbox_result[2] - bbox_result[0])) // 2
            text_y_result = text_y_crash + 60
            draw.text((text_x_result, text_y_result), result_text, font=font_medium,
                    fill=(255, 50, 50, 255), stroke_width=2, stroke_fill=(0,0,0,255))
        
        if did_win:
            bbox_cashout = font_medium.getbbox(cashout_text)
            text_x_cashout = (bg_frame_width - (bbox_cashout[2] - bbox_cashout[0])) // 2
            text_y_cashout = margin + 70
            
            draw.text((text_x_cashout, text_y_cashout), cashout_text, font=font_medium,
                    fill=(0, 255, 0, 255), stroke_width=2, stroke_fill=(0,0,0,255))
            
            bbox_win_amount = font_small.getbbox(win_amount_text)
            text_x_win = (bg_frame_width - (bbox_win_amount[2] - bbox_win_amount[0])) // 2
            text_y_win = text_y_cashout + 60
            
            draw.text((text_x_win, text_y_win), win_amount_text, font=font_small,
                    fill=(0, 255, 0, 255), stroke_width=2, stroke_fill=(0,0,0,255))
        
        pasek_wysokosc = 45
        pasek_y0 = bg_frame_height - pasek_wysokosc
        pasek_y1 = bg_frame_height
        draw.rectangle([0, pasek_y0, bg_frame_width, pasek_y1], 
                    fill=(40, 40, 40, 255))
        
        avatar_size = 90
        avatar = Image.open(avatar_path).convert("RGBA").resize((avatar_size, avatar_size))
        
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
        except:
            font_small = ImageFont.load_default()
        
        def _get_text_width(text, font):
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0]
        
        def create_avatar_bar(avatar_img, user_info, font):
            avatar_size_local = avatar_img.size[0]
            bar = Image.new("RGBA", (avatar_size_local, avatar_size_local), (0, 0, 0, 0))
            
            avatar_mask = Image.new("L", (avatar_size_local, avatar_size_local), 0)
            mask_draw = ImageDraw.Draw(avatar_mask)
            mask_draw.rounded_rectangle((0, 0, avatar_size_local, avatar_size_local), radius=5, fill=255)
            
            bar.paste(avatar_img, (0, 0), avatar_mask)
            bar_draw = ImageDraw.Draw(bar)
            
            level_text = str(user_info["level"])
            level_width = _get_text_width(level_text, font)
            level_x = avatar_size_local - level_width - 3
            bar_draw.text((level_x, 3), level_text, font=font, fill=(255,255,255,255), 
                        stroke_width=2, stroke_fill=(0,0,0,255))
            
            bar_height_px = 6
            bar_x0 = 3
            bar_y0 = avatar_size_local - bar_height_px - 3
            bar_width_full = avatar_size_local - 6
            progress = user_info.get("level_progress", 0.1)
            bar_x1 = int(bar_width_full * progress)
            bar_y1 = bar_y0 + bar_height_px
            bar_draw.rectangle((bar_x0, bar_y0, bar_x1, bar_y1), fill=(0, 120, 255, 255))
            bar_draw.rectangle((bar_x0, bar_y0, bar_width_full, bar_y1), 
                            outline=(255,255,255,255), width=1)
            
            return bar
        
        def create_bars(user_info, font, bet_icon_img, balance_icon_img):
            bars, bar_height, min_bar_width = [], 40, 80
            
            nick_lines = user_info["username"].split(" ")
            max_width = max([_get_text_width(w, font) for w in nick_lines])
            width = max(max_width + 20, min_bar_width)
            nick_bar = Image.new("RGBA", (width, bar_height), (0, 0, 0, 0))
            nick_draw = ImageDraw.Draw(nick_bar)
            nick_draw.rounded_rectangle((0, 0, width, bar_height), radius=7, fill=(40, 40, 40, 255))
            
            total_height = sum([font.getbbox(w)[3] - font.getbbox(w)[1] for w in nick_lines])
            y_offset = (bar_height - total_height) // 2 - 5
            for w in nick_lines:
                bbox = font.getbbox(w)
                text_width = bbox[2] - bbox[0]
                x = (width - text_width) // 2
                nick_draw.text((x, y_offset), w, font=font, fill=(255,255,255,255), 
                            stroke_width=2, stroke_fill=(0,0,0,255))
                y_offset += bbox[3] - bbox[1]
            bars.append(nick_bar)
            
            for icon, text_key, icon_img in [(bet_icon_img, "bet", bet_icon_img), 
                                            (balance_icon_img, "balance", balance_icon_img)]:
                text = f"{user_info[text_key]}"
                text_width = _get_text_width(text, font)
                width = max(icon_img.width + 5 + text_width + 10, min_bar_width)
                bar = Image.new("RGBA", (width, bar_height), (0, 0, 0, 0))
                bar_draw = ImageDraw.Draw(bar)
                bar_draw.rounded_rectangle((0, 0, width, bar_height), radius=7, fill=(40, 40, 40, 255))
                y_icon = (bar_height - icon_img.height) // 2
                bar.paste(icon_img, (5, y_icon), icon_img)
                x_text, y_text = icon_img.width + 10, (bar_height - (font.getbbox(text)[3] - font.getbbox(text)[1])) // 2 - 5
                bar_draw.text((x_text, y_text), text, font=font, fill=(255,255,255,255), 
                            stroke_width=2, stroke_fill=(0,0,0,255))
                bars.append(bar)
            
            return bars
        
        avatar_bar = create_avatar_bar(avatar, user_info_after, font_small)
        bars = create_bars(user_info_after, font_small, bet_icon, balance_icon)
        
        avatar_x = bg_frame_width - avatar_bar.width - 15
        avatar_y = pasek_y1 - avatar_bar.height - 5
        final_img.paste(avatar_bar, (avatar_x, avatar_y), avatar_bar)
        
        total_bars_width = sum([b.width for b in bars])
        x = (bg_frame_width - total_bars_width - avatar_bar.width - 30) // (len(bars) + 1)
        y = pasek_y1 - 45
        
        for b in bars:
            final_img.paste(b, (x, y), b)
            x += b.width + 10
                
        final_img.save(output_path, format="WEBP")
        return output_path

def register():
    plugin = CrashPlugin()
    return {
        "name": "crash",
        "aliases": ["/crash"],
        "description": "Crash game: /crash <amount> <cashout_multiplier> - Bet and cash out before crash!",
        "execute": plugin.execute_game
    }