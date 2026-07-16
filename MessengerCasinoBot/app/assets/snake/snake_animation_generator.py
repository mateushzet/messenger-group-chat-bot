import os
import random
import json
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List, Set
from PIL import Image, ImageDraw, ImageFont
from logger import logger

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_PATH = os.path.join(BASE_DIR, "assets", "snake")
FONT_PATH = os.path.join(BASE_DIR, "DejaVuSans.ttf")
FONT_BOLD_PATH = os.path.join(BASE_DIR, "DejaVuSans-Bold.ttf")

_DICE_SUM_PROB_ORDER_RARE_TO_COMMON = [2, 12, 3, 11, 4, 10, 5, 9, 6, 8, 7]
_DICE_SUMS = list(range(2, 13))

def _roll_2d6() -> Tuple[int, int, int]:
    d1 = random.randint(1, 6)
    d2 = random.randint(1, 6)
    return d1, d2, d1 + d2

def _format_mult(value: float) -> str:
    return f"{value:.2f}x"

@dataclass
class SnakesDifficulty:
    key: str
    min_mult: float
    max_mult: float
    snakes: int

_DIFFICULTIES: Dict[str, SnakesDifficulty] = {
    "easy": SnakesDifficulty("easy", 1.01, 2.00, 1),
    "medium": SnakesDifficulty("medium", 1.11, 4.00, 3),
    "hard": SnakesDifficulty("hard", 1.38, 7.50, 5),
    "expert": SnakesDifficulty("expert", 3.82, 10.00, 7),
    "master": SnakesDifficulty("master", 17.64, 18.00, 9),
}

class SnakesGame:
    TOTAL_ROUNDS = 5

    def __init__(self, bet: int, difficulty: SnakesDifficulty):
        self.bet = bet
        self.difficulty = difficulty
        self.round_index = 0
        self.cumulative_multiplier = 1.0
        self.last_roll: Optional[Tuple[int, int, int]] = None
        self.last_sum: Optional[int] = None
        self.last_outcome: Optional[str] = None
        self.last_multiplier: Optional[float] = None
        self.last_table_round_index: int = 0

    def is_finished(self) -> bool:
        return self.round_index >= self.TOTAL_ROUNDS or self.last_outcome == "snake"

    def distinct_multiplier_count(self) -> int:
        return (11 - self.difficulty.snakes) // 2

    def _generate_distinct_multipliers(self) -> List[float]:
        if self.difficulty.key == "easy":
            return [2.00, 1.30, 1.20, 1.10, 1.01]

        k = self.distinct_multiplier_count()
        if k <= 1:
            return [self.difficulty.max_mult]

        min_m = self.difficulty.min_mult
        max_m = self.difficulty.max_mult

        values: List[float] = []
        for i in range(k):
            t = i / (k - 1)
            v = max_m * ((min_m / max_m) ** t)
            values.append(round(v + 1e-9, 2))

        values[0] = round(max_m, 2)
        values[-1] = round(min_m, 2)
        return values

    def build_outcome_map(self) -> Dict[int, Optional[float]]:
        snakes = self.difficulty.snakes
        distinct = self._generate_distinct_multipliers()
        multipliers: List[float] = []
        for v in distinct:
            multipliers.extend([v, v])

        if len(multipliers) != (11 - snakes):
            raise ValueError("Invalid multiplier table size")

        rare_to_common = _DICE_SUM_PROB_ORDER_RARE_TO_COMMON
        snake_sums = set(rare_to_common[-snakes:])
        remaining_sums = [s for s in rare_to_common if s not in snake_sums]

        outcome: Dict[int, Optional[float]] = {}
        for s in snake_sums:
            outcome[s] = None

        multipliers_sorted = sorted(multipliers, reverse=True)
        for s, m in zip(remaining_sums, multipliers_sorted):
            outcome[s] = m

        for s in _DICE_SUMS:
            outcome.setdefault(s, distinct[-1])
        return outcome

    def roll(self) -> Dict:
        if self.is_finished():
            return {"ok": False, "error": "Game already finished"}

        d1, d2, s = _roll_2d6()
        outcomes = self.build_outcome_map()
        m = outcomes.get(s)

        self.last_roll = (d1, d2, s)
        self.last_sum = s

        if m is None:
            self.last_outcome = "snake"
            self.last_multiplier = None
            return {
                "ok": True,
                "dice": (d1, d2),
                "sum": s,
                "outcome": "snake",
                "round_index": self.round_index,
                "cumulative_multiplier": self.cumulative_multiplier,
            }

        self.last_outcome = "multiplier"
        self.last_multiplier = float(m)
        self.round_index += 1
        self.cumulative_multiplier = round(self.cumulative_multiplier * float(m), 4)

        return {
            "ok": True,
            "dice": (d1, d2),
            "sum": s,
            "outcome": "multiplier",
            "multiplier": float(m),
            "round_index": self.round_index,
            "cumulative_multiplier": self.cumulative_multiplier,
            "is_maxed": self.round_index >= self.TOTAL_ROUNDS,
        }

    def current_payout(self) -> int:
        return int(round(self.bet * self.cumulative_multiplier))

