import os
import time
import math
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from base_game_plugin import BaseGamePlugin
from logger import logger

class TimePlugin(BaseGamePlugin):
    def __init__(self):
        results_folder = self.get_app_path("temp")
        
        super().__init__(
            game_name="time",
            results_folder=results_folder,
        )
        
        os.makedirs(self.results_folder, exist_ok=True)
    
    def check_easter_egg(self, cache, user_id, current_time):
        if current_time.hour != 21 or current_time.minute != 37:
            return False, None
        
        easter_egg_key = "time_easter_egg_last_collected"
        
        last_collected_str = cache.get_setting(easter_egg_key)
        
        if last_collected_str:
            try:
                last_collected = datetime.fromisoformat(last_collected_str)
                today = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                last_collected_date = last_collected.replace(hour=0, minute=0, second=0, microsecond=0)
                
                if last_collected_date >= today:
                    logger.info(f"[Time] Easter egg already collected today at {last_collected}")
                    return False, None
            except Exception as e:
                logger.error(f"[Time] Error parsing last collected date: {e}")
        
        current_time_iso = current_time.isoformat()
        cache.set_setting(easter_egg_key, current_time_iso)
        
        user = cache.get_user(user_id)
        if user:
            new_balance = user.get("balance", 0) + 37
            cache.update_balance(user_id, new_balance)
            logger.info(f"[Time] Easter egg awarded to {user_id}: +37 coins at {current_time_iso}. New balance: {new_balance}")
            return True, new_balance
        
        return False, None
    
    def draw_clock(self, img, center_x, center_y, radius, current_time):
        draw = ImageDraw.Draw(img)
        
        draw.ellipse(
            [center_x - radius, center_y - radius, 
             center_x + radius, center_y + radius],
            fill=(240, 240, 245, 230),
            outline=(30, 30, 40, 255),
            width=6
        )
        
        for i in range(60):
            angle = math.radians(i * 6 - 90)
            if i % 5 == 0:
                mark_length = radius * 0.1
                mark_width = 3
            else:
                mark_length = radius * 0.05
                mark_width = 1
            
            x1 = center_x + (radius - mark_length) * math.cos(angle)
            y1 = center_y + (radius - mark_length) * math.sin(angle)
            x2 = center_x + radius * math.cos(angle)
            y2 = center_y + radius * math.sin(angle)
            
            draw.line([(x1, y1), (x2, y2)], fill=(30, 30, 40, 255), width=mark_width)
        
        try:
            font = ImageFont.truetype("DejaVuSans-Bold", int(radius * 0.12))
        except:
            font = ImageFont.load_default()
        
        for hour in range(1, 13):
            angle = math.radians(hour * 30 - 90)
            text_radius = radius * 0.75
            
            x = center_x + text_radius * math.cos(angle)
            y = center_y + text_radius * math.sin(angle)
            
            hour_text = str(hour)
            bbox = draw.textbbox((0, 0), hour_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            draw.text(
                (x - text_width/2, y - text_height/2),
                hour_text,
                fill=(30, 30, 40, 255),
                font=font
            )
        
        hour = current_time.hour % 12
        minute = current_time.minute
        second = current_time.second
        
        hour_angle = math.radians((hour * 30) + (minute * 0.5) - 90)
        minute_angle = math.radians(minute * 6 - 90)
        second_angle = math.radians(second * 6 - 90)
        
        second_length = radius * 0.85
        x_second = center_x + second_length * math.cos(second_angle)
        y_second = center_y + second_length * math.sin(second_angle)
        draw.line([(center_x, center_y), (x_second, y_second)], 
                 fill=(220, 50, 50, 255), 
                 width=2)
        
        minute_length = radius * 0.75
        x_minute = center_x + minute_length * math.cos(minute_angle)
        y_minute = center_y + minute_length * math.sin(minute_angle)
        draw.line([(center_x, center_y), (x_minute, y_minute)], 
                 fill=(50, 50, 60, 255), 
                 width=4)
        
        hour_length = radius * 0.5
        x_hour = center_x + hour_length * math.cos(hour_angle)
        y_hour = center_y + hour_length * math.sin(hour_angle)
        draw.line([(center_x, center_y), (x_hour, y_hour)], 
                 fill=(30, 30, 40, 255), 
                 width=6)
        
        draw.ellipse(
            [center_x - 8, center_y - 8, 
             center_x + 8, center_y + 8],
            fill=(30, 30, 40, 255)
        )

    def create_time_image(self, output_path, cache, user_id=None, easter_egg_awarded=False):
        width = 800
        height = 600
        
        bg_img = None
        try:
            if user_id and hasattr(cache, 'get_background_path'):
                bg_path = cache.get_background_path(user_id)
                if bg_path and os.path.exists(bg_path):
                    bg_img = Image.open(bg_path).convert('RGBA')
                    bg_img = bg_img.resize((width, height), Image.LANCZOS)
                    
                    darken_factor = 0.8
                    if bg_img.mode == 'RGBA':
                        r, g, b, a = bg_img.split()
                        r = r.point(lambda x: int(x * darken_factor))
                        g = g.point(lambda x: int(x * darken_factor))
                        b = b.point(lambda x: int(x * darken_factor))
                        bg_img = Image.merge('RGBA', (r, g, b, a))
                    else:
                        bg_img = bg_img.convert('RGB')
                        r, g, b = bg_img.split()
                        r = r.point(lambda x: int(x * darken_factor))
                        g = g.point(lambda x: int(x * darken_factor))
                        b = b.point(lambda x: int(x * darken_factor))
                        bg_img = Image.merge('RGB', (r, g, b)).convert('RGBA')
        except Exception as e:
            logger.error(f"[Time] Error loading user background: {e}")
            bg_img = None
        
        if bg_img:
            img = bg_img.copy()
        else:
            img = Image.new('RGBA', (width, height), (25, 30, 45, 255))
            draw = ImageDraw.Draw(img)
            
            for i in range(height):
                alpha = int(150 * (i / height))
                color = (40, 45, 60, alpha)
                draw.line([(0, i), (width, i)], fill=color)
        
        draw = ImageDraw.Draw(img)
        
        current_time = datetime.now()
        
        from datetime import timedelta
        display_time = current_time + timedelta(seconds=3)
        
        clock_radius = min(width, height) // 3
        center_x = width // 2
        center_y = height // 2
        
        self.draw_clock(img, center_x, center_y, clock_radius, display_time)
        
        try:
            time_font = ImageFont.truetype("DejaVuSans.ttf", 24)
            date_font = ImageFont.truetype("DejaVuSans.ttf", 20)
        except:
            time_font = ImageFont.load_default()
            date_font = ImageFont.load_default()
        
        time_text = display_time.strftime("%H:%M:%S")
        date_text = display_time.strftime("%A, %d %B %Y")
        
        time_bbox = draw.textbbox((0, 0), time_text, font=time_font)
        time_width = time_bbox[2] - time_bbox[0]
        time_height = time_bbox[3] - time_bbox[1]
        
        date_bbox = draw.textbbox((0, 0), date_text, font=date_font)
        date_width = date_bbox[2] - date_bbox[0]
        date_height = date_bbox[3] - date_bbox[1]
        
        text_y = center_y + clock_radius + 40
        
        padding = 20
        draw.rounded_rectangle(
            [center_x - max(time_width, date_width)//2 - padding, 
             text_y - padding//2,
             center_x + max(time_width, date_width)//2 + padding,
             text_y + time_height + date_height + padding],
            radius=10,
            fill=(30, 30, 40, 200),
            outline=(60, 60, 80, 255),
            width=2
        )
        
        time_x = center_x - time_width // 2
        draw.text((time_x, text_y), time_text, 
                 fill=(240, 240, 255, 255), 
                 font=time_font)
        
        date_x = center_x - date_width // 2
        draw.text((date_x, text_y + time_height + 10), date_text, 
                 fill=(200, 200, 220, 255), 
                 font=date_font)
        
        if easter_egg_awarded:
            try:
                win_font = ImageFont.truetype("DejaVuSans.ttf", 32)
            except:
                win_font = ImageFont.load_default()
            
            win_text = "WIN 37$"
            win_bbox = draw.textbbox((0, 0), win_text, font=win_font)
            win_width = win_bbox[2] - win_bbox[0]
            win_height = win_bbox[3] - win_bbox[1]
            
            win_y = center_y - clock_radius - 60
            
            win_padding = 15
            draw.rounded_rectangle(
                [center_x - win_width//2 - win_padding,
                 win_y - win_padding,
                 center_x + win_width//2 + win_padding,
                 win_y + win_height + win_padding],
                radius=15,
                fill=(0, 177, 64, 220),
                outline=(255, 255, 255, 255),
                width=3
            )
            
            draw.text((center_x - win_width//2 + 2, win_y + 2), 
                     win_text, 
                     fill=(0, 0, 0, 200), 
                     font=win_font)
            draw.text((center_x - win_width//2, win_y), 
                     win_text, 
                     fill=(255, 255, 255, 255), 
                     font=win_font)
        
        img.save(output_path, format='WEBP', quality=90, optimize=True)
        return output_path
    
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        
        self.cache = cache
        
        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        if error:
            return error
        
        current_time = datetime.now()
        easter_egg_awarded, new_balance = self.check_easter_egg(cache, user_id, current_time)
        
        timestamp = int(time.time())
        img_path = os.path.join(self.results_folder, f"time_{user_id}_{timestamp}.webp")
        
        self.create_time_image(img_path, cache, user_id, easter_egg_awarded)
        
        file_queue.put(img_path)
        
        return "Time image sent"


def register():
    plugin = TimePlugin()
    return {
        "name": "time",
        "aliases": ["/time"],
        "description": "Shows current time with analog clock on your background",
        "execute": plugin.execute_game
    }