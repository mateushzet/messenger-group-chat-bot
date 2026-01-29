import os
from PIL import Image, ImageDraw, ImageFilter
from text_renderer import CachedTextRenderer
from resource_cache import ResourceCache
from lazy_loader import LazyAnimationLoader
from typing import Dict, Optional, Callable
from logger import logger

class AnimationGenerator:
    
    BASE_DIR = os.path.dirname(__file__)
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    BET_ICON_PATH = os.path.join(ASSETS_DIR, "bet_icon.png")
    BALANCE_ICON_PATH = os.path.join(ASSETS_DIR, "balance_icon.png")
    
    def __init__(self):
        
        self.win_text_cache: Dict[str, Image.Image] = {}
        self.processed_bg_cache: Dict[str, Image.Image] = {}
        
        self.colors = {
            'text_light': (240, 240, 240, 255),
            'success': (70, 180, 90, 255),
            'danger': (220, 80, 80, 255),
            'warning': (220, 160, 60, 255)
        }
        
        self.text_renderer = CachedTextRenderer()
        self.resource_cache = ResourceCache(max_size_mb=200)
        self.lazy_loader = LazyAnimationLoader()
        
        self._preloaded_icons = None
        self._default_font_path = "DejaVuSans-Bold.ttf"
        
        self.custom_overlay_providers: Dict[str, Callable] = {}
    
    def register_custom_overlay_provider(self, game_type: str, provider_callback: Callable):
        self.custom_overlay_providers[game_type] = provider_callback
        
    def get_custom_overlay(self, game_type: str, frame_index: int = 0, **kwargs) -> Optional[Dict]:
        if game_type not in self.custom_overlay_providers:
            return None
        
        provider = self.custom_overlay_providers[game_type]
        
        try:
            overlay_data = provider(frame_index=frame_index, **kwargs)
            
            if overlay_data is None:
                return None
            
            if not isinstance(overlay_data, dict):
                raise ValueError(f"Overlay provider for {game_type} must return dict, got {type(overlay_data)}")
            
            if 'image' not in overlay_data:
                raise ValueError(f"Overlay provider for {game_type} must include 'image' key")
            
            if 'position' not in overlay_data:
                overlay_data['position'] = (0, 0)
            
            return overlay_data
            
        except Exception as e:
            logger.error(f"[AnimationGenerator] Error getting custom overlay for {game_type}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _preload_resources(self):
        if self._preloaded_icons is None:
            self._preloaded_icons = {
                'bet_icon': self.resource_cache.get_icon(self.BET_ICON_PATH, (20, 20)),
                'balance_icon': self.resource_cache.get_icon(self.BALANCE_ICON_PATH, (20, 20))
            }
        return self._preloaded_icons

    def _get_cached_win_text(self, text, font_size, color):
        cache_key = f"wintext_{text}_{font_size}_{color}"
        
        if cache_key in self.win_text_cache:
            return self.win_text_cache[cache_key]
        
        win_text_img = self.text_renderer.render_text_to_image(
            text=text,
            font_path=self._default_font_path,
            font_size=font_size,
            color=color,
            stroke_width=2,
            stroke_color=(0, 0, 0, 180)
        )
        
        self.win_text_cache[cache_key] = win_text_img
        if len(self.win_text_cache) > 50:
            self.win_text_cache.pop(next(iter(self.win_text_cache)))
        
        return win_text_img

    def _get_cached_background(self, bg_image, size):
        if bg_image is None:
            return None
        
        cache_key = f"bg_{size[0]}_{size[1]}_{hash(bg_image.tobytes())}"
        
        if cache_key in self.processed_bg_cache:
            return self.processed_bg_cache[cache_key]
        
        bg_resized = bg_image.resize(size)
        self.processed_bg_cache[cache_key] = bg_resized
        
        if len(self.processed_bg_cache) > 20:
            self.processed_bg_cache.pop(next(iter(self.processed_bg_cache)))
        
        return bg_resized

    def _process_single_frame(self, frame, overlay_data, win_text_img=None, 
                            bg_image=None, custom_overlay_data=None, win_text_height=-1):
        
        result = Image.new("RGBA", (frame.width, frame.height))
        
        if bg_image:
            bg_resized = self._get_cached_background(bg_image, frame.size)
            if bg_resized:
                result.paste(bg_resized, (0, 0))
        
        result.paste(frame, (0, 0), frame)
        
        overlay_img = overlay_data['image']
        is_on_animation = overlay_data.get('is_on_animation', False)
        
        if is_on_animation:
            if overlay_img.width != frame.width or overlay_img.height > frame.height:
                params = overlay_data.get('parameters', {})
                font_scale = params.get('font_scale', 1.0)
                avatar_size = params.get('avatar_size', 85)
                overlay_height = params.get('overlay_height', 110)
                
                overlay_height = min(overlay_height, frame.height - 10)
                
                if 'resized_overlay' not in overlay_data:
                    new_overlay = Image.new('RGBA', (frame.width, overlay_height), (0, 0, 0, 0))
                    
                    avatar_x_old, avatar_y_old, _ = overlay_data.get('avatar_position', (0, 0, avatar_size))
                    avatar_x_new = frame.width - avatar_size
                    avatar_y_new = overlay_height - avatar_size
                    
                    avatar_region = overlay_img.crop((
                        avatar_x_old, avatar_y_old,
                        avatar_x_old + avatar_size, avatar_y_old + avatar_size
                    ))
                    new_overlay.paste(avatar_region, (avatar_x_new, avatar_y_new))
                    
                    left_section_info = overlay_data.get('left_section_info', {})
                    text_start_x = left_section_info.get('text_start_x', int(2 * font_scale))
                    actual_left_width = left_section_info.get('actual_left_width', 260)
                    
                    crop_width = min(actual_left_width, overlay_img.width)
                    crop_height = min(overlay_height, overlay_img.height)
                    
                    text_region = overlay_img.crop((0, 0, crop_width, crop_height))
                    new_overlay.paste(text_region, (text_start_x, 0), text_region)
                    
                    overlay_data['resized_overlay'] = new_overlay
                    overlay_img = new_overlay
                else:
                    overlay_img = overlay_data['resized_overlay']
            
            overlay_y = frame.height - overlay_img.height
            result.alpha_composite(overlay_img, (0, overlay_y))
        
        if win_text_img:
            win_text_x = (frame.width - win_text_img.width) // 2
            if win_text_height != -1:
                    win_text_y = win_text_height
            else: 
                win_text_y = (frame.height - win_text_img.height) // 2
            result.alpha_composite(win_text_img, (win_text_x, win_text_y))
        
        if custom_overlay_data and 'image' in custom_overlay_data:
            overlay_img_custom = custom_overlay_data['image']
            overlay_pos = custom_overlay_data.get('position', (0, 0))
            
            if (overlay_img_custom.width <= result.width and 
                overlay_img_custom.height <= result.height):
                result.alpha_composite(overlay_img_custom, overlay_pos)
        
        return result
 
    def _load_animation_frames_batch(self, anim_path, frame_indices):
        frames = []
        
        for idx in frame_indices:
            frame = self.lazy_loader.get_frame_at_index(anim_path, idx)
            if frame:
                frames.append(frame)
        
        return frames

    def generate(self, anim_path, avatar_path, bg_path, user_info_before, 
                 user_info_after, output_path="output.webp", 
                 game_type=None, frame_duration=100, last_frame_multiplier=1.0,
                 custom_overlay_kwargs=None, show_win_text=True,
                 font_scale=1.0, avatar_size=85, overlay_frames=1,
                 show_bet_amount=True, win_text_height=-1):

        icons = self._preload_resources()
        
        avatar = self.resource_cache.get_image(
            avatar_path, 
            resize=(avatar_size, avatar_size),
            convert_mode="RGBA"
        )
        
        try:
            bg_image = self.resource_cache.get_image(bg_path, convert_mode="RGBA")
        except Exception as e:
            logger.error(f"[AnimationGenerator] Error loading background: {e}")
            bg_image = None
        
        total_frames = self.lazy_loader.get_frame_count(anim_path)
        is_animated = total_frames > 1
        
        if total_frames <= 75:
            frame_skip = 1
        elif total_frames <= 100:
            frame_skip = 2 
        elif total_frames <= 150:
            frame_skip = 3
        else:
            frame_skip = 4
        
        included_frames = list(range(0, total_frames, frame_skip))
        
        if is_animated and (total_frames - 1) not in included_frames:
            included_frames.append(total_frames - 1)
        
        frames = self._load_animation_frames_batch(anim_path, included_frames)
        
        if not frames:
            logger.error("[AnimationGenerator] No frames loaded!")
            return None

        win_value = user_info_after.get("win", 0)
        is_win = win_value > 0
        
        overlay_before = self._create_avatar_overlay(
            avatar_img=avatar,
            user_info=user_info_before,
            bet_icon=icons['bet_icon'],
            balance_icon=icons['balance_icon'],
            is_after=False,
            font_scale=font_scale,
            avatar_size=avatar_size,
            is_win=False,
            show_bet_amount=show_bet_amount
        )
        
        overlay_after = self._create_avatar_overlay(
            avatar_img=avatar,
            user_info=user_info_after,
            bet_icon=icons['bet_icon'],
            balance_icon=icons['balance_icon'],
            is_after=True,
            user_info_before=user_info_before,
            font_scale=font_scale,
            avatar_size=avatar_size,
            is_win=is_win,
            show_bet_amount=show_bet_amount
        )
        
        win_text_img = None
        if show_win_text:
            win_value = user_info_after["win"]
            
            if win_value > 0:
                label, color = "WIN!", self.colors['success']
            elif win_value < 0:
                label, color = "LOSE!", self.colors['danger']
            else:
                label, color = "DRAW!", (200, 200, 200, 255)
            
            win_text = f"{label} ${abs(win_value):,}"
            
            if game_type not in ["case", "hourly", "math"]:
                base_font_size = frames[0].size[0] // 12 if frames else 48
                win_text_img = self._get_cached_win_text(win_text, base_font_size, color)
        
        custom_overlay_data = None
        if game_type and game_type in self.custom_overlay_providers:
            custom_overlay_kwargs = custom_overlay_kwargs or {}
            
            if is_animated and len(included_frames) > 1:
                custom_overlay_data = []
                for i, frame_idx in enumerate(included_frames):
                    overlay = self.get_custom_overlay(
                        game_type=game_type,
                        frame_index=i,
                        total_frames=len(included_frames),
                        frame_idx=frame_idx,
                        **custom_overlay_kwargs
                    )
                    custom_overlay_data.append(overlay)
            else:
                custom_overlay_data = self.get_custom_overlay(
                    game_type=game_type,
                    frame_index=0,
                    **custom_overlay_kwargs
                )
        
        all_processed_frames = []
        durations = []
        
        switch_frame_idx = len(included_frames) - overlay_frames
        
        for i, frame_idx in enumerate(included_frames):
            if i < switch_frame_idx or not is_animated:
                current_overlay = overlay_before
                current_win_text = None
            else:
                current_overlay = overlay_after
                current_win_text = win_text_img if show_win_text else None
            
            current_custom_overlay = None
            if custom_overlay_data:
                if isinstance(custom_overlay_data, list) and i < len(custom_overlay_data):
                    current_custom_overlay = custom_overlay_data[i]
                else:
                    current_custom_overlay = custom_overlay_data
            
            processed = self._process_single_frame(
                frames[i],
                current_overlay,
                current_win_text,
                bg_image,
                current_custom_overlay,
                win_text_height=win_text_height
            )
            
            all_processed_frames.append(processed)
            
            is_last_frame = (frame_idx == total_frames - 1)
            duration = int(frame_duration * last_frame_multiplier) if is_last_frame else frame_duration
            durations.append(duration)
        
        if is_animated and len(all_processed_frames) > 1:
            all_processed_frames[0].save(
                output_path,
                save_all=True,
                append_images=all_processed_frames[1:],
                duration=durations,
                loop=0,
                format="WEBP",
                quality=25,
                method=3,
                lossless=False,
            )
        else:
            all_processed_frames[0].save(output_path, format="WEBP", quality=80, method=5)
        
        return output_path

    def generate_static(self, image_path, avatar_path, bg_path, user_info, output_path="output.webp", 
                        game_type=None, custom_overlay_kwargs=None, show_win_text=True, is_after=True,
                        font_scale=1.0, avatar_size=85, show_bet_amount=True, is_win=False, win_text_height=-1):
        
        icons = self._preload_resources()
        
        avatar = self.resource_cache.get_image(
            avatar_path,
            resize=(avatar_size, avatar_size),
            convert_mode="RGBA"
        )
        
        if hasattr(image_path, 'read'):
            base_img = Image.open(image_path).convert("RGBA")
        else:
            base_img = self.resource_cache.get_image(image_path, convert_mode="RGBA")
        
        overlay_data = self._create_avatar_overlay(
            avatar_img=avatar,
            user_info=user_info,
            bet_icon=icons['bet_icon'],
            balance_icon=icons['balance_icon'],
            is_after=is_after,
            font_scale=font_scale,
            avatar_size=avatar_size,
            is_win=is_win,
            show_bet_amount=show_bet_amount
        )
        
        overlay_img = overlay_data['image']
        frame_width, frame_height = base_img.size
        
        if overlay_img.width != frame_width or overlay_img.height > frame_height:
            params = overlay_data.get('parameters', {})
            font_scale_param = params.get('font_scale', 1.0)
            avatar_size_param = params.get('avatar_size', 85)
            overlay_height = params.get('overlay_height', 110)
            
            overlay_height = min(overlay_height, frame_height - 10)
            
            new_overlay = Image.new('RGBA', (frame_width, overlay_height), (0, 0, 0, 0))
            
            avatar_x_old, avatar_y_old, _ = overlay_data.get('avatar_position', (0, 0, avatar_size_param))
            avatar_x_new = frame_width - avatar_size_param
            avatar_y_new = overlay_height - avatar_size_param
            
            avatar_region = overlay_img.crop((
                avatar_x_old, avatar_y_old,
                avatar_x_old + avatar_size_param, avatar_y_old + avatar_size_param
            ))
            new_overlay.paste(avatar_region, (avatar_x_new, avatar_y_new))
            
            left_section_info = overlay_data.get('left_section_info', {})
            text_start_x = left_section_info.get('text_start_x', int(2 * font_scale_param))
            actual_left_width = left_section_info.get('actual_left_width', 260)
            
            crop_width = min(actual_left_width, overlay_img.width)
            crop_height = min(overlay_height, overlay_img.height)
            
            text_region = overlay_img.crop((0, 0, crop_width, crop_height))
            new_overlay.paste(text_region, (text_start_x, 0), text_region)
            
            overlay_img = new_overlay
        
        custom_overlay = None
        if game_type and game_type in self.custom_overlay_providers:
            custom_overlay_kwargs = custom_overlay_kwargs or {}
            custom_overlay = self.get_custom_overlay(
                game_type=game_type,
                frame_index=0,
                **custom_overlay_kwargs
            )
        
        final_img = Image.new("RGBA", (frame_width, frame_height))
        
        try:
            bg_image = self.resource_cache.get_image(bg_path, convert_mode="RGBA")
            bg_resized = self._get_cached_background(bg_image, (frame_width, frame_height))
            if bg_resized:
                final_img.paste(bg_resized, (0, 0))
        except:
            draw = ImageDraw.Draw(final_img)
            draw.rectangle([0, 0, frame_width, frame_height], 
                        fill=(20, 20, 30))
        
        final_img.paste(base_img, (0, 0), base_img)
        
        overlay_y = frame_height - overlay_img.height
        final_img.alpha_composite(overlay_img, (0, overlay_y))

        if show_win_text and game_type not in ["case", "hourly", "math"]:
            win_value = user_info.get("win", 0)
            
            if win_value > 0:
                label, color = "WIN!", self.colors['success']
            elif win_value < 0:
                label, color = "LOSE!", self.colors['danger']
            else:
                label, color = "DRAW!", (200, 200, 200, 255)
            
            win_text = f"{label} ${abs(win_value):,}"
            
            base_font_size = frame_width // 12
            win_text_img = self._get_cached_win_text(win_text, base_font_size, color)
            
            win_text_x = (frame_width - win_text_img.width) // 2
            if win_text_height != -1:
                win_text_y = win_text_height
            else:
                win_text_y = (frame_height - win_text_img.height) // 2
            final_img.alpha_composite(win_text_img, (win_text_x, win_text_y))
        
        if custom_overlay and 'image' in custom_overlay:
            overlay_pos = custom_overlay.get('position', (0, 0))
            if (custom_overlay['image'].width <= final_img.width and 
                custom_overlay['image'].height <= final_img.height):
                final_img.alpha_composite(custom_overlay['image'], overlay_pos)
        
        final_img.save(output_path, format="WEBP", quality=90, optimize=True)
        
        return output_path

    def _create_avatar_overlay(self, avatar_img, user_info, bet_icon=None, balance_icon=None, 
                                    is_after=False, user_info_before=None, 
                                    font_scale=1.0, avatar_size=95, is_win=False,
                                    show_bet_amount=True):

        username = user_info.get('username', '')
        balance = user_info.get('balance', 0)
        bet = user_info.get('bet', 0)
        level = user_info.get('level', 1)
        level_progress_percent = user_info.get('level_progress', 0.0) * 100
        
        scaled_font_size = int(20 * font_scale)
        scaled_username_size = int(18 * font_scale)
        scaled_icon_size = int(24 * font_scale)
        
        bet_img = None
        bet_bg_width = 0
        if show_bet_amount:
            bet_text = f"{bet:,}"
            bet_color = self.colors['warning'] if not is_after or is_win or user_info.get('win', 0) > user_info.get('amount', 0) else self.colors['danger']
            
            bet_img = self.text_renderer.render_text_to_image(
                text=bet_text,
                font_path=self._default_font_path,
                font_size=scaled_font_size,
                color=bet_color,
                stroke_width=max(1, int(1 * font_scale)),
                stroke_color=(0, 0, 0, 150)
            )
            
            icon_text_spacing = int(4 * font_scale)
            bet_bg_width = scaled_icon_size + bet_img.width + icon_text_spacing + int(4 * font_scale)
        
        if is_after and user_info_before is not None:
            balance_before = user_info_before.get('balance', 0)
            balance_color = self.colors['success'] if balance > balance_before else \
                        self.colors['danger'] if balance < balance_before else \
                        self.colors['text_light']
        elif user_info.get('win', 0) > 0:
            balance_color = self.colors['success']
        elif user_info.get('win', 0) < 0:
            balance_color = self.colors['danger']
        else:
            balance_color = self.colors['text_light']
        
        balance_text = f"{balance:,}"
        balance_img = self.text_renderer.render_text_to_image(
            text=balance_text,
            font_path=self._default_font_path,
            font_size=scaled_font_size,
            color=balance_color,
            stroke_width=max(1, int(1 * font_scale)),
            stroke_color=(0, 0, 0, 150)
        )
        
        username_img = None
        if username:
            username_img = self.text_renderer.render_text_to_image(
                text=username,
                font_path=self._default_font_path,
                font_size=scaled_username_size,
                color=self.colors['text_light'],
                stroke_width=max(1, int(1 * font_scale)),
                stroke_color=(0, 0, 0, 120)
            )
        
        icon_text_spacing = int(4 * font_scale)
        
        balance_bg_width = scaled_icon_size + balance_img.width + icon_text_spacing + int(4 * font_scale)
        username_bg_width = username_img.width + int(8 * font_scale) if username_img else 0

        widths_to_check = [balance_bg_width, username_bg_width]
        if show_bet_amount and bet_img:
            widths_to_check.append(bet_bg_width)
        
        actual_left_width = max(widths_to_check) if widths_to_check else 0
        
        element_height = int(28 * font_scale)
        username_height = int(26 * font_scale) if username_img else 0
        element_spacing = int(2 * font_scale)
        
        total_width = actual_left_width + avatar_size + int(5 * font_scale)
        
        num_elements = 1 + (1 if username_img else 0) + (1 if show_bet_amount else 0)
        total_elements_height = (num_elements * element_height) + max(0, (num_elements - 1) * element_spacing)
        if username_img:
            if show_bet_amount:
                total_elements_height = (3 * element_height) + username_height + (2 * element_spacing)
            else:
                total_elements_height = (2 * element_height) + username_height + element_spacing
        
        overlay_height = max(
            total_elements_height + int(10 * font_scale),
            avatar_size + int(30 * font_scale)
        )
        
        overlay = Image.new('RGBA', (total_width, overlay_height), (0, 0, 0, 0))
        
        avatar_x = total_width - avatar_size
        avatar_y = overlay_height - avatar_size
        
        if not hasattr(self, '_avatar_mask_cache'):
            self._avatar_mask_cache = {}
        
        mask_key = f"mask_{avatar_size}"
        if mask_key not in self._avatar_mask_cache:
            avatar_mask = Image.new('L', (avatar_size, avatar_size), 0)
            mask_draw = ImageDraw.Draw(avatar_mask)
            mask_draw.rounded_rectangle((0, 0, avatar_size, avatar_size), radius=5, fill=255)
            self._avatar_mask_cache[mask_key] = avatar_mask
        
        avatar_mask = self._avatar_mask_cache[mask_key]
        avatar_resized = avatar_img.resize((avatar_size, avatar_size))
        avatar_rounded = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        avatar_rounded.paste(avatar_resized, (0, 0), avatar_mask)
        overlay.paste(avatar_rounded, (avatar_x, avatar_y), avatar_mask)
        
        level_font_size = int(18 * font_scale)
        level_img = self.text_renderer.render_text_to_image(
            text=str(level),
            font_path=self._default_font_path,
            font_size=level_font_size,
            color=(255, 255, 255, 255),
            stroke_width=max(2, int(2 * font_scale)),
            stroke_color=(0, 0, 0, 200)
        )
        
        level_margin_right = int(5 * font_scale)
        level_margin_top = int(5 * font_scale)
        level_x = avatar_x + avatar_size - level_img.width - level_margin_right
        level_y = avatar_y + level_margin_top
        
        overlay.alpha_composite(level_img, (level_x, level_y))

        progress_bar_width = avatar_size - int(15 * font_scale)
        progress_bar_height = int(6 * font_scale)
        
        progress_bar_x = avatar_x + (avatar_size - progress_bar_width) // 2
        progress_bar_y = avatar_y + avatar_size - progress_bar_height - int(8 * font_scale)
        
        draw = ImageDraw.Draw(overlay)
        
        draw.rectangle(
            [progress_bar_x, progress_bar_y, 
            progress_bar_x + progress_bar_width, progress_bar_y + progress_bar_height],
            fill=(255, 255, 255, 200)
        )
        
        bg_x = progress_bar_x + int(1 * font_scale)
        bg_y = progress_bar_y + int(1 * font_scale)
        bg_width = progress_bar_width - int(2 * font_scale)
        bg_height = progress_bar_height - int(2 * font_scale)
        
        if bg_width > 0 and bg_height > 0:
            draw.rectangle(
                [bg_x, bg_y, bg_x + bg_width, bg_y + bg_height],
                fill=(40, 40, 60, 220)
            )
            
            filled_width = int(bg_width * (level_progress_percent / 100))
            if filled_width > 0:
                draw.rectangle(
                    [bg_x, bg_y, bg_x + filled_width, bg_y + bg_height],
                    fill=(80, 160, 255, 220)
                )
        
        text_start_x = int(2 * font_scale)
        current_y = overlay_height - int(5 * font_scale)
        bg_radius = int(4 * font_scale)
        
        blur_cache = {}
        
        if username_img:
            current_y -= username_height
            
            username_bg_key = f"username_bg_{username_bg_width}_{username_height}"
            if username_bg_key not in blur_cache:
                username_bg = Image.new('RGBA', (username_bg_width, username_height), (0, 0, 0, 180))
                username_bg_draw = ImageDraw.Draw(username_bg)
                username_bg_draw.rounded_rectangle(
                    [0, 0, username_bg_width-1, username_height-1], 
                    radius=bg_radius, 
                    fill=(0, 0, 0, 180)
                )
                blur_cache[username_bg_key] = username_bg
            
            overlay.alpha_composite(blur_cache[username_bg_key], (text_start_x, current_y))
            
            text_x = text_start_x + (username_bg_width - username_img.width) // 2
            text_offset_y = (username_height - username_img.height) // 2
            overlay.alpha_composite(username_img, (text_x, current_y + text_offset_y))
            
            current_y -= element_spacing
        
        current_y -= element_height
        
        balance_bg_key = f"balance_bg_{balance_bg_width}_{element_height}"
        if balance_bg_key not in blur_cache:
            balance_bg = Image.new('RGBA', (balance_bg_width, element_height), (0, 0, 0, 180))
            balance_bg_draw = ImageDraw.Draw(balance_bg)
            balance_bg_draw.rounded_rectangle(
                [0, 0, balance_bg_width-1, element_height-1], 
                radius=bg_radius, 
                fill=(0, 0, 0, 180)
            )
            blur_cache[balance_bg_key] = balance_bg
        
        overlay.alpha_composite(blur_cache[balance_bg_key], (text_start_x, current_y))
        
        if balance_icon:
            balance_icon_resized = balance_icon.resize((scaled_icon_size, scaled_icon_size))
            icon_offset_y = (element_height - scaled_icon_size) // 2
            overlay.alpha_composite(balance_icon_resized, 
                                (text_start_x + int(2 * font_scale), 
                                current_y + icon_offset_y))
        
        text_offset_y = (element_height - balance_img.height) // 2
        overlay.alpha_composite(balance_img, 
                            (text_start_x + scaled_icon_size + int(2 * font_scale), 
                            current_y + text_offset_y))
        
        if show_bet_amount and bet_img:
            current_y -= element_height + element_spacing
            
            bet_bg_key = f"bet_bg_{bet_bg_width}_{element_height}"
            if bet_bg_key not in blur_cache:
                bet_bg = Image.new('RGBA', (bet_bg_width, element_height), (0, 0, 0, 180))
                bet_bg_draw = ImageDraw.Draw(bet_bg)
                bet_bg_draw.rounded_rectangle(
                    [0, 0, bet_bg_width-1, element_height-1], 
                    radius=bg_radius, 
                    fill=(0, 0, 0, 180)
                )
                blur_cache[bet_bg_key] = bet_bg
            
            overlay.alpha_composite(blur_cache[bet_bg_key], (text_start_x, current_y))
            
            if bet_icon:
                bet_icon_resized = bet_icon.resize((scaled_icon_size, scaled_icon_size))
                icon_offset_y = (element_height - scaled_icon_size) // 2
                overlay.alpha_composite(bet_icon_resized, 
                                    (text_start_x + int(2 * font_scale), 
                                    current_y + icon_offset_y))
            
            text_offset_y = (element_height - bet_img.height) // 2
            overlay.alpha_composite(bet_img, 
                                (text_start_x + scaled_icon_size + int(2 * font_scale), 
                                current_y + text_offset_y))
        
        return {
            'image': overlay,
            'total_size': (total_width, overlay_height),
            'is_on_animation': True,
            'avatar_position': (avatar_x, avatar_y, avatar_size),
            'progress_bar_position': (progress_bar_x, progress_bar_y, progress_bar_width, progress_bar_height),
            'left_section_info': {
                'text_start_x': text_start_x,
                'actual_left_width': actual_left_width,
                'font_scale': font_scale,
            },
            'parameters': {
                'font_scale': font_scale,
                'avatar_size': avatar_size,
                'overlay_height': overlay_height,
                'show_bet_amount': show_bet_amount
            }
        }

    def generate_last_frame_static(self, anim_path, avatar_path, bg_path, 
                                user_info_after, output_path, 
                                game_type=None, custom_overlay_kwargs=None,
                                show_win_text=True,
                                font_scale=1.0, avatar_size=85,
                                show_bet_amount=True, win_text_height=-1):
        
        last_frame = self.lazy_loader.get_last_frame(anim_path, use_cache=True)
        
        if not last_frame:
            return None
        
        frame_width, frame_height = last_frame.size
        
        import io
        try:
            buffer = io.BytesIO()
            last_frame.save(buffer, format='PNG', optimize=True)
            buffer.seek(0)
            
            if custom_overlay_kwargs is None:
                custom_overlay_kwargs = {}
            custom_overlay_kwargs['frame_width'] = frame_width
            
            result = self.generate_static(
                buffer,
                avatar_path, bg_path, user_info_after, output_path,
                game_type=game_type, 
                custom_overlay_kwargs=custom_overlay_kwargs,
                show_win_text=show_win_text,
                font_scale=font_scale,
                avatar_size=avatar_size,
                show_bet_amount=show_bet_amount,
                win_text_height=win_text_height
            )
            
            return result
        finally:
            buffer.close() if 'buffer' in locals() else None