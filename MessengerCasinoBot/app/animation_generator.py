import os
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
from logger import logger
import time
import uuid
import colorsys


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
    final_frames_start_index: int = -1
    win_text_scale: int = -1
    overlay_position: str = 'bottom'

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

        ext = f".{self.options.output_format.lower()}"

        unique_id = str(uuid.uuid4())[:8]
        filename = f"{self.game_name}_{self.user_before.user_id}_{self.timestamp.strftime('%Y%m%d_%H%M%S')}_{unique_id}{ext}"

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
            self._load_default_icons()
            self._initialized = True

    def _load_default_fonts(self):
        font_sizes = [8, 9, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 40, 48, 56, 64]

        for size in font_sizes:
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", size)
            except:
                font = ImageFont.load_default()

            self.default_fonts[size] = font

    def _load_default_icons(self):
        self.reload_default_icons()

    def reload_default_icons(self):
        try:
            app_path = os.path.dirname(__file__)
            assets_path = os.path.join(app_path, "assets")

            bet_icon_path = os.path.join(assets_path, "bet_icon.png")
            balance_icon_path = os.path.join(assets_path, "balance_icon.png")

            if os.path.exists(bet_icon_path):
                bet_icon = Image.open(bet_icon_path).convert("RGBA")
                bet_icon = bet_icon.resize((24, 24), Image.Resampling.LANCZOS)
                self.icon_cache['bet'] = bet_icon
            else:
                self.icon_cache['bet'] = self._create_default_icon('💰')

            if os.path.exists(balance_icon_path):
                balance_icon = Image.open(balance_icon_path).convert("RGBA")
                balance_icon = balance_icon.resize((24, 24), Image.Resampling.LANCZOS)
                self.icon_cache['balance'] = balance_icon
            else:
                self.icon_cache['balance'] = self._create_default_icon('🪙')

        except Exception as e:
            logger.error(f"Error loading default icons: {e}")
            self.icon_cache['bet'] = self._create_default_icon('💰')
            self.icon_cache['balance'] = self._create_default_icon('🪙')

    def _create_default_icon(self, char: str) -> Image.Image:
        img = Image.new('RGBA', (24, 24), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
        except:
            font = ImageFont.load_default()
        draw.text((2, 0), char, fill=(255, 255, 255, 255), font=font)
        return img

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

        bbox = font.getbbox(text, stroke_width=stroke_width, anchor='lt')

        extra_bottom = int(font_size * 0.2)
        text_width = bbox[2] - bbox[0]
        text_height = (bbox[3] - bbox[1]) + extra_bottom

        if shadow:
            text_width += abs(shadow_offset[0]) * 2
            text_height += abs(shadow_offset[1]) * 2

        img = Image.new('RGBA', (text_width, text_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        x_offset = abs(shadow_offset[0]) if shadow and shadow_offset[0] < 0 else 0
        y_offset = abs(shadow_offset[1]) if shadow and shadow_offset[1] < 0 else 0

        text_position = (x_offset, y_offset + extra_bottom)

        if shadow:
            shadow_pos = (x_offset + shadow_offset[0], y_offset + extra_bottom + shadow_offset[1])
            draw.text(shadow_pos, text, font=font, fill=shadow_color,
                    stroke_width=stroke_width, stroke_fill=stroke_color, anchor='lt')

        draw.text(text_position, text, font=font, fill=color,
                stroke_width=stroke_width, stroke_fill=stroke_color, anchor='lt')

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
            self._default_colors = dict(self.colors)
            self.custom_overlay_providers: Dict[str, callable] = {}
            self.results_folder = None
            AnimationGenerator._initialized = True

    def register_custom_overlay_provider(self, game_name: str, provider_func: callable):
        self.custom_overlay_providers[game_name] = provider_func

    def _load_custom_icon(self, icon_path: str) -> Optional[Image.Image]:
        if not icon_path:
            return None

        possible_paths = [
            icon_path,
            os.path.join(os.path.dirname(os.path.dirname(__file__)), icon_path),
            os.path.join(os.getcwd(), "MessengerCasinoBot", "app", icon_path),
            os.path.join(os.getcwd(), icon_path)
        ]

        for path in possible_paths:
            if os.path.exists(path):
                try:
                    icon = Image.open(path).convert("RGBA")
                    icon = icon.resize((24, 24), Image.Resampling.LANCZOS)
                    return icon
                except Exception as e:
                    logger.error(f"Error loading icon {path}: {e}")
                    continue

        return None

    def _draw_exp_bar(self, draw, x, y, width, height, progress, effect_data):
        bar_type = effect_data.get("bar_type", "solid")
        fill_w = int(width * progress)
        if fill_w <= 0:
            return

        color = effect_data.get("color")

        if bar_type == "solid":
            c = color if isinstance(color, tuple) else (255, 215, 0, 255)
            c = c if len(c) == 4 else (*c, 255)
            draw.rectangle([x, y, x + fill_w, y + height], fill=c)

        elif bar_type == "gradient":
            c_from = effect_data.get("from", (255, 255, 255, 255))
            c_to = effect_data.get("to", (0, 0, 0, 255))
            for i in range(fill_w):
                t = i / max(1, fill_w - 1)
                c = tuple(int(c_from[j] * (1 - t) + c_to[j] * t) for j in range(4))
                draw.line([(x + i, y), (x + i, y + height)], fill=c, width=1)

        elif bar_type == "glow":
            c = color if isinstance(color, tuple) else (255, 215, 0, 255)
            c = c if len(c) == 4 else (*c, 255)
            for i, alpha in enumerate([60, 120, 200]):
                pad = 3 - i
                glow_c = (c[0], c[1], c[2], alpha)
                draw.rectangle(
                    [x - pad, y - pad, x + fill_w + pad, y + height + pad],
                    outline=glow_c, width=1
                )
            draw.rectangle([x, y, x + fill_w, y + height], fill=c)

        elif bar_type == "stripes":
            c = color if isinstance(color, tuple) else (0, 200, 200, 255)
            c = c if len(c) == 4 else (*c, 255)
            c_stripe = effect_data.get("stripe_color", (0, 100, 100, 255))
            c_stripe = c_stripe if len(c_stripe) == 4 else (*c_stripe, 255)
            draw.rectangle([x, y, x + fill_w, y + height], fill=c)
            stripe_w = 6
            for i in range(-height, fill_w + height, stripe_w * 2):
                draw.polygon(
                    [(x + i, y), (x + i + stripe_w, y),
                     (x + i + stripe_w - height, y + height),
                     (x + i - height, y + height)],
                    fill=c_stripe,
                )

        elif bar_type == "pulse":
            c = color if isinstance(color, tuple) else (80, 80, 100, 255)
            c = c if len(c) == 4 else (*c, 255)
            c_bright = (min(255, c[0] + 50), min(255, c[1] + 50), min(255, c[2] + 50), 255)
            num_segments = 10
            gap = 1
            seg_w = (width - (num_segments - 1) * gap) / num_segments
            for s in range(num_segments):
                seg_x = x + int(s * (seg_w + gap))
                seg_end = x + int(s * (seg_w + gap) + seg_w)
                if seg_end <= x + fill_w:
                    draw.rectangle([seg_x, y, seg_end, y + height], fill=c_bright)
                elif seg_x < x + fill_w:
                    draw.rectangle([seg_x, y, x + fill_w, y + height], fill=c)
                else:
                    draw.rectangle([seg_x, y, seg_end, y + height], fill=(40, 40, 60, 200))

        elif bar_type == "rainbow":
            for i in range(fill_w):
                hue = (i / max(1, width)) * 360
                r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 1.0, 1.0)
                c = (int(r * 255), int(g * 255), int(b * 255), 255)
                draw.line([(x + i, y), (x + i, y + height)], fill=c, width=1)

        elif bar_type == "stars":
            c = color if isinstance(color, tuple) else (40, 20, 80, 255)
            c = c if len(c) == 4 else (*c, 255)
            c_star = effect_data.get("star_color", (255, 255, 200, 255))
            c_star = c_star if len(c_star) == 4 else (*c_star, 255)
            draw.rectangle([x, y, x + fill_w, y + height], fill=c)
            import random
            rng = random.Random(42)
            num_stars = max(3, fill_w // 12)
            for _ in range(num_stars):
                sx = rng.randint(0, max(0, fill_w - 1))
                sy = rng.randint(0, max(0, height - 1))
                if sx < fill_w:
                    draw.point((x + sx, y + sy), fill=c_star)

        elif bar_type == "flames":
            c_base = color if isinstance(color, tuple) else (255, 100, 0, 255)
            c_base = c_base if len(c_base) == 4 else (*c_base, 255)
            c_flame = effect_data.get("flame_color", (255, 220, 0, 255))
            c_flame = c_flame if len(c_flame) == 4 else (*c_flame, 255)
            for j in range(height):
                t = j / max(1, height - 1)
                c = tuple(int(c_base[k] * (1 - t) + c_flame[k] * t) for k in range(3))
                draw.line([(x, y + j), (x + fill_w, y + j)], fill=(*c, 255), width=1)
            import random
            rng = random.Random(7)
            for i in range(0, fill_w, 4):
                flame_h = rng.randint(2, max(3, height // 2))
                draw.polygon(
                    [(x + i, y), (x + i + 2, y - flame_h), (x + i + 4, y)],
                    fill=c_flame,
                )

        elif bar_type == "lightning":
            c = color if isinstance(color, tuple) else (120, 80, 255, 255)
            c = c if len(c) == 4 else (*c, 255)
            c_bolt = effect_data.get("bolt_color", (255, 255, 255, 255))
            c_bolt = c_bolt if len(c_bolt) == 4 else (*c_bolt, 255)
            draw.rectangle([x, y, x + fill_w, y + height], fill=c)
            import random
            rng = random.Random(13)
            num_bolts = max(1, fill_w // 25)
            for _ in range(num_bolts):
                bx = rng.randint(0, max(0, fill_w - 5))
                by = y
                points = [(x + bx, by)]
                for _ in range(3):
                    bx += rng.randint(-3, 3)
                    by += max(1, height // 3)
                    points.append((x + bx, min(by, y + height)))
                draw.line(points, fill=c_bolt, width=1)

        elif bar_type == "rainbow_sparkle":
            for i in range(fill_w):
                hue = (i / max(1, width)) * 360
                r, g, b = colorsys.hsv_to_rgb(hue / 360.0, 1.0, 1.0)
                c = (int(r * 255), int(g * 255), int(b * 255), 255)
                draw.line([(x + i, y), (x + i, y + height)], fill=c, width=1)
            c_spark = effect_data.get("sparkle_color", (255, 255, 255, 255))
            c_spark = c_spark if len(c_spark) == 4 else (*c_spark, 255)
            import random
            rng = random.Random(99)
            num_sparks = max(2, fill_w // 8)
            for _ in range(num_sparks):
                sx = rng.randint(0, max(0, fill_w - 1))
                sy = rng.randint(0, max(0, height - 1))
                if sx < fill_w:
                    draw.point((x + sx, y + sy), fill=c_spark)

        else:
            c = color if isinstance(color, tuple) else (255, 215, 0, 255)
            c = c if len(c) == 4 else (*c, 255)
            draw.rectangle([x, y, x + fill_w, y + height], fill=c)

    def generate(self, request: GenerationRequest) -> Tuple[Optional[str], Optional[str]]:
        try:
            is_valid, error_msg = request.validate()
            if not is_valid:
                return None, f"Invalid request: {error_msg}"

            custom_kwargs = request.options.custom_overlay_kwargs or {}
            item_effects = custom_kwargs.get("item_effects", {})

            self.text_renderer.reload_default_icons()
            self.colors = dict(self._default_colors)

            icons = item_effects.get("icons", {})
            if "bet" in icons:
                icon_path = icons["bet"].get("path")
                if icon_path:
                    custom_icon = self._load_custom_icon(icon_path)
                    if custom_icon:
                        self.text_renderer.icon_cache['bet'] = custom_icon
                        logger.debug(f"Loaded custom bet icon: {icon_path}")

            if "balance" in icons:
                icon_path = icons["balance"].get("path")
                if icon_path:
                    custom_icon = self._load_custom_icon(icon_path)
                    if custom_icon:
                        self.text_renderer.icon_cache['balance'] = custom_icon
                        logger.debug(f"Loaded custom balance icon: {icon_path}")

            exp_bar_effect = item_effects.get("exp_bar")

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

            bg_resized = None
            if bg_img:
                target_size = base_frames[0].size
                bg_resized = bg_img.resize(target_size, Image.Resampling.LANCZOS).convert("RGBA")

            colors_for_win = self._calculate_colors(request)

            win_text_img = None
            if options.show_win_text:
                win_text_img = self._create_win_text(request, colors_for_win, options)

            user_overlay_before = self._create_user_overlay(
                request.user_before, avatar_img, options, frame_width, exp_bar_effect
            ) if avatar_img else None

            user_overlay_after = self._create_user_overlay(
                request.user_after, avatar_img, options, frame_width, exp_bar_effect
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
                    bg_img=bg_resized,
                    custom_overlay=custom_overlay,
                    options=options
                )

                processed_frames.append(processed_frame)

                if options.animated and options.last_frame_multiplier > 1:
                    if options.final_frames_start_index == -1:
                        if i == len(frame_indices) - 1:
                            for _ in range(int(options.last_frame_multiplier) - 1):
                                processed_frames.append(processed_frame.copy())
                    else:
                        if i >= options.final_frames_start_index:
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
                            options: GenerationOptions, frame_width: int,
                            exp_bar_effect: Optional[Dict] = None) -> Dict:
        if not avatar_img:
            return None

        avatar_size = options.avatar_size
        font_scale = options.font_scale
        overlay_position = options.overlay_position

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

        balance_font_size = int(20 * font_scale)
        bet_font_size = int(20 * font_scale)

        level_font_size = max(12, int(avatar_size * 0.2))

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
        horizontal_spacing = int(20 * font_scale)

        text_margin_left = int(20 * font_scale)
        text_margin_right = int(2 * font_scale)

        balance_width = 0
        bet_width = 0

        if balance_icon and balance_text:
            balance_width = icon_size + icon_text_spacing + balance_text.width
        elif balance_text:
            balance_width = balance_text.width

        if options.show_bet_amount and bet_text_img and bet_icon:
            bet_width = icon_size + icon_text_spacing + bet_text_img.width
        elif options.show_bet_amount and bet_text_img:
            bet_width = bet_text_img.width

        balance_height = max(icon_size, balance_text.height) if balance_text else 0
        bet_height = max(icon_size, bet_text_img.height) if bet_text_img else 0
        max_text_height = max(balance_height, bet_height)

        overlay_height = max(avatar_size, max_text_height)

        overlay_width = frame_width

        overlay = Image.new('RGBA', (overlay_width, overlay_height), (0, 0, 0, 0))

        avatar_x = overlay_width - avatar_size - text_margin_right
        avatar_y = 0

        avatar_mask = Image.new('L', (avatar_size, avatar_size), 0)
        mask_draw = ImageDraw.Draw(avatar_mask)
        mask_draw.rounded_rectangle((0, 0, avatar_size, avatar_size), radius=5, fill=255)

        avatar_resized = avatar_img.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
        avatar_rounded = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        avatar_rounded.paste(avatar_resized, (0, 0), avatar_mask)

        progress_layer = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
        progress_draw = ImageDraw.Draw(progress_layer)

        progress_bar_height = int(6 * font_scale)
        progress_bar_y = avatar_size - progress_bar_height - 1
        progress_bar_width = avatar_size - 15
        progress_bar_x = (avatar_size - progress_bar_width) // 2

        progress_draw.rectangle(
            [progress_bar_x, progress_bar_y,
             progress_bar_x + progress_bar_width, progress_bar_y + progress_bar_height],
            fill=(40, 40, 60, 220)
        )

        if exp_bar_effect:
            self._draw_exp_bar(
                progress_draw,
                progress_bar_x, progress_bar_y,
                progress_bar_width, progress_bar_height,
                level_progress, exp_bar_effect
            )
        else:
            filled_width = int(progress_bar_width * level_progress)
            if filled_width > 0:
                progress_draw.rectangle(
                    [progress_bar_x, progress_bar_y,
                     progress_bar_x + filled_width, progress_bar_y + progress_bar_height],
                    fill=(80, 160, 255, 220)
                )

        progress_draw.rectangle(
            [progress_bar_x, progress_bar_y,
             progress_bar_x + progress_bar_width, progress_bar_y + progress_bar_height],
            outline=(255, 255, 255, 180),
            width=1
        )

        avatar_with_progress = Image.alpha_composite(avatar_rounded, progress_layer)
        overlay.paste(avatar_with_progress, (avatar_x, avatar_y), avatar_mask)

        level_margin_right = int(5 * font_scale)
        level_margin_top = int(5 * font_scale)
        level_x = avatar_x + avatar_size - level_text_img.width - level_margin_right
        level_y = avatar_y + level_margin_top

        overlay.alpha_composite(level_text_img, (level_x, level_y))

        total_text_width = balance_width + bet_width
        if options.show_bet_amount and bet_text_img:
            total_text_width += horizontal_spacing

        start_x = text_margin_left

        if overlay_position == 'top':
            current_y = 0

            if balance_text:
                balance_y = current_y + (max_text_height - balance_height) // 2

                if balance_icon:
                    icon_y = balance_y + (balance_height - icon_size) // 2
                    overlay.alpha_composite(balance_icon, (start_x, icon_y))
                    balance_text_x = start_x + icon_size + icon_text_spacing
                else:
                    balance_text_x = start_x

                text_y = balance_y + (balance_height - balance_text.height) // 2
                overlay.alpha_composite(balance_text, (balance_text_x, text_y))

                start_x += balance_width

            if options.show_bet_amount and bet_text_img:
                start_x += horizontal_spacing

                bet_y = current_y + (max_text_height - bet_height) // 2

                if bet_icon:
                    icon_y = bet_y + (bet_height - icon_size) // 2
                    overlay.alpha_composite(bet_icon, (start_x, icon_y))
                    bet_text_x = start_x + icon_size + icon_text_spacing
                else:
                    bet_text_x = start_x

                text_y = bet_y + (bet_height - bet_text_img.height) // 2
                overlay.alpha_composite(bet_text_img, (bet_text_x, text_y))

        else:
            current_y = overlay_height - max_text_height

            if balance_text:
                balance_y = current_y + (max_text_height - balance_height) // 2

                if balance_icon:
                    icon_y = balance_y + (balance_height - icon_size) // 2
                    overlay.alpha_composite(balance_icon, (start_x, icon_y))
                    balance_text_x = start_x + icon_size + icon_text_spacing
                else:
                    balance_text_x = start_x

                text_y = balance_y + (balance_height - balance_text.height) // 2
                overlay.alpha_composite(balance_text, (balance_text_x, text_y))

                start_x += balance_width

            if options.show_bet_amount and bet_text_img:
                start_x += horizontal_spacing

                bet_y = current_y + (max_text_height - bet_height) // 2

                if bet_icon:
                    icon_y = bet_y + (bet_height - icon_size) // 2
                    overlay.alpha_composite(bet_icon, (start_x, icon_y))
                    bet_text_x = start_x + icon_size + icon_text_spacing
                else:
                    bet_text_x = start_x

                text_y = bet_y + (bet_height - bet_text_img.height) // 2
                overlay.alpha_composite(bet_text_img, (bet_text_x, text_y))

        return {
            'image': overlay,
            'position': (0, 0),
            'type': 'user_overlay',
            'is_on_animation': True,
            'avatar_position': (avatar_x, avatar_y, avatar_size),
            'text_position': (text_margin_left, current_y),
            'parameters': {
                'font_scale': font_scale,
                'avatar_size': avatar_size,
                'overlay_height': overlay_height,
                'show_bet_amount': options.show_bet_amount,
                'frame_width': frame_width,
                'overlay_position': overlay_position
            }
        }

    def _create_win_text(self, request: GenerationRequest, colors: Dict,
                        options: GenerationOptions) -> Optional[Image.Image]:
        if request.win_amount == 0:
            text = "BREAK EVEN"
            text_color = (180, 180, 180, 255)
        elif request.win_amount > 0:
            text = f"WIN! ${request.win_amount:.0f}"
            text_color = colors['win_text']
        else:
            text = f"LOSE! ${abs(request.win_amount):.0f}"
            text_color = colors['win_text']

        if options.win_text_scale != -1:
            font_size = int(48 * options.win_text_scale)
        else:
            font_size = int(48 * options.font_scale)

        return self.text_renderer.render_text(
            text=text,
            font_size=font_size,
            color=text_color,
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
                result = Image.alpha_composite(bg_img, result)
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

            if options.overlay_position == 'top':
                overlay_y = 0
            else:
                overlay_y = result.height - overlay_img.height

            result.alpha_composite(overlay_img, (overlay_x, overlay_y))

        return result

    def _save_animation(self, frames: List[Image.Image], output_path: str,
                    options: GenerationOptions) -> bool:
        if not frames:
            return False

        try:
            durations_to_use = []

            if options.last_frame_multiplier <= 1:
                durations_to_use = [options.frame_duration] * len(frames)
            else:
                if options.final_frames_start_index == -1:
                    for i in range(len(frames)):
                        if i == len(frames) - 1:
                            durations_to_use.append(int(options.frame_duration * options.last_frame_multiplier))
                        else:
                            durations_to_use.append(options.frame_duration)
                else:
                    multiplier = int(options.last_frame_multiplier)
                    start_index = options.final_frames_start_index

                    if start_index >= len(frames):
                        start_index = len(frames) - 1

                    for i in range(len(frames)):
                        duration = options.frame_duration

                        if i >= start_index:
                            pos_in_final = i - start_index

                            if pos_in_final % multiplier == 0:
                                duration = int(options.frame_duration * options.last_frame_multiplier)

                        if i == len(frames) - 1:
                            duration = int(options.frame_duration * 10 * options.last_frame_multiplier)

                        durations_to_use.append(duration)

            frames[0].save(
                output_path,
                format='WEBP',
                save_all=True,
                append_images=frames[1:],
                duration=durations_to_use,
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