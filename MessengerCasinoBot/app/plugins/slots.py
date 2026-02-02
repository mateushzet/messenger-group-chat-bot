import random
import os
from base_game_plugin import BaseGamePlugin
from logger import logger
import glob

class SlotsPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="slots"
        )
        
        self.MULTIPLIER_CHANCES = {
            0.0: 35.0,
            0.5: 27.0,
            1.0: 1.0,
            1.5: 9.0,
            2.0: 8.0,
            2.5: 5.5,
            3.0: 4.5,
            3.5: 3.0,
            4.0: 2.2,
            4.5: 1.6,
            5.0: 1.2,
            5.5: 0.9,
            6.0: 0.6,
            6.5: 0.5,
            7.0: 0.55,
            8.0: 0.45,
        }
        
        self.PREGENERATED_ANIMATIONS_FOLDER = os.path.join(self.get_asset_path("slots"), "precomputed_animations")
        
        if not os.path.exists(self.PREGENERATED_ANIMATIONS_FOLDER):
            logger.warning(f"Pregenerated animations folder not found: {self.PREGENERATED_ANIMATIONS_FOLDER}")
            os.makedirs(self.PREGENERATED_ANIMATIONS_FOLDER, exist_ok=True)
        
        self._available_files_cache = None
        self._files_loaded = False
    
    def _load_all_animation_files(self):
        if self._files_loaded and self._available_files_cache is not None:
            return self._available_files_cache
        
        logger.info(f"Loading animation files from: {self.PREGENERATED_ANIMATIONS_FOLDER}")
        self._available_files_cache = {}
        
        pattern = os.path.join(self.PREGENERATED_ANIMATIONS_FOLDER, "slots_anim_*.webp")
        all_files = glob.glob(pattern)
        
        if not all_files:
            logger.warning(f"No animation files found with pattern: {pattern}")
            self._files_loaded = True
            return self._available_files_cache
        
        logger.info(f"Found {len(all_files)} animation files")
        
        for filepath in all_files:
            filename = os.path.basename(filepath)
            
            try:
                name_part = filename.replace("slots_anim_", "").replace(".webp", "")
                
                parts = name_part.split("_")
                
                if len(parts) >= 1:
                    multiplier_str = parts[0]
                    multiplier_val = float(multiplier_str)
                    
                    if multiplier_val not in self._available_files_cache:
                        self._available_files_cache[multiplier_val] = []
                    
                    self._available_files_cache[multiplier_val].append(filepath)
                    
            except Exception as e:
                logger.warning(f"Could not parse filename {filename}: {e}")
                continue
        
        self._files_loaded = True
        return self._available_files_cache
    
    def _get_pregenerated_animations_list(self, multiplier):
        cache = self._load_all_animation_files()
        
        if not cache:
            logger.warning("No animation files available in cache")
            return []
        
        if multiplier in cache:
            return cache[multiplier]
        
        logger.error(f"No files found for multiplier {multiplier:.1f}")
        return []

    def _select_random_multiplier(self):
        multipliers = []
        probabilities = []
        
        for mult, prob in self.MULTIPLIER_CHANCES.items():
            multipliers.append(mult)
            probabilities.append(prob)
        
        selected = random.choices(multipliers, weights=probabilities, k=1)[0]
        return selected

    def _select_random_animation_file(self, multiplier):
        available_files = self._get_pregenerated_animations_list(multiplier)
        
        if not available_files:
            logger.error(f"No files found for multiplier {multiplier:.1f}")
            return None
        
        selected = random.choice(available_files)
        logger.info(f"Selected animated file: {os.path.basename(selected)}")
        return selected

    def calculate_win(self, bet_amount, win_multiplier):
        win = bet_amount * win_multiplier
        return int(round(win))
    
    def parse_bet(self, args):
        if len(args) == 1:
            try:
                amount = int(args[0])
                if amount <= 0:
                    return None,
                return amount, None
            except ValueError:
                return None,
        else:
            return None,
    
    def get_slot_result(self):
        try:
            multiplier = self._select_random_multiplier()
            animation_file = self._select_random_animation_file(multiplier)
            
            if not os.path.exists(animation_file):
                logger.error(f"Selected file does not exist: {animation_file}")
                return None, multiplier
            
            return animation_file, multiplier
            
        except Exception as e:
            logger.error(f"Error in get_slot_result: {e}")
            import traceback
            traceback.print_exc()
            return None, 0.0
    
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):

        self.cache = cache
        
        animated = True
        if len(args) >= 2 and args[-1].lower() == "x":
            animated = False
            args = args[:-1]
        
        if len(args) < 1:
            self.send_message_image(sender, file_queue, 
                                  "Usage: /slots <amount>\n\n" \
                                  "Examples:\n" \
                                  "• /slots 100\n" \
                                  "• /slots 50 x (static version)\n\n" \
                                  "Optional: Add 'x' at the end for static version",
                                  "Slots - Invalid Usage", cache, None)
            return None
        
        bet_amount, error = self.parse_bet(args)
        if error:
            self.send_message_image(sender, file_queue, error, "Slots - Bet Error", cache, None)
            return None
        
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, bet_amount)
        
        if error:
            if "Insufficient balance" in error:
                self.send_message_image(sender, file_queue, 
                                      f"Insufficient funds!\n\n" \
                                      f"Bet amount: ${bet_amount}\n" \
                                      f"Your balance: ${user.get('balance', 0) if user else 0}", 
                                      "Slots - Insufficient Funds", cache, user_id)
            else:
                self.send_message_image(sender, file_queue, "User validation failed!", "Slots - Validation Error", cache, user_id)
            return None
        
        balance_before = user["balance"]
        
        animation_file, win_multiplier = self.get_slot_result()

        if not animation_file:
            self.send_message_image(sender, file_queue, 
                                  "Error loading slot animation!\n\n" \
                                  "Technical issue - please try again later.", 
                                  "Slots - Animation Error", cache, user_id)
            return None
        
        win_amount = self.calculate_win(bet_amount, win_multiplier)
        net_win = win_amount - bet_amount
        new_balance = balance_before + net_win
        
        try:
            self.update_user_balance(user_id, new_balance)
        except Exception as e:
            logger.error(f"Error updating balance for user {user_id}: {e}")
            self.send_message_image(sender, file_queue, 
                                  "Error updating balance!\n\n" \
                                  "Please try again or contact support.", 
                                  "Slots - System Error", cache, user_id)
            return None
        
        user_info_before = self.create_user_info(sender, bet_amount, 0, balance_before, user.copy())
        
        try:
            newLevel, newLevelProgress = self.cache.add_experience(user_id, net_win, sender, file_queue)
        except Exception as e:
            logger.error(f"Error adding experience: {e}")
            newLevel = user.get("level", 1)
            newLevelProgress = user.get("level_progress", 0.1)
        
        user["level"] = newLevel
        user["level_progress"] = newLevelProgress
        user_info_after = self.create_user_info(sender, bet_amount, net_win, new_balance, user)
        
        result_path, error = self.generate_animation(
            base_animation_path=animation_file,
            user_id=user_id,
            user=user,
            user_info_before=user_info_before,
            user_info_after=user_info_after,
            animated=animated,
            frame_duration=45,
            last_frame_multiplier=4.0,
            show_win_text=True,
            font_scale=0.1,
            avatar_size=50,
            show_bet_amount=True,
            win_text_scale=0.6,
            win_text_height=110,
            final_frames_start_index=90
        )
        
        if error or not result_path:
            logger.error(f"Animation generation error: {error}")
            self.send_message_image(sender, file_queue, 
                                  f"Error generating animation!\n\n"
                                  f"Error: {error}\n"
                                  f"Please try again later.", 
                                  "Slots - Animation Error", cache, user_id)
            return None
        
        file_queue.put(result_path)
        
        if net_win > 0:
            win_str = f"+{net_win}"
        else:
            win_str = f"{net_win}"
        
        logger.info(f"SLOTS: {sender} bet {bet_amount} | Win multiplier: x{win_multiplier} | Net: {win_str} | Balance: {balance_before} -> {new_balance}")
        
        return None


def register():
    plugin = SlotsPlugin()
    return {
        "name": "slots",
        "aliases": ["/s"],
        "description": "Slot Machine Game - Match Symbols to Win\n\n**Command:**\n- /slots <bet> - Spin the slot machine\n- /slots <bet> x - Static version (no animation)\n\n**Features:**\n• Uses pre-generated animations for faster response\n• Accurate probability distribution\n• Multipliers from 0.0x to 9.0x\n\n**Special:** Add 'x' for static version (faster)",
        "execute": plugin.execute_game
    }