from PIL import Image, ImageDraw, ImageFont
import os
from typing import List, Tuple

class DailyRewardImageGenerator:
    def __init__(self):
        self.width = 800
        self.height = 300
        self.box_width = 100
        self.box_height = 110
        self.box_spacing = 15
        self.reward_amounts = [10, 20, 30, 40, 50, 75, 100]
        self.bar_height = 250
        self.bar_opacity = 230
        
    def generate_daily_reward_image(self, 
                                  current_day: int,
                                  already_claimed: bool) -> Image.Image:
        
        image = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image, 'RGBA')
        
        self._draw_background_bar(draw)
        
        self._draw_title_text(draw, current_day, already_claimed)
        
        total_width = 7 * self.box_width + 6 * self.box_spacing
        start_x = (self.width - total_width) // 2
        start_y = 150
        
        self._draw_reward_boxes(draw, image, start_x, start_y, current_day, already_claimed)
        
        return image
    
    def _draw_background_bar(self, draw: ImageDraw.Draw) -> None:
        bar_y = 30
        bar_height = self.bar_height
        
        bar_color = (0, 0, 0, self.bar_opacity)
        
        draw.rounded_rectangle(
            [0, bar_y, self.width, bar_y + bar_height],
            radius=15,
            fill=bar_color
        )
        
        border_color = (50, 50, 50, 100)
        draw.rounded_rectangle(
            [0, bar_y, self.width, bar_y + bar_height],
            radius=15,
            outline=border_color,
            width=1
        )
    
    def _draw_title_text(self,
                        draw: ImageDraw.Draw,
                        current_day: int,
                        already_claimed: bool) -> None:
        
        text_color = (255, 255, 255, 255)
        stroke_color = (0, 0, 0, 255)
        stroke_width = 2
        
        try:
            title_font = ImageFont.truetype("arial.ttf", 36)
            subtitle_font = ImageFont.truetype("arial.ttf", 28)
        except:
            try:
                title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
                subtitle_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
            except:
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
        
        if already_claimed:
            title = "DAILY REWARD"
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (self.width - title_width) // 2
            
            draw.text(
                (title_x, 40),
                title, 
                fill=text_color, 
                font=title_font,
                stroke_width=stroke_width,
                stroke_fill=stroke_color
            )
            
            subtitle = f"Day {current_day + 1} claimed - Come back tomorrow!"
            
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (self.width - subtitle_width) // 2
            
            draw.text(
                (subtitle_x, 90),
                subtitle, 
                fill=text_color, 
                font=subtitle_font,
                stroke_width=stroke_width,
                stroke_fill=stroke_color
            )
            
        else:
            title = "DAILY REWARD"
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (self.width - title_width) // 2
            
            draw.text(
                (title_x, 40),
                title, 
                fill=text_color, 
                font=title_font,
                stroke_width=stroke_width,
                stroke_fill=stroke_color
            )
            
            reward_amount = self.reward_amounts[current_day]
            subtitle = f"CLAIM: ${reward_amount}"
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (self.width - subtitle_width) // 2
            
            draw.text(
                (subtitle_x, 90),
                subtitle, 
                fill=text_color, 
                font=subtitle_font,
                stroke_width=stroke_width,
                stroke_fill=stroke_color
            )
    
    def _draw_reward_boxes(self,
                          draw: ImageDraw.Draw,
                          image: Image.Image,
                          start_x: int,
                          start_y: int,
                          current_day: int,
                          already_claimed: bool) -> None:
        
        for i in range(7):
            x = start_x + i * (self.box_width + self.box_spacing)
            y = start_y
            
            box_image = Image.new('RGBA', (self.box_width, self.box_height), (0, 0, 0, 0))
            box_draw = ImageDraw.Draw(box_image, 'RGBA')
            
            fill_color = self._get_box_fill_color(i, current_day, already_claimed)
            
            box_draw.rounded_rectangle(
                [0, 0, self.box_width, self.box_height], 
                radius=15, 
                fill=fill_color
            )
            
            border_color = self._get_box_border_color(i, current_day, already_claimed)
            border_width = 3 if (i == current_day and not already_claimed) else 2
            
            box_draw.rounded_rectangle(
                [0, 0, self.box_width, self.box_height], 
                radius=15, 
                outline=border_color, 
                width=border_width
            )
            
            self._draw_box_text(box_draw, i, current_day, already_claimed)
            
            image.alpha_composite(box_image, (x, y))
    
    def _draw_box_text(self,
                      draw: ImageDraw.Draw,
                      day_index: int,
                      current_day: int,
                      already_claimed: bool) -> None:
        
        if (already_claimed and day_index <= current_day) or (day_index < current_day):
            text_color = (255, 255, 255, 255)
            stroke_color = (0, 0, 0, 255)
        elif day_index == current_day and not already_claimed:
            text_color = (255, 215, 0, 255)
            stroke_color = (0, 0, 0, 255)
        else:
            text_color = (200, 200, 200, 255)
            stroke_color = (0, 0, 0, 255)
        
        stroke_width = 1
        
        try:
            day_font = ImageFont.truetype("arial.ttf", 18)
            amount_font = ImageFont.truetype("arial.ttf", 16)
        except:
            try:
                day_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
                amount_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
            except:
                day_font = ImageFont.load_default()
                amount_font = ImageFont.load_default()
        
        day_text = f"DAY {day_index + 1}"
        day_bbox = draw.textbbox((0, 0), day_text, font=day_font)
        day_width = day_bbox[2] - day_bbox[0]
        day_x = (self.box_width - day_width) // 2
        
        draw.text(
            (day_x, 25), 
            day_text, 
            fill=text_color, 
            font=day_font,
            stroke_width=stroke_width,
            stroke_fill=stroke_color
        )
        
        amount_text = f"${self.reward_amounts[day_index]}"
        amount_bbox = draw.textbbox((0, 0), amount_text, font=amount_font)
        amount_width = amount_bbox[2] - amount_bbox[0]
        amount_x = (self.box_width - amount_width) // 2
        
        draw.text(
            (amount_x, 60), 
            amount_text, 
            fill=text_color, 
            font=amount_font,
            stroke_width=stroke_width,
            stroke_fill=stroke_color
        )
        
    
    def _get_box_fill_color(self, day_index: int, current_day: int, already_claimed: bool) -> Tuple[int, int, int, int]:
        if already_claimed and day_index <= current_day:
            return (0, 120, 0, 255)
        elif day_index < current_day:
            return (0, 120, 0, 255)
        elif day_index == current_day and not already_claimed:
            return (60, 60, 60, 255)
        else:
            return (40, 40, 40, 255)
    
    def _get_box_border_color(self, day_index: int, current_day: int, already_claimed: bool) -> Tuple[int, int, int, int]:
        if not already_claimed and day_index == current_day:
            return (255, 215, 0, 255)
        elif (already_claimed and day_index <= current_day) or (day_index < current_day):
            return (0, 200, 0, 255)
        else:
            return (100, 100, 100, 255)

