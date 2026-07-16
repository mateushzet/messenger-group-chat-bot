import os
import time
import configparser
from PIL import Image, ImageDraw
from base_game_plugin import BaseGamePlugin
from logger import logger


class ShopPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="shop")
        self.assets_folder = self.get_asset_path("shop")
        
        self.BLIK_NUMBER = ConfigReader.get_gemini_api_key();
        
        self.MIN_EXCHANGE_RATE = 1000
        
        self.POOL_SETTING_KEY = "shop_withdrawal_pool"
        
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

    def get_withdrawal_pool(self):
        pool = self.cache.get_setting(self.POOL_SETTING_KEY, {})
        if not isinstance(pool, dict) or not pool:
            pool = {
                "total_pln": 0.0,
                "claimed_pln": 0.0,
                "available_pln": 0.0,
                "last_withdrawal": None,
                "withdrawal_history": []
            }
            self.cache.set_setting(self.POOL_SETTING_KEY, pool)
        else:
            if "available_pln" not in pool:
                pool["available_pln"] = pool.get("total_pln", 0.0) - pool.get("claimed_pln", 0.0)
            if "withdrawal_history" not in pool:
                pool["withdrawal_history"] = []
            if "last_withdrawal" not in pool:
                pool["last_withdrawal"] = None
            
            self.save_withdrawal_pool(pool)
        
        return pool

    def save_withdrawal_pool(self, pool):
        pool["available_pln"] = pool.get("total_pln", 0.0) - pool.get("claimed_pln", 0.0)
        self.cache.set_setting(self.POOL_SETTING_KEY, pool)

    def add_to_pool(self, pln_amount):
        pool = self.get_withdrawal_pool()
        half_pln = pln_amount / 2.0
        
        pool["total_pln"] += half_pln
        
        self.save_withdrawal_pool(pool)
        logger.info(f"[Shop] Added to pool: {half_pln:.2f} PLN")
        return pool

    def calculate_withdrawal_rate(self):
        pool = self.get_withdrawal_pool()
        available_pln = pool.get("available_pln", 0.0)
        total_coins = self.get_total_coins_in_economy()
        
        if total_coins <= 0 or available_pln <= 0:
            return self.MIN_EXCHANGE_RATE
        
        rate = total_coins / available_pln
        return max(rate, self.MIN_EXCHANGE_RATE)

    def get_pool_info(self):
        pool = self.get_withdrawal_pool()
        rate = self.calculate_withdrawal_rate()
        
        return {
            "total_pln": pool.get("total_pln", 0.0),
            "claimed_pln": pool.get("claimed_pln", 0.0),
            "available_pln": pool.get("available_pln", 0.0),
            "rate": rate,
            "min_rate": self.MIN_EXCHANGE_RATE
        }

    def get_total_coins_in_economy(self):
        if not self.cache or not hasattr(self.cache, 'users'):
            return 0
        
        total_coins = 0
        
        for user_id, user_data in self.cache.users.items():
            if isinstance(user_data, dict):
                balance = user_data.get('balance', 0)
                total_coins += balance
        
        try:
            case_battles = self.cache.get_setting('case_battles', {})
            if case_battles:
                locked_coins = 0
                for battle_id_str, battle in case_battles.items():
                    if battle.get('status') == 'waiting':
                        case_price = battle.get('case_price', 0)
                        locked_coins += case_price
                total_coins += locked_coins
        except Exception as e:
            logger.error(f"[Shop] Error getting case battles: {e}")
        
        try:
            active_jackpot = self.cache.get_setting('active_jackpot', None)
            if active_jackpot:
                status = active_jackpot.get('status', '')
                if status in ['waiting', 'counting_down']:
                    total_pot = active_jackpot.get('total_pot', 0)
                    total_coins += total_pot
        except Exception as e:
            logger.error(f"[Shop] Error getting active jackpot: {e}")
        
        try:
            active_mines = self.cache.get_setting('active_mines_games', {})
            if active_mines:
                for user_id_str, game_data in active_mines.items():
                    bet = game_data.get('bet', 0)
                    total_coins += bet
        except Exception as e:
            logger.error(f"[Shop] Error getting active Mines games: {e}")
        
        try:
            if hasattr(self.cache, 'games'):
                for user_id_str, game_states in self.cache.games.items():
                    if 'snakes' in game_states:
                        snake_data = game_states.get('snakes', {})
                        if isinstance(snake_data, dict):
                            meta = snake_data.get('meta', {})
                            bet = meta.get('bet', 0)
                            if bet > 0:
                                total_coins += bet
        except Exception as e:
            logger.error(f"[Shop] Error getting active Snakes games: {e}")
        
        return total_coins

    def _format_number(self, num):
        return f"{num:,}".replace(",", " ")

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        
        if error:
            self.send_message_image(
                sender, 
                file_queue, 
                "Player not found.", 
                "SHOP", 
                cache, 
                None
            )
            return ""
        
        user_id_str = str(user_id)
        user_name = user.get('name', sender)
        
        if args and args[0].lower() in ["withdraw", "wyplac", "w"]:
            self._handle_withdraw(user_id_str, user_name, args, file_queue)
            return ""
        
        if args and args[0].lower() in ["pool", "pula", "p"]:
            self._show_pool_status(user_id_str, user_name, file_queue)
            return ""
        
        image_path = self._create_shop_image(user_id_str, user_name)
        
        if image_path:
            file_queue.put(image_path)
        else:
            self.send_message_image(
                sender,
                file_queue,
                "Error creating shop image.",
                "SHOP",
                cache,
                user_id
            )
        
        return ""

    def _handle_withdraw(self, user_id, user_name, args, file_queue):
        try:
            if len(args) < 2:
                pool_info = self.get_pool_info()
                total_coins = self.get_total_coins_in_economy()
                message = (
                    f"WITHDRAWAL\n"
                    f"---------\n"
                    f"Available: {pool_info['available_pln']:.2f} PLN\n"
                    f"Total coins in economy: {self._format_number(total_coins)}\n"
                    f"Rate: {pool_info['rate']:.0f} coins per 1 PLN\n"
                    f"Minimum rate: {pool_info['min_rate']} coins per 1 PLN\n\n"
                    f"Use: /shop withdraw [amount_PLN]\n"
                    f"e.g. /shop withdraw 5"
                )
                self.send_message_image(
                    user_name,
                    file_queue,
                    message,
                    "WITHDRAWAL",
                    self.cache,
                    user_id
                )
                return
            
            try:
                pln_amount = float(args[1].replace(',', '.'))
            except ValueError:
                self.send_message_image(
                    user_name,
                    file_queue,
                    "Please enter a valid amount in PLN.",
                    "WITHDRAWAL",
                    self.cache,
                    user_id
                )
                return
            
            if pln_amount <= 0:
                self.send_message_image(
                    user_name,
                    file_queue,
                    "Amount must be greater than 0.",
                    "WITHDRAWAL",
                    self.cache,
                    user_id
                )
                return
            
            pool = self.get_withdrawal_pool()
            rate = self.calculate_withdrawal_rate()
            total_coins = self.get_total_coins_in_economy()
            
            available_pln = pool.get("available_pln", 0.0)
            
            if pln_amount > available_pln:
                self.send_message_image(
                    user_name,
                    file_queue,
                    f"Insufficient funds in pool.\n"
                    f"Available: {available_pln:.2f} PLN\n"
                    f"Requested: {pln_amount:.2f} PLN",
                    "WITHDRAWAL",
                    self.cache,
                    user_id
                )
                return
            
            coins_needed = pln_amount * rate
            coins_needed_int = int(coins_needed) + 1
            
            user = self.cache.get_user(user_id)
            if not user:
                self.send_message_image(
                    user_name,
                    file_queue,
                    "Player not found.",
                    "WITHDRAWAL",
                    self.cache,
                    user_id
                )
                return
            
            current_balance = user.get('balance', 0)
            
            if current_balance < coins_needed_int:
                self.send_message_image(
                    user_name,
                    file_queue,
                    f"Insufficient coins.\n"
                    f"Need: {coins_needed_int} coins\n"
                    f"Your balance: {current_balance} coins\n"
                    f"Rate: {rate:.0f} coins/PLN",
                    "WITHDRAWAL",
                    self.cache,
                    user_id
                )
                return
            
            new_balance = self.cache.update_balance(user_id, -coins_needed_int)
            
            pool["claimed_pln"] = pool.get("claimed_pln", 0.0) + pln_amount
            self.save_withdrawal_pool(pool)
            
            if "withdrawal_history" not in pool:
                pool["withdrawal_history"] = []
            
            pool["withdrawal_history"].append({
                "user_id": user_id,
                "user_name": user_name,
                "pln": pln_amount,
                "coins": coins_needed_int,
                "rate": rate,
                "timestamp": time.time()
            })
            
            if len(pool["withdrawal_history"]) > 100:
                pool["withdrawal_history"] = pool["withdrawal_history"][-100:]
            
            pool["last_withdrawal"] = {
                "user_id": user_id,
                "user_name": user_name,
                "pln": pln_amount,
                "coins": coins_needed_int,
                "rate": rate,
                "timestamp": time.time()
            }
            
            self.save_withdrawal_pool(pool)
            
            logger.info(f"[Shop] Withdrawal: {user_name} ({user_id}) - {pln_amount:.2f} PLN for {coins_needed_int} coins (rate: {rate:.0f})")
            
            remaining_pln = pool["available_pln"]
            new_total_coins = self.get_total_coins_in_economy()
            
            message = (
                f"WITHDRAWAL SUCCESSFUL!\n"
                f"----------------------\n"
                f"Amount: {pln_amount:.2f} PLN\n"
                f"Paid: {coins_needed_int} coins\n"
                f"Rate: {rate:.0f} coins/PLN\n"
                f"\n"
                f"Remaining in pool: {remaining_pln:.2f} PLN\n"
                f"Your new balance: {new_balance} coins\n"
                f"Total coins in economy: {self._format_number(new_total_coins)}"
            )
            
            self.send_message_image(
                user_name,
                file_queue,
                message,
                "WITHDRAWAL",
                self.cache,
                user_id
            )
            
        except Exception as e:
            logger.error(f"[Shop] Withdrawal error: {e}", exc_info=True)
            self.send_message_image(
                user_name,
                file_queue,
                f"Error: {e}",
                "WITHDRAWAL",
                self.cache,
                user_id
            )

    def _show_pool_status(self, user_id, user_name, file_queue):
        pool_info = self.get_pool_info()
        total_coins = self.get_total_coins_in_economy()
        
        message = (
            f"WITHDRAWAL POOL STATUS\n"
            f"----------------------\n"
            f"Total pool: {pool_info['total_pln']:.2f} PLN\n"
            f"Claimed: {pool_info['claimed_pln']:.2f} PLN\n"
            f"Available: {pool_info['available_pln']:.2f} PLN\n"
            f"\n"
            f"Total coins in economy: {self._format_number(total_coins)}\n"
            f"\n"
            f"Current rate: {pool_info['rate']:.0f} coins/PLN\n"
            f"Minimum rate: {pool_info['min_rate']} coins/PLN"
        )
        
        self.send_message_image(
            user_name,
            file_queue,
            message,
            "POOL STATUS",
            self.cache,
            user_id
        )

    def _create_shop_image(self, user_id, user_name):
        try:
            width, height = 600, 650
            img = self._load_background(user_id, width, height)
            draw = ImageDraw.Draw(img)
            
            overlay = Image.new("RGBA", (width, height), (0, 0, 0, 130))
            img = Image.alpha_composite(img.convert("RGBA"), overlay)
            draw = ImageDraw.Draw(img)
            
            title = self._render_text(
                "COIN SHOP", 
                38, 
                self.colors["gold"],
                stroke=3
            )
            img.paste(title, ((width - title.width) // 2, 20), title)
            
            draw.line([(40, 75), (width - 40, 75)], fill=self.colors["gold"], width=2)
            
            info_y = 110
            
            box_x1 = 40
            box_x2 = width - 40
            box_y1 = info_y
            box_y2 = info_y + 180
            
            draw.rounded_rectangle(
                [box_x1, box_y1, box_x2, box_y2],
                radius=15,
                fill=(self.colors["panel"][0], self.colors["panel"][1], self.colors["panel"][2], 200),
                outline=self.colors["gold"],
                width=2
            )
            
            line1 = "Send a BLIK transfer to:"
            line1_img = self._render_text(line1, 22, self.colors["text"], stroke=1)
            img.paste(line1_img, ((width - line1_img.width) // 2, box_y1 + 15), line1_img)
            
            blik_img = self._render_text(
                self.BLIK_NUMBER, 
                40, 
                self.colors["pink"],
                stroke=3
            )
            img.paste(blik_img, ((width - blik_img.width) // 2, box_y1 + 45), blik_img)
            
            line2 = "In the TRANSFER TITLE enter your ID:"
            line2_img = self._render_text(line2, 22, self.colors["text"], stroke=1)
            img.paste(line2_img, ((width - line2_img.width) // 2, box_y1 + 95), line2_img)
            
            id_big_img = self._render_text(
                f">>> {user_id} <<<", 
                36, 
                self.colors["green"],
                stroke=3
            )
            img.paste(id_big_img, ((width - id_big_img.width) // 2, box_y1 + 125), id_big_img)
            
            rate_y = box_y2 + 25
            
            rate_box_y1 = rate_y
            rate_box_y2 = rate_y + 70
            
            draw.rounded_rectangle(
                [box_x1, rate_box_y1, box_x2, rate_box_y2],
                radius=15,
                fill=(self.colors["panel"][0], self.colors["panel"][1], self.colors["panel"][2], 200),
                outline=self.colors["orange"],
                width=2
            )
            
            rate_text = f"1 PLN = {self.MIN_EXCHANGE_RATE} COINS"
            rate_img = self._render_text(rate_text, 28, self.colors["orange"], stroke=2)
            img.paste(rate_img, ((width - rate_img.width) // 2, rate_box_y1 + 20), rate_img)
            
            pool_y = rate_box_y2 + 25
            
            pool_box_y1 = pool_y
            pool_box_y2 = pool_y + 180
            
            draw.rounded_rectangle(
                [box_x1, pool_box_y1, box_x2, pool_box_y2],
                radius=15,
                fill=(self.colors["panel"][0], self.colors["panel"][1], self.colors["panel"][2], 200),
                outline=self.colors["green"],
                width=2
            )
            
            pool_line1 = "50% OF AMOUNT GOES TO WITHDRAWAL POOL"
            pool_line1_img = self._render_text(pool_line1, 22, self.colors["green"], stroke=2)
            img.paste(pool_line1_img, ((width - pool_line1_img.width) // 2, pool_box_y1 + 8), pool_line1_img)
            
            pool_line2 = "ANYONE CAN WITHDRAW IT"
            pool_line2_img = self._render_text(pool_line2, 20, self.colors["gold"], stroke=2)
            img.paste(pool_line2_img, ((width - pool_line2_img.width) // 2, pool_box_y1 + 38), pool_line2_img)
            
            pool_info = self.get_pool_info()
            
            pool_status = f"Available: {pool_info['available_pln']:.2f} PLN"
            pool_status_img = self._render_text(pool_status, 20, self.colors["muted"], stroke=1)
            img.paste(pool_status_img, ((width - pool_status_img.width) // 2, pool_box_y1 + 72), pool_status_img)
            
            pool_rate = f"Withdrawal rate: {pool_info['rate']:.0f} coins/PLN"
            pool_rate_img = self._render_text(pool_rate, 18, self.colors["blue"], stroke=1)
            img.paste(pool_rate_img, ((width - pool_rate_img.width) // 2, pool_box_y1 + 100), pool_rate_img)
            
            pool_cmds1 = "/shop pool - status"
            pool_cmds1_img = self._render_text(pool_cmds1, 16, self.colors["muted"], stroke=1)
            img.paste(pool_cmds1_img, ((width - pool_cmds1_img.width) // 2, pool_box_y1 + 128), pool_cmds1_img)
            
            pool_cmds2 = "/shop withdraw [amount] - withdraw"
            pool_cmds2_img = self._render_text(pool_cmds2, 16, self.colors["muted"], stroke=1)
            img.paste(pool_cmds2_img, ((width - pool_cmds2_img.width) // 2, pool_box_y1 + 148), pool_cmds2_img)
            
            footer_y = pool_box_y2 + 15
            footer_text = "Coins are added automatically after receiving the transfer"
            footer_img = self._render_text(footer_text, 16, self.colors["muted"], stroke=1)
            img.paste(footer_img, ((width - footer_img.width) // 2, footer_y), footer_img)
            
            output_dir = self.get_app_path("temp", "shop")
            os.makedirs(output_dir, exist_ok=True)
            path = os.path.join(output_dir, f"shop_{user_id}_{int(time.time() * 1000)}.png")
            img.convert("RGB").save(path, format="PNG", optimize=True)
            
            return path
            
        except Exception as e:
            logger.error(f"[Shop] Error creating shop image: {e}", exc_info=True)
            return None

    def _load_background(self, user_id, width, height):
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

    def _render_text(self, text, size, color, stroke=0):
        return self.text_renderer.render_text(
            text=text,
            font_size=size,
            color=color,
            stroke_width=stroke,
            stroke_color=(0, 0, 0, 255),
            shadow=stroke > 0,
            shadow_offset=(2, 2),
        )


def register():
    plugin = ShopPlugin()
    logger.info("[Shop] Shop plugin registered")
    return {
        "name": "shop",
        "aliases": ["/shop", "/sklep", "/store"],
        "description": "Coin Shop\n\n"
        "/shop - show shop information\n"
        "/shop pool - show withdrawal pool status\n"
        "/shop withdraw [amount] - withdraw money\n\n"
        "BLIK transfer to: 794 185 598\n"
        "Put your ID in the transfer title\n"
        "1 PLN = 1000 coins (BLIK purchase)\n"
        "50% goes to the withdrawal pool",
        "execute": plugin.execute_game,
    }

class ConfigReader:
    
    @staticmethod
    def get_gemini_api_key():
        try:
            app_path = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(app_path)))
            config_path = os.path.join(base_dir, 'MessengerCasinoBot', 'app', 'config', 'config.ini')
            
            logger.info(f"[Shop] Reading config from: {config_path}")
            
            if not os.path.exists(config_path):
                logger.error(f"[Shop] Config file not found")
                return None
            
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')
            
            if config.has_section('blik') and config.has_option('blik', 'phone_number'):
                blik_phone_number = config.get('blik', 'phone_number').strip()
                if blik_phone_number:
                    logger.info(f"[Shop] Found Blik phone number ({blik_phone_number})")
                    return blik_phone_number
                
            return None
                
        except Exception as e:
            logger.error(f"[Shop] Error reading config file: {e}")
            return None