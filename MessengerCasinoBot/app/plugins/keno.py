import os
import random
import time
from PIL import Image, ImageDraw
from base_game_plugin import BaseGamePlugin
from logger import logger
from plugins.monthly import record_monthly_win
from plugins.weekly import record_weekly_win


class KenoGame:
    TOTAL_NUMBERS = 80
    DRAWN_COUNT = 20
    MAX_PICKS = 10
    MIN_PICKS = 1
    
    PAYOUT_TABLE = {
        1: {0: 0, 1: 3},
        2: {0: 0, 1: 0, 2: 16},
        3: {0: 0, 1: 0, 2: 5, 3: 21},
        4: {0: 0, 1: 0, 2: 2, 3: 9, 4: 55},
        5: {0: 0, 1: 0, 2: 2, 3: 3, 4: 12, 5: 80},
        6: {0: 0, 1: 0, 2: 1, 3: 3, 4: 6, 5: 30, 6: 185},
        7: {0: 0, 1: 0, 2: 1, 3: 2, 4: 4, 5: 8, 6: 30, 7: 400},
        8: {0: 0, 1: 0, 2: 0, 3: 2, 4: 4, 5: 8, 6: 30, 7: 68, 8: 860},
        9: {0: 0, 1: 0, 2: 0, 3: 1, 4: 3, 5: 8, 6: 20, 7: 30, 8: 170, 9: 1750},
        10: {0: 0, 1: 0, 2: 0, 3: 0, 4: 3, 5: 7, 6: 13, 7: 15, 8: 30, 9: 260, 10: 4100},
    }
    
    def __init__(self, bet: int, picks: int, selected_numbers: list):
        self.bet = bet
        self.picks = picks
        self.selected_numbers = sorted(selected_numbers)
        self.drawn_numbers = []
        self.hits = 0
        self.multiplier = 0
        self.win_amount = 0
        self.is_complete = False
        
    def draw(self):
        all_numbers = list(range(1, self.TOTAL_NUMBERS + 1))
        self.drawn_numbers = random.sample(all_numbers, self.DRAWN_COUNT)
        
        self.hits = sum(1 for num in self.selected_numbers if num in self.drawn_numbers)
        
        payout_row = self.PAYOUT_TABLE.get(self.picks, {})
        self.multiplier = payout_row.get(self.hits, 0)
        self.win_amount = int(self.bet * self.multiplier)
        self.is_complete = True
        
        return {
            'hits': self.hits,
            'multiplier': self.multiplier,
            'win_amount': self.win_amount,
            'drawn_numbers': self.drawn_numbers,
            'selected_numbers': self.selected_numbers
        }


class KenoPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="keno")
        self.active_games = {}
        self.avatar_size = 80
        self.font_scale = 0.9
        
        self.colors = {
            "bg": (10, 14, 24),
            "bg_gradient": (18, 24, 40),
            "panel": (20, 26, 42),
            "panel_light": (32, 42, 68),
            "panel_dark": (12, 16, 28),
            "gold": (255, 215, 0),
            "gold_dark": (200, 170, 0),
            "green": (50, 225, 110),
            "green_dark": (30, 160, 75),
            "red": (255, 75, 75),
            "red_dark": (190, 45, 45),
            "blue": (50, 150, 255),
            "blue_dark": (25, 95, 190),
            "text": (245, 248, 255),
            "text_light": (195, 205, 225),
            "text_dim": (120, 135, 160),
            "border": (40, 55, 80),
            "border_light": (65, 85, 120),
            "selected": (255, 190, 0, 160),
            "selected_border": (255, 215, 0),
            "hit": (40, 210, 90, 200),
            "hit_border": (80, 255, 130),
            "miss": (230, 60, 60, 140),
            "miss_border": (255, 90, 90),
            "drawn_bg": (35, 75, 155, 180),
            "drawn_border": (70, 140, 255),
            "latest_drawn_bg": (255, 255, 255, 230),
            "latest_drawn_border": (255, 230, 50),
            "number_bg": (24, 31, 50),
        }

    def _parse_numbers(self, args) -> tuple:
        if not args:
            return None, None
        
        selected_numbers = []
        for arg in args:
            try:
                num = int(arg)
                if 1 <= num <= 80 and num not in selected_numbers:
                    selected_numbers.append(num)
            except ValueError:
                pass
        
        if not selected_numbers:
            return None, None
        
        picks = len(selected_numbers)
        if picks < KenoGame.MIN_PICKS or picks > KenoGame.MAX_PICKS:
            return None, None
        
        return picks, selected_numbers

    def _get_payout_table_text(self) -> str:
        lines = []
        lines.append("╔══════════════════════════════════════════════════════════════╗")
        lines.append("║                    KENO PAYOUT TABLE                       ║")
        lines.append("╠══════════════════════════════════════════════════════════════╣")
        
        for picks in range(1, 11):
            row = KenoGame.PAYOUT_TABLE.get(picks, {})
            max_hits = max(row.keys()) if row else 0
            
            if picks == 1:
                lines.append(f"║  [{picks} pick]   " + " " * (66 - len(f"  [{picks} pick]   ")))
            else:
                lines.append(f"║  [{picks} picks]  " + " " * (66 - len(f"  [{picks} picks]  ")))
            
            entries = []
            for hits in range(1, max_hits + 1):
                mult = row.get(hits, 0)
                if mult > 0:
                    entries.append(f"{hits}h={mult}x")
                elif hits > 0:
                    entries.append(f"{hits}h=0x")
            
            line = "  " + ", ".join(entries)
            padding = 70 - len(line)
            if padding > 0:
                line += " " * padding
            lines.append(line + "║")
        
        lines.append("╚══════════════════════════════════════════════════════════════╝")
        
        return "\n".join(lines)

    def _generate_animation_frames(self, game: KenoGame, user_id: str, user: dict,
                                   bet: int, net_win: int, balance: int, static: bool = False) -> list:
        frames = []
        width, height = 700, 680
        
        bg_img = self._load_background(user_id, width, height)
        
        if static:
            final_frame = self._draw_board_frame(
                bg_img.copy(), game, width, height, bet, balance,
                show_result=True, draw_phase=20,
                drawn_so_far=game.drawn_numbers
            )
            frames.append(final_frame)
        else:
            frame = self._draw_board_frame(
                bg_img.copy(), game, width, height, bet, balance,
                show_result=False, draw_phase=0
            )
            frames.append(frame)
            
            drawn_so_far = []
            all_drawn = game.drawn_numbers.copy()
            
            for i in range(20):
                drawn_so_far.append(all_drawn[i])
                frame = self._draw_board_frame(
                    bg_img.copy(), game, width, height, bet, balance,
                    show_result=False, draw_phase=i+1,
                    drawn_so_far=drawn_so_far
                )
                frames.append(frame)
            
            final_frame = self._draw_board_frame(
                bg_img.copy(), game, width, height, bet, balance,
                show_result=True, draw_phase=20,
                drawn_so_far=all_drawn
            )
            frames.append(final_frame)
        
        return frames

    def _load_background(self, user_id, width, height):
        bg_path = None
        if self.cache and user_id:
            bg_path = self.cache.get_background_path(user_id)
        
        if bg_path and os.path.exists(bg_path):
            try:
                bg = Image.open(bg_path).convert("RGB")
                bg = bg.resize((width, height), Image.Resampling.LANCZOS)
                return bg.convert("RGBA")
            except:
                pass
        
        bg = Image.new("RGBA", (width, height), self.colors["bg"])
        draw = ImageDraw.Draw(bg)
        
        for i in range(height):
            ratio = i / height
            r = int(self.colors["bg"][0] + (self.colors["bg_gradient"][0] - self.colors["bg"][0]) * ratio)
            g = int(self.colors["bg"][1] + (self.colors["bg_gradient"][1] - self.colors["bg"][1]) * ratio)
            b = int(self.colors["bg"][2] + (self.colors["bg_gradient"][2] - self.colors["bg"][2]) * ratio)
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        return bg

    def _draw_board_frame(self, img, game: KenoGame, width, height, bet, balance,
                          show_result=False, draw_phase=0, drawn_so_far=None):
        draw = ImageDraw.Draw(img)
        
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 160))
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)
        
        title_y = 15
        title = self._render_text("KENO", 42, self.colors["gold"], stroke=2)
        img.paste(title, ((width - title.width) // 2, title_y), title)
        
        cell_size = 54
        spacing = 5
        
        board_width = 10 * (cell_size + spacing) - spacing
        board_height = 8 * (cell_size + spacing) - spacing
        board_x = (width - board_width) // 2
        board_y = 70
        
        draw.rounded_rectangle(
            [board_x - 10, board_y - 10, board_x + board_width + 10, board_y + board_height + 10],
            radius=10, fill=self.colors["panel_dark"], outline=self.colors["border_light"], width=1
        )
        draw.rounded_rectangle(
            [board_x - 5, board_y - 5, board_x + board_width + 5, board_y + board_height + 5],
            radius=6, fill=self.colors["panel"], outline=self.colors["border"], width=1
        )
        
        drawn_set = set(drawn_so_far) if drawn_so_far else set()
        selected_set = set(game.selected_numbers)
        all_drawn_set = set(game.drawn_numbers) if game.drawn_numbers else set()
        
        latest_drawn = drawn_so_far[-1] if (drawn_so_far and not show_result) else None
        
        for i in range(1, 81):
            row = (i - 1) // 10
            col = (i - 1) % 10
            x = board_x + col * (cell_size + spacing)
            y = board_y + row * (cell_size + spacing)
            
            is_selected = i in selected_set
            is_drawn = i in drawn_set
            is_final_drawn = i in all_drawn_set
            is_latest = (i == latest_drawn)
            
            if show_result:
                if is_selected and is_final_drawn:
                    color = self.colors["hit"]
                    border_color = self.colors["hit_border"]
                    text_color = (255, 255, 255)
                    border_width = 2
                elif is_selected and not is_final_drawn:
                    color = self.colors["miss"]
                    border_color = self.colors["miss_border"]
                    text_color = (240, 180, 180)
                    border_width = 2
                elif is_final_drawn:
                    color = self.colors["drawn_bg"]
                    border_color = self.colors["drawn_border"]
                    text_color = (200, 225, 255)
                    border_width = 1
                else:
                    color = self.colors["number_bg"]
                    border_color = self.colors["border"]
                    text_color = self.colors["text_dim"]
                    border_width = 1
            else:
                if is_latest:
                    color = self.colors["latest_drawn_bg"]
                    border_color = self.colors["latest_drawn_border"]
                    text_color = (10, 20, 40)
                    border_width = 3
                elif is_selected and is_drawn:
                    color = self.colors["hit"]
                    border_color = self.colors["hit_border"]
                    text_color = (255, 255, 255)
                    border_width = 2
                elif is_selected:
                    color = self.colors["selected"]
                    border_color = self.colors["selected_border"]
                    text_color = (255, 255, 255)
                    border_width = 2
                elif is_drawn:
                    color = self.colors["drawn_bg"]
                    border_color = self.colors["drawn_border"]
                    text_color = (200, 225, 255)
                    border_width = 2
                else:
                    color = self.colors["number_bg"]
                    border_color = self.colors["border"]
                    text_color = self.colors["text_light"]
                    border_width = 1
            
            draw.rounded_rectangle(
                [x, y, x + cell_size, y + cell_size],
                radius=5, fill=color, outline=border_color, width=border_width
            )
            
            if not show_result and is_drawn and is_selected and not is_latest:
                draw.rounded_rectangle(
                    [x + 2, y + 2, x + cell_size - 2, y + cell_size - 2],
                    radius=3, fill=None, outline=(100, 255, 150, 200), width=2
                )
            
            font_size = 14
            num_text = self._render_text(str(i), font_size, text_color, stroke=1 if text_color != (10, 20, 40) else 0)
            text_x = x + (cell_size - num_text.width) // 2
            text_y = y + (cell_size - num_text.height) // 2
            img.paste(num_text, (text_x, text_y), num_text)
        
        status_y = board_y + board_height + 15
        status_bg = Image.new("RGBA", (board_width, 45), self.colors["panel_dark"])
        draw_status = ImageDraw.Draw(status_bg)
        draw_status.rounded_rectangle([(0, 0), (status_bg.width, status_bg.height)], radius=8, fill=self.colors["panel_dark"], outline=self.colors["border"], width=1)
        img.paste(status_bg, (board_x, status_y), status_bg)
        draw = ImageDraw.Draw(img)
        
        if show_result:
            if game.multiplier > 0:
                mult_text = f"Multiplier: x{game.multiplier}"
                mult_img = self._render_text(mult_text, 24, self.colors["green"], stroke=2)
                img.paste(mult_img, ((width - mult_img.width) // 2, status_y + 6), mult_img)
            else:
                no_mult_text = "Multiplier: x0"
                no_mult_img = self._render_text(no_mult_text, 22, self.colors["text_dim"], stroke=1)
                img.paste(no_mult_img, ((width - no_mult_img.width) // 2, status_y + 8), no_mult_img)
        else:
            current_hits = sum(1 for num in game.selected_numbers if num in drawn_set)
            current_multiplier = KenoGame.PAYOUT_TABLE.get(game.picks, {}).get(current_hits, 0)
            status_text = f"Multiplier: x{current_multiplier}"
            status_color = self.colors["gold"]
            
            status_img = self._render_text(status_text, 20, status_color, stroke=1)
            img.paste(status_img, ((width - status_img.width) // 2, status_y + 8), status_img)
        
        return img

    def _render_text(self, text, size, color, stroke=0):
        return self.text_renderer.render_text(
            text=text,
            font_size=size,
            color=color,
            stroke_width=stroke,
            stroke_color=(0, 0, 0, 255),
            shadow=stroke > 0,
            shadow_offset=(2, 2),
        )

    def _save_animation(self, frames, user_id, action_type, static=False):
        if not frames:
            return None
        
        output_dir = self.get_app_path("temp", "keno")
        os.makedirs(output_dir, exist_ok=True)
        
        path = os.path.join(output_dir, f"keno_{user_id}_{action_type}_{int(time.time() * 1000)}.webp")
        
        try:
            if static:
                frames[0].save(
                    path,
                    format='WEBP',
                    quality=85,
                    method=4,
                    optimize=True
                )
            else:
                frame_count = len(frames)
                frame_durations = [300] * frame_count
                
                if frame_count > 0:
                    frame_durations[-1] = 800
                
                frames[0].save(
                    path,
                    format='WEBP',
                    save_all=True,
                    append_images=frames[1:],
                    duration=frame_durations,
                    loop=0,
                    quality=70,
                    method=3,
                    optimize=True
                )
            return path
        except Exception as e:
            logger.error(f"[Keno] Error saving animation: {e}")
            return None

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        if error:
            self.send_message_image(
                sender, file_queue,
                error if error != "Invalid user" else "Player not found!",
                "KENO",
                cache,
                user_id
            )
            return ""
        
        balance = user.get('balance', 0)
        user_id_str = str(user_id)
        
        static = False
        if args and args[-1].lower() == 'x':
            static = True
            args = args[:-1]
        
        if not args or args[0].lower() in ["help", "h", "?"]:
            payout_table = self._get_payout_table_text()
            help_text = (
                "KENO GAME\n\n"
                "How to play:\n"
                "Pick 1-10 numbers from 1-80\n"
                "20 numbers are drawn\n"
                "Win based on how many you match!\n\n"
                "Commands:\n"
                "/keno <num1> <num2> ... - Play with default bet ($10)\n"
                "/keno bet <amount> <num1> <num2> ... - Play with custom bet\n"
                "/keno help - Show this help\n"
                "/keno <num1> <num2> ... x - Static result (no animation)\n\n"
                "Example: /keno bet 10 5 12 23 45 67\n\n"
                f"{payout_table}"
            )
            self.send_message_image(
                sender, file_queue,
                help_text,
                "KENO - Help & Payout Table",
                cache,
                user_id
            )
            return ""
        
        bet = 10
        args_list = list(args)
        
        if args_list[0].lower() == "bet":
            if len(args_list) < 3:
                self.send_message_image(
                    sender, file_queue,
                    "Usage: /keno bet <amount> <num1> <num2> ...\n"
                    "Example: /keno bet 10 5 12 23 45 67",
                    "KENO - Error",
                    cache,
                    user_id
                )
                return ""
            
            try:
                bet = int(args_list[1])
                if bet < 1:
                    self.send_message_image(
                        sender, file_queue,
                        "Minimum bet is $1!",
                        "KENO - Error",
                        cache,
                        user_id
                    )
                    return ""
                args_list = args_list[2:]
            except ValueError:
                self.send_message_image(
                    sender, file_queue,
                    "Invalid bet amount! Use whole numbers only.",
                    "KENO - Error",
                    cache,
                    user_id
                )
                return ""
        
        picks, selected_numbers = self._parse_numbers(args_list)
        
        if not selected_numbers:
            self.send_message_image(
                sender, file_queue,
                "Invalid numbers!\n\n"
                "Pick 1-10 unique numbers from 1-80.\n"
                "Example: /keno 5 12 23 45 67",
                "KENO - Error",
                cache,
                user_id
            )
            return ""
        
        if bet > balance:
            self.send_message_image(
                sender, file_queue,
                f"Insufficient funds!\n\n"
                f"Bet: ${bet}\n"
                f"Your balance: ${balance}",
                "KENO - Insufficient Funds",
                cache,
                user_id
            )
            return ""
        
        try:
            self.update_user_balance(user_id, balance - bet)
        except Exception as e:
            logger.error(f"[Keno] Error updating balance: {e}")
            self.send_message_image(
                sender, file_queue,
                "Error updating balance! Try again.",
                "KENO - Error",
                cache,
                user_id
            )
            return ""
        
        game = KenoGame(bet, picks, selected_numbers)
        result = game.draw()
        
        net_win = game.win_amount - bet
        new_balance = balance - bet + game.win_amount
        
        if game.win_amount > 0:
            try:
                self.update_user_balance(user_id, new_balance)
            except Exception as e:
                logger.error(f"[Keno] Error updating balance with winnings: {e}")
        
        try:
            self.cache.add_experience(user_id, net_win, sender, file_queue)
        except Exception as e:
            logger.warning(f"[Keno] Error adding experience: {e}")
        
        if net_win > 0:
            record_weekly_win(self.cache, user_id, "keno", net_win)
            record_monthly_win(self.cache, user_id, "keno", net_win)
        
        frames = self._generate_animation_frames(game, user_id_str, user, bet, net_win, new_balance, static)
        
        if frames:
            anim_path = self._save_animation(frames, user_id_str, "play", static)
            if anim_path:
                user_info_before = self.create_user_info(sender, bet, 0, balance, user)
                user_info_after = self.create_user_info(sender, bet, net_win, new_balance, user)
                
                if static:
                    result_path, error = self.generate_animation(
                        base_animation_path=anim_path,
                        user_id=user_id_str,
                        user=user,
                        user_info_before=user_info_before,
                        user_info_after=user_info_after,
                        animated=False,
                        frame_duration=130,
                        last_frame_multiplier=1,
                        show_win_text=True,
                        font_scale=0.9,
                        avatar_size=45,
                        win_text_height=280
                    )
                else:
                    result_path, error = self.generate_animation(
                        base_animation_path=anim_path,
                        user_id=user_id_str,
                        user=user,
                        user_info_before=user_info_before,
                        user_info_after=user_info_after,
                        animated=True,
                        frame_duration=120,
                        last_frame_multiplier=20,
                        show_win_text=True,
                        font_scale=0.9,
                        avatar_size=45,
                        win_text_height=280
                    )
                
                if result_path:
                    file_queue.put(result_path)
                    logger.info(f"[Keno] {sender} - {'Static' if static else 'Animated'} - Bet: ${bet}, Picks: {picks}, Hits: {game.hits}, Win: ${game.win_amount}, Net: ${net_win}")
                    return ""
                else:
                    file_queue.put(anim_path)
                    logger.warning(f"[Keno] Overlay generation failed: {error}")
                    return ""
        
        return ""


def register():
    plugin = KenoPlugin()
    logger.info("[Keno] Keno plugin registered with user overlay")
    return {
        "name": "keno",
        "aliases": ["/keno", "/k"],
        "description": "KENO Game\n\n"
        "Pick 1-10 numbers from 1-80 and win based on how many match the 20 drawn numbers!\n\n"
        "Commands:\n"
        "/keno <num1> <num2> ... - Play with default bet ($10)\n"
        "/keno bet <amount> <num1> <num2> ... - Play with custom bet\n"
        "/keno help - Show help with payout table\n"
        "/keno <num1> <num2> ... x - Static result (no animation)\n\n"
        "Example: /keno bet 10 5 12 23 45 67",
        "execute": plugin.execute_game
    }
