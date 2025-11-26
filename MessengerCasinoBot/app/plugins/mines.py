import os
import random
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from base_game_plugin import BaseGamePlugin
from logger import logger

class HazardMinesGame:
    def __init__(self, size=5, num_mines=5):
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
        
        self.all_multipliers = [
            1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9,
            2.0, 2.2, 2.4, 2.6, 2.8, 3.0, 3.3, 3.6, 4.0, 4.5,
            5.0, 6.0, 7.0, 8.0, 10.0
        ]
        self.multipliers = self.all_multipliers[:7]
        self.current_multiplier_index = 0
        self.global_multiplier_index = 0
        
        self.loaded_images = {}
        
    def load_board_elements(self, elements_folder):
        cell_types = ['hidden', 'safe', 'mine', 'exploded']
        for cell_type in cell_types:
            try:
                self.loaded_images[f'cell_{cell_type}'] = Image.open(
                    os.path.join(elements_folder, f"cell_{cell_type}.png")
                ).convert('RGBA')
            except:
                logger.warning(f"Missing file: cell_{cell_type}.png")
                self.loaded_images[f'cell_{cell_type}'] = None
        
        for number in range(1, 26):
            try:
                self.loaded_images[f'cell_hidden_{number}'] = Image.open(
                    os.path.join(elements_folder, f"cell_hidden_{number}.png")
                ).convert('RGBA')
            except:
                logger.warning(f"Missing file: cell_hidden_{number}.png")
                self.loaded_images[f'cell_hidden_{number}'] = None
        
        try:
            self.loaded_images['mine_icon'] = Image.open(
                os.path.join(elements_folder, "mine_icon.png")
            ).convert('RGBA')
        except:
            logger.warning("Missing file: mine_icon.png")
            self.loaded_images['mine_icon'] = None
        
        logger.info("Loaded all board elements")
    
    def initialize_board(self, first_click_pos):
        all_positions = [(r, c) for r in range(self.size) for c in range(self.size)]
        
        safe_positions = set()
        safe_positions.add(first_click_pos)
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = first_click_pos[0] + dr, first_click_pos[1] + dc
                if 0 <= nr < self.size and 0 <= nc < self.size:
                    safe_positions.add((nr, nc))
        
        available_positions = [pos for pos in all_positions if pos not in safe_positions]
        self.mines_positions = random.sample(available_positions, min(self.num_mines, len(available_positions)))
    
    def reveal(self, row, col):
        if self.game_over or self.revealed[row][col]:
            return True
        
        if self.moves == 0:
            self.initialize_board((row, col))
        
        self.moves += 1
        self.revealed[row][col] = True
        
        self.global_multiplier_index += 1
        
        if self.current_multiplier_index == 3 and self.global_multiplier_index < len(self.all_multipliers):
            if self.global_multiplier_index + 6 < len(self.all_multipliers):
                self.multipliers = self.all_multipliers[self.global_multiplier_index-3:self.global_multiplier_index+4]
            else:
                self.multipliers = self.all_multipliers[-7:]
        else:
            if self.current_multiplier_index < 6 and self.global_multiplier_index < len(self.all_multipliers):
                self.current_multiplier_index += 1
                if self.current_multiplier_index >= 4 and self.global_multiplier_index + 3 < len(self.all_multipliers):
                    self.multipliers = self.all_multipliers[self.global_multiplier_index-3:self.global_multiplier_index+4]
        
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
        return self.all_multipliers[self.current_multiplier_index]

    def get_game_state_image(self, output_path, elements_folder):
        CELL_SIZE = 70
        BORDER = 3
        IMAGE_SIZE = self.size * CELL_SIZE
        MULTIPLIER_BAR_HEIGHT = 50
        
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
            'counter_bg': (40, 40, 50, 220),
            'counter_border': (80, 80, 100),
            'counter_text': (200, 200, 220),
            'counter_number': (255, 80, 80),
        }
        
        total_height = IMAGE_SIZE + MULTIPLIER_BAR_HEIGHT + 10
        img = Image.new('RGBA', (IMAGE_SIZE, total_height), COLORS['bg'])
        draw = ImageDraw.Draw(img)
        
        try:
            multiplier_font = ImageFont.truetype("arial.ttf", 16)
            bold_font = ImageFont.truetype("arialbd.ttf", 16)
        except:
            multiplier_font = ImageFont.load_default()
            bold_font = ImageFont.load_default()
        
        counter_bg_width = 60
        counter_bg_height = 30
        counter_x = IMAGE_SIZE - counter_bg_width - 10
        counter_y = 8
        
        draw.rectangle([
            counter_x, counter_y,
            counter_x + counter_bg_width, counter_y + counter_bg_height
        ], fill=COLORS['counter_bg'], outline=COLORS['counter_border'], width=1)
        
        if self.loaded_images.get('mine_icon'):
            icon_x = counter_x + 5
            icon_y = counter_y + (counter_bg_height - self.loaded_images['mine_icon'].height) // 2
            img.paste(self.loaded_images['mine_icon'], (int(icon_x), int(icon_y)), self.loaded_images['mine_icon'])
        
        mines_text = f"{self.num_mines}"
        mines_bbox = draw.textbbox((0, 0), mines_text, font=bold_font)
        mines_width = mines_bbox[2] - mines_bbox[0]
        mines_height = mines_bbox[3] - mines_bbox[1]
        mines_x = counter_x + counter_bg_width - mines_width - 8
        mines_y = counter_y + (counter_bg_height - mines_height) // 2
        
        draw.text((mines_x, mines_y), mines_text, fill=COLORS['counter_number'], font=bold_font)
        
        multiplier_bar_y = 5
        total_multipliers_width = IMAGE_SIZE * 0.75
        multiplier_width = total_multipliers_width // 7
        multiplier_start_x = 10
        
        for i in range(7):
            x1 = multiplier_start_x + i * multiplier_width
            y1 = multiplier_bar_y
            x2 = multiplier_start_x + (i + 1) * multiplier_width - 2
            y2 = multiplier_bar_y + 35
            
            if i == self.current_multiplier_index:
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
            
            multiplier_text = f"x{self.multipliers[i]:.1f}" if self.multipliers[i] < 10 else f"x{self.multipliers[i]:.0f}"
            bbox = draw.textbbox((0, 0), multiplier_text, font=multiplier_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            text_x = x1 + (multiplier_width - text_width) // 2
            text_y = y1 + (35 - text_height) // 2
            
            draw.text((text_x, text_y), multiplier_text, fill=text_color, font=multiplier_font)
        
        board_start_y = multiplier_bar_y + 45
        
        draw.rectangle([
            0, board_start_y,
            IMAGE_SIZE, board_start_y + IMAGE_SIZE
        ], fill=COLORS['grid_bg'])
        
        for i in range(self.size + 1):
            line_pos = i * CELL_SIZE
            draw.line([(0, board_start_y + line_pos), 
                      (IMAGE_SIZE, board_start_y + line_pos)], 
                     fill=COLORS['border'], width=BORDER)
            draw.line([(line_pos, board_start_y), 
                      (line_pos, board_start_y + IMAGE_SIZE)], 
                     fill=COLORS['border'], width=BORDER)
        
        for row in range(self.size):
            for col in range(self.size):
                x = col * CELL_SIZE + BORDER - 3
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
                    cell_img = self.loaded_images[f'cell_hidden_{field_number}']
                
                if cell_img:
                    img.paste(cell_img, (int(x), int(y)), cell_img)
        
        img.save(output_path, format='WEBP', quality=90, optimize=True)
        logger.info(f"Saved image: {output_path}")

class MinesPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="mines",
            results_folder=self.get_asset_path("mines", "mines_results"),
        )
        self.active_games = {}
        self.elements_folder = self.get_asset_path("mines", "board_elements")
        os.makedirs(self.results_folder, exist_ok=True)

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 1)
        if error:
            return error

        balance_before = user["balance"]

        if len(args) == 0:
            return "Commands: /mines start <bet> <bombs>, /mines <tile>, /mines cashout"

        cmd = args[0].lower()
        if cmd == "start":
            if len(args) < 3:
                return "Usage: /mines start <bet> <bombs>"
            try:
                bet = int(args[1])
                bombs = int(args[2])
            except ValueError:
                return "Invalid format - use: /mines start 100 5"
            if user_id in self.active_games:
                return "You already have an active game! Use /mines cashout or finish the game."
            if bet > balance_before:
                return f"Insufficient funds! You have {balance_before}."
            
            game = HazardMinesGame(num_mines=bombs)
            self.active_games[user_id] = {"game": game, "bet": bet, "bombs": bombs, "start_time": datetime.now()}
            new_balance = balance_before - bet
            self.update_user_balance(user_id, new_balance)
            
            img_path = os.path.join(self.results_folder, f"mines_{user_id}.webp")
            game.get_game_state_image(img_path, self.elements_folder)
            
            overlay_path, error = self.apply_user_overlay(img_path, user_id, sender, bet, 0, new_balance, user)
            if overlay_path:
                file_queue.put(overlay_path)
                
            return f"New game started!\nBet: {bet}\nMines: {bombs}\nChoose tile /mines <number> (1-25)"

        elif cmd == "cashout":
            if user_id not in self.active_games:
                return "No active game."
                
            data = self.active_games.pop(user_id)
            game = data["game"]
            bet = data["bet"]
            mult = game.get_current_multiplier()
            win = int(bet * mult)
            new_balance = balance_before + win
            self.update_user_balance(user_id, new_balance)

            img_path = os.path.join(self.results_folder, f"mines_{user_id}_cashout.webp")
            game.get_game_state_image(img_path, self.elements_folder)
            
            overlay_path, error = self.apply_user_overlay(img_path, user_id, sender, bet, win, new_balance, user)
            if overlay_path:
                file_queue.put(overlay_path)

            return f"CASHOUT! You won {win} (x{mult:.2f})"

        else:
            if user_id not in self.active_games:
                return "No active game. Use /mines start <bet> <bombs>."
                
            data = self.active_games[user_id]
            game = data["game"]
            bet = data["bet"]
            
            try:
                tiles = [int(t.strip()) for t in cmd.split(",")]
            except ValueError:
                return "Usage: /mines <tile1>[,<tile2>,...]"
                
            messages = []
            for t in tiles:
                if not (1 <= t <= 25):
                    messages.append(f"{t} out of range 1-25.")
                    continue
                    
                row, col = (t - 1) // 5, (t - 1) % 5
                safe = game.reveal(row, col)
                
                if not safe:
                    messages.append(f"BOOM! You hit a mine on tile {t}.")
                    self.active_games.pop(user_id, None)
                    
                    newLevel, newLevelProgress = self.cache.add_experience(user_id, -bet)
                    user["level"] = newLevel
                    user["level_progress"] = newLevelProgress

                    img_path = os.path.join(self.results_folder, f"mines_{user_id}_lost.webp")
                    game.get_game_state_image(img_path, self.elements_folder)
                    
                    overlay_path, error = self.apply_user_overlay(img_path, user_id, sender, bet, -bet, balance_before, user)
                    if overlay_path:
                        file_queue.put(overlay_path)
                    return "\n".join(messages)
                else:
                    mult = game.get_current_multiplier()
                    messages.append(f"Safe! x{mult:.2f}")
                    
            img_path = os.path.join(self.results_folder, f"mines_{user_id}_move.webp")
            game.get_game_state_image(img_path, self.elements_folder)
            
            overlay_path, error = self.apply_user_overlay(img_path, user_id, sender, bet, 0, balance_before, user)
            if overlay_path:
                file_queue.put(overlay_path)
                
            return "\n".join(messages)

def register():
    plugin = MinesPlugin()
    return {
        "name": "mines",
        "aliases": ["/m"],
        "description": "Mines game: /mines start <bet> <bombs> /mines <tile> /mines cashout",
        "execute": plugin.execute_game
    }