import os
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
from logger import logger
import time

@dataclass
class GenerationOptions:
    animated: bool = False
    avatar_size: int = 85
    font_scale: float = 1.0
    show_win_text: bool = True
    output_format: str = "WEBP"
    quality: int = 90
    frame_duration: int = 100
    last_frame_multiplier: float = 1.0
    show_bet_amount: bool = True
    win_text_height: int = -1
    custom_overlay_kwargs: Optional[Dict] = None
    
    @classmethod
    def from_kwargs(cls, **kwargs) -> 'GenerationOptions':
        return cls(**{
            k: v for k, v in kwargs.items() 
            if k in cls.__annotations__
        })

@dataclass
class UserInfo:
    user_id: str
    username: str
    balance: float
    win: float = 0.0
    bet: float = 0.0
    is_win: bool = False
    avatar_path: str = ""
    level: int = 1
    level_progress: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict) -> 'UserInfo':
        return cls(
            user_id=str(data.get('user_id', '')),
            username=str(data.get('username', 'Player')),
            balance=float(data.get('balance', 0)),
            win=float(data.get('win', 0)),
            bet=float(data.get('bet', 0)),
            is_win=bool(data.get('is_win', False)),
            avatar_path=str(data.get('avatar_path', '')),
            level=int(data.get('level', 1)),
            level_progress=float(data.get('level_progress', 0.0))
        )

@dataclass
class GenerationRequest:
    animation_path: str
    background_path: str
    user_before: UserInfo
    user_after: UserInfo
    game_name: str = "Game"
    output_path: Optional[str] = None
    cache_path: Optional[str] = None
    options: GenerationOptions = field(default_factory=GenerationOptions)
    timestamp: datetime = field(default_factory=datetime.now)
    request_id: str = field(default_factory=lambda: hashlib.md5(
        str(time.time()).encode()).hexdigest()[:8]
    )
    
    @property
    def avatar_path(self) -> str:
        return self.user_before.avatar_path or self.user_after.avatar_path
    
    @property
    def is_win(self) -> bool:
        return self.user_after.is_win or self.user_after.win > 0
    
    @property
    def win_amount(self) -> float:
        return self.user_after.win
    
    @property
    def bet_amount(self) -> float:
        return self.user_before.bet
    
    def get_effective_output_path(self, default_dir: str) -> str:
        if self.output_path:
            return self.output_path
        
        ext = ".gif" if self.options.animated else f".{self.options.output_format.lower()}"
        filename = f"{self.game_name}_{self.user_before.user_id}_{self.timestamp.strftime('%Y%m%d_%H%M%S')}{ext}"
        
        if self.cache_path:
            return os.path.join(self.cache_path, filename)
        
        return os.path.join(default_dir, filename)
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        if not os.path.exists(self.animation_path):
            return False, f"Animation path not found: {self.animation_path}"
        if not os.path.exists(self.background_path):
            return False, f"Background path not found: {self.background_path}"
        
        avatar_path = self.avatar_path
        if avatar_path and not os.path.exists(avatar_path):
            return False, f"Avatar path not found: {avatar_path}"
        
        if self.user_before.user_id != self.user_after.user_id:
            return False, "User IDs don't match"
        
        return True, None

