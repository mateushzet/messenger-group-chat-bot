import os
import random
import time
import tempfile
from typing import Any, Dict, Optional

from PIL import Image, ImageDraw

from base_game_plugin import BaseGamePlugin
from logger import logger
from plugins.weekly import record_weekly_win


class Roulette2Plugin(BaseGamePlugin):
    HISTORY_KEY = "roulette2_history"
    MAX_HISTORY = 10
    OFFSETS = ("start", "center", "end")
    CROP_AMOUNT = 34

    def __init__(self):
        super().__init__(game_name="roulette2")
        self.fields = [0, 7, 2, 10, 4, 12, 6, 1, 9, 3, 11, 5, 8]
        self.field_colors = {
            0: "green",
            7: "red",
            2: "black",
            10: "red",
            4: "black",
            12: "red",
            6: "black",
            1: "red",
            9: "black",
            3: "red",
            11: "black",
            5: "red",
            8: "black",
        }
        self.color_rgb = {
            "green": (0, 177, 88),
            "red": (207, 57, 64),
            "black": (45, 48, 54),
        }
        self.colors = {
            "gold": (255, 210, 75),
        }

    def get_temp_path(self, filename: str) -> str:
        temp_dir = os.path.join(tempfile.gettempdir(), "roulette2")
        os.makedirs(temp_dir, exist_ok=True)
        return os.path.join(temp_dir, filename)

    def get_custom_overlay(self, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            frame_width = kwargs.get("frame_width", 800)
            request = kwargs.get("request")
            custom_kwargs = {}
            if request and hasattr(request.options, "custom_overlay_kwargs"):
                custom_kwargs = request.options.custom_overlay_kwargs or {}

            result = custom_kwargs.get("result")
            history = self.get_history()

            before = self._generate_history_overlay(frame_width, history)
            after_history = history.copy()
            if result is not None:
                after_history.insert(0, {
                    "number": result,
                    "color": self.field_colors[result],
                    "timestamp": time.time(),
                    "is_current": True,
                })
                after_history = after_history[:self.MAX_HISTORY]

            after = self._generate_history_overlay(frame_width, after_history, show_current=True)

            return {
                "before": {
                    "image": before,
                    "position": (0, 0),
                    "type": "before",
                    "per_frame": True,
                },
                "after": {
                    "image": after,
                    "position": (0, 0),
                    "type": "after",
                    "per_frame": True,
                },
            }
        except Exception as e:
            logger.error(f"[Roulette2] Error creating history overlay: {e}", exc_info=True)
            return None

    def _generate_history_overlay(self, frame_width: int, history=None, show_current=False):
        history = history or []
        height = 42
        overlay = Image.new("RGBA", (frame_width, height), (0, 0, 0, 0))
        if not history:
            return overlay

        draw = ImageDraw.Draw(overlay)
        item_count = min(len(history), self.MAX_HISTORY)
        field_w = 34
        field_h = 28
        gap = 5
        total_w = item_count * field_w + (item_count - 1) * gap
        start_x = (frame_width - total_w) // 2
        y = (height - field_h) // 2

        for display_index, item in enumerate(reversed(history[:item_count])):
            number = int(item.get("number", 0))
            color_name = item.get("color", self.field_colors.get(number, "green"))
            is_current = bool(item.get("is_current")) and show_current
            alpha = 255 if is_current else int(115 + (display_index / max(1, item_count - 1)) * 110)
            fill = self.color_rgb.get(color_name, self.color_rgb["green"]) + (alpha,)
            outline = self.colors["gold"] + (255,) if is_current else (15, 18, 24, alpha)
            x = start_x + display_index * (field_w + gap)

            draw.rectangle([x, y, x + field_w, y + field_h], fill=fill, outline=outline, width=3 if is_current else 2)
            number_img = self.text_renderer.render_text(
                text=str(number),
                font_size=13,
                color=(255, 255, 255, alpha),
                stroke_width=1,
                stroke_color=(0, 0, 0, alpha),
            )
            overlay.alpha_composite(number_img, (x + (field_w - number_img.width) // 2, y + (field_h - number_img.height) // 2))

        return overlay

    def validate_bet(self, amount_str: str, bet_type: str) -> Optional[str]:
        if not amount_str.isdigit():
            return "Amount must be a positive whole number"

        amount = int(amount_str)
        if amount <= 0:
            return "Amount must be greater than 0"

        valid = [str(n) for n in self.fields] + ["red", "black", "green"]
        if bet_type not in valid:
            return f"Invalid bet: {bet_type}\n\nValid bets: 0-12, red, black, green"

        return None

    def calculate_win(self, bet_type: str, amount: int, result: int) -> int:
        result_color = self.field_colors[result]
        if bet_type.isdigit() and int(bet_type) == result:
            return amount * 12
        if bet_type == "green" and result == 0:
            return amount * 12
        if bet_type in ("red", "black") and bet_type == result_color:
            return amount * 2
        return 0

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache

        if len(args) == 0 or args[0].lower() == "help":
            self.send_message_image(
                sender,
                file_queue,
                "Use: /roulette2 <amount> <bet>\n\n"
                "Bets: 0-12, red, black, green\n"
                "0 is green and pays x12\n"
                "Numbers pay x12, colors pay x2\n\n"
                "Example: /roulette2 100 red",
                "Roulette2",
                cache,
                None,
            )
            return None

        animated = True
        if len(args) >= 3 and args[-1].lower() == "x":
            animated = False
            args = args[:-1]

        if len(args) < 2:
            self.send_message_image(sender, file_queue, "Usage: /roulette2 <amount> <bet>", "Roulette2 - Invalid Usage", cache, None)
            return None

        amount_str = args[0]
        bet_type = args[1].lower()
        error = self.validate_bet(amount_str, bet_type)
        if error:
            self.send_message_image(sender, file_queue, error, "Roulette2 - Invalid Bet", cache, None)
            return None

        amount = int(amount_str)
        user_id, user, user_error = self.validate_user_and_balance(cache, sender, avatar_url, amount)
        if user_error:
            if user_error == "Invalid user":
                self.send_message_image(sender, file_queue, "Invalid user!", "Roulette2 - Error", cache, None)
            else:
                balance = user.get("balance", 0) if user else 0
                self.send_message_image(sender, file_queue, f"Insufficient funds!\n\nYou need: ${amount}\nYour balance: ${balance}", "Roulette2 - Error", cache, user_id)
            return None

        balance_before = user.get("balance", 0)
        result = random.choice(self.fields)
        win = self.calculate_win(bet_type, amount, result)
        net_win = win - amount
        new_balance = balance_before - amount + win

        try:
            self.update_user_balance(user_id, new_balance)
        except Exception as e:
            logger.error(f"[Roulette2] Error updating balance for user {user_id}: {e}")
            self.send_message_image(sender, file_queue, "Error updating balance!", "Roulette2 - Error", cache, user_id)
            return None

        try:
            exp_amount = net_win if net_win > 0 else -amount
            new_level, new_progress = self.cache.add_experience(user_id, exp_amount, sender, file_queue)
            user["level"] = new_level
            user["level_progress"] = new_progress
        except Exception as e:
            logger.error(f"[Roulette2] Error adding experience: {e}")

        if net_win > 0:
            record_weekly_win(self.cache, user_id, "roulette", net_win)

        base_animation_path = self.get_base_animation_path(result, animated)
        if not base_animation_path:
            self.send_message_image(
                sender,
                file_queue,
                "Roulette2 assets are missing. Run assets/roulette2/generate_roulette2_assets.py first.",
                "Roulette2 - Assets Missing",
                cache,
                user_id,
            )
            return None

        cropped_animation_path = self._crop_animation(base_animation_path)
        if not cropped_animation_path:
            logger.warning(f"[Roulette2] Could not crop animation, using original: {base_animation_path}")
            cropped_animation_path = base_animation_path

        user_info_before = self.create_user_info(sender, amount, 0, balance_before, user.copy())
        user_info_after = self.create_user_info(sender, amount, net_win, new_balance, user)

        result_path, overlay_error = self.generate_animation(
            base_animation_path=cropped_animation_path,
            user_id=user_id,
            user=user,
            user_info_before=user_info_before,
            user_info_after=user_info_after,
            animated=animated,
            frame_duration=50,
            last_frame_multiplier=8.0,
            custom_overlay_kwargs={"result": result},
            show_win_text=True,
            font_scale=0.95,
            avatar_size=74,
            overlay_position="bottom",
            win_text_height=34,
            win_text_scale=0.72,
            quality=68,
        )

        self.add_to_history(result)

        if overlay_error or not result_path:
            logger.error(f"[Roulette2] Overlay generation error: {overlay_error}")
            self.send_message_image(sender, file_queue, f"Error generating animation!\n\n{overlay_error}", "Roulette2 - Error", cache, user_id)
            return None

        file_queue.put(result_path)
        logger.info(
            f"ROULETTE2: {sender} bet {amount} on {bet_type} | Result: {result} {self.field_colors[result]} | Net: {net_win} | Balance: {balance_before} -> {new_balance}"
        )
        return None

    def _crop_animation(self, animation_path: str) -> Optional[str]:
        try:
            from PIL import Image
            
            img = Image.open(animation_path)
            
            is_animated = getattr(img, 'is_animated', False)
            
            if is_animated:
                frames = []
                durations = []
                
                for frame_no in range(img.n_frames):
                    img.seek(frame_no)
                    frame = img.copy()
                    
                    width, height = frame.size
                    cropped = frame.crop((
                        self.CROP_AMOUNT,
                        0,
                        width - self.CROP_AMOUNT,
                        height
                    ))
                    frames.append(cropped)
                    durations.append(img.info.get('duration', 50))
                
                temp_path = self.get_temp_path(f"cropped_{os.path.basename(animation_path)}")
                frames[0].save(
                    temp_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=durations,
                    loop=0,
                    format="WEBP",
                    quality=68,
                    method=4,
                )
                return temp_path
            else:
                width, height = img.size
                cropped = img.crop((
                    self.CROP_AMOUNT,
                    0,
                    width - self.CROP_AMOUNT,
                    height
                ))
                temp_path = self.get_temp_path(f"cropped_{os.path.basename(animation_path)}")
                cropped.save(temp_path, "WEBP", quality=68)
                return temp_path
                
        except Exception as e:
            logger.error(f"[Roulette2] Error cropping animation: {e}", exc_info=True)
            return None

    def get_base_animation_path(self, result: int, animated: bool = True) -> Optional[str]:
        if not animated:
            path = self.get_asset_path("roulette2", "results", f"result_{result}_center.webp")
            return path if os.path.exists(path) else None

        variants = list(self.OFFSETS)
        random.shuffle(variants)
        for variant in variants:
            path = self.get_asset_path("roulette2", "results", f"result_{result}_{variant}.webp")
            if os.path.exists(path):
                return path
        return None

    def add_to_history(self, result: int):
        if not self.cache:
            return

        history = self.cache.get_setting(self.HISTORY_KEY, [])
        if not isinstance(history, list):
            history = []

        history.insert(0, {
            "number": result,
            "color": self.field_colors[result],
            "timestamp": time.time(),
        })
        self.cache.set_setting(self.HISTORY_KEY, history[:self.MAX_HISTORY])

    def get_history(self):
        if not self.cache:
            return []

        history = self.cache.get_setting(self.HISTORY_KEY, [])
        if not isinstance(history, list):
            return []
        return history[:self.MAX_HISTORY]


def register():
    plugin = Roulette2Plugin()
    return {
        "name": "roulette2",
        "aliases": ["/r2"],
        "description": "Roulette2 - 13-field strip roulette. 0 is green. Use: /roulette2 <amount> <bet>",
        "execute": plugin.execute_game,
    }