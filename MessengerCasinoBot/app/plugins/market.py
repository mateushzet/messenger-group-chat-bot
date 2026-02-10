import os
import time
from PIL import Image, ImageDraw
from datetime import datetime
from base_game_plugin import BaseGamePlugin

_market_instance = None

def get_market_instance():
    global _market_instance
    if _market_instance is None:
        _market_instance = BackgroundMarketPlugin()
    return _market_instance

class BackgroundMarketPlugin(BaseGamePlugin):
    def __init__(self):     
        super().__init__(game_name="market")
        
        self.backgrounds_folder = self.get_asset_path("backgrounds")
        self.avatars_folder = self.get_asset_path("avatars")
        self.error_folder = self.get_asset_path("errors")
        
        os.makedirs(self.error_folder, exist_ok=True)
        
        self.auctions_cache = None
        self.auctions_cache_time = 0
        
        self.quick_sell_prices = {
            "cheap": 100,
            "medium": 400,
            "expensive": 1000
        }
        
        self.listing_fee = 5
        self.auction_fee = 5

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

    def load_market_items(self):
        if not hasattr(self.cache, 'market_items'):
            return []
        
        items = self.cache.get_market_items()
        active_items = []
        
        for item in items:
            if item.get("status") == "for_sale":
                listed_at = item.get("listed_at", 0)
                if time.time() - listed_at < 604800:
                    active_items.append(item)
                else:
                    self._return_expired_item(item)
        
        return active_items

    def load_active_auctions(self):
        if not hasattr(self.cache, 'auctions'):
            return []
        
        now = time.time()
        auctions = self.cache.get_auctions()
        active_auctions = []
        expired_auctions = []
        
        for auction in auctions:
            if auction.get("status") == "active":
                if auction.get("ends_at", 0) > now:
                    time_left = auction["ends_at"] - now
                    auction["time_left_hours"] = round(time_left / 3600, 1)
                    auction["time_left_minutes"] = round((time_left % 3600) / 60)
                    active_auctions.append(auction)
                else:
                    expired_auctions.append(auction)
        
        for auction in expired_auctions:
            self._finalize_expired_auction(auction)
        
        return active_auctions

    def _return_expired_item(self, item):
        seller_id = item.get("seller_id")
        item_type = item.get("type")
        item_file = item.get("file")
        
        if not seller_id or not item_type or not item_file:
            return False
        
        seller = self.cache.get_user(seller_id)
        if not seller:
            return False
        
        if item_type == "avatar":
            avatars = seller.get("avatars", [])
            if item_file not in avatars:
                avatars.append(item_file)
                self.cache.update_user(seller_id, avatars=avatars)
        elif item_type == "background":
            backgrounds = seller.get("backgrounds", [])
            if item_file not in backgrounds:
                backgrounds.append(item_file)
                self.cache.update_user(seller_id, backgrounds=backgrounds)
        
        self.cache.remove_market_item(item_file)
        return True

    def _finalize_expired_auction(self, auction):
        auction_index = None
        auctions = self.cache.get_auctions()
        
        for idx, a in enumerate(auctions):
            if a.get("id") == auction.get("id"):
                auction_index = idx
                break
        
        if auction_index is None:
            return False
        
        if auction.get("current_bidder"):
            winner_id = auction["current_bidder"]
            seller_id = auction["seller_id"]
            final_price = auction["current_price"]
            
            if auction["type"] == "avatar":
                winner = self.cache.get_user(winner_id)
                if winner:
                    avatars = winner.get("avatars", [])
                    if auction["file"] not in avatars:
                        avatars.append(auction["file"])
                        self.cache.update_user(winner_id, avatars=avatars)
            else:
                winner = self.cache.get_user(winner_id)
                if winner:
                    backgrounds = winner.get("backgrounds", [])
                    if auction["file"] not in backgrounds:
                        backgrounds.append(auction["file"])
                        self.cache.update_user(winner_id, backgrounds=backgrounds)
            
            self.cache.update_balance(seller_id, final_price)
            auction["status"] = "completed"
            auction["completed_at"] = time.time()
            auction["winner_id"] = winner_id
            auction["final_price"] = final_price
        else:
            seller_id = auction["seller_id"]
            if auction["type"] == "avatar":
                seller = self.cache.get_user(seller_id)
                if seller:
                    avatars = seller.get("avatars", [])
                    if auction["file"] not in avatars:
                        avatars.append(auction["file"])
                        self.cache.update_user(seller_id, avatars=avatars)
            else:
                seller = self.cache.get_user(seller_id)
                if seller:
                    backgrounds = seller.get("backgrounds", [])
                    if auction["file"] not in backgrounds:
                        backgrounds.append(auction["file"])
                        self.cache.update_user(seller_id, backgrounds=backgrounds)
            
            auction["status"] = "expired"
            auction["expired_at"] = time.time()
        
        self.cache.update_auction(auction_index, auction)
        return True

    def place_bid(self, user_id, auction_index, bid_amount):
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"
        
        auctions = self.load_active_auctions()
        if auction_index < 0 or auction_index >= len(auctions):
            return False, "Invalid auction number"
        
        auction = auctions[auction_index]
        
        if auction.get("status") != "active":
            return False, "Auction is no longer active"
        
        if auction.get("seller_id") == user_id:
            return False, "Cannot bid on your own auction"
        
        current_price = auction.get("current_price", auction.get("start_price", 0))
        min_bid = auction.get("min_bid", 10)
        
        if bid_amount < current_price + min_bid:
            return False, f"Bid must be at least {current_price + min_bid} coins"
        
        if user["balance"] < bid_amount:
            return False, f"Insufficient funds. You have {user['balance']} coins"
        
        all_auctions = self.cache.get_auctions()
        real_auction_index = -1
        
        for idx, a in enumerate(all_auctions):
            if a.get("id") == auction.get("id"):
                real_auction_index = idx
                break
        
        if real_auction_index == -1:
            return False, "Auction not found"
        
        real_auction = all_auctions[real_auction_index]
        
        now = time.time()
        ends_at = real_auction.get("ends_at", 0)
        time_left = ends_at - now
        
        if time_left < 300:
            new_ends_at = now + 300
            real_auction["ends_at"] = new_ends_at
        
        prev_bidder = real_auction.get("current_bidder")
        if prev_bidder:
            prev_bid = real_auction.get("bids", [])[-1]["amount"] if real_auction.get("bids") else current_price
            self.cache.update_balance(prev_bidder, prev_bid)
        
        self.cache.update_balance(user_id, -bid_amount)
        real_auction["current_price"] = bid_amount
        real_auction["current_bidder"] = user_id
        
        bid_record = {
            "bidder_id": user_id,
            "bidder_name": user.get("name", ""),
            "amount": bid_amount,
            "timestamp": time.time()
        }
        
        if "bids" not in real_auction:
            real_auction["bids"] = []
        real_auction["bids"].append(bid_record)
        
        self.cache.update_auction(real_auction_index, real_auction)
        
        final_ends_at = real_auction.get("ends_at", ends_at)
        final_time_left_seconds = final_ends_at - now
        
        if final_time_left_seconds > 3600:
            time_left_text = f"{int(final_time_left_seconds / 3600)} hours"
        elif final_time_left_seconds > 60:
            time_left_text = f"{int(final_time_left_seconds / 60)} minutes"
        else:
            time_left_text = f"{int(final_time_left_seconds)} seconds"
        
        if time_left < 300:
            return True, f"**Bid placed successfully!**\n\n" \
                        f"**New price:** {bid_amount} coins\n" \
                        f"**You are now the highest bidder!**\n" \
                        f"**Auction time extended!**\n" \
                        f"**Ends in:** {time_left_text}\n\n" \
                        f"If someone outbids you, your coins will be returned."
        else:
            return True, f"**Bid placed successfully!**\n\n" \
                        f"**New price:** {bid_amount} coins\n" \
                        f"**You are now the highest bidder!**\n" \
                        f"**Ends in:** {time_left_text}\n\n" \
                        f"If someone outbids you, your coins will be returned."

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
        price = item.get("price", 100)
        seller_id = item.get("seller_id")
        
        if not item_type or not item_file:
            return False, "Invalid market item"
        
        if seller_id == user_id:
            return False, "Cannot buy your own item"
        
        if user["balance"] < price:
            return False, f"Not enough funds. Required: {price} coins, you have: {user['balance']} coins"
        
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
        
        if seller_id:
            self.cache.update_balance(seller_id, price)
        
        self.cache.remove_market_item(item_file)
        
        return True, f"**Purchase successful!**\n\n" \
                    f"**Item:** {item_file}\n" \
                    f"**Price:** {price} coins\n" \
                    f"**Type:** {item_type}\n\n" \
                    f"Use `/{'bg' if item_type == 'background' else 'avatar'} set` to activate it!"

    def create_market_image(self, output_path, user_id, show_type="market"):
        if show_type == "market":
            items = self.load_market_items()
            title = "PLAYER MARKET"
            subtitle = ""
            no_items_msg = "Market is empty! Sell items with /bg sellprice or /avatar sellprice"
            price_label = "Price:"
            show_time_left = False
            show_seller = True
            show_current_bidder = False
            show_min_bid = False
        else:
            items = self.load_active_auctions()
            title = "ACTIVE AUCTIONS"
            subtitle = "Live Auctions - Place Your Bids!"
            no_items_msg = "No active auctions! Create one with /bg auction or /avatar auction"
            price_label = "Current:"
            show_time_left = True
            show_seller = True
            show_current_bidder = True
            show_min_bid = True
        
        if not items:
            return self._create_empty_market_image(output_path, title, no_items_msg, show_type)
        
        ITEM_WIDTH = 160
        ITEM_HEIGHT = 300
        MARGIN = 8
        ITEMS_PER_ROW = 5
        
        num_items = len(items)
        rows = (num_items + ITEMS_PER_ROW - 1) // ITEMS_PER_ROW
        
        total_width = ITEM_WIDTH * ITEMS_PER_ROW + MARGIN * (ITEMS_PER_ROW + 1)
        total_height = (ITEM_HEIGHT + MARGIN) * rows + MARGIN * 3 + 140
        
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
        top_bar = Image.new('RGBA', (total_width, top_bar_height), (40, 40, 50, 230))
        img.paste(top_bar, (0, 0), top_bar)
        
        if hasattr(self, 'text_renderer'):
            title_img = self.text_renderer.render_text(
                text=title,
                font_size=22,
                color=(255, 255, 255, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255)
            )
            title_x = (total_width - title_img.width) // 2
            img.paste(title_img, (title_x, MARGIN), title_img)
            
            subtitle_img = self.text_renderer.render_text(
                text=subtitle,
                font_size=16,
                color=(200, 200, 200, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255)
            )
            subtitle_x = (total_width - subtitle_img.width) // 2
            img.paste(subtitle_img, (subtitle_x, MARGIN + 25), subtitle_img)
        else:
            draw = ImageDraw.Draw(img)
            title_bbox = draw.textbbox((0, 0), title)
            title_x = (total_width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, MARGIN), title, fill=(255, 255, 255))
            
            subtitle_bbox = draw.textbbox((0, 0), subtitle)
            subtitle_x = (total_width - (subtitle_bbox[2] - subtitle_bbox[0])) // 2
            draw.text((subtitle_x, MARGIN + 25), subtitle, fill=(200, 200, 200))
        
        y_offset = MARGIN + 70
        
        for idx, item in enumerate(items):
            row = idx // ITEMS_PER_ROW
            col = idx % ITEMS_PER_ROW
            
            x = MARGIN + col * (ITEM_WIDTH + MARGIN)
            y = y_offset + row * (ITEM_HEIGHT + MARGIN)
            
            item_type = item.get("type", "background")
            seller_id = item.get("seller_id")
            seller_name = item.get("seller_name", "Unknown")
            
            if not seller_name or seller_name == "Unknown":
                seller = self.cache.get_user(seller_id) if seller_id else None
                seller_name = seller.get("name", "Unknown") if seller else "Unknown"
            
            current_bidder_id = item.get("current_bidder")
            current_bidder_name = None
            if current_bidder_id and show_current_bidder:
                bidder = self.cache.get_user(current_bidder_id)
                current_bidder_name = bidder.get("name", "Unknown") if bidder else "Unknown"
            
            if item_type == "avatar":
                outline_color = (100, 150, 255)
                type_color = (100, 200, 255, 255)
                type_bg_color = (30, 60, 100, 200)
            else:
                outline_color = (255, 200, 100)
                type_color = (255, 200, 100, 255)
                type_bg_color = (100, 80, 30, 200)
            
            draw_rect = ImageDraw.Draw(img)
            draw_rect.rectangle([x, y, x + ITEM_WIDTH, y + ITEM_HEIGHT], 
                              fill=(50, 50, 60, 220), outline=outline_color, width=2)
            
            if hasattr(self, 'text_renderer'):
                type_text = item_type.upper()
                type_img = self.text_renderer.render_text(
                    text=type_text,
                    font_size=12,
                    color=type_color,
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                
                type_x = x + 2
                type_y = y + 2
                type_bg = Image.new('RGBA', (type_img.width + 4, type_img.height + 4), type_bg_color)
                img.paste(type_bg, (type_x, type_y), type_bg)
                img.paste(type_img, (type_x + 2, type_y + 2), type_img)
                
                item_number = idx + 1
                if show_type == "market":
                    command_text = f"/market buy {item_number}"
                else:
                    command_text = f"/market bid {item_number}"
                
                command_img = self.text_renderer.render_text(
                    text=command_text,
                    font_size=14,
                    color=(255, 255, 255, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                command_x = x + (ITEM_WIDTH - command_img.width) // 2
                command_y = y + 18
                img.paste(command_img, (command_x, command_y), command_img)
            
            try:
                item_file = item.get("file", "")
                if item_type == "avatar":
                    full_path = os.path.join(self.avatars_folder, item_file)
                else:
                    full_path = os.path.join(self.backgrounds_folder, item_file)
                
                if os.path.exists(full_path):
                    item_img = Image.open(full_path).convert('RGBA')
                    img_width = ITEM_WIDTH - 20
                    img_height = ITEM_HEIGHT - 150 if show_time_left else ITEM_HEIGHT - 130
                    
                    item_img.thumbnail((img_width, img_height), Image.LANCZOS)
                    
                    item_x = x + (ITEM_WIDTH - item_img.width) // 2
                    item_y = y + 35
                    
                    if item_type == "avatar":
                        img.paste(item_img, (item_x, item_y), item_img)
                    else:
                        img.paste(item_img, (item_x, item_y))
                        
            except Exception:
                pass
            
            if hasattr(self, 'text_renderer'):
                filename = item.get("file", "")
                if len(filename) > 23:
                    filename = filename[:18] + ".."
                
                filename_img = self.text_renderer.render_text(
                    text=filename,
                    font_size=10,
                    color=(180, 180, 200, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                filename_x = x + (ITEM_WIDTH - filename_img.width) // 2
                filename_y = y + ITEM_HEIGHT - 130 if show_time_left else y + ITEM_HEIGHT - 110
                img.paste(filename_img, (filename_x, filename_y), filename_img)
                
                if show_seller:
                    seller_text = f"by: {seller_name[:20]}" if len(seller_name) > 20 else f"by: {seller_name}"
                    seller_img = self.text_renderer.render_text(
                        text=seller_text,
                        font_size=11,
                        color=(200, 180, 220, 255),
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )
                    seller_x = x + (ITEM_WIDTH - seller_img.width) // 2
                    seller_y = y + ITEM_HEIGHT - 115 if show_time_left else y + ITEM_HEIGHT - 95
                    img.paste(seller_img, (seller_x, seller_y), seller_img)
                
                if show_current_bidder:
                    if current_bidder_name:
                        bidder_text = f"bid: {current_bidder_name[:8]}" if len(current_bidder_name) > 8 else f"bid: {current_bidder_name}"
                        bidder_color = (180, 220, 200, 255)
                    else:
                        bidder_text = "no bids"
                        bidder_color = (150, 150, 150, 255)
                    
                    bidder_img = self.text_renderer.render_text(
                        text=bidder_text,
                        font_size=10,
                        color=bidder_color,
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )
                    bidder_x = x + (ITEM_WIDTH - bidder_img.width) // 2
                    bidder_y = y + ITEM_HEIGHT - 100 if show_time_left else y + ITEM_HEIGHT - 80
                    img.paste(bidder_img, (bidder_x, bidder_y), bidder_img)
                
                if show_min_bid and show_type != "market":
                    min_bid = item.get("min_bid", 10)
                    min_bid_text = f"min +{min_bid}"
                    min_bid_img = self.text_renderer.render_text(
                        text=min_bid_text,
                        font_size=10,
                        color=(255, 200, 100, 255),
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )
                    min_bid_x = x + (ITEM_WIDTH - min_bid_img.width) // 2
                    min_bid_y = y + ITEM_HEIGHT - 85
                    img.paste(min_bid_img, (min_bid_x, min_bid_y), min_bid_img)
                
                if show_type == "market":
                    price = item.get("price", 100)
                    price_text = f"{price_label} {price}"
                    price_y = y + ITEM_HEIGHT - 70 if show_seller else y + ITEM_HEIGHT - 60
                else:
                    price = item.get("current_price", item.get("start_price", 100))
                    price_text = f"{price_label} {price}"
                    price_y = y + ITEM_HEIGHT - 70 if show_min_bid else y + ITEM_HEIGHT - 65 if show_current_bidder else y + ITEM_HEIGHT - 55
                
                price_img = self.text_renderer.render_text(
                    text=price_text,
                    font_size=16,
                    color=(100, 255, 100, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                price_x = x + (ITEM_WIDTH - price_img.width) // 2
                img.paste(price_img, (price_x, price_y), price_img)
                
                if show_time_left:
                    time_left = item.get("time_left_hours", 0)
                    if time_left > 24:
                        time_text = f"{int(time_left/24)}d"
                    elif time_left > 1:
                        time_text = f"{int(time_left)}h"
                    else:
                        minutes = int(time_left * 60)
                        time_text = f"{minutes}m"
                    
                    if time_left < 1:
                        time_color = (255, 100, 100, 255)
                    elif time_left < 6:
                        time_color = (255, 200, 100, 255)
                    else:
                        time_color = (150, 255, 150, 255)
                    
                    time_img = self.text_renderer.render_text(
                        text=time_text,
                        font_size=12,
                        color=time_color,
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )
                    time_x = x + (ITEM_WIDTH - time_img.width) // 2
                    time_y = y + ITEM_HEIGHT - 50
                    img.paste(time_img, (time_x, time_y), time_img)
        
        if hasattr(self, 'text_renderer'):
            legend_y = total_height - 20
            if show_type == "market":
                legend_text = "BUY: /market buy <num>"
                legend_img = self.text_renderer.render_text(
                    text=legend_text,
                    font_size=12,
                    color=(200, 200, 200, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
            else:
                legend_text = "BID: /market bid <num> <amount>"
                legend_img = self.text_renderer.render_text(
                    text=legend_text,
                    font_size=12,
                    color=(255, 200, 100, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
            
            legend_x = (total_width - legend_img.width) // 2
            img.paste(legend_img, (legend_x, legend_y), legend_img)
        
        img.save(output_path, format='WEBP', quality=100, optimize=True)
        return output_path

    def _create_empty_market_image(self, output_path, title, message, show_type):
        total_width = 600
        total_height = 400
        
        img = Image.new('RGBA', (total_width, total_height), (20, 20, 30, 255))
        
        if hasattr(self, 'text_renderer'):
            title_img = self.text_renderer.render_text(
                text=title,
                font_size=28,
                color=(255, 255, 255, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255)
            )
            title_x = (total_width - title_img.width) // 2
            img.paste(title_img, (title_x, 50), title_img)
            
            message_img = self.text_renderer.render_text(
                text=message,
                font_size=18,
                color=(200, 200, 200, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255)
            )
            message_x = (total_width - message_img.width) // 2
            img.paste(message_img, (message_x, 150), message_img)
            
            if show_type == "market":
                help_text = "Sell items with:\n/bg sellprice <num> <price>\n/avatar sellprice <num> <price>"
            else:
                help_text = "Create auctions with:\n/bg auction <num> <start> <min> <hours>\n/avatar auction <num> <start> <min> <hours>"
            
            help_lines = help_text.split('\n')
            line_height = 25
            start_y = 220
            
            for i, line in enumerate(help_lines):
                line_img = self.text_renderer.render_text(
                    text=line,
                    font_size=16,
                    color=(150, 200, 255, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                line_x = (total_width - line_img.width) // 2
                img.paste(line_img, (line_x, start_y + i * line_height), line_img)
        
        img.save(output_path, format='WEBP', quality=100, optimize=True)
        return output_path

    def cancel_market_listing(self, user_id, market_index):
        market_items = self.cache.get_market_items()
        
        if market_index < 0 or market_index >= len(market_items):
            return False, "Invalid item number"
        
        item = market_items[market_index]
        
        if item.get("seller_id") != user_id:
            return False, "This is not your item"
        
        item_type = item.get("type")
        item_file = item.get("file")
        
        if not item_type or not item_file:
            return False, "Invalid item data"
        
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"
        
        if item_type == "background":
            backgrounds = user.get("backgrounds", [])
            if item_file not in backgrounds:
                backgrounds.append(item_file)
                self.cache.update_user(user_id, backgrounds=backgrounds)
        elif item_type == "avatar":
            avatars = user.get("avatars", [])
            if item_file not in avatars:
                avatars.append(item_file)
                self.cache.update_user(user_id, avatars=avatars)
        
        self.cache.remove_market_item(item_file)
        
        return True, f"Cancelled listing for **{item_file}**\nThe {item_type} has been returned to your collection."

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 0)
        
        if error:
            self.send_message_image(sender, file_queue, error, "Validation Error", cache, user_id)
            return ""

        if not args:
            return self.execute_game(command_name, ["market"], file_queue, cache, sender, avatar_url)
        
        cmd = args[0].lower()
        
        if cmd == "market":
            market_items = self.load_market_items()
            
            if not market_items:
                self.send_message_image(sender, file_queue,
                    "Market is empty!\n\n"
                    "Sell items with:\n"
                    "• /bg sellprice <num> <price>\n"
                    "• /avatar sellprice <num> <price>\n\n"
                    "View auctions with: /market auctions",
                    "Empty Market", cache, user_id)
                return ""
            
            img_path = os.path.join(self.results_folder, f"market_{user_id}.webp")
            self.create_market_image(img_path, user_id, "market")
            
            overlay_path, error = self.apply_user_overlay(
                img_path, user_id, sender, 0, 0, user["balance"], user, 
                show_win_text=False, show_bet_amount=False
            )
            if overlay_path:
                file_queue.put(overlay_path)
            
            return f"**Player Market** ({len(market_items)} items)\n" \
                f"Use `/market buy <number>` to purchase.\n" \
                f"Check auctions with `/market auctions`"
        
        elif cmd == "auctions" or cmd == "auction":
            auctions = self.load_active_auctions()
            
            if not auctions:
                self.send_message_image(sender, file_queue,
                    "No active auctions!\n\n"
                    "Create auctions with:\n"
                    "• /bg auction <num> <start> <min> <hours>\n"
                    "• /avatar auction <num> <start> <min> <hours>\n\n"
                    "View market with: /market",
                    "No Active Auctions", cache, user_id)
                return ""
            
            img_path = os.path.join(self.results_folder, f"auctions_{user_id}.webp")
            self.create_market_image(img_path, user_id, "auctions")
            
            overlay_path, error = self.apply_user_overlay(
                img_path, user_id, sender, 0, 0, user["balance"], user, 
                show_win_text=False, show_bet_amount=False
            )
            if overlay_path:
                file_queue.put(overlay_path)
            
            return f"**Active Auctions** ({len(auctions)} auctions)\n" \
                f"Use `/market bid <number> <amount>` to place a bid.\n" \
                f"• Shows seller, current bidder, and minimum bid\n" \
                f"• If outbid, your coins are returned automatically"
        
        elif cmd == "cancel" or cmd == "c":
            if len(args) < 2:
                self.send_message_image(sender, file_queue,
                    "Usage: `/market cancel <item_number>`\nExample: `/market cancel 1`\n\n"
                    "This will remove your item from market\nand return it to your collection.",
                    "Cancel Help", cache, user_id)
                return ""
            
            try:
                item_index = int(args[1]) - 1
                success, message = self.cancel_market_listing(user_id, item_index)
                
                if success:
                    market_items = self.load_market_items()
                    
                    if market_items:
                        img_path = os.path.join(self.results_folder, f"market_after_cancel_{user_id}.webp")
                        self.create_market_image(img_path, user_id, "market")
                        
                        if os.path.exists(img_path):
                            if hasattr(self, 'apply_user_overlay'):
                                overlay_path, error = self.apply_user_overlay(
                                    img_path, user_id, sender, 0, 0, user["balance"], user,
                                    show_win_text=False, show_bet_amount=False
                                )
                                if overlay_path:
                                    file_queue.put(overlay_path)
                            else:
                                file_queue.put(img_path)
                    else:
                        self.send_message_image(sender, file_queue,
                            "Cancelled successfully!\n\nMarket is now empty.",
                            "Cancelled", cache, user_id)
                        return message
                    
                    return message + f"\n\n**Market updated!** ({len(market_items)} items remaining)"
                else:
                    self.send_message_image(sender, file_queue, message, "Cancel Error", cache, user_id)
                    return ""
                    
            except ValueError:
                self.send_message_image(sender, file_queue,
                    "Invalid number format\nUsage: `/market cancel <number>`",
                    "Invalid Input", cache, user_id)
                return ""
        
        elif cmd == "bid":
            if len(args) < 3:
                self.send_message_image(sender, file_queue,
                    "Usage: `/market bid <auction_number> <bid_amount>`\n"
                    "Example: `/market bid 1 1500`\n\n"
                    "Check active auctions with: `/market auctions`\n\n"
                    "Note: If outbid, your coins will be returned automatically.",
                    "Bid Help", cache, user_id)
                return ""
            
            try:
                auction_index = int(args[1]) - 1
                bid_amount = int(args[2])
                
                success, message = self.place_bid(user_id, auction_index, bid_amount)
                
                if success:
                    img_path = os.path.join(self.results_folder, f"auctions_after_bid_{user_id}.webp")
                    self.create_market_image(img_path, user_id, "auctions")
                    
                    overlay_path, error = self.apply_user_overlay(
                        img_path, user_id, sender, -bid_amount, -bid_amount, 
                        user["balance"], user, show_win_text=False, show_bet_amount=False
                    )
                    if overlay_path:
                        file_queue.put(overlay_path)
                    
                    return message
                else:
                    self.send_message_image(sender, file_queue, message, "Bid Error", cache, user_id)
                    return ""
                    
            except ValueError:
                self.send_message_image(sender, file_queue,
                    "Invalid number format\nUsage: `/market bid <number> <amount>`",
                    "Invalid Input", cache, user_id)
                return ""
        
        elif cmd == "buy":
            if len(args) < 2:
                self.send_message_image(sender, file_queue, 
                    "Usage: `/market buy <number>`\nExample: `/market buy 1`\n\n"
                    "Check available items with: `/market`",
                    "Market Buy Help", cache, user_id)
                return ""

            try:
                index = int(args[1]) - 1
                success, msg = self.buy_item_from_market(user_id, index)
                
                if not success:
                    if "already owned" in msg.lower():
                        self.send_message_image(sender, file_queue, msg, "Market - Already Owned", cache, user_id)
                    elif "not enough funds" in msg.lower():
                        self.send_message_image(sender, file_queue, 
                            f"{msg}\n\nYour balance: {user.get('balance', 0)} coins", 
                            "Insufficient Funds", cache, user_id)
                    elif "invalid item number" in msg.lower():
                        self.send_message_image(sender, file_queue, 
                            f"{msg}\n\nUse `/market` to see available items", 
                            "Invalid Item Number", cache, user_id)
                    else:
                        self.send_message_image(sender, file_queue, msg, "Market Error", cache, user_id)
                    return ""
                
                img_path = os.path.join(self.results_folder, f"market_after_buy_{user_id}.webp")
                self.create_market_image(img_path, user_id, "market")
                
                item_type = "avatar" if "avatar" in msg.lower() else "background"
                
                overlay_path, error = self.apply_user_overlay(
                    img_path, user_id, sender, 0, 0, user["balance"], user, 
                    show_win_text=False, show_bet_amount=False
                )
                if overlay_path:
                    file_queue.put(overlay_path)
                
                command_to_use = "/avatar set" if item_type == "avatar" else "/bg set"
                collection_command = "/avatar list" if item_type == "avatar" else "/bg list"
                
                purchase_info = (
                    f"**SUCCESSFUL PURCHASE!**\n\n"
                    f"{msg}\n\n"
                    f"**How to use your new {item_type}:**\n"
                    f"• Use `{command_to_use} <filename>` to set it as active\n"
                    f"• Check your collection with `{collection_command}`"
                )
                
                return purchase_info
                    
            except ValueError:
                self.send_message_image(sender, file_queue,
                    "Invalid number format\n\n"
                    "Please use: `/market buy <number>`\nExample: `/market buy 1`", 
                    "Market Error", cache, user_id)
                return ""

        elif cmd == "info" or cmd == "help":
            market_items = self.load_market_items()
            auctions = self.load_active_auctions()
            
            market_bg = sum(1 for item in market_items if item.get("type") == "background")
            market_av = sum(1 for item in market_items if item.get("type") == "avatar")
            
            auction_bg = sum(1 for auction in auctions if auction.get("type") == "background")
            auction_av = sum(1 for auction in auctions if auction.get("type") == "avatar")
            
            market_value = sum(item.get("price", 0) for item in market_items)
            auction_value = sum(auction.get("current_price", auction.get("start_price", 0)) for auction in auctions)
            
            most_expensive_market = max(market_items, key=lambda x: x.get("price", 0), default=None)
            most_expensive_auction = max(auctions, key=lambda x: x.get("current_price", x.get("start_price", 0)), default=None)
            
            info_text = (
                f"**MARKET SYSTEM OVERVIEW**\n\n"
                f"**Direct Market:**\n"
                f"• Items: {len(market_items)}\n"
                f"• Backgrounds: {market_bg}\n"
                f"• Avatars: {market_av}\n"
                f"• Total value: {market_value} coins\n"
            )
            
            if most_expensive_market:
                info_text += f"• Most expensive: {most_expensive_market.get('file', 'N/A')} - {most_expensive_market.get('price', 0)} coins\n"
            
            info_text += f"\n**Active Auctions:**\n"
            info_text += f"• Auctions: {len(auctions)}\n"
            info_text += f"• Backgrounds: {auction_bg}\n"
            info_text += f"• Avatars: {auction_av}\n"
            info_text += f"• Total value: {auction_value} coins\n"
            
            if most_expensive_auction:
                price = most_expensive_auction.get("current_price", most_expensive_auction.get("start_price", 0))
                info_text += f"• Most expensive: {most_expensive_auction.get('file', 'N/A')} - {price} coins\n"
            
            info_text += f"\n**Your Stats:**\n"
            info_text += f"• Balance: {user.get('balance', 0)} coins\n"
            info_text += f"• Market items: {sum(1 for item in market_items if item.get('seller_id') == user_id)}\n"
            info_text += f"• Auctions: {sum(1 for auction in auctions if auction.get('seller_id') == user_id)}\n"
            
            info_text += f"\n**Commands:**\n"
            info_text += f"`/market` - view direct market\n"
            info_text += f"`/market auctions` - view auctions\n"
            info_text += f"`/market buy <num>` - buy from market\n"
            info_text += f"`/market bid <num> <amount>` - bid on auction\n"
            info_text += f"`/market info` - this information\n"
            
            info_text += f"\n**Sell items:**\n"
            info_text += f"`/bg quicksell` - instant cash\n"
            info_text += f"`/bg sellprice` - list on market (fee: {self.listing_fee} coins)\n"
            info_text += f"`/bg auction` - create auction (fee: {self.auction_fee} coins)\n"
            info_text += f"`/avatar quicksell` - instant cash\n"
            info_text += f"`/avatar sellprice` - list on market (fee: {self.listing_fee} coins)\n"
            info_text += f"`/avatar auction` - create auction (fee: {self.auction_fee} coins)\n"
            
            info_text += f"\n*Last updated: {datetime.now().strftime('%H:%M:%S')}*"
            
            return info_text

        else:
            self.send_message_image(sender, file_queue,
                "**Market System Commands**\n\n"
                "**View Markets:**\n"
                "`/market` - view direct market\n"
                "`/market auctions` - view active auctions\n\n"
                "**Buy/Bid:**\n"
                "`/market buy <number>` - buy from market\n"
                "`/market bid <num> <amount>` - bid on auction\n\n"
                "**Information:**\n"
                "`/market info` - market statistics\n\n"
                "**Sell Items:**\n"
                "Use `/bg` or `/avatar` commands to sell items!",
                "Market System Help", cache, user_id)
            return ""

def register():
    plugin = BackgroundMarketPlugin()
    return {
        "name": "market",
        "aliases": ["/market"],
        "description": """**Player Market System**

Trade avatars and backgrounds with other players! Buy, sell, or bid in auctions.

**Market Viewing:**
• `/market` - Direct sales (buy items)
• `/market auctions` - Active auctions (bid on items)

**Buying & Bidding:**
• `/market buy <number>` - Purchase from market
• `/market bid <num> <amount>` - Place bid in auction

**Your Listings:**
• `/market cancel <number>` - Remove your listing
• `/market info` - Market statistics

**Sell Items With:**
• `/bg quicksell/sellprice/auction` - Backgrounds
• `/avatar quicksell/sellprice/auction` - Avatars""",
        "execute": plugin.execute_game
    }