def save_as_webp(image: Image.Image, filename: str, quality: int = 85) -> None:
    if not filename.endswith('.webp'):
        filename += '.webp'
    
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    image.save(filename, 'WEBP', quality=quality, lossless=True, method=6)

def generate_all_combinations():
    generator = DailyRewardImageGenerator()
    
    os.makedirs("daily_rewards", exist_ok=True)
    
    for day in range(7):
        for claimed in [False, True]:
            image = generator.generate_daily_reward_image(
                current_day=day,
                already_claimed=claimed
            )
            
            status = "claimed" if claimed else "available"
            filename = f"daily_rewards/day_{day+1}_{status}"
            save_as_webp(image, filename)

def generate_examples():
    generator = DailyRewardImageGenerator()
    
    examples = [
        (0, False, "example_day1_available"),
        (2, False, "example_day3_available"), 
        (4, False, "example_day5_available"),
        (6, False, "example_day7_available"),
        (3, True, "example_day4_claimed"),
        (6, True, "example_weekly_completed")
    ]
    
    for day, claimed, filename in examples:
        image = generator.generate_daily_reward_image(
            current_day=day,
            already_claimed=claimed
        )
        save_as_webp(image, filename)

def preview_image(image: Image.Image, title: str = "Preview"):
    preview = Image.new('RGBA', image.size, (30, 30, 40, 255))
    preview.paste(image, (0, 0), image)
    preview.save(f"preview_{title}.png", 'PNG')

if __name__ == "__main__":
    print("GENERATING DAILY REWARD IMAGES")
    print("Image size: 800x300")
    print("Box size: 100x110")
    print("Reward amounts: [10, 20, 30, 40, 50, 75, 100]")
    print("Transparent background")
    print("Opaque reward boxes")
    print("White text with black outline")
    print("Semi-transparent black bar behind text")
    
    generator = DailyRewardImageGenerator()
    test_image = generator.generate_daily_reward_image(
        current_day=3,
        already_claimed=False
    )
    preview_image(test_image, "daily_reward_example")
    
    print("Generating all combinations...")
    generate_all_combinations()
    
    print("Generating examples...")
    generate_examples()
    
    print("GENERATION COMPLETE!")