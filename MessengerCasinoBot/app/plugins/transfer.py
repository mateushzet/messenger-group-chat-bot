from base_game_plugin import BaseGamePlugin
from logger import logger
from PIL import Image, ImageDraw, ImageFont
import os
import time
import textwrap
from utils import _get_unique_id

class TransferPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="transfer",
            results_folder=self.get_app_path("temp"),
        )
        self._icons_loaded = False
        self._fonts = {}
        self.WIDTH, self.HEIGHT = 300, 200  # Zwiększona wysokość dla lepszego rozmieszczenia

    def _load_fonts(self):
        """Ładuje czcionki tylko raz"""
        if self._icons_loaded:
            return
        
        try:
            self._fonts['title'] = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
            self._fonts['amount'] = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
            self._fonts['names'] = ImageFont.truetype("DejaVuSans-Bold.ttf", 11)  # Mniejsza czcionka
            self._fonts['balance'] = ImageFont.truetype("DejaVuSans-Bold.ttf", 10)  # Mniejsza czcionka
        except:
            # Fallback na czcionkę domyślną
            default_font = ImageFont.load_default()
            self._fonts = {k: default_font for k in ['title', 'amount', 'names', 'balance']}
        
        self._icons_loaded = True

    def _split_nickname(self, nickname, max_width, font):
        """Dzieli nickname na linie jeśli jest za długi"""
        words = nickname.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if self._get_text_width(test_line, font) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Jeśli nadal za długie, skróć
        if len(lines) > 2:
            lines = lines[:2]
            lines[-1] = lines[-1][:10] + ".." if len(lines[-1]) > 10 else lines[-1]
        
        return lines

    def _create_transfer_image(self, sender_id, sender_data, recipient_id, recipient_data, 
                             amount, sender_balance_before, recipient_balance_before):
        """Tworzy customową grafikę transferu z tłem i avatarami"""
        try:
            self._load_fonts()
            
            # Pobierz tło nadawcy (lub domyślne)
            sender_bg_path = self.cache.get_background_path(sender_id)
            if os.path.exists(sender_bg_path):
                background = Image.open(sender_bg_path).convert("RGBA")
            else:
                # Domyślne tło jeśli brak
                background = Image.new("RGBA", (self.WIDTH, self.HEIGHT), (30, 30, 40, 255))
            
            background = background.resize((self.WIDTH, self.HEIGHT))
            
            # Utwórz przezroczystą warstwę overlay
            overlay = Image.new("RGBA", (self.WIDTH, self.HEIGHT), (0, 0, 0, 150))
            draw = ImageDraw.Draw(overlay)
            
            # ===== GÓRNA CZĘŚĆ: TYTUŁ =====
            title_text = "TRANSFER COMPLETED"
            title_width = self._get_text_width(title_text, self._fonts['title'])
            title_x = (self.WIDTH - title_width) // 2
            draw.text((title_x, 15), title_text, font=self._fonts['title'], 
                     fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 255))
            
            # ===== ŚRODKOWA CZĘŚĆ: AVATARY I STRZAŁKA =====
            avatar_size = 60
            arrow_width = 60  # Szersza strzałka
            
            # Avatar nadawcy
            sender_avatar_path = self.cache.get_avatar_path(sender_id)
            sender_avatar = Image.open(sender_avatar_path).convert("RGBA").resize((avatar_size, avatar_size))
            sender_avatar_mask = Image.new("L", (avatar_size, avatar_size), 0)
            ImageDraw.Draw(sender_avatar_mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
            
            # Avatar odbiorcy
            recipient_avatar_path = self.cache.get_avatar_path(recipient_id)
            recipient_avatar = Image.open(recipient_avatar_path).convert("RGBA").resize((avatar_size, avatar_size))
            recipient_avatar_mask = Image.new("L", (avatar_size, avatar_size), 0)
            ImageDraw.Draw(recipient_avatar_mask).ellipse((0, 0, avatar_size, avatar_size), fill=255)
            
            # Pozycje - wszystko wycentrowane
            total_width_needed = (avatar_size * 2) + arrow_width
            start_x = (self.WIDTH - total_width_needed) // 2
            
            sender_avatar_x = start_x
            sender_avatar_y = 70
            
            # Strzałka na środku między avatarami
            arrow_x = sender_avatar_x + avatar_size
            arrow_y = sender_avatar_y + (avatar_size // 2) - 15  # Wyżej dla kwoty
            
            recipient_avatar_x = arrow_x + arrow_width
            recipient_avatar_y = sender_avatar_y
            
            # ===== KWOTA TRANSFERU NAD STRZAŁKĄ =====
            amount_text = f"{amount}$"
            amount_width = self._get_text_width(amount_text, self._fonts['amount'])
            amount_x = arrow_x + (arrow_width - amount_width) // 2
            draw.text((amount_x, arrow_y - 25), amount_text, font=self._fonts['amount'],
                     fill=(0, 255, 0, 255), stroke_width=2, stroke_fill=(0, 0, 0, 255))
            
            # ===== STRZAŁKA (grubsza, bardziej widoczna) =====
            arrow_color = (0, 200, 0, 255)
            arrow_center_x = arrow_x + (arrow_width // 2)
            arrow_center_y = arrow_y + 25
            
            # Linia pozioma strzałki
            draw.line([(arrow_x + 10, arrow_center_y), (arrow_x + arrow_width - 20, arrow_center_y)], 
                     fill=arrow_color, width=5)
            
            # Grot strzałki
            arrow_tip_x = arrow_x + arrow_width - 10
            arrow_tip_y = arrow_center_y
            
            # Rysuj grot strzałki (trójkąt)
            draw.polygon([
                (arrow_tip_x, arrow_tip_y),
                (arrow_tip_x - 15, arrow_tip_y - 8),
                (arrow_tip_x - 15, arrow_tip_y + 8)
            ], fill=arrow_color)
            
            # ===== NICKI POD AVATARAMI =====
            info_start_y = sender_avatar_y + avatar_size + 10
            
            # Nick nadawcy
            sender_name = sender_data.get("name", "Sender")
            sender_lines = self._split_nickname(sender_name, avatar_size + 10, self._fonts['names'])
            
            sender_text_height = len(sender_lines) * 12
            sender_text_y = info_start_y
            
            for i, line in enumerate(sender_lines):
                line_width = self._get_text_width(line, self._fonts['names'])
                line_x = sender_avatar_x + (avatar_size - line_width) // 2
                draw.text((line_x, sender_text_y + (i * 12)), line, 
                         font=self._fonts['names'], fill=(220, 220, 220, 255),
                         stroke_width=1, stroke_fill=(0, 0, 0, 255))
            
            # Nick odbiorcy
            recipient_name = recipient_data.get("name", "Recipient")
            recipient_lines = self._split_nickname(recipient_name, avatar_size + 10, self._fonts['names'])
            
            recipient_text_height = len(recipient_lines) * 12
            recipient_text_y = info_start_y
            
            for i, line in enumerate(recipient_lines):
                line_width = self._get_text_width(line, self._fonts['names'])
                line_x = recipient_avatar_x + (avatar_size - line_width) // 2
                draw.text((line_x, recipient_text_y + (i * 12)), line, 
                         font=self._fonts['names'], fill=(220, 220, 220, 255),
                         stroke_width=1, stroke_fill=(0, 0, 0, 255))
            
            # ===== BALANSE =====
            balance_y = max(sender_text_y + sender_text_height, recipient_text_y + recipient_text_height) + 5
            
            # Balans nadawcy
            sender_balance_text = f"{sender_balance_before} → {sender_balance_before - amount}"
            sender_balance_width = self._get_text_width(sender_balance_text, self._fonts['balance'])
            sender_balance_x = sender_avatar_x + (avatar_size - sender_balance_width) // 2
            
            draw.text((sender_balance_x, balance_y), sender_balance_text, 
                     font=self._fonts['balance'], fill=(255, 100, 100, 255))
            
            # Balans odbiorcy
            recipient_balance_text = f"{recipient_balance_before} → {recipient_balance_before + amount}"
            recipient_balance_width = self._get_text_width(recipient_balance_text, self._fonts['balance'])
            recipient_balance_x = recipient_avatar_x + (avatar_size - recipient_balance_width) // 2
            
            draw.text((recipient_balance_x, balance_y), recipient_balance_text, 
                     font=self._fonts['balance'], fill=(100, 255, 100, 255))
            
            # ===== KOMPOZYCJA FINALNA =====
            # Połącz tło z overlay
            composite = Image.alpha_composite(background, overlay)
            
            # Dodaj avatary na wierzch (żeby były nad overlay)
            avatar_overlay = Image.new("RGBA", (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
            avatar_overlay.paste(sender_avatar, (sender_avatar_x, sender_avatar_y), sender_avatar_mask)
            avatar_overlay.paste(recipient_avatar, (recipient_avatar_x, recipient_avatar_y), recipient_avatar_mask)
            
            composite = Image.alpha_composite(composite, avatar_overlay)
            
            # Dodaj dekoracyjne ramki wokół avatarów
            decor_draw = ImageDraw.Draw(composite)
            # Ramka nadawcy (czerwona)
            decor_draw.ellipse([(sender_avatar_x-2, sender_avatar_y-2), 
                              (sender_avatar_x+avatar_size+1, sender_avatar_y+avatar_size+1)], 
                             outline=(255, 100, 100, 255), width=2)
            # Ramka odbiorcy (zielona)
            decor_draw.ellipse([(recipient_avatar_x-2, recipient_avatar_y-2), 
                              (recipient_avatar_x+avatar_size+1, recipient_avatar_y+avatar_size+1)], 
                             outline=(100, 255, 100, 255), width=2)
            
            # Zapisz obrazek
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

    def _get_text_width(self, text, font):
        """Pomocnicza funkcja do pobierania szerokości tekstu"""
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache

        if not cache or not sender or not avatar_url:
            logger.error(f"[Transfer] Internal error: insufficient data")
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Internal Error: Unsufficient data",
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
            recipient_id = int(recipient_input)
            recipient_data = cache.users.get(recipient_id)

            if not recipient_data:
                self.send_message_image(
                    nickname=sender,
                    file_queue=file_queue,
                    message=f"Player with ID {recipient_id} not found",
                    title="TRANSFER ERROR",
                    cache=cache,
                    user_id=sender_id
                )
                return None

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
            # Zapisujemy balanse przed operacją
            sender_balance_new = sender_balance_before - amount
            recipient_balance_new = recipient_balance_before + amount
            
            # Aktualizuj balans nadawcy
            if not cache.update_user(sender_id, balance=sender_balance_new):
                raise RuntimeError("Failed to update sender balance")

            # Aktualizuj balans odbiorcy
            if not cache.update_user(recipient_id, balance=recipient_balance_new):
                # Rollback jeśli odbiorca się nie zaktualizuje
                cache.update_user(sender_id, balance=sender_balance_before)
                raise RuntimeError("Failed to update recipient balance")

            # Stwórz customową grafikę transferu
            transfer_image_path = self._create_transfer_image(
                sender_id=sender_id,
                sender_data=sender_data,
                recipient_id=recipient_id,
                recipient_data=recipient_data,
                amount=amount,
                sender_balance_before=sender_balance_before,
                recipient_balance_before=recipient_balance_before
            )

            # Wyślij grafikę jeśli się udało stworzyć
            if transfer_image_path and os.path.exists(transfer_image_path):
                file_queue.put(transfer_image_path)
            else:
                # Fallback: wyślij tekstową wiadomość
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
                # Rollback w przypadku błędu
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