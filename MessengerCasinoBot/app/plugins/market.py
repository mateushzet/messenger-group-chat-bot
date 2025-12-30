import os
import json
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime
from base_game_plugin import BaseGamePlugin
from logger import logger

class BackgroundMarketPlugin(BaseGamePlugin):
    def __init__(self):     
        results_folder = self.get_app_path("temp")
        super().__init__(
            game_name="market",
            results_folder=results_folder,
        )

        backgrounds_folder = self.get_asset_path("backgrounds")
        avatars_folder = self.get_asset_path("avatars")
        error_folder = self.get_asset_path("errors")
        
        self.backgrounds_folder = backgrounds_folder
        self.avatars_folder = avatars_folder
        self.error_folder = error_folder
        
        os.makedirs(self.results_folder, exist_ok=True)

    def load_market_items(self):
        if not hasattr(self.cache, 'market_items'):
            return []
        return self.cache.get_market_items()

    def buy_item_from_market(self, user_id, index):
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"
        
        items = self.load_market_items()
        if not items:
            return False, "Market is empty"
        
        if index < 0 or index >= len(items):
            return False, "Invalid item number"
        
        item = items[index]
        item_type = item.get("type")
        item_file = item.get("file")
        price = 100
        
        if not item_type or not item_file:
            return False, "Invalid market item"
        
        if user["balance"] < price:
            return False, "Not enough funds"
        
        if item_type == "background":
            user_backgrounds = user.get("backgrounds", [])
            if item_file in user_backgrounds:
                return False, "Background already owned"
                
        elif item_type == "avatar":
            user_avatars = user.get("avatars", [])
            if item_file in user_avatars:
                return False, "Avatar already owned"
        
        if item_type == "background":
            full_path = os.path.join(self.backgrounds_folder, item_file)
        else:
            full_path = os.path.join(self.avatars_folder, item_file)
            
        if not os.path.exists(full_path):
            return False, f"{item_type} file missing"
        
        self.cache.update_balance(user_id, -price)
        
        if item_type == "background":
            user_backgrounds = user.get("backgrounds", [])
            if item_file not in user_backgrounds:
                user_backgrounds.append(item_file)
                self.cache.update_user(user_id, backgrounds=user_backgrounds)
                
        elif item_type == "avatar":
            user_avatars = user.get("avatars", [])
            if item_file not in user_avatars:
                user_avatars.append(item_file)
                self.cache.update_user(user_id, avatars=user_avatars)
        
        self.cache.remove_market_item(item_file)
        
        return True, f"Purchased {item_file} for {price} coins"

    def create_market_image(self, output_path, user_id):
        items = self.load_market_items()
        
        if not items:
            return None
        
        ITEM_WIDTH = 250
        ITEM_HEIGHT = 250
        MARGIN = 20
        ITEMS_PER_ROW = 3
        
        num_items = len(items)
        rows = (num_items + ITEMS_PER_ROW - 1) // ITEMS_PER_ROW
        
        total_width = ITEM_WIDTH * ITEMS_PER_ROW + MARGIN * (ITEMS_PER_ROW + 1)
        total_height = (ITEM_HEIGHT + MARGIN) * rows + MARGIN * 3 + 120
        
        try:
            bg_path = self.cache.get_background_path(user_id)
            if bg_path and os.path.exists(bg_path):
                bg_img = Image.open(bg_path)
                bg_img = bg_img.resize((total_width, total_height), Image.LANCZOS)
                img = bg_img.convert('RGBA')
            else:
                img = Image.new('RGBA', (total_width, total_height), (20, 20, 30, 255))
        except Exception as e:
            logger.error(f"Error loading background for market image: {e}")
            img = Image.new('RGBA', (total_width, total_height), (20, 20, 30, 255))
        
        top_bar_height = 80
        top_bar = Image.new('RGBA', (total_width, top_bar_height), (40, 40, 50))
        img.paste(top_bar, (0, 0), top_bar)
        
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
            price_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
            command_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
            info_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 12)
            small_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 11)
        except:
            title_font = ImageFont.load_default()
            price_font = ImageFont.load_default()
            command_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        title_text = "PLAYER MARKET"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_x = (total_width - (title_bbox[2] - title_bbox[0])) // 2
        draw.text((title_x, MARGIN), title_text, fill=(255, 255, 255), font=title_font)
        
        y_offset = MARGIN + 100
        
        for idx, item in enumerate(items):
            row = idx // ITEMS_PER_ROW
            col = idx % ITEMS_PER_ROW
            
            x = MARGIN + col * (ITEM_WIDTH + MARGIN)
            y = y_offset + row * (ITEM_HEIGHT + MARGIN)
            
            item_type = item.get("type", "background")
            
            if item_type == "avatar":
                outline_color = (100, 150, 255)
                type_color = (100, 200, 255)
            else:
                outline_color = (255, 200, 100)
                type_color = (255, 200, 100)
            
            draw.rectangle([x, y, x + ITEM_WIDTH, y + ITEM_HEIGHT], 
                          fill=(50, 50, 60, 220), outline=outline_color, width=3)
            
            type_text = item_type.upper()
            type_bbox = draw.textbbox((0, 0), type_text, font=small_font)
            type_x = x + 10
            type_y = y + 8
            draw.text((type_x, type_y), type_text, fill=type_color, font=small_font)
            
            item_number = idx + 1
            command_text = f"/market buy {item_number}"
            command_bbox = draw.textbbox((0, 0), command_text, font=command_font)
            command_x = x + (ITEM_WIDTH - (command_bbox[2] - command_bbox[0])) // 2
            command_y = y + 25
            draw.text((command_x, command_y), command_text, fill=(255, 255, 255), font=command_font)
            
            try:
                item_file = item.get("file", "")
                if item_type == "avatar":
                    full_path = os.path.join(self.avatars_folder, item_file)
                else:
                    full_path = os.path.join(self.backgrounds_folder, item_file)
                
                if os.path.exists(full_path):
                    if item_type == "avatar":
                        item_img = Image.open(full_path).convert('RGBA')
                        item_img = item_img.resize((ITEM_WIDTH - 60, ITEM_HEIGHT - 80), Image.LANCZOS)
                        
                        item_x = x + (ITEM_WIDTH - item_img.width) // 2
                        item_y = y + (ITEM_HEIGHT - item_img.height) // 2 + 10
                        img.paste(item_img, (item_x, item_y), item_img)
                    else:
                        item_img = Image.open(full_path)
                        item_img = item_img.resize((ITEM_WIDTH - 60, ITEM_HEIGHT - 80), Image.LANCZOS)
                        
                        item_x = x + (ITEM_WIDTH - item_img.width) // 2
                        item_y = y + (ITEM_HEIGHT - item_img.height) // 2 + 10
                        img.paste(item_img, (item_x, item_y))
                else:
                    name_text = os.path.splitext(item_file)[0]
                    if len(name_text) > 20:
                        name_text = name_text[:17] + "..."
                    
                    name_bbox = draw.textbbox((0, 0), name_text, font=info_font)
                    name_width = name_bbox[2] - name_bbox[0]
                    name_height = name_bbox[3] - name_bbox[1]
                    
                    name_x = x + (ITEM_WIDTH - name_width) // 2
                    name_y = y + (ITEM_HEIGHT - name_height) // 2
                    
                    draw.rectangle([name_x - 5, name_y - 5, name_x + name_width + 5, name_y + name_height + 5], 
                                  fill=(40, 40, 50, 200))
                    draw.text((name_x, name_y), name_text, fill=(200, 200, 200), font=info_font)
                    
            except Exception as e:
                logger.error(f"Error loading {item_type} image {item.get('file', '')}: {e}")
                error_text = "IMAGE ERROR"
                error_bbox = draw.textbbox((0, 0), error_text, font=command_font)
                error_x = x + (ITEM_WIDTH - (error_bbox[2] - error_bbox[0])) // 2
                error_y = y + (ITEM_HEIGHT - (error_bbox[3] - error_bbox[1])) // 2
                draw.text((error_x, error_y), error_text, fill=(255, 100, 100), font=command_font)
            
            filename = item.get("file", "")
            if len(filename) > 22:
                filename = filename[:19] + "..."
            
            filename_bbox = draw.textbbox((0, 0), filename, font=small_font)
            filename_x = x + (ITEM_WIDTH - (filename_bbox[2] - filename_bbox[0])) // 2
            filename_y = y + ITEM_HEIGHT - 45
            draw.text((filename_x, filename_y), filename, fill=(180, 180, 200), font=small_font)
            
            price_tag = "100 coins"
            price_bbox = draw.textbbox((0, 0), price_tag, font=price_font)
            price_x = x + (ITEM_WIDTH - (price_bbox[2] - price_bbox[0])) // 2
            price_y = y + ITEM_HEIGHT - 25
            draw.text((price_x, price_y), price_tag, fill=(100, 255, 100), font=price_font)
        
        if len(items) == 0:
            info_text = "Market is empty! Sell items with /bg sell or /avatar sell"
            info_bbox = draw.textbbox((0, 0), info_text, font=info_font)
            info_x = (total_width - (info_bbox[2] - info_bbox[0])) // 2
            info_y = total_height - 40
            draw.text((info_x, info_y), info_text, fill=(255, 200, 100), font=info_font)
        else:
            legend_y = total_height - 35
            legend_avatar = "◼︎ AVATAR"
            legend_bg = "◼︎ BACKGROUND"
            
            avatar_bbox = draw.textbbox((0, 0), legend_avatar, font=small_font)
            bg_bbox = draw.textbbox((0, 0), legend_bg, font=small_font)
            
            total_legend_width = avatar_bbox[2] - avatar_bbox[0] + 40 + bg_bbox[2] - bg_bbox[0]
            start_x = (total_width - total_legend_width) // 2
            
            draw.text((start_x, legend_y), legend_avatar, fill=(100, 200, 255), font=small_font)
            
            draw.text((start_x + avatar_bbox[2] - avatar_bbox[0] + 40, legend_y), legend_bg, fill=(255, 200, 100), font=small_font)
        
        img.save(output_path, format='WEBP', quality=85, optimize=True)
        logger.info(f"Market image saved to: {output_path}")
        return output_path

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 0)
        
        if error == "Invalid user":
            self._send_error_image("validation_error", sender, file_queue)
            return ""
        elif error:
            self._send_error_image("insufficient_funds", sender, file_queue)
            return ""
        
        nickname = sender

        if not args:
            items = self.load_market_items()
            
            if not items:
                self._send_error_image("market_empty", nickname, file_queue)
                return ""
            
            img_path = os.path.join(self.results_folder, f"market_{user_id}.webp")
            logger.info(f"Creating market image: {img_path}")
            self.create_market_image(img_path, user_id)
            
            overlay_path, error = self.apply_user_overlay(
                img_path, user_id, sender, 0, 0, user["balance"], user
            )
            if overlay_path:
                file_queue.put(overlay_path)
                logger.info(f"Market overlay saved to: {overlay_path}")
            
            bg_count = sum(1 for item in items if item.get("type") == "background")
            av_count = sum(1 for item in items if item.get("type") == "avatar")
            
            return f"**Player Market** ({len(items)} items)\n Backgrounds: {bg_count}\n• Avatars: {av_count}\n Price: 100 coins each\n\nUse `/market buy <number>` to purchase."

        cmd = args[0].lower()

        if cmd == "buy":
            if len(args) < 2:
                self._send_error_image("invalid_usage_market", nickname, file_queue, "Usage: /market buy <number>")
                return ""

            try:
                index = int(args[1]) - 1
                success, msg = self.buy_item_from_market(user_id, index)
                
                if not success:
                    if "already owned" in msg.lower():
                        self._send_error_image("market_already_owned", nickname, file_queue, msg)
                    elif "not enough funds" in msg.lower():
                        self._send_error_image("insufficient_funds", nickname, file_queue, msg)
                    elif "invalid item number" in msg.lower():
                        self._send_error_image("market_invalid_number", nickname, file_queue, msg)
                    else:
                        self._send_error_image("image_fatal_error", nickname, file_queue, msg)
                    return ""
                
                items = self.load_market_items()
                if items:
                    img_path = os.path.join(self.results_folder, f"market_{user_id}_after_buy.webp")
                    self.create_market_image(img_path, user_id)
                    
                    overlay_path, error = self.apply_user_overlay(
                        img_path, user_id, sender, 100, -100, user["balance"], user
                    )
                    if overlay_path:
                        file_queue.put(overlay_path)
                
                return f"✅ {msg}"
                
            except ValueError:
                self._send_error_image("market_invalid_number", nickname, file_queue, "Invalid number format")
                return ""

        elif cmd == "info":
            items = self.load_market_items()
            bg_count = sum(1 for item in items if item.get("type") == "background")
            av_count = sum(1 for item in items if item.get("type") == "avatar")
            
            return (
                f"🏪 **Player Market**\n"
                f"• Total items: {len(items)}\n"
                f"• Backgrounds: {bg_count}\n"
                f"• Avatars: {av_count}\n"
                f"• Price per item: 100 coins\n"
                f"• Last update: {datetime.now().strftime('%H:%M:%S')}\n\n"
                "**Commands:**\n"
                "`/market` - view market\n"
                "`/market buy <number>` - buy item\n\n"
                "**Sell items:**\n"
                "`/bg sell` - sell backgrounds\n"
                "`/avatar sell` - sell avatars"
            )

        self._send_error_image("invalid_usage_market", nickname, file_queue, "Available commands: /market, /market buy, /market info")
        return ""


def register():
    plugin = BackgroundMarketPlugin()
    return {
        "name": "market",
        "aliases": ["/market"],
        "description": "Player market - buy avatars & backgrounds from other players",
        "execute": plugin.execute_game
    }