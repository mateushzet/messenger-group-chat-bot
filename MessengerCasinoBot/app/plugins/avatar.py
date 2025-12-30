import os
import random
import glob
import time
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from base_game_plugin import BaseGamePlugin
from logger import logger
from utils import _get_unique_id

class AvatarPlugin(BaseGamePlugin):
    def __init__(self):
        results_folder = self.get_app_path("temp", "avatar_results")
        super().__init__(
            game_name="avatar_system",
            results_folder=results_folder,
        )
        self.avatars_folder = self.get_asset_path("avatars")
        error_folder = self.get_asset_path("errors")
        self.error_folder = error_folder
        
        os.makedirs(results_folder, exist_ok=True)
        os.makedirs(self.error_folder, exist_ok=True)
        
        self.available_avatars_cache = None
        self.avatars_cache_time = None
        self.avatar_config = {
            "available_for_roll": 50,
            "roll_animation_frames": 10,
            "roll_delay": 0.1,
            "chance_per_level": 0.3,
            "items_per_page": 9,
            "roll_cost": 1000
        }

    def get_available_avatars(self, force_refresh=False):
        if (
            not force_refresh
            and self.available_avatars_cache
            and self.avatars_cache_time
            and (datetime.now() - self.avatars_cache_time).seconds < 300
        ):
            return self.available_avatars_cache

        try:
            pattern = os.path.join(self.avatars_folder, "*.png")
            all_avatars = glob.glob(pattern)

            if not all_avatars:
                logger.warning(f"No avatars found in {self.avatars_folder}")
                self.available_avatars_cache = []
                self.avatars_cache_time = datetime.now()
                return []

            def sort_key(x):
                try:
                    return int(os.path.splitext(os.path.basename(x))[0])
                except ValueError:
                    return float("inf")

            all_avatars.sort(key=sort_key)

            available_count = self.avatar_config["available_for_roll"]
            avatar_files = all_avatars[:available_count]
            result = [os.path.basename(avatar) for avatar in avatar_files]

            self.available_avatars_cache = result
            self.avatars_cache_time = datetime.now()

            return result

        except Exception as e:
            logger.error(f"Error loading avatars: {e}")
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
            logger.info(f"User {user_id} unlocked avatar: {avatar_file}")
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
        logger.info(f"User {user_id} set avatar to: {avatar_file}")
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

        avatar_path = os.path.join(self.avatars_folder, avatar_file)
        if not os.path.exists(avatar_path):
            return False, "Avatar file not found"

        self.cache.add_market_item("avatar", avatar_file)
        
        success = self.remove_user_avatar(user_id, avatar_file)
        if not success:
            return False, "Failed to remove avatar from your collection"
        
        self.cache.update_balance(user_id, 100)

        return True, f"✅ Sold **{avatar_file}** for 100 coins!\nIt's now available on the market for other players."

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
        
        title_text = "YOUR AVATAR COLLECTION"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_x = (total_width - (title_bbox[2] - title_bbox[0])) // 2
        draw.text((title_x, MARGIN), title_text, fill=(255, 255, 255), font=title_font)
        
        page_text = f"Page {page}/{total_pages}"
        page_bbox = draw.textbbox((0, 0), page_text, font=page_font)
        page_x = (total_width - (page_bbox[2] - page_bbox[0])) // 2
        draw.text((page_x, MARGIN + 35), page_text, fill=(200, 200, 200), font=page_font)
        
        y_offset = MARGIN + 70
        
        for idx, avatar_file in enumerate(current_avatars):
            row = idx // ITEMS_PER_ROW
            col = idx % ITEMS_PER_ROW
            
            x = MARGIN + col * (ITEM_WIDTH + MARGIN)
            y = y_offset + row * (ITEM_HEIGHT + MARGIN)
            
            draw.rectangle([x, y, x + ITEM_WIDTH, y + ITEM_HEIGHT], 
                          fill=(50, 50, 60, 180), outline=(100, 100, 120), width=2)
            
            actual_index = start_idx + idx
            
            command_text = f"/ava set {actual_index + 1}"
            
            command_bbox = draw.textbbox((0, 0), command_text, font=command_font)
            command_x = x + (ITEM_WIDTH - (command_bbox[2] - command_bbox[0])) // 2
            command_y = y + 10
            draw.text((command_x, command_y), command_text, fill=(255, 255, 255), font=command_font)
            
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
                    
                    if is_default:
                        default_text = "DEFAULT"
                        default_bbox = draw.textbbox((0, 0), default_text, font=default_font)
                        default_x = x + (ITEM_WIDTH - (default_bbox[2] - default_bbox[0])) // 2
                        default_y = y + ITEM_HEIGHT - 35
                        draw.text((default_x, default_y), default_text, fill=(200, 200, 255), font=default_font)
                else:
                    if is_default:
                        name_text = "DEFAULT"
                    else:
                        name_text = os.path.splitext(avatar_file)[0]
                        if len(name_text) > 15:
                            name_text = name_text[:12] + "..."
                    
                    name_bbox = draw.textbbox((0, 0), name_text, font=active_font)
                    name_x = x + (ITEM_WIDTH - (name_bbox[2] - name_bbox[0])) // 2
                    name_y = y + (ITEM_HEIGHT - (name_bbox[3] - name_bbox[1])) // 2
                    draw.text((name_x, name_y), name_text, fill=(200, 200, 200), font=active_font)
                    
            except Exception as e:
                logger.error(f"Error loading avatar image {avatar_file}: {e}")
                error_text = "IMAGE ERROR"
                error_bbox = draw.textbbox((0, 0), error_text, font=command_font)
                error_x = x + (ITEM_WIDTH - (error_bbox[2] - error_bbox[0])) // 2
                error_y = y + (ITEM_HEIGHT - (error_bbox[3] - error_bbox[1])) // 2
                draw.text((error_x, error_y), error_text, fill=(255, 100, 100), font=command_font)
            
            if avatar_file == current_avatar:
                active_text = "ACTIVE"
                active_bbox = draw.textbbox((0, 0), active_text, font=active_font)
                active_x = x + (ITEM_WIDTH - (active_bbox[2] - active_bbox[0])) // 2
                if avatar_file == default_avatar_file or avatar_file == "default-avatar.png":
                    active_y = y + ITEM_HEIGHT - 50
                else:
                    active_y = y + ITEM_HEIGHT - 25
                draw.text((active_x, active_y), active_text, fill=(100, 255, 100), font=active_font)
        
        if total_pages > 1:
            instructions_y = total_height - 25
            if page < total_pages:
                instructions = f"Use '/avatar list {page + 1}' for next page"
            else:
                instructions = "Use '/avatar list 1' for first page"
            
            inst_bbox = draw.textbbox((0, 0), instructions, font=active_font)
            inst_x = (total_width - (inst_bbox[2] - inst_bbox[0])) // 2
            draw.text((inst_x, instructions_y), instructions, fill=(200, 200, 255), font=active_font)
        
        return img

    def create_roll_animation(self, user_id, sender, avatar_to_unlock, file_queue):
        try:
            import math, gc

            available_avatars = self.get_available_avatars()
            if not available_avatars or avatar_to_unlock not in available_avatars:
                return False

            width, height = 220, 220
            avatar_size = 100
            bg_color = (35, 35, 45)
            avatar_x = (width - avatar_size) // 2
            avatar_y = 62

            if not hasattr(self, "_cached_fonts"):
                try:
                    self._cached_fonts = {
                        "title": ImageFont.truetype("DejaVuSans-Bold.ttf", 18),
                        "text": ImageFont.truetype("DejaVuSans-Bold.ttf", 14),
                        "small": ImageFont.truetype("DejaVuSans-Bold.ttf", 12),
                        "tiny": ImageFont.truetype("DejaVuSans-Bold.ttf", 10),
                    }
                except:
                    default = ImageFont.load_default()
                    self._cached_fonts = {
                        "title": default,
                        "text": default,
                        "small": default,
                        "tiny": default,
                    }

            title_font = self._cached_fonts["title"]
            text_font = self._cached_fonts["text"]
            small_font = self._cached_fonts["small"]
            tiny_font = self._cached_fonts["tiny"]

            avatar_path = os.path.join(self.avatars_folder, avatar_to_unlock)
            if not os.path.exists(avatar_path):
                return False

            winner_img = Image.open(avatar_path).convert("RGBA")
            winner_img = winner_img.resize((avatar_size, avatar_size), Image.LANCZOS)

            other_paths = [
                os.path.join(self.avatars_folder, a)
                for a in available_avatars
                if a != avatar_to_unlock
            ]
            other_paths = [p for p in other_paths if os.path.exists(p)]

            bg_with_title = Image.new("RGBA", (width, height), bg_color)
            draw_bg = ImageDraw.Draw(bg_with_title)

            title = "LEVEL UP REWARD!"
            tw = draw_bg.textbbox((0, 0), title, font=title_font)[2]
            draw_bg.text(((width - tw) // 2, 4), title, fill=(120, 220, 255), font=title_font)

            sender_text = f"For: {sender[:25]}" if len(sender) > 25 else f"For: {sender}"
            sender_w = draw_bg.textbbox((0, 0), sender_text, font=tiny_font)[2]
            draw_bg.text(
                ((width - sender_w) // 2, 25),
                sender_text,
                fill=(200, 200, 220),
                font=tiny_font,
            )

            def create_frame(avatar_image=None, cmd_offset=50):
                frame_img = bg_with_title.copy()

                if avatar_image:
                    frame_img.paste(avatar_image, (avatar_x, avatar_y), avatar_image)

                if cmd_offset < 50:
                    draw_cmd = ImageDraw.Draw(frame_img)

                    set_cmd = f"/avatar set {avatar_to_unlock}"
                    w = draw_cmd.textbbox((0, 0), set_cmd, font=text_font)[2]
                    draw_cmd.text(
                        ((width - w) // 2, 45 + cmd_offset),
                        set_cmd,
                        fill=(210, 230, 255),
                        font=text_font,
                    )

                    sell_info = "Sell for 100 coins: /avatar sell"
                    info_w = draw_cmd.textbbox((0, 0), sell_info, font=small_font)[2]
                    draw_cmd.text(
                        ((width - info_w) // 2, height - 35 + cmd_offset),
                        sell_info,
                        fill=(200, 210, 240),
                        font=small_font,
                    )

                return frame_img.convert("RGB")

            frames = []
            durations = []

            roll_count = min(15, len(other_paths) * 2)

            for i in range(roll_count):
                random_path = random.choice(other_paths)
                try:
                    avatar = Image.open(random_path).convert("RGBA")
                    avatar = avatar.resize((avatar_size, avatar_size), Image.LANCZOS)
                except:
                    avatar = Image.new("RGBA", (avatar_size, avatar_size), (100, 100, 100, 255))

                if i < roll_count // 3:
                    duration = 80
                elif i < 2 * roll_count // 3:
                    duration = 60
                else:
                    duration = 40

                frames.append(create_frame(avatar))
                durations.append(duration)

                if i % 5 == 0:
                    gc.collect()

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
                method=6,
                minimize_size=True,
                allow_mixed=True,
            )

            del frames, durations, winner_img, bg_with_title
            gc.collect()

            file_queue.put(output)
            return True

        except Exception as e:
            print(f"[AVATAR ANIM ERROR] {e}")
            import traceback
            traceback.print_exc()
            return False

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 0)
        if error:
            self._send_error_image("validation_error", sender, file_queue)
            return ""
        
        nickname = sender
        
        if not args:
            user_avatars = self.get_user_avatars_for_display(user_id)
            if not user_avatars:
                self._send_error_image("no_avatars", nickname, file_queue)
                return ""
            
            img_path = os.path.join(self.results_folder, f"collection_{user_id}.webp")
            current_avatar = user.get("avatar", "default-avatar.png")
            collection_img = self.create_collection_image(user_avatars, current_avatar, user_id, 1)
            
            if collection_img:
                collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                
                overlay_path, error = self.apply_user_overlay(
                    img_path, user_id, sender, 0, 0, user["balance"], user
                )
                if overlay_path:
                    file_queue.put(overlay_path)
                
                return "**Your Avatar Collection**\nUse `/avatar set <number>` to set active avatar.\nUse `/avatar sell <number>` to sell avatar for 100 coins."
            else:
                self._send_error_image("image_generation_error", nickname, file_queue)
                return ""
        
        cmd = args[0].lower()
        
        if cmd == "set":
            if len(args) < 2:
                self._send_error_image("invalid_usage", nickname, file_queue, "Usage: /avatar set <number>")
                return ""
            
            set_arg = " ".join(args[1:])
            user_avatars = self.get_user_avatars_for_display(user_id)
            
            try:
                item_number = int(set_arg)
                if 1 <= item_number <= len(user_avatars):
                    avatar_name = user_avatars[item_number - 1]
                else:
                    self._send_error_image(
                        "invalid_range_set", 
                        nickname, 
                        file_queue, 
                        f"Choose 1-{len(user_avatars)}\nYou have {len(user_avatars)} avatars."
                    )
                    return ""
            except ValueError:
                avatar_name = set_arg
                if avatar_name not in user_avatars:
                    self._send_error_image(
                        "not_owned", 
                        nickname, 
                        file_queue, 
                        f"You don't own: {avatar_name}"
                    )
                    return ""
            
            if self.set_user_current_avatar(user_id, avatar_name):
                user_avatars = self.get_user_avatars_for_display(user_id)
                current_avatar = user.get("avatar", "default-avatar.png")
                
                page_with_item = 1
                if 'item_number' in locals() and item_number > 9:
                    page_with_item = (item_number - 1) // 9 + 1
                
                collection_img = self.create_collection_image(user_avatars, current_avatar, user_id, page_with_item)
                
                if collection_img:
                    img_path = os.path.join(self.results_folder, f"collection_after_set_{user_id}.webp")
                    collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                    
                    collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                    
                    overlay_path, error = self.apply_user_overlay(
                        img_path, user_id, sender, 0, 0, user["balance"], user
                    )
                    if overlay_path:
                        file_queue.put(overlay_path)
                    
                    return f"✅ Avatar set to: **{avatar_name}**\nNow active in your collection!"
                else:
                    self._send_error_image("set_success", nickname, file_queue, f"Avatar set to: {avatar_name}")
                    return ""
            else:
                self._send_error_image("set_error", nickname, file_queue)
                return ""
        
        elif cmd == "sell":
            if len(args) < 2:
                self._send_error_image(
                    "invalid_usage", 
                    nickname, 
                    file_queue, 
                    "Usage: /avatar sell <number>\nCheck available avatars with: /avatar list"
                )
                return ""
            
            try:
                index = int(args[1]) - 1
                user_avatars = self.get_user_avatars_for_display(user_id)
                
                if index < 0 or index >= len(user_avatars):
                    self._send_error_image(
                        "invalid_range_sell", 
                        nickname, 
                        file_queue, 
                        f"Choose 1-{len(user_avatars)}\nYou have {len(user_avatars)} avatars."
                    )
                    return ""
                
                avatar_file = user_avatars[index]
                
                default_avatar_file = self.get_user_default_avatar_file(user_id)
                if avatar_file == default_avatar_file or avatar_file == "default-avatar.png":
                    self._send_error_image("cannot_sell_default", nickname, file_queue)
                    return ""
                
                current_avatar = user.get("avatar", "")
                if avatar_file == current_avatar:
                    self._send_error_image("cannot_sell_active", nickname, file_queue)
                    return ""
                
                success, msg = self.sell_avatar_to_market(user_id, avatar_file)
                
                if success:
                    user_avatars = self.get_user_avatars_for_display(user_id)
                    collection_img = self.create_collection_image(user_avatars, user.get("avatar", ""), user_id, 1)
                    
                    if collection_img:
                        img_path = os.path.join(self.results_folder, f"collection_after_sell_{user_id}.webp")
                        collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                        
                        collection_img.save(img_path, format='WEBP', quality=85, optimize=True)
                        
                        overlay_path, error = self.apply_user_overlay(
                            img_path, user_id, sender, 100, 100, user["balance"], user
                        )
                        if overlay_path:
                            file_queue.put(overlay_path)
                        
                        return f"✅ Sold **{avatar_file}** for 100 coins!\nCheck your updated collection."
                    else:
                        self._send_error_image(
                            "sell_success", 
                            nickname, 
                            file_queue, 
                            f"Sold: {avatar_file}\nPrice: 100 coins\nNew balance: {user['balance']} coins"
                        )
                        return ""
                else:
                    self._send_error_image("sell_error", nickname, file_queue, msg)
                    return ""
                    
            except ValueError:
                self._send_error_image(
                    "invalid_range_sell", 
                    nickname, 
                    file_queue, 
                    f"Usage: /avatar sell <number>\n'{args[1]}' is not a valid number."
                )
                return ""
        
        elif cmd == "list" or cmd == "collection":
            user_avatars = self.get_user_avatars_for_display(user_id)
            if not user_avatars:
                self._send_error_image("no_avatars", nickname, file_queue)
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
                    img_path, user_id, sender, 0, 0, user["balance"], user
                )
                if overlay_path:
                    file_queue.put(overlay_path)
                
                total_pages = (len(user_avatars) + 8) // 9
                page_info = f" (Page {page}/{total_pages})" if total_pages > 1 else ""
                return f"**Your avatar collection{page_info}!**\nUse `/avatar set <number>` to set active.\nUse `/avatar sell <number>` to sell for 100 coins."
            else:
                self._send_error_image("image_generation_error", nickname, file_queue)
                return ""
        
        elif cmd == "current":
            current_avatar = user.get("avatar", "default-avatar.png")
            return f"Your current avatar: **{current_avatar}**\nUse `/avatar list` to see all your avatars."
        
        elif cmd == "roll":
            if user["balance"] < self.avatar_config["roll_cost"]:
                self._send_error_image(
                    "insufficient_funds", 
                    nickname, 
                    file_queue, 
                    f"Required: {self.avatar_config['roll_cost']}\nYou have: {user['balance']}"
                )
                return ""
            
            avatar_to_unlock = self.get_avatar_for_roll(user_id)
            if not avatar_to_unlock:
                self._send_error_image("all_avatars_owned", nickname, file_queue)
                return ""
            
            self.cache.update_balance(user_id, -self.avatar_config["roll_cost"])
            self.add_user_avatar(user_id, avatar_to_unlock)
            
            user["balance"] -= self.avatar_config["roll_cost"]
            
            self.create_roll_animation(user_id, sender, avatar_to_unlock, file_queue)
            
            return f"Spent {self.avatar_config['roll_cost']} coins on avatar roll!"
        
        else:
            return """**Avatar System Commands:**

**Collection:**
`/avatar` - show your avatars
`/avatar list [page]` - your collection
`/avatar set <number>` - set active avatar
`/avatar current` - current avatar

**Market:**
`/avatar sell <number>` - sell avatar for 100 coins
*Note: Default avatar cannot be sold*

**Roll (1000 coins):**
`/avatar roll` - try to get a new avatar

**Player Market:**
`/market` - view market (avatars & backgrounds)
`/market buy` - buy from market"""

    def on_level_up(self, user_id, sender, file_queue):
        print(f"[AVATAR] on_level_up START - user_id: {user_id}")
        
        try:
            print(f"[AVATAR] self.cache exists: {hasattr(self, 'cache')}")
            if hasattr(self, 'cache'):
                print(f"[AVATAR] self.cache value: {self.cache}")
                print(f"[AVATAR] self.cache type: {type(self.cache)}")
            
            if not hasattr(self, 'cache') or self.cache is None:
                print(f"[AVATAR] ERROR: cache is not set or is None!")
                logger.error("AvatarPlugin: cache is not set in on_level_up")
                return None
            
            print(f"[AVATAR] Calling cache.get_user({user_id})...")
            user = self.cache.get_user(user_id)
            print(f"[AVATAR] get_user returned: {user}")
            
            if not user:
                print(f"[AVATAR] ERROR: user {user_id} not found in cache")
                logger.error(f"AvatarPlugin: user {user_id} not found")
                return None
            
            print(f"[AVATAR] User found: name={user.get('name')}, level={user.get('level')}")
            
            print(f"[AVATAR] Testing get_available_avatars...")
            available = self.get_available_avatars()
            print(f"[AVATAR] Available avatars: {len(available)}")
            
            print(f"[AVATAR] Calling get_avatar_for_roll...")
            unlocked_avatar = self.get_avatar_for_roll(user_id)
            print(f"[AVATAR] get_avatar_for_roll returned: {unlocked_avatar}")
            
            if not unlocked_avatar:
                print(f"[AVATAR] No avatar to unlock (user has all or none available)")
                logger.info(f"AvatarPlugin: user {user_id} already has all avatars")
                return None
            
            print(f"[AVATAR] Avatar to unlock: {unlocked_avatar}")
            
            animation_created = False
            if file_queue:
                print(f"[AVATAR] Creating roll animation...")
                animation_created = self.create_roll_animation(user_id, sender, unlocked_avatar, file_queue)
                print(f"[AVATAR] Animation created: {animation_created}")
            
            print(f"[AVATAR] Adding avatar to collection...")
            added = self.add_user_avatar(user_id, unlocked_avatar)
            print(f"[AVATAR] Avatar added: {added}")
            
            if added:
                print(f"[AVATAR] SUCCESS! Avatar unlocked")
                logger.info(f"AvatarPlugin: user {user_id} unlocked avatar: {unlocked_avatar}")
                
                if animation_created:
                    return f"🎉 New avatar unlocked: {unlocked_avatar}\nUse: /avatar set {unlocked_avatar}"
                else:
                    return f"🎉 New avatar unlocked: {unlocked_avatar} (use /avatar set {unlocked_avatar})"
            else:
                print(f"[AVATAR] FAILED to add avatar")
                logger.error(f"AvatarPlugin: failed to add avatar {unlocked_avatar} to user {user_id}")
                return None
                
        except Exception as e:
            print(f"[AVATAR] EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error in on_level_up: {e}")
            return None

def register():
    plugin = AvatarPlugin()
    return {
        "name": "avatar",
        "aliases": ["/ava"],
        "description": "Avatar system: /avatar, /avatar set, /avatar sell, /avatar roll",
        "execute": plugin.execute_game
    }