from PIL import Image, ImageDraw, ImageFont
import os
from typing import List, Tuple

class DailyRewardImageGenerator:
    def __init__(self):
        self.width = 800
        self.height = 300
        self.box_width = 90
        self.box_height = 100
        self.box_spacing = 20
        self.reward_amounts = [10, 20, 30, 40, 50, 75, 100]
        
    def generate_daily_reward_image(self, 
                                  current_day: int,
                                  already_claimed: bool) -> Image.Image:
        
        image = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        start_x = (self.width - (7 * self.box_width + 6 * self.box_spacing)) // 2
        start_y = 150
        
        self._draw_main_container(draw)
        self._draw_reward_amount_text(draw, current_day, already_claimed)
        self._draw_reward_boxes(draw, start_x, start_y, current_day, already_claimed)
        
        return image
    
    def _draw_main_container(self, draw: ImageDraw.Draw) -> None:
        container_color = (0, 0, 0, 150)
        border_color = (255, 255, 255, 255)
        
        draw.rounded_rectangle([10, 30, self.width - 10, self.height - 10], 
                             radius=30, fill=container_color)
        
        draw.rounded_rectangle([10, 30, self.width - 10, self.height - 10], 
                             radius=30, outline=border_color, width=2)
    
    def _draw_reward_amount_text(self,
                               draw: ImageDraw.Draw,
                               current_day: int,
                               already_claimed: bool) -> None:
        
        text_color = (255, 255, 255, 255)
        
        try:
            reward_font = ImageFont.truetype("arial.ttf", 32)
            message_font = ImageFont.truetype("arial.ttf", 24)
        except:
            reward_font = ImageFont.load_default()
            message_font = ImageFont.load_default()
        
        if already_claimed:
            if current_day == 6:
                message = "Daily reward already claimed! Come back tomorrow."
            else:
                message = f"Daily reward already claimed! Come back tomorrow."
            
            msg_bbox = draw.textbbox((0, 0), message, font=message_font)
            msg_width = msg_bbox[2] - msg_bbox[0]
            msg_x = (self.width - msg_width) // 2
            draw.text((msg_x, 80), message, fill=text_color, font=message_font)
        else:
            reward_text = f"${self.reward_amounts[current_day]}"
            reward_bbox = draw.textbbox((0, 0), reward_text, font=reward_font)
            reward_width = reward_bbox[2] - reward_bbox[0]
            reward_x = (self.width - reward_width) // 2
            draw.text((reward_x, 60), reward_text, fill=text_color, font=reward_font)
            
            message = "received today!"
            msg_bbox = draw.textbbox((0, 0), message, font=message_font)
            msg_width = msg_bbox[2] - msg_bbox[0]
            msg_x = (self.width - msg_width) // 2
            draw.text((msg_x, 100), message, fill=text_color, font=message_font)
    
    def _draw_reward_boxes(self,
                          draw: ImageDraw.Draw,
                          start_x: int,
                          start_y: int,
                          current_day: int,
                          already_claimed: bool) -> None:
        
        for i in range(7):
            x = start_x + i * (self.box_width + self.box_spacing)
            y = start_y
            
            fill_color = self._get_box_fill_color(i, current_day, already_claimed)
            
            draw.rounded_rectangle([x, y, x + self.box_width, y + self.box_height], 
                                 radius=20, fill=fill_color)
            
            border_color = self._get_box_border_color(i, current_day, already_claimed)
            border_width = 4 if (i == current_day and not already_claimed) else 2
            draw.rounded_rectangle([x, y, x + self.box_width, y + self.box_height], 
                                 radius=20, outline=border_color, width=border_width)
            
            self._draw_box_text(draw, x, y, i)
    
    def _draw_box_text(self,
                      draw: ImageDraw.Draw,
                      x: int, y: int,
                      day_index: int) -> None:
        
        text_color = (255, 255, 255, 255)
        
        try:
            day_font = ImageFont.truetype("arial.ttf", 16)
            amount_font = ImageFont.truetype("arial.ttf", 14)
        except:
            day_font = ImageFont.load_default()
            amount_font = ImageFont.load_default()
        
        day_text = f"Day {day_index + 1}"
        day_bbox = draw.textbbox((0, 0), day_text, font=day_font)
        day_width = day_bbox[2] - day_bbox[0]
        day_x = x + (self.box_width - day_width) // 2
        draw.text((day_x, y + 20), day_text, fill=text_color, font=day_font)
        
        amount_text = f"${self.reward_amounts[day_index]}"
        amount_bbox = draw.textbbox((0, 0), amount_text, font=amount_font)
        amount_width = amount_bbox[2] - amount_bbox[0]
        amount_x = x + (self.box_width - amount_width) // 2
        draw.text((amount_x, y + 50), amount_text, fill=text_color, font=amount_font)
    
    def _get_box_fill_color(self, day_index: int, current_day: int, already_claimed: bool) -> Tuple[int, int, int, int]:
        if already_claimed and day_index <= current_day:
            return (0, 150, 0, 180)
        elif day_index < current_day:
            return (0, 150, 0, 180)
        elif day_index == current_day and not already_claimed:
            return (100, 100, 100, 120)
        else:
            return (100, 100, 100, 120)
    
    def _get_box_border_color(self, day_index: int, current_day: int, already_claimed: bool) -> Tuple[int, int, int, int]:
        if not already_claimed and day_index == current_day:
            return (255, 215, 0, 255)
        else:
            return (255, 255, 255, 255)

def save_as_webp(image: Image.Image, filename: str, quality: int = 80) -> None:
    if not filename.endswith('.webp'):
        filename += '.webp'
    
    image.save(filename, 'WEBP', quality=quality)

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

if __name__ == "__main__":
    generate_examples()
    generate_all_combinations()