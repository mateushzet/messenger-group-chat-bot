import os
import time
import re
import threading
import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw
from logger import logger
import configparser


class EmailMonitor:
    def __init__(self, cache, command_queue=None, file_queue=None):
        self.cache = cache
        self.command_queue = command_queue
        self.file_queue = file_queue
        self.running = True
        
        self._load_config()
        
        self.processed_message_ids = set()
        self.log_file = 'transfers.log'
        
        self.temp_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "temp", "email_confirm")
        os.makedirs(self.temp_folder, exist_ok=True)
        
        self.colors = {
            "bg": (25, 28, 36),
            "panel": (39, 43, 54),
            "gold": (255, 210, 90),
            "green": (118, 240, 170),
            "pink": (255, 126, 173),
            "blue": (100, 180, 255),
            "red": (255, 100, 110),
            "text": (245, 245, 248),
            "muted": (178, 185, 198),
            "line": (72, 77, 92),
            "orange": (255, 165, 50),
            "purple": (180, 130, 255),
        }
        
        logger.info("[EmailMonitor] Initialized")
    
    def _load_config(self):
        try:
            app_path = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(app_path)))
            config_path = os.path.join(base_dir, 'MessengerCasinoBot', 'app', 'config', 'config.ini')
            
            logger.info(f"[EmailMonitor] Reading config from: {config_path}")
            
            if not os.path.exists(config_path):
                logger.error(f"[EmailMonitor] Config file not found")
                raise Exception("Config file not found")
            
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')
            
            if not config.has_section('email'):
                logger.error("[EmailMonitor] No [email] section in config")
                raise Exception("No [email] section in config")
            
            self.IMAP_SERVER = config.get('email', 'imap_server')
            self.EMAIL = config.get('email', 'email')
            self.PASSWORD = config.get('email', 'password')
            self.EXCHANGE_RATE = config.getint('email', 'exchange_rate')
            
            senders_str = config.get('email', 'allowed_senders')
            self.ALLOWED_SENDERS = [s.strip() for s in senders_str.split(',') if s.strip()]
            
            if not self.EMAIL or not self.PASSWORD:
                raise Exception("Email or password not configured")
            
            if not self.ALLOWED_SENDERS:
                raise Exception("No allowed senders configured")
            
            logger.info(f"[EmailMonitor] Config loaded successfully")
            
        except Exception as e:
            logger.error(f"[EmailMonitor] Error loading config: {e}")
            raise
    
    def decode_email_header(self, header):
        if not header:
            return ""
        try:
            decoded = decode_header(header)
            result = []
            for part, encoding in decoded:
                if isinstance(part, bytes):
                    try:
                        if encoding:
                            part = part.decode(encoding)
                        else:
                            part = part.decode('utf-8', errors='ignore')
                    except:
                        part = part.decode('utf-8', errors='ignore')
                result.append(str(part))
            return ''.join(result)
        except Exception as e:
            logger.error(f"Error decoding header: {e}")
            return str(header)
        
    def extract_transfer_details(self, email_body):
        try:
            if '<html' in email_body.lower() or '<div' in email_body.lower():
                soup = BeautifulSoup(email_body, 'html.parser')
                text = soup.get_text(separator=' ', strip=True)
            else:
                text = email_body
            
            result = {
                'kwota_pln': None,
                'kwota_grosze': None,
                'tytul': None,
                'user_id': None,
                'nadawca': None,
                'data_waluty': None,
                'stan_konta': None
            }
            
            amount_patterns = [
                r'wpłynęła\s+k(w|W)ota\s+\+([\d\s]+,\d{2})\s+PLN',
                r'w\s*tym:\s*\+([\d\s]+,\d{2})\s+PLN\s+Przelew',
                r'\+([\d\s]+,\d{2})\s+PLN\s+Przelew\s+na\s+telefon',
                r'\+([\d\s]+,\d{2})\s+PLN'
            ]
            
            match_amount = None
            for pattern in amount_patterns:
                match_amount = re.search(pattern, text, re.IGNORECASE)
                if match_amount:
                    break
            
            if match_amount:
                amount_str = None
                for group in match_amount.groups():
                    if group and re.search(r'[\d,]+', group):
                        amount_str = group.replace(' ', '').replace(',', '.')
                        break
                
                if amount_str:
                    result['kwota_pln'] = float(amount_str)
                    result['kwota_grosze'] = int(round(result['kwota_pln'] * 100))
            
            title_patterns = [
                r'tytuł\s*:\s*([^,\s]+(?:\s+[^,\n]+?)?)(?=\s*,|\s*$|\s*\.|\s*<|$)',
                r'tytuł\s*:\s*([^\n,]+)',
                r'tytu[łl]\s*:\s*([^,\s]+)',
                r'tytu[łl][:\s]+([^\n,]+)',
                r'tytu\s*:\s*([^,\s]+)',
                r'tytu[:\s]+([^\n,]+)',
                r'tytuł\s*([^\n,]+)',
            ]
            
            match_title = None
            for pattern in title_patterns:
                match_title = re.search(pattern, text, re.IGNORECASE)
                if match_title:
                    break
            
            if match_title:
                result['tytul'] = match_title.group(1).strip()
                result['tytul'] = re.sub(r'\s+', ' ', result['tytul'])
            
            if result['tytul']:
                clean_title = re.sub(r'\s+', '', result['tytul'])
                
                if re.match(r'^\d+$', clean_title):
                    result['user_id'] = clean_title
                    logger.info(f"Found clean numeric ID: {result['user_id']}")
                else:
                    id_patterns = [
                        r'^(\d+)\s+OD:',
                        r'^(\d+)\s+od\s+',
                        r'^(\d+)\s+',
                        r'#(\d+)',
                        r'ID[:\s]+(\d+)',
                        r'ID[:\s]*#?(\d+)',
                    ]
                    
                    match_id = None
                    for pattern in id_patterns:
                        match_id = re.search(pattern, result['tytul'], re.IGNORECASE)
                        if match_id:
                            break
                    
                    if match_id:
                        potential_id = match_id.group(1).strip()
                        if re.match(r'^\d+$', potential_id):
                            result['user_id'] = potential_id
                            logger.info(f"Found ID in pattern: {result['user_id']}")
                        else:
                            logger.warning(f"Found non-numeric ID pattern: {potential_id}")
                    else:
                        if re.match(r'^[\d\s]+$', result['tytul']):
                            clean_id = re.sub(r'\s+', '', result['tytul'])
                            if re.match(r'^\d+$', clean_id):
                                result['user_id'] = clean_id
                                logger.info(f"Found numeric title: {result['user_id']}")
                        else:
                            logger.warning(f"Title contains non-numeric characters: {result['tytul']}")
            
            sender_patterns = [
                r'nadawca:\s*([^,]+)',
                r'od\s*([^,]+?)(?:\s*,|\s*$)',
            ]
            
            match_sender = None
            for pattern in sender_patterns:
                match_sender = re.search(pattern, text, re.IGNORECASE)
                if match_sender:
                    break
            
            if match_sender:
                result['nadawca'] = match_sender.group(1).strip()
            
            date_patterns = [
                r'Data waluty:\s*([\d-]{10})',
                r'Data\s+waluty[:\s]+([\d-]{10})',
            ]
            
            match_date = None
            for pattern in date_patterns:
                match_date = re.search(pattern, text, re.IGNORECASE)
                if match_date:
                    break
            
            if match_date:
                result['data_waluty'] = match_date.group(1)
            
            balance_match = re.search(r'Stan\s+konta\s+po\s+operacji:\s*\+([\d\s]+,\d{2})\s+PLN', text, re.IGNORECASE)
            if balance_match:
                result['stan_konta'] = balance_match.group(1).replace(' ', '').replace(',', '.')
            
            if result['kwota_pln']:
                logger.info(f"Transfer: {result['kwota_pln']:.2f} PLN, UserID: {result['user_id']}, Title: {result['tytul']}")
                return result
            else:
                return None
            
        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return None

    def process_email(self, msg):
        try:
            subject = self.decode_email_header(msg.get('Subject', ''))
            from_ = self.decode_email_header(msg.get('From', ''))
            message_id = msg.get('Message-ID', '')
            
            logger.info(f"Analyzing: {subject} | From: {from_}")
            
            if not any(sender in from_ for sender in self.ALLOWED_SENDERS):
                logger.info(f"Skipping - not from PKO")
                return False
            
            if message_id and message_id in self.processed_message_ids:
                logger.info(f"Skipping - already processed")
                return False
            
            logger.info(f"PKO email detected")
            
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition', ''))
                    
                    if content_type == 'text/plain' and 'attachment' not in content_disposition:
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode('utf-8', errors='ignore')
                                break
                        except:
                            continue
                    elif content_type == 'text/html' and 'attachment' not in content_disposition:
                        try:
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode('utf-8', errors='ignore')
                        except:
                            continue
            else:
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode('utf-8', errors='ignore')
                except:
                    pass
            
            if not body:
                logger.warning("Empty email body")
                return False
            
            logger.info(f"Body length: {len(body)} chars")
            
            details = self.extract_transfer_details(body)
            
            if not details:
                logger.warning("No transfer data found")
                return False
            
            if not details['kwota_pln']:
                logger.warning("No amount found")
                return False
            
            if not details['user_id']:
                logger.warning(f"No user ID found - title: {details['tytul']}")
                return False
            
            logger.info(f"Transfer: {details['kwota_pln']:.2f} PLN | User: {details['user_id']} | Sender: {details['nadawca']}")
            
            success = self.add_coins_for_transfer(
                details['user_id'], 
                details['kwota_grosze'],
                details['tytul'],
                details['kwota_pln']
            )
            
            if success and message_id:
                self.processed_message_ids.add(message_id)
                if len(self.processed_message_ids) > 1000:
                    self.processed_message_ids = set(list(self.processed_message_ids)[-500:])
                logger.info(f"Transfer processed successfully")
                return True
            
            logger.warning(f"Failed to process transfer")
            return False
                
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return False

    def check_emails(self):
        try:
            mail = imaplib.IMAP4_SSL(self.IMAP_SERVER)
            mail.login(self.EMAIL, self.PASSWORD)
            mail.select('INBOX')
            
            status, messages = mail.search(None, 'UNSEEN')
            
            if status != 'OK' or not messages[0]:
                mail.close()
                mail.logout()
                return
            
            message_ids = messages[0].split()
            logger.info(f"Found {len(message_ids)} new email(s)")
            
            processed = 0
            skipped = 0
            errors = 0
            
            for idx, msg_id in enumerate(message_ids, 1):
                try:
                    logger.info(f"Processing email {idx}/{len(message_ids)} | ID: {msg_id.decode()}")
                    
                    status, msg_data = mail.fetch(msg_id, '(RFC822)')
                    if status != 'OK':
                        logger.error(f"Failed to fetch email")
                        errors += 1
                        continue
                    
                    msg = email.message_from_bytes(msg_data[0][1])
                    subject = self.decode_email_header(msg.get('Subject', ''))
                    from_ = self.decode_email_header(msg.get('From', ''))
                    date = msg.get('Date', '')
                    
                    logger.info(f"Subject: {subject}")
                    logger.info(f"From: {from_}")
                    logger.info(f"Date: {date}")
                    
                    result = self.process_email(msg)
                    
                    if result:
                        processed += 1
                    else:
                        skipped += 1
                    
                except Exception as e:
                    logger.error(f"Error processing email {idx}: {e}")
                    errors += 1
            
            logger.info(f"Summary: {processed} processed, {skipped} skipped, {errors} errors")
            
            mail.close()
            mail.logout()
            
        except Exception as e:
            logger.error(f"Error checking emails: {e}")

    def run(self):
        logger.info("Starting email monitor...")
        logger.info("Monitoring started (checking every 30s)")
        
        while self.running:
            try:
                self.check_emails()
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Stopping...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)
        
        logger.info("Monitor stopped")

    def add_coins_for_transfer(self, user_id, kwota_grosze, tytul, kwota_pln):
        if not user_id:
            return False
        
        coins_to_add = kwota_grosze * self.EXCHANGE_RATE
        
        logger.info(f"Adding {coins_to_add} coins for user {user_id} ({kwota_pln:.2f} PLN)")
        
        try:
            user = self.cache.get_user(user_id)
            user_name = None
            
            if not user:
                self.cache.set_user(
                    user_id=user_id,
                    name=f"User_{user_id}",
                    balance=coins_to_add,
                    level=1,
                    level_progress=0.0,
                    avatar="default-avatar.png",
                    background="default-bg.png"
                )
                user_name = f"User_{user_id}"
                logger.info(f"Created new user {user_id} with {coins_to_add} coins")
            else:
                new_balance = self.cache.update_balance(user_id, coins_to_add)
                user_name = user.get('name', f'User_{user_id}')
                logger.info(f"Updated user {user_id}: +{coins_to_add} coins (new balance: {new_balance})")
            
            try:
                exp_amount = coins_to_add / 10
                self.cache.add_experience(user_id, -exp_amount, None, None)
            except:
                pass
            
            try:
                from plugins.shop import ShopPlugin
                shop_plugin = ShopPlugin()
                shop_plugin.cache = self.cache
                shop_plugin.add_to_pool(kwota_pln)
            except:
                pass
            
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {user_id} | {user_name} | {kwota_pln:.2f} PLN | {coins_to_add} coins | {tytul}\n")
            except:
                pass
            
            self._send_confirmation(user_id, user_name, kwota_pln, coins_to_add, tytul)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding coins: {e}")
            return False

    def _load_background(self, user_id, width, height):
        bg_path = None
        
        if self.cache and user_id and hasattr(self.cache, "get_background_path"):
            bg_path = self.cache.get_background_path(user_id)
        
        if not bg_path or not os.path.exists(bg_path):
            bg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "backgrounds", "default-bg.png")
            if not os.path.exists(bg_path):
                return Image.new("RGB", (width, height), self.colors["bg"])
        
        try:
            bg = Image.open(bg_path).convert("RGB")
        except:
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

    def _render_text(self, text, size, color, stroke=0):
        from PIL import ImageFont
        try:
            font = ImageFont.truetype("arial.ttf", size)
        except:
            font = ImageFont.load_default()
        
        from PIL import ImageDraw as Draw
        temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        temp_draw = Draw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_img = Image.new('RGBA', (text_width + 10, text_height + 10), (0, 0, 0, 0))
        draw = Draw.Draw(text_img)
        
        shadow_color = (0, 0, 0, 180)
        draw.text((4, 4), text, font=font, fill=shadow_color)
        draw.text((2, 2), text, font=font, fill=shadow_color)
        draw.text((0, 0), text, font=font, fill=color)
        
        return text_img

    def _create_confirmation_image(self, user_id, user_name, kwota_pln, coins_added, tytul):
        try:
            width, height = 500, 500
            
            img = self._load_background(user_id, width, height)
            draw = ImageDraw.Draw(img)
            
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 130))
            img = Image.alpha_composite(img.convert("RGBA"), overlay)
            draw = ImageDraw.Draw(img)
            
            title = self._render_text("TRANSFER CONFIRMATION", 32, self.colors["gold"], stroke=3)
            img.paste(title, ((width - title.width) // 2, 20), title)
            
            draw.line([(40, 75), (width - 40, 75)], fill=self.colors["gold"], width=2)
            
            box_x1, box_x2 = 40, width - 40
            box_y1, box_y2 = 100, 430
            
            draw.rounded_rectangle(
                [box_x1, box_y1, box_x2, box_y2],
                radius=15,
                fill=(self.colors["panel"][0], self.colors["panel"][1], self.colors["panel"][2], 200),
                outline=self.colors["green"],
                width=2
            )
            
            y_pos = box_y1 + 25
            
            player_text = f"PLAYER: {user_name}"
            player_img = self._render_text(player_text, 22, self.colors["blue"], stroke=2)
            img.paste(player_img, ((width - player_img.width) // 2, y_pos), player_img)
            y_pos += 40
            
            id_text = f"ID: {user_id}"
            id_img = self._render_text(id_text, 20, self.colors["muted"], stroke=1)
            img.paste(id_img, ((width - id_img.width) // 2, y_pos), id_img)
            y_pos += 45
            
            draw.line([(box_x1 + 20, y_pos), (box_x2 - 20, y_pos)], fill=self.colors["line"], width=1)
            y_pos += 20
            
            amount_text = f"{kwota_pln:.2f} PLN"
            amount_img = self._render_text(amount_text, 36, self.colors["green"], stroke=3)
            img.paste(amount_img, ((width - amount_img.width) // 2, y_pos), amount_img)
            y_pos += 50
            
            coins_text = f"+ {coins_added} COINS"
            coins_img = self._render_text(coins_text, 28, self.colors["gold"], stroke=2)
            img.paste(coins_img, ((width - coins_img.width) // 2, y_pos), coins_img)
            y_pos += 50
            
            draw.line([(box_x1 + 20, y_pos), (box_x2 - 20, y_pos)], fill=self.colors["line"], width=1)
            y_pos += 20
            
            if len(tytul) > 40:
                tytul = tytul[:37] + "..."
            title_text = f"TITLE: {tytul}"
            title_img = self._render_text(title_text, 16, self.colors["muted"], stroke=1)
            img.paste(title_img, ((width - title_img.width) // 2, y_pos), title_img)
            y_pos += 30
            
            footer_text = "Thank you for your purchase!"
            footer_img = self._render_text(footer_text, 18, self.colors["gold"], stroke=1)
            img.paste(footer_img, ((width - footer_img.width) // 2, box_y2 - 25), footer_img)
            
            output_dir = self.temp_folder
            os.makedirs(output_dir, exist_ok=True)
            path = os.path.join(output_dir, f"confirm_{user_id}_{int(time.time() * 1000)}.png")
            img.convert("RGB").save(path, format="PNG", optimize=True)
            
            return path
            
        except Exception as e:
            logger.error(f"Error creating confirmation image: {e}")
            return None

    def _send_confirmation(self, user_id, user_name, kwota_pln, coins_added, tytul):
        if not self.file_queue:
            return
        
        try:
            image_path = self._create_confirmation_image(user_id, user_name, kwota_pln, coins_added, tytul)
            if image_path:
                self.file_queue.put(image_path)
                logger.info(f"Confirmation image sent for user {user_id}")
        except Exception as e:
            logger.error(f"Error sending confirmation: {e}")

    def stop(self):
        self.running = False
        logger.info("Monitor stopped")


def start_email_monitor(cache, command_queue=None, file_queue=None):
    monitor = EmailMonitor(cache, command_queue, file_queue)
    thread = threading.Thread(target=monitor.run, daemon=True)
    thread.start()
    logger.info("Email monitor started")
    return monitor