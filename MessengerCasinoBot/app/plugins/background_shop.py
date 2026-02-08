import os
import random
import time
from PIL import Image, ImageDraw
from datetime import datetime
from base_game_plugin import BaseGamePlugin
from logger import logger

class BackgroundShopPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="background_shop")
        
        self.backgrounds_folder = self.get_asset_path("backgrounds")
        self.error_folder = self.get_asset_path("errors")
        
        os.makedirs(self.backgrounds_folder, exist_ok=True)
        os.makedirs(self.error_folder, exist_ok=True)
        
        self.available_backgrounds_cache = None
        self.backgrounds_cache_time = None
        
        self.quick_sell_prices = {
            "cheap": 100,
            "medium": 300,
            "expensive": 900
        }
        
        self.crafting_requirements = {
            "medium": {"type": "cheap", "count": 3},
            "expensive": {"type": "medium", "count": 3}
        }
        
        self.price_ranges = {
            "cheap": (100, 500),
            "medium": (400, 1500),
            "expensive": (1000, 5000)
        }
        
        self.daily_offers = {}
        self.all_backgrounds = self._load_all_backgrounds()
        self.auction_listing_fee = 5

    def _load_all_backgrounds(self):
        backgrounds = []
        if os.path.exists(self.backgrounds_folder):
            for file in os.listdir(self.backgrounds_folder):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    category = self._get_category_by_filename(file)
                    backgrounds.append({
                        "file": file,
                        "price": self._extract_price_from_filename(file),
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
        elif "expensive" in filename_lower:
            return "expensive"
        else:
            return "medium"

    def get_daily_seed(self, username=None):
        today = datetime.now().strftime("%Y%m%d")
        
        if username:
            import hashlib
            seed_str = f"{today}{username}"
            seed_hash = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
            return seed_hash
        else:
            return int(today)

    def load_daily_offers(self, username=None):
        today = datetime.now().date()
        
        if not username:
            username = "default"
        
        if username in self.daily_offers:
            user_data = self.daily_offers[username]
            if user_data["date"] == today:
                return user_data["offers"]
        
        seed = self.get_daily_seed(username)
        random.seed(seed)
        
        offers = {}
        
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
            
            offers[category_name] = {
                "display_name": category_name.upper(),
                "offers": selected_backgrounds
            }
        
        self.daily_offers[username] = {
            "date": today,
            "offers": offers
        }
        
        return offers

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
        except Exception:
            img = Image.new('RGBA', (total_width, total_height), (20, 20, 30, 255))

        top_bar_height = 80
        top_bar = Image.new('RGBA', (total_width, top_bar_height), (30, 30, 30))
        img.paste(top_bar, (0, 0), top_bar)
        
        if hasattr(self, 'text_renderer'):
            title_text = "YOUR BACKGROUND COLLECTION"
            title_img = self.text_renderer.render_text(
                text=title_text,
                font_size=24,
                color=(255, 255, 255, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255)
            )
            title_x = (total_width - title_img.width) // 2
            img.paste(title_img, (title_x, MARGIN), title_img)
            
            page_text = f"Page {page}/{total_pages}"
            page_img = self.text_renderer.render_text(
                text=page_text,
                font_size=16,
                color=(200, 200, 200, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255)
            )
            page_x = (total_width - page_img.width) // 2
            img.paste(page_img, (page_x, MARGIN + 35), page_img)
        else:
            draw = ImageDraw.Draw(img)
            title_text = "YOUR BACKGROUND COLLECTION"
            title_bbox = draw.textbbox((0, 0), title_text)
            title_x = (total_width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, MARGIN), title_text, fill=(255, 255, 255))
            
            page_text = f"Page {page}/{total_pages}"
            page_bbox = draw.textbbox((0, 0), page_text)
            page_x = (total_width - (page_bbox[2] - page_bbox[0])) // 2
            draw.text((page_x, MARGIN + 35), page_text, fill=(200, 200, 200))
        
        y_offset = MARGIN + 70
        
        for idx, background_file in enumerate(current_backgrounds):
            row = idx // ITEMS_PER_ROW
            col = idx % ITEMS_PER_ROW
            
            x = MARGIN + col * (ITEM_WIDTH + MARGIN)
            y = y_offset + row * (ITEM_HEIGHT + MARGIN)
            
            draw_rect = ImageDraw.Draw(img)
            draw_rect.rectangle([x, y, x + ITEM_WIDTH, y + ITEM_HEIGHT],
                              fill=(50, 50, 60, 220), outline=(100, 100, 120), width=2)
            
            actual_index = start_idx + idx
            
            if hasattr(self, 'text_renderer'):
                if background_file == "default-bg.png":
                    command_text = f"/bg set default"
                else:
                    command_text = f"/bg set {actual_index + 1}"
                
                command_img = self.text_renderer.render_text(
                    text=command_text,
                    font_size=14,
                    color=(255, 255, 255, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                command_x = x + (ITEM_WIDTH - command_img.width) // 2
                command_y = y + 10
                img.paste(command_img, (command_x, command_y), command_img)
            
            try:
                bg_path = os.path.join(self.backgrounds_folder, background_file)
                
                if os.path.exists(bg_path):
                    bg_img = Image.open(bg_path)
                    bg_img = bg_img.resize((ITEM_WIDTH - 40, ITEM_HEIGHT - 60), Image.LANCZOS)
                    
                    bg_x = x + (ITEM_WIDTH - bg_img.width) // 2
                    bg_y = y + (ITEM_HEIGHT - bg_img.height) // 2
                    img.paste(bg_img, (bg_x, bg_y))
                    
                    if background_file == "default-bg.png" and hasattr(self, 'text_renderer'):
                        default_img = self.text_renderer.render_text(
                            text="DEFAULT",
                            font_size=10,
                            color=(200, 200, 255, 255),
                            stroke_width=1,
                            stroke_color=(0, 0, 0, 255)
                        )
                        default_x = x + (ITEM_WIDTH - default_img.width) // 2
                        default_y = y + ITEM_HEIGHT - 35
                        img.paste(default_img, (default_x, default_y), default_img)
                elif hasattr(self, 'text_renderer'):
                    name_text = os.path.splitext(background_file)[0][:20]
                    name_img = self.text_renderer.render_text(
                        text=name_text,
                        font_size=12,
                        color=(200, 200, 200, 255),
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )
                    name_x = x + (ITEM_WIDTH - name_img.width) // 2
                    name_y = y + (ITEM_HEIGHT - name_img.height) // 2
                    img.paste(name_img, (name_x, name_y), name_img)
                
            except Exception:
                if hasattr(self, 'text_renderer'):
                    error_img = self.text_renderer.render_text(
                        text="IMAGE ERROR",
                        font_size=14,
                        color=(255, 100, 100, 255),
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )
                    error_x = x + (ITEM_WIDTH - error_img.width) // 2
                    error_y = y + (ITEM_HEIGHT - error_img.height) // 2
                    img.paste(error_img, (error_x, error_y), error_img)
            
            if background_file != "default-bg.png" and hasattr(self, 'text_renderer'):
                rarity = self._get_category_by_filename(background_file)
                rarity_text = rarity.upper()
                
                if rarity == "cheap":
                    rarity_color = (255, 100, 100, 255)
                elif rarity == "medium":
                    rarity_color = (255, 200, 100, 255)
                else:
                    rarity_color = (100, 255, 100, 255)
                
                rarity_img = self.text_renderer.render_text(
                    text=rarity_text,
                    font_size=11,
                    color=rarity_color,
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                rarity_x = x + (ITEM_WIDTH - rarity_img.width) // 2
                rarity_y = y + ITEM_HEIGHT - 45
                img.paste(rarity_img, (rarity_x, rarity_y), rarity_img)
            
            if background_file == current_bg and hasattr(self, 'text_renderer'):
                active_img = self.text_renderer.render_text(
                    text="ACTIVE",
                    font_size=12,
                    color=(100, 255, 100, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                active_x = x + (ITEM_WIDTH - active_img.width) // 2
                if background_file == "default-bg.png":
                    active_y = y + ITEM_HEIGHT - 50
                else:
                    active_y = y + ITEM_HEIGHT - 30
                img.paste(active_img, (active_x, active_y), active_img)
        
        if total_pages > 1 and hasattr(self, 'text_renderer'):
            instructions_y = total_height - 25
            if page < total_pages:
                instructions = f"Use '/bg list {page + 1}' for next page"
            else:
                instructions = "Use '/bg list 1' for first page"
            
            inst_img = self.text_renderer.render_text(
                text=instructions,
                font_size=14,
                color=(200, 200, 255, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255)
            )
            inst_x = (total_width - inst_img.width) // 2
            img.paste(inst_img, (inst_x, instructions_y), inst_img)
        
        return img
    
    def create_shop_image(self, output_path, user_id, user_backgrounds=None, username=None):
        if user_backgrounds is None:
            user_backgrounds = []
        
        offers = self.load_daily_offers(username)
        
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
        except Exception:
            img = Image.new('RGBA', (total_width, total_height), (20, 20, 30, 255))
        
        top_bar_height = 100
        top_bar = Image.new('RGBA', (total_width, top_bar_height), (30, 30, 30))
        img.paste(top_bar, (0, 0), top_bar)
        
        if hasattr(self, 'text_renderer'):
            title_text = "BACKGROUND SHOP"
            title_img = self.text_renderer.render_text(
                text=title_text,
                font_size=24,
                color=(255, 255, 255, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255)
            )
            title_x = (total_width - title_img.width) // 2
            img.paste(title_img, (title_x, MARGIN), title_img)
            
            date_text = f"Offer valid: {datetime.now().strftime('%d.%m.%Y')}"
            date_img = self.text_renderer.render_text(
                text=date_text,
                font_size=14,
                color=(200, 200, 200, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255)
            )
            date_x = (total_width - date_img.width) // 2
            img.paste(date_img, (date_x, MARGIN + 30), date_img)
            
            market_text = "Check player market with: /market"
            market_img = self.text_renderer.render_text(
                text=market_text,
                font_size=14,
                color=(255, 200, 100, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255)
            )
            market_x = (total_width - market_img.width) // 2
            img.paste(market_img, (market_x, MARGIN + 55), market_img)
            
            personal_text = f"Personal offer for: {username}"
            personal_img = self.text_renderer.render_text(
                text=personal_text,
                font_size=14,
                color=(200, 255, 200, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255)
            )
            personal_x = (total_width - personal_img.width) // 2
            img.paste(personal_img, (personal_x, MARGIN + 80), personal_img)
        
        y_offset = MARGIN + 105
        
        item_counter = 1
        for category_idx, (category, category_data) in enumerate(offers.items()):
            category_y = y_offset + category_idx * (ITEM_HEIGHT + CATEGORY_MARGIN)
            
            if hasattr(self, 'text_renderer'):
                category_img = self.text_renderer.render_text(
                    text=category_data["display_name"],
                    font_size=20,
                    color=(255, 215, 0, 255),
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 255)
                )
                category_x = MARGIN
                img.paste(category_img, (category_x, category_y), category_img)
            
            for item_idx, offer in enumerate(category_data["offers"]):
                x = MARGIN + item_idx * (ITEM_WIDTH + MARGIN)
                y = category_y + 30
                
                draw_rect = ImageDraw.Draw(img)
                draw_rect.rectangle([x, y, x + ITEM_WIDTH, y + ITEM_HEIGHT],
                                  fill=(50, 50, 60, 220), outline=(100, 100, 120), width=2)
                
                is_owned = offer["file"] in user_backgrounds
                
                if hasattr(self, 'text_renderer'):
                    if is_owned:
                        command_text = "✓ OWNED"
                        command_color = (100, 255, 100, 255)
                    else:
                        command_text = f"/bg buy {item_counter}"
                        command_color = (255, 255, 255, 255)
                    
                    command_img = self.text_renderer.render_text(
                        text=command_text,
                        font_size=14,
                        color=command_color,
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )
                    command_x = x + (ITEM_WIDTH - command_img.width) // 2
                    command_y = y + 10
                    img.paste(command_img, (command_x, command_y), command_img)
                
                try:
                    bg_img = Image.open(offer["full_path"])
                    bg_img = bg_img.resize((ITEM_WIDTH - 40, ITEM_HEIGHT - 60), Image.LANCZOS)
                    
                    bg_x = x + (ITEM_WIDTH - bg_img.width) // 2
                    bg_y = y + (ITEM_HEIGHT - bg_img.height) // 2
                    img.paste(bg_img, (bg_x, bg_y))
                    
                except Exception:
                    if hasattr(self, 'text_renderer'):
                        error_img = self.text_renderer.render_text(
                            text="IMAGE ERROR",
                            font_size=18,
                            color=(255, 100, 100, 255),
                            stroke_width=1,
                            stroke_color=(0, 0, 0, 255)
                        )
                        error_x = x + (ITEM_WIDTH - error_img.width) // 2
                        error_y = y + (ITEM_HEIGHT - error_img.height) // 2
                        img.paste(error_img, (error_x, error_y), error_img)
                
                if hasattr(self, 'text_renderer'):
                    price_img = self.text_renderer.render_text(
                        text=str(offer['price']),
                        font_size=18,
                        color=(100, 255, 100, 255),
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )
                    price_x = x + (ITEM_WIDTH - price_img.width) // 2
                    price_y = y + ITEM_HEIGHT - 25
                    img.paste(price_img, (price_x, price_y), price_img)
                
                item_counter += 1
        
        img.save(output_path, format='WEBP', quality=85, optimize=True)
        return output_path
    
    def quick_sell_background(self, user_id, background_file):
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"
        
        if background_file == "default-bg.png":
            return False, "Cannot quick sell default background"
        
        if background_file == user.get("background"):
            return False, "Cannot quick sell active background"
        
        user_backgrounds = self.get_user_backgrounds_for_display(user_id)
        if background_file not in user_backgrounds:
            return False, "You don't own this background"
        
        category = self._get_category_by_filename(background_file)
        price = self.quick_sell_prices.get(category, 100)
        
        success = self.remove_user_background(user_id, background_file)
        if not success:
            return False, "Failed to remove background"
        
        self.cache.update_balance(user_id, price)
        
        return True, f"Quick sold **{background_file}** for {price} coins!\nBackground has been removed."

    def sell_background_for_price(self, user_id, background_file, price):
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"
        
        if background_file == "default-bg.png":
            return False, "Cannot sell default background"
        
        if background_file == user.get("background"):
            return False, "Cannot sell active background"
        
        if price < 50 or price > 10000:
            return False, "Price must be between 50 and 10,000 coins"
        
        user_backgrounds = self.get_user_backgrounds_for_display(user_id)
        if background_file not in user_backgrounds:
            return False, "You don't own this background"
        
        success = self.remove_user_background(user_id, background_file)
        if not success:
            return False, "Failed to remove background from collection"
        
        market_item = {
            "type": "background",
            "file": background_file,
            "price": price,
            "seller_id": user_id,
            "seller_name": user.get("name", ""),
            "listed_at": time.time(),
            "status": "for_sale",
            "category": self._get_category_by_filename(background_file)
        }
        
        self.cache.add_market_item(market_item)
        
        return True, f"Listed **{background_file}** on market for {price} coins!\nYou'll get paid when someone buys it."
    
    def cancel_market_listing(self, user_id, market_index):
        market_items = self.cache.get_market_items()
        
        if market_index < 0 or market_index >= len(market_items):
            return False, "Invalid item number"
        
        item = market_items[market_index]
        
        if item.get("seller_id") != user_id:
            return False, "This is not your item"
        
        if item.get("type") != "background":
            return False, "This is not a background item"
        
        background_file = item.get("file")
        
        success = self.add_user_background(user_id, background_file)
        if not success:
            return False, "Failed to return background to your collection"
        
        self.cache.remove_market_item(background_file)
        
        return True, f"Cancelled listing for **{background_file}**\nThe background has been returned to your collection."
                
    def create_crafting_animation(self, user_id, used_files, result_file, source_category, target_category, file_queue):
        try:
            import gc
            from PIL import Image

            available_bgs = [bg["file"] for bg in self.all_backgrounds]
            
            if not available_bgs or result_file not in available_bgs:
                return False

            width, height = 240, 240
            bg_color = (30, 30, 40)
            bg_size = 120
            bg_x = (width - bg_size) // 2
            bg_y = 70

            use_text_renderer = hasattr(self, 'text_renderer')
            
            base = Image.new("RGBA", (width, height), bg_color)
            
            if use_text_renderer:
                title_img = self.text_renderer.render_text(
                    text="BACKGROUND CRAFT",
                    font_size=16,
                    color=(120, 220, 255, 255),
                    stroke_width=2
                )
                base.paste(title_img, ((width-title_img.width)//2, 6), title_img)
                
                info_img = self.text_renderer.render_text(
                    text=f"{source_category} → {target_category}",
                    font_size=11,
                    color=(200, 200, 220, 255)
                )
                base.paste(info_img, ((width-info_img.width)//2, 26), info_img)

            def create_frame(bg_image=None, text_offset=40):
                frame = base.copy()

                if bg_image:
                    frame.paste(bg_image, (bg_x, bg_y), bg_image)

                if text_offset < 40 and use_text_renderer:
                    txt_img = self.text_renderer.render_text(
                        text=f"Obtained: {result_file}",
                        font_size=12,
                        color=(210, 230, 255, 255)
                    )
                    frame.paste(txt_img, ((width-txt_img.width)//2, 50+text_offset), txt_img)

                return frame.convert("RGB")

            frames = []
            durations = []

            other_paths = []
            for bg in self.all_backgrounds:
                if bg["file"] != result_file:
                    other_paths.append(bg["full_path"])
            
            other_paths = [p for p in other_paths if os.path.exists(p)]
            
            if not other_paths:
                return False

            roll_count = min(18, len(other_paths) * 2)

            for i in range(roll_count):
                path = random.choice(other_paths)
                try:
                    img = Image.open(path).convert("RGBA")
                    img = img.resize((bg_size, bg_size), Image.LANCZOS)
                except Exception:
                    img = Image.new("RGBA", (bg_size, bg_size), (100, 100, 100, 255))

                duration = 70 if i < roll_count // 3 else 50 if i < 2 * roll_count // 3 else 30
                frames.append(create_frame(img))
                durations.append(duration)

            result_path = os.path.join(self.backgrounds_folder, result_file)
            if not os.path.exists(result_path):
                return False
                
            try:
                winner = Image.open(result_path).convert("RGBA")
                winner = winner.resize((bg_size, bg_size), Image.LANCZOS)
            except Exception:
                return False

            for _ in range(3):
                frames.append(create_frame(winner, text_offset=40))
                durations.append(40)

            highlight_frames = 8
            for i in range(highlight_frames):
                progress = i / highlight_frames
                offset = int(40 * (1 - progress**0.7))
                frames.append(create_frame(winner, text_offset=offset))
                durations.append(90 if i < 4 else 70)

            frames.append(create_frame(winner, text_offset=0))
            durations.append(3000)

            output = os.path.join(self.results_folder, f"craft_bg_{user_id}_{int(time.time())}.webp")

            frames[0].save(
                output,
                format="WEBP",
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=0,
                quality=80,
                method=6
            )

            del frames, durations, winner, base
            gc.collect()

            return output

        except Exception as e:
            logger.error(f"[Background] Craft animation error: {e}")
            return False

    def create_background_auction(self, user_id, background_file, start_price, min_bid, duration_hours):
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"
        
        if background_file == "default-bg.png":
            return False, "Cannot auction default background"
        
        if background_file == user.get("background"):
            return False, "Cannot auction active background"
        
        if start_price < 50 or start_price > 10000:
            return False, "Start price must be between 50 and 10,000 coins"
        
        if min_bid < 10 or min_bid > 1000:
            return False, "Minimum bid must be between 10 and 1,000 coins"
        
        if duration_hours < 1 or duration_hours > 168:
            return False, "Auction duration must be 1-168 hours (1-7 days)"
        
        if user["balance"] < self.auction_listing_fee:
            return False, f"Need {self.auction_listing_fee} coins auction fee"
        
        self.cache.update_balance(user_id, -self.auction_listing_fee)
        
        success = self.remove_user_background(user_id, background_file)
        if not success:
            self.cache.update_balance(user_id, self.auction_listing_fee)
            return False, "Failed to remove background from collection"
        
        auction = {
            "type": "background",
            "file": background_file,
            "start_price": start_price,
            "current_price": start_price,
            "min_bid": min_bid,
            "seller_id": user_id,
            "seller_name": user.get("name", ""),
            "created_at": time.time(),
            "ends_at": time.time() + (duration_hours * 3600),
            "status": "active",
            "bids": [],
            "current_bidder": None,
            "category": self._get_category_by_filename(background_file)
        }
        
        self.cache.add_auction(auction)
        
        return True, f"Created auction for **{background_file}**!\nStart price: {start_price} coins\nMin bid: {min_bid} coins\nDuration: {duration_hours} hours"

    def craft_backgrounds(self, user_id, background_indices, file_queue):
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"
        
        if len(background_indices) != 3:
            return False, "Need exactly 3 backgrounds to craft"
        
        user_backgrounds = self.get_user_backgrounds_for_display(user_id)
        background_files = []
        
        for idx in background_indices:
            if idx < 0 or idx >= len(user_backgrounds):
                return False, f"Invalid background number: #{idx+1}"
            bg_file = user_backgrounds[idx]
            background_files.append(bg_file)
        
        if len(set(background_files)) != 3:
            return False, "You must use 3 different backgrounds"
        
        categories = [self._get_category_by_filename(bg) for bg in background_files]
        
        if not all(cat == categories[0] for cat in categories):
            return False, "All 3 backgrounds must be of same rarity"
        
        source_category = categories[0]
        
        if source_category not in ["cheap", "medium"]:
            return False, f"Cannot craft from {source_category} backgrounds. Only 'cheap' or 'medium' backgrounds."
        
        current_bg = user.get("background", "default-bg.png")
        
        for bg_file in background_files:
            if bg_file == current_bg:
                return False, "Cannot use active background for crafting"
            if bg_file == "default-bg.png":
                return False, "Cannot use default background for crafting"
        
        for bg_file in background_files:
            self.remove_user_background(user_id, bg_file)
        
        target_category = "medium" if source_category == "cheap" else "expensive"
        
        available_upgrades = [
            bg for bg in self.all_backgrounds 
            if bg["category"] == target_category and bg["file"] not in user_backgrounds
        ]
        
        if not available_upgrades:
            available_upgrades = [
                bg for bg in self.all_backgrounds 
                if bg["category"] == target_category
            ]
        
        if not available_upgrades:
            return False, "No backgrounds available for crafting result"
        
        new_background = random.choice(available_upgrades)
        new_file = new_background["file"]
        
        self.add_user_background(user_id, new_file)
        
        animation_path = self.create_crafting_animation(user_id, background_files, new_file, source_category, target_category, file_queue)
        
        if animation_path:
            file_queue.put(animation_path)
            return True, {
                "message": f"Crafting successful!\nUsed 3 {source_category} backgrounds\nObtained: **{new_file}** ({target_category})",
                "animation": animation_path,
                "type": "crafting_animation"
            }
        else:
            return True, f"Crafting successful!\nUsed 3 {source_category} backgrounds\nObtained: **{new_file}** ({target_category})"

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 0)
        
        if error:
            self.send_message_image(sender, file_queue, error, "Validation Error", cache, user_id)
            return ""
        
        nickname = sender
        
        if len(args) == 0:
            args = ["list", "1"]
    
        cmd = args[0].lower()
        
        if cmd == "quicksell" or cmd == "qs" or cmd == "q":
            if len(args) < 2:
                self.send_message_image(
                    sender, 
                    file_queue, 
                    "**Quick Sell Backgrounds**\nUsage: `/bg quicksell <number>`\nExample: `/bg quicksell 3`\n\nQuick sell prices:\n• Cheap: 100 coins\n• Medium: 300 coins\n• Expensive: 900 coins\n\nBackground is destroyed after sale!",
                    "QUICKSELL HELP", 
                    cache, 
                    user_id
                )
                return ""
            
            try:
                index = int(args[1]) - 1
                user_backgrounds = self.get_user_backgrounds_for_display(user_id)
                
                if index < 0 or index >= len(user_backgrounds):
                    self.send_message_image(
                        sender, 
                        file_queue, 
                        f"Choose number 1-{len(user_backgrounds)}\nYou have {len(user_backgrounds)} backgrounds.", 
                        "INVALID RANGE", 
                        cache, 
                        user_id
                    )
                    return ""
                
                background_file = user_backgrounds[index]
                
                success, message = self.quick_sell_background(user_id, background_file)
                
                if success:
                    category = self._get_category_by_filename(background_file)
                    price = self.quick_sell_prices.get(category, 100)
                    
                    user_backgrounds = self.get_user_backgrounds_for_display(user_id)
                    collection_img = self.create_collection_image(user_backgrounds, user.get("background", ""), user_id, 1)
                    
                    if collection_img:
                        img_path = os.path.join(self.results_folder, f"collection_after_quicksell_{user_id}.webp")
                        collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                        
                        overlay_path, error = self.apply_user_overlay(
                            img_path, user_id, sender, price, price, 
                            user["balance"], user, show_win_text=False, show_bet_amount=False
                        )
                        if overlay_path:
                            file_queue.put(overlay_path)
                    
                    return f"{message}"
                else:
                    self.send_message_image(sender, file_queue, message, "QUICKSELL ERROR", cache, user_id)
                    return ""
                    
            except ValueError:
                self.send_message_image(
                    sender, 
                    file_queue, 
                    f"Usage: `/bg quicksell <number>`\n'{args[1]}' is not a valid number.", 
                    "INVALID NUMBER", 
                    cache, 
                    user_id
                )
                return ""
        
        elif cmd == "sellprice" or cmd == "sell" or cmd == "s":
            if len(args) < 3:
                self.send_message_image(
                    sender, 
                    file_queue, 
                    "**Market List Background**\nUsage: `/bg sellprice <number> <price>`\nExample: `/bg sellprice 3 1500`\n\nPrice: 50-10,000 coins\nFree listing!\n\nYou'll get paid when someone buys it from market.",
                    "SELL FOR PRICE HELP", 
                    cache, 
                    user_id
                )
                return ""
            
            try:
                index = int(args[1]) - 1
                price = int(args[2])
                
                user_backgrounds = self.get_user_backgrounds_for_display(user_id)
                
                if index < 0 or index >= len(user_backgrounds):
                    self.send_message_image(
                        sender, 
                        file_queue, 
                        f"Choose number 1-{len(user_backgrounds)}", 
                        "INVALID RANGE", 
                        cache, 
                        user_id
                    )
                    return ""
                
                background_file = user_backgrounds[index]
                
                success, message = self.sell_background_for_price(user_id, background_file, price)
                
                if success:
                    from .market import get_market_instance
                    market_plugin = get_market_instance()
                    market_plugin.cache = self.cache
                    
                    market_img_path = os.path.join(self.results_folder, f"market_after_sellprice_{user_id}.webp")
                    market_plugin.create_market_image(market_img_path, user_id, "market")
                    
                    overlay_path, error = self.apply_user_overlay(
                        market_img_path, user_id, sender, 0, 0, 
                        user["balance"], user, show_win_text=False, show_bet_amount=False
                    )
                    if overlay_path:
                        file_queue.put(overlay_path)
                    
                    return message
                else:
                    self.send_message_image(sender, file_queue, message, "SELL ERROR", cache, user_id)
                    return ""
                    
            except ValueError:
                self.send_message_image(
                    sender, 
                    file_queue, 
                    "Invalid number format\nUsage: `/bg sellprice <number> <price>`", 
                    "INVALID INPUT", 
                    cache, 
                    user_id
                )
                return ""
        
        elif cmd == "craft" or cmd == "c":
            if len(args) < 2:
                self.send_message_image(
                    sender, 
                    file_queue, 
                    "**Background Crafting System**\nUsage: `/bg craft <num1> <num2> <num3>`\nExamples:\n• `/bg craft 1 2 3` (spaces)\n• `/bg craft 1,2,3` (commas)\n\nCrafting rules:\n• 3 cheap backgrounds → 1 medium background\n• 3 medium backgrounds → 1 expensive background\n• All 3 must be same rarity\n• Cannot use default or active background",
                    "CRAFTING HELP", 
                    cache, 
                    user_id
                )
                return ""
            
            try:
                craft_args = []
                if len(args) > 1:
                    if ',' in args[1]:
                        craft_args = args[1].split(',')
                    else:
                        craft_args = args[1:]
                
                if len(craft_args) < 3:
                    self.send_message_image(
                        sender, 
                        file_queue, 
                        "Need 3 background numbers!\nUsage: `/bg craft <num1> <num2> <num3>`", 
                        "INVALID INPUT", 
                        cache, 
                        user_id
                    )
                    return ""
                
                craft_args = craft_args[:3]
                
                indices = []
                for arg in craft_args:
                    try:
                        idx = int(arg.strip()) - 1
                        indices.append(idx)
                    except ValueError:
                        self.send_message_image(
                            sender, 
                            file_queue, 
                            f"Invalid number: '{arg}'\nUse numbers only.", 
                            "INVALID INPUT", 
                            cache, 
                            user_id
                        )
                        return ""
                
                success, message = self.craft_backgrounds(user_id, indices, file_queue)
                
                if success:
                    return message
                else:
                    self.send_message_image(sender, file_queue, message, "CRAFTING ERROR", cache, user_id)
                    return ""
                    
            except ValueError:
                self.send_message_image(
                    sender, 
                    file_queue, 
                    "Invalid number format\nUsage: `/bg craft <num1> <num2> <num3>`", 
                    "INVALID INPUT", 
                    cache, 
                    user_id
                )
                return ""
        
        elif cmd == "auction" or cmd == "a":
            if len(args) < 5:
                self.send_message_image(
                    sender, 
                    file_queue, 
                    "**Background Auction**\nUsage: `/bg auction <number> <start_price> <min_bid> <hours>`\nExample: `/bg auction 3 2000 100 48`\n\nStart price: 50-10,000 coins\nMin bid: 10-1,000 coins\nDuration: 1-168 hours\nAuction fee: 5 coins",
                    "AUCTION HELP", 
                    cache, 
                    user_id
                )
                return ""
            
            try:
                index = int(args[1]) - 1
                start_price = int(args[2])
                min_bid = int(args[3])
                duration_hours = int(args[4])
                
                user_backgrounds = self.get_user_backgrounds_for_display(user_id)
                
                if index < 0 or index >= len(user_backgrounds):
                    self.send_message_image(
                        sender, 
                        file_queue, 
                        f"Choose number 1-{len(user_backgrounds)}", 
                        "INVALID RANGE", 
                        cache, 
                        user_id
                    )
                    return ""
                
                background_file = user_backgrounds[index]
                
                success, message = self.create_background_auction(user_id, background_file, start_price, min_bid, duration_hours)
                
                if success:
                    from .market import get_market_instance
                    market_plugin = get_market_instance()
                    market_plugin.cache = self.cache
                    
                    market_img_path = os.path.join(self.results_folder, f"market_after_auction_{user_id}.webp")
                    market_plugin.create_market_image(market_img_path, user_id, "auctions")
                    
                    overlay_path, error = self.apply_user_overlay(
                        market_img_path, user_id, sender, -self.auction_listing_fee, -self.auction_listing_fee, 
                        user["balance"], user, show_win_text=False, show_bet_amount=False
                    )
                    if overlay_path:
                        file_queue.put(overlay_path)
                    
                    return message
                else:
                    self.send_message_image(sender, file_queue, message, "AUCTION ERROR", cache, user_id)
                    return ""
                    
            except ValueError:
                self.send_message_image(
                    sender, 
                    file_queue, 
                    "Invalid number format\nCheck all parameters are numbers", 
                    "INVALID INPUT", 
                    cache, 
                    user_id
                )
                return ""
        
        elif cmd == "list" or cmd == "l":
            user_backgrounds = self.get_user_backgrounds_for_display(user_id)
            if not user_backgrounds:
                self.send_message_image(sender, file_queue, "You don't have any backgrounds yet!", "No Backgrounds", cache, user_id)
                return ""
            
            page = 1
            if len(args) > 1:
                try:
                    page = int(args[1])
                except ValueError:
                    self.send_message_image(sender, file_queue, "Invalid page number", "Error", cache, user_id)
                    return ""
            
            current_bg = user.get("background", "default-bg.png")
            collection_img = self.create_collection_image(user_backgrounds, current_bg, user_id, page)
            
            if collection_img:
                img_path = os.path.join(self.results_folder, f"collection_{user_id}_page{page}.webp")
                collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                
                overlay_path, error = self.apply_user_overlay(
                    img_path, user_id, sender, 0, 0, user["balance"], user, show_win_text=False, show_bet_amount=False
                )
                if overlay_path:
                    file_queue.put(overlay_path)
                
                total_pages = (len(user_backgrounds) + 8) // 9
                page_info = f" (Page {page}/{total_pages})" if total_pages > 1 else ""
                return f"Your background collection{page_info}!\nUse `/bg set <number>` to set active background."
            else:
                self.send_message_image(sender, file_queue, "Failed to generate collection image", "Image Error", cache, user_id)
                return ""
            
        elif cmd == "shop":
            user_backgrounds = self.get_user_backgrounds(user_id)
            img_path = os.path.join(self.results_folder, f"shop_{user_id}.webp")
            self.create_shop_image(img_path, user_id, user_backgrounds, nickname)
            
            shop_img = Image.open(img_path).convert('RGBA')
            shop_img.save(img_path, format='WEBP', quality=85, optimize=True)
            
            overlay_path, error = self.apply_user_overlay(
                img_path, user_id, sender, 0, 0, user["balance"], user, show_win_text=False, show_bet_amount=False
            )
            if overlay_path:
                file_queue.put(overlay_path)
            
            return "**Background Shop**\nUse `/bg buy <number>` to purchase.\nSell your backgrounds with `/bg sellprice <number> <price>`!"
        
        elif cmd == "buy":
            if len(args) < 2:
                self.send_message_image(sender, file_queue, "Usage: `/bg buy <number>` (1-9)", "Invalid Usage", cache, user_id)
                return ""
            
            try:
                item_number = int(args[1])
            except ValueError:
                self.send_message_image(sender, file_queue, "Item number must be a number", "Invalid Number", cache, user_id)
                return ""
            
            if not 1 <= item_number <= 9:
                self.send_message_image(sender, file_queue, "Item number must be between 1 and 9", "Invalid Range", cache, user_id)
                return ""
            
            offers = self.load_daily_offers(nickname)
            
            item_index = item_number - 1
            category_index = item_index // 3
            item_in_category_index = item_index % 3
            
            categories = list(offers.keys())
            if category_index >= len(categories):
                self.send_message_image(sender, file_queue, "Invalid item number", "Invalid Item", cache, user_id)
                return ""
            
            category = categories[category_index]
            category_offers = offers[category]["offers"]
            
            if item_in_category_index >= len(category_offers):
                self.send_message_image(sender, file_queue, "Invalid item number", "Invalid Item", cache, user_id)
                return ""
            
            offer = category_offers[item_in_category_index]
            price = offer["price"]
            
            user_backgrounds = self.get_user_backgrounds(user_id)
            if offer["file"] in user_backgrounds:
                self.send_message_image(sender, file_queue, f"You already own: {offer['file']}", "Already Owned", cache, user_id)
                return ""
            
            if user["balance"] < price:
                self.send_message_image(sender, file_queue, f"Need: {price} coins\nYou have: {user['balance']} coins", "Insufficient Funds", cache, user_id)
                return ""
            
            new_balance = user["balance"] - price
            self.update_user_balance(user_id, new_balance)
            self.add_user_background(user_id, offer["file"])
            self.set_user_current_background(user_id, offer["file"])
            
            user["balance"] = new_balance
            user["background"] = offer["file"]
            
            user_backgrounds = self.get_user_backgrounds_for_display(user_id)
            
            shop_img_path = os.path.join(self.results_folder, f"shop_after_buy_{user_id}.webp")
            self.create_shop_image(shop_img_path, user_id, user_backgrounds, nickname)
            
            shop_img = Image.open(shop_img_path).convert('RGBA')
            shop_img.save(shop_img_path, format='WEBP', quality=85, optimize=True)
            
            overlay_path, error = self.apply_user_overlay(
                shop_img_path, user_id, sender, -price, 0, user["balance"], user, show_win_text=False
            )
            if overlay_path:
                file_queue.put(overlay_path)
            
            return f"Purchased & activated: **{offer['file']}** for {price} coins!\nCheck your collection with `/bg list`"

        elif cmd == "set":
            if len(args) < 2:
                self.send_message_image(sender, file_queue, "Usage: `/bg set <number>`", "Invalid Usage", cache, user_id)
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
                        self.send_message_image(sender, file_queue, f"Choose number 1-{len(user_backgrounds)}", "Invalid Range", cache, user_id)
                        return ""
            except ValueError:
                background_name = set_arg
            
            if background_name not in user_backgrounds:
                self.send_message_image(sender, file_queue, f"You don't own: {background_name}", "Not Owned", cache, user_id)
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
                    
                    overlay_path, error = self.apply_user_overlay(
                        img_path, user_id, sender, 0, 0, user["balance"], user
                    )
                    if overlay_path:
                        file_queue.put(overlay_path)
                    
                    return f"Background set to: **{background_name}**\nNow active in your collection!"
                else:
                    self.send_message_image(sender, file_queue, f"Background set to: {background_name}", "Success", cache, user_id)
                    return ""
            else:
                self.send_message_image(sender, file_queue, "Failed to set background", "Error", cache, user_id)
                return ""
        
        else:
            self.send_message_image(sender, file_queue, 
                                  "**Background System Commands**\n\n"
                                  "• `/bg shop` - View daily offers\n"
                                  "• `/bg list [page]` - Your collection\n"
                                  "• `/bg buy <1-9>` - Purchase background\n"
                                  "• `/bg set <number>` - Set active background\n"
                                  "• `/bg sellprice <num> <price>` - List on market\n"
                                  "• `/bg auction <num> <start> <min_bid> <hours>` - Create auction\n"
                                  "• `/bg craft <1> <2> <3>` - Craft backgrounds\n"
                                  "• `/bg quicksell <number>` - Quick sell for coins", 
                                  "COMMAND HELP", cache, user_id)
            return ""

def register():
    plugin = BackgroundShopPlugin()
    return {
        "name": "background",
        "aliases": ["/bg"],
        "description": """**Background Collection System**

Customize your game interface with unique backgrounds! Buy from daily shop, craft better ones, or trade on the market.

**Shop & Collection:**
• `/bg shop` - View daily personal offers
• `/bg list [page]` - Browse your collection  
• `/bg buy <1-9>` - Purchase background
• `/bg set <number>` - Set active background

**Crafting System:**
• `/bg craft <1> <2> <3>` - Combine 3 same-rarity backgrounds
• 3 cheap → 1 medium background
• 3 medium → 1 expensive background

**Market & Selling:**
• `/bg sellprice <num> <price>` - List on market (50-10,000 coins)
• `/bg auction <num> <start> <min_bid> <hours>` - Create auction
• `/bg quicksell <number>` - Quick sell for instant coins

**Player Marketplace:**
• `/market` - View player market
• `/market buy` - Buy from other players""",
        "execute": plugin.execute_game
    }