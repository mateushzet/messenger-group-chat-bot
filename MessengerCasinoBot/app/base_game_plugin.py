import os
from datetime import datetime as dt
from AnimationGenerator import AnimationGenerator
from utils import _get_unique_id
from user_manager import UserManager
from logger import logger
from PIL import Image, ImageFont, ImageDraw

class BaseGamePlugin:
    def __init__(self, game_name, results_folder, valid_bets=None):
        self.game_name = game_name
        self.results_folder = results_folder
        self.valid_bets = valid_bets or []
        self.cache = None
        os.makedirs(self.results_folder, exist_ok=True)

    def validate_user_and_balance(self, cache, sender, avatar_url, amount):
        user_manager = UserManager(cache)
        user_id, user = user_manager.find_user_by_name_avatar(sender, avatar_url)
        
        if not user:
            return None, None, "Invalid user"
        
        balance_before = user["balance"]
        
        if amount > balance_before:
            return None, None, "Insufficient balance"
        
        return user_id, user, None

    def validate_bet(self, bet_type, amount):
        if self.valid_bets and bet_type not in self.valid_bets:
            return f"Invalid bet type: {bet_type}"
        
        try:
            amount = int(amount)
            if amount <= 0:
                return "Amount must be positive"
        except ValueError:
            return "Invalid amount"
        
        return None

    def generate_animation(self, base_animation_path, user_id, user, user_info_before, user_info_after, game_type=None, animated=True):
        timestamp = _get_unique_id()
        
        temp_dir = self.get_app_path("temp")
        output_path = os.path.join(temp_dir, f"{self.game_name}_{timestamp}.webp")

        user_avatar_path = self.cache.get_avatar_path(user_id)
        user_background_path = self.cache.get_background_path(user_id)

        try:
            generator = AnimationGenerator()

            if animated:
                result_path = generator.generate(
                    anim_path=base_animation_path,
                    avatar_path=user_avatar_path,
                    bg_path=user_background_path,
                    user_info_before=user_info_before,
                    user_info_after=user_info_after,
                    output_path=output_path,
                    game_type=game_type
                )
            else:
                result_path = generator.generate_last_frame_static(
                    anim_path=base_animation_path,
                    avatar_path=user_avatar_path,
                    bg_path=user_background_path,
                    user_info_after=user_info_after,
                    output_path=output_path
                )

            return result_path, None

        except Exception as e:
            return None, f"Animation generation error: {e}"

    def update_user_balance(self, user_id, new_balance):
        self.cache.update_user(user_id, balance=new_balance)

    def create_user_info(self, sender, amount, win, balance, user):
        return {  
            "username": sender,
            "bet": amount,
            "win": win,
            "balance": balance,
            "level": user["level"],
            "level_progress": user["level_progress"]
        }

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        raise NotImplementedError("Subclasses must implement execute_game")
    
    def get_app_path(self, *relative_paths):
        plugins_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(plugins_dir)
        
        full_path = os.path.join(app_dir, "app", *relative_paths)
        
        if not any('.' in path for path in relative_paths):
            os.makedirs(full_path, exist_ok=True)
        
        return full_path

    def get_asset_path(self, asset_type, *subpaths):
        return self.get_app_path("assets", asset_type, *subpaths)
    
    def generate_static(self, image_path, avatar_path, bg_path, user_info, output_path=None):
        from AnimationGenerator import AnimationGenerator
        
        try:
            if output_path is None:
                timestamp = _get_unique_id()
                temp_dir = self.get_app_path("temp")
                output_path = os.path.join(temp_dir, f"{self.game_name}_{timestamp}.webp")
            
            generator = AnimationGenerator()
            final_path = generator.generate_static(
                image_path=image_path,
                avatar_path=avatar_path,
                bg_path=bg_path,
                user_info=user_info,
                output_path=output_path
            )
            return final_path
        except Exception as e:
            raise e
    
    def apply_user_overlay(self, base_image_path, user_id, sender, total_bet, win_amount, balance, user):
        try:
            user_info = {
                "username": sender,
                "bet": total_bet,
                "balance": balance,
                "level": user["level"],
                "level_progress": user.get("level_progress", 0.1),
                "win": win_amount
            }

            avatar_path = self.cache.get_avatar_path(user_id)
            bg_path = self.cache.get_background_path(user_id)

            timestamp = _get_unique_id()
            temp_dir = self.get_app_path("temp")
            final_path = os.path.join(temp_dir, f"{self.game_name}_{timestamp}.webp")
            
            final_path = self.generate_static(
                image_path=base_image_path,
                avatar_path=avatar_path,
                bg_path=bg_path,
                user_info=user_info,
                output_path=final_path
            )
            return final_path, None
            
        except Exception as e:
            return None, f"Error generating static overlay: {e}"
        
    def _add_nickname_to_image(self, img, nickname):
        if not nickname:
            return img
        
        try:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            font = ImageFont.truetype("LiberationSans-Regular.ttf", 16)
            
            draw = ImageDraw.Draw(img)
            
            x, y = 20, 17
            
            draw.text((x, y), nickname, 
                    fill=(0, 0, 0, 255),
                    font=font)
            
            return img
        except Exception as e:
            logger.error(f"Error adding nickname to image: {e}")
            return img

    def _send_error_image(self, error_type, nickname, file_queue, additional_info=""):
        try:
            error_file = f"{error_type}.png"
            error_path = os.path.join(self.error_folder, error_file)
            
            if os.path.exists(error_path):
                error_img = Image.open(error_path).convert('RGBA')
                
                error_img = self._add_nickname_to_image(error_img, nickname)
                
                temp_path = os.path.join(self.results_folder, f"error_{_get_unique_id()}.png")
                error_img.save(temp_path, format='PNG')
                
                file_queue.put(temp_path)
                
                return True
            else:
                logger.error(f"Error image not found: {error_path}")
                return False
        except Exception as e:
            logger.error(f"Error sending error image: {e}")
            return False