import os
import random
import re
from datetime import datetime
from PIL import Image
from base_game_plugin import BaseGamePlugin
from logger import logger

class LottoPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="lotto"
        )
        self.min_bet = 10
        self.total_numbers = 49
        self.player_numbers_count = 6
        self.multipliers = {
            0: 0,
            1: 0,
            2: 2,
            3: 21,
            4: 351,
            5: 10001,
            6: 100001
        }
        self.lotto_animations = {}
        
    def calculate_hit_probabilities(self):
        probabilities = {
            0: 0.435,
            1: 0.413,
            2: 0.132,
            3: 0.018,
            4: 0.001,
            5: 0.00002,
            6: 0.00000007
        }
        return probabilities
    
    def draw_hits(self):
        probabilities = self.calculate_hit_probabilities()
        hits = random.choices(
            list(probabilities.keys()),
            weights=list(probabilities.values()),
            k=1
        )[0]
        return hits
    
    def load_lotto_animations(self, hits):
        hits_folder = self.get_asset_path("lotto", "generated_animations", f"{hits}_hits")
        
        if not os.path.exists(hits_folder):
            logger.error(f"[Lotto] Lotto folder not found: {hits_folder}")
            return []
        
        animation_files = []
        for file in os.listdir(hits_folder):
            if file.startswith(f"lotto_{hits}hits_") and file.endswith('.webp'):
                animation_files.append(file)
        
        animation_files.sort(key=lambda x: self._extract_animation_number(x))
        
        return [os.path.join(hits_folder, f) for f in animation_files]
    
    def _extract_animation_number(self, filename):
        match = re.search(r'lotto_\dhits_(\d+)', filename)
        if match:
            return int(match.group(1))
        return 0
    
    def get_random_lotto_animation(self, hits):
        if hits not in self.lotto_animations:
            self.lotto_animations[hits] = self.load_lotto_animations(hits)
        
        animations = self.lotto_animations[hits]
        if not animations:
            logger.error(f"[Lotto] No animations found for {hits} hits")
            return None
        
        return random.choice(animations)
    
    def _add_hits_text_to_image(self, image, hits):
        try:
            if hits == 0 or hits == 1:
                text = f"x{self.multipliers[hits]}"
            else:
                text = f"{hits} hits x{self.multipliers[hits]}"
            
            if hits == 0 or hits == 1:
                color = (180, 180, 180, 255)
            elif hits == 2:
                color = (80, 160, 255, 255)
            elif hits == 3:
                color = (100, 255, 100, 255)
            elif hits == 4:
                color = (255, 200, 50, 255)
            elif hits == 5:
                color = (255, 140, 0, 255)
            else:
                color = (255, 50, 100, 255)
            
            text_img = self.text_renderer.render_text(
                text=text,
                font_size=40,
                color=color,
                stroke_width=2,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_offset=(2, 2)
            )
            
            text_x = (image.width - text_img.width) // 2
            text_y = image.height - text_img.height - 50
            
            result = image.copy()
            result.alpha_composite(text_img, (text_x, text_y))
            
            return result
            
        except Exception as e:
            logger.error(f"[Lotto] Error adding hits text: {e}")
            return image
    
    def _create_multi_game_image(self, games_data, user_id, user, total_bet, total_net_win, new_balance, sender):
        try:
            temp_images = []
            
            for i, game_data in enumerate(games_data):
                hits = game_data['hits']
                
                animation_path = self.get_random_lotto_animation(hits)
                if not animation_path:
                    logger.error(f"[Lotto] Could not load animation for hits: {hits}")
                    continue
                
                try:
                    with Image.open(animation_path) as img:
                        frame_count = 0
                        try:
                            while True:
                                img.seek(frame_count)
                                frame_count += 1
                        except EOFError:
                            pass
                        
                        if frame_count > 1:
                            img.seek(frame_count - 1)
                            base_frame = img.copy().convert('RGBA')
                        else:
                            img.seek(0)
                            base_frame = img.copy().convert('RGBA')
                            
                except Exception as img_error:
                    logger.error(f"[Lotto] Error processing animation {animation_path}: {img_error}")
                    continue
                
                base_frame = self._remove_transparent_border_fixed(base_frame)
                
                frame_with_text = self._add_hits_text_to_image(base_frame, hits)
                temp_images.append(frame_with_text)
            
            if not temp_images:
                return None, "No games generated"
            
            total_width = max(img.width for img in temp_images)
            total_height = sum(img.height for img in temp_images)
            
            result_img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 255))
            
            y_offset = 0
            for game_img in temp_images:
                x_offset = (total_width - game_img.width) // 2
                result_img.paste(game_img, (x_offset, y_offset), game_img)
                y_offset += game_img.height
            
            temp_path = os.path.join(self.results_folder, f"temp_multi_{user_id}_{int(datetime.now().timestamp())}.webp")
            result_img.save(temp_path, format='WEBP', quality=95)
            
            overlay_path, overlay_error = self.apply_user_overlay(
                base_image_path=temp_path,
                user_id=user_id,
                sender=sender,
                total_bet=total_bet,
                win_amount=total_net_win,
                balance=new_balance,
                user=user,
                show_win_text=True,
                font_scale=1.8,
                avatar_size=90,
                show_bet_amount=True,
                win_text_scale=0.8
            )
            
            try:
                os.remove(temp_path)
            except:
                pass
            
            if overlay_error:
                logger.error(f"[Lotto] Error applying user overlay: {overlay_error}")
                return None, overlay_error
            
            return overlay_path, None
            
        except Exception as e:
            logger.error(f"[Lotto] Error creating multi-game image: {e}")
            return None, str(e)

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        animated = True
        multi_game_count = 1
        
        if args:
            last_arg = args[-1].lower()
            if last_arg == "x":
                animated = False
                args = args[:-1]
            elif last_arg.startswith("x"):
                try:
                    count_str = last_arg[1:]
                    if count_str:
                        multi_game_count = int(count_str)
                        animated = False
                        args = args[:-1]
                except ValueError:
                    pass
        
        if len(args) == 0:
            help_text = self._get_help_message()
            self.send_message_image(sender, file_queue, help_text, "Lotto Game", cache, None)
            return ""
        
        try:
            bet_amount = int(args[0])
        except ValueError:
            self.send_message_image(sender, file_queue, 
                                f"Invalid bet amount!\n\n"
                                f"Use: /lotto <amount>\n"
                                f"Minimum bet: ${self.min_bet}",
                                "Lotto - Error", cache, None)
            return ""
        
        if bet_amount < self.min_bet:
            self.send_message_image(sender, file_queue, 
                                f"Minimum bet is ${self.min_bet}!\n\n"
                                f"Your bet: ${bet_amount}",
                                "Lotto - Error", cache, None)
            return ""
        
        if multi_game_count > 10:
            multi_game_count = 10
        
        total_bet = bet_amount * multi_game_count
        
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, total_bet)
        if error == "Invalid user":
            self.send_message_image(sender, file_queue, "Invalid user!", "Lotto - Validation Error", cache, user_id)
            return ""
        elif error:
            self.send_message_image(sender, file_queue, 
                                f"Insufficient funds!\n\n"
                                f"Total bet: ${total_bet} ({multi_game_count} × ${bet_amount})\n"
                                f"Your balance: ${user.get('balance', 0) if user else 0}",
                                "Lotto - Insufficient Funds", cache, user_id)
            return ""
        
        balance_before = user["balance"]
        
        games_data = []
        total_net_win = 0
        
        for game_num in range(multi_game_count):
            hits = self.draw_hits()
            
            multiplier = self.multipliers[hits]
            win_amount = bet_amount * multiplier
            net_win = win_amount - bet_amount
            total_net_win += net_win
            
            games_data.append({
                'game_num': game_num + 1,
                'bet_amount': bet_amount,
                'hits': hits,
                'multiplier': multiplier,
                'win_amount': win_amount,
                'net_win': net_win
            })
        
        new_balance = balance_before + total_net_win
        
        try:
            self.update_user_balance(user_id, new_balance)
        except Exception as e:
            logger.error(f"[Lotto] Error updating balance for user {user_id}: {e}")
            self.send_message_image(sender, file_queue, 
                                "Error updating balance!",
                                "Lotto - System Error", cache, user_id)
            return ""
        
        user_info_before = self.create_user_info(sender, total_bet, 0, balance_before, user.copy())
        
        try:
            newLevel, newLevelProgress = self.cache.add_experience(user_id, total_net_win, sender, file_queue)
        except Exception as e:
            logger.error(f"[Lotto] Error adding experience: {e}")
            newLevel = user.get("level", 1)
            newLevelProgress = user.get("level_progress", 0.1)
        
        user["level"] = newLevel
        user["level_progress"] = newLevelProgress
        user_info_after = self.create_user_info(sender, total_bet, total_net_win, new_balance, user)
        
        if multi_game_count == 1:
            game_data = games_data[0]
            animation_path = self.get_random_lotto_animation(game_data['hits'])
            
            if not animation_path:
                self.send_message_image(sender, file_queue, 
                                    f"Error loading lotto animations!",
                                    "Lotto - Error", cache, user_id)
                return ""
            
            result_path, error = self.generate_animation(
                base_animation_path=animation_path,
                user_id=user_id,
                user=user,
                user_info_before=user_info_before,
                user_info_after=user_info_after,
                animated=animated,
                frame_duration=65,
                last_frame_multiplier=20,
                show_win_text=True,
                font_scale=0.8,
                avatar_size=75,
                win_text_height=50
            )
            
            if error:
                logger.error(f"[Lotto] Animation error: {error}")
                self.send_message_image(sender, file_queue, 
                                    f"Error generating animation!",
                                    "Lotto - Animation Error", cache, user_id)
                return ""
            
        else:
            result_path, error = self._create_multi_game_image(
                games_data, user_id, user, total_bet, total_net_win, new_balance, sender
            )
            
            if error:
                logger.error(f"[Lotto] Multi-game image error: {error}")
                self.send_message_image(sender, file_queue, 
                                    f"Error creating multi-game image!",
                                    "Lotto - Multi-Game Error", cache, user_id)
                return ""
        
        file_queue.put(result_path)
        
        if total_net_win > 0:
            result_status = f"WIN +${total_net_win}"
        elif total_net_win < 0:
            result_status = f"LOSE -${abs(total_net_win)}"
        else:
            result_status = "BREAK EVEN"
        
        hits_summary = ", ".join([f"{g['hits']} hits" for g in games_data])
        logger.info(f"[Lotto] LOTTO: {sender} bet ${total_bet} ({multi_game_count} games) | Hits: {hits_summary} | Net: {result_status}")
        
        return ""

    def _get_help_message(self):
        return (
            "LOTTO GAME\n\n"
            f"Minimum bet: ${self.min_bet}\n\n"
            "Multipliers:\n"
            "• 0-1 hits: x0\n"
            "• 2 hits: x2\n"
            "• 3 hits: x20\n"
            "• 4 hits: x350\n"
            "• 5 hits: x10,000\n"
            "• 6 hits: x100,000\n\n"
            "Commands:\n"
            "• /lotto <amount> - Play with animation\n"
            "• /lotto <amount> x - Static image\n"
            f"• /lotto <amount> xN - N static games (max 10)\n\n"
            "Examples:\n"
            "• /lotto 100\n"
            "• /lotto 50 x\n"
            "• /lotto 10 x5"
        )
    
    def _remove_transparent_border_fixed(self, img):
        try:
            if img.size == (445, 260):
                return img.crop((30, 30, 415, 230))
            elif img.size == (385, 200):
                return img
            else:
                return img
                
        except Exception as e:
            logger.error(f"[Lotto] Error removing border: {e}")
            return img

def register():
    plugin = LottoPlugin()
    logger.info("[Lotto] Lotto plugin registered")
    return {
        "name": "lotto",
        "aliases": ["/l"],
        "description": f"Lotto game - match numbers for huge multipliers (min ${plugin.min_bet})",
        "execute": plugin.execute_game
    }