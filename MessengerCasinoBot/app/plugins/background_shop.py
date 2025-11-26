import os
import random
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime
from base_game_plugin import BaseGamePlugin
from logger import logger

class BackgroundShopPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="background_shop",
            results_folder=self.get_asset_path("shop_results"),
        )
        self.shop_folder = self.get_asset_path("backgrounds")
        os.makedirs(self.results_folder, exist_ok=True)
        
        self.background_categories = {
            "cheap": {
                "folder": "cheap",
                "price_range": (100, 500),
                "display_name": "💰 Cheap"
            },
            "medium": {
                "folder": "medium", 
                "price_range": (600, 1500),
                "display_name": "💎 Medium"
            },
            "expensive": {
                "folder": "expensive",
                "price_range": (2000, 5000),
                "display_name": "💎💎 Expensive"
            }
        }
        
        self.daily_offers = {}
        self.last_update_date = None

    def get_daily_seed(self):
        today = datetime.now().strftime("%Y%m%d")
        return int(today)

    def round_price(self, price):
        return (price // 10) * 10

    def load_daily_offers(self):
        today = datetime.now().date()
        
        if self.last_update_date == today and self.daily_offers:
            return self.daily_offers
        
        self.daily_offers = {}
        seed = self.get_daily_seed()
        random.seed(seed)
        
        for category, config in self.background_categories.items():
            category_folder = os.path.join(self.shop_folder, config["folder"])
            
            if not os.path.exists(category_folder):
                continue
            
            background_files = []
            for ext in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
                background_files.extend([f for f in os.listdir(category_folder) if f.lower().endswith(ext[1:])])
            
            if not background_files:
                continue
            
            selected_backgrounds = random.sample(background_files, min(3, len(background_files)))
            
            offers = []
            for bg_file in selected_backgrounds:
                price = random.randint(config["price_range"][0], config["price_range"][1])
                rounded_price = self.round_price(price)
                offers.append({
                    "file": bg_file,
                    "price": rounded_price,
                    "full_path": os.path.join(category_folder, bg_file)
                })
            
            self.daily_offers[category] = {
                "display_name": config["display_name"],
                "offers": offers
            }
        
        self.last_update_date = today
        return self.daily_offers

    def get_user_backgrounds(self, user_id):
        user = self.cache.get_user(user_id)
        if user and "backgrounds" in user:
            return user["backgrounds"]
        return []

    def add_user_background(self, user_id, background_file):
        user = self.cache.get_user(user_id)
        if not user:
            return False
        
        if "backgrounds" not in user:
            user["backgrounds"] = []
        
        if background_file not in user["backgrounds"]:
            user["backgrounds"].append(background_file)
            self.cache.update_user(user_id, backgrounds=user["backgrounds"])
            return True
        return False

    def set_user_current_background(self, user_id, background_file):
        user = self.cache.get_user(user_id)
        if not user:
            return False
        
        user_backgrounds = self.get_user_backgrounds(user_id)
        if background_file not in user_backgrounds:
            return False
        
        self.cache.update_user(user_id, background=background_file)
        return True

    def create_shop_image(self, output_path, user_backgrounds=None):
        if user_backgrounds is None:
            user_backgrounds = []
        
        offers = self.load_daily_offers()
        
        ITEM_WIDTH = 300
        ITEM_HEIGHT = 200
        MARGIN = 20
        CATEGORY_MARGIN = 40
        
        categories_count = len(offers)
        items_per_category = 3
        
        total_width = ITEM_WIDTH * items_per_category + MARGIN * (items_per_category + 1)
        total_height = (ITEM_HEIGHT + CATEGORY_MARGIN) * categories_count + MARGIN * 2
        
        img = Image.new('RGBA', (total_width, total_height), (35, 35, 45, 255))
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
            category_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
            price_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
            number_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
            owned_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
        except:
            title_font = ImageFont.load_default()
            category_font = ImageFont.load_default()
            price_font = ImageFont.load_default()
            number_font = ImageFont.load_default()
            owned_font = ImageFont.load_default()
        
        title_text = "BACKGROUND SHOP"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_x = (total_width - (title_bbox[2] - title_bbox[0])) // 2
        draw.text((title_x, MARGIN), title_text, fill=(255, 255, 255), font=title_font)
        
        date_text = f"Offer valid: {datetime.now().strftime('%d.%m.%Y')}"
        date_bbox = draw.textbbox((0, 0), date_text, font=owned_font)
        date_x = (total_width - (date_bbox[2] - date_bbox[0])) // 2
        draw.text((date_x, MARGIN + 30), date_text, fill=(200, 200, 200), font=owned_font)
        
        y_offset = MARGIN + 70
        
        item_counter = 1
        for category_idx, (category, category_data) in enumerate(offers.items()):
            category_y = y_offset + category_idx * (ITEM_HEIGHT + CATEGORY_MARGIN)
            draw.text((MARGIN, category_y), category_data["display_name"], 
                     fill=(255, 215, 0), font=category_font)
            
            for item_idx, offer in enumerate(category_data["offers"]):
                x = MARGIN + item_idx * (ITEM_WIDTH + MARGIN)
                y = category_y + 30
                
                draw.rectangle([x, y, x + ITEM_WIDTH, y + ITEM_HEIGHT], 
                              fill=(50, 50, 60), outline=(100, 100, 120), width=2)
                
                number_text = f"{item_counter}"
                number_bbox = draw.textbbox((0, 0), number_text, font=number_font)
                number_x = x + 10
                number_y = y + 10
                draw.text((number_x, number_y), number_text, fill=(255, 255, 255), font=number_font)
                
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
                
                if offer["file"] in user_backgrounds:
                    owned_text = "✓ OWNED"
                    owned_bbox = draw.textbbox((0, 0), owned_text, font=owned_font)
                    owned_x = x + (ITEM_WIDTH - (owned_bbox[2] - owned_bbox[0])) // 2
                    owned_y = y + 5
                    draw.text((owned_x, owned_y), owned_text, fill=(100, 255, 100), font=owned_font)
                
                item_counter += 1
        
        img.save(output_path, format='WEBP', quality=85, optimize=True)
        return output_path

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 0)
        if error:
            return error

        if len(args) == 0:
            user_backgrounds = self.get_user_backgrounds(user_id)
            img_path = os.path.join(self.results_folder, f"shop_{user_id}.webp")
            self.create_shop_image(img_path, user_backgrounds)
            
            overlay_path, error = self.apply_user_overlay(
                img_path, user_id, sender, 0, 0, user["balance"], user
            )
            if overlay_path:
                file_queue.put(overlay_path)
            
            return "Background shop! Use `/bg buy <number>` to purchase."

        cmd = args[0].lower()
        
        if cmd == "buy":
            if len(args) < 2:
                return "Usage: `/bg buy <number>`"
            
            try:
                item_number = int(args[1])
            except ValueError:
                return "Please enter a valid item number (1-9)"
            
            if not 1 <= item_number <= 9:
                return "Item number must be between 1 and 9"
            
            offers = self.load_daily_offers()
            
            item_index = item_number - 1
            category_index = item_index // 3
            item_in_category_index = item_index % 3
            
            categories = list(offers.keys())
            if category_index >= len(categories):
                return "Invalid item number"
            
            category = categories[category_index]
            category_offers = offers[category]["offers"]
            
            if item_in_category_index >= len(category_offers):
                return "Invalid item number"
            
            offer = category_offers[item_in_category_index]
            price = offer["price"]
            
            user_backgrounds = self.get_user_backgrounds(user_id)
            if offer["file"] in user_backgrounds:
                return "ℹYou already own this background!"
            
            if user["balance"] < price:
                return f"Not enough funds! You have {user['balance']}, need {price}"
            
            new_balance = user["balance"] - price
            self.update_user_balance(user_id, new_balance)
            self.add_user_background(user_id, offer["file"])
            
            user["balance"] = new_balance
            
            user_backgrounds = self.get_user_backgrounds(user_id)
            img_path = os.path.join(self.results_folder, f"shop_{user_id}_purchase.webp")
            self.create_shop_image(img_path, user_backgrounds)
            
            overlay_path, error = self.apply_user_overlay(
                img_path, user_id, sender, price, -price, new_balance, user
            )
            if overlay_path:
                file_queue.put(overlay_path)
            
            return f"Purchased background for {price}!\nUse `/backgrounds` to see your collection."

        elif cmd == "list" or cmd == "collection":
            user_backgrounds = self.get_user_backgrounds(user_id)
            if not user_backgrounds:
                return "You don't have any backgrounds yet. Visit the shop! `/bg`"
            
            current_bg = user.get("background", "default-bg.png")
            backgrounds_list = "\n".join([f"{bg} {'(ACTIVE)' if bg == current_bg else ''}" for bg in user_backgrounds])
            return f"Your background collection:\n{backgrounds_list}\n\nUse `/background set <name>` to set background."

        elif cmd == "set":
            if len(args) < 2:
                return "Usage: `/bg set <background_name>`"
            
            background_name = " ".join(args[1:])
            user_backgrounds = self.get_user_backgrounds(user_id)
            
            if background_name not in user_backgrounds:
                return f"You don't own background '{background_name}' or it doesn't exist"
            
            if self.set_user_current_background(user_id, background_name):
                return f"Set background: {background_name}"
            else:
                return "Error setting background"

        elif cmd == "current":
            current_bg = user.get("background", "default-bg.png")
            return f"Your current background: {current_bg}"

        else:
            return "Background Shop\nCommands:\n`/bg` - show shop\n`/bg buy <1-9>` - buy background\n`/bg list` - your collection\n`/bg set <name>` - set background\n`/bg current` - current background"

def register():
    plugin = BackgroundShopPlugin()
    return {
        "name": "background_shop",
        "aliases": ["/bg", "/background", "/shop"],
        "description": "Background shop: /bg, /bg buy <1-9>, /bg list, /bg set <name>",
        "execute": plugin.execute_game
    }