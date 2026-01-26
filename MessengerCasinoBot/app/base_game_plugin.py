import os
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from animation_generator import AnimationGenerator
from utils import _get_unique_id
from user_manager import UserManager
from logger import logger

class BaseGamePlugin:
    
    def __init__(self, game_name: str, results_folder: str):
        self.game_name = game_name
        self.results_folder = results_folder
        self.cache = None
        
        os.makedirs(self.results_folder, exist_ok=True)
        self.generator = AnimationGenerator()
        
        try:
            from text_renderer import CachedTextRenderer
            self.text_renderer = CachedTextRenderer(max_text_cache=300, max_metrics_cache=1000)
        except ImportError:
            self.text_renderer = None

        if hasattr(self, 'get_custom_overlay'):
            self.generator.register_custom_overlay_provider(
                self.game_name,
                self.get_custom_overlay
            )
    
    def get_custom_overlay(self, **kwargs) -> Optional[Dict]:
        return None
    
    def generate_animation(self, base_animation_path, user_id, user, user_info_before, 
                         user_info_after, game_type=None, animated=True, frame_duration=100,
                         last_frame_multiplier=1.0, custom_overlay_kwargs=None, 
                         show_win_text=True, font_scale=1.0, avatar_size=85):
        
        if game_type is None:
            game_type = self.game_name
        
        avatar_path = self.cache.get_avatar_path(user_id) if self.cache else None
        bg_path = self.cache.get_background_path(user_id) if self.cache else None
        
        if not avatar_path or not os.path.exists(avatar_path):
            error_msg = f"Avatar not found for user {user_id}"
            logger.error(f"[{self.game_name}] {error_msg}")
            return None, error_msg
        
        if not bg_path or not os.path.exists(bg_path):
            error_msg = f"Background not found for user {user_id}"
            logger.error(f"[{self.game_name}] {error_msg}")
            return None, error_msg
        
        if not os.path.exists(base_animation_path):
            error_msg = f"Base animation not found: {base_animation_path}"
            logger.error(f"[{self.game_name}] {error_msg}")
            return None, error_msg
        
        output_path = self._get_output_path(prefix=f"{self.game_name}_{'anim' if animated else 'static'}")
        
        try:
            if animated:
                result_path = self.generator.generate(
                    anim_path=base_animation_path,
                    avatar_path=avatar_path,
                    bg_path=bg_path,
                    user_info_before=user_info_before,
                    user_info_after=user_info_after,
                    output_path=output_path,
                    game_type=game_type,
                    frame_duration=frame_duration,
                    last_frame_multiplier=last_frame_multiplier,
                    custom_overlay_kwargs=custom_overlay_kwargs,
                    show_win_text=show_win_text,
                    font_scale=font_scale,
                    avatar_size=avatar_size
                )
            else:
                result_path = self.generator.generate_last_frame_static(
                    anim_path=base_animation_path,
                    avatar_path=avatar_path,
                    bg_path=bg_path,
                    user_info_after=user_info_after,
                    output_path=output_path,
                    game_type=game_type,
                    custom_overlay_kwargs=custom_overlay_kwargs,
                    show_win_text=show_win_text,
                    font_scale=font_scale,
                    avatar_size=avatar_size
                )
            
            return result_path, None
            
        except Exception as e:           
            error_msg = f"Animation generation error: {str(e)}"
            logger.critical(f"[{self.game_name}] {error_msg}", exc_info=True)
            return None, error_msg
    
    def generate_static(self, image_path: str, avatar_path: str, bg_path: str,
                       user_info: Dict, output_path: Optional[str] = None,
                       custom_overlay_kwargs: Optional[Dict] = None) -> str:
        
        try:
            if output_path is None:
                output_path = self._get_output_path(prefix=f"{self.game_name}_static")
            
            result_path = self.generator.generate_static(
                image_path=image_path,
                avatar_path=avatar_path,
                bg_path=bg_path,
                user_info=user_info,
                output_path=output_path,
                game_type=self.game_name,
                custom_overlay_kwargs=custom_overlay_kwargs
            )
                        
            return result_path
            
        except Exception as e:
            logger.error(f"[{self.game_name}] Static image generation failed: {e}")
            raise
    
    def apply_user_overlay(self, base_image_path: str, user_id: str, sender: str,
                          total_bet: int, win_amount: int, balance: int,
                          user: Dict) -> Tuple[Optional[str], Optional[str]]:
        try:
            user_info = self.create_user_info(sender, total_bet, win_amount, balance, user)
            
            avatar_path = self.cache.get_avatar_path(user_id) if self.cache else None
            bg_path = self.cache.get_background_path(user_id) if self.cache else None
            
            if not avatar_path or not bg_path:
                return None, "User resources not found"
            
            final_path = self.generate_static(
                image_path=base_image_path,
                avatar_path=avatar_path,
                bg_path=bg_path,
                user_info=user_info
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
            if cache and user_id:
                background_path = cache.get_background_path(user_id)
            
            if not background_path or not os.path.exists(background_path):
                background_path = self.get_asset_path("backgrounds", "default-bg.png")
            
            if not background_path or not os.path.exists(background_path):
                logger.error(f"[{self.game_name}] No background available for: {nickname}")
                return False

            output_folder = self.get_app_path("temp", "message_images")
            os.makedirs(output_folder, exist_ok=True)

            if self.text_renderer:
                image_path = self._generate_dynamic_message_image_cached(
                    username=nickname,
                    error_title=title,
                    error_message=message,
                    background_path=background_path,
                    output_folder=output_folder
                )
            else:
                image_path = self._generate_dynamic_message_image_fallback(
                    username=nickname,
                    error_title=title,
                    error_message=message,
                    background_path=background_path,
                    output_folder=output_folder
                )
            
            if not image_path:
                logger.error(f"[{self.game_name}] Failed to generate message image")
                return False

            file_queue.put(image_path)
            return True
            
        except Exception as e:
            logger.error(f"[{self.game_name}] Error in send_message_image: {e}")
            return False

    def _generate_dynamic_message_image_cached(self, username, error_title, error_message, 
                                            background_path, output_folder):
        try:
            IMAGE_WIDTH = 600
            BOX_WIDTH = 560
            BOX_PADDING = 15
            TITLE_Y = 15
            MAX_LINE_WIDTH = 520
            
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            
            try:
                message_font = ImageFont.truetype("DejaVuSans.ttf", 16)
            except:
                message_font = ImageFont.load_default()
            
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
            
            test_bbox = temp_draw.textbbox((0, 0), "Ay", font=message_font)
            line_height = test_bbox[3] - test_bbox[1]
            LINE_HEIGHT = max(28, line_height + 2)
            
            text_height = len(lines) * LINE_HEIGHT
            box_height = text_height + (BOX_PADDING * 2)
            
            try:
                title_font = ImageFont.truetype("DejaVuSans.ttf", 32)
            except:
                title_font = ImageFont.load_default()
            
            title_bbox = temp_draw.textbbox((0, 0), error_title, font=title_font)
            title_height = title_bbox[3] - title_bbox[1]
            
            box_y = TITLE_Y + title_height + 15
            separator_y = box_y + box_height + 15
            
            nick_bbox = temp_draw.textbbox((0, 0), username, font=message_font)
            nick_height = nick_bbox[3] - nick_bbox[1]
            nick_y = separator_y + 15
            
            image_height = nick_y + nick_height + 15
            
            original_bg = Image.open(background_path).convert("RGB")
            original_bg = original_bg.resize((IMAGE_WIDTH, image_height))
            draw = ImageDraw.Draw(original_bg)
            
            title_img = self.text_renderer.render_text_to_image(
                text=error_title,
                font_path="DejaVuSans.ttf",
                font_size=32,
                color=(255, 255, 255),
                shadow=True,
                shadow_color=(0, 0, 0, 150),
                shadow_offset=(2, 2)
            )
            
            title_x = (IMAGE_WIDTH - title_img.width) // 2
            original_bg.paste(title_img, (title_x, TITLE_Y), title_img)
            
            dark_color = (30, 30, 40)
            box_x = (IMAGE_WIDTH - BOX_WIDTH) // 2
            draw.rectangle(
                [box_x, box_y, box_x + BOX_WIDTH, box_y + box_height],
                fill=dark_color
            )
            
            text_start_y = box_y + BOX_PADDING
            
            for i, line in enumerate(lines):
                if line:
                    line_img = self.text_renderer.render_text_to_image(
                        text=line,
                        font_path="DejaVuSans.ttf",
                        font_size=16,
                        color=(255, 255, 255)
                    )
                    
                    line_x = box_x + (BOX_WIDTH - line_img.width) // 2
                    
                    line_img_height = line_img.height
                    line_y = text_start_y + i * LINE_HEIGHT
                    
                    vertical_offset = (LINE_HEIGHT - line_img_height) // 2
                    line_y += vertical_offset
                    
                    original_bg.paste(line_img, (int(line_x), int(line_y)), line_img)
            
            draw.line([(0, separator_y), (IMAGE_WIDTH, separator_y)],
                    fill=dark_color, width=2)
            
            username_img = self.text_renderer.render_text_to_image(
                text=username,
                font_path="DejaVuSans.ttf",
                font_size=16,
                color=(255, 255, 255),
                shadow=True,
                shadow_color=(0, 0, 0, 100),
                shadow_offset=(1, 1)
            )
            
            nick_x = (IMAGE_WIDTH - username_img.width) // 2
            original_bg.paste(username_img, (nick_x, nick_y), username_img)
            
            timestamp = _get_unique_id()
            output_path = os.path.join(
                output_folder,
                f"message_{username}_{timestamp}.png"
            )
            
            original_bg.save(output_path, "PNG", quality=95)
            return output_path
            
        except Exception as e:
            logger.error(f"[{self.game_name}] Error in cached message generation: {e}")
            return self._generate_dynamic_message_image_fallback(
                username, error_title, error_message, background_path, output_folder
            )

    def _generate_dynamic_message_image_fallback(self, username, error_title, error_message, 
                                                background_path, output_folder):
        try:
            temp_img = Image.new('RGB', (1, 1))
            temp_draw = ImageDraw.Draw(temp_img)
            
            try:
                title_font = ImageFont.truetype("DejaVuSans.ttf", 32)
                message_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
            except:
                title_font = ImageFont.load_default()
                message_font = ImageFont.load_default()
            
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
            logger.error(f"[BaseGamePlugin] Error generating dynamic image: {e}", exc_info=True)
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
        
        if not any('.' in path for path in relative_paths):
            os.makedirs(full_path, exist_ok=True)
        
        return full_path

    def get_asset_path(self, asset_type, *subpaths):
        return self.get_app_path("assets", asset_type, *subpaths)
    
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
    
    def _get_output_path(self, prefix: str = "output", extension: str = "webp") -> str:
        timestamp = _get_unique_id()
        temp_dir = self.get_app_path("temp", self.game_name)
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = f"{prefix}_{timestamp}.{extension}"
        output_path = os.path.join(temp_dir, filename)
        
        return output_path