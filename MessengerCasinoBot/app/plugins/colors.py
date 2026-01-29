import random
import os
import time
from base_game_plugin import BaseGamePlugin
from logger import logger
from PIL import Image, ImageDraw, ImageFont

class ColorsPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="colors"
        )
        
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

        self.history_colors = {
            "black": (68, 70, 72),
            "red": (207, 57, 64),
            "blue": (53, 172, 254),
            "gold": (255, 204, 48)
        }
        
        self.max_history = 25

        self._overlay_cache = {}
    
    def get_custom_overlay(self, **kwargs):
        try:
            frame_index = kwargs.get('frame_index', 0)
            total_frames = kwargs.get('total_frames', 1)
            result_color = kwargs.get('result_color', 'black')
            frame_width = kwargs.get('frame_width', 400)
            
            available_width = frame_width - 50
            section_width = min(int(available_width * 0.9), 350)
            
            history_height = 40
            multipliers_height = 40
            total_height = history_height + multipliers_height + 30
            
            overlay_image = Image.new('RGBA', (frame_width, total_height), (0, 0, 0, 0))
            
            history = self.get_history()

            history_to_display = history[:self.max_history]
            
            history_overlay = self._generate_history_overlay(
                width=section_width, 
                height=history_height,
                history=history_to_display,
                show_current=(frame_index == total_frames - 1 and result_color is not None)
            )
            
            multipliers_overlay = self._create_multipliers_overlay(section_width, multipliers_height)
            
            section_x = (frame_width - section_width) // 2
            history_y = 10
            multipliers_y = history_y + history_height + 15
            
            if history_overlay:
                overlay_image.alpha_composite(history_overlay, (section_x, history_y))
            
            if multipliers_overlay:
                overlay_image.alpha_composite(multipliers_overlay, (section_x, multipliers_y))

            overlay_position_y = 170
            
            overlay_data = {
                'image': overlay_image,
                'position': (0, overlay_position_y),
                'per_frame': False
            }
            
            return overlay_data
            
        except Exception as e:
            logger.error(f"[Colors] Error in get_custom_overlay: {e}")
            return None
    
    def _generate_history_overlay(self, width=350, height=40, history=None, show_current=False):
        try:
            if not history:
                history = []
            
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            total_items = min(len(history), self.max_history)
            if total_items == 0:
                return overlay
            
            bar_width = 10
            spacing = 2
            bar_height = 30
            
            total_width_needed = (total_items * bar_width) + ((total_items - 1) * spacing)
            start_x = (width - total_width_needed) // 2
            bar_y_start = (height - bar_height) // 2

            if start_x < 0 or total_width_needed > width:
                max_items = width // (bar_width + spacing)
                if max_items < total_items:
                    total_items = max_items
                    history = history[:total_items]
                    total_width_needed = (total_items * bar_width) + ((total_items - 1) * spacing)
                    start_x = (width - total_width_needed) // 2

            for i in range(total_items):
                history_index = total_items - 1 - i
                screen_position = i
                
                if history_index < len(history):
                    item = history[history_index]
                    color_name = item.get("color", "black")
                    timestamp = item.get("timestamp", 0)
                    
                    is_current = (history_index == 0) and show_current and timestamp > time.time() - 2
                    
                    if is_current:
                        alpha = 255
                        highlight_color = (255, 255, 255, 100)
                        highlight_x_start = start_x + (screen_position * (bar_width + spacing)) - 1
                        highlight_x_end = highlight_x_start + bar_width + 2
                        draw.rectangle([(highlight_x_start, bar_y_start - 1), 
                                      (highlight_x_end, bar_y_start + bar_height)], 
                                      fill=highlight_color)
                    else:
                        fade_factor = (screen_position / total_items) if total_items > 0 else 0
                        alpha = int(255 * (0.3 + (fade_factor * 0.7)))
                        if alpha > 255:
                            alpha = 255
                else:
                    color_name = "black"
                    alpha = 100
                
                color_rgb = self.history_colors.get(color_name, self.history_colors["black"])
                bar_color = color_rgb + (alpha,)
                
                x_start = start_x + (screen_position * (bar_width + spacing))
                x_end = x_start + bar_width
                draw.rectangle([(x_start, bar_y_start), (x_end - 1, bar_y_start + bar_height - 1)], 
                              fill=bar_color)
            
            return overlay
            
        except Exception as e:
            logger.error(f"[Colors] Error generating history overlay: {e}")
            return None
    
    def _create_multipliers_overlay(self, width, height):
        try:
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            
            if not hasattr(self, 'text_renderer'):
                from text_renderer import CachedTextRenderer
                self.text_renderer = CachedTextRenderer()
            
            colors_info = [
                ("black", self.multipliers["black"]),
                ("red", self.multipliers["red"]),
                ("blue", self.multipliers["blue"]),
                ("gold", self.multipliers["gold"])
            ]
            
            text_images = []
            total_width = 0
            
            for color_key, multiplier in colors_info:
                text = f"x{multiplier}"
                color = self.history_colors[color_key]
                
                text_img = self.text_renderer.render_text_to_image(
                    text=text,
                    font_path="DejaVuSans-Bold.ttf",
                    font_size=24,
                    color=color + (255,),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255),
                    shadow=True,
                    shadow_color=(0, 0, 0, 180),
                    shadow_offset=(1, 1)
                )
                
                text_images.append({
                    "image": text_img,
                    "width": text_img.width,
                    "height": text_img.height
                })
                total_width += text_img.width
            
            spacing = 30
            total_width_needed = total_width + (len(text_images) - 1) * spacing
            
            if total_width_needed > width:
                spacing = max(10, (width - total_width) // (len(text_images) - 1))
                total_width_needed = total_width + (len(text_images) - 1) * spacing
            
            x_start = (width - total_width_needed) // 2
            y = (height - 24) // 2
            
            for item in text_images:
                text_img = item["image"]
                text_y = y + (24 - item["height"]) // 2 if item["height"] < 24 else y
                
                overlay.alpha_composite(text_img, (x_start, text_y))
                x_start += item["width"] + spacing
            
            return overlay
            
        except Exception as e:
            logger.error(f"[Colors] Error creating multipliers overlay: {e}")
            return None
        
    def get_color_at_position(self, position):
        if 0 <= position < len(self.color_order):
            color_number = self.color_order[position]
            return self.color_map[color_number]
        return "black"
        
    def calculate_win(self, bet_type, bets, amount, result_position):
        result_color = self.get_color_at_position(result_position)
        
        if bet_type == "single":
            bet_color = bets[0]
            if bet_color == result_color:
                return amount * self.multipliers[result_color]
            return 0
        
        elif bet_type == "multiple":
            colors = ["black", "red", "blue", "gold"]
            total_payout = 0
            
            for i, bet_amount in enumerate(bets):
                if colors[i] == result_color and bet_amount > 0:
                    total_payout += bet_amount * self.multipliers[result_color]
            
            return total_payout
        
        return 0
 
    def validate_bet(self, bet_type, amount_str, bets=None):
        try:
            valid_colors = ["black", "red", "blue", "gold"]
            
            if bet_type == "single":
                if bets[0] not in valid_colors:
                    return f"Invalid color. Valid: {', '.join(valid_colors)}"
                
                try:
                    amount = int(amount_str)
                    if amount <= 0:
                        return "Amount must be positive"
                except ValueError:
                    return "Amount must be a number"
                
                return None
                
            elif bet_type == "multiple":
                total_bet = 0
                for bet in bets:
                    if bet < 0:
                        return "All bets must be non-negative"
                    total_bet += bet
                
                if total_bet <= 0:
                    return "Total bet must be positive"
                
                return None
            
            return "Invalid bet type"
            
        except Exception as e:
            logger.error(f"[Colors] Error validating bet: {e}")
            return f"Validation error: {e}"
    
    def get_base_animation_path(self, result_position, result_color):
        animation_variant = random.randint(0, 2)
        base_path = os.path.join(
            self.get_asset_path("colors", "colors_results"), 
            f"colors_wheel_{result_color}_{result_position}_{animation_variant}.webp"
        )
        
        if not os.path.exists(base_path):
            logger.error(f"[Colors] Animation file not found: {base_path}")
            return None
        
        return base_path
    
    def get_history(self):
        if not hasattr(self, 'cache') or self.cache is None:
            return []
        
        history_key = "colors_history"
        history = self.cache.get_setting(history_key, [])
        
        return history[:self.max_history]
    
    def add_to_history(self, result_color, result_position):
        if not hasattr(self, 'cache') or self.cache is None:
            logger.warning(f"[Colors] Cache not available, skipping history")
            return
        
        history_key = "colors_history"
        history = self.cache.get_setting(history_key, [])
        
        history.insert(0, {
            "color": result_color,
            "position": result_position,
            "timestamp": time.time()
        })
        
        if len(history) > self.max_history:
            history = history[:self.max_history]
        
        self.cache.set_setting(history_key, history)
        logger.debug(f"[Colors] Added to history: {result_color} at {result_position}")
    
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        if len(args) == 0:
            help_text = (
                "Colors Wheel Game\n\n"
                "Commands:\n"
                "- /colors <amount> <color> - Bet on single color\n"
                "- /colors <black> <red> <blue> <gold> - Place multiple bets\n\n"
                "Colors & Multipliers:\n"
                "- Black ×2\n- Red ×3\n- Blue ×5\n- Gold ×50\n\n"
                "Examples:\n"
                "/colors 100 red\n"
                "/colors 50 20 10 5 (black, red, blue, gold)"
            )
            self.send_message_image(sender, file_queue, help_text, "Colors Help", cache, None)
            return None

        animated = True
        if len(args) >= 2 and args[-1].lower() == "x":
            animated = False
            args = args[:-1]

        if len(args) == 4:
            try:
                bets = [int(arg) for arg in args]
                total_bet = sum(bets)
                bet_type = "multiple"
                amount_str = str(total_bet)
            except ValueError:
                self.send_message_image(sender, file_queue,
                                      "All bets must be numbers!",
                                      "Colors - Invalid Bet", cache, None)
                return None
        elif len(args) == 2:
            amount_str, color = args[0], args[1].lower()
            bet_type = "single"
            bets = [color]
        else:
            self.send_message_image(sender, file_queue,
                                  "Usage: /colors <amount> <color> OR /colors <black> <red> <blue> <gold>",
                                  "Colors - Invalid Usage", cache, None)
            return None
        
        error = self.validate_bet(bet_type, amount_str, bets)
        if error:
            self.send_message_image(sender, file_queue, error, "Colors - Invalid Bet", cache, None)
            return None
        
        try:
            amount = int(amount_str) if bet_type == "single" else sum(bets)
        except ValueError:
            self.send_message_image(sender, file_queue,
                                  "Invalid amount format!",
                                  "Colors - Invalid Amount", cache, None)
            return None
        
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, amount)
        if error:
            if error == "Invalid user":
                self.send_message_image(sender, file_queue, "Invalid user!", "Colors - Validation Error", cache, None)
            else:
                balance = user.get('balance', 0) if user else 0
                self.send_message_image(sender, file_queue,
                                      f"Insufficient funds!\n\n"
                                      f"You need: ${amount}\n"
                                      f"Your balance: ${balance}",
                                      "Colors - Insufficient Funds", cache, user_id)
            return None
        
        balance_before = user["balance"]

        result_position = random.randint(0, 53)
        result_color = self.get_color_at_position(result_position)

        win = self.calculate_win(bet_type, bets, amount, result_position)

        if bet_type == "multiple":
            net_win = win - amount
        else:
            if win > 0:
                net_win = win - amount
            else:
                net_win = -amount

        new_balance = balance_before + net_win

        print(f"DEBUG: balance_before={balance_before}, amount={amount}, win={win}, net_win={net_win}, new_balance={new_balance}")

        try:
            self.update_user_balance(user_id, new_balance)
        except Exception as e:
            logger.error(f"[Colors] Error updating balance: {e}")
            self.send_message_image(sender, file_queue,
                                "Error updating balance!",
                                "Colors - System Error", cache, user_id)
            return None
        
        user_info_before = self.create_user_info(sender, amount, 0, balance_before, user.copy())
        
        try:
            exp_amount = net_win if net_win > 0 else -amount
            newLevel, newLevelProgress = self.cache.add_experience(user_id, exp_amount, sender, file_queue)
            user["level"] = newLevel
            user["level_progress"] = newLevelProgress
        except Exception as e:
            logger.error(f"[Colors] Error adding experience: {e}")
        
        base_animation_path = self.get_base_animation_path(result_position, result_color)
        if not base_animation_path:
            self.send_message_image(sender, file_queue,
                                  f"Animation for {result_color} not found!",
                                  "Colors - Animation Error", cache, user_id)
            return None
        
        user_info_after = self.create_user_info(sender, amount, net_win, new_balance, user)
        
        result_path, error = self.generate_animation(
            base_animation_path=base_animation_path,
            user_id=user_id,
            user=user,
            user_info_before=user_info_before,
            user_info_after=user_info_after,
            game_type="colors",
            animated=animated,
            frame_duration=60,
            last_frame_multiplier=30,
            custom_overlay_kwargs={
                'frame_width': 400,
                'result_color': result_color,
                'result_position': result_position,
                'animated': animated
            },
            show_win_text=True,
            font_scale=0.8,
            avatar_size=75,
            win_text_height=110
        )
        
        self.add_to_history(result_color, result_position)
        
        if error or not result_path:
            logger.error(f"[Colors] Animation error: {error}")
            self.send_message_image(sender, file_queue,
                                  "Error generating animation!",
                                  "Colors - Animation Error", cache, user_id)
            return None
        
        try:
            file_queue.put(result_path)
        except Exception as e:
            logger.error(f"[Colors] Error sending animation: {e}")
            self.send_message_image(sender, file_queue,
                                  "Error sending animation!",
                                  "Colors - System Error", cache, user_id)
            return None
        
        if bet_type == "single":
            bet_str = f"{amount} on {bets[0]}"
        else:
            bet_str = f"black={bets[0]}, red={bets[1]}, blue={bets[2]}, gold={bets[3]}"
        
        logger.info(f"COLORS: {sender} bet {bet_str} | "
                   f"Result: {result_color} (pos {result_position}) | "
                   f"Net: {net_win:+} | Balance: {balance_before} -> {new_balance}")
        
        return None

def register():
    plugin = ColorsPlugin()
    return {
        "name": "colors",
        "aliases": ["/c"],
        "description": "Colors Wheel Game - bet on colors with different multipliers",
        "execute": plugin.execute_game
    }