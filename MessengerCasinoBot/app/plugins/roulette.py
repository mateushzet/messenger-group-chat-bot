import random
import os
import time
from typing import Dict, Optional
from base_game_plugin import BaseGamePlugin
from logger import logger
from PIL import Image, ImageDraw, ImageFont

RED_NUMBERS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK_NUMBERS = set(range(1,37)) - RED_NUMBERS

class RoulettePlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="roulette"
        )
        
        self.history_colors = {
            "red": (207, 57, 64),
            "black": (68, 70, 72),
            "green": (0, 177, 64)
        }
        
        self.max_history = 13
        
    def get_custom_overlay(self, **kwargs) -> Optional[Dict]:
        try:
            anim_width = kwargs.get('width', 400)
            
            history = kwargs.get('history')
            if history is None:
                history = self.get_history()
            
            if not history:
                return None
            
            overlay_height = 30
            overlay = Image.new('RGBA', (anim_width, overlay_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            total_items = min(len(history), self.max_history)
            
            if total_items == 0:
                return None
            
            circle_diameter = 28
            spacing = 3
            
            available_width = anim_width - 20
            total_width_needed = (total_items * circle_diameter) + ((total_items - 1) * spacing)
            
            start_x = 10 + (available_width - total_width_needed) // 2
            circle_y = (overlay_height - circle_diameter) // 2
            
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 10)
            except:
                font = ImageFont.load_default()
            
            for i in range(total_items):
                item = history[i]
                number = item.get("number", 0)
                color_name = item.get("color", "green")
                
                color_rgb = self.history_colors.get(color_name, self.history_colors["green"])
                
                position_on_screen = total_items - 1 - i
                
                if position_on_screen < 5:
                    if position_on_screen == 0:
                        alpha = 100
                    elif position_on_screen == 1:
                        alpha = 160  
                    else:
                        alpha = 190
                else:
                    alpha = 255
                
                if item.get("timestamp", 0) == 0:
                    alpha = 0
                
                circle_color = color_rgb + (alpha,)
                
                circle_x = start_x + (position_on_screen * (circle_diameter + spacing))
                
                if alpha > 0 and (number > 0 or color_name == "green"):
                    draw.ellipse(
                        [(circle_x, circle_y), 
                        (circle_x + circle_diameter - 1, circle_y + circle_diameter - 1)],
                        fill=circle_color,
                        outline=(30, 30, 30, 150),
                        width=2
                    )
                    
                    number_text = str(number)
                    bbox = font.getbbox(number_text)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    
                    text_x = circle_x + (circle_diameter - text_width) // 2
                    text_y = circle_y + (circle_diameter - text_height) // 2 - 1
                    
                    text_alpha = min(alpha + 50, 255)
                    
                    draw.text(
                        (text_x + 1, text_y + 1),
                        number_text,
                        font=font,
                        fill=(0, 0, 0, text_alpha - 50)
                    )
                    draw.text(
                        (text_x, text_y),
                        number_text,
                        font=font,
                        fill=(255, 255, 255, text_alpha)
                    )
            
            return {
                'image': overlay,
                'position': (0, 10),
                'cache_key': f"roulette_history_{len(history)}",
                'per_frame': False
            }
            
        except Exception as e:
            logger.error(f"[Roulette] Error generating roulette history overlay: {e}")
            return None
    
    def _get_color_for_number(self, number):
        if number == 0:
            return "green"
        elif number in RED_NUMBERS:
            return "red"
        else:
            return "black"
    
    def add_to_history(self, result_number):
        if not hasattr(self, 'cache') or self.cache is None:
            logger.warning(f"[Roulette] Cache not available, skipping history for {result_number}")
            return
        
        result_color = self._get_color_for_number(result_number)
        
        history_key = "roulette_history"
        history = self.cache.get_setting(history_key, [])
        
        history.insert(0, {
            "number": result_number,
            "color": result_color,
            "timestamp": time.time()
        })
        
        if len(history) > self.max_history:
            history = history[:self.max_history]
        
        self.cache.set_setting(history_key, history)
    
    def get_history(self):
        if not hasattr(self, 'cache') or self.cache is None:
            return []
        
        history_key = "roulette_history"
        history = self.cache.get_setting(history_key, [])
        
        return history[:self.max_history]
    
    def calculate_win(self, bet_type, amount, result_number):
        result_color = "red" if result_number in RED_NUMBERS else "black" if result_number in BLACK_NUMBERS else "green"
        
        if bet_type.isdigit():
            if int(bet_type) == result_number:
                return amount * 36
        
        elif bet_type in ["red", "black"] and bet_type == result_color:
            return amount * 2
        elif bet_type in ["even", "odd"] and result_number != 0 and bet_type == ("even" if result_number % 2 == 0 else "odd"):
            return amount * 2
        elif bet_type == "high" and 19 <= result_number <= 36:
            return amount * 2
        elif bet_type == "low" and 1 <= result_number <= 18:
            return amount * 2
        elif bet_type == "green" and result_number == 0:
            return amount * 36
        elif bet_type == "1to12" and 1 <= result_number <= 12:
            return amount * 3
        elif bet_type == "13to24" and 13 <= result_number <= 24:
            return amount * 3
        elif bet_type == "25to36" and 25 <= result_number <= 36:
            return amount * 3
        elif bet_type == "1st" and result_number % 3 == 1 and result_number != 0:
            return amount * 3
        elif bet_type == "2nd" and result_number % 3 == 2 and result_number != 0:
            return amount * 3
        elif bet_type == "3rd" and result_number % 3 == 0 and result_number != 0:
            return amount * 3
        
        return 0

    def validate_bet(self, bet_type, amount_str):
        try:
            try:
                amount = int(amount_str)
                if amount <= 0:
                    return "Amount must be a positive whole number"
                if not amount_str.isdigit():
                    return "Amount must be a whole number (no decimals)"
            except ValueError:
                return "Invalid amount - must be a whole number"
            
            valid_bets = [str(n) for n in range(37)] + ["red","black","even","odd","high","low","green",
                    "1to12","13to24","25to36","1st","2nd","3rd"]
            
            bet_lower = bet_type.lower()
            if bet_lower not in valid_bets:
                return f"Invalid bet type: {bet_type}\n\nValid bets: 0-36, red, black, green, even, odd, high, low\n1to12, 13to24, 25to36, 1st, 2nd, 3rd"
            
            return None
        except Exception as e:
            logger.error(f"[Roulette] Error validating bet: {e}")
            return f"Validation error: {e}"

    def get_base_animation_path(self, result_number):
        animation_variant = random.randint(1, 4)
        base_path = os.path.join(self.get_asset_path("roulette", "roulette_results"), f"result_{result_number}_{animation_variant}.webp")
        
        if not os.path.exists(base_path):
            logger.error(f"[Roulette] Animation file not found: {base_path}")
            return None
        
        return base_path

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache

        if len(args) == 0:
            help_image_path = self.get_asset_path("roulette", "roulette_help.png")
            try:
                with Image.open(help_image_path) as img:
                    img_width, img_height = img.size
            except:
                img_width, img_height = 400, 400
            
            overlay_data = self.get_custom_overlay(
                width=img_width,
                height=img_height,
               history=self.get_history()
            )
            
            if overlay_data and overlay_data['image']:
                help_img = Image.open(help_image_path).convert("RGBA")
                overlay_img = overlay_data['image']
                
                position = (0, 10)
                help_img.paste(overlay_img, position, overlay_img)
                
                temp_path = os.path.join(self.get_asset_path("temp"), f"roulette_help_with_history_{int(time.time())}.png")
                help_img.save(temp_path, "PNG")
                
                try:
                    file_queue.put(temp_path)
                except Exception as e:
                    logger.error(f"[Roulette] Error sending help image: {e}")
                    self.send_message_image(sender, file_queue, 
                        "Error sending help image!", "Roulette - Error", cache, None)
            else:
                try:
                    file_queue.put(help_image_path)
                except Exception as e:
                    logger.error(f"[Roulette] Error sending help image: {e}")
                    self.send_message_image(sender, file_queue, 
                        "Error sending help image!", "Roulette - Error", cache, None)
            return None

        animated = True
        if len(args) >= 3 and args[-1].lower() == "x":
            animated = False
            args = args[:-1]

        if len(args) < 2:
            self.send_message_image(sender, file_queue, 
                "Usage: /roulette <amount> <bet_type>\n\n"
                "For full bet list, use: /roulette",
                "Roulette - Invalid Usage", cache, None)
            return None

        try:
            amount_str = args[0]
            bet_type = args[1].lower()
            
            error = self.validate_bet(bet_type, amount_str)
            if error:
                self.send_message_image(sender, file_queue, 
                    f"{error}\n\nUse /roulette for full bet list",
                    "Roulette - Invalid Bet", cache, None)
                return None
            
            try:
                amount = int(amount_str)
                if amount <= 0:
                    self.send_message_image(sender, file_queue,
                        "Amount must be greater than 0!",
                        "Roulette - Invalid Amount", cache, None)
                    return None
            except ValueError:
                self.send_message_image(sender, file_queue,
                    "Invalid amount format! Use numbers",
                    "Roulette - Invalid Amount", cache, None)
                return None
            
        except (ValueError, IndexError):
            self.send_message_image(sender, file_queue, 
                "Invalid arguments!\n\n"
                "Use: /roulette <amount> <bet_type>\n\n"
                "Example: /roulette 10 red\n"
                "Roulette - Error", cache, None)
            return None

        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, amount)
        if error:
            if error == "Invalid user":
                self.send_message_image(sender, file_queue, "Invalid user!", "Roulette - Validation Error", cache, None)
            else:
                balance = user.get('balance', 0) if user else 0
                self.send_message_image(sender, file_queue, 
                    f"Insufficient funds!\n\n"
                    f"You need: ${amount}\n"
                    f"Your balance: ${balance}", 
                    "Roulette - Insufficient Funds", cache, user_id)
            return None

        balance_before = user["balance"] - amount

        result_number = random.randint(0, 36)
        result_color = self._get_color_for_number(result_number)
        win = self.calculate_win(bet_type, amount, result_number)
        new_balance = balance_before + win
        
        try:
            self.update_user_balance(user_id, new_balance)
        except Exception as e:
            logger.error(f"[Roulette] Error updating balance for user {user_id}: {e}")
            self.send_message_image(sender, file_queue, 
                "Error updating balance!\n\n"
                "Please try again or contact support.", 
                "Roulette - System Error", cache, user_id)
            return None

        net_win = win - amount
        
        user_info_before = self.create_user_info(sender, amount, 0, balance_before, user.copy())
        
        try:
            exp_amount = net_win if net_win > 0 else -amount
            newLevel, newLevelProgress = self.cache.add_experience(user_id, exp_amount, sender, file_queue)
        except Exception as e:
            logger.error(f"[Roulette] Error adding experience: {e}")
            newLevel = user.get("level", 1)
            newLevelProgress = user.get("level_progress", 0.1)

        base_animation_path = self.get_base_animation_path(result_number)
        if not base_animation_path:
            self.send_message_image(sender, file_queue, 
                f"Animation for number {result_number} not found!\n\n"
                f"Technical issue - please try again later.", 
                "Roulette - Animation Error", cache, user_id)
            return None
        
        user["level"] = newLevel
        user["level_progress"] = newLevelProgress
        user_info_after = self.create_user_info(sender, amount, net_win, new_balance, user)

        result_path, error = self.generate_animation(
            base_animation_path=base_animation_path,
            user_id=user_id,
            user=user,
            user_info_before=user_info_before,
            user_info_after=user_info_after,
            game_type="roulette",
            animated=animated,
            frame_duration=75,
            last_frame_multiplier=30.0,
            custom_overlay_kwargs={
                'width': 400,
                'height': 400,
                'history': self.get_history()
            },
            show_win_text=True,
            font_scale=1.2,
            avatar_size=90
        )
        
        self.add_to_history(result_number)
        
        if error or not result_path:
            logger.error(f"[Roulette] Animation generation error: {error}")
            self.send_message_image(sender, file_queue, 
                f"Error generating animation!\n\n"
                f"Error: {error}\n"
                f"Please try again later.", 
                "Roulette - Animation Error", cache, user_id)
            return None

        try:
            file_queue.put(result_path)
        except Exception as e:
            logger.error(f"[Roulette] Error putting file to queue: {e}")
            self.send_message_image(sender, file_queue, 
                "Error sending animation!\n\n"
                "Please try again.", 
                "Roulette - System Error", cache, user_id)
            return None
        
        if net_win > 0:
            win_str = f"+{net_win}"
        else:
            win_str = f"{net_win}"
        
        logger.info(f"ROULETTE: {sender} bet {amount} on {bet_type} | "
                   f"Result: {result_number} {result_color} | "
                   f"Net: {win_str} | Balance: {balance_before} -> {new_balance}")
        
        return None

def register():
    plugin = RoulettePlugin()
    return {
        "name": "roulette",
        "aliases": ["/r"],
        "description": "Roulette game - bet on numbers, colors, dozens or columns\n"
                      "Bet types: 0-36, red, black, green, even, odd, high, low\n"
                      "1to12, 13to24, 25to36, 1st, 2nd, 3rd\n"
                      "Use: /roulette <amount> <bet_type>",
        "execute": plugin.execute_game
    }