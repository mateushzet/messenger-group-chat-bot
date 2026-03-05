import os
import time
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
from dataclasses import dataclass
from typing import Tuple, Optional
from base_game_plugin import BaseGamePlugin
from logger import logger
from utils import _get_unique_id

@dataclass
class GiftConfig:
    width: int = 350
    height: int = 300
    avatar_size: int = 70
    corner_radius: int = 20
    webp_quality: int = 90

@dataclass
class GiftColors:
    background_top: int = 20
    background_bottom_offset: int = 20
    
    background: Tuple[int, int, int, int] = (25, 25, 35, 230)
    title_color: Tuple[int, int, int, int] = (255, 220, 100, 255)
    amount_color: Tuple[int, int, int, int] = (100, 255, 100, 255)
    text_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    status_color: Tuple[int, int, int, int] = (200, 200, 220, 255)
    error_color: Tuple[int, int, int, int] = (255, 100, 100, 255)
    info_color: Tuple[int, int, int, int] = (100, 200, 255, 255)
    sender_color: Tuple[int, int, int, int] = (255, 150, 100, 255)
    recipient_color: Tuple[int, int, int, int] = (100, 255, 150, 255)

class GiftImageGenerator:
    def __init__(self, text_renderer):
        self.config = GiftConfig()
        self.colors = GiftColors()
        self.text_renderer = text_renderer
    
    def _get_text_width(self, text, font_size):
        font = self.text_renderer.get_font(font_size)
        temp_img = Image.new('RGBA', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]
    
    def _split_nickname(self, nickname, max_width, font_size=14):
        words = nickname.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if self._get_text_width(test_line, font_size) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        if len(lines) > 2:
            lines = lines[:2]
            if len(lines[-1]) > 15:
                lines[-1] = lines[-1][:12] + "..."
        
        return lines
    
    def generate_gift_image(self,
                          sender_name: str,
                          sender_avatar_path: str,
                          recipient_name: str,
                          recipient_avatar_path: str,
                          recipient_balance_after: int,
                          amount: int = 50,
                          error_message: Optional[str] = None) -> Optional[Image.Image]:
        try:
            img = Image.new("RGBA", (self.config.width, self.config.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            draw.rectangle(
                [0, 0, self.config.width, self.config.height],
                fill=self.colors.background
            )
            
            if error_message:
                title_text = "GIFT ERROR"
                title_color = self.colors.error_color
            else:
                title_text = "DAILY GIFT SENT"
                title_color = self.colors.title_color
            
            title_img = self.text_renderer.render_text(
                text=title_text,
                font_size=28,
                color=title_color,
                stroke_width=2,
                stroke_color=(0, 0, 0, 200),
                shadow=True
            )
            
            title_x = (self.config.width - title_img.width) // 2
            img.paste(title_img, (title_x, 25), title_img)
            
            if not error_message:
                amount_text = f"+{amount}$"
                amount_img = self.text_renderer.render_text(
                    text=amount_text,
                    font_size=42,
                    color=self.colors.amount_color,
                    stroke_width=3,
                    stroke_color=(0, 0, 0, 200),
                    shadow=True,
                    shadow_offset=(2, 2)
                )
                
                amount_x = (self.config.width - amount_img.width) // 2
                img.paste(amount_img, (amount_x, 70), amount_img)
            
            avatars_y = 140
            
            avatar_spacing = 40
            total_width = (self.config.avatar_size * 2) + avatar_spacing
            start_x = (self.config.width - total_width) // 2
            
            sender_avatar_x = start_x
            sender_avatar_y = avatars_y
            
            if sender_avatar_path and os.path.exists(sender_avatar_path):
                try:
                    sender_avatar = Image.open(sender_avatar_path).convert("RGBA")
                    sender_avatar = sender_avatar.resize((self.config.avatar_size, self.config.avatar_size))
                    
                    mask = Image.new('L', (self.config.avatar_size, self.config.avatar_size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse([0, 0, self.config.avatar_size, self.config.avatar_size], fill=255)
                    
                    img.paste(sender_avatar, (sender_avatar_x, sender_avatar_y), mask)
                    
                    draw.ellipse(
                        [sender_avatar_x-2, sender_avatar_y-2,
                         sender_avatar_x+self.config.avatar_size+2, sender_avatar_y+self.config.avatar_size+2],
                        outline=self.colors.sender_color,
                        width=3
                    )
                except Exception as e:
                    logger.error(f"Error loading sender avatar: {e}")
                    draw.ellipse(
                        [sender_avatar_x, sender_avatar_y,
                         sender_avatar_x+self.config.avatar_size, sender_avatar_y+self.config.avatar_size],
                        fill=(100, 100, 120, 255),
                        outline=self.colors.sender_color,
                        width=2
                    )
            else:
                draw.ellipse(
                    [sender_avatar_x, sender_avatar_y,
                     sender_avatar_x+self.config.avatar_size, sender_avatar_y+self.config.avatar_size],
                    fill=(100, 100, 120, 255),
                    outline=self.colors.sender_color,
                    width=2
                )
            
            recipient_avatar_x = start_x + self.config.avatar_size + avatar_spacing
            recipient_avatar_y = avatars_y
            
            if recipient_avatar_path and os.path.exists(recipient_avatar_path):
                try:
                    recipient_avatar = Image.open(recipient_avatar_path).convert("RGBA")
                    recipient_avatar = recipient_avatar.resize((self.config.avatar_size, self.config.avatar_size))
                    
                    mask = Image.new('L', (self.config.avatar_size, self.config.avatar_size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse([0, 0, self.config.avatar_size, self.config.avatar_size], fill=255)
                    
                    img.paste(recipient_avatar, (recipient_avatar_x, recipient_avatar_y), mask)
                    
                    draw.ellipse(
                        [recipient_avatar_x-2, recipient_avatar_y-2,
                         recipient_avatar_x+self.config.avatar_size+2, recipient_avatar_y+self.config.avatar_size+2],
                        outline=self.colors.recipient_color,
                        width=3
                    )
                except Exception as e:
                    logger.error(f"Error loading recipient avatar: {e}")
                    draw.ellipse(
                        [recipient_avatar_x, recipient_avatar_y,
                         recipient_avatar_x+self.config.avatar_size, recipient_avatar_y+self.config.avatar_size],
                        fill=(100, 100, 120, 255),
                        outline=self.colors.recipient_color,
                        width=2
                    )
            else:
                draw.ellipse(
                    [recipient_avatar_x, recipient_avatar_y,
                     recipient_avatar_x+self.config.avatar_size, recipient_avatar_y+self.config.avatar_size],
                    fill=(100, 100, 120, 255),
                    outline=self.colors.recipient_color,
                    width=2
                )
            
            arrow_start_x = sender_avatar_x + self.config.avatar_size + 5
            arrow_end_x = recipient_avatar_x - 5
            arrow_center_y = avatars_y + self.config.avatar_size // 2
            
            draw.line([(arrow_start_x, arrow_center_y), (arrow_end_x, arrow_center_y)],
                     fill=(255, 255, 255, 255), width=4)
            
            arrow_head_size = 12
            draw.polygon([
                (arrow_end_x, arrow_center_y),
                (arrow_end_x - arrow_head_size, arrow_center_y - 8),
                (arrow_end_x - arrow_head_size, arrow_center_y + 8)
            ], fill=(255, 255, 255, 255))
            
            name_start_y = avatars_y + self.config.avatar_size + 10
            max_name_width = self.config.avatar_size + 20
            
            sender_lines = self._split_nickname(sender_name, max_name_width, font_size=14)
            for i, line in enumerate(sender_lines):
                name_img = self.text_renderer.render_text(
                    text=line,
                    font_size=14,
                    color=self.colors.sender_color,
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 150)
                )
                name_x = sender_avatar_x + (self.config.avatar_size - name_img.width) // 2
                img.paste(name_img, (name_x, name_start_y + i * 18), name_img)
            
            recipient_lines = self._split_nickname(recipient_name, max_name_width, font_size=14)
            for i, line in enumerate(recipient_lines):
                name_img = self.text_renderer.render_text(
                    text=line,
                    font_size=14,
                    color=self.colors.recipient_color,
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 150)
                )
                name_x = recipient_avatar_x + (self.config.avatar_size - name_img.width) // 2
                img.paste(name_img, (name_x, name_start_y + i * 18), name_img)
            
            balance_y = name_start_y + max(len(sender_lines), len(recipient_lines)) * 18 + 15
            
            recipient_balance_text = f"{recipient_balance_after}$"
            recipient_balance_img = self.text_renderer.render_text(
                text=recipient_balance_text,
                font_size=14,
                color=self.colors.recipient_color,
                stroke_width=1,
                stroke_color=(0, 0, 0, 150)
            )
            recipient_balance_x = recipient_avatar_x + (self.config.avatar_size - recipient_balance_img.width) // 2
            img.paste(recipient_balance_img, (recipient_balance_x, balance_y), recipient_balance_img)
            
            if error_message:
                error_y = self.config.height - 80
                error_lines = self._split_text(error_message, 450, font_size=16)
                for i, line in enumerate(error_lines):
                    error_img = self.text_renderer.render_text(
                        text=line,
                        font_size=16,
                        color=self.colors.error_color,
                        stroke_width=1
                    )
                    error_x = (self.config.width - error_img.width) // 2
                    img.paste(error_img, (error_x, error_y + i * 20), error_img)
            
            return img
            
        except Exception as e:
            logger.error(f"Error generating gift image: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _split_text(self, text, max_width, font_size=16):
        words = text.split()
        lines = []
        current_line = []
        
        font = self.text_renderer.get_font(font_size)
        temp_img = Image.new('RGBA', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = temp_draw.textbbox((0, 0), test_line, font=font)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
class GiftPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="gift")
        
        text_renderer = self.generator.text_renderer
        self.image_generator = GiftImageGenerator(text_renderer=text_renderer)
        
        self.GIFT_AMOUNT = 50
        
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
    
    def _can_send_gift_today(self, user_id):
        user = self.cache.get_user(user_id)
        if not user:
            return False, None
        
        today = datetime.now().date()
        last_gift_date = self._parse_date(user.get("last_gift_time"))
        
        if not last_gift_date:
            return True, None
        
        if last_gift_date == today:
            next_gift_date = today + timedelta(days=1)
            return False, next_gift_date
        
        return True, None
    
    def _find_recipient(self, name_or_id, cache):
        if name_or_id.isdigit():
            for uid, udata in cache.users.items():
                if uid == name_or_id:
                    return [(uid, udata)]
        
        return self._find_recipient_by_name_safe(name_or_id, cache)
    
    def _find_recipient_by_name_safe(self, name, cache):
        if not hasattr(cache, 'users') or not cache.users:
            return []
        
        search_name = name
        if search_name.startswith('@'):
            search_name = search_name[1:].strip()
        
        exact_matches = []
        partial_matches = []
        name_lower = search_name.lower().strip()
        
        for user_id, user_data in cache.users.items():
            if not isinstance(user_data, dict):
                continue
            
            user_name = user_data.get('name', '')
            if not user_name:
                continue
            
            user_name_lower = user_name.lower()
            
            if user_name_lower == name_lower:
                exact_matches.append((user_id, user_data))
            elif user_name_lower.startswith(name_lower):
                partial_matches.append((user_id, user_data))
        
        return exact_matches + partial_matches
    
    def _format_multiple_recipients_error(self, recipients, searched_name):
        error_msg = "MULTIPLE USERS FOUND\n\n"
        error_msg += f"More than one user matches '{searched_name}'.\n"
        error_msg += "Please use the USER ID instead of the name.\n\n"
        
        for i, (user_id, user_data) in enumerate(recipients[:5], 1):
            user_name = user_data.get("name", "Unknown")
            error_msg += f"{i}. {user_name} (ID: {user_id})\n"
        
        if len(recipients) > 5:
            error_msg += f"\n... and {len(recipients) - 5} more users."
        
        error_msg += "\n\nExample: /gift 123456"
        return error_msg
    
    def _send_gift(self, sender_id, recipient_id):
        sender = self.cache.get_user(sender_id)
        recipient = self.cache.get_user(recipient_id)
        
        if not sender or not recipient:
            return None, "User not found"
        
        recipient_balance_before = recipient.get("balance", 0)
        
        recipient_balance_after = recipient_balance_before + self.GIFT_AMOUNT
        
        today_str = datetime.now().date().isoformat()
        if not self.cache.update_user(sender_id, last_gift_time=today_str):
            return None, "Failed to update sender"
        
        if not self.cache.update_user(recipient_id, balance=recipient_balance_after):
            self.cache.update_user(sender_id, last_gift_time=None)
            return None, "Failed to update recipient"
        
        return {
            'recipient_balance_before': recipient_balance_before,
            'recipient_balance_after': recipient_balance_after,
            'amount': self.GIFT_AMOUNT
        }, None
    
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        if not cache or not sender or not avatar_url:
            logger.error("[Gift] Internal error: insufficient data")
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Internal Error: Insufficient data",
                title="GIFT ERROR",
                cache=cache,
                user_id=None
            )
            return None
        
        sender_id, sender_data, error = self.validate_user(cache, sender, avatar_url)
        if error or not sender_data:
            logger.error(f"[Gift] Sender not found: {sender}")
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Sender account not found",
                title="GIFT ERROR",
                cache=cache,
                user_id=None
            )
            return None
        
        if len(args) < 1:
            return self._show_help(sender, sender_id, sender_data, file_queue)
        
        recipient_input = " ".join(args).strip()
        recipient_input = recipient_input[1:].strip() if recipient_input.startswith("@") else recipient_input
        
        can_send, next_gift_date = self._can_send_gift_today(sender_id)
        if not can_send:
            
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message=(
                    f"ALREADY SENT TODAY\n\n"
                    f"You've already sent your daily gift.\n"
                    f"Next gift available tomorrow"
                ),
                title="ALREADY SENT",
                cache=cache,
                user_id=sender_id
            )
            return None
        
        recipients = self._find_recipient(recipient_input, cache)
        
        if not recipients:
            return self._show_recipient_not_found(sender, sender_id, sender_data, 
                                                  recipient_input, file_queue)
        
        if len(recipients) > 1:
            return self._show_multiple_recipients(sender, sender_id, sender_data, 
                                                  recipients, recipient_input, file_queue)
        
        recipient_id, recipient_data = recipients[0]
        
        if sender_id == recipient_id:
            error_img = self.image_generator.generate_gift_image(
                sender_name=sender_data.get("name", sender),
                sender_avatar_path=self.cache.get_avatar_path(sender_id),
                recipient_name=recipient_data.get("name", recipient_input),
                recipient_avatar_path=self.cache.get_avatar_path(recipient_id),
                recipient_balance_after=recipient_data.get("balance", 0),
                error_message="Cannot send gift to yourself"
            )
            
            if error_img:
                self._save_and_queue_image(error_img, sender_id, file_queue)
            return None
        
        result, error_msg = self._send_gift(sender_id, recipient_id)
        
        if error_msg or not result:
            error_img = self.image_generator.generate_gift_image(
                sender_name=sender_data.get("name", sender),
                sender_avatar_path=self.cache.get_avatar_path(sender_id),
                recipient_name=recipient_data.get("name", recipient_input),
                recipient_avatar_path=self.cache.get_avatar_path(recipient_id),
                recipient_balance_after=recipient_data.get("balance", 0),
                error_message=f"Transfer failed: {error_msg or 'Unknown error'}"
            )
            
            if error_img:
                self._save_and_queue_image(error_img, sender_id, file_queue)
            return None
        
        updated_recipient = self.cache.get_user(recipient_id)
        recipient_balance_after = updated_recipient.get("balance", 0) if updated_recipient else 0
        
        success_img = self.image_generator.generate_gift_image(
            sender_name=sender_data.get("name", sender),
            sender_avatar_path=self.cache.get_avatar_path(sender_id),
            recipient_name=recipient_data.get("name", recipient_input),
            recipient_avatar_path=self.cache.get_avatar_path(recipient_id),
            recipient_balance_after=recipient_balance_after,
            amount=self.GIFT_AMOUNT
        )
        
        if success_img:
            self._save_and_queue_image(success_img, sender_id, file_queue)
        
        return None
    
    def _show_help(self, sender, sender_id, sender_data, file_queue):
        can_send, _ = self._can_send_gift_today(sender_id)
        
        if can_send:
            status = "Available now!"
        else:
            status = "Already sent today"
        
        help_text = (
            f"DAILY GIFT SYSTEM\n\n"
            f"Send {self.GIFT_AMOUNT}$ to another player for FREE!\n"
            f"One gift per day.\n\n"
            f"Status: {status}\n\n"
            f"Usage: /gift <player_name>\n"
            f"Examples:\n"
            f"  /gift John\n"
            f"  /gift 123456\n"
            f"  /gift @John"
        )
        
        self.send_message_image(
            nickname=sender,
            file_queue=file_queue,
            message=help_text,
            title="GIFT SYSTEM",
            cache=self.cache,
            user_id=sender_id
        )
        
        return None
    
    def _show_recipient_not_found(self, sender, sender_id, sender_data, recipient_input, file_queue):
        error_img = self.image_generator.generate_gift_image(
            sender_name=sender_data.get("name", sender),
            sender_avatar_path=self.cache.get_avatar_path(sender_id),
            recipient_name=recipient_input,
            recipient_avatar_path="",
            recipient_balance_after=0,
            error_message=f"Player '{recipient_input}' not found"
        )
        
        if error_img:
            self._save_and_queue_image(error_img, sender_id, file_queue)
        
        return None
    
    def _show_multiple_recipients(self, sender, sender_id, sender_data, recipients, recipient_input, file_queue):
        error_msg = self._format_multiple_recipients_error(recipients, recipient_input)
        
        error_img = self.image_generator.generate_gift_image(
            sender_name=sender_data.get("name", sender),
            sender_avatar_path=self.cache.get_avatar_path(sender_id),
            recipient_name=recipient_input,
            recipient_avatar_path="",
            recipient_balance_after=0,
            error_message="Multiple users found. Use ID."
        )
        
        if error_img:
            self._save_and_queue_image(error_img, sender_id, file_queue)
        
        self.send_message_image(
            nickname=sender,
            file_queue=file_queue,
            message=error_msg,
            title="GIFT - MULTIPLE USERS",
            cache=self.cache,
            user_id=sender_id
        )
        
        return None
    
    def _save_and_queue_image(self, img, user_id, file_queue):
        timestamp = _get_unique_id()
        img_path = os.path.join(self.results_folder, f"gift_{user_id}_{timestamp}.webp")
        img.save(img_path, format='WEBP', quality=90)
        file_queue.put(img_path)

def register():
    plugin = GiftPlugin()
    return {
        "name": "gift",
        "aliases": ["/gift", "/dailygift"],
        "description": (
            "DAILY GIFT SYSTEM\n\n"
            f"Send {plugin.GIFT_AMOUNT}$ to another player every day for FREE!\n\n"
            "Usage:\n"
            "  /gift <player_name>  - Send daily gift\n"
            "  /gift                - Check status\n\n"
            "Examples:\n"
            "  /gift John\n"
            "  /gift 123456        (using user ID)\n"
            "  /gift @John         (ignores @ symbol)"
        ),
        "execute": plugin.execute_game
    }