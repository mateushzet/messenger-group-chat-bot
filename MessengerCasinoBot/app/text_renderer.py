import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import hashlib
from collections import OrderedDict
from logger import logger

class FontCache:
    _instance = None
    _fonts = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_font(self, font_path, font_size):
        key = f"{font_path}_{font_size}"
        
        if key not in self._fonts:
            try:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                else:
                    font = ImageFont.load_default()
                    if hasattr(font, 'size'):
                        font.size = font_size
            except Exception as e:
                logger.error(f"[FontCache] Font loading error: {e}")
                font = ImageFont.load_default()
            
            self._fonts[key] = font
        
        return self._fonts[key]

class CachedTextRenderer:
    
    def __init__(self, max_text_cache=1000, max_metrics_cache=2000):
        self.font_cache = FontCache()
        self.text_image_cache = OrderedDict()
        self.text_metrics_cache = {}
        self.max_text_cache = max_text_cache
        self.max_metrics_cache = max_metrics_cache
        
    def get_text_metrics(self, text, font_path, font_size):
        key = f"{hash(text)}_{font_path}_{font_size}"
        
        if key not in self.text_metrics_cache:
            font = self.get_font(font_path, font_size)
            try:
                bbox = font.getbbox(text)
                metrics = {
                    'width': bbox[2] - bbox[0],
                    'height': bbox[3] - bbox[1],
                    'ascent': -bbox[1],
                    'descent': bbox[3]
                }
            except:
                metrics = {'width': len(text) * font_size // 2, 'height': font_size}
            
            self.text_metrics_cache[key] = metrics
            
            if len(self.text_metrics_cache) > self.max_metrics_cache:
                oldest_key = next(iter(self.text_metrics_cache))
                del self.text_metrics_cache[oldest_key]
        
        return self.text_metrics_cache[key]
    
    def get_font(self, font_path, font_size):
        return self.font_cache.get_font(font_path, font_size)
        
    def render_text_to_image(self, text, font_path, font_size, color=(255, 255, 255),
                        stroke_width=0, stroke_color=(0, 0, 0), bg_color=None,
                        shadow=False, shadow_color=(0, 0, 0, 100), shadow_offset=(2, 2),
                        include_full_ascent_descent=True):
        
        cache_key_parts = [
            text, font_path, str(font_size), str(color),
            str(stroke_width), str(stroke_color), str(bg_color),
            str(shadow), str(shadow_color), str(shadow_offset),
            str(include_full_ascent_descent)
        ]
        cache_key = hashlib.md5("_".join(cache_key_parts).encode()).hexdigest()
        
        if cache_key in self.text_image_cache:
            img = self.text_image_cache.pop(cache_key)
            self.text_image_cache[cache_key] = img
            return img.copy()
        
        font = self.get_font(font_path, font_size)
        
        try:
            try:
                bbox = font.getbbox(text)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                ascent = -bbox[1]
                descent = bbox[3] - (bbox[3] - bbox[1]) + bbox[1]
            except:
                ascent, descent = font.getmetrics()
                text_width = font.getlength(text)
                text_height = ascent + descent
            
            if include_full_ascent_descent:
                render_height = text_height
            else:
                render_height = ascent
        except Exception as e:
            logger.error(f"[FontCache] Error getting font metrics: {e}")
            text_width = len(text) * font_size // 2
            text_height = font_size
            render_height = text_height
            ascent = font_size
            descent = 0
        
        stroke_margin = abs(stroke_width) * 2 if stroke_width > 0 else 0
        shadow_offset_x, shadow_offset_y = shadow_offset if shadow else (0, 0)
        shadow_margin = max(abs(shadow_offset_x), abs(shadow_offset_y)) * 2 if shadow else 0
        
        total_margin = max(stroke_margin, shadow_margin, 2)
        img_width = int(text_width) + total_margin * 2
        
        if include_full_ascent_descent and descent > 0:
            img_height = int(render_height) + total_margin * 2
            extra_descent_padding = descent // 2
            img_height += extra_descent_padding
        else:
            img_height = int(render_height) + total_margin * 2
        
        if bg_color is not None and len(bg_color) >= 3:
            if len(bg_color) == 4 and bg_color[3] > 0:
                text_img = Image.new("RGBA", (img_width, img_height), bg_color)
            elif len(bg_color) == 3:
                text_img = Image.new("RGB", (img_width, img_height), bg_color)
            else:
                text_img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        else:
            text_img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
        
        draw = ImageDraw.Draw(text_img)
        
        x = total_margin
        y = total_margin
        
        if include_full_ascent_descent and descent > 0:
            y += extra_descent_padding // 2
        
        if shadow:
            shadow_img = Image.new("RGBA", (img_width, img_height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_img)
            
            if stroke_width > 0:
                offsets = [(dx, dy) for dx in range(-stroke_width, stroke_width + 1)
                        for dy in range(-stroke_width, stroke_width + 1)
                        if dx != 0 or dy != 0]
                
                for dx, dy in offsets:
                    shadow_draw.text((x + dx + shadow_offset_x, y + dy + shadow_offset_y), 
                                text, font=font, fill=shadow_color)
            
            shadow_draw.text((x + shadow_offset_x, y + shadow_offset_y), 
                        text, font=font, fill=shadow_color)
            
            shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=1))
            
            text_img = Image.alpha_composite(shadow_img, text_img)
            draw = ImageDraw.Draw(text_img)
        
        if stroke_width > 0:
            offsets = []
            for dx in range(-stroke_width, stroke_width + 1):
                for dy in range(-stroke_width, stroke_width + 1):
                    if dx != 0 or dy != 0:
                        if abs(dx) == stroke_width or abs(dy) == stroke_width:
                            offsets.insert(0, (dx, dy))
                        else:
                            offsets.append((dx, dy))
            
            for dx, dy in offsets:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
        
        draw.text((x, y), text, font=font, fill=color)
        
        if bg_color is None or (len(bg_color) == 4 and bg_color[3] == 0):
            bbox = text_img.getbbox()
            if bbox:
                text_img = text_img.crop(bbox)
        
        if len(self.text_image_cache) >= self.max_text_cache:
            self.text_image_cache.popitem(last=False)
        
        self.text_image_cache[cache_key] = text_img
        
        return text_img.copy()
    
    def pre_render_texts(self, texts_configs):
        results = {}
        for key, config in texts_configs.items():
            results[key] = self.render_text_to_image(**config)
        return results