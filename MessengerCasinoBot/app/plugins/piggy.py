import os
import random
import threading
import time

from PIL import Image, ImageDraw

from base_game_plugin import BaseGamePlugin
from logger import logger
from plugins.monthly import record_monthly_win


class PiggyBank:
    SETTING_KEY = "piggy_bank"
    MIN_FREEZE_SECONDS = 20 * 60
    MAX_FREEZE_SECONDS = 2 * 60 * 60
    MIN_GROWTH_SPEED = 0.80
    MAX_GROWTH_SPEED = 1.25
    MAX_FREEZES_PER_CYCLE = 3

    def __init__(self, plugin):
        self.plugin = plugin

    def get_state(self):
        state = self.plugin.cache.get_setting(self.SETTING_KEY, None) if self.plugin.cache else None
        if not isinstance(state, dict):
            now = time.time()
            state = {
                "growth_started_at": now,
                "cooldown_until": 0,
                "freeze_until": 0,
                "growth_speed": self._new_growth_speed(),
                "last_claimed_at": None,
                "last_claimed_by": None,
                "last_claimed_amount": 0,
                "freeze_count": 0,
            }
            self.save_state(state)
        updated = False
        if "growth_speed" not in state:
            state["growth_speed"] = self._new_growth_speed()
            updated = True
        if "freeze_until" not in state:
            state["freeze_until"] = 0
            updated = True
        if "freeze_count" not in state:
            state["freeze_count"] = 0
            updated = True
        if updated:
            self.save_state(state)
        return state

    def save_state(self, state):
        if self.plugin.cache:
            self.plugin.cache.set_setting(self.SETTING_KEY, state)

    def get_info(self, now=None):
        now = now or time.time()
        state = self.get_state()
        cooldown_until = float(state.get("cooldown_until") or 0)
        freeze_until = float(state.get("freeze_until") or 0)

        growth_started_at = float(state.get("growth_started_at") or now)
        growth_speed = float(state.get("growth_speed") or 1.0)
        elapsed_seconds = max(0, now - growth_started_at)
        elapsed_hours = elapsed_seconds / 3600.0
        amount = self.value_after_hours(elapsed_hours)

        info = {
            "state": state,
            "status": "frozen" if freeze_until > now else "growing",
            "amount": int(amount),
            "rate": int(round(self.rate_at_hour(elapsed_hours) * growth_speed)),
            "elapsed_seconds": elapsed_seconds,
            "cooldown_remaining": 0,
            "freeze_remaining": max(0, freeze_until - now),
            "stage": -1 if freeze_until > now else self.stage_for_hours(elapsed_hours),
            "growth_speed": growth_speed,
        }
        return info

    def claim(self, user_id, username, now=None):
        now = now or time.time()
        info = self.get_info(now)

        if info["status"] == "frozen":
            return False, info, "Piggy bank is frozen."

        amount = int(info["amount"])
        if amount < 1:
            return False, info, "Piggy bank is still empty. Come back later."

        state = {
            "growth_started_at": now,
            "cooldown_until": 0,
            "freeze_until": 0,
            "growth_speed": self._new_growth_speed(),
            "last_claimed_at": now,
            "last_claimed_by": username,
            "last_claimed_by_id": str(user_id),
            "last_claimed_amount": amount,
            "freeze_count": 0,
        }
        self.save_state(state)

        info["state"] = state
        info["claimed_amount"] = amount
        return True, info, ""

    def freeze(self, now=None):
        now = now or time.time()
        state = self.get_state()
        cooldown_until = float(state.get("cooldown_until") or 0)
        freeze_until = float(state.get("freeze_until") or 0)
        freeze_count = int(state.get("freeze_count") or 0)


        if freeze_until > now:
            return False, self.get_info(now), "Piggy bank is already frozen."

        if freeze_count >= self.MAX_FREEZES_PER_CYCLE:
            return False, self.get_info(now), f"Piggy can only be frozen {self.MAX_FREEZES_PER_CYCLE} times per cycle."

        duration = random.randint(self.MIN_FREEZE_SECONDS, self.MAX_FREEZE_SECONDS)
        state["freeze_until"] = now + duration
        state["freeze_count"] = freeze_count + 1
        self.save_state(state)

        info = self.get_info(now)
        info["freeze_duration"] = duration
        info["freezes_remaining"] = self.MAX_FREEZES_PER_CYCLE - (freeze_count + 1)
        return True, info, f"Piggy frozen for a random 20-120 minutes."

    @classmethod
    def rate_at_hour(cls, hour):
        if hour < 1:
            return 0
        if hour < 2:
            return 3
        if hour < 3:
            return 5
        if hour < 4:
            return 7
        if hour < 5:
            return 9
        if hour < 6:
            return 12
        if hour < 12:
            return cls._linear(hour, 6, 12, 15, 35)
        if hour < 24:
            return cls._linear(hour, 12, 24, 40, 95)
        return 150

    @classmethod
    def value_after_hours(cls, hours):
        hours = max(0, hours)
        total = 0.0
        cursor = 0.0

        for end, rate in [(1, 0), (2, 3), (3, 5), (4, 7), (5, 9), (6, 12)]:
            if hours <= cursor:
                break
            span = min(hours, end) - cursor
            if span > 0:
                total += span * rate
            cursor = end

        if hours > 6:
            end = min(hours, 12)
            if end > 6:
                total += cls._integrate_linear(6, end, 6, 12, 15, 35)

        if hours > 12:
            end = min(hours, 24)
            if end > 12:
                total += cls._integrate_linear(12, end, 12, 24, 40, 95)

        if hours > 24:
            total += (hours - 24) * 150

        return total

    @staticmethod
    def _linear(x, x1, x2, y1, y2):
        progress = (x - x1) / float(x2 - x1)
        return y1 + (y2 - y1) * progress

    @classmethod
    def _integrate_linear(cls, start, end, x1, x2, y1, y2):
        def antiderivative(x):
            slope = (y2 - y1) / float(x2 - x1)
            return y1 * x + slope * ((x - x1) ** 2) / 2.0

        return antiderivative(end) - antiderivative(start)

    @staticmethod
    def stage_for_hours(hours):
        if hours <= 0:
            return 0

        progress = min(hours, 48) / 48.0
        return max(1, min(26, 1 + int(progress * 25)))

    @classmethod
    def _new_growth_speed(cls):
        return round(random.uniform(cls.MIN_GROWTH_SPEED, cls.MAX_GROWTH_SPEED), 3)

    @staticmethod
    def format_duration(seconds):
        seconds = max(0, int(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


class PiggyPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="piggy")
        self.bank = PiggyBank(self)
        self.claim_lock = threading.Lock()
        self.assets_folder = self.get_asset_path("piggy")
        self.colors = {
            "bg": (25, 28, 36),
            "panel": (39, 43, 54),
            "pink": (255, 126, 173),
            "gold": (255, 210, 90),
            "green": (118, 240, 170),
            "red": (255, 100, 110),
            "text": (245, 245, 248),
            "muted": (178, 185, 198),
            "line": (72, 77, 92),
        }

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user(cache, sender, avatar_url)

        if error:
            self.send_message_image(sender, file_queue, "Player not found.", "Piggy", cache, None)
            return ""

        if not args:
            self._send_status(user_id, sender, file_queue)
            return ""

        cmd = args[0].lower()
        if cmd in ["smash", "collect"]:
            self._handle_smash(user_id, user, sender, file_queue)
            return ""

        if cmd in ["freeze", "f"]:
            self._handle_freeze(user_id, sender, file_queue)
            return ""

        if cmd in ["help", "h", "?"]:
            self.send_message_image(
                sender,
                file_queue,
                "/piggy - show piggy bank status\n"
                "/piggy smash - collect the full pot\n"
                "/piggy freeze - block smashing for 20-120 minutes\n\n"
                "Maximum 3 freezes per piggy cycle.",
                "Piggy Help",
                self.cache,
                user_id,
            )
            return ""

        self.send_message_image(sender, file_queue, "Use /piggy, /piggy smash or /piggy freeze.", "Piggy", self.cache, user_id)
        return ""

    def _handle_freeze(self, user_id, sender, file_queue):
        success, info, message = self.bank.freeze()
        image_path, error = self._create_status_image(
            info,
            user_id=user_id,
            message=message,
            winner=success,
        )
        if image_path and not error:
            file_queue.put(image_path)

    def _handle_smash(self, user_id, user, sender, file_queue):
        with self.claim_lock:
            success, info, message = self.bank.claim(user_id, sender)
            if not success:
                image_path, error = self._create_status_image(info, user_id=user_id, message=message)
                if image_path and not error:
                    file_queue.put(image_path)
                return

            amount = int(info["claimed_amount"])
            new_balance = self.cache.update_balance(user_id, amount)
            user["balance"] = new_balance
            record_monthly_win(self.cache, user_id, "piggy", amount)

            logger.info(f"[Piggy] {sender} smashed piggy for {amount} coins")

            image_path, error = self._create_status_image(
                info,
                user_id=user_id,
                message=f"{sender} collected {amount}$!",
                winner=sender,
                claimed_amount=amount,
            )
            if image_path and not error:
                file_queue.put(image_path)

    def _send_status(self, user_id, sender, file_queue):
        info = self.bank.get_info()
        image_path, error = self._create_status_image(info, user_id=user_id)
        if image_path and not error:
            file_queue.put(image_path)
        else:
            self.send_message_image(sender, file_queue, error or "Piggy bank status error.", "Piggy", self.cache, user_id)

    def _create_status_image(self, info, user_id=None, message=None, winner=None, claimed_amount=None):
        try:
            width, height = 520, 520
            img = self._load_player_background(user_id, width, height)
            draw = ImageDraw.Draw(img)

            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 115))
            img = Image.alpha_composite(img.convert("RGBA"), overlay)
            draw = ImageDraw.Draw(img)

            title = self._text("PIGGY BANK", 42, self.colors["gold"], stroke=2)
            img.paste(title, ((width - title.width) // 2, 22), title)

            rate = info.get("rate", 0)
            status = info.get("status", "growing")
            header_text = f"+{rate}$ / h"
            header_color = self.colors["green"] if rate else self.colors["muted"]
            rate_text = self._text(header_text, 28, header_color, stroke=2)
            img.paste(rate_text, ((width - rate_text.width) // 2, 74), rate_text)

            piggy = self._load_piggy_image(info.get("stage", 0))
            piggy = self._fit_image(piggy, 390, 295)
            piggy_x = (width - piggy.width) // 2
            piggy_y = 118
            img.paste(piggy, (piggy_x, piggy_y), piggy)

            amount = info.get("amount", 0)

            if status == "frozen" and not message:
                command = self._text("Piggy Frozen!", 30, self.colors["muted"], stroke=2)
            else:
                command = self._text("/piggy smash", 30, self.colors["gold"], stroke=2)
                
            command_y = 414
            img.paste(command, ((width - command.width) // 2, command_y), command)

            amount_text = self._text(f"{amount}$", 46, self.colors["text"], stroke=3)
            amount_y = 462
            img.paste(amount_text, ((width - amount_text.width) // 2, amount_y), amount_text)

            if message:
                msg_color = self.colors["green"] if winner or claimed_amount else self.colors["muted"]
                msg_img = self._text(message, 22, msg_color, stroke=2)
                msg_x = (width - msg_img.width) // 2
                msg_y = 382
                self._draw_text_plate(img, msg_x, msg_y, msg_img)
                img.paste(msg_img, (msg_x, msg_y), msg_img)

            output_dir = self.get_app_path("temp", "piggy")
            os.makedirs(output_dir, exist_ok=True)
            path = os.path.join(output_dir, f"piggy_{int(time.time() * 1000)}.png")
            img.convert("RGB").save(path, format="PNG", optimize=True)
            return path, None
        except Exception as e:
            logger.error(f"[Piggy] Error creating status image: {e}", exc_info=True)
            return None, str(e)

    def _load_player_background(self, user_id, width, height):
        bg_path = None
        cache = getattr(self, "cache", None)
        if cache and user_id and hasattr(cache, "get_background_path"):
            bg_path = cache.get_background_path(user_id)

        if not bg_path or not os.path.exists(bg_path):
            bg_path = self.get_asset_path("backgrounds", "default-bg.png")

        try:
            bg = Image.open(bg_path).convert("RGB")
        except Exception:
            return Image.new("RGB", (width, height), self.colors["bg"])

        bg_ratio = bg.width / float(bg.height)
        target_ratio = width / float(height)

        if bg_ratio > target_ratio:
            new_height = height
            new_width = int(height * bg_ratio)
        else:
            new_width = width
            new_height = int(width / bg_ratio)

        bg = bg.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - width) // 2
        top = (new_height - height) // 2
        return bg.crop((left, top, left + width, top + height))

    def _load_piggy_image(self, stage):
        os.makedirs(self.assets_folder, exist_ok=True)
        path = os.path.join(self.assets_folder, f"piggy_{stage}.png")
        if os.path.exists(path):
            try:
                return Image.open(path).convert("RGBA")
            except Exception as e:
                logger.error(f"[Piggy] Cannot load asset {path}: {e}")

        return self._fallback_piggy(stage)

    @staticmethod
    def _fit_image(image, max_width, max_height):
        image = image.convert("RGBA")
        scale = min(max_width / image.width, max_height / image.height)
        size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
        return image.resize(size, Image.Resampling.LANCZOS)

    @staticmethod
    def _draw_text_plate(image, x, y, text_image, padding_x=12, padding_y=5):
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle(
            [
                x - padding_x,
                y - padding_y,
                x + text_image.width + padding_x,
                y + text_image.height + padding_y,
            ],
            radius=10,
            fill=(0, 0, 0, 120),
        )

    def _fallback_piggy(self, stage):
        img = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        body = (255, 136, 180, 255)
        dark = (170, 72, 112, 255)
        shine = (255, 190, 215, 255)

        draw.ellipse([34, 82, 224, 196], fill=body, outline=dark, width=5)
        draw.ellipse([182, 103, 238, 158], fill=body, outline=dark, width=4)
        draw.ellipse([198, 120, 210, 132], fill=dark)
        draw.ellipse([220, 120, 232, 132], fill=dark)
        draw.polygon([(78, 88), (98, 40), (122, 92)], fill=body, outline=dark)
        draw.polygon([(145, 88), (178, 42), (184, 104)], fill=body, outline=dark)
        draw.ellipse([126, 103, 142, 119], fill=(40, 35, 40, 255))
        draw.rectangle([90, 76, 168, 86], fill=(42, 37, 45, 255))
        draw.arc([22, 118, 58, 162], start=120, end=330, fill=dark, width=5)
        draw.rectangle([78, 188, 98, 222], fill=dark)
        draw.rectangle([162, 188, 182, 222], fill=dark)
        draw.ellipse([72, 92, 130, 125], fill=shine)

        badge = self._text(str(stage), 34, self.colors["gold"], stroke=2)
        img.paste(badge, ((260 - badge.width) // 2, 142), badge)
        return img

    def _text(self, text, size, color, stroke=0):
        return self.text_renderer.render_text(
            text=text,
            font_size=size,
            color=color,
            stroke_width=stroke,
            stroke_color=(0, 0, 0, 255),
            shadow=stroke > 0,
            shadow_offset=(2, 2),
        )

    @staticmethod
    def _format_duration(seconds):
        seconds = max(0, int(seconds))
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"


def register():
    plugin = PiggyPlugin()
    logger.info("[Piggy] Piggy plugin registered")
    return {
        "name": "piggy",
        "aliases": ["/pigg", "/pb", "/pg"],
        "description": "Piggy Bank Jackpot\n\n"
        "/piggy - show piggy bank status\n"
        "/piggy smash - collect the current pot\n\n"
        "/piggy freeze - block smashing for 20-120 minutes\n\n"
        "Maximum 3 freezes per piggy cycle.",
        "execute": plugin.execute_game,
    }
