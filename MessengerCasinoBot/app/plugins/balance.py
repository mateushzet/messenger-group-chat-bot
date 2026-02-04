import os
from PIL import Image, ImageDraw
from base_game_plugin import BaseGamePlugin
from logger import logger
from utils import _get_unique_id

class BalancePlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="balance"
        )
        
        self.assets_dir = self.get_app_path("assets")
        self.balance_icon_path = os.path.join(self.assets_dir, "balance_icon.png")

    def _load_icon(self, icon_path, default_size=(40, 40)):
        if hasattr(self, 'generator') and hasattr(self.generator, 'resource_cache'):
            icon = self.generator.resource_cache.get_icon(icon_path, default_size)
            if icon:
                return icon
        
        try:
            if os.path.exists(icon_path):
                icon = Image.open(icon_path).convert('RGBA')
                return icon.resize(default_size, Image.Resampling.LANCZOS)
        except:
            pass
        
        icon = Image.new('RGBA', default_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(icon)

        draw.ellipse([5, 5, 35, 35], fill=(255, 215, 0, 255))
        
        dollar_text = "$"
        dollar_img = self.text_renderer.render_text(
            text=dollar_text,
            font_size=18,
            color=(139, 69, 19, 255),
            stroke_width=1,
            stroke_color=(0, 0, 0, 255)
        )
        
        dollar_x = (default_size[0] - dollar_img.width) // 2
        dollar_y = (default_size[1] - dollar_img.height) // 2
        icon.paste(dollar_img, (dollar_x, dollar_y), dollar_img)
        
        return icon
    
    def _create_avatar(self, avatar_path, size=90):
        if (hasattr(self, 'generator') and hasattr(self.generator, 'resource_cache') and
            avatar_path and os.path.exists(avatar_path)):
            
            avatar = self.generator.resource_cache.get_image(
                avatar_path, 
                resize=(size, size),
                convert_mode="RGBA"
            )
            if avatar:
                return avatar

        try:
            if avatar_path and os.path.exists(avatar_path):
                avatar = Image.open(avatar_path).convert('RGBA')
            else:
                avatar = Image.new('RGBA', (size, size), (70, 130, 180, 255))
                draw = ImageDraw.Draw(avatar)
                draw.rectangle([10, 10, size-10, size-10], fill=(255, 255, 255, 255))
                
                question_text = "?"
                question_img = self.text_renderer.render_text(
                    text=question_text,
                    font_size=size//3,
                    color=(70, 130, 180, 255),
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 255)
                )
                q_x = (size - question_img.width) // 2
                q_y = (size - question_img.height) // 2
                avatar.paste(question_img, (q_x, q_y), question_img)
            
            avatar = avatar.resize((size, size), Image.Resampling.LANCZOS)
            
            return avatar
            
        except Exception as e:
            logger.error(f"[Balance] Error creating avatar: {e}")
            return Image.new('RGBA', (size, size), (70, 130, 180, 255))
    
    def _render_text(self, text, font_size, color, **kwargs):
        return self.text_renderer.render_text(
            text=text,
            font_size=font_size,
            color=color,
            stroke_width=kwargs.get('stroke_width', 0),
            stroke_color=kwargs.get('stroke_color', (0, 0, 0, 255)),
            shadow=kwargs.get('shadow', False),
            shadow_color=kwargs.get('shadow_color', (0, 0, 0, 100)),
            shadow_offset=kwargs.get('shadow_offset', (2, 2))
        )
    
    def _add_progress_bar(self, draw, position, size, progress, text=""):
        x, y = position
        width, height = size
        
        draw.rounded_rectangle([x, y, x + width, y + height], 
                              radius=height//2, fill=(50, 50, 50, 255))
        
        fill_width = max(10, int(width * progress))
        draw.rounded_rectangle([x, y, x + fill_width, y + height], 
                              radius=height//2, fill=(70, 130, 180, 255))
        
        draw.rounded_rectangle([x, y, x + width, y + height], 
                              radius=height//2, outline=(255, 255, 255, 255), width=2)
        
        if text:
            text_img = self.text_renderer.render_text(
                text=text,
                font_size=14,
                color=(255, 255, 255, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255)
            )
            text_x = x + (width - text_img.width) // 2
            text_y = y + (height - text_img.height) // 2
            
            draw.bitmap((text_x, text_y), 
                       text_img.split()[3] if text_img.mode == 'RGBA' else None,
                       fill=(255, 255, 255, 255))
    
    def _create_stat_card(self, icon, value, label, bg_color=(40, 40, 40, 255)):
        card_width = 220
        card_height = 80
        
        card = Image.new('RGBA', (card_width, card_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(card)
        
        draw.rounded_rectangle([0, 0, card_width, card_height], radius=15, fill=bg_color)
        
        icon_x = 15
        icon_y = (card_height - icon.size[1]) // 2
        
        card.paste(icon, (icon_x, icon_y), icon)
        
        if isinstance(value, (int, float)):
            formatted_value = f"{value:,}"
        else:
            formatted_value = str(value)
        
        value_img = self.text_renderer.render_text(
            text=formatted_value,
            font_size=24,
            color=(255, 255, 255, 255),
            stroke_width=1,
            stroke_color=(0, 0, 0, 255)
        )
        
        value_x = icon_x + icon.size[0] + 15
        value_y = 15
        
        card.paste(value_img, (value_x, value_y), value_img)
        
        label_img = self.text_renderer.render_text(
            text=label.upper(),
            font_size=14,
            color=(200, 200, 200, 255),
            stroke_width=1,
            stroke_color=(0, 0, 0, 255)
        )
        
        label_y = value_y + 35
        card.paste(label_img, (value_x, label_y), label_img)
        
        return card
    
    def generate_balance_image(self, username, balance, level, level_progress, 
                              avatar_path, bg_path, output_path):
        try:
            width = 520
            height = 280

            bg = None
            if hasattr(self, 'generator') and hasattr(self.generator, 'resource_cache'):
                bg = self.generator.resource_cache.get_image(
                    bg_path, 
                    convert_mode="RGB"
                ) if bg_path and os.path.exists(bg_path) else None
                
                if bg is None:
                    default_bg_path = self.get_asset_path("backgrounds", "default-bg.png")
                    if os.path.exists(default_bg_path):
                        bg = self.generator.resource_cache.get_image(
                            default_bg_path,
                            convert_mode="RGB"
                        )
            
            if bg:
                bg = bg.resize((width, height), Image.Resampling.LANCZOS)
            else:
                bg = Image.new('RGB', (width, height), (30, 35, 45))
                draw_bg = ImageDraw.Draw(bg)
                for y in range(height):
                    ratio = y / height
                    r = int(30 + (50 - 30) * ratio)
                    g = int(35 + (60 - 35) * ratio)
                    b = int(45 + (80 - 45) * ratio)
                    draw_bg.line([(0, y), (width, y)], fill=(r, g, b))
            
            balance_icon = self._load_icon(self.balance_icon_path, (50, 50))
            
            avatar = self._create_avatar(avatar_path, 90)
            
            balance_card = self._create_stat_card(balance_icon, balance, "BALANCE", 
                                                 (40, 40, 40, 255))
            
            result = Image.new('RGB', (width, height), (0, 0, 0))
            result.paste(bg, (0, 0))
            
            draw = ImageDraw.Draw(result)
            
            padding = 25
            
            overlay_height = 200
            overlay_y = 40
            overlay_width = width
            
            draw.rectangle([0, overlay_y, overlay_width, overlay_y + overlay_height], 
                         fill=(25, 25, 25))
            
            avatar_height = avatar.size[1]
            username_height = 40
            card_height = balance_card.size[1]
            level_text_height = 30
            progress_bar_height = 24
            
            total_content_height = (
                username_height + 10 + card_height + 20 + 
                level_text_height + 10 + progress_bar_height
            )
            
            content_start_y = overlay_y + (overlay_height - total_content_height) // 2 + 10
            
            avatar_x = padding
            avatar_y = content_start_y + (total_content_height - avatar_height) // 2
            result.paste(avatar, (avatar_x, avatar_y), avatar)

            username_img = self.text_renderer.render_text(
                text=username,
                font_size=28,
                color=(255, 255, 255, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255)
            )
            username_x = avatar_x + avatar.size[0] + padding
            username_y = content_start_y
            result.paste(username_img, (username_x, username_y), username_img)
            
            card_x = avatar_x + avatar.size[0] + padding
            card_y = content_start_y + username_height + 10
            
            result.paste(balance_card, (card_x, card_y), balance_card)

            level_y = card_y + card_height + 20
            
            level_text_str = f"LEVEL {level}"
            level_img = self.text_renderer.render_text(
                text=level_text_str,
                font_size=22,
                color=(255, 255, 255, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255)
            )
            level_x = card_x
            level_y_pos = level_y
            result.paste(level_img, (level_x, level_y_pos), level_img)
            level_text_width = level_img.width
            
            progress_x = card_x + level_text_width + 20
            progress_y = level_y + 10
            progress_width = 180
            progress_height = 24
            
            progress_text = f"{int(level_progress * 100)}%"
            self._add_progress_bar(draw, 
                                 (progress_x, progress_y), 
                                 (progress_width, progress_height), 
                                 level_progress, 
                                 progress_text)
            
            result.save(output_path, format="WEBP", quality=90, optimize=True)
            
            return output_path
            
        except Exception as e:
            logger.error(f"[Balance] Error generating balance image: {e}", exc_info=True)
            raise
    
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 0)
        if error:
            self.send_message_image(sender, file_queue, "User validation failed!", 
                                  "Balance - Validation Error", cache, user_id)
            return ""
        
        try:
            avatar_path = cache.get_avatar_path(user_id) if cache else None
            bg_path = cache.get_background_path(user_id) if cache else None
            
            username = sender
            balance = user.get("balance", 0)
            level = user.get("level", 1)
            level_progress = user.get("level_progress", 0.0)
            
            timestamp = _get_unique_id()
            output_path = os.path.join(self.results_folder, f"balance_{user_id}_{timestamp}.webp")
            
            self.generate_balance_image(
                username=username,
                balance=balance,
                level=level,
                level_progress=level_progress,
                avatar_path=avatar_path,
                bg_path=bg_path,
                output_path=output_path
            )
            
            if os.path.exists(output_path):
                file_queue.put(output_path)
                
                response = (
                    f"**{sender}'s Stats**\n\n"
                    f"**Balance:** {balance:,} coins\n"
                    f"**Level:** {level} ({int(level_progress * 100)}%)"
                )
                
                return response
            else:
                logger.error(f"[Balance] Generated image not found at {output_path}")
                return "Failed to generate balance image."
                
        except Exception as e:
            logger.error(f"[Balance] Error in balance plugin: {e}", exc_info=True)
            return f"Error: {str(e)}"


def register():
    plugin = BalancePlugin()
    return {
        "name": "balance",
        "aliases": ["/balance", "/money", "/level", "/bal", "/stats"],
        "description": "Check your balance, level and stats\nShows current coins and level progress",
        "execute": plugin.execute_game
    }