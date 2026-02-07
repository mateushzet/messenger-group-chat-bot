import os
import time
import random
import threading
from datetime import datetime
from base_game_plugin import BaseGamePlugin
from logger import logger
from PIL import Image, ImageDraw

class JackpotGame:
    def __init__(self, plugin_instance):
        self.active_jackpot = None
        self.plugin = plugin_instance
        self.draw_timer = None
        self.draw_lock = threading.Lock()
        
    def _load_from_cache(self):
        try:
            if self.plugin.cache:
                saved_jackpot = self.plugin.cache.get_setting("active_jackpot", None)
                if saved_jackpot:
                    status = saved_jackpot.get('status', 'waiting')
                    draw_time = saved_jackpot.get('draw_time')
                    current_time = time.time()
                    
                    if status == 'counting_down' and draw_time and draw_time > current_time:
                        self.active_jackpot = saved_jackpot
                        time_remaining = draw_time - current_time
                        self._start_draw_timer(time_remaining)
                        logger.info(f"[Jackpot] Restarted jackpot timer: {time_remaining:.0f}s remaining")
                        
                    elif status == 'waiting':
                        self.active_jackpot = saved_jackpot
                        logger.info(f"[Jackpot] Restored waiting jackpot with {len(saved_jackpot.get('players', []))} player(s)")
                        
                    else:
                        self._force_complete_jackpot(saved_jackpot)
                        
        except Exception as e:
            logger.error(f"[Jackpot] Error loading jackpot from cache: {e}")

    def _start_draw_timer(self, seconds):
        with self.draw_lock:
            if self.draw_timer and self.draw_timer.is_alive():
                self.draw_timer.cancel()
            
            self.draw_timer = threading.Timer(seconds, self._draw_jackpot)
            self.draw_timer.daemon = True
            self.draw_timer.start()
            logger.info(f"[Jackpot] Jackpot timer started: {seconds:.0f} seconds")
        
    def _draw_jackpot(self):
        try:
            with self.draw_lock:
                if not self.active_jackpot or len(self.active_jackpot.get('players', [])) < 2:
                    logger.warning("[Jackpot] No valid jackpot to draw")
                    return
                
                logger.info("[Jackpot] JACKPOT DRAW TIME!")
                
                players = self.active_jackpot['players']
                total_pot = self.active_jackpot['total_pot']
                
                bets = [p['bet_amount'] for p in players]
                total_bets = sum(bets)
                random_point = random.uniform(0, total_bets)
                
                current_sum = 0
                winner = None
                for player in players:
                    current_sum += player['bet_amount']
                    if random_point <= current_sum:
                        winner = player
                        break
                
                if not winner:
                    winner = players[-1]
                
                jackpot_result = {
                    'jackpot_id': self.active_jackpot['id'],
                    'winner': winner,
                    'total_pot': total_pot,
                    'all_players': players,
                    'drawn_at': time.time()
                }
                
                winner_id = winner.get('user_id')
                if winner_id and self.plugin.cache:
                    winner_user = self.plugin.cache.get_user(winner_id)
                    if winner_user:
                        new_balance = winner_user.get('balance', 0) + total_pot
                        self.plugin.update_user_balance(winner_id, new_balance)
                        
                        logger.info(f"[Jackpot] {winner.get('username')} won ${total_pot}!")

                for player in players:
                    player_id = player.get('user_id')
                    player_bet = player.get('bet_amount', 0)
                    
                    if player_id == winner_id:
                        player_net = total_pot - player_bet
                    else:
                        player_net = -player_bet
                    
                    self.plugin.cache.add_experience(
                        player_id,
                        player_net,
                        player.get('username'),
                        self.plugin.file_queue
                    )
                
                anim_path, error = self.plugin._create_winner_animation(jackpot_result)
                if anim_path and not error and self.plugin.file_queue:
                    self.plugin.file_queue.put(anim_path)
                    logger.info(f"[Jackpot] Jackpot animation sent: {anim_path}")
                
                self.active_jackpot = None
                self._save_to_cache()
                
                logger.info("[Jackpot] Jackpot draw completed successfully!")
                    
        except Exception as e:
            logger.error(f"[Jackpot] Error drawing jackpot: {e}")

    def _extend_draw_time(self, minutes=1):
        if not self.active_jackpot or not self.active_jackpot.get('draw_time'):
            return False
        
        current_time = time.time()
        new_draw_time = self.active_jackpot['draw_time'] + (minutes * 60)
        self.active_jackpot['draw_time'] = new_draw_time
        self.active_jackpot['last_extend_time'] = current_time
        
        time_remaining = new_draw_time - current_time
        self._start_draw_timer(time_remaining)
        
        logger.info(f"[Jackpot] Jackpot extended by {minutes} minute(s). New draw time: {datetime.fromtimestamp(new_draw_time)}")
        return True

    def create_or_join_jackpot(self, user_id, username, bet_amount):
        current_time = time.time()
        
        if not self.active_jackpot:
            self.active_jackpot = {
                'id': int(current_time * 1000),
                'players': [],
                'total_pot': 0,
                'draw_time': None,
                'created_at': current_time,
                'last_extend_time': current_time,
                'status': 'waiting'
            }
        
        existing_player = None
        for player in self.active_jackpot.get('players', []):
            if player.get('user_id') == user_id:
                existing_player = player
                break
        
        if existing_player:
            existing_player['bet_amount'] += bet_amount
        else:
            player_entry = {
                'user_id': user_id,
                'username': username,
                'bet_amount': bet_amount,
                'joined_at': current_time
            }
            self.active_jackpot['players'].append(player_entry)
        
        self.active_jackpot['total_pot'] += bet_amount
        
        player_count = len(self.active_jackpot['players'])
        
        if player_count == 2 and self.active_jackpot['status'] == 'waiting':
            draw_time = current_time + 600
            self.active_jackpot['draw_time'] = draw_time
            self.active_jackpot['status'] = 'counting_down'
            
            self._start_draw_timer(600)
        
        elif player_count >= 2 and self.active_jackpot['status'] == 'counting_down':
            time_remaining = self.active_jackpot['draw_time'] - current_time
            if time_remaining < 30:
                self._extend_draw_time(1)
        
        self._save_to_cache()
        
        if existing_player:
            return True, "Increased your bet successfully!"
        else:
            return True, "Joined jackpot successfully!"

    def get_jackpot_info(self):
        if not self.active_jackpot:
            return None
        
        info = self.active_jackpot.copy()
        current_time = time.time()
        
        total_pot = info['total_pot']
        for player in info['players']:
            player['percentage'] = (player['bet_amount'] / total_pot * 100) if total_pot > 0 else 0
        
        if info.get('draw_time') and info.get('status') == 'counting_down':
            actual_time_remaining = max(0, info['draw_time'] - current_time)
            info['time_remaining'] = actual_time_remaining
            
            last_extend_time = info.get('last_extend_time', 0)
            seconds_since_last_extend = current_time - last_extend_time
            
            if seconds_since_last_extend < 60 and actual_time_remaining < 60:
                time_before_extension = actual_time_remaining - 60
                
                if time_before_extension > 0:
                    minutes_base = int(time_before_extension // 60)
                    seconds_base = int(time_before_extension % 60)
                    
                    info['time_remaining_formatted'] = f"{minutes_base:01d}:{seconds_base:02d} +1:00"
                    info['show_extension'] = True
                else:
                    minutes = int(actual_time_remaining // 60)
                    seconds = int(actual_time_remaining % 60)
                    info['time_remaining_formatted'] = f"{minutes:01d}:{seconds:02d}"
                    info['show_extension'] = False
            else:
                minutes = int(actual_time_remaining // 60)
                seconds = int(actual_time_remaining % 60)
                info['time_remaining_formatted'] = f"{minutes:01d}:{seconds:02d}"
                info['show_extension'] = False
        else:
            info['time_remaining'] = None
            info['time_remaining_formatted'] = "Waiting..."
            info['show_extension'] = False
        
        return info

    def _save_to_cache(self):
        try:
            if self.plugin.cache:
                self.plugin.cache.set_setting("active_jackpot", self.active_jackpot)
        except Exception as e:
            logger.error(f"[Jackpot] Error saving jackpot: {e}")

    def _force_complete_jackpot(self, jackpot):
        try:
            status = jackpot.get('status', 'waiting')
            
            if status == 'waiting' and len(jackpot.get('players', [])) == 1:
                self.active_jackpot = jackpot
                return
            
            if jackpot and len(jackpot.get('players', [])) >= 2:
                self.active_jackpot = jackpot
                self._draw_jackpot()
        except Exception as e:
            logger.error(f"[Jackpot] Error forcing completion: {e}")


class JackpotPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="jackpot"
        )
        self.jackpot_manager = JackpotGame(self)
        self.file_queue = None
        self._initialized = False
        
        self.colors = {
            'gold': (255, 215, 0),
            'red': (255, 50, 50),
            'green': (0, 255, 100),
            'orange': (255, 165, 0),
            'yellow': (255, 200, 0),
            'white': (240, 240, 240),
            'light_gray': (180, 180, 200),
            'dark_gray': (60, 65, 75),
            'bg_dark': (20, 25, 35),
            'bg_medium': (25, 30, 40),
            'bg_light': (30, 35, 45),
        }
        
        logger.info("[Jackpot] JackpotPlugin initialized with threading")
    
    def set_file_queue(self, file_queue):
        self.file_queue = file_queue

    def initialize_with_cache(self):
        if self.cache:
            self.jackpot_manager._load_from_cache()
            self._initialized = True
            logger.info("[Jackpot] Jackpot initialized with cache")
                
    def _create_jackpot_info_image(self, jackpot_info, user_id=None):
        try:
            width = 700
            avatar_size = 50
            player_height = 70
            margin = 25
            section_spacing = 15
            
            player_count = len(jackpot_info.get('players', []))
            header_height = 190
            players_height = player_count * player_height
            footer_height = 70
            total_height = header_height + players_height + footer_height + section_spacing * 3 - 40
            
            img = Image.new('RGB', (width, total_height), color=self.colors['bg_dark'])
            draw = ImageDraw.Draw(img)
            
            title_text = self.text_renderer.render_text(
                text="JACKPOT",
                font_size=32,
                color=self.colors['gold'],
                stroke_width=2,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_offset=(2, 2)
            )
            
            title_x = (width - title_text.width) // 2
            img.paste(title_text, (title_x, 40), title_text)
            
            draw.line([(margin, 80), (width - margin, 80)], 
                    fill=self.colors['dark_gray'], width=2)
            
            y_pos = 100
            col1_x = margin
            col2_x = width // 2 + margin
            
            total_pot = jackpot_info.get('total_pot', 0)
            time_text = jackpot_info.get('time_remaining_formatted', 'Waiting...')
            status = jackpot_info.get('status', 'waiting')
            
            pot_label = self.text_renderer.render_text(
                text="Total Pot:",
                font_size=22,
                color=self.colors['light_gray']
            )
            img.paste(pot_label, (col1_x, y_pos), pot_label)
            
            pot_value = self.text_renderer.render_text(
                text=f"${total_pot}",
                font_size=26,
                color=self.colors['white'],
                stroke_width=1,
                stroke_color=(0, 0, 0, 255)
            )
            img.paste(pot_value, (col1_x, y_pos + 30), pot_value)
            
            if status == 'counting_down':
                time_label = self.text_renderer.render_text(
                    text="Time Left:",
                    font_size=22,
                    color=self.colors['light_gray']
                )
                img.paste(time_label, (col2_x, y_pos), time_label)
                
                show_extension = jackpot_info.get('show_extension', False)
                time_seconds = jackpot_info.get('time_remaining', 0)
                
                if show_extension and ' +' in time_text:
                    base_time, extension = time_text.split(' +')
                    
                    base_time_img = self.text_renderer.render_text(
                        text=base_time,
                        font_size=28,
                        color=self.colors['red'],
                        stroke_width=2,
                        stroke_color=(0, 0, 0, 255)
                    )
                    img.paste(base_time_img, (col2_x, y_pos + 30), base_time_img)
                    
                    extension_img = self.text_renderer.render_text(
                        text=f"+{extension}",
                        font_size=28,
                        color=self.colors['green'],
                        stroke_width=2,
                        stroke_color=(0, 0, 0, 255)
                    )
                    extension_x = col2_x + base_time_img.width + 5
                    img.paste(extension_img, (extension_x, y_pos + 30), extension_img)
                else:
                    if time_seconds > 300:
                        time_color = self.colors['green']
                    elif time_seconds > 60:
                        time_color = self.colors['yellow']
                    else:
                        time_color = self.colors['red']
                    
                    time_display = time_text
                    if ':' in time_text and time_text.startswith('0'):
                        minutes, seconds = time_text.split(':')
                        try:
                            if int(minutes) == 0:
                                time_display = f"00:{seconds}"
                        except:
                            pass
                    
                    time_value = self.text_renderer.render_text(
                        text=time_display,
                        font_size=28,
                        color=time_color,
                        stroke_width=2,
                        stroke_color=(0, 0, 0, 255)
                    )
                    img.paste(time_value, (col2_x, y_pos + 30), time_value)
            else:
                status_label = self.text_renderer.render_text(
                    text="Status:",
                    font_size=22,
                    color=self.colors['light_gray']
                )
                img.paste(status_label, (col2_x, y_pos), status_label)
                
                if player_count < 2:
                    status_text = f"Waiting ({player_count}/2)"
                    status_color = self.colors['orange']
                else:
                    status_text = "Ready!"
                    status_color = self.colors['green']
                
                status_value = self.text_renderer.render_text(
                    text=status_text,
                    font_size=26,
                    color=status_color,
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                img.paste(status_value, (col2_x, y_pos + 30), status_value)
            
            draw.line([(width // 2, 100), (width // 2, 160)], 
                    fill=self.colors['dark_gray'], width=1)
            
            players_y = header_height + section_spacing
            draw.rectangle([margin, players_y, width - margin, 
                        players_y + players_height + 45], 
                        fill=self.colors['bg_medium'], 
                        outline=self.colors['dark_gray'], 
                        width=2)
            
            players_sorted = sorted(jackpot_info.get('players', []), 
                                  key=lambda x: x.get('bet_amount', 0), 
                                  reverse=True)
            
            y_pos = players_y + 40
            
            for i, player in enumerate(players_sorted):
                username = player.get('username', 'Unknown')
                bet_amount = player.get('bet_amount', 0)
                percentage = player.get('percentage', 0)
                player_user_id = player.get('user_id')
                
                avatar_x = margin + 10
                avatar_y = y_pos - 10
                
                try:
                    if player_user_id and self.cache:
                        avatar_path = self.cache.get_avatar_path(player_user_id)
                        if avatar_path and os.path.exists(avatar_path):
                            avatar_img = Image.open(avatar_path).convert('RGBA')
                            avatar_img = avatar_img.resize((avatar_size, avatar_size))
                            
                            mask = Image.new('L', (avatar_size, avatar_size), 0)
                            mask_draw = ImageDraw.Draw(mask)
                            mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                            avatar_img.putalpha(mask)
                            
                            border_color = self.colors['dark_gray']
                            if player_user_id == user_id:
                                border_color = self.colors['gold']
                            
                            border_img = Image.new('RGBA', (avatar_size + 4, avatar_size + 4), (0, 0, 0, 0))
                            border_draw = ImageDraw.Draw(border_img)
                            border_draw.ellipse((0, 0, avatar_size + 4, avatar_size + 4), 
                                            fill=border_color)
                            border_img.paste(avatar_img, (2, 2), avatar_img)
                            
                            img.paste(border_img, (avatar_x, avatar_y), border_img)
                except Exception as e:
                    logger.debug(f"[Jackpot] Error loading avatar: {e}")
                    placeholder_color = self.colors['dark_gray']
                    if player_user_id == user_id:
                        placeholder_color = self.colors['gold']
                    
                    draw.ellipse([avatar_x + 2, avatar_y + 2, 
                                avatar_x + avatar_size + 2, avatar_y + avatar_size + 2], 
                            fill=placeholder_color)
                
                text_x = avatar_x + avatar_size + 15
                
                display_name = username
                if len(username) > 15:
                    display_name = username[:15] + "..."
                
                name_color = self.colors['white']
                if player_user_id == user_id:
                    name_color = self.colors['gold']
                
                name_img = self.text_renderer.render_text(
                    text=display_name,
                    font_size=20,
                    color=name_color,
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 150)
                )
                img.paste(name_img, (text_x, y_pos - 10), name_img)
                
                chance_text = f"${bet_amount} ({percentage:.1f}%)"
                chance_img = self.text_renderer.render_text(
                    text=chance_text,
                    font_size=18,
                    color=self.colors['light_gray']
                )
                img.paste(chance_img, (text_x, y_pos + 20), chance_img)
                
                if user_id and player_user_id == user_id:
                    indicator_img = self.text_renderer.render_text(
                        text="▶",
                        font_size=20,
                        color=self.colors['gold']
                    )
                    indicator_x = width - margin - 670
                    img.paste(indicator_img, (indicator_x, y_pos + 5), indicator_img)
                
                y_pos += player_height
            
            footer_y = header_height + players_height + section_spacing * 2
            
            instruction_img = self.text_renderer.render_text(
                text="Join: /jackpot bet <amount>",
                font_size=18,
                color=(150, 200, 255)
            )
            instruction_x = (width - instruction_img.width) // 2
            img.paste(instruction_img, (instruction_x, footer_y + 50), instruction_img)
            
            if status == 'counting_down':
                time_seconds = jackpot_info.get('time_remaining', 0)
            
            temp_dir = self.get_app_path("temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            timestamp = int(time.time() * 1000)
            filename = f"jackpot_info_{timestamp}.png"
            if user_id:
                filename = f"jackpot_info_{user_id}_{timestamp}.png"
            
            output_path = os.path.join(temp_dir, filename)
            img.save(output_path, format='PNG', optimize=True, quality=95)
            
            return output_path, None
            
        except Exception as e:
            logger.error(f"[Jackpot] Error creating jackpot info image: {e}")
            return None, str(e)

    def _create_winner_animation(self, jackpot_result):
        return self._create_jackpot_animation(jackpot_result)

    def _create_no_jackpot_image(self):
        try:
            width, height = 500, 250
            img = Image.new('RGB', (width, height), color=self.colors['bg_dark'])
            
            title_img = self.text_renderer.render_text(
                text="NO ACTIVE JACKPOT",
                font_size=28,
                color=self.colors['gold'],
                stroke_width=2,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_offset=(2, 2)
            )
            title_x = (width - title_img.width) // 2
            img.paste(title_img, (title_x, 80), title_img)
            
            message_img = self.text_renderer.render_text(
                text="Be the first to join!",
                font_size=20,
                color=self.colors['white']
            )
            message_x = (width - message_img.width) // 2
            img.paste(message_img, (message_x, 130), message_img)
            
            instruction_img = self.text_renderer.render_text(
                text="/jackpot bet <amount>",
                font_size=18,
                color=(150, 200, 255)
            )
            instruction_x = (width - instruction_img.width) // 2
            img.paste(instruction_img, (instruction_x, 170), instruction_img)
            
            temp_dir = self.get_app_path("temp")
            path = os.path.join(temp_dir, f"no_jackpot_{int(time.time()*1000)}.png")
            img.save(path, format='PNG', optimize=True, quality=95)
            return path, None
            
        except Exception as e:
            logger.error(f"[Jackpot] Error creating no jackpot image: {e}")
            return None, str(e)
    
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        self.file_queue = file_queue
        
        if not self._initialized and cache:
            logger.info("[Jackpot] First execution - initializing jackpot with cache")
            self.initialize_with_cache()
        
        if len(args) == 0 or args[0].lower() == "info":
            return self._handle_jackpot_info(sender, file_queue, cache, avatar_url)
        
        elif args[0].lower() == "bet":
            if len(args) < 2:
                self.send_message_image(sender, file_queue,
                    "Usage: /jackpot bet <amount>\n\n"
                    "Example: /jackpot bet 100\n"
                    "Minimum bet: $1\n"
                    "Only whole dollars allowed (no cents)",
                    "Jackpot - Error", cache, None)
                return ""
            
            try:
                bet_amount = float(args[1])
                
                if not bet_amount.is_integer():
                    self.send_message_image(sender, file_queue,
                        "Only whole dollars allowed! No cents.\n\n"
                        f"Your bet: ${bet_amount}\n"
                        "Please use whole numbers like: 1, 5, 10, 100",
                        "Jackpot - Error", cache, None)
                    return ""
                
                bet_amount = int(bet_amount)
                
                if bet_amount < 1:
                    self.send_message_image(sender, file_queue,
                        "Minimum bet is $1!",
                        "Jackpot - Error", cache, None)
                    return ""
            except ValueError:
                self.send_message_image(sender, file_queue,
                    "Invalid bet amount! Use whole numbers only.",
                    "Jackpot - Error", cache, None)
                return ""
            
            return self._handle_jackpot_bet(sender, avatar_url, bet_amount, file_queue, cache)
        
        else:
            help_text = (
                "**JACKPOT COMMANDS**\n\n"
                "/jackpot - Show current jackpot\n"
                "/jackpot bet <amount> - Join jackpot\n"
                "/jackpot help - Detailed info\n\n"
                "**Rules:**\n"
                "• Min 2 players to start\n"
                "• 10 minute countdown\n"
                "• Join in last 30s = +1 minute\n"
                "• Bigger bet = better chances!"
            )
            self.send_message_image(sender, file_queue, help_text, 
                                  "Jackpot - Help", cache, None)
            return ""
    
    def _handle_jackpot_info(self, sender, file_queue, cache, avatar_url=None):
        jackpot_info = self.jackpot_manager.get_jackpot_info()
        
        if not jackpot_info:
            img_path, error = self._create_no_jackpot_image()
            if img_path and not error:
                file_queue.put(img_path)
            return ""
        
        user_manager = self._get_user_manager(cache)
        user_id, user = user_manager.find_user_by_name_avatar(sender, avatar_url)
        
        img_path, error = self._create_jackpot_info_image(jackpot_info, user_id)
        if img_path and not error:
            file_queue.put(img_path)
        
        return ""

    def _handle_jackpot_bet(self, sender, avatar_url, bet_amount, file_queue, cache):
        user_manager = self._get_user_manager(cache)
        user_id, user = user_manager.find_user_by_name_avatar(sender, avatar_url)
        
        if not user:
            self.send_message_image(sender, file_queue, "Invalid user!", 
                                  "Jackpot - Error", cache, None)
            return ""
        
        if user.get('balance', 0) < bet_amount:
            self.send_message_image(sender, file_queue,
                f"Insufficient funds!\n\n"
                f"Required: ${bet_amount}\n"
                f"Your balance: ${user.get('balance', 0)}",
                "Jackpot - Error", cache, user_id)
            return ""
        
        balance_before = user.get('balance', 0)
        new_balance = balance_before - bet_amount
        self.update_user_balance(user_id, new_balance)
        
        success, message = self.jackpot_manager.create_or_join_jackpot(user_id, sender, bet_amount)
        
        if not success:
            self.update_user_balance(user_id, balance_before)
            self.send_message_image(sender, file_queue, message, 
                                  "Jackpot - Error", cache, user_id)
            return ""
        
        jackpot_info = self.jackpot_manager.get_jackpot_info()
        
        user_total_bet = 0
        user_percentage = 0
        for player in jackpot_info.get('players', []):
            if player.get('user_id') == user_id:
                user_total_bet = player.get('bet_amount', 0)
                user_percentage = player.get('percentage', 0)
                break
        
        player_count = len(jackpot_info.get('players', []))
        total_pot = jackpot_info.get('total_pot', 0)
        
        if user_total_bet == bet_amount:
            success_message = (
                f"**JACKPOT JOINED!**\n\n"
                f"**Your bet:** ${bet_amount}\n"
                f"**Total players:** {player_count}\n"
                f"**Total pot:** ${total_pot}\n"
                f"**Your chance:** {user_percentage:.1f}%\n\n"
            )
        else:
            success_message = (
                f"**BET INCREASED!**\n\n"
                f"**Added:** ${bet_amount}\n"
                f"**Your total bet:** ${user_total_bet}\n"
                f"**Total players:** {player_count}\n"
                f"**Total pot:** ${total_pot}\n"
                f"**Your chance:** {user_percentage:.1f}%\n\n"
            )
        
        if player_count == 1:
            success_message += "Waiting for more players... (need 1 more)"
        else:
            time_left = jackpot_info.get('time_remaining_formatted', '01:00')
            success_message += f"**JACKPOT STARTED!** \nDrawing in: {time_left}"
        
        img_path, error = self._create_jackpot_info_image(jackpot_info, user_id)
        if img_path and not error:
            file_queue.put(img_path)
        
        return ""

    def _create_jackpot_animation(self, jackpot_result):
        try:
            import os
            import time
            import random
            from PIL import Image, ImageDraw

            players = jackpot_result["all_players"]
            winner = jackpot_result["winner"]
            total_pot = jackpot_result["total_pot"]

            if not players or not winner:
                return None, "Invalid jackpot data"

            WIDTH, HEIGHT = 800, 360
            AVATAR = 70
            GAP = 6
            FRAMES = 160
            VISIBLE_AVATARS = 11

            WINNER_POSITION_IN_VISIBLE = VISIBLE_AVATARS // 2
            WINNER_INDEX_IN_STRIP = 150

            CENTER_X = WIDTH // 2 - AVATAR // 2
            STRIP_Y = 220

            for p in players:
                p['percentage'] = (p['bet_amount'] / total_pot * 100) if total_pot > 0 else 0

            sorted_players = sorted(players, key=lambda x: x['percentage'], reverse=True)
            winner_percentage = winner['percentage']

            avatar_entries = []

            for player in sorted_players:
                img = None
                try:
                    if player.get("user_id") and self.cache:
                        path = self.cache.get_avatar_path(player["user_id"])
                        if path and os.path.exists(path):
                            img = Image.open(path).convert("RGBA")
                except:
                    pass

                if not img:
                    img = Image.new("RGBA", (AVATAR, AVATAR), (70, 70, 90))
                    letter = player["username"][:1].upper()

                    letter_img = self.text_renderer.render_text(
                        text=letter,
                        font_size=AVATAR // 2,
                        color=(255, 255, 255, 255),
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )

                    lx = (AVATAR - letter_img.width) // 2
                    ly = (AVATAR - letter_img.height) // 2
                    img.paste(letter_img, (lx, ly), letter_img)

                img = img.resize((AVATAR, AVATAR))

                avatar_entries.append({
                    "img": img,
                    "player": player,
                    "percentage": player['percentage']
                })

            total_avatars_needed = 300
            strip = []
            strip_info = []

            for entry in avatar_entries:
                count = int(entry['percentage'] / 100 * total_avatars_needed)
                count = max(5, count)

                for _ in range(count):
                    strip.append(entry["img"])
                    strip_info.append(entry['player']['user_id'])

            diff = total_avatars_needed - len(strip)
            for _ in range(max(0, diff)):
                strip.append(avatar_entries[0]["img"])
                strip_info.append(avatar_entries[0]['player']['user_id'])

            winner_positions = [i for i, pid in enumerate(strip_info) if pid == winner['user_id']]
            target_position = min(WINNER_INDEX_IN_STRIP, len(strip) // 2)

            closest = min(winner_positions, key=lambda x: abs(x - target_position))
            strip[target_position], strip[closest] = strip[closest], strip[target_position]
            strip_info[target_position], strip_info[closest] = strip_info[closest], strip_info[target_position]

            WINNER_INDEX_IN_STRIP = target_position

            positions = list(range(len(strip)))
            positions.remove(WINNER_INDEX_IN_STRIP)
            random.shuffle(positions)

            new_strip = [None] * len(strip)
            new_info = [None] * len(strip)

            new_strip[WINNER_INDEX_IN_STRIP] = strip[WINNER_INDEX_IN_STRIP]
            new_info[WINNER_INDEX_IN_STRIP] = strip_info[WINNER_INDEX_IN_STRIP]

            idx = 0
            for i in range(len(strip)):
                if i == WINNER_INDEX_IN_STRIP:
                    continue
                old_pos = positions[idx]
                new_strip[i] = strip[old_pos]
                new_info[i] = strip_info[old_pos]
                idx += 1

            strip = new_strip
            strip_info = new_info

            end_pos = WINNER_INDEX_IN_STRIP - WINNER_POSITION_IN_VISIBLE
            end_pos = max(0, min(end_pos, len(strip) - VISIBLE_AVATARS - 1))

            start_pos = end_pos + 120 + random.randint(-15, 15)
            start_pos = min(start_pos, len(strip) - VISIBLE_AVATARS - 1)

            frames = []
            durations = []

            for f in range(FRAMES):
                t = f / (FRAMES - 1)

                if t < 0.70:
                    move_t = t / 0.85
                    ease = 1 - (1 - move_t) ** 4
                    pos = start_pos + (end_pos - start_pos) * ease
                else:
                    pos = end_pos

                if t < 0.3:
                    duration = 30
                elif t < 0.6:
                    duration = 50
                elif t < 0.85:
                    duration = 90
                else:
                    duration = 160

                img = Image.new("RGB", (WIDTH, HEIGHT), self.colors['bg_dark'])
                draw = ImageDraw.Draw(img)

                title = self.text_renderer.render_text(
                    text="JACKPOT DRAW",
                    font_size=34,
                    color=self.colors['gold'],
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 255)
                )
                img.paste(title, ((WIDTH - title.width) // 2, 20), title)

                if f >= int(FRAMES * 0.70):
                    info_y = 80
                    info_height = 80

                    draw.rectangle(
                        [0, info_y, WIDTH, info_y + info_height],
                        fill=self.colors['bg_medium']
                    )

                    win_label = self.text_renderer.render_text(
                        text="WINNER",
                        font_size=22,
                        color=self.colors['gold'],
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )
                    img.paste(win_label, ((WIDTH - win_label.width)//2, info_y + 5), win_label)

                    name_img = self.text_renderer.render_text(
                        text=winner['username'],
                        font_size=30,
                        color=self.colors['white'],
                        stroke_width=2,
                        stroke_color=(0, 0, 0, 255)
                    )
                    img.paste(name_img, ((WIDTH - name_img.width)//2, info_y + 28), name_img)

                    pot_img = self.text_renderer.render_text(
                        text=f"${total_pot}",
                        font_size=20,
                        color=(100, 255, 180),
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )
                    img.paste(pot_img, ((WIDTH - pot_img.width)//2, info_y + 58), pot_img)

                    if f >= int(FRAMES * 0.7):
                        stats = f"Chance: {winner_percentage:.1f}% | Bet: ${winner['bet_amount']}"
                        stats_img = self.text_renderer.render_text(
                            text=stats,
                            font_size=16,
                            color=(180, 200, 255)
                        )
                        img.paste(stats_img, ((WIDTH - stats_img.width)//2, 320), stats_img)

                frame_width = VISIBLE_AVATARS * (AVATAR + GAP) + 20
                frame_left = WIDTH//2 - frame_width//2
                frame_right = WIDTH//2 + frame_width//2

                draw.rectangle(
                    [frame_left-10, STRIP_Y-10, frame_right+10, STRIP_Y+AVATAR+10],
                    fill=self.colors['bg_medium'],
                    outline=self.colors['dark_gray'],
                    width=2
                )

                px = WIDTH // 2
                draw.polygon(
                    [(px - 10, STRIP_Y - 20),
                    (px + 10, STRIP_Y - 20),
                    (px, STRIP_Y)],
                    fill=self.colors['gold']
                )

                base = int(pos)
                offset = (pos - base) * (AVATAR + GAP)

                for i in range(VISIBLE_AVATARS + 2):
                    idx2 = (base + i) % len(strip)
                    x = CENTER_X + (i - VISIBLE_AVATARS//2) * (AVATAR + GAP) - offset
                    img.paste(strip[idx2], (int(x), STRIP_Y), strip[idx2])

                frames.append(img)
                durations.append(duration)

            out_dir = self.get_app_path("temp", "jackpot")
            os.makedirs(out_dir, exist_ok=True)

            path = os.path.join(out_dir, f"jackpot_{int(time.time()*1000)}.webp")

            frames[0].save(
                path,
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=0,
                format='WEBP',
                quality=70,
                method=4
            )

            return path, None

        except Exception as e:
            import traceback
            return None, traceback.format_exc()

    def _get_user_manager(self, cache):
        from user_manager import UserManager
        return UserManager(cache)

def register():
    plugin = JackpotPlugin()
    logger.info("[Jackpot] Jackpot plugin registered")
    return {
        "name": "jackpot",
        "description": "Jackpot game - everyone puts in money, one wins all!\n\nCommands:\n/jackpot - Show current jackpot\n/jackpot bet <amount> - Join jackpot\n/jackpot help - Detailed info",
        "aliases": ["/jp"],
        "execute": plugin.execute_game,
        "set_file_queue": plugin.set_file_queue
    }