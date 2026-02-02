from base_game_plugin import BaseGamePlugin
from logger import logger
from PIL import Image, ImageDraw
import os
from utils import _get_unique_id
from user_manager import UserManager

class TransferPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="transfer"
        )
        self.WIDTH, self.HEIGHT = 300, 200
    
    def _get_text_width(self, text, font_size):
        font = self.text_renderer.get_font(font_size)
        
        temp_img = Image.new('RGBA', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0]
    
    def _create_transfer_image(self, sender_id, sender_data, recipient_id, recipient_data, 
                             amount, sender_balance_before, recipient_balance_before):
        try:
            title_text = "TRANSFER COMPLETED"
            title_image = self.text_renderer.render_text(
                text=title_text,
                font_size=20,
                color=(255, 255, 255, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255)
            )
            
            amount_text = f"{amount}$"
            amount_image = self.text_renderer.render_text(
                text=amount_text,
                font_size=26,
                color=(0, 255, 0, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255)
            )
            
            sender_bg_path = self.cache.get_background_path(sender_id)
            if sender_bg_path and os.path.exists(sender_bg_path):
                background = Image.open(sender_bg_path).convert("RGBA")
            else:
                background = Image.new("RGBA", (self.WIDTH, self.HEIGHT), (30, 30, 40, 255))
            
            background = background.resize((self.WIDTH, self.HEIGHT))
            
            overlay = Image.new("RGBA", (self.WIDTH, self.HEIGHT), (0, 0, 0, 150))
            draw = ImageDraw.Draw(overlay)
            
            title_x = (self.WIDTH - title_image.width) // 2
            overlay.paste(title_image, (title_x, 15), title_image)
            
            avatar_size = 60
            arrow_width = 60
            
            sender_avatar_path = self.cache.get_avatar_path(sender_id)
            sender_avatar = Image.open(sender_avatar_path).convert("RGBA").resize((avatar_size, avatar_size))
            sender_avatar_mask = Image.new("L", (avatar_size, avatar_size), 0)
            ImageDraw.Draw(sender_avatar_mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
            
            recipient_avatar_path = self.cache.get_avatar_path(recipient_id)
            recipient_avatar = Image.open(recipient_avatar_path).convert("RGBA").resize((avatar_size, avatar_size))
            recipient_avatar_mask = Image.new("L", (avatar_size, avatar_size), 0)
            ImageDraw.Draw(recipient_avatar_mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
            
            total_width_needed = (avatar_size * 2) + arrow_width
            start_x = (self.WIDTH - total_width_needed) // 2
            
            sender_avatar_x = start_x
            sender_avatar_y = 70
            
            arrow_x = sender_avatar_x + avatar_size
            arrow_y = sender_avatar_y + (avatar_size // 2) - 15
            
            recipient_avatar_x = arrow_x + arrow_width
            recipient_avatar_y = sender_avatar_y
            
            amount_x = arrow_x + (arrow_width - amount_image.width) // 2
            overlay.paste(amount_image, (amount_x, arrow_y - 25), amount_image)
            
            arrow_color = (0, 200, 0, 255)
            arrow_center_y = arrow_y + 25
            
            draw.line([(arrow_x + 10, arrow_center_y), (arrow_x + arrow_width - 20, arrow_center_y)], 
                     fill=arrow_color, width=5)
            
            arrow_tip_x = arrow_x + arrow_width - 10
            arrow_tip_y = arrow_center_y
            
            draw.polygon([
                (arrow_tip_x, arrow_tip_y),
                (arrow_tip_x - 15, arrow_tip_y - 8),
                (arrow_tip_x - 15, arrow_tip_y + 8)
            ], fill=arrow_color)
            
            info_start_y = sender_avatar_y + avatar_size + 10
            
            sender_name = sender_data.get("name", "Sender")
            sender_lines = self._split_nickname(sender_name, avatar_size + 10, font_size=11)
            
            for i, line in enumerate(sender_lines):
                name_image = self.text_renderer.render_text(
                    text=line,
                    font_size=11,
                    color=(220, 220, 220, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                line_x = sender_avatar_x + (avatar_size - name_image.width) // 2
                overlay.paste(name_image, (line_x, info_start_y + (i * 12)), name_image)
            
            recipient_name = recipient_data.get("name", "Recipient")
            recipient_lines = self._split_nickname(recipient_name, avatar_size + 10, font_size=11)
            
            for i, line in enumerate(recipient_lines):
                name_image = self.text_renderer.render_text(
                    text=line,
                    font_size=11,
                    color=(220, 220, 220, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                line_x = recipient_avatar_x + (avatar_size - name_image.width) // 2
                overlay.paste(name_image, (line_x, info_start_y + (i * 12)), name_image)
            
            balance_y = info_start_y + max(len(sender_lines), len(recipient_lines)) * 12 + 5
            
            sender_balance_text = f"{sender_balance_before} → {sender_balance_before - amount}"
            sender_balance_image = self.text_renderer.render_text(
                text=sender_balance_text,
                font_size=10,
                color=(255, 100, 100, 255)
            )
            sender_balance_x = sender_avatar_x + (avatar_size - sender_balance_image.width) // 2
            overlay.paste(sender_balance_image, (sender_balance_x, balance_y), sender_balance_image)
            
            recipient_balance_text = f"{recipient_balance_before} → {recipient_balance_before + amount}"
            recipient_balance_image = self.text_renderer.render_text(
                text=recipient_balance_text,
                font_size=10,
                color=(100, 255, 100, 255)
            )
            recipient_balance_x = recipient_avatar_x + (avatar_size - recipient_balance_image.width) // 2
            overlay.paste(recipient_balance_image, (recipient_balance_x, balance_y), recipient_balance_image)
            
            composite = Image.alpha_composite(background, overlay)
            
            avatar_overlay = Image.new("RGBA", (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
            avatar_overlay.paste(sender_avatar, (sender_avatar_x, sender_avatar_y), sender_avatar_mask)
            avatar_overlay.paste(recipient_avatar, (recipient_avatar_x, recipient_avatar_y), recipient_avatar_mask)
            
            composite = Image.alpha_composite(composite, avatar_overlay)
            
            decor_draw = ImageDraw.Draw(composite)
            decor_draw.ellipse([(sender_avatar_x-2, sender_avatar_y-2), 
                              (sender_avatar_x+avatar_size+1, sender_avatar_y+avatar_size+1)], 
                             outline=(255, 100, 100, 255), width=2)
            decor_draw.ellipse([(recipient_avatar_x-2, recipient_avatar_y-2), 
                              (recipient_avatar_x+avatar_size+1, recipient_avatar_y+avatar_size+1)], 
                             outline=(100, 255, 100, 255), width=2)
            
            timestamp = _get_unique_id()
            output_path = os.path.join(self.get_app_path("temp"), f"transfer_{timestamp}.webp")
            composite.save(output_path, format="WEBP", quality=90, method=4)
            
            logger.info(f"Transfer image created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating transfer image: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _split_nickname(self, nickname, max_width, font_size=11):
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
            lines[-1] = lines[-1][:10] + ".." if len(lines[-1]) > 10 else lines[-1]
        
        return lines

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache

        if not cache or not sender or not avatar_url:
            logger.error(f"[Transfer] Internal error: insufficient data")
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Internal Error: Insufficient data",
                title="TRANSFER ERROR",
                cache=cache,
                user_id=None
            )
            return None

        if len(args) < 2:
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Usage: /transfer <amount> <player_name>\n\nExample: /transfer 100 John",
                title="TRANSFER HELP",
                cache=cache,
                user_id=None
            )
            return None

        try:
            amount = int(args[0])
            if amount <= 0:
                raise ValueError
        except ValueError:
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message=(
                    "Invalid amount. Must be a positive number\n\n"
                    "Examples:\n"
                    "- /transfer 100 John\n"
                    "- /transfer 500 Jane Doe"
                ),
                title="TRANSFER ERROR",
                cache=cache,
                user_id=None
            )
            return None

        recipient_name_raw = " ".join(args[1:]).strip()
        recipient_input = recipient_name_raw[1:].strip() if recipient_name_raw.startswith("@") else recipient_name_raw

        if not recipient_input:
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Player name cannot be empty\n\nUsage: /transfer <amount> <player_name>",
                title="TRANSFER ERROR",
                cache=cache,
                user_id=None
            )
            return None

        sender_id, sender_data, error = self.validate_user(cache, sender, avatar_url)
        if error or not sender_data:
            logger.error(f"[Transfer] Sender not found: {sender}")
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Sender account not found",
                title="TRANSFER ERROR",
                cache=cache,
                user_id=None
            )
            return None

        sender_balance_before = sender_data.get("balance", 0)
        if sender_balance_before < amount:
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message=(
                    f"Insufficient funds\n\n"
                    f"Your balance: {sender_balance_before}\n"
                    f"Transfer amount: {amount}"
                ),
                title="TRANSFER ERROR",
                cache=cache,
                user_id=sender_id
            )
            return None

        recipients = []

        if recipient_input.isdigit():
            user_manager = UserManager(cache)
            
            result = user_manager.find_user_by_id(recipient_input)
            
            if not result or not result[1]:
                self.send_message_image(
                    nickname=sender,
                    file_queue=file_queue,
                    message=f"Player with ID '{recipient_input}' not found",
                    title="TRANSFER ERROR",
                    cache=cache,
                    user_id=sender_id
                )
                return None
            
            recipient_id, recipient_data = result
            recipients = [(recipient_id, recipient_data)]

        else:
            recipients = self._find_recipient_by_name_safe(recipient_input, cache)

            if not recipients:
                self.send_message_image(
                    nickname=sender,
                    file_queue=file_queue,
                    message=f"Player '{recipient_input}' not found",
                    title="TRANSFER ERROR",
                    cache=cache,
                    user_id=sender_id
                )
                return None

            if len(recipients) > 1:
                self.send_message_image(
                    nickname=sender,
                    file_queue=file_queue,
                    message=self._format_multiple_recipients_error(recipients, recipient_input),
                    title="TRANSFER - MULTIPLE USERS",
                    cache=cache,
                    user_id=sender_id
                )
                return None

            recipient_id, recipient_data = recipients[0]

        if sender_id == recipient_id:
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Cannot transfer money to yourself",
                title="TRANSFER ERROR",
                cache=cache,
                user_id=sender_id
            )
            return None

        recipient_balance_before = recipient_data.get("balance", 0)

        try:
            sender_balance_new = sender_balance_before - amount
            recipient_balance_new = recipient_balance_before + amount
            
            if not cache.update_user(sender_id, balance=sender_balance_new):
                raise RuntimeError("Failed to update sender balance")

            if not cache.update_user(recipient_id, balance=recipient_balance_new):
                cache.update_user(sender_id, balance=sender_balance_before)
                raise RuntimeError("Failed to update recipient balance")

            transfer_image_path = self._create_transfer_image(
                sender_id=sender_id,
                sender_data=sender_data,
                recipient_id=recipient_id,
                recipient_data=recipient_data,
                amount=amount,
                sender_balance_before=sender_balance_before,
                recipient_balance_before=recipient_balance_before
            )

            if transfer_image_path and os.path.exists(transfer_image_path):
                file_queue.put(transfer_image_path)
            else:
                logger.warning("Transfer image creation failed, sending text message")
                recipient_display_name = recipient_data.get("name", recipient_input)
                self.send_message_image(
                    nickname=sender,
                    file_queue=file_queue,
                    message=(
                        "SUCCESSFUL TRANSFER\n\n"
                        f"Amount: {amount}$\n"
                        f"To: {recipient_display_name}\n"
                        f"Your balance: {sender_balance_before} → {sender_balance_new}\n"
                        f"Recipient's balance: {recipient_balance_before} → {recipient_balance_new}"
                    ),
                    title="TRANSFER COMPLETED",
                    cache=cache,
                    user_id=sender_id
                )

            logger.info(f"[Transfer] Transfer completed: {sender_id} → {recipient_id}, amount: {amount}")

        except Exception as e:
            logger.error("[Transfer] Transfer failed", exc_info=True)
            try:
                cache.update_user(sender_id, balance=sender_balance_before)
                cache.update_user(recipient_id, balance=recipient_balance_before)
            except Exception:
                pass

            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message=f"Transfer failed: {str(e)}\n\nPlease try again later",
                title="TRANSFER ERROR",
                cache=cache,
                user_id=sender_id
            )

        return None
    
    def _find_recipient_by_name_safe(self, name, cache):
        if not hasattr(cache, 'users') or not cache.users:
            logger.error("[Transfer] Cache has no users or users is empty")
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
        if not recipients:
            return ""

        error_msg = "MULTIPLE USERS FOUND\n\n"
        error_msg += f"More than one user matches '{searched_name}'.\n"
        error_msg += "Please use the USER ID instead of the name.\n\n"

        for i, (user_id, user_data) in enumerate(recipients[:5], 1):
            user_name = user_data.get("name", "Unknown")
            balance = user_data.get("balance", 0)

            error_msg += (
                f"{i}. Name: {user_name}\n"
                f"   User ID: {user_id}\n"
                f"   Balance: {balance}\n\n"
            )

        if len(recipients) > 5:
            error_msg += f"... and {len(recipients) - 5} more users.\n\n"

        error_msg += (
            "Example:\n"
            "/transfer <amount> <user_id>"
        )

        return error_msg

def register():
    plugin = TransferPlugin()
    return {
        "name": "transfer",
        "aliases": ["/t"],
        "description": (
            "TRANSFER MONEY BETWEEN PLAYERS\n\n"
            "Usage: /transfer <amount> <player_name>\n\n"
            "Examples:\n"
            "- /transfer 100 John\n"
            "- /transfer 500 Jane Doe\n"
            "- /transfer 100 @John  (ignores @ symbol)\n\n"
            "Creates a visual representation of the transfer with avatars!"
        ),
        "execute": plugin.execute_game
    }