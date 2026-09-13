import os
import colorsys
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
    
    def _add_progress_bar(self, draw, position, size, progress, text="", exp_bar_effect=None):
        x, y = position
        width, height = size

        draw.rounded_rectangle([x, y, x + width, y + height],
                              radius=height//2, fill=(50, 50, 50, 255))

        fill_width = max(10, int(width * progress))

        if exp_bar_effect:
            bar_type = exp_bar_effect.get("bar_type", "solid")
            color = exp_bar_effect.get("color")
        else:
            bar_type = "solid"
            color = (70, 130, 180, 255)

        if bar_type == "solid":
            c = color if isinstance(color, tuple) else (70, 130, 180, 255)
            c = c if len(c) == 4 else (*c, 255)
            draw.rounded_rectangle([x, y, x + fill_width, y + height],
                                  radius=height//2, fill=c)

        elif bar_type == "gradient":
            c_from = exp_bar_effect.get("from", (255, 255, 255, 255))
            c_to = exp_bar_effect.get("to", (0, 0, 0, 255))
            for i in range(fill_width):
                t = i / max(1, fill_width - 1)
                c = tuple(int(c_from[j] * (1 - t) + c_to[j] * t) for j in range(4))
                draw.line([(x + i, y + 1), (x + i, y + height - 1)], fill=c, width=1)

        elif bar_type == "glow":
            c = color if isinstance(color, tuple) else (255, 215, 0, 255)
            c = c if len(c) == 4 else (*c, 255)
            for i, alpha in enumerate([60, 120, 200]):
                pad = 3 - i
                glow_c = (c[0], c[1], c[2], alpha)
                draw.rectangle([x - pad, y - pad, x + fill_width + pad, y + height + pad],
                              outline=glow_c, width=1)
            draw.rounded_rectangle([x, y, x + fill_width, y + height],
                                  radius=height//2, fill=c)

        elif bar_type == "stripes":
            c = color if isinstance(color, tuple) else (0, 200, 200, 255)
            c = c if len(c) == 4 else (*c, 255)
            c_stripe = exp_bar_effect.get("stripe_color", (0, 100, 100, 255))
            c_stripe = c_stripe if len(c_stripe) == 4 else (*c_stripe, 255)
            draw.rounded_rectangle([x, y, x + fill_width, y + height],
                                  radius=height//2, fill=c)
            stripe_w = 8
            for i in range(-height, fill_width + height, stripe_w * 2):
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
            gap = 2
            seg_w = (width - (num_segments - 1) * gap) / num_segments
            for s in range(num_segments):
                seg_x = x + int(s * (seg_w + gap))
                seg_end = x + int(s * (seg_w + gap) + seg_w)
                if seg_end <= x + fill_width:
                    draw.rounded_rectangle([seg_x, y, seg_end, y + height],
                                          radius=2, fill=c_bright)
                elif seg_x < x + fill_width:
                    draw.rounded_rectangle([seg_x, y, x + fill_width, y + height],
                                          radius=2, fill=c)
                else:
                    draw.rounded_rectangle([seg_x, y, seg_end, y + height],
                                          radius=2, fill=(40, 40, 60, 200))

        elif bar_type in ("rainbow", "rainbow_sparkle"):
            sat = 0.55 if bar_type == "rainbow_sparkle" else 1.0
            for i in range(fill_width):
                hue = (i / max(1, width)) * 360
                r, g, b = colorsys.hsv_to_rgb(hue / 360.0, sat, 1.0)
                c = (int(r * 255), int(g * 255), int(b * 255), 255)
                draw.line([(x + i, y + 1), (x + i, y + height - 1)], fill=c, width=1)

        elif bar_type == "stars":
            c = color if isinstance(color, tuple) else (40, 20, 80, 255)
            c = c if len(c) == 4 else (*c, 255)
            c_star = exp_bar_effect.get("star_color", (255, 255, 200, 255))
            c_star = c_star if len(c_star) == 4 else (*c_star, 255)
            draw.rounded_rectangle([x, y, x + fill_width, y + height],
                                  radius=height//2, fill=c)
            import random
            rng = random.Random(42)
            num_stars = max(3, fill_width // 15)
            for _ in range(num_stars):
                sx = rng.randint(0, max(0, fill_width - 1))
                sy = rng.randint(1, max(1, height - 2))
                if sx < fill_width:
                    draw.point((x + sx, y + sy), fill=c_star)

        elif bar_type == "flames":
            c_base = color if isinstance(color, tuple) else (255, 100, 0, 255)
            c_base = c_base if len(c_base) == 4 else (*c_base, 255)
            c_flame = exp_bar_effect.get("flame_color", (255, 220, 0, 255))
            c_flame = c_flame if len(c_flame) == 4 else (*c_flame, 255)
            for j in range(height):
                t = j / max(1, height - 1)
                c = tuple(int(c_base[k] * (1 - t) + c_flame[k] * t) for k in range(3))
                draw.line([(x, y + j), (x + fill_width, y + j)], fill=(*c, 255), width=1)
            import random
            rng = random.Random(7)
            for i in range(0, fill_width, 5):
                flame_h = rng.randint(2, max(3, height // 2))
                draw.polygon(
                    [(x + i, y), (x + i + 2, y - flame_h), (x + i + 4, y)],
                    fill=c_flame,
                )

        elif bar_type == "lightning":
            c = color if isinstance(color, tuple) else (120, 80, 255, 255)
            c = c if len(c) == 4 else (*c, 255)
            c_bolt = exp_bar_effect.get("bolt_color", (255, 255, 255, 255))
            c_bolt = c_bolt if len(c_bolt) == 4 else (*c_bolt, 255)
            draw.rounded_rectangle([x, y, x + fill_width, y + height],
                                  radius=height//2, fill=c)
            import random
            rng = random.Random(13)
            num_bolts = max(1, fill_width // 30)
            for _ in range(num_bolts):
                bx = rng.randint(0, max(0, fill_width - 5))
                by = y
                points = [(x + bx, by)]
                for _ in range(3):
                    bx += rng.randint(-3, 3)
                    by += max(1, height // 3)
                    points.append((x + bx, min(by, y + height)))
                draw.line(points, fill=c_bolt, width=1)

        else:
            c = color if isinstance(color, tuple) else (70, 130, 180, 255)
            c = c if len(c) == 4 else (*c, 255)
            draw.rounded_rectangle([x, y, x + fill_width, y + height],
                                  radius=height//2, fill=c)

        draw.rounded_rectangle([x, y, x + width, y + height],
                              radius=height//2, outline=(255, 255, 255, 255), width=2)

        if text:
            text_img = self.text_renderer.render_text(
                text=text,
                font_size=14,
                color=(255, 255, 255, 255)
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
    
    def _load_background(self, bg_path, width, height):
        if bg_path and os.path.exists(bg_path):
            try:
                bg = Image.open(bg_path).convert("RGB")
                return bg.resize((width, height), Image.Resampling.LANCZOS)
            except Exception as e:
                logger.error(f"[Balance] Could not load bg {bg_path}: {e}")

        default_bg = self.get_asset_path("backgrounds", "default-bg.png")
        if os.path.exists(default_bg):
            try:
                bg = Image.open(default_bg).convert("RGB")
                return bg.resize((width, height), Image.Resampling.LANCZOS)
            except Exception as e:
                logger.error(f"[Balance] Could not load default bg: {e}")

        bg = Image.new('RGB', (width, height), (30, 35, 45))
        draw_bg = ImageDraw.Draw(bg)
        for y in range(height):
            ratio = y / height
            r = int(30 + (50 - 30) * ratio)
            g = int(35 + (60 - 35) * ratio)
            b = int(45 + (80 - 45) * ratio)
            draw_bg.line([(0, y), (width, y)], fill=(r, g, b))
        return bg

    def generate_balance_image(self, username, balance, level, level_progress, 
                              avatar_path, bg_path, output_path, item_effects=None):
        try:
            width = 520
            height = 280

            logger.info(f"[Balance] bg_path={bg_path}, exists={os.path.exists(bg_path) if bg_path else False}")

            bg = self._load_background(bg_path, width, height)
            
            balance_icon_path = self.balance_icon_path
            if item_effects:
                icons = item_effects.get("icons", {})
                bal_icon_info = icons.get("balance", {})
                custom_path = bal_icon_info.get("path")
                if custom_path:
                    full_custom = self.get_app_path(custom_path)
                    if os.path.exists(full_custom):
                        balance_icon_path = full_custom

            balance_icon = self._load_icon(balance_icon_path, (50, 50))
            
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
                         fill=(25, 25, 30))
            
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
            exp_bar_effect = item_effects.get("exp_bar") if item_effects else None
            self._add_progress_bar(draw, 
                                 (progress_x, progress_y), 
                                 (progress_width, progress_height), 
                                 level_progress, 
                                 progress_text,
                                 exp_bar_effect=exp_bar_effect)
            
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

            item_effects = self._get_user_effects(user_id)

            timestamp = _get_unique_id()
            output_path = os.path.join(self.results_folder, f"balance_{user_id}_{timestamp}.webp")
            
            self.generate_balance_image(
                username=username,
                balance=balance,
                level=level,
                level_progress=level_progress,
                avatar_path=avatar_path,
                bg_path=bg_path,
                output_path=output_path,
                item_effects=item_effects
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
        "aliases": ["/balance", "/money", "/level", "/stats"],
        "description": "Check your balance, level and stats\nShows current coins and level progress",
        "execute": plugin.execute_game
    }