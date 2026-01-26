from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
from dataclasses import dataclass
from typing import Optional, Tuple, List
from pathlib import Path
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AnimationConfig:
    width: int = 420
    height: int = 200
    box_x: int = 20
    box_y: int = 60
    box_width: Optional[int] = None
    box_height: int = 120
    bar_height: int = 30
    segments: int = 9
    bar_y: Optional[int] = None
    frame_delay_ms: int = 60
    final_pause_ms: int = 60
    max_frames: int = 120
    progress_step: float = 0.015
    webp_quality: int = 90
    webp_method: int = 6
    
    def __post_init__(self):
        if self.box_width is None:
            self.box_width = self.width - 40
        if self.bar_y is None:
            self.bar_y = self.box_y + 25

@dataclass
class ColorScheme:
    background: Tuple[int, int, int, int] = (0, 0, 0, 0)
    progress_background: Tuple[int, int, int, int] = (0, 0, 0, 255)
    bar_background: Tuple[int, int, int, int] = (50, 50, 50, 255)
    bar_divider: Tuple[int, int, int, int] = (100, 100, 100, 255)
    bar_foreground_base: Tuple[int, int, int] = (255, 215, 0)
    bar_gradient_dark: Tuple[int, int, int] = (200, 170, 0)
    text: Tuple[int, int, int, int] = (255, 255, 255, 255)
    text_outline: Tuple[int, int, int, int] = (0, 0, 0, 255)
    highlight: Tuple[int, int, int, int] = (255, 240, 100, 255)
    highlight_outline: Tuple[int, int, int, int] = (0, 0, 0, 255)
    title_color: Tuple[int, int, int, int] = (255, 220, 80, 255)
    title_outline: Tuple[int, int, int, int] = (0, 0, 0, 255)
    shadow: Tuple[int, int, int, int] = (0, 0, 0, 255)
    shine_color: Tuple[int, int, int, int] = (255, 255, 200, 255)
    outline_color: Tuple[int, int, int, int] = (100, 100, 100, 255)
    glow_color: Tuple[int, int, int, int] = (255, 255, 150, 255)

