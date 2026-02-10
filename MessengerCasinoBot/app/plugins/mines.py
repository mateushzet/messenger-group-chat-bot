import os
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from base_game_plugin import BaseGamePlugin
from logger import logger

class MinesGame:
    def __init__(self, size=5, num_mines=5, text_renderer=None):
        self.size = size
        self.num_mines = num_mines
        self.mines_positions = []
        self.revealed = [[False for _ in range(size)] for _ in range(size)]
        self.game_over = False
        self.win = False
        self.moves = 0
        self.safe_revealed = 0
        self.total_safe = size * size - num_mines
        self.exploded_mine = None
        self.text_renderer = text_renderer
        
        self.multiplier_sets = self.calculate_multipliers()
        
        self.all_multipliers = self.multiplier_sets.get(num_mines, self.multiplier_sets[5])
        
        max_display = min(7, len(self.all_multipliers))
        self.multipliers = self.all_multipliers[:max_display]
        self.current_multiplier_index = 0
        self.global_multiplier_index = 0
        
        self.loaded_images = {}

    def calculate_multipliers(self):

        multiplier_sets = {}
        
        total_cells = 25
        
        for mines in range(1, 25):
            safe_cells = total_cells - mines
            multipliers = []
            
            for safe_revealed in range(0, safe_cells + 1):
                if safe_revealed == 0:
                    probability = 1.0
                else:
                    probability = 1.0
                    for i in range(safe_revealed):
                        probability *= (safe_cells - i) / (total_cells - i)
                
                if probability > 0:
                    multiplier = 0.99 / probability
                else:
                    multiplier = 0
                
                multipliers.append(multiplier)
                            
            multiplier_sets[mines] = multipliers

        return multiplier_sets

    def load_board_elements(self, elements_folder):
        cell_types = ['hidden', 'safe', 'mine', 'exploded']
        loaded_count = 0
        
        for cell_type in cell_types:
            file_path = os.path.join(elements_folder, f"cell_{cell_type}.png")
            try:
                self.loaded_images[f'cell_{cell_type}'] = Image.open(file_path).convert('RGBA')
                loaded_count += 1
            except Exception as e:
                logger.warning(f"[Mines] Failed to load {file_path}: {e}")
                self.loaded_images[f'cell_{cell_type}'] = None
        
        for number in range(1, 26):
            file_path = os.path.join(elements_folder, f"cell_hidden_{number}.png")
            try:
                self.loaded_images[f'cell_hidden_{number}'] = Image.open(file_path).convert('RGBA')
                loaded_count += 1
            except Exception as e:
                logger.warning(f"[Mines] Missing numbered cell: {file_path} - {e}")
                self.loaded_images[f'cell_hidden_{number}'] = None
        
        file_path = os.path.join(elements_folder, "mine_icon.png")
        try:
            self.loaded_images['mine_icon'] = Image.open(file_path).convert('RGBA')
            loaded_count += 1
        except Exception as e:
            logger.warning(f"[Mines] Failed to load {file_path}: {e}")
            self.loaded_images['mine_icon'] = None
            
    def initialize_board(self):
        all_positions = [(r, c) for r in range(self.size) for c in range(self.size)]
        self.mines_positions = random.sample(all_positions, min(self.num_mines, len(all_positions)))

        return True
    
    def reveal(self, row, col):
        
        if self.game_over:
            return None
        
        if self.revealed[row][col]:
            return "already_revealed"
        
        if self.moves == 0:
            self.initialize_board()
        
        self.moves += 1
        self.revealed[row][col] = True
        
        self.global_multiplier_index += 1
        
        if self.global_multiplier_index < len(self.all_multipliers):
            self.current_multiplier_index = self.global_multiplier_index
        
        if len(self.all_multipliers) > 7:
            if self.current_multiplier_index >= 3 and self.global_multiplier_index + 3 < len(self.all_multipliers):
                start_idx = max(0, self.current_multiplier_index - 3)
                end_idx = min(len(self.all_multipliers), self.current_multiplier_index + 4)
                self.multipliers = self.all_multipliers[start_idx:end_idx]
            elif self.global_multiplier_index >= len(self.all_multipliers) - 3:
                self.multipliers = self.all_multipliers[-7:]
            else:
                self.multipliers = self.all_multipliers[:7]
        else:
            self.multipliers = self.all_multipliers[:]
        
        if (row, col) in self.mines_positions:
            self.game_over = True
            self.win = False
            self.exploded_mine = (row, col)
            
            for r, c in self.mines_positions:
                self.revealed[r][c] = True
            
            return False
        else:
            self.safe_revealed += 1
            
            if self.safe_revealed == self.total_safe:
                self.game_over = True
                self.win = True
                for r, c in self.mines_positions:
                    self.revealed[r][c] = True
                return "auto_win"
            
            return True
    
    def draw_gradient_rectangle(self, draw, x1, y1, x2, y2, color1, color2, direction='horizontal'):
        if direction == 'horizontal':
            for x in range(int(x1), int(x2)):
                ratio = (x - x1) / (x2 - x1)
                r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                draw.line([(x, y1), (x, y2)], fill=(r, g, b))
        else:
            for y in range(int(y1), int(y2)):
                ratio = (y - y1) / (y2 - y1)
                r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                draw.line([(x1, y), (x2, y)], fill=(r, g, b))
    
    def get_current_multiplier(self):
        if self.current_multiplier_index < len(self.all_multipliers):
            mult = self.all_multipliers[self.current_multiplier_index]
            return mult
        mult = self.all_multipliers[-1]
        return mult
    
    def get_max_multiplier(self):
        max_mult = self.all_multipliers[-1] if self.all_multipliers else 1.0
        return max_mult
    
    def get_multiplier_for_safe(self, safe_count):
        if safe_count < len(self.all_multipliers):
            mult = self.all_multipliers[safe_count]
            return mult
        mult = self.all_multipliers[-1]
        return mult

    def get_game_state_image(self, output_path, elements_folder, game_result=None, win_amount=0):
        
        CELL_SIZE = 70
        BORDER = 3
        IMAGE_SIZE = self.size * CELL_SIZE
        MULTIPLIER_BAR_HEIGHT = 50
        
        MARGIN_TOP = 10
        MARGIN_BOTTOM = 70
        MARGIN_LEFT = 10
        MARGIN_RIGHT = 10
        
        total_width = IMAGE_SIZE + MARGIN_LEFT + MARGIN_RIGHT
        total_height = IMAGE_SIZE + MULTIPLIER_BAR_HEIGHT + MARGIN_TOP + MARGIN_BOTTOM
        
        if not self.loaded_images:
            self.load_board_elements(elements_folder)
        
        COLORS = {
            'bg': (0, 0, 0, 0),
            'multiplier_active1': (76, 175, 80),
            'multiplier_active2': (56, 142, 60),
            'multiplier_inactive1': (50, 50, 60),
            'multiplier_inactive2': (70, 70, 80),
            'multiplier_border': (100, 100, 120),
            'multiplier_text': (200, 200, 220),
            'multiplier_active_text': (255, 255, 255),
            'border': (60, 60, 80),
            'grid_bg': (35, 35, 45),
            'counter_bg': (40, 40, 50, 255),
            'counter_border': (80, 80, 100),
            'counter_text': (200, 200, 220),
            'counter_number': (255, 80, 80),
            'win_bg': (40, 167, 69, 220),
            'lose_bg': (220, 53, 69, 220),
            'result_text': (255, 255, 255),
        }
        
        img = Image.new('RGBA', (total_width, total_height), COLORS['bg'])
        draw = ImageDraw.Draw(img)
        
        multiplier_font_size = 11
        bold_font_size = 11
        
        board_start_x = MARGIN_LEFT
        board_start_y = MARGIN_TOP + MULTIPLIER_BAR_HEIGHT
        
        counter_bg_width = 60
        counter_bg_height = 30
        counter_x = board_start_x + IMAGE_SIZE - counter_bg_width - 5
        counter_y = MARGIN_TOP + 8
        
        draw.rectangle([
            counter_x, counter_y,
            counter_x + counter_bg_width, counter_y + counter_bg_height
        ], fill=COLORS['counter_bg'], outline=COLORS['counter_border'], width=1)
        
        if self.loaded_images.get('mine_icon'):
            icon_x = counter_x + 5
            icon_y = counter_y + (counter_bg_height - self.loaded_images['mine_icon'].height) // 2
            img.paste(self.loaded_images['mine_icon'], (int(icon_x), int(icon_y)), self.loaded_images['mine_icon'])
        
        mines_left = self.num_mines
        for row in range(self.size):
            for col in range(self.size):
                if (row, col) in self.mines_positions and self.revealed[row][col]:
                    mines_left -= 1
        
        mines_text = f"{self.num_mines}"
        
        if self.text_renderer:
            mines_img = self.text_renderer.render_text(
                text=mines_text,
                font_size=bold_font_size,
                color=COLORS['counter_number']
            )
            
            mines_x = counter_x + counter_bg_width - mines_img.width - 8
            mines_y = counter_y + (counter_bg_height - mines_img.height) // 2
            
            img.paste(mines_img, (int(mines_x), int(mines_y)), mines_img)
            
        multiplier_bar_y = MARGIN_TOP + 5
        total_multipliers_width = IMAGE_SIZE * 0.75
        
        display_multipliers_count = 7
        multiplier_width = total_multipliers_width // display_multipliers_count
        multiplier_start_x = 25

        active_position = 3
        
        if len(self.all_multipliers) <= 7:
            start_idx = 0
            display_multipliers = self.all_multipliers
            display_active_index = min(self.current_multiplier_index, len(display_multipliers) - 1)
        else:
            
            start_idx = self.current_multiplier_index - active_position
            
            if start_idx < 0:
                start_idx = 0
            
            end_idx = start_idx + 7
            if end_idx > len(self.all_multipliers):
                end_idx = len(self.all_multipliers)
                start_idx = end_idx - 7
                
                if start_idx < 0:
                    start_idx = 0
            
            display_multipliers = self.all_multipliers[start_idx:end_idx]
            display_active_index = self.current_multiplier_index - start_idx
                    
        actual_display_count = len(display_multipliers)
        if actual_display_count < 7:
            adjusted_multiplier_width = total_multipliers_width // actual_display_count
            multiplier_width = adjusted_multiplier_width
        
        display_active_index = min(display_active_index, len(display_multipliers) - 1)
        display_active_index = max(display_active_index, 0)
        
        for i in range(len(display_multipliers)):
            x1 = multiplier_start_x + i * multiplier_width
            y1 = multiplier_bar_y
            x2 = multiplier_start_x + (i + 1) * multiplier_width - 2
            y2 = multiplier_bar_y + 35
            
            multiplier_value = display_multipliers[i]
            is_active = i == display_active_index
            
            
            if is_active:
                self.draw_gradient_rectangle(draw, x1, y1, x2, y2, 
                                        COLORS['multiplier_active1'], 
                                        COLORS['multiplier_active2'], 
                                        'vertical')
                text_color = COLORS['multiplier_active_text']
                border_color = (56, 142, 60)
            else:
                self.draw_gradient_rectangle(draw, x1, y1, x2, y2,
                                        COLORS['multiplier_inactive1'],
                                        COLORS['multiplier_inactive2'],
                                        'vertical')
                text_color = COLORS['multiplier_text']
                border_color = COLORS['multiplier_border']
            
            draw.rectangle([x1, y1, x2, y2], outline=border_color, width=2)
            
            if multiplier_value < 10:
                multiplier_text = f"x{multiplier_value:.2f}"
            elif multiplier_value < 100:
                multiplier_text = f"x{multiplier_value:.1f}"
            else:
                multiplier_text = f"x{multiplier_value:.0f}"
            
            if self.text_renderer:
                multiplier_img = self.text_renderer.render_text(
                    text=multiplier_text,
                    font_size=multiplier_font_size,
                    color=text_color
                )
                
                text_x = x1 + (multiplier_width - multiplier_img.width) // 2
                text_y = y1 + (35 - multiplier_img.height) // 2
                
                img.paste(multiplier_img, (int(text_x), int(text_y)), multiplier_img)

        draw.rectangle([
            board_start_x, board_start_y,
            board_start_x + IMAGE_SIZE, board_start_y + IMAGE_SIZE
        ], fill=COLORS['grid_bg'])
        
        for i in range(self.size + 1):
            line_pos = i * CELL_SIZE
            draw.line([(board_start_x, board_start_y + line_pos), 
                      (board_start_x + IMAGE_SIZE, board_start_y + line_pos)], 
                     fill=COLORS['border'], width=BORDER)
            draw.line([(board_start_x + line_pos, board_start_y), 
                      (board_start_x + line_pos, board_start_y + IMAGE_SIZE)], 
                     fill=COLORS['border'], width=BORDER)
        
        cells_with_images = 0
        
        is_win_result = game_result == "WIN"
        
        for row in range(self.size):
            for col in range(self.size):
                x = board_start_x + col * CELL_SIZE + BORDER - 3
                y = board_start_y + row * CELL_SIZE + BORDER - 3
                field_number = row * self.size + col + 1
                
                if self.revealed[row][col]:
                    is_mine = (row, col) in self.mines_positions
                    
                    if is_mine:
                        is_exploded = (row, col) == self.exploded_mine
                        if is_exploded:
                            cell_img = self.loaded_images['cell_exploded']
                        else:
                            cell_img = self.loaded_images['cell_mine']
                    else:
                        cell_img = self.loaded_images['cell_safe']
                else:
                    if is_win_result and (row, col) in self.mines_positions:
                        cell_img = self.loaded_images['cell_mine']
                    else:
                        cell_img = self.loaded_images[f'cell_hidden_{field_number}']
                
                if cell_img:
                    img.paste(cell_img, (int(x), int(y)), cell_img)
                    cells_with_images += 1
                
        img.save(output_path, format='WEBP', quality=90, optimize=True)

