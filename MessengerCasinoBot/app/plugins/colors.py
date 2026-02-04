import random
import os
import time
from base_game_plugin import BaseGamePlugin
from logger import logger
from PIL import Image, ImageDraw

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
                                
    def _generate_history_overlay(self, width=350, height=40, history=None, show_current=False):
        try:
            if not history:
                history = []
            
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            total_items = min(len(history), self.max_history)
            if total_items == 0:
                return overlay
            
            bar_width = 12
            spacing = 3
            bar_height = 30
            
            total_width_needed = (total_items * bar_width) + ((total_items - 1) * spacing)
            
            if total_width_needed > width:
                bar_width = max(6, (width - (total_items - 1) * spacing) // total_items)
                total_width_needed = (total_items * bar_width) + ((total_items - 1) * spacing)
            
            start_x = (width - total_width_needed) // 2
            bar_y_start = (height - bar_height) // 2
            
            for i in range(total_items):
                display_index = total_items - 1 - i
                item = history[display_index]
                color_name = item.get("color", "black")
                is_current_item = item.get('is_current', False)
                
                color_rgb = self.history_colors.get(color_name, self.history_colors["black"])
                
                if is_current_item and show_current:
                    alpha = 255
                    current_bar_width = bar_width + 4
                    current_bar_height = bar_height + 4
                    current_x_start = start_x + (i * (bar_width + spacing)) - 2
                    current_y_start = bar_y_start - 2
                    
                    draw.rectangle([current_x_start, current_y_start,
                                current_x_start + current_bar_width, current_y_start + current_bar_height],
                                fill=(255, 255, 255, 80))
                    
                    inner_x = current_x_start + 2
                    inner_y = current_y_start + 2
                    inner_width = current_bar_width - 4
                    inner_height = current_bar_height - 4
                    
                    draw.rectangle([inner_x, inner_y,
                                inner_x + inner_width, inner_y + inner_height],
                                fill=color_rgb + (alpha,))
                    
                    continue
                
                else:
                    fade_factor = (i / total_items) if total_items > 0 else 0
                    alpha = int(255 * (0.3 + (0.7 * fade_factor)))
                
                bar_color = color_rgb + (alpha,)
                
                x_start = start_x + (i * (bar_width + spacing))
                x_end = x_start + bar_width
                
                draw.rectangle([x_start, bar_y_start, x_end, bar_y_start + bar_height],
                            fill=bar_color)
            
            return overlay
            
        except Exception as e:
            logger.error(f"[Colors] Error generating history overlay: {e}")
            return None
            
    def get_custom_overlay(self, **kwargs):
        try:
            frame_width = kwargs.get('frame_width', 400)
            request = kwargs.get('request', None)
            
            custom_kwargs = {}
            if request and hasattr(request.options, 'custom_overlay_kwargs'):
                custom_kwargs = request.options.custom_overlay_kwargs or {}
            
            result_color = custom_kwargs.get('result_color')
            result_position = custom_kwargs.get('result_position')
            
            history = self.get_history()
            history_to_display = history[:self.max_history]
            
            overlay_before = self._generate_complete_overlay(
                frame_width=frame_width,
                history=history_to_display,
                show_current=False
            )
            
            overlay_after = None
            if result_color:
                history_with_new = history_to_display.copy()
                new_entry = {
                    "color": result_color,
                    "position": result_position,
                    "timestamp": time.time(),
                    "is_current": True
                }
                history_with_new.insert(0, new_entry)
                
                if len(history_with_new) > self.max_history:
                    history_with_new = history_with_new[:self.max_history]
                
                overlay_after = self._generate_complete_overlay(
                    frame_width=frame_width,
                    history=history_with_new,
                    show_current=True
                )
            else:
                overlay_after = overlay_before
            
            overlay_y_position = 150
            
            return {
                'before': {
                    'image': overlay_before,
                    'position': (0, overlay_y_position),
                    'type': 'before'
                },
                'after': {
                    'image': overlay_after,
                    'position': (0, overlay_y_position),
                    'type': 'after'
                }
            }
            
        except Exception as e:
            logger.error(f"[Colors] Error in get_custom_overlay: {e}", exc_info=True)
            return None
            
    def _generate_complete_overlay(self, frame_width, history=None, show_current=False):
        if history is None:
            history = []
        
        available_width = frame_width - 50
        section_width = min(int(available_width * 0.9), 350)
        
        history_height = 40
        multipliers_height = 50
        padding_between = 10

        top_margin = 30
        
        total_height = history_height + multipliers_height + padding_between + top_margin
        
        overlay_image = Image.new('RGBA', (frame_width, total_height), (0, 0, 0, 0))
        
        multipliers_overlay = self._create_multipliers_overlay(section_width, multipliers_height)
        
        history_overlay = self._generate_history_overlay(
            width=section_width, 
            height=history_height,
            history=history,
            show_current=show_current
        )
        
        section_x = (frame_width - section_width) // 2
        history_y = top_margin
        multipliers_y = history_y + history_height + padding_between
        
        if history_overlay:
            overlay_image.alpha_composite(history_overlay, (section_x, history_y))
        
        if multipliers_overlay:
            overlay_image.alpha_composite(multipliers_overlay, (section_x, multipliers_y))
        
        return overlay_image

    def _create_multipliers_overlay(self, width, height):
        try:
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            
            text_renderer = self.text_renderer
            if not text_renderer:
                logger.warning("[Colors] TextRenderer not available for multipliers")
                return overlay
            
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
                
                text_img = text_renderer.render_text(
                    text=text,
                    font_size=18,
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
            animated=animated,
            frame_duration=60,
            last_frame_multiplier=30,
            custom_overlay_kwargs={
                'result_color': result_color,
                'result_position': result_position,
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