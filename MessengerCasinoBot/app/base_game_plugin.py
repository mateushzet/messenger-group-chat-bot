import os
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw
from animation_generator import AnimationGenerator, GenerationRequest, UserInfo, GenerationOptions
from utils import _get_unique_id
from user_manager import UserManager
from logger import logger

class BaseGamePlugin:
    
    _shared_generator = None
    
    @classmethod
    def get_shared_generator(cls):
        if cls._shared_generator is None:
            cls._shared_generator = AnimationGenerator()
        return cls._shared_generator
    
    def __init__(self, game_name: str):
        self.game_name = game_name
        
        self.results_folder = self.get_asset_path("temp")

        self.generator = self.get_shared_generator()
        
        self.generator.results_folder = self.results_folder

        self.text_renderer = self.generator.text_renderer
        
        if hasattr(self, 'get_custom_overlay') and callable(self.get_custom_overlay):
            if game_name not in self.generator.custom_overlay_providers:
                self.generator.register_custom_overlay_provider(
                    game_name, 
                    self.get_custom_overlay
                )
    
    def get_custom_overlay(self, **kwargs) -> Optional[Dict]:
        return None
    
    def generate_animation(self, base_animation_path, user_id, user, user_info_before, 
                         user_info_after, animated=True, frame_duration=100,
                         last_frame_multiplier=1.0, custom_overlay_kwargs=None, 
                         show_win_text=True, font_scale=1.0, avatar_size=85, 
                         show_bet_amount=True, win_text_height=-1, final_frames_start_index=-1,
                         win_text_scale=-1, overlay_position="bottom"):
        avatar_path = None
        bg_path = None
        
        if hasattr(self, 'cache') and self.cache:
            avatar_path = self.cache.get_avatar_path(user_id) if hasattr(self.cache, 'get_avatar_path') else None
            bg_path = self.cache.get_background_path(user_id) if hasattr(self.cache, 'get_background_path') else None
        
        validation_errors = []
        
        if not avatar_path or not os.path.exists(avatar_path):
            validation_errors.append(f"Avatar not found for user {user_id}: {avatar_path}")
        
        if not bg_path or not os.path.exists(bg_path):
            validation_errors.append(f"Background not found for user {user_id}: {bg_path}")
        
        if not os.path.exists(base_animation_path):
            validation_errors.append(f"Base animation not found: {base_animation_path}")
        
        if validation_errors:
            error_msg = " | ".join(validation_errors)
            logger.error(f"[{self.game_name}] {error_msg}")
            return None, error_msg
        
        user_before = UserInfo.from_dict({
            **user_info_before,
            'user_id': str(user_id),
            'avatar_path': avatar_path
        })
        
        user_after = UserInfo.from_dict({
            **user_info_after,
            'user_id': str(user_id),
            'avatar_path': avatar_path
        })
        
        options = GenerationOptions(
            animated=animated,
            avatar_size=avatar_size,
            font_scale=font_scale,
            show_win_text=show_win_text,
            frame_duration=frame_duration,
            last_frame_multiplier=last_frame_multiplier,
            show_bet_amount=show_bet_amount,
            win_text_height=win_text_height,
            custom_overlay_kwargs=custom_overlay_kwargs,
            final_frames_start_index=final_frames_start_index,
            win_text_scale=win_text_scale,
            overlay_position=overlay_position
        )
        
        request = GenerationRequest(
            animation_path=base_animation_path,
            background_path=bg_path,
            user_before=user_before,
            user_after=user_after,
            game_name=self.game_name,
            options=options
        )
        
        try:
            output_path, error = self.generator.generate(request)
            
            if output_path:
                logger.info(f"[{self.game_name}] Successfully generated: {output_path}")
                return output_path, None
            else:
                logger.error(f"[{self.game_name}] Generation failed: {error}")
                return None, error
                
        except Exception as e:           
            error_msg = f"Animation generation error: {str(e)}"
            logger.critical(f"[{self.game_name}] {error_msg}", exc_info=True)
            return None, error_msg
    
    def generate_static(self, image_path: str, avatar_path: str, bg_path: str,
                       user_info: Dict, custom_overlay_kwargs: Optional[Dict] = None,
                       show_bet_amount: bool = True, show_win_text: bool = True,
                       font_scale: float = 1.0, avatar_size: int = 85) -> str:
        try:
            user_info_data = {
                **user_info,
                'avatar_path': avatar_path
            }
            
            user = UserInfo.from_dict(user_info_data)
            
            options = GenerationOptions(
                animated=False,
                avatar_size=avatar_size,
                font_scale=font_scale,
                show_win_text=show_win_text,
                show_bet_amount=show_bet_amount,
                custom_overlay_kwargs=custom_overlay_kwargs
            )
            
            request = GenerationRequest(
                animation_path=image_path,
                background_path=bg_path,
                user_before=user,
                user_after=user,
                game_name=self.game_name,
                options=options
            )
            
            output_path, error = self.generator.generate(request)
        
            if output_path:
                return output_path
            else:
                raise Exception(f"Generation failed: {error}")
                        
        except Exception as e:
            logger.error(f"[{self.game_name}] Static image generation failed: {e}")
            raise
    
    def apply_user_overlay(self, base_image_path: str, user_id: str, sender: str,
                        total_bet: int, win_amount: int, balance: int,
                        user: Dict, show_win_text: bool = True, font_scale: float = 1.0, 
                        avatar_size: int = 85, show_bet_amount: bool = True) -> Tuple[Optional[str], Optional[str]]:
        try:
            user_info = self.create_user_info(sender, total_bet, win_amount, balance, user)
            
            avatar_path = None
            bg_path = None
            
            if hasattr(self, 'cache') and self.cache:
                avatar_path = self.cache.get_avatar_path(user_id) if hasattr(self.cache, 'get_avatar_path') else None
                bg_path = self.cache.get_background_path(user_id) if hasattr(self.cache, 'get_background_path') else None
            
            if not avatar_path or not bg_path:
                return None, "User resources not found"
            
            final_path = self.generate_static(
                image_path=base_image_path,
                avatar_path=avatar_path,
                bg_path=bg_path,
                user_info=user_info,
                show_bet_amount=show_bet_amount,
                show_win_text=show_win_text,
                font_scale=font_scale,
                avatar_size=avatar_size
            )
            
            return final_path, None
            
        except Exception as e:
            error_msg = f"Error applying user overlay: {str(e)}"
            logger.critical(f"[{self.game_name}] {error_msg}", exc_info=True)
            return None, error_msg
    
    def send_message_image(self, nickname: str, file_queue, message: str = "",
                        title: str = "", cache=None, user_id: Optional[str] = None) -> bool:
        try:
            background_path = None
            if cache and user_id and hasattr(cache, 'get_background_path'):
                background_path = cache.get_background_path(user_id)
            
            if not background_path or not os.path.exists(background_path):
                background_path = self.get_asset_path("backgrounds", "default-bg.png")
            
            if not background_path or not os.path.exists(background_path):
                logger.error(f"[{self.game_name}] No background available for: {nickname}")
                return False

            image_path = self._generate_dynamic_message_image(
                username=nickname,
                error_title=title,
                error_message=message,
                background_path=background_path,
                output_folder=self.results_folder
            )
            
            if not image_path:
                logger.error(f"[{self.game_name}] Failed to generate message image")
                return False

            file_queue.put(image_path)
            return True
            
        except Exception as e:
            logger.error(f"[{self.game_name}] Error in send_message_image: {e}")
            return False

    def _generate_dynamic_message_image(self, username, error_title, error_message, 
                                    background_path, output_folder):
        try:
            IMAGE_WIDTH = 600
            BOX_WIDTH = 560
            BOX_PADDING = 15
            TITLE_Y = 15
            MAX_LINE_WIDTH = 520
            
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            
            title_font = self.generator.text_renderer.get_font(32)
            message_font = self.generator.text_renderer.get_font(16)

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
                    
                    if line_width <= MAX_LINE_WIDTH:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
            
                if current_line:
                    lines.append(current_line)
            
            title_bbox = temp_draw.textbbox((0, 0), error_title, font=title_font)
            title_height = title_bbox[3] - title_bbox[1]
            
            test_bbox = temp_draw.textbbox((0, 0), "Ay", font=message_font)
            line_height = test_bbox[3] - test_bbox[1]
            LINE_HEIGHT = max(28, line_height + 2)
            
            text_height = len(lines) * LINE_HEIGHT
            box_height = text_height + (BOX_PADDING * 2)
            
            box_y = TITLE_Y + title_height + 15
            separator_y = box_y + box_height + 15
            
            nick_bbox = temp_draw.textbbox((0, 0), username, font=message_font)
            nick_height = nick_bbox[3] - nick_bbox[1]
            nick_y = separator_y + 15
            
            image_height = nick_y + nick_height + 15
            
            original_bg = Image.open(background_path).convert("RGB")
            original_bg = original_bg.resize((IMAGE_WIDTH, image_height))
            draw = ImageDraw.Draw(original_bg)
            
            title_x = (IMAGE_WIDTH - (title_bbox[2] - title_bbox[0])) // 2
            
            for dx in [-2, -1, 1, 2]:
                for dy in [-2, -1, 1, 2]:
                    draw.text((title_x + dx, TITLE_Y + dy), error_title,
                            font=title_font, fill=(0, 0, 0))
            
            draw.text((title_x, TITLE_Y), error_title,
                    font=title_font, fill=(255, 255, 255))
            
            dark_color = (30, 30, 40)
            box_x = (IMAGE_WIDTH - BOX_WIDTH) // 2
            draw.rectangle(
                [box_x, box_y, box_x + BOX_WIDTH, box_y + box_height],
                fill=dark_color
            )
            
            text_start_y = box_y + BOX_PADDING
            
            for i, line in enumerate(lines):
                if line:
                    bbox = temp_draw.textbbox((0, 0), line, font=message_font)
                    line_x = box_x + (BOX_WIDTH - (bbox[2] - bbox[0])) // 2
                    line_y = text_start_y + i * LINE_HEIGHT
                    
                    draw.text((line_x, line_y), line,
                            font=message_font, fill=(255, 255, 255))
            
            draw.line([(0, separator_y), (IMAGE_WIDTH, separator_y)],
                    fill=dark_color, width=2)
            
            nick_x = (IMAGE_WIDTH - (nick_bbox[2] - nick_bbox[0])) // 2
            
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
            logger.error(f"[{self.game_name}] Error generating message image: {e}", exc_info=True)
            return None

    def execute_game(self, command_name: str, args: List[str], file_queue,
                    cache=None, sender: Optional[str] = None,
                    avatar_url: Optional[str] = None) -> None:
        self.cache = cache
        raise NotImplementedError(f"{self.game_name} must implement execute_game")
    
    def get_game_resource(self, resource_name: str) -> Optional[Image.Image]:

        resource_path = self.get_asset_path("games", self.game_name, resource_name)
        
        if not os.path.exists(resource_path):
            logger.error(f"[{self.game_name}] Resource not found: {resource_path}")
            return None
        
        try:
            img = Image.open(resource_path).convert("RGBA")
            return img
        except Exception as e:
            logger.error(f"[{self.game_name}] Error loading resource {resource_name}: {e}")
            return None

    def get_app_path(self, *relative_paths):
        plugins_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(plugins_dir)
        
        full_path = os.path.join(app_dir, "app", *relative_paths)
        
        return full_path

    def get_asset_path(self, asset_type, *subpaths):
        return self.get_app_path("assets", asset_type, *subpaths)
    
    def validate_user_and_balance(self, cache, sender, avatar_url, amount):
        user_manager = UserManager(cache)
        user_id, user = user_manager.find_user_by_name_avatar(sender, avatar_url)
        
        if not user:
            logger.warning(f"[{self.game_name}] Invalid user {sender}: {avatar_url}")
            return None, None, "Invalid user"
        
        balance_before = user["balance"]
        
        if amount > balance_before:
            logger.info(f"[{self.game_name}] Insufficient balance, user: {sender}, amount: {amount}, balance: {balance_before}")
            return user_id, user, "Insufficient balance"
        
        return user_id, user, None
    
    def validate_user(self, cache, sender, avatar_url):
        user_manager = UserManager(cache)
        user_id, user = user_manager.find_user_by_name_avatar(sender, avatar_url)
        if not user:
            logger.warning(f"[{self.game_name}] Invalid user - {sender} - {avatar_url}")
            return None, None, "Invalid user"
        
        return user_id, user, None
    
    def update_user_balance(self, user_id, new_balance):
        if hasattr(self, 'cache') and self.cache and hasattr(self.cache, 'update_user'):
            self.cache.update_user(user_id, balance=new_balance)
        else:
            logger.warning(f"[{self.game_name}] Cache not available for updating balance")

    def create_user_info(self, sender, amount, win, balance, user):
        return {  
            "user_id": str(user.get('id', '')),
            "username": sender,
            "bet": amount,
            "win": win,
            "balance": balance,
            "level": user.get("level", 1),
            "level_progress": user.get("level_progress", 0),
            "is_win": win > 0,
            "avatar_path": user.get("avatar_path", "")
        }