class TextRenderer:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized') or not self._initialized:
            self.default_fonts = {}
            self.icon_cache: Dict[str, Image.Image] = {}
            self._load_default_fonts()
            self._load_icons()
            self._initialized = True
    
    def _load_default_fonts(self):
        font_sizes = [12, 14, 16, 18, 20, 24, 28, 32, 36, 40, 48, 56, 64]
        
        for size in font_sizes:
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", size)
            except:
                font = ImageFont.load_default()
            
            self.default_fonts[size] = font
    
    def _load_icons(self):
        try:
            app_path = os.path.dirname(__file__)
            assets_path = os.path.join(app_path, "assets")
            
            bet_icon_path = os.path.join(assets_path, "bet_icon.png")
            balance_icon_path = os.path.join(assets_path, "balance_icon.png")

            if os.path.exists(bet_icon_path):
                bet_icon = Image.open(bet_icon_path).convert("RGBA")
                bet_icon = bet_icon.resize((24, 24), Image.Resampling.LANCZOS)
                self.icon_cache['bet'] = bet_icon
            
            if os.path.exists(balance_icon_path):
                balance_icon = Image.open(balance_icon_path).convert("RGBA")
                balance_icon = balance_icon.resize((24, 24), Image.Resampling.LANCZOS)
                self.icon_cache['balance'] = balance_icon
                
        except Exception as e:
            self.icon_cache['bet'] = Image.new('RGBA', (24, 24), (0, 0, 0, 0))
            self.icon_cache['balance'] = Image.new('RGBA', (24, 24), (0, 0, 0, 0))
    
    def get_font(self, font_size: int) -> ImageFont.FreeTypeFont:
        if font_size in self.default_fonts:
            return self.default_fonts[font_size]
        
        closest_size = min(self.default_fonts.keys(), key=lambda x: abs(x - font_size))
        return self.default_fonts[closest_size]
    
    def render_text(self, text: str, font_size: int, 
                   color: Tuple[int, int, int, int] = (240, 240, 240, 255),
                   stroke_width: int = 0,
                   stroke_color: Tuple[int, int, int, int] = (0, 0, 0, 255),
                   shadow: bool = False,
                   shadow_color: Tuple[int, int, int, int] = (0, 0, 0, 180),
                   shadow_offset: Tuple[int, int] = (2, 2)) -> Image.Image:
        font = self.get_font(font_size)
        
        draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        if shadow:
            text_width += abs(shadow_offset[0]) * 2
            text_height += abs(shadow_offset[1]) * 2
        
        img = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        x_offset = abs(shadow_offset[0]) if shadow and shadow_offset[0] < 0 else 0
        y_offset = abs(shadow_offset[1]) if shadow and shadow_offset[1] < 0 else 0
        
        text_position = (x_offset, y_offset)
        
        if shadow:
            shadow_pos = (x_offset + shadow_offset[0], y_offset + shadow_offset[1])
            draw.text(shadow_pos, text, font=font, fill=shadow_color, 
                     stroke_width=stroke_width, stroke_fill=stroke_color)
        
        draw.text(text_position, text, font=font, fill=color,
                 stroke_width=stroke_width, stroke_fill=stroke_color)
        
        return img