class MinesPlugin(BaseGamePlugin):
    def __init__(self):
        logger.info("[Mines] Initializing MinesPlugin")
        super().__init__(
            game_name="mines"
        )
        self.active_games = {}
        self.elements_folder = self.get_asset_path("mines", "board_elements")

        self.avatar_size = 80
        self.font_scale = 0.9
    
    def get_multiplier_info(self, bombs):
        if bombs < 1 or bombs > 24:
            return ""
        
        game = MinesGame(num_mines=bombs, text_renderer=self.text_renderer)
        
        info_lines = []
        safe_cells = 25 - bombs
        
        for i in range(0, safe_cells + 1):
            if i < len(game.all_multipliers):
                mult = game.get_multiplier_for_safe(i)
                profit = mult - 1.0
                info_lines.append(f"  {i} safe: x{mult:.2f} (+{profit:.2f}x)")
          
        if len(info_lines) > 8:
            step = max(1, len(info_lines) // 5)
            filtered_lines = []
            for idx in range(0, len(info_lines), step):
                filtered_lines.append(info_lines[idx])
            if len(info_lines) - 1 not in range(0, len(info_lines), step):
                filtered_lines.append(info_lines[-1])
            return "\n".join(filtered_lines)
        else:
            return "\n".join(info_lines)

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        
        self.cache = cache

        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        if error == "Invalid user":
            self.send_message_image(sender, file_queue, "Invalid user!", "Mines - Validation Error", cache, user_id)
            return ""
        elif error:
            self.send_message_image(sender, file_queue, error, "Mines - Error", cache, user_id)
            return ""
        
        balance_before = user.get("balance", 0)

        if len(args) == 0:
            self.send_message_image(sender, file_queue,
                                  "Mines Game Commands:\n\n"
                                  "Start new game:\n"
                                  "/mines start <bet> <bombs>\n\n"
                                  "Reveal tiles:\n"
                                  "/mines <tile> (1-25)\n"
                                  "Example: /mines 13\n\n"
                                  "Cashout:\n"
                                  "/mines cashout\n\n"
                                  "Bombs: 1-24 mines on 5x5 board",
                                  "Mines Game Help", cache, user_id)
            return ""

        cmd = args[0].lower()
        
        if cmd == "start" or cmd == "bet" or cmd == "b" or cmd == "s":
            if len(args) < 3:
                self.send_message_image(sender, file_queue,
                                      "Usage: /mines start <bet> <bombs>\n\n"
                                      "Example: /mines start 100 5\n\n"
                                      "Bombs: 1-24 mines on 5x5 board",
                                      "Mines - Start Game", cache, user_id)
                return ""
            try:
                bet = int(args[1])
                bombs = int(args[2])
            except ValueError as e:
                self.send_message_image(sender, file_queue,
                                      "Invalid format!\n\n"
                                      "Use: /mines start <bet> <bombs>\n"
                                      "Example: /mines start 100 5",
                                      "Mines - Error", cache, user_id)
                return ""
            
            if bombs < 1 or bombs > 24:
                self.send_message_image(sender, file_queue,
                                      f"Invalid bomb count: {bombs}\n\n"
                                      f"Number of bombs must be between 1 and 24",
                                      "Mines - Error", cache, user_id)
                return ""
                
            if user_id in self.active_games:
                self.send_message_image(sender, file_queue,
                                      "You already have an active game!\n\n"
                                      "Use /mines cashout or finish the current game.",
                                      "Mines - Active Game", cache, user_id)
                return ""
            
            if bet > balance_before:
                self.send_message_image(sender, file_queue,
                                      f"Insufficient funds!\n\n"
                                      f"Bet: ${bet}\n"
                                      f"Your balance: ${balance_before}",
                                      "Mines - Insufficient Funds", cache, user_id)
                return ""
            
            game = MinesGame(num_mines=bombs, text_renderer=self.text_renderer)
            self.active_games[user_id] = {
                "game": game, 
                "bet": bet, 
                "bombs": bombs,
                "player": sender
            }
            
            new_balance = balance_before - bet
            try:
                self.update_user_balance(user_id, new_balance)
            except Exception as e:
                self.send_message_image(sender, file_queue,
                                      "Error updating balance!\n\n"
                                      "Please try again or contact support.",
                                      "Mines - System Error", cache, user_id)
                return ""
                        
            img_path = os.path.join(self.results_folder, f"mines_{user_id}.webp")
            game.get_game_state_image(img_path, self.elements_folder)
            
            overlay_path, error = self.apply_user_overlay(img_path, user_id, sender, bet, 0, new_balance, user, show_win_text=False, font_scale=self.font_scale, avatar_size=self.avatar_size)
            if overlay_path:
                file_queue.put(overlay_path)
            else:
                logger.warning(f"[Mines] Failed to create overlay for {sender}")
                
            current_mult = game.get_current_multiplier()
                        
            return ""

        elif cmd == "cashout" or cmd == "c" or cmd == "stand":
            if user_id not in self.active_games:
                self.send_message_image(sender, file_queue,
                                      "No active game found!\n\n"
                                      "Start a new game with: /mines start <bet> <bombs>",
                                      "Mines - No Game", cache, user_id)
                return ""
                
            data = self.active_games.pop(user_id)
            game = data["game"]
            bet = data["bet"]
            bombs = data["bombs"]
            
            mult = game.get_current_multiplier()
            win_amount = int(bet * mult)
            net_win = win_amount - bet
            new_balance = balance_before + win_amount
            
            logger.info(f"[Mines] Cashout for {sender}: bet={bet}, multiplier=x{mult:.2f}, win={win_amount}, net={net_win}")
            
            try:
                newLevel, newLevelProgress = self.cache.add_experience(user_id, net_win, sender, file_queue)
                user["level"] = newLevel
                user["level_progress"] = newLevelProgress
            except Exception as e:
                logger.error(f"[Mines] Error adding experience for {sender}: {e}")
            
            try:
                self.update_user_balance(user_id, new_balance)
            except Exception as e:
                logger.error(f"[Mines] Error updating balance for {sender}: {e}")
                self.send_message_image(sender, file_queue,
                                      "Error updating balance!\n\n"
                                      "Please try again or contact support.",
                                      "Mines - System Error", cache, user_id)
                return ""
            
            img_path = os.path.join(self.results_folder, f"mines_{user_id}_cashout.webp")
            game.get_game_state_image(img_path, self.elements_folder, "WIN", net_win)
            
            overlay_path, error = self.apply_user_overlay(img_path, user_id, sender, bet, net_win, new_balance, user, show_win_text=True, font_scale=self.font_scale, avatar_size=self.avatar_size)
            if overlay_path:
                file_queue.put(overlay_path)
            
            return ""

        else:
            if user_id not in self.active_games:
                self.send_message_image(sender, file_queue,
                                      "No active game found!\n\n"
                                      "Start a new game with: /mines start <bet> <bombs>",
                                      "Mines - No Game", cache, user_id)
                return ""
                
            data = self.active_games[user_id]
            game = data["game"]
            bet = data["bet"]
            bombs = data["bombs"]
                        
            try:
                tiles = [int(t.strip()) for t in cmd.split(",")]
            except ValueError as e:
                self.send_message_image(sender, file_queue,
                                      "Invalid tile format!\n\n"
                                      "Usage: /mines <tile>\n"
                                      "Example: /mines 13\n"
                                      "Multiple tiles: /mines 1,2,3",
                                      "Mines - Error", cache, user_id)
                return ""
                
            messages = []
            lost_game = False
            
            for t in tiles:
                if not (1 <= t <= 25):
                    messages.append(f"Tile {t} out of range 1-25.")
                    continue
                    
                row, col = (t - 1) // 5, (t - 1) % 5
                
                safe = game.reveal(row, col)
                
                if safe == "already_revealed":
                    messages.append(f"Tile {t} was already revealed!")
                    continue
                elif safe == "auto_win":
                    messages.append(f"Safe! Tile {t}")
                    messages.append(f"ALL SAFE TILES REVEALED! Automatic cashout!")
                    
                    if user_id in self.active_games:
                        self.active_games.pop(user_id, None)
                    
                    mult = game.get_current_multiplier()
                    win_amount = int(bet * mult)
                    net_win = win_amount - bet
                    new_balance = balance_before + win_amount
                    
                    try:
                        newLevel, newLevelProgress = self.cache.add_experience(user_id, net_win, sender, file_queue)
                        user["level"] = newLevel
                        user["level_progress"] = newLevelProgress
                    except Exception as e:
                        logger.error(f"[Mines] Error adding experience for win: {e}")
                    
                    try:
                        self.update_user_balance(user_id, new_balance)
                    except Exception as e:
                        logger.error(f"[Mines] Error updating balance for auto-win: {e}")
                        self.send_message_image(sender, file_queue,
                                              "Error updating balance!\n\n"
                                              "Please try again or contact support.",
                                              "Mines - System Error", cache, user_id)
                        return ""
                                        
                    img_path = os.path.join(self.results_folder, f"mines_{user_id}_win.webp")
                    game.get_game_state_image(img_path, self.elements_folder, "WIN", net_win)
                    
                    overlay_path, error = self.apply_user_overlay(img_path, user_id, sender, bet, net_win, new_balance, user, show_win_text=True, font_scale=self.font_scale, avatar_size=self.avatar_size)
                    if overlay_path:
                        file_queue.put(overlay_path)
                    
                    messages.append(f"Multiplier: x{mult:.2f}")
                    messages.append(f"Total payout: ${win_amount} (+${net_win})")
                    messages.append(f"New balance: ${new_balance}")
                                        
                    return ""
                elif safe is None:
                    logger.error(f"[Mines] Failed to reveal tile {t} for {sender}")
                    continue
                
                if not safe:
                    lost_game = True
                    logger.info(f"[Mines] Game lost by {sender} on tile {t}")
                    
                    if user_id in self.active_games:
                        self.active_games.pop(user_id, None)
                    
                    try:
                        newLevel, newLevelProgress = self.cache.add_experience(user_id, -bet, sender, file_queue)
                        user["level"] = newLevel
                        user["level_progress"] = newLevelProgress
                    except Exception as e:
                        logger.error(f"[Mines] Error adding experience for loss: {e}")

                    img_path = os.path.join(self.results_folder, f"mines_{user_id}_lost.webp")
                    game.get_game_state_image(img_path, self.elements_folder, "LOST", bet)
                    
                    overlay_path, error = self.apply_user_overlay(img_path, user_id, sender, bet, -bet, balance_before, user, show_win_text=True, font_scale=self.font_scale, avatar_size=self.avatar_size)
                    if overlay_path:
                        file_queue.put(overlay_path)
                    
                    break
                else:
                    mult = game.get_current_multiplier()
                    total_payout = int(bet * mult)
                    net_payout = total_payout - bet
                    
                    messages.append(f"Safe! Tile {t}")
                    messages.append(f"Multiplier: x{mult:.2f}")
                    messages.append(f"Current payout: ${total_payout} (+${net_payout})")
                    logger.debug(f"[Mines] Tile {t} safe: multiplier={mult:.2f}, payout={total_payout}, net={net_payout}")
            
            if not lost_game:
                img_path = os.path.join(self.results_folder, f"mines_{user_id}_move.webp")
                game.get_game_state_image(img_path, self.elements_folder)
                
                current_mult = game.get_current_multiplier()
                total_payout = int(bet * current_mult)
                net_payout = total_payout - bet
                safe_tiles_left = game.total_safe - game.safe_revealed
                
                mines_left = bombs
                for row in range(5):
                    for col in range(5):
                        if (row, col) in game.mines_positions and game.revealed[row][col]:
                            mines_left -= 1
                
                
                overlay_path, error = self.apply_user_overlay(img_path, user_id, sender, bet, net_payout, balance_before, user,
                                                          show_win_text=False, font_scale=self.font_scale, avatar_size=self.avatar_size)
                if overlay_path:
                    file_queue.put(overlay_path)
                
                if game.safe_revealed > 0:
                    messages.append(f"Progress: {game.safe_revealed}/{game.total_safe} safe tiles")
                    messages.append(f"Safe tiles left: {safe_tiles_left}")
                    messages.append(f"Mines left: {mines_left}")
                    
                    if safe_tiles_left > 0 and mines_left > 0:
                        prob_safe = safe_tiles_left / (safe_tiles_left + mines_left)
                        messages.append(f"Next safe chance: {prob_safe*100:.1f}%")
                    
                    if safe_tiles_left > 0 and game.current_multiplier_index + 1 < len(game.all_multipliers):
                        next_mult = game.all_multipliers[game.current_multiplier_index + 1]
                        next_payout = int(bet * next_mult)
                        next_net = next_payout - bet
                        messages.append(f"Next safe: x{next_mult:.2f} (payout: ${next_payout}, +${next_net})")
                    
                    cashout_mult = game.get_current_multiplier()
                    cashout_payout = int(bet * cashout_mult)
                    cashout_net = cashout_payout - bet
                    messages.append(f"Cashout now: x{cashout_mult:.2f} = ${cashout_payout} (+${cashout_net})")
                    messages.append(f"Use: /mines cashout")
                        
            return ""

def register():
    logger.info("[Mines] Registering Mines plugin")
    plugin = MinesPlugin()
    return {
        "name": "mines",
        "aliases": ["/m"],
        "description": "Minesweeper Game - Find Safe Tiles Before Hitting Mines\n\n**Commands:**\n- /mines start <bet> <bombs> - Start new game\n- /mines <tile> - Reveal tile (1-25)\n- /mines cashout - Cashout and collect winnings\n\n**Bombs:** 1-24 mines on 5×5 board\n**Multiplier:** Increases with each safe tile revealed",
        "execute": plugin.execute_game
    }