class SnakesAnimationGenerator:
    def __init__(self, text_renderer=None):
        self.text_renderer = text_renderer
        
        self.WIDTH = 270
        self.HEIGHT = 330
        self.tile_size = 50
        self.tile_gap = 4
        self.dice_size = 30

        self._load_assets()
        self._load_fonts()
        
        self.board_width = 4 * self.tile_size + 3 * self.tile_gap
        self.board_height = 4 * self.tile_size + 3 * self.tile_gap
        
        self.board_x0 = (self.WIDTH - self.board_width) // 2
        self.board_y0 = 50
        
        self.dice_holder_width = 108
        self.dice_holder_height = 50
        dice_holder_x = (self.board_x0 + 1 * (self.tile_size + self.tile_gap)) + 28
        dice_holder_y = self.board_y0 + 1 * (self.tile_size + self.tile_gap) + 8
        self.dice_holder_pos = (dice_holder_x - 29, dice_holder_y - 8)
        
        self.dice_size = 40
        self.dice1_pos = (dice_holder_x + 5 - 18, dice_holder_y) 
        self.dice2_pos = (dice_holder_x + self.tile_size + self.tile_gap + 5 - 28, dice_holder_y)
        
        self.multiplier_holder_width = 108
        self.multiplier_holder_height = 50
        multiplier_holder_x = (self.board_x0 + 1 * (self.tile_size + self.tile_gap)) - 1
        multiplier_holder_y = self.board_y0 + 2 * (self.tile_size + self.tile_gap) + 8
        self.multiplier_holder_pos = (multiplier_holder_x, multiplier_holder_y - 8)
        
        self.path_order = [
            (0, 0),
            (0, 1),
            (0, 2),
            (0, 3),
            (1, 3),
            (2, 3),
            (3, 3),
            (3, 2),
            (3, 1),
            (3, 0),
            (2, 0),
            (1, 0),
        ]
        
        self.sum_to_path_index = {
            2: 1,
            3: 2,
            4: 3,
            5: 4,
            6: 5,
            7: 6,
            8: 7,
            9: 8,
            10: 9,
            11: 10,
            12: 11,
        }
        
        self.sum_to_pos = {
            2: (0, 1),
            3: (0, 2),
            4: (0, 3),
            5: (1, 3),
            6: (2, 3),
            7: (3, 3),
            8: (3, 2),
            9: (3, 1),
            10: (3, 0),
            11: (2, 0),
            12: (1, 0),
        }
        
        self.pos_to_path_index = {pos: i for i, pos in enumerate(self.path_order)}
    
    def _load_fonts(self):
        self.font_small = None
        self.font_medium = None
        self.font_large = None
        
        try:
            if os.path.exists(FONT_PATH):
                self.font_small = ImageFont.truetype(FONT_PATH, 12)
                self.font_medium = ImageFont.truetype(FONT_PATH, 16)
                self.font_large = ImageFont.truetype(FONT_PATH, 18)
                logger.info(f"[Snakes] Loaded fonts from {FONT_PATH}")
            else:
                logger.warning(f"[Snakes] Font not found: {FONT_PATH}")
        except Exception as e:
            logger.error(f"[Snakes] Error loading fonts: {e}")
    
    def _load_assets(self):
        assets_path = ASSETS_PATH
        
        self.board_bg_color = (16, 15, 22, 255)
        
        if not os.path.exists(assets_path):
            logger.warning(f"[Snakes] Assets not found at {assets_path}, using placeholders")
            os.makedirs(assets_path, exist_ok=True)
        
        items_holder_path = os.path.join(assets_path, "items_holder.png")
        if os.path.exists(items_holder_path):
            self.items_holder = Image.open(items_holder_path).convert('RGBA')
            logger.info(f"[Snakes] Loaded items_holder")
        else:
            self.items_holder = Image.new('RGBA', (108, 50), (30, 40, 50, 200))
            logger.warning(f"[Snakes] items_holder.png not found, using placeholder")
        
        self.dice_images = {}
        for i in range(0, 7):
            dice_path = os.path.join(assets_path, f"dice_{i}.png")
            if os.path.exists(dice_path):
                img = Image.open(dice_path).convert('RGBA')
                img = img.resize((self.dice_size, self.dice_size))
                self.dice_images[i] = img
            else:
                img = Image.new('RGBA', (self.dice_size, self.dice_size), (50, 50, 50, 200))
                draw = ImageDraw.Draw(img)
                draw.rectangle([0, 0, self.dice_size-1, self.dice_size-1], outline=(200, 200, 200), width=2)
                if i > 0:
                    try:
                        font = ImageFont.truetype(FONT_PATH, 20) if os.path.exists(FONT_PATH) else None
                        draw.text((self.dice_size//2-8, self.dice_size//2-12), str(i), fill=(255, 255, 255), font=font)
                    except:
                        draw.text((self.dice_size//2-8, self.dice_size//2-12), str(i), fill=(255, 255, 255))
                self.dice_images[i] = img
        
        self.tale_images = {}
        tale_names = ['clear_tale', 'snake_tale', 'start_tale']
        for name in tale_names:
            normal_path = os.path.join(assets_path, f"{name}.png")
            active_path = os.path.join(assets_path, f"{name}_active.png")
            
            if os.path.exists(normal_path):
                img = Image.open(normal_path).convert('RGBA')
                img = img.resize((self.tile_size, self.tile_size))
                self.tale_images[f"{name}_normal"] = img
            else:
                img = Image.new('RGBA', (self.tile_size, self.tile_size), (40, 50, 60, 200))
                draw = ImageDraw.Draw(img)
                draw.rectangle([0, 0, self.tile_size-1, self.tile_size-1], outline=(100, 100, 100), width=1)
                self.tale_images[f"{name}_normal"] = img
            
            if os.path.exists(active_path):
                img = Image.open(active_path).convert('RGBA')
                img = img.resize((self.tile_size, self.tile_size))
                self.tale_images[f"{name}_active"] = img
            else:
                img = Image.new('RGBA', (self.tile_size, self.tile_size), (100, 150, 80, 200))
                draw = ImageDraw.Draw(img)
                draw.rectangle([0, 0, self.tile_size-1, self.tile_size-1], outline=(200, 200, 100), width=2)
                self.tale_images[f"{name}_active"] = img
        
        logger.info(f"[Snakes] Loaded {len(self.tale_images)} tale images")
    
    def create_base_image(self, user_background_path=None) -> Image.Image:
        img = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
        
        draw = ImageDraw.Draw(img)
        board_rect = [
            self.board_x0 - 10, self.board_y0 - 10,
            self.board_x0 + self.board_width + 10, self.board_y0 + self.board_height + 10
        ]
        draw.rounded_rectangle(board_rect, radius=10, fill=self.board_bg_color, outline=(30, 40, 50, 255), width=2)
        
        return img
    
    def draw_text(self, img, x, y, text, font_size=16, color=(255, 255, 255, 255)):
        if self.text_renderer:
            text_img = self.text_renderer.render_text(text, font_size=font_size, color=color)
            img.paste(text_img, (x, y), text_img)
        else:
            draw = ImageDraw.Draw(img)
            try:
                if font_size <= 12 and self.font_small:
                    font = self.font_small
                elif font_size <= 16 and self.font_medium:
                    font = self.font_medium
                elif self.font_large:
                    font = self.font_large
                else:
                    font = None
                draw.text((x, y), text, fill=color, font=font)
            except:
                draw.text((x, y), text, fill=color)
    
    def draw_board(self, img, game: SnakesGame, highlight_positions=None):
        outcomes = game.build_outcome_map()
        
        for r in range(4):
            for c in range(4):
                x = self.board_x0 + c * (self.tile_size + self.tile_gap)
                y = self.board_y0 + r * (self.tile_size + self.tile_gap)
                
                is_dice_holder = (r == 1 and c in (1, 2))
                is_multiplier_holder = (r == 2 and c in (1, 2))
                
                if is_dice_holder or is_multiplier_holder:
                    continue
                
                s = None
                for sum_val, pos in self.sum_to_pos.items():
                    if pos == (r, c):
                        s = sum_val
                        break
                
                is_highlight = highlight_positions and (r, c) in highlight_positions
                
                if (r, c) == (0, 0):
                    tale_key = 'start_tale_active' if is_highlight else 'start_tale_normal'
                elif s and outcomes.get(s) is None:
                    tale_key = 'snake_tale_active' if is_highlight else 'snake_tale_normal'
                else:
                    tale_key = 'clear_tale_active' if is_highlight else 'clear_tale_normal'
                
                tale_img = self.tale_images.get(tale_key)
                if tale_img:
                    img.paste(tale_img, (x, y), tale_img)
                
                if s and outcomes.get(s) is not None and (r, c) != (0, 0):
                    mult_text = _format_mult(float(outcomes[s]))
                    text_x = x + (self.tile_size // 2) - 16
                    text_y = y + (self.tile_size // 2) - 8
                    self.draw_text(img, text_x, text_y, mult_text, 12, (255, 255, 255, 255))
    
    def draw_dice_center(self, img, game: SnakesGame, frame_idx=0, is_rolling=False):
        if self.items_holder:
            holder_resized = self.items_holder.resize((self.dice_holder_width, self.dice_holder_height))
            img.paste(holder_resized, self.dice_holder_pos, holder_resized)
        
        if game.last_roll and not is_rolling:
            d1, d2, _ = game.last_roll
            self._draw_dice(img, d1, self.dice1_pos[0], self.dice1_pos[1])
            self._draw_dice(img, d2, self.dice2_pos[0], self.dice2_pos[1])
        elif is_rolling:
            dice1_value = ((frame_idx // 2) % 6) + 1
            dice2_value = ((frame_idx // 3) % 6) + 1
            self._draw_dice(img, dice1_value, self.dice1_pos[0], self.dice1_pos[1])
            self._draw_dice(img, dice2_value, self.dice2_pos[0], self.dice2_pos[1])
        else:
            self._draw_dice(img, 0, self.dice1_pos[0], self.dice1_pos[1])
            self._draw_dice(img, 0, self.dice2_pos[0], self.dice2_pos[1])
    
    def _draw_dice(self, img, value, x, y):
        dice_img = self.dice_images.get(value)
        if dice_img:
            img.paste(dice_img, (x, y), dice_img)
        
    def draw_multiplier_center(self, img, game: SnakesGame, multiplier_color=None):
        if self.items_holder:
            holder_resized = self.items_holder.resize((self.multiplier_holder_width, self.multiplier_holder_height))
            img.paste(holder_resized, self.multiplier_holder_pos, holder_resized)
        
        mult_text = _format_mult(game.cumulative_multiplier)
        text_x = self.multiplier_holder_pos[0] + 30
        text_y = self.multiplier_holder_pos[1] + 15
        
        if multiplier_color:
            color = multiplier_color
        else:
            if game.last_outcome == "snake":
                color = (255, 80, 80, 255)
            elif game.last_outcome == "multiplier":
                color = (80, 255, 80, 255)
            else:
                color = (170, 220, 190, 255)
        
        self.draw_text(img, text_x, text_y, mult_text, 18, color)
        
    def draw_progress_dots(self, img, game: SnakesGame, show_round: int = None):
        draw = ImageDraw.Draw(img)
        
        dots_y = self.board_y0 + self.board_height + 15
        dot_r = 6
        dot_gap = 15
        total_width = SnakesGame.TOTAL_ROUNDS * (2 * dot_r + dot_gap) - dot_gap
        start_x = self.board_x0 + (self.board_width - total_width) // 2
        
        if show_round is None:
            show_round = game.round_index
        
        for i in range(SnakesGame.TOTAL_ROUNDS):
            cx = start_x + i * (2 * dot_r + dot_gap) + dot_r
            cy = dots_y + dot_r
            filled = (i + 1) <= show_round
            fill = (55, 149, 255, 255) if filled else (70, 85, 100, 255)
            draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=fill)
            self.draw_text(img, cx - 3, cy - 5, str(i + 1), 9, (255, 255, 255, 200))
    
    def get_path_positions_to_target(self, target_sum: int) -> List[Tuple[int, int]]:
        target_idx = self.sum_to_path_index.get(target_sum, -1)
        
        if target_idx == -1:
            return [(0, 0)]
        
        positions = []
        for i in range(target_idx + 1):
            positions.append(self.path_order[i])
        return positions

    def generate_animation_frames(self, game: SnakesGame, action_type: str, 
                                user_background_path=None, old_game_state: SnakesGame = None,
                                show_round: int = None) -> Optional[List[Image.Image]]:
        frames = []
        
        ANIMATION_LENGTH = 15
        HOLD_FRAMES = 8
        PATH_FRAMES = 2
        
        default_color = (170, 220, 190, 255)
        
        if action_type in ['start', 'roll']:
            if action_type == 'start':
                original_multiplier = game.cumulative_multiplier
                game.cumulative_multiplier = 1.0
                old_state = None
                multiplier_color = (170, 220, 190, 255)
                if show_round is None:
                    show_round = 1
            else:
                old_state = old_game_state
                if game.last_outcome == "snake":
                    multiplier_color = (255, 80, 80, 255)
                else:
                    multiplier_color = (80, 255, 80, 255)
                if show_round is None:
                    show_round = game.round_index
            
            for frame_idx in range(ANIMATION_LENGTH):
                img = self.create_base_image(user_background_path)
                
                if old_state:
                    self.draw_board(img, old_state, highlight_positions=[])
                else:
                    self.draw_board(img, game)
                
                self.draw_dice_center(img, game, frame_idx=frame_idx, is_rolling=True)
                
                if old_state:
                    temp_mult = game.cumulative_multiplier
                    game.cumulative_multiplier = old_state.cumulative_multiplier
                    self.draw_multiplier_center(img, old_state, default_color)
                    game.cumulative_multiplier = temp_mult
                    self.draw_progress_dots(img, old_state, show_round)
                else:
                    self.draw_multiplier_center(img, game, default_color)
                    self.draw_progress_dots(img, game, show_round)
                
                frames.append(img)
            
            target_sum = game.last_sum
            path_positions = self.get_path_positions_to_target(target_sum)
            
            for pos in path_positions:
                for _ in range(PATH_FRAMES):
                    img = self.create_base_image(user_background_path)
                    
                    self.draw_board(img, game, highlight_positions=[pos])
                    self.draw_dice_center(img, game, is_rolling=False)
                    
                    if old_state:
                        temp_mult = game.cumulative_multiplier
                        game.cumulative_multiplier = old_state.cumulative_multiplier
                        self.draw_multiplier_center(img, game, default_color)
                        game.cumulative_multiplier = temp_mult
                    else:
                        self.draw_multiplier_center(img, game, default_color)
                    
                    self.draw_progress_dots(img, game, show_round)
                    frames.append(img)
            
            if action_type == 'start':
                game.cumulative_multiplier = original_multiplier
            
            target_pos = self.sum_to_pos.get(target_sum, (0, 0))
            for _ in range(HOLD_FRAMES):
                img = self.create_base_image(user_background_path)
                self.draw_board(img, game, highlight_positions=[target_pos])
                self.draw_dice_center(img, game, is_rolling=False)
                self.draw_multiplier_center(img, game, multiplier_color)
                self.draw_progress_dots(img, game, show_round)
                frames.append(img)
        
        return frames if frames else None

    def save_animation(self, frames: List[Image.Image], filepath: str) -> bool:
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            if frames:
                frames[0].save(
                    filepath,
                    format='WEBP',
                    save_all=True,
                    append_images=frames[1:],
                    duration=50,
                    loop=0,
                    quality=85
                )
                return True
        except Exception as e:
            logger.error(f"[Snakes] Error saving animation {filepath}: {e}")
        return False

class SnakesAnimationPreGenerator:
    def __init__(self, text_renderer=None, base_path='pre_generated_animations'):
        self.text_renderer = text_renderer
        self.base_path = base_path
        self.generator = SnakesAnimationGenerator(text_renderer)
        self.animation_cache = {}
        self.metadata = {}
        
        self.animation_counts = {
            'easy': [141, 128, 116, 106, 96],
            'medium': [113, 82, 59, 43, 31],
            'hard': [84, 46, 25, 13, 7],
            'expert': [56, 20, 7, 2, 1],
            'master': [28, 5, 1, 1, 1]
        }
        
        self.sum_probabilities = {
            2: 1/36, 3: 2/36, 4: 3/36, 5: 4/36, 6: 5/36,
            7: 6/36, 8: 5/36, 9: 4/36, 10: 3/36, 11: 2/36, 12: 1/36
        }
        
        os.makedirs(self.base_path, exist_ok=True)
        
    def pre_generate_all(self):
        logger.info("[Snakes] Starting pre-generation of all animations...")
        total_generated = 0
        
        for difficulty in self.animation_counts.keys():
            count = self.pre_generate_difficulty(difficulty)
            total_generated += count
            logger.info(f"[Snakes] Generated {count} animations for {difficulty}")
        
        self._save_metadata()
        logger.info(f"[Snakes] Pre-generation complete! Total: {total_generated} animations")
        return total_generated
            
    def pre_generate_difficulty(self, difficulty: str) -> int:
        counts = self.animation_counts[difficulty]
        difficulty_path = os.path.join(self.base_path, difficulty)
        difficulty_obj = _DIFFICULTIES[difficulty]
        
        total = 0
        
        for round_num in range(1, 6):
            total += self._generate_round_animations(
                difficulty_obj, 
                difficulty_path, 
                round_num, 
                counts[round_num - 1]
            )
        
        return total
    
    def _get_outcome_map_for_difficulty(self, difficulty_obj: SnakesDifficulty) -> Dict[int, Optional[float]]:
        temp_game = SnakesGame(bet=100, difficulty=difficulty_obj)
        return temp_game.build_outcome_map()
    
    def _get_previous_multipliers(self, difficulty_obj: SnakesDifficulty, round_num: int) -> List[float]:
        if round_num <= 1:
            return [1.0]
            
        possible_mults = set()
        self._simulate_paths(difficulty_obj, round_num - 1, 1.0, possible_mults)
        return sorted(possible_mults)
    
    def _simulate_paths(self, difficulty_obj: SnakesDifficulty, remaining_rounds: int, 
                        current_mult: float, results: Set[float]):
        if remaining_rounds == 0:
            results.add(round(current_mult, 4))
            return
            
        outcome_map = self._get_outcome_map_for_difficulty(difficulty_obj)
        for sum_val, mult in outcome_map.items():
            if mult is not None:
                new_mult = round(current_mult * mult, 4)
                self._simulate_paths(
                    difficulty_obj, 
                    remaining_rounds - 1, 
                    new_mult, 
                    results
                )
    
    def _select_sums_proportionally(self, count: int) -> List[int]:
        if count >= 11:
            return list(range(2, 13))
            
        sums = list(self.sum_probabilities.keys())
        weights = list(self.sum_probabilities.values())
        
        total = sum(weights)
        weights = [w / total for w in weights]
        
        selected = []
        available = list(zip(sums, weights))
        
        for _ in range(min(count, len(available))):
            if not available:
                break
            chosen_idx = random.choices(range(len(available)), weights=[w for _, w in available])[0]
            chosen_sum, _ = available.pop(chosen_idx)
            selected.append(chosen_sum)
        
        return selected
    
    def _generate_round_animations(self, difficulty_obj: SnakesDifficulty, path: str, 
                                   round_num: int, count: int) -> int:
        generated = 0
        outcome_map = self._get_outcome_map_for_difficulty(difficulty_obj)
        
        previous_multipliers = self._get_previous_multipliers(difficulty_obj, round_num)
        
        if not previous_multipliers:
            previous_multipliers = [1.0]
        
        per_state = max(1, count // len(previous_multipliers))
        
        for prev_mult in previous_multipliers[:10]:
            sums = self._select_sums_proportionally(min(per_state, 11))
            
            for sum_val in sums:
                new_multiplier = outcome_map.get(sum_val)
                
                if new_multiplier is None:
                    old_game = SnakesGame(bet=100, difficulty=difficulty_obj)
                    old_game.round_index = round_num - 1
                    old_game.cumulative_multiplier = prev_mult
                    old_game.last_sum = sum_val - 1 if sum_val > 2 else 12
                    old_game.last_roll = self._get_dice_for_sum(old_game.last_sum)
                    
                    new_game = SnakesGame(bet=100, difficulty=difficulty_obj)
                    new_game.round_index = round_num - 1
                    new_game.cumulative_multiplier = prev_mult
                    new_game.last_sum = sum_val
                    new_game.last_roll = self._get_dice_for_sum(sum_val)
                    new_game.last_outcome = 'snake'
                    new_game.last_multiplier = None
                    
                    frames = self.generator.generate_animation_frames(
                        new_game, 'roll',
                        user_background_path=None,
                        old_game_state=old_game,
                        show_round=round_num
                    )
                    
                    if frames:
                        filename = f"round{round_num}_sum{sum_val}_snake_{prev_mult:.2f}x.webp"
                        filepath = os.path.join(path, filename)
                        
                        if self.generator.save_animation(frames, filepath):
                            generated += 1
                            key = f"{difficulty_obj.key}_round{round_num}_sum{sum_val}_snake"
                            self.animation_cache[key] = filepath
                            self.metadata[key] = {
                                'difficulty': difficulty_obj.key,
                                'round': round_num,
                                'sum': sum_val,
                                'prev_mult': prev_mult,
                                'next_mult': 0,
                                'outcome': 'snake',
                                'filepath': filepath
                            }
                else:
                    next_mult = round(prev_mult * new_multiplier, 4)
                    
                    old_game = SnakesGame(bet=100, difficulty=difficulty_obj)
                    old_game.round_index = round_num - 1
                    old_game.cumulative_multiplier = prev_mult
                    old_game.last_sum = sum_val - 1 if sum_val > 2 else 12
                    old_game.last_roll = self._get_dice_for_sum(old_game.last_sum)
                    
                    new_game = SnakesGame(bet=100, difficulty=difficulty_obj)
                    new_game.round_index = round_num
                    new_game.cumulative_multiplier = next_mult
                    new_game.last_sum = sum_val
                    new_game.last_roll = self._get_dice_for_sum(sum_val)
                    new_game.last_outcome = 'multiplier'
                    new_game.last_multiplier = new_multiplier
                    
                    frames = self.generator.generate_animation_frames(
                        new_game, 'roll',
                        user_background_path=None,
                        old_game_state=old_game,
                        show_round=round_num
                    )
                    
                    if frames:
                        filename = f"round{round_num}_sum{sum_val}_mult_{prev_mult:.2f}x_to_{next_mult:.2f}x.webp"
                        filepath = os.path.join(path, filename)
                        
                        if self.generator.save_animation(frames, filepath):
                            generated += 1
                            key = f"{difficulty_obj.key}_round{round_num}_sum{sum_val}"
                            self.animation_cache[key] = filepath
                            self.metadata[key] = {
                                'difficulty': difficulty_obj.key,
                                'round': round_num,
                                'sum': sum_val,
                                'prev_mult': prev_mult,
                                'next_mult': next_mult,
                                'multiplier': new_multiplier,
                                'outcome': 'multiplier',
                                'filepath': filepath
                            }
        
        logger.info(f"[Snakes] Generated {generated} animations for {difficulty_obj.key} round {round_num}")
        return generated
    
    def _get_dice_for_sum(self, sum_val: int) -> Tuple[int, int, int]:
        if sum_val < 2 or sum_val > 12:
            return (1, 1, 2)
        
        combinations = []
        for d1 in range(1, 7):
            for d2 in range(1, 7):
                if d1 + d2 == sum_val:
                    combinations.append((d1, d2))
        
        if combinations:
            d1, d2 = random.choice(combinations)
            return (d1, d2, sum_val)
        
        return (1, 1, 2)
    
    def get_animation_path(self, difficulty: str, round_num: int, sum_val: int, 
                          outcome: str = 'multiplier') -> Optional[str]:
        if outcome == 'snake':
            key = f"{difficulty}_round{round_num}_sum{sum_val}_snake"
        else:
            key = f"{difficulty}_round{round_num}_sum{sum_val}"
        
        if key in self.animation_cache:
            return self.animation_cache[key]
        
        if key in self.metadata:
            filepath = self.metadata[key]['filepath']
            if os.path.exists(filepath):
                self.animation_cache[key] = filepath
                return filepath
        
        return None
    
    def _save_metadata(self):
        metadata_path = os.path.join(self.base_path, 'metadata.json')
        try:
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            logger.info(f"[Snakes] Metadata saved to {metadata_path}")
        except Exception as e:
            logger.error(f"[Snakes] Error saving metadata: {e}")

def main():
    print("=" * 60)
    print("SNAKES ANIMATION PRE-GENERATOR")
    print("=" * 60)
    print(f"\nAssets path: {ASSETS_PATH}")
    print(f"Fonts path: {FONT_PATH}")
    
    generator = SnakesAnimationPreGenerator(
        text_renderer=None,
        base_path='pre_generated_animations'
    )
    
    print("\nStarting pre-generation...")
    print(f"Animations will be saved to: {generator.base_path}")
    print("\nAnimation counts per difficulty:")
    
    for diff, counts in generator.animation_counts.items():
        print(f"  {diff.upper()}: {sum(counts)} total (rounds: {counts})")
    
    print("\n" + "-" * 60)
    
    total = generator.pre_generate_all()
    
    print("\n" + "=" * 60)
    print(f"PRE-GENERATION COMPLETE!")
    print(f"Total animations generated: {total}")
    print(f"Location: {os.path.abspath(generator.base_path)}")
    print("=" * 60)
    
    print("\nSummary by difficulty:")
    for difficulty in generator.animation_counts.keys():
        path = os.path.join(generator.base_path, difficulty)
        count = 0
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                count += len([f for f in files if f.endswith('.webp')])
        print(f"  {difficulty.upper()}: {count} files")
    
    print("\nDone!")

if __name__ == "__main__":
    main()