class AnimationGenerator:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not AnimationGenerator._initialized:
            self.text_renderer = TextRenderer()
            self.colors = {
                'text_light': (240, 240, 240, 255),
                'success': (70, 180, 90, 255),
                'danger': (220, 80, 80, 255),
                'warning': (220, 160, 60, 255),
                'bet': (220, 160, 60, 255),
                'balance': (240, 240, 240, 255)
            }
            self.custom_overlay_providers: Dict[str, callable] = {}
            self.results_folder = None
            AnimationGenerator._initialized = True
    
    def register_custom_overlay_provider(self, game_name: str, provider_func: callable):
        self.custom_overlay_providers[game_name] = provider_func
                
    def generate(self, request: GenerationRequest) -> Tuple[Optional[str], Optional[str]]:
        try:
            is_valid, error_msg = request.validate()
            if not is_valid:
                return None, f"Invalid request: {error_msg}"
            
            base_frames = self._load_animation_frames(request.animation_path)
            if not base_frames:
                return None, "Can not load animation frames"
            
            frame_width = base_frames[0].width if base_frames else 400

            options = request.options
            frame_indices = self._get_frame_indices(
                len(base_frames), 
                options.animated
            )
            
            avatar_img = self._load_and_resize_image(
                request.avatar_path, 
                (options.avatar_size, options.avatar_size)
            )
            
            bg_img = self._load_image(request.background_path)
            
            colors = self._calculate_colors(request)
            
            win_text_img = None
            if options.show_win_text and request.win_amount != 0:
                win_text_img = self._create_win_text(request, colors, options)
            
            user_overlay_before = self._create_user_overlay(
                request.user_before, avatar_img, options, frame_width
            ) if avatar_img else None
            
            user_overlay_after = self._create_user_overlay(
                request.user_after, avatar_img, options, frame_width
            ) if avatar_img else None
            
            custom_overlay_dict = None
            if request.game_name in self.custom_overlay_providers:
                custom_kwargs = options.custom_overlay_kwargs or {}
                custom_kwargs.update({
                    'total_frames': len(frame_indices),
                    'frame_width': frame_width,
                    'request': request
                })
                
                custom_overlay_dict = self.custom_overlay_providers[request.game_name](**custom_kwargs)
            
            processed_frames = []
            
            for i, frame_idx in enumerate(frame_indices):
                frame = base_frames[frame_idx]
                
                if options.animated:
                    if i < len(frame_indices) - 1:
                        user_overlay = user_overlay_before
                        show_win_text = False
                        custom_overlay = custom_overlay_dict.get('before') if custom_overlay_dict else None
                    else:
                        user_overlay = user_overlay_after
                        show_win_text = True
                        custom_overlay = custom_overlay_dict.get('after') if custom_overlay_dict else None
                else:
                    user_overlay = user_overlay_after
                    show_win_text = True
                    custom_overlay = custom_overlay_dict.get('after') if custom_overlay_dict else None
                
                processed_frame = self._process_single_frame(
                    frame=frame,
                    user_overlay=user_overlay,
                    win_text=win_text_img if show_win_text else None,
                    bg_img=bg_img,
                    custom_overlay=custom_overlay,
                    options=options
                )
                
                processed_frames.append(processed_frame)
                
                if options.animated and i == len(frame_indices) - 1 and options.last_frame_multiplier > 1:
                    for _ in range(int(options.last_frame_multiplier) - 1):
                        processed_frames.append(processed_frame.copy())
            
            output_dir = self.results_folder
            
            output_path = request.get_effective_output_path(output_dir)
            
            if options.animated:
                success = self._save_animation(processed_frames, output_path, options)
            else:
                success = self._save_static(
                    processed_frames[-1] if processed_frames else None,
                    output_path,
                    options
                )
            
            if success:
                return output_path, None
            else:
                return None, "Failed to save file"
                
        except Exception as e:
            return None, f"Animation generation error: {str(e)}"
        
    def _load_image(self, path: str) -> Optional[Image.Image]:
        if not path or not os.path.exists(path):
            return None
        
        try:
            return Image.open(path).convert("RGBA")
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None
    
    def _load_and_resize_image(self, path: str, size: Tuple[int, int]) -> Optional[Image.Image]:
        img = self._load_image(path)
        if img and size:
            return img.resize(size, Image.Resampling.LANCZOS)
        return img
    
    def _load_animation_frames(self, anim_path: str) -> List[Image.Image]:
        try:
            frames = []
            with Image.open(anim_path) as img:
                if hasattr(img, 'n_frames') and img.n_frames > 1:
                    for frame in ImageSequence.Iterator(img):
                        frames.append(frame.copy().convert("RGBA"))
                else:
                    frames.append(img.copy().convert("RGBA"))
            
            return frames
        except Exception as e:
            print(f"Error loading animation {anim_path}: {e}")
            return []
    
    def _get_frame_indices(self, total_frames: int, animated: bool) -> List[int]:
        if total_frames == 0:
            return []
        
        if animated:
            return list(range(total_frames))
        else:
            return [total_frames - 1]
    
    def _calculate_colors(self, request: GenerationRequest) -> Dict[str, Tuple]:
        colors = {
            'balance': self.colors['balance'],
            'bet': self.colors['bet']
        }
        
        win_amount = request.win_amount
        if win_amount > 0:
            colors['win_text'] = self.colors['success']
        elif win_amount < 0:
            colors['win_text'] = self.colors['danger']
        else:
            colors['win_text'] = (200, 200, 200, 255)
        
        return colors
                    
    def _create_user_overlay(self, user_info: UserInfo, avatar_img: Image.Image, 
                        options: GenerationOptions, frame_width: int) -> Dict:
        if not avatar_img:
            return None
        
        avatar_size = options.avatar_size
        font_scale = options.font_scale
        
        level = getattr(user_info, 'level', 1)
        level_progress = getattr(user_info, 'level_progress', 0.0)
        
        if user_info.is_win:
            balance_color = self.colors['success']
        elif user_info.win < 0:
            balance_color = self.colors['danger']
        else:
            balance_color = self.colors['balance']
        
        bet_color = self.colors['bet']
        text_color = self.colors['text_light']
        
        bet_icon = self.text_renderer.icon_cache.get('bet')
        balance_icon = self.text_renderer.icon_cache.get('balance')
        icon_size = 20
        
        username_font_size = int(18 * font_scale)
        balance_font_size = int(20 * font_scale)
        bet_font_size = int(20 * font_scale)
        level_font_size = int(18 * font_scale)
        
        username_text = self.text_renderer.render_text(
            text=user_info.username,
            font_size=username_font_size,
            color=text_color,
            stroke_width=max(2, int(2 * font_scale)),
            stroke_color=(0, 0, 0, 255)
        )
        
        balance_text = self.text_renderer.render_text(
            text=f"{user_info.balance:.0f}", 
            font_size=balance_font_size,
            color=balance_color,
            stroke_width=max(2, int(2 * font_scale)),
            stroke_color=(0, 0, 0, 255)
        )
        
        bet_text_img = None
        if options.show_bet_amount and user_info.bet > 0:
            bet_text_img = self.text_renderer.render_text(
                text=f"{user_info.bet:.0f}",
                font_size=bet_font_size,
                color=bet_color,
                stroke_width=max(2, int(2 * font_scale)),
                stroke_color=(0, 0, 0, 255)
            )
        
        level_text_img = self.text_renderer.render_text(
            text=str(level),
            font_size=level_font_size,
            color=(255, 255, 255, 255),
            stroke_width=max(3, int(3 * font_scale)),
            stroke_color=(0, 0, 0, 255)
        )
        
        if bet_icon:
            bet_icon = bet_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        if balance_icon:
            balance_icon = balance_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        
        icon_text_spacing = int(8 * font_scale)
        vertical_spacing = int(8 * font_scale)
        
        text_margin_left = int(5 * font_scale)
        bottom_margin = int(5 * font_scale)
        
        overlay_height = avatar_size + int(30 * font_scale)
        
        text_heights = []
        total_text_height = 0
        
        if bet_text_img:
            bet_height = max(icon_size, bet_text_img.height)
            text_heights.append(('bet', bet_height))
            total_text_height += bet_height
        
        if balance_text:
            balance_height = max(icon_size, balance_text.height)
            text_heights.append(('balance', balance_height))
            total_text_height += balance_height
        
        if username_text:
            text_heights.append(('username', username_text.height))
            total_text_height += username_text.height
        
        if len(text_heights) > 1:
            total_text_height += (len(text_heights) - 1) * vertical_spacing
        
        text_area_needed = total_text_height + int(15 * font_scale)
        overlay_height = max(overlay_height, text_area_needed)
        
        overlay = Image.new('RGBA', (frame_width, overlay_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        avatar_x = frame_width - avatar_size
        avatar_y = overlay_height - avatar_size
        
        avatar_mask = Image.new('L', (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(avatar_mask)
        mask_draw.rounded_rectangle((0, 0, avatar_size, avatar_size), radius=5, fill=255)
        
        avatar_resized = avatar_img.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
        avatar_rounded = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        avatar_rounded.paste(avatar_resized, (0, 0), avatar_mask)
        overlay.paste(avatar_rounded, (avatar_x, avatar_y), avatar_mask)
        
        level_margin_right = int(5 * font_scale)
        level_margin_top = int(5 * font_scale)
        level_x = avatar_x + avatar_size - level_text_img.width - level_margin_right
        level_y = avatar_y + level_margin_top
        overlay.alpha_composite(level_text_img, (level_x, level_y))
        
        progress_bar_width = avatar_size - int(15 * font_scale)
        progress_bar_height = int(6 * font_scale)
        progress_bar_x = avatar_x + (avatar_size - progress_bar_width) // 2
        progress_bar_y = avatar_y + avatar_size - progress_bar_height - int(8 * font_scale)
        
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
            
            filled_width = int(bg_width * level_progress)
            if filled_width > 0:
                draw.rectangle(
                    [bg_x, bg_y, bg_x + filled_width, bg_y + bg_height],
                    fill=(80, 160, 255, 220)
                )
        
        text_x = text_margin_left
        current_y = overlay_height - bottom_margin
        
        if username_text:
            username_y = current_y - username_text.height
            overlay.alpha_composite(username_text, (text_x, username_y))
            current_y = username_y - vertical_spacing
        
        if balance_text:
            element_height = max(icon_size, balance_text.height)
            balance_y = current_y - element_height
            
            if balance_icon:
                icon_y = balance_y + (element_height - icon_size) // 2
                overlay.alpha_composite(balance_icon, (text_x, icon_y))
                balance_text_x = text_x + icon_size + icon_text_spacing
            else:
                balance_text_x = text_x
            
            text_y = balance_y + (element_height - balance_text.height) // 2
            overlay.alpha_composite(balance_text, (balance_text_x, text_y))
            
            current_y = balance_y - vertical_spacing
        
        if bet_text_img and options.show_bet_amount:
            element_height = max(icon_size, bet_text_img.height)
            bet_y = current_y - element_height
            
            if bet_icon:
                icon_y = bet_y + (element_height - icon_size) // 2
                overlay.alpha_composite(bet_icon, (text_x, icon_y))
                bet_text_x = text_x + icon_size + icon_text_spacing
            else:
                bet_text_x = text_x
            
            text_y = bet_y + (element_height - bet_text_img.height) // 2
            overlay.alpha_composite(bet_text_img, (bet_text_x, text_y))
        
        return {
            'image': overlay,
            'position': (0, 0),
            'type': 'user_overlay',
            'is_on_animation': True,
            'avatar_position': (avatar_x, avatar_y, avatar_size),
            'text_position': (text_x, current_y),
            'parameters': {
                'font_scale': font_scale,
                'avatar_size': avatar_size,
                'overlay_height': overlay_height,
                'show_bet_amount': options.show_bet_amount,
                'frame_width': frame_width
            }
        }

    def _create_win_text(self, request: GenerationRequest, colors: Dict,
                        options: GenerationOptions) -> Optional[Image.Image]:
        if request.win_amount > 0:
            text = f"WIN! ${request.win_amount:.0f}"
        else:
            text = f"LOSE! ${abs(request.win_amount):.0f}"
        
        font_size = int(48 * options.font_scale)
        
        return self.text_renderer.render_text(
            text=text,
            font_size=font_size,
            color=colors['win_text'],
            stroke_width=2,
            stroke_color=(0, 0, 0, 255),
            shadow=True,
            shadow_color=(0, 0, 0, 180),
            shadow_offset=(2, 2)
        )

    def _process_single_frame(self, frame: Image.Image, user_overlay: Optional[Dict],
                            win_text: Optional[Image.Image], bg_img: Optional[Image.Image],
                            custom_overlay: Optional[Dict], options: GenerationOptions) -> Image.Image:
        result = frame.copy()
        
        if bg_img:
            try:
                bg_resized = bg_img.resize(result.size, Image.Resampling.LANCZOS)
                result = Image.alpha_composite(bg_resized.convert("RGBA"), result)
            except Exception as e:
                print(f"Error applying background: {e}")
        
        if custom_overlay and custom_overlay.get('image'):
            custom_img = custom_overlay['image']
            custom_pos = custom_overlay.get('position', (0, 0))
            
            if custom_overlay.get('per_frame', True) or options.animated:
                result.alpha_composite(custom_img, custom_pos)
        
        if win_text:
            win_x = (result.width - win_text.width) // 2
            if options.win_text_height > 0:
                win_y = options.win_text_height
            else:
                win_y = 20
            
            result.alpha_composite(win_text, (win_x, win_y))
        
        if user_overlay and user_overlay.get('image'):
            overlay_img = user_overlay['image']
            
            if overlay_img.width != result.width:
                scale_factor = result.width / overlay_img.width
                new_width = result.width
                new_height = int(overlay_img.height * scale_factor)
                overlay_img = overlay_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            overlay_x = 0 
            overlay_y = result.height - overlay_img.height
            
            result.alpha_composite(overlay_img, (overlay_x, overlay_y))
        
        return result
    
    def _save_animation(self, frames: List[Image.Image], output_path: str,
                    options: GenerationOptions) -> bool:
        if not frames:
            return False
        
        try:
            frames[0].save(
                output_path,
                format='WEBP',
                save_all=True,
                append_images=frames[1:],
                duration=options.frame_duration,
                loop=0,
                quality=options.quality
            )
            return True
        except Exception as e:
            logger.error(f"Error saving animation: {e}")
            return False

    def _save_static(self, frame: Optional[Image.Image], output_path: str,
                    options: GenerationOptions) -> bool:
        if not frame:
            return False
        
        try:
            frame.save(
                output_path,
                format=options.output_format,
                quality=options.quality
            )
            return True
        except Exception as e:
            logger.error(f"Error saving static image: {e}")
            return False