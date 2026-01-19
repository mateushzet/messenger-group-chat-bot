import os
from animation_generator import AnimationGenerator
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
            logger.warning(f"[BaseGamePlugin] Invalid user {sender}: {avatar_url}")
            return None, None, "Invalid user"
        
        balance_before = user["balance"]
        
        if amount > balance_before:
            logger.info(f"[BaseGamePlugin] Insufficient balance, user: {sender}, amount: {amount}, balance: {balance_before}")
            return user_id, user, "Insufficient balance"
        
        return user_id, user, None
    
    def validate_user(self, cache, sender, avatar_url):
        user_manager = UserManager(cache)
        user_id, user = user_manager.find_user_by_name_avatar(sender, avatar_url)
        if not user:
            logger.warning(f"[BaseGamePlugin] Invalid user - {sender} - {avatar_url}")
            return None, None, "Invalid user"
        
        return user_id, user, None

    def validate_bet(self, bet_type, amount):
        if self.valid_bets and bet_type not in self.valid_bets:
            logger.info(f"[BaseGamePlugin] Invalid bet type: {bet_type}")
            return f"Invalid bet type: {bet_type}"
        
        try:
            amount = int(amount)
            if amount <= 0:
                logger.info("[BaseGamePlugin] Invalid bet amount <= 0")
                return "Amount must be positive"
        except ValueError:
            logger.info("[BaseGamePlugin] Invalid bet amount format")
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
            logger.critical(f"[BaseGamePlugin] Animation generation error: {e}", exc_info=True)
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
        logger.critical(f"[BaseGamePlugin] Subclasses must implement execute_game")
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
        from animation_generator import AnimationGenerator
        
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
            logger.critical(f"[BaseGamePlugin] Error generating static overlay: {e}", exc_info=True)
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
            logger.error(f"Error adding nickname to image: {e}", exc_info=True)
            return img

    def send_message_image(self, nickname, file_queue, message="", title="", cache=None, user_id=None):

        try:
            background_path = cache.get_background_path(user_id)
            
            if not background_path or not os.path.exists(background_path):
                logger.error(f"User background not found for user_id: {user_id}")
                return False
            
            output_folder = self.get_app_path("temp", "message_images")
            os.makedirs(output_folder, exist_ok=True)
            
            image_path = self._generate_dynamic_message_image(
                username=nickname,
                error_title=title,
                error_message=message,
                background_path=background_path,
                output_folder=output_folder
            )
            
            if not image_path:
                logger.error("Failed to generate dynamic message image")
                return False
            
            file_queue.put(image_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in send_message_image: {e}", exc_info=True)
            return False

    def _generate_dynamic_message_image(self, username, error_title, error_message, background_path, output_folder):
        try:
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            
            title_font = ImageFont.truetype("DejaVuSans.ttf", 32)
            message_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
            
            title_bbox = temp_draw.textbbox((0, 0), error_title, font=title_font)
            title_height = title_bbox[3] - title_bbox[1]
            title_y = 15
            
            max_line_width = 520
            lines = []
            
            paragraphs = error_message.split('\n')
            
            for paragraph in paragraphs:
                if not paragraph.strip():
                    lines.append("")
                    continue
                    
                words = paragraph.split()
                current_line = ""
                
                for word in words:
                    test_line = f"{current_line} {word}".strip() if current_line else word
                    bbox = temp_draw.textbbox((0, 0), test_line, font=message_font)
                    line_width = bbox[2] - bbox[0]
                    
                    if line_width <= max_line_width:
                        current_line = test_line
                    else:
                        lines.append(current_line)
                        current_line = word
                
                if current_line:
                    lines.append(current_line)
            
            line_height = 28
            text_height = len(lines) * line_height
            
            box_padding = 15
            box_height = text_height + (box_padding * 2)
            
            box_width = 560
            box_x = 20
            box_y = title_y + title_height + 15
            
            separator_y = box_y + box_height + 15
            
            nick_bbox = temp_draw.textbbox((0, 0), username, font=message_font)
            nick_height = nick_bbox[3] - nick_bbox[1]
            nick_y = separator_y + 15
            
            image_height = nick_y + nick_height + 15
            image_width = 600
            
            original_bg = Image.open(background_path).convert("RGB")
            original_bg = original_bg.resize((image_width, image_height))
            draw = ImageDraw.Draw(original_bg)

            title_x = (image_width - (title_bbox[2] - title_bbox[0])) // 2

            for dx in [-2, -1, 1, 2]:
                for dy in [-2, -1, 1, 2]:
                    draw.text((title_x + dx, title_y + dy), error_title,
                            font=title_font, fill=(0, 0, 0))

            draw.text((title_x, title_y), error_title,
                    font=title_font, fill=(255, 255, 255))

            dark_color = (30, 30, 40)
            draw.rectangle(
                [box_x, box_y, box_x + box_width, box_y + box_height],
                fill=dark_color
            )

            text_start_y = box_y + box_padding
            for i, line in enumerate(lines):
                if line:
                    bbox = draw.textbbox((0, 0), line, font=message_font)
                    line_x = box_x + (box_width - (bbox[2] - bbox[0])) // 2
                    line_y = text_start_y + i * line_height
                    
                    draw.text((line_x, line_y), line,
                            font=message_font, fill=(255, 255, 255))

            draw.line([(0, separator_y), (image_width, separator_y)],
                    fill=dark_color, width=2)

            nick_x = (image_width - (nick_bbox[2] - nick_bbox[0])) // 2

            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx or dy:
                        draw.text((nick_x + dx, nick_y + dy), username,
                                font=message_font, fill=(0, 0, 0))

            draw.text((nick_x, nick_y), username,
                    font=message_font, fill=(255, 255, 255))

            timestamp = _get_unique_id()
            output_path = os.path.join(
                output_folder,
                f"message_{username}_{timestamp}.png"
            )

            original_bg.save(output_path, "PNG", quality=95)

            return output_path

        except Exception as e:
            logger.error(f"Error generating dynamic image: {e}", exc_info=True)
            return None