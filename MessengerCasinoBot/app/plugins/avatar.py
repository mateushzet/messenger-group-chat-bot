import os
import random
import time
from PIL import Image, ImageDraw
from datetime import datetime
from base_game_plugin import BaseGamePlugin
from logger import logger

class AvatarPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="avatar_system")
        self.avatars_folder = self.get_asset_path("avatars")
        
        self.available_avatars_cache = None
        self.avatars_cache_time = None
        
        self.quick_sell_price = 100
        self.auction_listing_fee = 5

    def get_available_avatars(self, force_refresh=False):
        if (
            not force_refresh
            and self.available_avatars_cache
            and self.avatars_cache_time
            and (datetime.now() - self.avatars_cache_time).seconds < 300
        ):
            return self.available_avatars_cache

        try:
            MIN_AVATAR = 1
            MAX_AVATAR = 825
            
            all_possible_avatars = [f"{i}.png" for i in range(MIN_AVATAR, MAX_AVATAR + 1)]
            sample_size = min(50, len(all_possible_avatars))
            selected_avatars = random.sample(all_possible_avatars, sample_size)
            
            self.available_avatars_cache = selected_avatars
            self.avatars_cache_time = datetime.now()
            
            return selected_avatars
        except Exception as e:
            logger.error(f"[Avatar] Error generating avatars: {e}")
            return []

    def get_user_avatars(self, user_id):
        user = self.cache.get_user(user_id)
        if user and "avatars" in user:
            return user["avatars"]

        if user:
            avatars = []
            self.cache.update_user(user_id, avatars=avatars)
            return avatars

        return []

    def get_user_default_avatar_file(self, user_id):
        user = self.cache.get_user(user_id)
        if user and "avatar_url" in user and user["avatar_url"]:
            return user["avatar_url"]
        return None

    def get_user_avatars_for_display(self, user_id):
        user = self.cache.get_user(user_id)
        if not user:
            return []
        
        user_avatars = self.get_user_avatars(user_id)
        default_avatar_file = self.get_user_default_avatar_file(user_id)
        
        display_avatars = []
        
        if default_avatar_file:
            default_path = os.path.join(self.avatars_folder, default_avatar_file)
            if os.path.exists(default_path):
                display_avatars.append(default_avatar_file)
            else:
                display_avatars.append("default-avatar.png")
        else:
            display_avatars.append("default-avatar.png")
        
        for avatar in user_avatars:
            if avatar != default_avatar_file and avatar not in display_avatars:
                avatar_path = os.path.join(self.avatars_folder, avatar)
                if os.path.exists(avatar_path):
                    display_avatars.append(avatar)
        
        return display_avatars

    def add_user_avatar(self, user_id, avatar_file):
        user = self.cache.get_user(user_id)
        if not user:
            return False

        if "avatars" not in user:
            user["avatars"] = []

        default_avatar_file = self.get_user_default_avatar_file(user_id)
        if avatar_file == default_avatar_file:
            return True

        if avatar_file not in user["avatars"]:
            user["avatars"].append(avatar_file)
            self.cache.update_user(user_id, avatars=user["avatars"])
            return True
        return False

    def remove_user_avatar(self, user_id, avatar_file):
        user = self.cache.get_user(user_id)
        if not user or "avatars" not in user:
            return False

        default_avatar_file = self.get_user_default_avatar_file(user_id)
        if avatar_file == default_avatar_file:
            return False

        if avatar_file in user["avatars"]:
            user["avatars"].remove(avatar_file)
            self.cache.update_user(user_id, avatars=user["avatars"])
            return True
        return False

    def set_user_current_avatar(self, user_id, avatar_file):
        user = self.cache.get_user(user_id)
        if not user:
            return False

        default_avatar_file = self.get_user_default_avatar_file(user_id)
        
        if avatar_file == "default-avatar.png" or avatar_file == default_avatar_file:
            if default_avatar_file:
                avatar_to_set = default_avatar_file
            else:
                avatar_to_set = "default-avatar.png"
            
            if user.get("avatar") == avatar_to_set:
                return True
            
            self.cache.update_user(user_id, avatar=avatar_to_set)
            return True
        
        user_avatars = self.get_user_avatars_for_display(user_id)
        if avatar_file not in user_avatars:
            if user.get("avatar") == avatar_file:
                return True
            return False

        self.cache.update_user(user_id, avatar=avatar_file)
        return True

    def get_avatar_for_roll(self, user_id):
        available_avatars = self.get_available_avatars()
        user_avatars = self.get_user_avatars_for_display(user_id)

        if not available_avatars:
            return None

        available_for_user = [av for av in available_avatars 
                             if av not in user_avatars]

        if not available_for_user:
            return None

        return random.choice(available_for_user)

    def sell_avatar_to_market(self, user_id, avatar_file):
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"

        default_avatar_file = self.get_user_default_avatar_file(user_id)
        if avatar_file == default_avatar_file or avatar_file == "default-avatar.png":
            return False, "Cannot sell the default avatar"

        user_avatars = self.get_user_avatars_for_display(user_id)
        if avatar_file not in user_avatars:
            return False, "You do not own this avatar"

        if avatar_file == user.get("avatar"):
            return False, "Cannot sell active avatar"

        self.cache.add_market_item("avatar", avatar_file)
        
        success = self.remove_user_avatar(user_id, avatar_file)
        if not success:
            return False, "Failed to remove avatar from your collection"
        
        self.cache.update_balance(user_id, 100)

        return True, f"Sold **{avatar_file}** for 100 coins!\nIt's now available on the market for other players."

    def create_collection_image(self, user_avatars, current_avatar, user_id, page=1, items_per_page=9):
        if not user_avatars:
            return None
        
        total_items = len(user_avatars)
        total_pages = (total_items + items_per_page - 1) // items_per_page
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        current_avatars = user_avatars[start_idx:end_idx]
        
        ITEM_WIDTH = 200
        ITEM_HEIGHT = 200
        MARGIN = 20
        ITEMS_PER_ROW = 3
        
        rows = (len(current_avatars) + ITEMS_PER_ROW - 1) // ITEMS_PER_ROW
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
            title_text = "YOUR AVATAR COLLECTION"
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
            title_text = "YOUR AVATAR COLLECTION"
            title_bbox = draw.textbbox((0, 0), title_text)
            title_x = (total_width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, MARGIN), title_text, fill=(255, 255, 255))
            
            page_text = f"Page {page}/{total_pages}"
            page_bbox = draw.textbbox((0, 0), page_text)
            page_x = (total_width - (page_bbox[2] - page_bbox[0])) // 2
            draw.text((page_x, MARGIN + 35), page_text, fill=(200, 200, 200))
        
        y_offset = MARGIN + 70
        
        for idx, avatar_file in enumerate(current_avatars):
            row = idx // ITEMS_PER_ROW
            col = idx % ITEMS_PER_ROW
            
            x = MARGIN + col * (ITEM_WIDTH + MARGIN)
            y = y_offset + row * (ITEM_HEIGHT + MARGIN)
            
            draw_rect = ImageDraw.Draw(img)
            draw_rect.rectangle([x, y, x + ITEM_WIDTH, y + ITEM_HEIGHT], 
                              fill=(50, 50, 60, 180), outline=(100, 100, 120), width=2)
            
            actual_index = start_idx + idx
            
            if hasattr(self, 'text_renderer'):
                command_text = f"/ava set {actual_index + 1}"
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
            else:
                draw_rect.text((x + 10, y + 10), command_text, fill=(255, 255, 255))
            
            try:
                default_avatar_file = self.get_user_default_avatar_file(user_id)
                is_default = (avatar_file == default_avatar_file or 
                            avatar_file == "default-avatar.png")
                
                avatar_path = os.path.join(self.avatars_folder, avatar_file)
                if os.path.exists(avatar_path):
                    avatar_img = Image.open(avatar_path).convert('RGBA')
                    avatar_img = avatar_img.resize((ITEM_WIDTH - 40, ITEM_HEIGHT - 60), Image.LANCZOS)
                    
                    avatar_x = x + (ITEM_WIDTH - avatar_img.width) // 2
                    avatar_y = y + (ITEM_HEIGHT - avatar_img.height) // 2
                    img.paste(avatar_img, (avatar_x, avatar_y), avatar_img)
                    
                    if is_default and hasattr(self, 'text_renderer'):
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
            
            if avatar_file == current_avatar and hasattr(self, 'text_renderer'):
                active_img = self.text_renderer.render_text(
                    text="ACTIVE",
                    font_size=12,
                    color=(100, 255, 100, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                active_x = x + (ITEM_WIDTH - active_img.width) // 2
                if avatar_file == default_avatar_file or avatar_file == "default-avatar.png":
                    active_y = y + ITEM_HEIGHT - 50
                else:
                    active_y = y + ITEM_HEIGHT - 25
                img.paste(active_img, (active_x, active_y), active_img)
        
        if total_pages > 1 and hasattr(self, 'text_renderer'):
            instructions_y = total_height - 25
            if page < total_pages:
                instructions = f"Use '/avatar list {page + 1}' for next page"
            else:
                instructions = "Use '/avatar list 1' for first page"
            
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

    def create_roll_animation(self, user_id, sender, avatar_to_unlock, file_queue, title="LEVEL UP REWARD!"):
        try:
            import gc

            available_avatars = self.get_available_avatars()
            if not available_avatars or avatar_to_unlock not in available_avatars:
                return False

            width, height = 220, 220
            avatar_size = 100
            bg_color = (35, 35, 45)
            avatar_x = (width - avatar_size) // 2
            avatar_y = 62
            
            use_text_renderer = hasattr(self, 'text_renderer')
            
            bg_with_title = Image.new("RGBA", (width, height), bg_color)
            
            if use_text_renderer:
                title_img = self.text_renderer.render_text(
                    text=title,
                    font_size=18,
                    color=(120, 220, 255, 255),
                    stroke_width=2
                )
                title_x = (width - title_img.width) // 2
                bg_with_title.paste(title_img, (title_x, 4), title_img)
                
                sender_text = f"For: {sender[:25]}" if len(sender) > 25 else f"For: {sender}"
                sender_img = self.text_renderer.render_text(
                    text=sender_text,
                    font_size=10,
                    color=(200, 200, 220, 255)
                )
                sender_x = (width - sender_img.width) // 2
                bg_with_title.paste(sender_img, (sender_x, 25), sender_img)

            def create_frame(avatar_image=None, cmd_offset=50):
                frame_img = bg_with_title.copy()

                if avatar_image:
                    frame_img.paste(avatar_image, (avatar_x, avatar_y), avatar_image)

                if cmd_offset < 50 and use_text_renderer:
                    set_cmd = f"/avatar set {avatar_to_unlock}"
                    cmd_img = self.text_renderer.render_text(
                        text=set_cmd,
                        font_size=14,
                        color=(210, 230, 255, 255),
                        stroke_width=1
                    )
                    cmd_x = (width - cmd_img.width) // 2
                    frame_img.paste(cmd_img, (cmd_x, 45 + cmd_offset), cmd_img)

                    sell_info = "Sell for 100 coins: /avatar quickSell"
                    info_img = self.text_renderer.render_text(
                        text=sell_info,
                        font_size=10,
                        color=(200, 210, 240, 255)
                    )
                    info_x = (width - info_img.width) // 2
                    frame_img.paste(info_img, (info_x, height - 35 + cmd_offset), info_img)

                return frame_img.convert("RGB")

            frames = []
            durations = []

            other_paths = [
                os.path.join(self.avatars_folder, a)
                for a in available_avatars
                if a != avatar_to_unlock and os.path.exists(os.path.join(self.avatars_folder, a))
            ]

            roll_count = min(15, len(other_paths) * 2)

            for i in range(roll_count):
                random_path = random.choice(other_paths)
                try:
                    avatar = Image.open(random_path).convert("RGBA")
                    avatar = avatar.resize((avatar_size, avatar_size), Image.LANCZOS)
                except:
                    avatar = Image.new("RGBA", (avatar_size, avatar_size), (100, 100, 100, 255))

                duration = 80 if i < roll_count // 3 else 60 if i < 2 * roll_count // 3 else 40
                frames.append(create_frame(avatar))
                durations.append(duration)

            winner_path = os.path.join(self.avatars_folder, avatar_to_unlock)
            winner_img = Image.open(winner_path).convert("RGBA")
            winner_img = winner_img.resize((avatar_size, avatar_size), Image.LANCZOS)

            for _ in range(3):
                frames.append(create_frame(winner_img, cmd_offset=50))
                durations.append(30)

            highlight_frames = 8
            for i in range(highlight_frames):
                progress = i / highlight_frames
                offset = int(50 * (1 - progress**0.7))
                frames.append(create_frame(winner_img, cmd_offset=offset))
                durations.append(90 if i < 4 else 70)

            frames.append(create_frame(winner_img, cmd_offset=0))
            durations.append(3000)

            output = os.path.join(self.results_folder, f"roll_{user_id}.webp")

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

            del frames, durations, winner_img, bg_with_title
            gc.collect()

            file_queue.put(output)
            return True

        except Exception as e:
            logger.error(f"[Avatar] Roll animation error: {e}")
            return False
        
    def quick_sell_avatar(self, user_id, avatar_file):
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"
        
        default_avatar_file = self.get_user_default_avatar_file(user_id)
        if avatar_file == default_avatar_file or avatar_file == "default-avatar.png":
            return False, "Cannot quick sell the default avatar"
        
        if avatar_file == user.get("avatar"):
            return False, "Cannot quick sell active avatar"
        
        user_avatars = self.get_user_avatars_for_display(user_id)
        if avatar_file not in user_avatars:
            return False, "You don't own this avatar"
        
        success = self.remove_user_avatar(user_id, avatar_file)
        if not success:
            return False, "Failed to remove avatar"
        
        self.cache.update_balance(user_id, self.quick_sell_price)
        
        return True, f"Quick sold **{avatar_file}** for {self.quick_sell_price} coins!\nAvatar has been removed from your collection."

    def sell_avatar_for_price(self, user_id, avatar_file, price):
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"
        
        default_avatar_file = self.get_user_default_avatar_file(user_id)
        if avatar_file == default_avatar_file or avatar_file == "default-avatar.png":
            return False, "Cannot sell the default avatar"
        
        if avatar_file == user.get("avatar"):
            return False, "Cannot sell active avatar"
        
        if price < 50 or price > 10000:
            return False, "Price must be between 50 and 10,000 coins"
        
        user_avatars = self.get_user_avatars_for_display(user_id)
        if avatar_file not in user_avatars:
            return False, "You don't own this avatar"
        
        success = self.remove_user_avatar(user_id, avatar_file)
        
        market_item = {
            "type": "avatar",
            "file": avatar_file,
            "price": price,
            "seller_id": user_id,
            "seller_name": user.get("name", ""),
            "listed_at": time.time(),
            "status": "for_sale"
        }
        
        self.cache.add_market_item(market_item)
        
        return True, f"Listed **{avatar_file}** on market for {price} coins!\nListing fee: {self.auction_listing_fee} coins."

    def create_auction(self, user_id, avatar_file, start_price, min_bid, duration_hours):
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User not found"
        
        default_avatar_file = self.get_user_default_avatar_file(user_id)
        if avatar_file == default_avatar_file or avatar_file == "default-avatar.png":
            return False, "Cannot auction the default avatar"
        
        if avatar_file == user.get("avatar"):
            return False, "Cannot auction active avatar"
        
        if start_price < 50 or start_price > 10000:
            return False, "Start price must be between 50 and 10,000 coins"
        
        if min_bid < 10 or min_bid > 1000:
            return False, "Minimum bid must be between 10 and 1,000 coins"
        
        if duration_hours < 1 or duration_hours > 168:
            return False, "Auction duration must be 1-168 hours (1-7 days)"
        
        auction_fee = self.auction_listing_fee
        if user["balance"] < auction_fee:
            return False, f"Need {auction_fee} coins auction fee"
        
        self.cache.update_balance(user_id, -auction_fee)
        
        success = self.remove_user_avatar(user_id, avatar_file)
        if not success:
            self.cache.update_balance(user_id, auction_fee)
            return False, "Failed to remove avatar from collection"
        
        auction = {
            "type": "avatar",
            "file": avatar_file,
            "start_price": start_price,
            "current_price": start_price,
            "min_bid": min_bid,
            "seller_id": user_id,
            "seller_name": user.get("name", ""),
            "created_at": time.time(),
            "ends_at": time.time() + (duration_hours * 3600),
            "status": "active",
            "bids": [],
            "current_bidder": None
        }
        
        self.cache.add_auction(auction)
        
        return True, f"Created auction for **{avatar_file}**!\nStart price: {start_price} coins\nMin bid: {min_bid} coins\nDuration: {duration_hours} hours"

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 0)
        if error:
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Invalid user or authentication error",
                title="VALIDATION ERROR",
                cache=cache,
                user_id=user_id if user_id else None
            )
            return ""
        
        nickname = sender
        
        if not args:
            user_avatars = self.get_user_avatars_for_display(user_id)
            if not user_avatars:
                self.send_message_image(
                    nickname=nickname,
                    file_queue=file_queue,
                    message="You don't have any avatars yet.\n\nEarn them by leveling up!",
                    title="NO AVATARS",
                    cache=cache,
                    user_id=user_id
                )
                return ""
            
            img_path = os.path.join(self.results_folder, f"collection_{user_id}.webp")
            current_avatar = user.get("avatar", "default-avatar.png")
            collection_img = self.create_collection_image(user_avatars, current_avatar, user_id, 1)
            
            if collection_img:
                collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                
                overlay_path, error = self.apply_user_overlay(
                    img_path, user_id, sender, 0, 0, user["balance"], user, show_win_text=False, show_bet_amount=False
                )
                if overlay_path:
                    file_queue.put(overlay_path)
                
                return "**Your Avatar Collection**\nUse `/avatar set <number>` to set active avatar.\nUse `/avatar sell <number>` to sell avatar for 100 coins."
            else:
                self.send_message_image(
                    nickname=nickname,
                    file_queue=file_queue,
                    message="Failed to generate collection image",
                    title="IMAGE ERROR",
                    cache=cache,
                    user_id=user_id
                )
                return ""
        
        cmd = args[0].lower()
        
        if cmd == "quicksell" or cmd == "q" or cmd == "qs":
            if len(args) < 2:
                self.send_message_image(
                    nickname=nickname,
                    file_queue=file_queue,
                    message="**Quick Sell Help**\nUsage: `/avatar quicksell <number>`\nExample: `/avatar quicksell 3`\n\nInstant 100 coins - avatar is destroyed!",
                    title="QUICKSELL HELP",
                    cache=cache,
                    user_id=user_id
                )
                return ""
            
            try:
                index = int(args[1]) - 1
                user_avatars = self.get_user_avatars_for_display(user_id)
                
                if index < 0 or index >= len(user_avatars):
                    self.send_message_image(
                        nickname=nickname,
                        file_queue=file_queue,
                        message=f"Invalid avatar number!\nChoose between 1-{len(user_avatars)}\nYou have {len(user_avatars)} avatars.",
                        title="INVALID RANGE",
                        cache=cache,
                        user_id=user_id
                    )
                    return ""
                
                avatar_file = user_avatars[index]
                
                success, message = self.quick_sell_avatar(user_id, avatar_file)
                
                if success:
                    user_avatars = self.get_user_avatars_for_display(user_id)
                    collection_img = self.create_collection_image(user_avatars, user.get("avatar", ""), user_id, 1)
                    
                    if collection_img:
                        img_path = os.path.join(self.results_folder, f"collection_after_quicksell_{user_id}.webp")
                        collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                        
                        overlay_path, error = self.apply_user_overlay(
                            img_path, user_id, sender, self.quick_sell_price, self.quick_sell_price, 
                            user["balance"], user, show_win_text=False, show_bet_amount=False
                        )
                        if overlay_path:
                            file_queue.put(overlay_path)
                    
                    return message
                else:
                    self.send_message_image(
                        nickname=nickname,
                        file_queue=file_queue,
                        message=message,
                        title="QUICKSELL ERROR",
                        cache=cache,
                        user_id=user_id
                    )
                    return ""
                    
            except ValueError:
                self.send_message_image(
                    nickname=nickname,
                    file_queue=file_queue,
                    message="Invalid number format\nUsage: `/avatar quicksell <number>`",
                    title="INVALID INPUT",
                    cache=cache,
                    user_id=user_id
                )
                return ""
        elif cmd == "set":
            if len(args) < 2:
                self.send_message_image(
                    nickname=nickname,
                    file_queue=file_queue,
                    message="**Usage:** `/avatar set <number>`\n**Example:** `/avatar set 3`\n\nUse `/avatar list` to see your collection.",
                    title="SET AVATAR HELP",
                    cache=cache,
                    user_id=user_id
                )
                return ""
            
            set_arg = " ".join(args[1:])
            user_avatars = self.get_user_avatars_for_display(user_id)
            
            try:
                item_number = int(set_arg)
                if 1 <= item_number <= len(user_avatars):
                    avatar_name = user_avatars[item_number - 1]
                else:
                    self.send_message_image(
                        nickname=nickname,
                        file_queue=file_queue,
                        message=f"Invalid avatar number!\nChoose between 1-{len(user_avatars)}\nYou have {len(user_avatars)} avatars.",
                        title="INVALID RANGE",
                        cache=cache,
                        user_id=user_id
                    )
                    return ""
            except ValueError:
                avatar_name = set_arg
                if avatar_name not in user_avatars:
                    self.send_message_image(
                        nickname=nickname,
                        file_queue=file_queue,
                        message=f"You don't own this avatar: {avatar_name}\n\nUse `/avatar list` to see your collection.",
                        title="NOT OWNED",
                        cache=cache,
                        user_id=user_id
                    )
                    return ""
            
            if self.set_user_current_avatar(user_id, avatar_name):
                user = self.cache.get_user(user_id)
                
                user_avatars = self.get_user_avatars_for_display(user_id)
                current_avatar = user.get("avatar", "default-avatar.png")
                
                page_with_item = 1
                if 'item_number' in locals() and item_number > 9:
                    page_with_item = (item_number - 1) // 9 + 1
                
                collection_img = self.create_collection_image(user_avatars, current_avatar, user_id, page_with_item)
                
                if collection_img:
                    img_path = os.path.join(self.results_folder, f"collection_after_set_{user_id}.webp")
                    collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                    
                    overlay_path, error = self.apply_user_overlay(
                        img_path, user_id, sender, 0, 0, user["balance"], user,
                        show_win_text=False, show_bet_amount=False
                    )
                    if overlay_path:
                        file_queue.put(overlay_path)
                    
                    return f"**Avatar set to:** **{avatar_name}**\n\nNow active in your collection!"
                else:
                    return f"**Avatar set to:** **{avatar_name}**\n\nUse `/avatar list` to see your updated collection."
            else:
                logger.error(f"[Avatar] Failed to set avatar for user {user_id}")
                
                self.send_message_image(
                    nickname=nickname,
                    file_queue=file_queue,
                    message=f"Failed to set avatar to: {avatar_name}\n\nMake sure you own this avatar and it's not your default.",
                    title="SET ERROR",
                    cache=cache,
                    user_id=user_id
                )
                return ""
                
        elif cmd == "sellprice" or cmd == "sell" or cmd == "s":
            if len(args) < 3:
                self.send_message_image(
                    nickname=nickname,
                    file_queue=file_queue,
                    message="**Market List Help**\nUsage: `/avatar sellprice <number> <price>`\nExample: `/avatar sellprice 3 500`\n\nPrice: 50-10,000 coins\nListing fee: 5 coins\n\nYou'll get paid when someone buys it.",
                    title="MARKET LIST HELP",
                    cache=cache,
                    user_id=user_id
                )
                return ""
            
            try:
                index = int(args[1]) - 1
                price = int(args[2])
                
                user_avatars = self.get_user_avatars_for_display(user_id)
                
                if index < 0 or index >= len(user_avatars):
                    self.send_message_image(
                        nickname=nickname,
                        file_queue=file_queue,
                        message=f"Invalid avatar number!\nChoose between 1-{len(user_avatars)}",
                        title="INVALID RANGE",
                        cache=cache,
                        user_id=user_id
                    )
                    return ""
                
                avatar_file = user_avatars[index]
                
                success, message = self.sell_avatar_for_price(user_id, avatar_file, price)
                
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
                    self.send_message_image(
                        nickname=nickname,
                        file_queue=file_queue,
                        message=message,
                        title="SELL ERROR",
                        cache=cache,
                        user_id=user_id
                    )
                    return ""
                    
            except ValueError:
                self.send_message_image(
                    nickname=nickname,
                    file_queue=file_queue,
                    message="Invalid number format\nUsage: `/avatar sellprice <number> <price>`",
                    title="INVALID INPUT",
                    cache=cache,
                    user_id=user_id
                )
                return ""
        
        elif cmd == "auction" or cmd == "a":
            if len(args) < 5:
                self.send_message_image(
                    nickname=nickname,
                    file_queue=file_queue,
                    message="**Auction Help**\nUsage: `/avatar auction <number> <start_price> <min_bid> <hours>`\n\nExample: `/avatar auction 3 1000 50 24`\nStart price: 50-10,000 coins\nMin bid: 10-1,000 coins\nDuration: 1-168 hours\nAuction fee: 5 coins",
                    title="AUCTION HELP",
                    cache=cache,
                    user_id=user_id
                )
                return ""
            
            try:
                index = int(args[1]) - 1
                start_price = int(args[2])
                min_bid = int(args[3])
                duration_hours = int(args[4])
                
                user_avatars = self.get_user_avatars_for_display(user_id)
                
                if index < 0 or index >= len(user_avatars):
                    self.send_message_image(
                        nickname=nickname,
                        file_queue=file_queue,
                        message=f"Invalid avatar number!\nChoose between 1-{len(user_avatars)}",
                        title="INVALID RANGE",
                        cache=cache,
                        user_id=user_id
                    )
                    return ""
                
                avatar_file = user_avatars[index]
                
                success, message = self.create_auction(user_id, avatar_file, start_price, min_bid, duration_hours)
                
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
                    self.send_message_image(
                        nickname=nickname,
                        file_queue=file_queue,
                        message=message,
                        title="AUCTION ERROR",
                        cache=cache,
                        user_id=user_id
                    )
                    return ""
                    
            except ValueError:
                self.send_message_image(
                    nickname=nickname,
                    file_queue=file_queue,
                    message="Invalid number format\nCheck all parameters are numbers",
                    title="INVALID INPUT",
                    cache=cache,
                    user_id=user_id
                )
                return ""
        
        elif cmd == "list" or cmd == "collection" or cmd == "l" :
            user_avatars = self.get_user_avatars_for_display(user_id)
            if not user_avatars:
                self.send_message_image(
                    nickname=nickname,
                    file_queue=file_queue,
                    message="You don't have any avatars yet.\n\nEarn them by leveling up!",
                    title="NO AVATARS",
                    cache=cache,
                    user_id=user_id
                )
                return ""
            
            page = 1
            if len(args) > 1:
                try:
                    page = int(args[1])
                except ValueError:
                    page = 1
            
            current_avatar = user.get("avatar", "default-avatar.png")
            collection_img = self.create_collection_image(user_avatars, current_avatar, user_id, page)
            
            if collection_img:
                img_path = os.path.join(self.results_folder, f"collection_{user_id}_page{page}.webp")
                collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                
                overlay_path, error = self.apply_user_overlay(
                    img_path, user_id, sender, 0, 0, user["balance"], user, show_win_text=False, show_bet_amount=False
                )
                if overlay_path:
                    file_queue.put(overlay_path)
                
                total_pages = (len(user_avatars) + 8) // 9
                page_info = f" (Page {page}/{total_pages})" if total_pages > 1 else ""
                return f"**Your avatar collection{page_info}!**\nUse `/avatar set <number>` to set active.\nUse `/avatar sell <number>` to sell for 100 coins."
            else:
                self.send_message_image(
                    nickname=nickname,
                    file_queue=file_queue,
                    message="Failed to generate collection image",
                    title="IMAGE ERROR",
                    cache=cache,
                    user_id=user_id
                )
                return ""
        elif cmd == "craft" or cmd == "c":
            try:
                craft_args = []
                if len(args) > 1:
                    if ',' in args[1]:
                        craft_args = args[1].split(',')
                    else:
                        craft_args = args[1:]
                
                if len(craft_args) < 3:
                    self.send_message_image(
                        nickname=nickname,
                        file_queue=file_queue,
                        message="**Crafting System**\n\nUsage: `/ava craft <id1> <id2> <id3>`\nExamples:\n• `/ava craft 4 5 6` (spaces)\n• `/ava craft 4,5,6` (commas)\n\nWarning: Lose 3 avatars to get 1 random new avatar!",
                        title="CRAFTING HELP",
                        cache=cache,
                        user_id=user_id
                    )
                    return ""
                
                craft_args = craft_args[:3]
                
                av_numbers = []
                for arg in craft_args:
                    try:
                        num = int(arg.strip())
                        av_numbers.append(num)
                    except ValueError:
                        self.send_message_image(
                            nickname=nickname,
                            file_queue=file_queue,
                            message=f"Invalid number: '{arg}'!\nUse numbers only.",
                            title="INVALID INPUT",
                            cache=cache,
                            user_id=user_id
                        )
                        return ""
                
                av1, av2, av3 = av_numbers
                
                user_avatars_display = self.get_user_avatars_for_display(user_id)
                avatar_files = []
                missing_indices = []
                
                for index_num in [av1, av2, av3]:
                    if 1 <= index_num <= len(user_avatars_display):
                        avatar_file = user_avatars_display[index_num - 1]
                        avatar_files.append(avatar_file)
                    else:
                        missing_indices.append(str(index_num))
                
                if missing_indices:
                    self.send_message_image(
                        nickname=nickname,
                        file_queue=file_queue,
                        message=f"Invalid avatar numbers!\nYou don't have avatars at positions: #{', #'.join(missing_indices)}\nYou have {len(user_avatars_display)} avatars.",
                        title="INVALID INDICES",
                        cache=cache,
                        user_id=user_id
                    )
                    return ""
                
                if len(set(av_numbers)) != 3:
                    self.send_message_image(
                        nickname=nickname,
                        file_queue=file_queue,
                        message="Duplicate avatars!\nYou must use 3 different avatars.",
                        title="DUPLICATES ERROR",
                        cache=cache,
                        user_id=user_id
                    )
                    return ""
                
                default_avatar_file = self.get_user_default_avatar_file(user_id)
                current_avatar = user.get("avatar", "")
                
                for i, avatar_file in enumerate(avatar_files):
                    if avatar_file == default_avatar_file or avatar_file == "default-avatar.png":
                        self.send_message_image(
                            nickname=nickname,
                            file_queue=file_queue,
                            message=f"Cannot craft with default avatar!\nAvatar #{av_numbers[i]} is your default/starting avatar.",
                            title="DEFAULT AVATAR",
                            cache=cache,
                            user_id=user_id
                        )
                        return ""
                    
                    if avatar_file == current_avatar:
                        self.send_message_image(
                            nickname=nickname,
                            file_queue=file_queue,
                            message=f"Cannot craft with active avatar!\nAvatar #{av_numbers[i]} is currently active.\nChange avatar first.",
                            title="ACTIVE AVATAR",
                            cache=cache,
                            user_id=user_id
                        )
                        return ""
                
                avatar_to_unlock = self.get_avatar_for_roll(user_id)
                
                if not avatar_to_unlock:
                    self.send_message_image(
                        nickname=nickname,
                        file_queue=file_queue,
                        message="Congratulations!\nYou already own all available avatars!\n\nCheck the market for more options.",
                        title="ALL AVATARS OWNED",
                        cache=cache,
                        user_id=user_id
                    )
                    return ""
                
                for avatar_file in avatar_files:
                    self.remove_user_avatar(user_id, avatar_file)
                
                added = self.add_user_avatar(user_id, avatar_to_unlock)
                animation_result = self.create_roll_animation(user_id, sender, avatar_to_unlock, file_queue, title="AVATAR CRAFTED!")
                
                return f"**Crafting complete!**\n\n" \
                    f"**Sacrificed avatars from collection:** #{av1}, #{av2}, #{av3}\n" \
                    f"**Obtained new avatar:** **{avatar_to_unlock.replace('.png', '')}**\n\n" \
                    f"*Three have become one!*"

            except Exception as e:
                self.send_message_image(
                    nickname=nickname,
                    file_queue=file_queue,
                    message=f"**Crafting failed!**\nAn error occurred: {str(e)[:50]}",
                    title="CRAFTING ERROR",
                    cache=cache,
                    user_id=user_id
                )
                return ""
        
        else:
            return """**Avatar System Commands:**

**Collection:**
`/avatar` - Show your avatar collection
`/avatar list [page]` - Browse your collection
`/avatar set <number>` - Set active avatar

**Crafting:**
`/avatar craft <id1> <id2> <id3>` - Combine 3 avatars into 1 new random avatar

**Selling:**
`/avatar sell <number>` - Quick sell for 100 coins
`/avatar sellprice <num> <price>` - List on market (50-10,000 coins)
`/avatar auction <num> <start> <min_bid> <hours>` - Create auction

**Market:**
`/market` - View player market
`/market buy` - Buy items from market"""

    def on_level_up(self, user_id, sender, file_queue):
        try:
            if not hasattr(self, 'cache') or self.cache is None:
                logger.error("[Avatar] AvatarPlugin: cache is not set in on_level_up")
                return None
            
            user = self.cache.get_user(user_id)
            if not user:
                logger.error(f"[Avatar] AvatarPlugin: user {user_id} not found")
                return None
            
            unlocked_avatar = self.get_avatar_for_roll(user_id)
            if not unlocked_avatar:
                logger.info(f"[Avatar] AvatarPlugin: user {user_id} already has all avatars")
                return None
            
            animation_created = False
            if file_queue:
                animation_created = self.create_roll_animation(user_id, sender, unlocked_avatar, file_queue)
            
            added = self.add_user_avatar(user_id, unlocked_avatar)
            
            if added:
                logger.info(f"[Avatar] AvatarPlugin: user {user_id} unlocked avatar: {unlocked_avatar}")
                
                if animation_created:
                    return f"New avatar unlocked: {unlocked_avatar}\nUse: /avatar set {unlocked_avatar}"
                else:
                    return f"New avatar unlocked: {unlocked_avatar} (use /avatar set {unlocked_avatar})"
            else:
                logger.error(f"[Avatar] AvatarPlugin: failed to add avatar {unlocked_avatar} to user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"[Avatar] Error in on_level_up: {e}")
            return None

def register():
    plugin = AvatarPlugin()
    return {
        "name": "avatar",
        "aliases": ["/ava"],
        "description": """**Avatar Collection System**

Collect and customize your avatars! Earn new avatars by leveling up, buy/sell on the market, or craft new ones.

**Main Commands:**
• `/avatar` - View your collection
• `/avatar set <number>` - Change active avatar
• `/avatar craft <1> <2> <3>` - Combine 3 avatars into 1 new
• `/avatar sellprice <num> <price>` - List on market
• `/avatar auction` - Create auctions
• `/market` - Player marketplace""",
        "execute": plugin.execute_game
    }