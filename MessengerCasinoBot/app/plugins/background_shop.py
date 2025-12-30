import os
import random
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime
from base_game_plugin import BaseGamePlugin
from logger import logger
from utils import _get_unique_id

class BackgroundShopPlugin(BaseGamePlugin):
    def __init__(self):
        
        results_folder = self.get_app_path("temp")

        super().__init__(
            game_name="background_shop",
            results_folder=results_folder,
        )

        backgrounds_folder = self.get_asset_path("backgrounds")
        error_folder = self.get_asset_path("errors")
        self.backgrounds_folder = backgrounds_folder
        self.error_folder = error_folder
        
        os.makedirs(self.results_folder, exist_ok=True)
        os.makedirs(self.backgrounds_folder, exist_ok=True)
        os.makedirs(self.error_folder, exist_ok=True)
        
        self.price_ranges = {
            "cheap": (100, 500),
            "medium": (400, 1500), 
            "expensive": (1000, 5000)
        }
        
        self.daily_offers = {}
        self.last_update_date = None
        self.all_backgrounds = self._load_all_backgrounds()
        
        self.error_images = {}

    def _load_all_backgrounds(self):
        backgrounds = []
        if os.path.exists(self.backgrounds_folder):
            for file in os.listdir(self.backgrounds_folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    category = self._get_category_by_filename(file)
                    price = self._extract_price_from_filename(file)
                    
                    backgrounds.append({
                        "file": file,
                        "price": price,
                        "full_path": os.path.join(self.backgrounds_folder, file),
                        "category": category
                    })
        return backgrounds

    def _extract_price_from_filename(self, filename):
        filename_lower = filename.lower()
        
        if "cheap" in filename_lower:
            return random.randint(100, 500)
        elif "medium" in filename_lower:
            return random.randint(400, 1500)
        elif "expensive" in filename_lower or "premium" in filename_lower:
            return random.randint(1000, 5000)
        else:
            return random.randint(400, 5000)

    def _get_category_by_filename(self, filename):
        filename_lower = filename.lower()
        
        if "cheap" in filename_lower:
            return "cheap"
        elif "medium" in filename_lower:
            return "medium"
        elif "expensive" in filename_lower or "premium" in filename_lower:
            return "expensive"
        else:
            return "medium"

    def get_daily_seed(self):
        today = datetime.now().strftime("%Y%m%d")
        return int(today)

    def load_daily_offers(self):
        today = datetime.now().date()
        
        if self.last_update_date == today and self.daily_offers:
            return self.daily_offers
        
        self.daily_offers = {}
        seed = self.get_daily_seed()
        random.seed(seed)
        
        for category_name, price_range in self.price_ranges.items():
            category_backgrounds = [
                bg for bg in self.all_backgrounds 
                if bg["category"] == category_name
            ]
            
            if not category_backgrounds:
                category_backgrounds = [
                    bg for bg in self.all_backgrounds 
                    if price_range[0] <= bg["price"] <= price_range[1]
                ]
            
            if not category_backgrounds:
                continue
            
            selected_backgrounds = random.sample(
                category_backgrounds, 
                min(3, len(category_backgrounds))
            )
            
            display_name = category_name.upper()
            
            self.daily_offers[category_name] = {
                "display_name": display_name,
                "offers": selected_backgrounds
            }
        
        self.last_update_date = today
        return self.daily_offers

    def get_user_backgrounds(self, user_id):
        user = self.cache.get_user(user_id)
        if user and "backgrounds" in user:
            return user["backgrounds"]
        return []

    def get_user_backgrounds_for_display(self, user_id):
        user = self.cache.get_user(user_id)
        if not user:
            return ["default-bg.png"]
        
        user_backgrounds = self.get_user_backgrounds(user_id)
        
        display_backgrounds = ["default-bg.png"]
        
        for background in user_backgrounds:
            if background != "default-bg.png" and background not in display_backgrounds:
                display_backgrounds.append(background)
        
        return display_backgrounds

    def add_user_background(self, user_id, background_file):
        user = self.cache.get_user(user_id)
        if not user:
            return False
        
        if "backgrounds" not in user:
            user["backgrounds"] = []

        if background_file == "default-bg.png":
            return False
        
        if background_file not in user["backgrounds"]:
            user["backgrounds"].append(background_file)
            self.cache.update_user(user_id, backgrounds=user["backgrounds"])
            return True
        return False

    def remove_user_background(self, user_id, background_file):
        user = self.cache.get_user(user_id)
        if not user:
            return False
        
        if "backgrounds" not in user:
            return False
        
        if background_file == "default-bg.png":
            return False
        
        if background_file in user["backgrounds"]:
            user["backgrounds"].remove(background_file)
            self.cache.update_user(user_id, backgrounds=user["backgrounds"])
            return True
        return False

    def set_user_current_background(self, user_id, background_file):
        user = self.cache.get_user(user_id)
        if not user:
            return False
        
        user_backgrounds = self.get_user_backgrounds_for_display(user_id)
        
        if background_file == "default-bg.png":
            if user.get("background") == "default-bg.png":
                return True
            self.cache.update_user(user_id, background="default-bg.png")
            return True
        
        if background_file not in user_backgrounds:
            if user.get("background") == background_file:
                return True
            return False
        
        self.cache.update_user(user_id, background=background_file)
        return True

    def create_collection_image(self, user_backgrounds, current_bg, user_id, page=1, items_per_page=9):
        if not user_backgrounds:
            return None
        
        total_items = len(user_backgrounds)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        current_backgrounds = user_backgrounds[start_idx:end_idx]
        
        ITEM_WIDTH = 300
        ITEM_HEIGHT = 200
        MARGIN = 20
        ITEMS_PER_ROW = 3
        
        rows = (len(current_backgrounds) + ITEMS_PER_ROW - 1) // ITEMS_PER_ROW
        total_width = ITEM_WIDTH * ITEMS_PER_ROW + MARGIN * (ITEMS_PER_ROW + 1)
        total_height = (ITEM_HEIGHT + MARGIN) * rows + MARGIN * 3 + 60
        
        try:
            bg_path = self.cache.get_background_path(user_id)
            if bg_path and os.path.exists(bg_path):
                bg_img = Image.open(bg_path)
                bg_img = bg_img.resize((total_width, total_height), Image.LANCZOS)
                img = bg_img.convert('RGBA')
            else:
                img = Image.new('RGBA', (total_width, total_height), (20, 20, 30, 255))
        except Exception as e:
            logger.error(f"Error loading background for collection image: {e}")
            img = Image.new('RGBA', (total_width, total_height), (20, 20, 30, 255))
        
        top_bar_height = 80
        top_bar = Image.new('RGBA', (total_width, top_bar_height), (30, 30, 30))
        
        img.paste(top_bar, (0, 0), top_bar)
        
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
            command_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
            page_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
            active_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 12)
            default_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 10)
        except:
            title_font = ImageFont.load_default()
            command_font = ImageFont.load_default()
            page_font = ImageFont.load_default()
            active_font = ImageFont.load_default()
            default_font = ImageFont.load_default()
        
        title_text = "YOUR BACKGROUND COLLECTION"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_x = (total_width - (title_bbox[2] - title_bbox[0])) // 2
        draw.text((title_x, MARGIN), title_text, fill=(255, 255, 255), font=title_font)
        
        page_text = f"Page {page}/{total_pages}"
        page_bbox = draw.textbbox((0, 0), page_text, font=page_font)
        page_x = (total_width - (page_bbox[2] - page_bbox[0])) // 2
        draw.text((page_x, MARGIN + 35), page_text, fill=(200, 200, 200), font=page_font)
        
        y_offset = MARGIN + 90
        
        for idx, background_file in enumerate(current_backgrounds):
            row = idx // ITEMS_PER_ROW
            col = idx % ITEMS_PER_ROW
            
            x = MARGIN + col * (ITEM_WIDTH + MARGIN)
            y = y_offset + row * (ITEM_HEIGHT + MARGIN)
            
            draw.rectangle([x, y, x + ITEM_WIDTH, y + ITEM_HEIGHT], 
                          fill=(50, 50, 60, 220), outline=(100, 100, 120), width=2)
            
            actual_index = start_idx + idx
            
            if background_file == "default-bg.png":
                command_text = f"/bg set default"
            else:
                command_text = f"/bg set {actual_index + 1}"
            
            command_bbox = draw.textbbox((0, 0), command_text, font=command_font)
            command_x = x + (ITEM_WIDTH - (command_bbox[2] - command_bbox[0])) // 2
            command_y = y + 10
            draw.text((command_x, command_y), command_text, fill=(255, 255, 255), font=command_font)
            
            try:
                bg_path = os.path.join(self.backgrounds_folder, background_file)
                
                if os.path.exists(bg_path):
                    bg_img = Image.open(bg_path)
                    bg_img = bg_img.resize((ITEM_WIDTH - 40, ITEM_HEIGHT - 60), Image.LANCZOS)
                    
                    bg_x = x + (ITEM_WIDTH - bg_img.width) // 2
                    bg_y = y + (ITEM_HEIGHT - bg_img.height) // 2
                    img.paste(bg_img, (bg_x, bg_y))
                    
                    if background_file == "default-bg.png":
                        default_text = "DEFAULT"
                        default_bbox = draw.textbbox((0, 0), default_text, font=default_font)
                        default_x = x + (ITEM_WIDTH - (default_bbox[2] - default_bbox[0])) // 2
                        default_y = y + ITEM_HEIGHT - 35
                        draw.text((default_x, default_y), default_text, fill=(200, 200, 255), font=default_font)
                else:
                    name_text = os.path.splitext(background_file)[0]
                    if len(name_text) > 20:
                        name_text = name_text[:17] + "..."
                    name_bbox = draw.textbbox((0, 0), name_text, font=active_font)
                    name_x = x + (ITEM_WIDTH - (name_bbox[2] - name_bbox[0])) // 2
                    name_y = y + (ITEM_HEIGHT - (name_bbox[3] - name_bbox[1])) // 2
                    draw.text((name_x, name_y), name_text, fill=(200, 200, 200), font=active_font)
                    
            except Exception as e:
                logger.error(f"Error loading background image {background_file}: {e}")
                error_text = "IMAGE ERROR"
                error_bbox = draw.textbbox((0, 0), error_text, font=command_font)
                error_x = x + (ITEM_WIDTH - (error_bbox[2] - error_bbox[0])) // 2
                error_y = y + (ITEM_HEIGHT - (error_bbox[3] - error_bbox[1])) // 2
                draw.text((error_x, error_y), error_text, fill=(255, 100, 100), font=command_font)
            
            if background_file == current_bg:
                active_text = "ACTIVE"
                active_bbox = draw.textbbox((0, 0), active_text, font=active_font)
                active_x = x + (ITEM_WIDTH - (active_bbox[2] - active_bbox[0])) // 2
                if background_file == "default-bg.png":
                    active_y = y + ITEM_HEIGHT - 50
                else:
                    active_y = y + ITEM_HEIGHT - 25
                draw.text((active_x, active_y), active_text, fill=(100, 255, 100), font=active_font)
        
        if total_pages > 1:
            instructions_y = total_height - 25
            if page < total_pages:
                instructions = f"Use '/bg list {page + 1}' for next page"
            else:
                instructions = "Use '/bg list 1' for first page"
            
            inst_bbox = draw.textbbox((0, 0), instructions, font=active_font)
            inst_x = (total_width - (inst_bbox[2] - inst_bbox[0])) // 2
            draw.text((inst_x, instructions_y), instructions, fill=(200, 200, 255), font=active_font)
        
        return img

    def create_shop_image(self, output_path, user_id, user_backgrounds=None):
        if user_backgrounds is None:
            user_backgrounds = []
        
        offers = self.load_daily_offers()
        
        ITEM_WIDTH = 300
        ITEM_HEIGHT = 200
        MARGIN = 20
        CATEGORY_MARGIN = 40
        BOTTOM_SPACE = 80
        
        categories_count = len(offers)
        items_per_category = 3
        
        total_width = ITEM_WIDTH * items_per_category + MARGIN * (items_per_category + 1)
        total_height = (ITEM_HEIGHT + CATEGORY_MARGIN) * categories_count + MARGIN * 2 + BOTTOM_SPACE
        
        try:
            bg_path = self.cache.get_background_path(user_id)
            if bg_path and os.path.exists(bg_path):
                bg_img = Image.open(bg_path)
                bg_img = bg_img.resize((total_width, total_height), Image.LANCZOS)
                img = bg_img.convert('RGBA')
            else:
                img = Image.new('RGBA', (total_width, total_height), (20, 20, 30, 255))
        except Exception as e:
            logger.error(f"Error loading background for shop image: {e}")
            img = Image.new('RGBA', (total_width, total_height), (20, 20, 30, 255))
        
        top_bar_height = 100
        top_bar = Image.new('RGBA', (total_width, top_bar_height), (30, 30, 30))
        
        img.paste(top_bar, (0, 0), top_bar)
        
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
            category_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
            price_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
            command_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
            owned_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
        except:
            title_font = ImageFont.load_default()
            category_font = ImageFont.load_default()
            price_font = ImageFont.load_default()
            command_font = ImageFont.load_default()
            owned_font = ImageFont.load_default()
        
        title_text = "BACKGROUND SHOP"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_x = (total_width - (title_bbox[2] - title_bbox[0])) // 2
        draw.text((title_x, MARGIN), title_text, fill=(255, 255, 255), font=title_font)
        
        date_text = f"Offer valid: {datetime.now().strftime('%d.%m.%Y')}"
        date_bbox = draw.textbbox((0, 0), date_text, font=owned_font)
        date_x = (total_width - (date_bbox[2] - date_bbox[0])) // 2
        draw.text((date_x, MARGIN + 30), date_text, fill=(200, 200, 200), font=owned_font)
        
        market_text = "Check player market with: /market"
        market_bbox = draw.textbbox((0, 0), market_text, font=command_font)
        market_x = (total_width - (market_bbox[2] - market_bbox[0])) // 2
        draw.text((market_x, MARGIN + 55), market_text, fill=(255, 200, 100), font=command_font)
        
        y_offset = MARGIN + 85
        
        item_counter = 1
        for category_idx, (category, category_data) in enumerate(offers.items()):
            category_y = y_offset + category_idx * (ITEM_HEIGHT + CATEGORY_MARGIN)
            
            category_text = category_data["display_name"]
            category_bbox = draw.textbbox((0, 0), category_text, font=category_font)
            text_width = category_bbox[2] - category_bbox[0]
            text_height = category_bbox[3] - category_bbox[1]
            
            padding = 10
            rect_x = MARGIN - padding
            rect_y = category_y - padding
            rect_width = text_width + (padding * 2)
            rect_height = text_height + (padding * 2)
            
            draw.rectangle(
                [rect_x, rect_y, rect_x + rect_width, rect_y + rect_height],
                fill=(0, 0, 0, 220),
                outline=(255, 215, 0),
                width=2
            )
            
            draw.text((MARGIN, category_y), category_text, 
                    fill=(255, 215, 0), font=category_font)
            
            for item_idx, offer in enumerate(category_data["offers"]):
                x = MARGIN + item_idx * (ITEM_WIDTH + MARGIN)
                y = category_y + 30
                
                draw.rectangle([x, y, x + ITEM_WIDTH, y + ITEM_HEIGHT], 
                            fill=(50, 50, 60, 220), outline=(100, 100, 120), width=2)
                
                is_owned = offer["file"] in user_backgrounds
                
                if is_owned:
                    command_text = "✓ OWNED"
                    command_color = (100, 255, 100)
                    command_font_to_use = owned_font
                else:
                    command_text = f"/bg buy {item_counter}"
                    command_color = (255, 255, 255)
                    command_font_to_use = command_font
                
                command_bbox = draw.textbbox((0, 0), command_text, font=command_font_to_use)
                command_x = x + (ITEM_WIDTH - (command_bbox[2] - command_bbox[0])) // 2
                command_y = y + 10
                draw.text((command_x, command_y), command_text, fill=command_color, font=command_font_to_use)
                
                try:
                    bg_img = Image.open(offer["full_path"])
                    bg_img = bg_img.resize((ITEM_WIDTH - 40, ITEM_HEIGHT - 60), Image.LANCZOS)
                    
                    bg_x = x + (ITEM_WIDTH - bg_img.width) // 2
                    bg_y = y + (ITEM_HEIGHT - bg_img.height) // 2
                    img.paste(bg_img, (bg_x, bg_y))
                    
                except Exception as e:
                    error_text = "IMAGE ERROR"
                    error_bbox = draw.textbbox((0, 0), error_text, font=price_font)
                    error_x = x + (ITEM_WIDTH - (error_bbox[2] - error_bbox[0])) // 2
                    error_y = y + (ITEM_HEIGHT - (error_bbox[3] - error_bbox[1])) // 2
                    draw.text((error_x, error_y), error_text, fill=(255, 100, 100), font=price_font)
                
                price_text = f"{offer['price']}"
                price_bbox = draw.textbbox((0, 0), price_text, font=price_font)
                price_x = x + (ITEM_WIDTH - (price_bbox[2] - price_bbox[0])) // 2
                price_y = y + ITEM_HEIGHT - 25
                draw.text((price_x, price_y), price_text, fill=(100, 255, 100), font=price_font)
                
                item_counter += 1
        
        img.save(output_path, format='WEBP', quality=85, optimize=True)
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
        
        if len(args) == 0:
            args = ["list", "1"]
    
        cmd = args[0].lower()
        
        if cmd == "list":
            user_backgrounds = self.get_user_backgrounds_for_display(user_id)
            if not user_backgrounds:
                self._send_error_image("no_backgrounds", nickname, file_queue)
                return ""
            
            page = 1
            if len(args) > 1:
                try:
                    page = int(args[1])
                except ValueError:
                    page = 1
            
            current_bg = user.get("background", "default-bg.png")
            collection_img = self.create_collection_image(user_backgrounds, current_bg, user_id, page)
            
            if collection_img:
                img_path = os.path.join(self.results_folder, f"collection_{user_id}_page{page}.webp")
                collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                
                collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                
                overlay_path, error = self.apply_user_overlay(
                    img_path, user_id, sender, 0, 0, user["balance"], user
                )
                if overlay_path:
                    file_queue.put(overlay_path)
                
                total_pages = (len(user_backgrounds) + 8) // 9
                page_info = f" (Page {page}/{total_pages})" if total_pages > 1 else ""
                return f"Your background collection{page_info}!\nUse `/bg set <number>` to set active background."
            else:
                self._send_error_image("image_generation_error", nickname, file_queue)
                return ""
            
        elif cmd == "shop" :
            user_backgrounds = self.get_user_backgrounds(user_id)
            img_path = os.path.join(self.results_folder, f"shop_{user_id}.webp")
            self.create_shop_image(img_path, user_id, user_backgrounds)
            
            shop_img = Image.open(img_path).convert('RGBA')
            shop_img.save(img_path, format='WEBP', quality=85, optimize=True)
            
            overlay_path, error = self.apply_user_overlay(
                img_path, user_id, sender, 0, 0, user["balance"], user
            )
            if overlay_path:
                file_queue.put(overlay_path)
            
            return "**Background Shop**\nUse `/bg buy <number>` to purchase.\nSell your backgrounds with `/bg sell`!"
        
        elif cmd == "buy":
            if len(args) < 2:
                self._send_error_image("invalid_usage_bg", nickname, file_queue, "Usage: /bg buy <number>")
                return ""
            
            try:
                item_number = int(args[1])
            except ValueError:
                self._send_error_image("invalid_number", nickname, file_queue)
                return ""
            
            if not 1 <= item_number <= 9:
                self._send_error_image("invalid_range_buy", nickname, file_queue, "Number must be 1-9")
                return ""
            
            offers = self.load_daily_offers()
            
            item_index = item_number - 1
            category_index = item_index // 3
            item_in_category_index = item_index % 3
            
            categories = list(offers.keys())
            if category_index >= len(categories):
                self._send_error_image("invalid_range_buy", nickname, file_queue)
                return ""
            
            category = categories[category_index]
            category_offers = offers[category]["offers"]
            
            if item_in_category_index >= len(category_offers):
                self._send_error_image("invalid_range_buy", nickname, file_queue)
                return ""
            
            offer = category_offers[item_in_category_index]
            price = offer["price"]
            
            user_backgrounds = self.get_user_backgrounds(user_id)
            if offer["file"] in user_backgrounds:
                self._send_error_image("already_owned", nickname, file_queue)
                return ""
            
            if user["balance"] < price:
                self._send_error_image("insufficient_funds", nickname, file_queue, f"Need: {price}, Have: {user['balance']}")
                return ""
            
            new_balance = user["balance"] - price
            self.update_user_balance(user_id, new_balance)
            self.add_user_background(user_id, offer["file"])
            
            self.set_user_current_background(user_id, offer["file"])
            
            user["balance"] = new_balance
            user["background"] = offer["file"]
            
            user_backgrounds = self.get_user_backgrounds_for_display(user_id)
            
            shop_img_path = os.path.join(self.results_folder, f"shop_after_buy_{user_id}.webp")
            self.create_shop_image(shop_img_path, user_id, user_backgrounds)
            
            shop_img = Image.open(shop_img_path).convert('RGBA')
            shop_img.save(shop_img_path, format='WEBP', quality=85, optimize=True)
            
            overlay_path, error = self.apply_user_overlay(
                shop_img_path, user_id, sender, -price, 0, user["balance"], user
            )
            if overlay_path:
                file_queue.put(overlay_path)
            
            return f"Purchased & activated: **{offer['file']}** for {price} coins!\nCheck your collection with `/bg list`"

        elif cmd == "sell":
            if len(args) < 2:
                self._send_error_image(
                    "invalid_usage_bg", 
                    nickname, 
                    file_queue, 
                    "Usage: /bg sell <number>\nCheck available backgrounds with: /bg list"
                )
                return ""
            
            if args[1].lower() == "default":
                self._send_error_image("cannot_sell_default_bg", nickname, file_queue)
                return ""
            
            try:
                index = int(args[1]) - 1
                user_backgrounds = self.get_user_backgrounds_for_display(user_id)
                
                if index < 0 or index >= len(user_backgrounds):
                    self._send_error_image(
                        "invalid_range_sell_bg", 
                        nickname, 
                        file_queue, 
                        f"Choose 1-{len(user_backgrounds)}\nYou have {len(user_backgrounds)} backgrounds."
                    )
                    return ""
                
                background_file = user_backgrounds[index]
                
                if background_file == "default-bg.png":
                    self._send_error_image("cannot_sell_default_bg", nickname, file_queue)
                    return ""
                
                user_real_backgrounds = self.get_user_backgrounds(user_id)
                if background_file not in user_real_backgrounds:
                    self._send_error_image("not_owned_bg", nickname, file_queue, f"You don't own: {background_file}")
                    return ""
                
                current_bg = user.get("background", "")
                if background_file == current_bg:
                    self._send_error_image("cannot_sell_active_bg", nickname, file_queue)
                    return ""
                
                background_path = os.path.join(self.backgrounds_folder, background_file)
                if not os.path.exists(background_path):
                    self._send_error_image("sell_error", nickname, file_queue, f"Background file not found: {background_file}")
                    return ""
                
                if not hasattr(self.cache, 'market_backgrounds'):
                    self.cache.market_backgrounds = []
                
                self.cache.add_market_item("background", background_file)
                
                success = self.remove_user_background(user_id, background_file)
                if not success:
                    self._send_error_image("sell_error", nickname, file_queue, f"Failed to remove background: {background_file}")
                    return ""
                
                self.cache.update_balance(user_id, 100)
                user["balance"] += 100
                
                user_backgrounds = self.get_user_backgrounds_for_display(user_id)
                collection_img = self.create_collection_image(user_backgrounds, user.get("background", ""), user_id, 1)
                
                if collection_img:
                    img_path = os.path.join(self.results_folder, f"collection_after_sell_{user_id}.webp")
                    collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                    
                    collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                    
                    overlay_path, error = self.apply_user_overlay(
                        img_path, user_id, sender, 100, 100, user["balance"], user
                    )
                    if overlay_path:
                        file_queue.put(overlay_path)
                    
                    return f"✅ Sold **{background_file}** for 100 coins!\nCheck your updated collection."
                else:
                    self._send_error_image(
                        "sell_success_bg", 
                        nickname, 
                        file_queue, 
                        f"Sold: {background_file}\nPrice: 100 coins\nNew balance: {user['balance']} coins"
                    )
                    return ""
                    
            except ValueError:
                self._send_error_image(
                    "invalid_range_sell_bg", 
                    nickname, 
                    file_queue, 
                    f"Usage: /bg sell <number>\n'{args[1]}' is not a valid number."
                )
                return ""

        elif cmd == "set":
            if len(args) < 2:
                self._send_error_image("invalid_usage_bg", nickname, file_queue, "Usage: /bg set <number>")
                return ""
            
            set_arg = " ".join(args[1:])
            user_backgrounds = self.get_user_backgrounds_for_display(user_id)
            
            try:
                if set_arg.lower() == "default":
                    background_name = "default-bg.png"
                    item_number = 1
                else:
                    item_number = int(set_arg)
                    if 1 <= item_number <= len(user_backgrounds):
                        background_name = user_backgrounds[item_number - 1]
                    else:
                        self._send_error_image("invalid_range_set_bg", nickname, file_queue, f"Choose 1-{len(user_backgrounds)}")
                        return ""
            except ValueError:
                background_name = set_arg
            
            if background_name not in user_backgrounds:
                self._send_error_image("not_owned_bg", nickname, file_queue, f"You don't own: {background_name}")
                return ""
            
            if self.set_user_current_background(user_id, background_name):               
                user_backgrounds = self.get_user_backgrounds_for_display(user_id)
                current_bg = user.get("background", "default-bg.png")
                
                page_with_item = 1
                if item_number > 9:
                    page_with_item = (item_number - 1) // 9 + 1
                
                collection_img = self.create_collection_image(user_backgrounds, current_bg, user_id, page_with_item)
                
                if collection_img:
                    img_path = os.path.join(self.results_folder, f"collection_after_set_{user_id}.webp")
                    collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                    
                    collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                    
                    overlay_path, error = self.apply_user_overlay(
                        img_path, user_id, sender, 0, 0, user["balance"], user
                    )
                    if overlay_path:
                        file_queue.put(overlay_path)
                    
                    return f"✅ Background set to: **{background_name}**\nNow active in your collection!"
                else:
                    self._send_error_image("set_success", nickname, file_queue, f"Background set to: {background_name}")
                    return ""
            else:
                self._send_error_image("set_error_bg", nickname, file_queue)
                return ""

def register():
    plugin = BackgroundShopPlugin()
    return {
        "name": "background",
        "aliases": ["/bg"],
        "description": "Background shop: /bg, /bg buy <1-9>, /bg list, /bg set, /bg sell",
        "execute": plugin.execute_game
    }