class FontManager:
    _fonts_cache = {}
    
    @classmethod
    def get_font(cls, bold: bool = False, size: int = 12, 
                 font_path: Optional[str] = None) -> ImageFont.FreeTypeFont:
        cache_key = (bold, size, font_path)
        
        if cache_key in cls._fonts_cache:
            return cls._fonts_cache[cache_key]
        
        font = cls._load_font(bold, size, font_path)
        cls._fonts_cache[cache_key] = font
        return font
    
    @staticmethod
    def _load_font(bold: bool, size: int, font_path: Optional[str]) -> ImageFont.FreeTypeFont:
        try:
            if font_path and os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
            
            if bold:
                possible_paths = [
                    "DejaVuSans-Bold.ttf",
                    "arialbd.ttf",
                    "C:/Windows/Fonts/arialbd.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                ]
            else:
                possible_paths = [
                    "DejaVuSans.ttf",
                    "arial.ttf",
                    "C:/Windows/Fonts/arial.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return ImageFont.truetype(path, size)
            
            return ImageFont.load_default(size)
            
        except Exception as e:
            logger.warning(f"Could not load font: {e}. Using default.")
            return ImageFont.load_default(size)

def validate_reward(reward: int) -> None:
    if not isinstance(reward, int):
        raise TypeError(f"Reward must be integer, got {type(reward)}")
    if not 0 <= reward <= 100:
        raise ValueError(f"Reward must be between 0 and 100, got {reward}")

class ProgressBarAnimation:
    
    def __init__(self, 
                 config: Optional[AnimationConfig] = None,
                 colors: Optional[ColorScheme] = None,
                 font_manager: Optional[FontManager] = None,
                 title_text: str = "Hourly Reward"):
        
        self.config = config or AnimationConfig()
        self.colors = colors or ColorScheme()
        self.font_manager = font_manager or FontManager()
        self.title_text = title_text
        
        self.reward_font = self.font_manager.get_font(bold=True, size=32)
        self.label_font = self.font_manager.get_font(bold=True, size=20)
        self.title_font = self.font_manager.get_font(bold=True, size=28)
    
    def draw_text_with_outline(self,
                              draw: ImageDraw.Draw,
                              text: str,
                              position: Tuple[int, int],
                              font: ImageFont.FreeTypeFont,
                              fill: Tuple[int, int, int, int],
                              outline_color: Tuple[int, int, int, int],
                              outline_width: int = 3) -> None:
        x, y = position
        
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if abs(dx) == outline_width or abs(dy) == outline_width:
                    draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
        
        draw.text((x, y), text, font=font, fill=fill)
    
    def create_gradient_bar(self, width: int, pulse_value: float = 1.0) -> Image.Image:
        if width <= 0:
            return Image.new("RGBA", (0, self.config.bar_height), (0, 0, 0, 0))
        
        bar = Image.new("RGBA", (width, self.config.bar_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(bar)
        
        base_color = self.colors.bar_foreground_base
        dark_color = self.colors.bar_gradient_dark
        
        pulse_factor = 0.8 + 0.2 * pulse_value
        
        for y in range(self.config.bar_height):
            pos = y / (self.config.bar_height - 1)
            
            r = int(dark_color[0] + (base_color[0] - dark_color[0]) * pos)
            g = int(dark_color[1] + (base_color[1] - dark_color[1]) * pos)
            b = int(dark_color[2] + (base_color[2] - dark_color[2]) * pos)
            
            r = min(255, int(r * pulse_factor))
            g = min(255, int(g * pulse_factor))
            b = min(255, int(b * pulse_factor))
            
            draw.line([(0, y), (width - 1, y)], fill=(r, g, b, 255))
        
        return bar
    
    def create_frame(self, 
                    reward: int, 
                    progress: float, 
                    highlight: bool, 
                    pulse_value: float) -> Image.Image:
        
        progress = max(0.0, min(1.0, progress))
        
        original_height = self.config.height
        frame_height = original_height + 40
        
        img = Image.new("RGBA", (self.config.width, frame_height), 
                       (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        background_width = self.config.box_width + 40
        background_height = self.config.box_height + 20
        background_x = self.config.box_x - 20
        background_y = self.config.box_y - 10
        
        draw.rounded_rectangle(
            [background_x, 
             background_y + 10, 
             background_x + background_width, 
             background_y + background_height - 35],
            radius=15, 
            fill=self.colors.progress_background
        )
        
        if highlight:
            title_text = f"Reward: {reward} coins"
            
            max_title_width = self.config.width - 40
            title_font_size = 28
            current_title_font = self.title_font
            
            bbox_title = draw.textbbox((0, 0), title_text, font=current_title_font)
            w_title = bbox_title[2] - bbox_title[0]
            
            while w_title > max_title_width and title_font_size > 18:
                title_font_size -= 2
                current_title_font = self.font_manager.get_font(bold=True, size=title_font_size)
                bbox_title = draw.textbbox((0, 0), title_text, font=current_title_font)
                w_title = bbox_title[2] - bbox_title[0]
        else:
            title_text = self.title_text
            current_title_font = self.title_font
            bbox_title = draw.textbbox((0, 0), title_text, font=current_title_font)
            w_title = bbox_title[2] - bbox_title[0]
        
        title_x = (self.config.width - w_title) // 2
        title_y = 20
        
        self.draw_text_with_outline(
            draw, title_text,
            (title_x, title_y),
            current_title_font,
            self.colors.title_color,
            self.colors.title_outline,
            outline_width=3
        )
        
        draw.rounded_rectangle(
            [self.config.box_x, 
             self.config.bar_y, 
             self.config.box_x + self.config.box_width, 
             self.config.bar_y + self.config.bar_height],
            radius=12, 
            fill=self.colors.bar_background
        )
        
        draw.rounded_rectangle(
            [self.config.box_x - 2, 
             self.config.bar_y - 2, 
             self.config.box_x + self.config.box_width + 2, 
             self.config.bar_y + self.config.bar_height + 2],
            radius=12, 
            outline=self.colors.outline_color,
            width=2
        )
        
        for i in range(1, self.config.segments + 1):
            x = self.config.box_x + (self.config.box_width * i // (self.config.segments + 1))
            draw.line(
                [(x, self.config.bar_y + 4), 
                 (x, self.config.bar_y + self.config.bar_height - 4)],
                fill=self.colors.bar_divider,
                width=2
            )
        
        fill_width = int(self.config.box_width * progress)
        
        if fill_width > 0:
            gradient_bar = self.create_gradient_bar(fill_width, pulse_value)
            
            mask = Image.new("L", (fill_width, self.config.bar_height), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle(
                [0, 0, fill_width - 1, self.config.bar_height - 1],
                radius=10,
                fill=255
            )
            
            bar_x = self.config.box_x
            bar_y = self.config.bar_y
            img.paste(gradient_bar, (bar_x, bar_y), mask)
        
        label_y = self.config.bar_y + self.config.bar_height + 10
        
        bbox_0 = draw.textbbox((0, 0), "0", font=self.label_font)
        w_0 = bbox_0[2] - bbox_0[0]
        x_0 = self.config.box_x - w_0 // 2
        
        self.draw_text_with_outline(
            draw, "0",
            (x_0, label_y),
            self.label_font,
            self.colors.text,
            self.colors.text_outline,
            outline_width=2
        )
        
        bbox_50 = draw.textbbox((0, 0), "50", font=self.label_font)
        w_50 = bbox_50[2] - bbox_50[0]
        x_50 = self.config.box_x + self.config.box_width // 2 - w_50 // 2
        
        self.draw_text_with_outline(
            draw, "50",
            (x_50, label_y),
            self.label_font,
            self.colors.text,
            self.colors.text_outline,
            outline_width=2
        )
        
        bbox_100 = draw.textbbox((0, 0), "100", font=self.label_font)
        w_100 = bbox_100[2] - bbox_100[0]
        x_100 = self.config.box_x + self.config.box_width - w_100 // 2
        
        self.draw_text_with_outline(
            draw, "100",
            (x_100, label_y),
            self.label_font,
            self.colors.text,
            self.colors.text_outline,
            outline_width=2
        )
        
        pixels = img.load()
        for x in range(img.width):
            for y in range(img.height):
                r, g, b, a = pixels[x, y]
                if a > 0:
                    pixels[x, y] = (r, g, b, 255)
        
        return img
    
    def generate_pulse_values(self, count: int) -> List[float]:
        values = []
        for i in range(count):
            t = i / self.config.max_frames
            pulse1 = 0.7 + 0.3 * ((math.sin(2 * math.pi * t) + 1) / 2)
            pulse2 = 0.8 + 0.2 * ((math.sin(4 * math.pi * t + math.pi/4) + 1) / 2)
            pulse = (pulse1 + pulse2) / 2
            values.append(pulse)
        return values
    
    def generate_webp(self, reward: int, output_path: str) -> bool:
        try:
            validate_reward(reward)
            
            target_progress = reward / 100.0
            
            base_frames = min(
                int(math.ceil(target_progress / self.config.progress_step)),
                self.config.max_frames - 1
            )
            
            extra_frames = int(target_progress * 20)
            animated_frames = min(base_frames + extra_frames, self.config.max_frames - 1)
            
            pulses = self.generate_pulse_values(self.config.max_frames * 2)
            
            frames = []
            durations = []
            
            for i in range(animated_frames):
                t = i / max(animated_frames - 1, 1)
                eased_t = 1 - (1 - t) ** 3
                progress = min(eased_t * target_progress, target_progress)
                
                frame = self.create_frame(
                    reward=reward,
                    progress=progress,
                    highlight=False,
                    pulse_value=pulses[i % len(pulses)]
                )
                frames.append(frame)
                durations.append(self.config.frame_delay_ms)
            
            highlight_frames = 8
            for i in range(highlight_frames):
                pulse_index = (animated_frames + i) % len(pulses)
                frame = self.create_frame(
                    reward=reward,
                    progress=target_progress,
                    highlight=True,
                    pulse_value=pulses[pulse_index]
                )
                frames.append(frame)
                durations.append(self.config.frame_delay_ms)
            
            frames[0].save(
                output_path,
                format="WEBP",
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=0,
                quality=self.config.webp_quality,
                method=self.config.webp_method,
                minimize_size=True,
                allow_mixed=True,
                background=(0, 0, 0, 0)
            )
            
            file_size = os.path.getsize(output_path) / 1024
            logger.info(f"Generated: {output_path} ({file_size:.1f} KB)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating {output_path}: {str(e)}", exc_info=True)
            return False
    
    def generate_all_rewards(self, 
                            output_dir: str = "rewards", 
                            rewards: List[int] = None) -> List[str]:
        if rewards is None:
            rewards = list(range(10, 101, 10))
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        successful = []
        
        for reward in rewards:
            filename = output_path / f"reward_{reward:03d}.webp"
            logger.info(f"Generating {self.title_text} reward {reward}...")
            
            if self.generate_webp(reward, str(filename)):
                successful.append(str(filename))
            else:
                logger.error(f"Failed to generate reward {reward}")
        
        logger.info(f"Generated {len(successful)} out of {len(rewards)} animations in {output_dir}")
        return successful


def create_golden_color_scheme() -> ColorScheme:
    return ColorScheme(
        background=(0, 0, 0, 0),
        progress_background=(0, 0, 0, 255),
        bar_background=(40, 40, 40, 255),
        bar_divider=(80, 80, 80, 255),
        bar_foreground_base=(255, 215, 0),
        bar_gradient_dark=(180, 140, 0),
        text=(255, 255, 255, 255),
        text_outline=(0, 0, 0, 255),
        highlight=(255, 220, 60, 255),
        highlight_outline=(0, 0, 0, 255),
        title_color=(255, 200, 40, 255),
        title_outline=(0, 0, 0, 255),
        shadow=(0, 0, 0, 255),
        shine_color=(255, 240, 180, 255),
        outline_color=(120, 120, 120, 255),
        glow_color=(255, 200, 80, 255)
    )


def create_premium_color_scheme() -> ColorScheme:
    return ColorScheme(
        background=(0, 0, 0, 0),
        progress_background=(0, 0, 0, 255),
        bar_background=(30, 40, 50, 255),
        bar_divider=(60, 80, 100, 255),
        bar_foreground_base=(0, 180, 255),
        bar_gradient_dark=(0, 80, 160),
        text=(255, 255, 255, 255),
        text_outline=(0, 0, 0, 255),
        highlight=(0, 200, 255, 255),
        highlight_outline=(0, 0, 0, 255),
        title_color=(0, 160, 220, 255),
        title_outline=(0, 0, 0, 255),
        shadow=(0, 0, 0, 255),
        shine_color=(180, 220, 255, 255),
        outline_color=(80, 100, 120, 255),
        glow_color=(100, 180, 240, 255)
    )


def generate_hourly_reward_golden():
    colors = create_golden_color_scheme()
    
    animator = ProgressBarAnimation(
        colors=colors,
        title_text="Hourly Reward"
    )
    
    rewards = list(range(10, 101, 10))
    
    successful = animator.generate_all_rewards(
        output_dir="rewards_hourly_golden",
        rewards=rewards
    )
    
    print(f"\nGenerated {len(successful)} Hourly Reward (Golden) animations")
    print(f"Location: rewards_hourly_golden/")
    
    return successful


def generate_correct_answer_premium():
    colors = create_premium_color_scheme()
    
    animator = ProgressBarAnimation(
        colors=colors,
        title_text="Correct Answer"
    )
    
    rewards = list(range(10, 101, 10))
    
    successful = animator.generate_all_rewards(
        output_dir="rewards_hourly_premium",
        rewards=rewards
    )
    
    print(f"\nGenerated {len(successful)} Correct Answer (Premium Blue) animations")
    print(f"Location: rewards_hourly_premium/")
    
    return successful


def main():
    print("PROGRESS BAR ANIMATION GENERATOR")
    print("Generating only two sets:")
    print("1. Hourly Reward (Golden)")
    print("2. Correct Answer (Premium Blue)")
    
    hourly_successful = generate_hourly_reward_golden()
    
    print("\n" + "-" * 60)
    
    correct_successful = generate_correct_answer_premium()
    
    print("\n" + "=" * 60)
    print("GENERATION COMPLETE!")
    print("=" * 60)
    
    total_generated = len(hourly_successful) + len(correct_successful)
    print(f"\nTotal animations generated: {total_generated}")
    print("\nGenerated sets:")
    print(f"  1. Hourly Reward (Golden): {len(hourly_successful)} animations")
    print(f"     → rewards_hourly_golden/")
    print(f"  2. Correct Answer (Premium Blue): {len(correct_successful)} animations")
    print(f"     → rewards_hourly_premium/")


if __name__ == "__main__":
    main()