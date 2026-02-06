import os
import random
import re
import time
from base_game_plugin import BaseGamePlugin
from logger import logger
from PIL import Image, ImageDraw, ImageFont

class CaseBattle:
    def __init__(self, plugin_instance):
        self.plugin = plugin_instance
    
    def _get_cache_battles(self):
        return self.plugin.cache.get_setting("case_battles", {}) if self.plugin.cache else {}
    
    def _save_cache_battles(self, battles):
        if self.plugin.cache:
            self.plugin.cache.set_setting("case_battles", battles)
        
    def create_battle(self, creator_id, creator_name, case_price, file_queue, cache):
        battles = self._get_cache_battles()
        
        if not battles:
            battle_counter = 1
        else:
            battle_counter = self.plugin.cache.get_setting("case_battle_counter", 1)
        
        battle_id = battle_counter
        
        new_battle = {
            'id': battle_id,
            'creator_id': creator_id,
            'creator_name': creator_name,
            'case_price': case_price,
            'status': 'waiting',
            'created_at': time.time()
        }
        
        battles[str(battle_id)] = new_battle
        self._save_cache_battles(battles)
        self.plugin.cache.set_setting("case_battle_counter", battle_counter + 1)
        
        logger.info(f"[Case] Battle {battle_id} created by {creator_name} for ${case_price}")
        return battle_id
    
    def get_active_battles(self):
        battles = self._get_cache_battles()
        active = []
        
        for battle_id_str, battle in battles.items():
            if battle.get('status') == 'waiting':
                active.append(battle)
        
        return active

    def get_battle(self, battle_id):
        battles = self._get_cache_battles()
        battle_id_str = str(battle_id)
        
        if battle_id_str in battles:
            battle = battles[battle_id_str]
            return battle
        return None
    
    def accept_battle(self, battle_id, acceptor_id, acceptor_name):
        battles = self._get_cache_battles()
        battle_id_str = str(battle_id)
        
        if battle_id_str not in battles:
            return False, "Battle not found"
        
        battle = battles[battle_id_str]
        
        if battle.get('status') != 'waiting':
            return False, "Battle already accepted or completed"
        
        if battle.get('creator_id') == acceptor_id:
            return False, "Cannot accept your own battle"
        
        battle['acceptor_id'] = acceptor_id
        battle['acceptor_name'] = acceptor_name
        battle['status'] = 'active'
        
        battles[battle_id_str] = battle
        self._save_cache_battles(battles)
        
        logger.info(f"[Case] Battle {battle_id} accepted by {acceptor_name}")
        return True, "Battle accepted"
        
    def complete_battle(self, battle_id, creator_win, acceptor_win):
        battles = self._get_cache_battles()
        battle_id_str = str(battle_id)
        
        if battle_id_str not in battles:
            logger.error(f"[Case] Battle {battle_id} not found in cache")
            return False, "Battle not found"
        
        battle = battles[battle_id_str]
        
        if creator_win > acceptor_win:
            result = 'creator_wins'
            winner = battle.get('creator_name', 'Unknown')
            winner_total = creator_win + acceptor_win
        elif acceptor_win > creator_win:
            result = 'acceptor_wins'
            winner = battle.get('acceptor_name', 'Unknown')
            winner_total = creator_win + acceptor_win
        else:
            result = 'draw'
            winner = 'both'
            winner_total = (creator_win + acceptor_win) / 2
        
        completed_battle = {
            'id': battle.get('id'),
            'creator_name': battle.get('creator_name'),
            'acceptor_name': battle.get('acceptor_name'),
            'case_price': battle.get('case_price', 0),
            'creator_win': creator_win,
            'acceptor_win': acceptor_win,
            'result': result,
            'winner': winner,
            'winner_total': winner_total,
            'completed_at': time.time()
        }
        
        if battle_id_str in battles:
            del battles[battle_id_str]
            self._save_cache_battles(battles)
        
        return True, completed_battle
    
    def cancel_battle(self, battle_id, user_id):
        battles = self._get_cache_battles()
        battle_id_str = str(battle_id)
        
        if battle_id_str not in battles:
            return False, "Battle not found"
        
        battle = battles[battle_id_str]
        
        if battle.get('creator_id') != user_id:
            return False, "You can only cancel your own battles"
        
        if battle.get('status') != 'waiting':
            return False, "Battle already started or completed"
        
        del battles[battle_id_str]
        self._save_cache_battles(battles)
        
        logger.info(f"[Case] Battle {battle_id} cancelled and removed from cache by user {user_id}")
        return True, "Battle cancelled successfully"
    
    def get_user_battles(self, user_id):
        battles = self._get_cache_battles()
        user_battles = []
        
        for battle_id_str, battle in battles.items():
            if (battle.get('creator_id') == user_id and 
                battle.get('status') == 'waiting'):
                user_battles.append(battle)
        
        return user_battles

class CasePlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="case"
        )
        self.case_prices = [10, 100, 1000]
        self.case_animations = {}
        self.battle_manager = CaseBattle(self)

        self.colors = {
            'bg_dark': (20, 20, 30, 255),
            'bg_medium': (30, 35, 45, 255),
            'bg_light': (40, 45, 55, 255),
            'text_primary': (240, 240, 240, 255),
            'text_secondary': (180, 180, 200, 255),
            'text_highlight': (80, 160, 255, 255),
            'success': (70, 180, 90, 255),
            'warning': (220, 180, 60, 255),
            'danger': (220, 80, 80, 255),
            'border': (70, 80, 100, 255)
        }
            
    def _create_battle_user_info_before(self, username, case_price, actual_balance, user_data):
        return self.create_user_info(
            username,
            case_price,
            0,
            actual_balance,
            user_data
        )

    def _create_battle_user_info_after(self, username, case_price, net_win, final_balance, user_data):
        return self.create_user_info(
            username,
            case_price,
            net_win,
            final_balance,
            user_data
        )
    
    def load_case_animations(self, case_price):
        case_folder = self.get_asset_path("case", str(case_price))
        
        if not os.path.exists(case_folder):
            logger.error(f"[Case] Case folder not found: {case_folder}")
            return []
        
        animation_files = []
        for file in os.listdir(case_folder):
            if file.startswith(f"case_{case_price}_") and file.endswith('.webp'):
                animation_files.append(file)
        
        animation_files.sort(key=lambda x: self._extract_animation_number(x))
        
        return [os.path.join(case_folder, f) for f in animation_files]
    
    def _extract_animation_number(self, filename):
        match = re.search(r'case_\d+_(\d+)', filename)
        if match:
            return int(match.group(1))
        return 0
    
    def _extract_win_amount(self, filename):
        match = re.search(r'\((\d+)\)', filename)
        if match:
            return int(match.group(1))
        return 0
    
    def get_random_case_animation(self, case_price):
        if case_price not in self.case_animations:
            self.case_animations[case_price] = self.load_case_animations(case_price)
        
        animations = self.case_animations[case_price]
        if not animations:
            logger.error(f"[Case] No animations found for case ${case_price}")
            return None, 0
        
        animation_path = random.choice(animations)
        win_amount = self._extract_win_amount(os.path.basename(animation_path))
        
        return animation_path, win_amount
            
    def _combine_two_animations(self, animation1_path, animation2_path, battle_id):
        try:
            if hasattr(self.generator, '_load_animation_frames'):
                frames1 = self.generator._load_animation_frames(animation1_path)
                frames2 = self.generator._load_animation_frames(animation2_path)
            else:
                logger.error(f"[Case] Error loading animation {e}")
                return None, "Failed to load animation frames"
            
            if not frames1 or not frames2:
                return None, "Failed to load animation frames"
            
            width1, height1 = frames1[0].size
            width2, height2 = frames2[0].size
            
            combined_width = max(width1, width2)
            combined_height = height1 + height2
            
            frame_count = max(len(frames1), len(frames2))
            
            combined_frames = []
            frame_durations = []
            
            BASE_DURATION = 70
            LAST_FRAME_MULTIPLIER = 30
            
            for i in range(frame_count):
                combined_frame = Image.new('RGBA', (combined_width, combined_height), (0, 0, 0, 0))
                
                if i < len(frames1):
                    frame1 = frames1[i]
                else:
                    frame1 = frames1[-1]
                
                combined_frame.paste(frame1, ((combined_width - width1) // 2, 0))
                
                if i < len(frames2):
                    frame2 = frames2[i]
                else:
                    frame2 = frames2[-1]
                
                combined_frame.paste(frame2, ((combined_width - width2) // 2, height1))
                
                combined_frame_rgb = combined_frame.convert('RGB')
                combined_frames.append(combined_frame_rgb)
                
                if i == frame_count - 1:
                    duration = BASE_DURATION * LAST_FRAME_MULTIPLIER
                else:
                    duration = BASE_DURATION
                
                frame_durations.append(duration)
            
            if len(combined_frames) > 0 and combined_frames[0].size[0] * combined_frames[0].size[1] > 1000000:
                MAX_WIDTH = 800
                if combined_frames[0].size[0] > MAX_WIDTH:
                    scale_factor = MAX_WIDTH / combined_frames[0].size[0]
                    new_width = MAX_WIDTH
                    new_height = int(combined_frames[0].size[1] * scale_factor)
                    
                    scaled_frames = []
                    for frame in combined_frames:
                        scaled_frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        scaled_frames.append(scaled_frame)
                    
                    combined_frames = scaled_frames
            
            temp_dir = self.get_app_path("temp", "battles")
            os.makedirs(temp_dir, exist_ok=True)
            
            timestamp = int(time.time() * 1000)
            output_path = os.path.join(temp_dir, f"case_battle_{battle_id}_{timestamp}.webp")
            
            if len(combined_frames) > 1:
                save_kwargs = {
                    'save_all': True,
                    'append_images': combined_frames[1:],
                    'duration': frame_durations,
                    'loop': 0,
                    'quality': 80,
                    'method': 0,
                }
                
                combined_frames[0].save(output_path, format='WEBP', **save_kwargs)
            else:
                combined_frames[0].save(output_path, format='WEBP', quality=80)
                        
            try:
                if os.path.exists(animation1_path):
                    os.remove(animation1_path)
            except Exception as e:
                logger.debug(f"[Case] Error removing {animation1_path}: {e}")
                
            try:
                if os.path.exists(animation2_path):
                    os.remove(animation2_path)
            except Exception as e:
                logger.debug(f"[Case] Error removing {animation2_path}: {e}")
            
            return output_path, None
                
        except Exception as e:
            logger.error(f"[Case] Error combining animations: {e}")
            return None, str(e)
            
    def _generate_battle_list_image(self, battles, user_id, user_background_path=None):
        try:
            
            IMAGE_WIDTH = 1000
            ITEMS_PER_ROW = 3
            ITEM_WIDTH = 320
            ITEM_HEIGHT = 220
            ITEM_MARGIN = 15
            AVATAR_SIZE = 80
            CASE_ICON_SIZE = 60
            ID_FONT_SIZE = 36
            
            num_battles = len(battles)
            rows = (num_battles + ITEMS_PER_ROW - 1) // ITEMS_PER_ROW
            
            header_height = 60
            footer_height = 120
            grid_height = rows * (ITEM_HEIGHT + ITEM_MARGIN)
            total_height = header_height + grid_height + footer_height
                        
            bg_color = tuple(self.colors['bg_dark'][:3])
            bg = Image.new('RGB', (IMAGE_WIDTH, total_height), bg_color)
            
            text_renderer = self.generator.text_renderer
            colors = getattr(self.generator, 'colors', self.colors)
            
            header_text = "ACTIVE CASE BATTLES"
            header_img = text_renderer.render_text(
                text=header_text,
                font_size=28,
                color=colors.get('text_primary', (240, 240, 240, 255)),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255)
            )
            
            header_x = (IMAGE_WIDTH - header_img.width) // 2
            header_y = 20
            bg.paste(header_img, (header_x, header_y), header_img)
            
            grid_start_y = header_height
            grid_width = ITEMS_PER_ROW * (ITEM_WIDTH + ITEM_MARGIN) - ITEM_MARGIN
            grid_start_x = (IMAGE_WIDTH - grid_width) // 2
            
            for i, battle in enumerate(battles):
                row = i // ITEMS_PER_ROW
                col = i % ITEMS_PER_ROW
                
                item_x = grid_start_x + col * (ITEM_WIDTH + ITEM_MARGIN)
                item_y = grid_start_y + row * (ITEM_HEIGHT + ITEM_MARGIN)
                
                item_bg = Image.new('RGB', (ITEM_WIDTH, ITEM_HEIGHT), 
                                tuple(colors.get('bg_medium', (30, 35, 45))[:3]))
                
                battle_id = battle.get('id', '?')
                creator_id = battle.get('creator_id', '')
                creator_name = battle.get('creator_name', 'Unknown')
                
                avatar_x = (ITEM_WIDTH - AVATAR_SIZE) // 2
                avatar_y = 20
                
                avatar_img = self._load_avatar_simple(creator_id, AVATAR_SIZE)
                if avatar_img:
                    item_bg.paste(avatar_img, (avatar_x, avatar_y))
                else:
                    avatar_placeholder = self._create_simple_avatar(creator_name, AVATAR_SIZE)
                    item_bg.paste(avatar_placeholder, (avatar_x, avatar_y))
                
                name_img = text_renderer.render_text(
                    text=creator_name,
                    font_size=16,
                    color=colors.get('text_primary', (240, 240, 240, 255)),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 150)
                )
                
                name_x = (ITEM_WIDTH - name_img.width) // 2
                name_y = avatar_y + AVATAR_SIZE + 10
                item_bg.paste(name_img, (name_x, name_y), name_img)
                
                content_start_y = name_y + name_img.height + 20
                
                case_price = battle.get('case_price', 0)
                case_icon = self._get_simple_case_icon(case_price, CASE_ICON_SIZE)
                
                id_text = f"#{battle_id}"
                id_img = text_renderer.render_text(
                    text=id_text,
                    font_size=ID_FONT_SIZE,
                    color=colors.get('text_highlight', (80, 160, 255, 255)),
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 255)
                )
                
                spacing = 20
                total_width = CASE_ICON_SIZE + spacing + id_img.width
                start_x = (ITEM_WIDTH - total_width) // 2
                
                case_x = start_x
                case_y = content_start_y + (id_img.height - CASE_ICON_SIZE) // 2
                
                id_x = start_x + CASE_ICON_SIZE + spacing
                id_y = content_start_y
                
                if case_icon:
                    item_bg.paste(case_icon, (case_x, case_y), case_icon)
                
                item_bg.paste(id_img, (id_x, id_y), id_img)
                
                bg.paste(item_bg, (item_x, item_y))
            
            footer_y = grid_start_y + grid_height + 40
            
            commands = [
                "Create battle: /cs b start <price>",
                "Accept battle: /cs b a <number>", 
                "Cancel battle: /cs b cancel <number>",
            ]
            
            for j, cmd in enumerate(commands):
                cmd_img = text_renderer.render_text(
                    text=cmd,
                    font_size=14,
                    color=colors.get('text_primary', (240, 240, 240, 255)),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 150)
                )
                
                cmd_x = (IMAGE_WIDTH - cmd_img.width) // 2
                cmd_y = footer_y + (j * 25)
                bg.paste(cmd_img, (cmd_x, cmd_y), cmd_img)
            
            temp_dir = self.get_app_path("temp", "battle_list")
            os.makedirs(temp_dir, exist_ok=True)
            
            timestamp = int(time.time())
            output_path = os.path.join(temp_dir, f"battle_list_{user_id}_{timestamp}.png")
            
            bg.save(output_path, format='PNG', optimize=True, quality=95)
            
            return output_path
            
        except Exception as e:
            logger.error(f"[Case] Error generating battle list image: {e}", exc_info=True)
            return None

    def _load_avatar_simple(self, user_id, size):
        try:
            if not self.cache:
                return None
            
            avatar_path = None
            if hasattr(self.cache, 'get_avatar_path'):
                avatar_path = self.cache.get_avatar_path(user_id)
            
            if avatar_path and os.path.exists(avatar_path):
                img = Image.open(avatar_path).convert('RGB')
                img = img.resize((size, size), Image.Resampling.LANCZOS)
                return img
                
        except Exception as e:
            logger.debug(f"[Case] Error loading avatar: {e}")
            return None

    def _create_simple_avatar(self, username, size):
        try:
            colors = [
                (60, 100, 180),
                (180, 80, 160),
                (80, 160, 100),
                (200, 140, 60),
                (140, 100, 200),
            ]
            
            color_idx = hash(username) % len(colors)
            bg_color = colors[color_idx]
            
            avatar = Image.new('RGB', (size, size), bg_color)
            draw = ImageDraw.Draw(avatar)
            
            initials = ''.join([word[0].upper() for word in username.split()[:2]])[:2]
            if not initials:
                initials = username[0].upper() if username else "?"
            
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", size // 3)
            except:
                font = ImageFont.load_default()
            
            initials_bbox = draw.textbbox((0, 0), initials, font=font)
            initials_x = (size - (initials_bbox[2] - initials_bbox[0])) // 2
            initials_y = (size - (initials_bbox[3] - initials_bbox[1])) // 2
            
            draw.text((initials_x, initials_y), initials, 
                     font=font, fill=(255, 255, 255))
            
            return avatar
            
        except Exception as e:
            logger.error(f"[Case] Error creating avatar placeholder: {e}")
            return Image.new('RGB', (size, size), (100, 150, 255))

    def _get_simple_case_icon(self, case_price, size):
        try:
            icon_path = self.get_asset_path("case", "icons", f"case_{case_price}_icon.png")
            
            if os.path.exists(icon_path):
                icon = Image.open(icon_path).convert('RGBA')
                icon = icon.resize((size, size), Image.Resampling.LANCZOS)
                return icon
            
            color_map = {
                10: (100, 150, 255),
                100: (180, 120, 255),
                1000: (255, 200, 50)
            }
            
            color = color_map.get(case_price, (100, 150, 255))
            
            icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(icon)
            
            border = 5
            draw.rectangle([border, border, size-border-1, size-border-1], 
                          fill=color, outline=(255, 255, 255), width=2)
            
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", size // 3)
            except:
                font = ImageFont.load_default()
            
            dollar_text = f"${case_price}"
            bbox = draw.textbbox((0, 0), dollar_text, font=font)
            text_x = (size - (bbox[2] - bbox[0])) // 2
            text_y = (size - (bbox[3] - bbox[1])) // 2
            
            draw.text((text_x+1, text_y+1), dollar_text, font=font, fill=(0, 0, 0))
            draw.text((text_x, text_y), dollar_text, font=font, fill=(255, 255, 255))
            
            return icon
            
        except Exception as e:
            logger.error(f"[Case] Error creating case icon: {e}")
            return None
    
    def _handle_case_battle_list(self, sender, file_queue, cache, user_id):
        active_battles = self.battle_manager.get_active_battles()
        
        if not active_battles:
            self.send_message_image(
                sender, file_queue,
                "No active case battles available.\n\n" \
                "Create one with: /case battle start <price>",
                "Case Battle - No Battles", cache, user_id
            )
            return ""
        
        user_background_path = None
        if user_id and cache:
            user_background_path = cache.get_background_path(user_id)
            if not os.path.exists(user_background_path):
                user_background_path = None
        
        list_image_path = self._generate_battle_list_image(active_battles, user_id, user_background_path)
        
        if list_image_path and os.path.exists(list_image_path):
            file_queue.put(list_image_path)
            
            if len(active_battles) == 1:
                battle = active_battles[0]
                return f"Found 1 active battle! Check the image for details.\nTo accept: /case battle accept {battle.get('id')}"
            else:
                return f"Found {len(active_battles)} active battles! Check the image for details."
        else:
            logger.warning("[Case] Failed to generate battle list image, falling back to text")
            
            message_lines = [""]
            for battle in active_battles:
                message_lines.append(f"Battle #{battle.get('id', '?')}")
                message_lines.append(f"Created by: {battle.get('creator_name', 'Unknown')}")
                message_lines.append(f"Case price: ${battle.get('case_price', 0)}")
                message_lines.append(f"Accept with: /case battle accept {battle.get('id', '?')}")
                message_lines.append("")
            
            message_lines.append("To accept a battle:")
            message_lines.append("/case battle accept <battle_number>")
            message_lines.append("")
            message_lines.append("Cancel your battle:")
            message_lines.append("/case battle cancel <battle_number>")
            
            message = "\n".join(message_lines)
            
            self.send_message_image(
                sender, file_queue, message, "Case Battle - Active List", cache, user_id
            )
            return ""
        
    def _handle_case_battle_cancel(self, args, sender, file_queue, cache, user_id):
        if len(args) < 1:
            user_battles = self.battle_manager.get_user_battles(user_id)
            
            if not user_battles:
                self.send_message_image(
                    sender, file_queue,
                    "You have no active battles to cancel.\n\n" \
                    "Create one with: /case battle start <price>",
                    "Case Battle - Cancel", cache, user_id
                )
                return ""
            
            message_lines = ["YOUR ACTIVE BATTLES:", ""]
            
            for battle in user_battles:
                message_lines.append(f"Battle #{battle.get('id', '?')}")
                message_lines.append(f"Price: ${battle.get('case_price', 0)}")
                message_lines.append(f"Cancel with: /case battle cancel {battle.get('id', '?')}")
                message_lines.append("")
            
            message = "\n".join(message_lines)
            
            self.send_message_image(
                sender, file_queue, message, "Case Battle - Your Battles", cache, user_id
            )
            return ""
        
        try:
            battle_id = int(args[0])
        except ValueError:
            self.send_message_image(
                sender, file_queue,
                "Invalid battle number!\n\n" \
                "Usage: /case battle cancel <number>",
                "Case Battle - Error", cache, user_id
            )
            return ""
        
        battle = self.battle_manager.get_battle(battle_id)
        if not battle:
            self.send_message_image(
                sender, file_queue,
                f"Battle #{battle_id} not found!",
                "Case Battle - Error", cache, user_id
            )
            return ""
        
        success, message = self.battle_manager.cancel_battle(battle_id, user_id)
        
        if success:
            creator_user = cache.get_user(user_id)
            if creator_user:
                refund_amount = battle.get('case_price', 0)
                new_balance = creator_user.get('balance', 0) + refund_amount
                self.update_user_balance(user_id, new_balance)
            
            self.send_message_image(
                sender, file_queue,
                f"Battle #{battle_id} cancelled successfully!\n" \
                f"Your ${battle.get('case_price', 0)} bet has been refunded.",
                "Case Battle - Cancelled", cache, user_id
            )
        else:
            self.send_message_image(
                sender, file_queue,
                f"Cannot cancel battle:\n{message}",
                "Case Battle - Error", cache, user_id
            )
        
        return ""
    
    def _handle_case_battle_start(self, args, sender, avatar_url, file_queue, cache):
        if len(args) < 1:
            self.send_message_image(
                sender, file_queue,
                "Invalid command!\n\n" \
                "Usage: /case battle start <price>\n" \
                "Prices: 10, 100, 1000",
                "Case Battle - Error", cache, None
            )
            return ""
        
        try:
            case_price = int(args[0])
        except ValueError:
            self.send_message_image(
                sender, file_queue,
                "Invalid case price!\n\n" \
                "Use: 10, 100, or 1000",
                "Case Battle - Error", cache, None
            )
            return ""
        
        if case_price not in self.case_prices:
            self.send_message_image(
                sender, file_queue,
                f"Invalid case price!\n\n" \
                f"Available prices:\n" \
                f"• $10 case\n" \
                f"• $100 case\n" \
                f"• $1000 case",
                "Case Battle - Error", cache, None
            )
            return ""
        
        from user_manager import UserManager
        user_manager = UserManager(cache)
        user_id, user = user_manager.find_user_by_name_avatar(sender, avatar_url)
        
        if not user:
            self.send_message_image(sender, file_queue, "Invalid user!", "Case Battle - Error", cache, None)
            return ""
        
        if user.get('balance', 0) < case_price:
            self.send_message_image(sender, file_queue, 
                f"Insufficient funds!\n\n" \
                f"Case price: ${case_price}\n" \
                f"Your balance: ${user.get('balance', 0)}",
                "Case Battle - Insufficient Funds", cache, user_id
            )
            return ""
        
        creator_balance_before = user.get('balance', 0)
        creator_new_balance = creator_balance_before - case_price
        self.update_user_balance(user_id, creator_new_balance)
        
        battle_id = self.battle_manager.create_battle(user_id, sender, case_price, file_queue, cache)
        
        return self._handle_case_battle_list(sender, file_queue, cache, user_id)
 
    def _handle_case_battle_accept(self, args, sender, avatar_url, file_queue, cache):
        """Handle /case battle accept <battle_id> command - ANIMOWANE WERSJA"""
        if len(args) < 1:
            self.send_message_image(
                sender, file_queue,
                "Invalid command!\n\n" \
                "Usage: /case battle accept <battle_number>\n\n" \
                "View available battles:\n" \
                "/case battle list",
                "Case Battle - Error", cache, None
            )
            return ""
        
        try:
            battle_id = int(args[0])
        except ValueError:
            self.send_message_image(
                sender, file_queue,
                "Invalid battle number!\n\n" \
                "Usage: /case battle accept <number>\n\n" \
                "View available battles:\n" \
                "/case battle list",
                "Case Battle - Error", cache, None
            )
            return ""
        
        from user_manager import UserManager
        user_manager = UserManager(cache)
        acceptor_id, acceptor_user = user_manager.find_user_by_name_avatar(sender, avatar_url)
        
        if not acceptor_user:
            self.send_message_image(sender, file_queue, "Invalid user!", "Case Battle - Error", cache, None)
            return ""
        
        battle = self.battle_manager.get_battle(battle_id)
        if not battle:
            self.send_message_image(
                sender, file_queue,
                f"Battle #{battle_id} not found!\n\n" \
                f"It may have been cancelled.\n\n" \
                f"View active battles:\n" \
                f"/case battle list",
                "Case Battle - Not Found", cache, acceptor_id
            )
            return ""
        
        if 'creator_id' not in battle or 'case_price' not in battle:
            logger.error(f"[Case] Battle #{battle_id} missing required fields: {battle}")
            self.send_message_image(
                sender, file_queue,
                f"Battle #{battle_id} has corrupted data. Please create a new battle.",
                "Case Battle - Error", cache, acceptor_id
            )
            return ""
        
        if battle.get('creator_id') == acceptor_id:
            self.send_message_image(
                sender, file_queue,
                "You cannot accept your own battle!",
                "Case Battle - Error", cache, acceptor_id
            )
            return ""
        
        case_price = battle.get('case_price', 0)
        if acceptor_user.get('balance', 0) < case_price:
            self.send_message_image(
                sender, file_queue,
                f"Insufficient funds to join battle!\n\n" \
                f"Required: ${case_price}\n" \
                f"Your balance: ${acceptor_user.get('balance', 0)}",
                "Case Battle - Insufficient Funds", cache, acceptor_id
            )
            return ""
        
        acceptor_balance_before = acceptor_user.get('balance', 0)
        acceptor_new_balance = acceptor_balance_before - case_price
        self.update_user_balance(acceptor_id, acceptor_new_balance)
        acceptor_user = cache.get_user(acceptor_id)
        
        creator_user_id = battle.get('creator_id')
        if not creator_user_id:
            logger.error(f"[Case] Battle #{battle_id} has no creator_id")
            self.update_user_balance(acceptor_id, acceptor_balance_before)
            self.send_message_image(
                sender, file_queue,
                "Battle data corrupted. Bet refunded.",
                "Case Battle - Error", cache, acceptor_id
            )
            return ""
        
        creator_user = cache.get_user(creator_user_id)
        
        if not creator_user:
            self.update_user_balance(acceptor_id, acceptor_balance_before)
            self.send_message_image(
                sender, file_queue,
                "Creator no longer exists. Battle cancelled and bet refunded.",
                "Case Battle - Error", cache, acceptor_id
            )
            return ""
        
        success, message = self.battle_manager.accept_battle(battle_id, acceptor_id, sender)
        
        if not success:
            self.update_user_balance(acceptor_id, acceptor_balance_before)
            logger.info(f"[Case] Refunded ${case_price} to {sender} after failed acceptance")
            
            self.send_message_image(
                sender, file_queue,
                f"Cannot accept battle:\n{message}",
                "Case Battle - Error", cache, acceptor_id
            )
            return ""
        
        creator_animation_path, creator_win = self.get_random_case_animation(case_price)
        acceptor_animation_path, acceptor_win = self.get_random_case_animation(case_price)
        
        success, completed_battle = self.battle_manager.complete_battle(battle_id, creator_win, acceptor_win)
        
        if not success:
            logger.error(f"[Case] Failed to complete battle #{battle_id}: {completed_battle}")
            self.update_user_balance(creator_user_id, creator_user.get('balance', 0))
            self.update_user_balance(acceptor_id, acceptor_balance_before)
            
            self.send_message_image(
                sender, file_queue,
                "Error completing battle. Bets refunded.",
                "Case Battle - Error", cache, acceptor_id
            )
            return ""
        
        battle = completed_battle
        
        total_pot = creator_win + acceptor_win
        
        creator_current_balance = creator_user.get('balance', 0)
        acceptor_current_balance = acceptor_user.get('balance', 0)
        
        battle_result = battle.get('result')
        
        if battle_result == 'creator_wins':
            creator_final_balance = creator_current_balance + total_pot
            acceptor_final_balance = acceptor_current_balance
        
        elif battle_result == 'acceptor_wins':
            creator_final_balance = creator_current_balance
            acceptor_final_balance = acceptor_current_balance + total_pot
        
        else:
            creator_final_balance = creator_current_balance + creator_win
            acceptor_final_balance = acceptor_current_balance + acceptor_win
        
        self.update_user_balance(creator_user_id, creator_final_balance)
        self.update_user_balance(acceptor_id, acceptor_final_balance)
        
        try:
            creator_exp_amount = creator_win - case_price
            acceptor_exp_amount = acceptor_win - case_price
            
            self.cache.add_experience(creator_user_id, creator_exp_amount, battle.get('creator_name'), file_queue)
            self.cache.add_experience(acceptor_id, acceptor_exp_amount, sender, file_queue)
                        
        except Exception as e:
            logger.error(f"[Case] Error adding experience: {e}")
        
        creator_net_win = creator_final_balance - creator_current_balance
        acceptor_net_win = acceptor_final_balance - acceptor_current_balance
        
        creator_user_info_before = self._create_battle_user_info_before(
            battle.get('creator_name'), 
            case_price, 
            creator_current_balance,
            creator_user
        )
        
        creator_user_info_after = self._create_battle_user_info_after(
            battle.get('creator_name'), 
            case_price, 
            creator_net_win,
            creator_final_balance,
            creator_user
        )
        
        acceptor_user_info_before = self._create_battle_user_info_before(
            sender, 
            case_price, 
            acceptor_current_balance,
            acceptor_user
        )
        
        acceptor_user_info_after = self._create_battle_user_info_after(
            sender, 
            case_price, 
            acceptor_net_win,
            acceptor_final_balance,
            acceptor_user
        )
        
        creator_anim_result, creator_anim_error = self.generate_animation(
            base_animation_path=creator_animation_path,
            user_id=creator_user_id,
            user=creator_user,
            user_info_before=creator_user_info_before,
            user_info_after=creator_user_info_after,
            animated=True,
            frame_duration=70,
            last_frame_multiplier=30,
            show_win_text=False,
            font_scale=0.8,
            avatar_size=75,
            show_bet_amount=True
        )
        
        acceptor_anim_result, acceptor_anim_error = self.generate_animation(
            base_animation_path=acceptor_animation_path,
            user_id=acceptor_id,
            user=acceptor_user,
            user_info_before=acceptor_user_info_before,
            user_info_after=acceptor_user_info_after,
            animated=True,
            frame_duration=70,
            last_frame_multiplier=30,
            show_win_text=False,
            font_scale=0.8,
            avatar_size=75,
            show_bet_amount=True
        )
        
        logger.info(f"[Case] Animation generation results - Creator: {'Success' if creator_anim_result else 'Failed'}, Acceptor: {'Success' if acceptor_anim_result else 'Failed'}")
        if creator_anim_error:
            logger.error(f"[Case] Creator animation error: {creator_anim_error}")
        if acceptor_anim_error:
            logger.error(f"[Case] Acceptor animation error: {acceptor_anim_error}")
        
        if creator_anim_result and acceptor_anim_result and not creator_anim_error and not acceptor_anim_error:
            combined_path, combine_error = self._combine_two_animations(
                creator_anim_result,
                acceptor_anim_result,
                battle_id
            )
            
            if combined_path and not combine_error:
                file_queue.put(combined_path)                
                return "Animation created successfully"
                
            elif combine_error:
                logger.error(f"[Case] Error combining animations: {combine_error}")
                if creator_anim_result:
                    file_queue.put(creator_anim_result)
                if acceptor_anim_result:
                    file_queue.put(acceptor_anim_result)
        else:
            logger.error(f"[Case] Couldn't generate or combine animations. Creator: {creator_anim_error}, Acceptor: {acceptor_anim_error}")
            if creator_anim_result and not creator_anim_error:
                file_queue.put(creator_anim_result)
            if acceptor_anim_result and not acceptor_anim_error:
                file_queue.put(acceptor_anim_result)
        
        return "Animation creation failed"

    def _handle_case_battle_help(self, sender, file_queue, cache, user_id):
        """Show case battle help"""
        message = (
            "🎮 CASE BATTLE SYSTEM 🎮\n\n"
            "Commands:\n"
            "• /case battle list - Show active battles\n"
            "• /case battle start <price> - Create battle\n"
            "• /case battle accept <id> - Join battle\n"
            "• /case battle cancel <id> - Cancel your battle\n\n"
            "How it works:\n"
            "1. Create battle with /case battle start\n"
            "2. Others accept with /case battle accept\n"
            "3. Both open same value case\n"
            "4. Player with HIGHER case win takes BOTH wins!\n"
            "5. Loser gets NOTHING (loses only the bet)\n"
            "6. Draw = Each keeps their own win\n\n"
            "Winner takes ALL (sum of both wins)!\n"
            "Available prices: $10, $100, $1000"
        )
        
        self.send_message_image(
            sender, file_queue, message, "Case Battle - Help", cache, user_id
        )
        return ""
    
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        if len(args) >= 1 and (args[0].lower() == "battle" or args[0].lower() == "b"):
            battle_subargs = args[1:] if len(args) > 1 else []
            
            from user_manager import UserManager
            user_manager = UserManager(cache)
            user_id, user = user_manager.find_user_by_name_avatar(sender, avatar_url)
            user_id = user_id if user_id else sender
            
            if len(battle_subargs) == 0:
                return self._handle_case_battle_help(sender, file_queue, cache, user_id)
            
            battle_subcommand = battle_subargs[0].lower()
            
            if battle_subcommand == "list" or battle_subcommand == "l":
                return self._handle_case_battle_list(sender, file_queue, cache, user_id)
            
            elif battle_subcommand == "start" or battle_subcommand == "create" or battle_subcommand == "s":
                return self._handle_case_battle_start(battle_subargs[1:], sender, avatar_url, file_queue, cache)
            
            elif battle_subcommand == "accept" or battle_subcommand == "a":
                return self._handle_case_battle_accept(battle_subargs[1:], sender, avatar_url, file_queue, cache)
            
            elif battle_subcommand == "cancel" or battle_subcommand == "c":
                return self._handle_case_battle_cancel(battle_subargs[1:], sender, file_queue, cache, user_id)
            
            elif battle_subcommand == "help":
                return self._handle_case_battle_help(sender, file_queue, cache, user_id)
            
            else:
                self.send_message_image(
                    sender, file_queue,
                    "Unknown case battle command!\n\n" \
                    "Use:\n" \
                    "• /case battle list\n" \
                    "• /case battle start <price>\n" \
                    "• /case battle accept <id>\n" \
                    "• /case battle cancel <id>",
                    "Case Battle - Error", cache, user_id
                )
                return ""
        
        animated = True
        if len(args) >= 1 and args[-1].lower() == "x":
            animated = False
            args = args[:-1]

        if len(args) == 0:
            self.send_message_image(sender, file_queue, 
                                  "🎮 CASE GAME 🎮\n\n" \
                                  "Single Player:\n" \
                                  "/case 10 - $10 case\n" \
                                  "/case 100 - $100 case\n" \
                                  "/case 1000 - $1000 case\n\n" \
                                  "Case Battle (PVP):\n" \
                                  "/case battle help",
                                  "Case Game", cache, None)
            return ""
        
        try:
            case_price = int(args[0])
        except ValueError:
            self.send_message_image(sender, file_queue, 
                                  "Invalid case price!\n\n" \
                                  "Use: /case 10, /case 100, or /case 1000",
                                  "Case - Error", cache, None)
            return ""
        
        if case_price not in self.case_prices:
            self.send_message_image(sender, file_queue, 
                                  f"Invalid case price!\n\n" \
                                  f"Available cases:\n" \
                                  f"• $10 case\n" \
                                  f"• $100 case\n" \
                                  f"• $1000 case",
                                  "Case - Error", cache, None)
            return ""
        
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, case_price)
        if error == "Invalid user":
            self.send_message_image(sender, file_queue, "Invalid user!", "Case - Validation Error", cache, user_id)
            return ""
        elif error:
            self.send_message_image(sender, file_queue, 
                                  f"Insufficient funds!\n\n" \
                                  f"Case price: ${case_price}\n" \
                                  f"Your balance: ${user.get('balance', 0) if user else 0}",
                                  "Case - Insufficient Funds", cache, user_id)
            return ""

        balance_before = user.get("balance", 0)
        
        animation_path, win_amount = self.get_random_case_animation(case_price)
        
        if not animation_path:
            self.send_message_image(sender, file_queue, 
                                  f"Error loading case animations!\n\n" \
                                  f"Please try again later.",
                                  "Case - Error", cache, user_id)
            return ""
        
        final_win = win_amount
        net_win = final_win - case_price
        new_balance = balance_before - case_price + final_win
        
        try:
            self.update_user_balance(user_id, new_balance)
        except Exception as e:
            logger.error(f"[Case] Error updating balance for user {user_id}: {e}")
            self.send_message_image(sender, file_queue, 
                                  "Error updating balance!",
                                  "Case - System Error", cache, user_id)
            return ""

        user_info_before = self.create_user_info(sender, case_price, 0, balance_before, user)
        
        try:
            newLevel, newLevelProgress = self.cache.add_experience(user_id, win_amount - case_price + final_win, sender, file_queue)
        except Exception as e:
            logger.error(f"[Case] Error adding experience: {e}")
            newLevel = user.get("level", 1)
            newLevelProgress = user.get("level_progress", 0.1)

        user["level"] = newLevel
        user["level_progress"] = newLevelProgress
        user_info_after = self.create_user_info(sender, case_price, net_win, new_balance, user)
        
        result_path, error = self.generate_animation(
            animation_path, user_id, user, user_info_before, user_info_after, 
            animated=animated,
            frame_duration=70,
            show_win_text=False,
            last_frame_multiplier=30
        )
        
        if error:
            logger.error(f"[Case] Animation error: {error}")
            self.send_message_image(sender, file_queue, 
                                  f"Error generating animation!\n\n{error}",
                                  "Case - Animation Error", cache, user_id)
            return ""
        
        file_queue.put(result_path)
        
        if net_win > 0:
            result_status = f"WIN +${net_win}"
        elif net_win < 0:
            result_status = f"LOSE -${abs(net_win)}"
        else:
            result_status = "BREAK EVEN"
        
        logger.info(f"[Case] CASE: {sender} opened ${case_price} case | Win: ${win_amount} | Net: {result_status}")
        
        return ""

def register():
    plugin = CasePlugin()
    logger.info("[Case] Case plugin registered")
    return {
        "name": "case",
        "description": "Open mystery cases: /case 10, /case 100, /case 1000\nCase Battle PVP: /case battle help",
        "aliases": ["/cs"],
        "execute": plugin.execute_game
    }