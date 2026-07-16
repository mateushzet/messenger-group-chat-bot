import os
import random
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List

from PIL import Image, ImageDraw

from base_game_plugin import BaseGamePlugin
from logger import logger
from plugins.weekly import record_weekly_win


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

    def _generate_distinct_multipliers(self, table_round_index: int) -> List[float]:
        if self.difficulty.key == "easy":
            return [2.00, 1.30, 1.20, 1.10, 1.01]

        k = self.distinct_multiplier_count()
        if k <= 1:
            return [self.difficulty.max_mult]

        min_m = self.difficulty.min_mult
        max_m = self.difficulty.max_mult

        drift = (table_round_index) * (max_m - min_m) * 0.01
        stage_min = min(max_m, max(min_m, min_m + drift))

        values: List[float] = []
        for i in range(k):
            t = i / (k - 1)
            v = max_m * ((stage_min / max_m) ** t)
            values.append(round(v + 1e-9, 2))

        values[0] = round(max_m, 2)
        values[-1] = round(stage_min, 2)
        return values

    def build_outcome_map(self, table_round_index: Optional[int] = None) -> Dict[int, Optional[float]]:
        snakes = self.difficulty.snakes
        if table_round_index is None:
            table_round_index = self.round_index
        distinct = self._generate_distinct_multipliers(table_round_index=table_round_index)
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
        self.last_table_round_index = self.round_index
        outcomes = self.build_outcome_map(table_round_index=self.last_table_round_index)
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

    def serialize(self) -> Dict:
        return {
            "bet": int(self.bet),
            "difficulty": str(self.difficulty.key),
            "round_index": int(self.round_index),
            "cumulative_multiplier": float(self.cumulative_multiplier),
            "last_roll": list(self.last_roll) if self.last_roll else None,
            "last_sum": int(self.last_sum) if self.last_sum is not None else None,
            "last_outcome": self.last_outcome,
            "last_multiplier": float(self.last_multiplier) if self.last_multiplier is not None else None,
            "last_table_round_index": int(self.last_table_round_index),
        }

    @classmethod
    def deserialize(cls, data: Dict) -> "SnakesGame":
        bet = int(data.get("bet", 0))
        difficulty_key = str(data.get("difficulty", "medium")).lower()
        difficulty = _DIFFICULTIES.get(difficulty_key, _DIFFICULTIES["medium"])
        game = cls(bet=bet, difficulty=difficulty)
        game.round_index = int(data.get("round_index", 0))
        game.cumulative_multiplier = float(data.get("cumulative_multiplier", 1.0))
        last_roll = data.get("last_roll")
        game.last_roll = tuple(last_roll) if isinstance(last_roll, (list, tuple)) and len(last_roll) == 3 else None
        game.last_sum = data.get("last_sum")
        game.last_sum = int(game.last_sum) if game.last_sum is not None else None
        game.last_outcome = data.get("last_outcome")
        game.last_multiplier = data.get("last_multiplier")
        game.last_multiplier = float(game.last_multiplier) if game.last_multiplier is not None else None
        game.last_table_round_index = int(data.get("last_table_round_index", game.round_index))
        return game


class SnakesAnimationGenerator:
    def __init__(self, text_renderer):
        self.text_renderer = text_renderer
        
        self.WIDTH = 270
        self.HEIGHT = 330
        self.tile_size = 50
        self.tile_gap = 4
        self.dice_size = 30

        self._load_assets()
        
        self.board_width = 4 * self.tile_size + 3 * self.tile_gap
        self.board_height = 4 * self.tile_size + 3 * self.tile_gap
        
        self.board_x0 = (self.WIDTH - self.board_width) // 2
        self.board_y0 = 50
        
        self.dice_holder_width = 108
        self.dice_holder_height = 50
        dice_holder_x = (self.board_x0 + 1 * (self.tile_size + self.tile_gap)) + 28
        dice_holder_y = self.board_y0 + 1 * (self.tile_size + self.tile_gap) + 8
        self.dice_holder_pos = (dice_holder_x - 29, dice_holder_y - 8)
        
        self.multiplier_color = (170, 220, 190, 255)

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
            (0, 1), (0, 2), (0, 3),
            (1, 3), (2, 3), (3, 3),
            (3, 2), (3, 1), (3, 0),
            (2, 0), (1, 0),
        ]
        
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
    
    def _load_assets(self):
        assets_path = os.path.join(os.path.dirname(__file__), "..", "assets", "snake")
        
        self.board_bg_color = (16, 15, 22, 255)
        
        items_holder_path = os.path.join(assets_path, "items_holder.png")
        if os.path.exists(items_holder_path):
            self.items_holder = Image.open(items_holder_path).convert('RGBA')
            logger.info(f"[Snakes] Loaded items_holder")
        else:
            self.items_holder = None
        
        self.dice_images = {}
        for i in range(0, 7):
            dice_path = os.path.join(assets_path, f"dice_{i}.png")
            if os.path.exists(dice_path):
                img = Image.open(dice_path).convert('RGBA')
                img = img.resize((self.dice_size, self.dice_size))
                self.dice_images[i] = img
                logger.info(f"[Snakes] Loaded dice_{i}")
            else:
                self.dice_images[i] = None
        
        self.tale_images = {}
        tale_names = ['clear_tale', 'snake_tale', 'start_tale']
        for name in tale_names:
            normal_path = os.path.join(assets_path, f"{name}.png")
            active_path = os.path.join(assets_path, f"{name}_active.png")
            
            if os.path.exists(normal_path):
                img = Image.open(normal_path).convert('RGBA')
                img = img.resize((self.tile_size, self.tile_size))
                self.tale_images[f"{name}_normal"] = img
            if os.path.exists(active_path):
                img = Image.open(active_path).convert('RGBA')
                img = img.resize((self.tile_size, self.tile_size))
                self.tale_images[f"{name}_active"] = img
        
        logger.info(f"[Snakes] Loaded {len(self.tale_images)} tale images")
    
    def create_base_image(self, user_background_path=None) -> Image.Image:
        if user_background_path and os.path.exists(user_background_path):
            try:
                bg = Image.open(user_background_path).convert('RGBA')
                bg = bg.resize((self.WIDTH, self.HEIGHT))
                img = bg
            except Exception as e:
                logger.error(f"[Snakes] Error loading background: {e}")
                img = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (13, 23, 32, 255))
        else:
            img = Image.new('RGBA', (self.WIDTH, self.HEIGHT), (13, 23, 32, 255))
        
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
            dice1_value = random.randint(1, 6)
            dice2_value = random.randint(1, 6)
            self._draw_dice(img, dice1_value, self.dice1_pos[0], self.dice1_pos[1])
            self._draw_dice(img, dice2_value, self.dice2_pos[0], self.dice2_pos[1])
        else:
            self._draw_dice(img, 0, self.dice1_pos[0], self.dice1_pos[1])
            self._draw_dice(img, 0, self.dice2_pos[0], self.dice2_pos[1])
    
    def _draw_dice(self, img, value, x, y):
        dice_img = self.dice_images.get(value)
        if dice_img:
            img.paste(dice_img, (x, y), dice_img)
        
    def draw_multiplier_center(self, img, game: SnakesGame):
        if self.items_holder:
            holder_resized = self.items_holder.resize((self.multiplier_holder_width, self.multiplier_holder_height))
            img.paste(holder_resized, self.multiplier_holder_pos, holder_resized)
        
        mult_text = _format_mult(game.cumulative_multiplier)
        text_x = self.multiplier_holder_pos[0] + 30
        text_y = self.multiplier_holder_pos[1] + 15
        
        if hasattr(self, 'multiplier_color'):
            color = self.multiplier_color
        else:
            if game.last_outcome == "snake":
                color = (255, 80, 80, 255)
            elif game.last_outcome == "multiplier":
                color = (80, 255, 80, 255)
            else:
                color = (170, 220, 190, 255)
        
        self.draw_text(img, text_x, text_y, mult_text, 18, color)
        
    def draw_progress_dots(self, img, game: SnakesGame):
        draw = ImageDraw.Draw(img)
        
        dots_y = self.board_y0 + self.board_height + 15
        dot_r = 6
        dot_gap = 15
        total_width = SnakesGame.TOTAL_ROUNDS * (2 * dot_r + dot_gap) - dot_gap
        start_x = self.board_x0 + (self.board_width - total_width) // 2
        
        for i in range(SnakesGame.TOTAL_ROUNDS):
            cx = start_x + i * (2 * dot_r + dot_gap) + dot_r
            cy = dots_y + dot_r
            filled = i < game.round_index
            fill = (55, 149, 255, 255) if filled else (70, 85, 100, 255)
            draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r], fill=fill)
            self.draw_text(img, cx - 3, cy - 5, str(i + 1), 9, (255, 255, 255, 200))
    
    def get_path_positions_to_target(self, target_pos, start_pos=(0, 0)):
        target_idx = self.pos_to_path_index.get(target_pos, -1)
        start_idx = self.pos_to_path_index.get(start_pos, 0)
        
        if target_idx == -1 or start_idx == -1:
            return [target_pos]
        
        positions = []
        for i in range(start_idx, target_idx + 1):
            positions.append(self.path_order[i])
        return positions    

    def generate_animation_frames(self, game: SnakesGame, action_type: str, 
                                user_background_path=None, old_game_state: SnakesGame = None) -> Optional[str]:
        logger.info(f"[Snakes] Generating animation for action: {action_type}")
        frames = []
        
        ANIMATION_LENGTH = 20
        HOLD_FRAMES = 20
        
        if action_type == 'start':
            original_multiplier = game.cumulative_multiplier
            game.cumulative_multiplier = 1.0
            
            for _ in range(HOLD_FRAMES * 20):
                img = self.create_base_image(user_background_path)
                self.draw_board(img, game)
                self.draw_dice_center(img, game, is_rolling=False)
                self.draw_multiplier_center(img, game)
                self.draw_progress_dots(img, game)
                frames.append(img)
            
            for frame_idx in range(ANIMATION_LENGTH):
                img = self.create_base_image(user_background_path)
                self.draw_board(img, game)
                self.draw_dice_center(img, game, frame_idx=frame_idx, is_rolling=True)
                self.draw_multiplier_center(img, game)
                self.draw_progress_dots(img, game)
                frames.append(img)
            
            target_pos = self.sum_to_pos.get(game.last_sum, (0, 0))
            path_positions = self.get_path_positions_to_target(target_pos, (0, 0))
            
            for pos in path_positions:
                for _ in range(HOLD_FRAMES):
                    img = self.create_base_image(user_background_path)
                    self.draw_board(img, game, highlight_positions=[pos])
                    self.draw_dice_center(img, game, is_rolling=False)
                    self.draw_multiplier_center(img, game)
                    self.draw_progress_dots(img, game)
                    frames.append(img)
            
            game.cumulative_multiplier = original_multiplier
            
            if game.last_outcome == "snake":
                self.multiplier_color = (255, 80, 80, 255)
            else:
                self.multiplier_color = (80, 255, 80, 255)
            
            for _ in range(HOLD_FRAMES):
                img = self.create_base_image(user_background_path)
                self.draw_board(img, game, highlight_positions=[target_pos])
                self.draw_dice_center(img, game, is_rolling=False)
                self.draw_multiplier_center(img, game)
                self.draw_progress_dots(img, game)
                frames.append(img)
                        
        elif action_type == 'roll' and old_game_state:
            start_pos = (0, 0)
            
            for _ in range(HOLD_FRAMES):
                img = self.create_base_image(user_background_path)
                self.draw_board(img, old_game_state, highlight_positions=[])
                self.draw_dice_center(img, old_game_state, is_rolling=False)
                temp_mult = game.cumulative_multiplier
                game.cumulative_multiplier = old_game_state.cumulative_multiplier
                self.draw_multiplier_center(img, old_game_state)
                game.cumulative_multiplier = temp_mult
                self.draw_progress_dots(img, old_game_state)
                frames.append(img)
            
            for frame_idx in range(ANIMATION_LENGTH):
                img = self.create_base_image(user_background_path)
                self.draw_board(img, old_game_state, highlight_positions=[])
                self.draw_dice_center(img, game, frame_idx=frame_idx, is_rolling=True)
                temp_mult = game.cumulative_multiplier
                game.cumulative_multiplier = old_game_state.cumulative_multiplier
                self.draw_multiplier_center(img, old_game_state)
                game.cumulative_multiplier = temp_mult
                self.draw_progress_dots(img, old_game_state)
                frames.append(img)
            
            new_target_pos = self.sum_to_pos.get(game.last_sum, (0, 0))
            path_positions = self.get_path_positions_to_target(new_target_pos, start_pos)
            
            for pos in path_positions:
                for _ in range(HOLD_FRAMES * 15):
                    img = self.create_base_image(user_background_path)
                    self.draw_board(img, game, highlight_positions=[pos])
                    self.draw_dice_center(img, game, is_rolling=False)
                    temp_mult = game.cumulative_multiplier
                    game.cumulative_multiplier = old_game_state.cumulative_multiplier
                    self.draw_multiplier_center(img, game)
                    game.cumulative_multiplier = temp_mult
                    self.draw_progress_dots(img, game)
                    frames.append(img)
            
            if game.last_outcome == "snake":
                self.multiplier_color = (255, 80, 80, 255)
            else:
                self.multiplier_color = (80, 255, 80, 255)
            
            for _ in range(HOLD_FRAMES):
                img = self.create_base_image(user_background_path)
                self.draw_board(img, game, highlight_positions=[new_target_pos])
                self.draw_dice_center(img, game, is_rolling=False)
                self.draw_multiplier_center(img, game)
                self.draw_progress_dots(img, game)
                frames.append(img)
        
        elif action_type == 'cashout':
            current_pos = self.sum_to_pos.get(game.last_sum, (0, 0)) if game.last_sum else (0, 0)
            self.multiplier_color = (80, 255, 80, 255)
            for _ in range(HOLD_FRAMES * 15):
                img = self.create_base_image(user_background_path)
                self.draw_board(img, game, highlight_positions=[current_pos])
                self.draw_dice_center(img, game, is_rolling=False)
                self.draw_multiplier_center(img, game)
                self.draw_progress_dots(img, game)
                frames.append(img)
        
        elif action_type == 'game_over':
            
            if old_game_state and old_game_state.last_sum:
                old_target_pos = self.sum_to_pos.get(old_game_state.last_sum, (0, 0))
                old_multiplier = old_game_state.cumulative_multiplier
                
                for _ in range(HOLD_FRAMES):
                    img = self.create_base_image(user_background_path)
                    self.draw_board(img, old_game_state, highlight_positions=[old_target_pos])
                    self.draw_dice_center(img, old_game_state, is_rolling=False)
                    temp_mult = game.cumulative_multiplier
                    game.cumulative_multiplier = old_multiplier
                    self.draw_multiplier_center(img, old_game_state)
                    game.cumulative_multiplier = temp_mult
                    self.draw_progress_dots(img, old_game_state)
                    frames.append(img)
            else:
                for _ in range(HOLD_FRAMES):
                    img = self.create_base_image(user_background_path)
                    self.draw_board(img, game)
                    self.draw_dice_center(img, game, is_rolling=False)
                    self.draw_multiplier_center(img, game)
                    self.draw_progress_dots(img, game)
                    frames.append(img)
            
            for frame_idx in range(ANIMATION_LENGTH):
                img = self.create_base_image(user_background_path)
                
                if old_game_state:
                    self.draw_board(img, old_game_state)
                else:
                    self.draw_board(img, game)
                
                self.draw_dice_center(img, game, frame_idx=frame_idx, is_rolling=True)
                
                if old_game_state:
                    temp_mult = game.cumulative_multiplier
                    game.cumulative_multiplier = old_game_state.cumulative_multiplier
                    self.draw_multiplier_center(img, old_game_state)
                    game.cumulative_multiplier = temp_mult
                    self.draw_progress_dots(img, old_game_state)
                else:
                    self.draw_multiplier_center(img, game)
                    self.draw_progress_dots(img, game)
                
                frames.append(img)
            
            if game.last_sum:
                target_pos = self.sum_to_pos.get(game.last_sum, (0, 0))
                start_pos = (0, 0)
                path_positions = self.get_path_positions_to_target(target_pos, start_pos)
                
                for pos in path_positions:
                    for _ in range(HOLD_FRAMES * 2):
                        img = self.create_base_image(user_background_path)
                        self.draw_board(img, game, highlight_positions=[pos])
                        self.draw_dice_center(img, game, is_rolling=False)
                        
                        if old_game_state:
                            temp_mult = game.cumulative_multiplier
                            game.cumulative_multiplier = old_game_state.cumulative_multiplier
                            self.draw_multiplier_center(img, game)
                            game.cumulative_multiplier = temp_mult
                        else:
                            self.draw_multiplier_center(img, game)
                        
                        self.draw_progress_dots(img, game)
                        frames.append(img)
            
            self.multiplier_color = (255, 80, 80, 255)
            for _ in range(HOLD_FRAMES):
                img = self.create_base_image(user_background_path)

                if game.last_sum:
                    final_pos = self.sum_to_pos.get(game.last_sum, (0, 0))
                    self.draw_board(img, game, highlight_positions=[final_pos])
                else:
                    self.draw_board(img, game)

                self.draw_dice_center(img, game, is_rolling=False)
                self.draw_multiplier_center(img, game)
                self.draw_progress_dots(img, game)
                frames.append(img)
            
            self.multiplier_color = (255, 80, 80, 255)
            for _ in range(HOLD_FRAMES):
                img = self.create_base_image(user_background_path)
                
                if game.last_sum:
                    final_pos = self.sum_to_pos.get(game.last_sum, (0, 0))
                    self.draw_board(img, game, highlight_positions=[final_pos])
                else:
                    self.draw_board(img, game)
                
                self.draw_dice_center(img, game, is_rolling=False)
                self.draw_multiplier_center(img, game)
                self.draw_progress_dots(img, game)
                frames.append(img)
        
        if frames:
            temp_path = os.path.join(os.path.dirname(__file__), "..", "results", 
                                    f"snakes_{action_type}_{random.randint(1000,9999)}.webp")
            
            try:
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                
                frames[0].save(
                    temp_path,
                    format='WEBP',
                    save_all=True,
                    append_images=frames[1:],
                    duration=75,
                    loop=0,
                    quality=90
                )
                return temp_path
            except Exception as e:
                logger.error(f"[Snakes] Error saving animation: {e}")
                return None
        
        return None

class SnakesPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="snakes")
        self.active_games: Dict[str, Dict] = {}
        self.animation_generator = None
        self.animation_generator = SnakesAnimationGenerator(self.text_renderer)
        logger.info("[Snakes] Animation generator initialized")

    def _parse_difficulty(self, value: Optional[str]) -> SnakesDifficulty:
        if not value:
            return _DIFFICULTIES["medium"]
        key = value.strip().lower()

        if key.isdigit():
            num = int(key)
            order = ["easy", "medium", "hard", "expert", "master"]
            if 1 <= num <= len(order):
                return _DIFFICULTIES[order[num - 1]]

        if key in _DIFFICULTIES:
            return _DIFFICULTIES[key]

        if key in ("e", "ea"):
            return _DIFFICULTIES["easy"]
        if key in ("med", "m"):
            return _DIFFICULTIES["medium"]
        if key in ("h",):
            return _DIFFICULTIES["hard"]
        if key in ("x", "ex", "exp"):
            return _DIFFICULTIES["expert"]
        if key in ("ma", "mas"):
            return _DIFFICULTIES["master"]
        return _DIFFICULTIES["medium"]

    def load_game_state(self, user_id: str) -> Optional[Dict]:
        user_id = str(user_id)
        if user_id in self.active_games:
            return self.active_games[user_id]

        if hasattr(self, "cache") and self.cache:
            stored = self.cache.get_game_state(user_id, self.game_name)
            if stored:
                try:
                    game_data = stored.get("game") if isinstance(stored, dict) else None
                    meta = stored.get("meta") if isinstance(stored, dict) else None
                    if not isinstance(game_data, dict) or not isinstance(meta, dict):
                        return None
                    game = SnakesGame.deserialize(game_data)
                    data = {
                        "game": game,
                        "bet": int(meta.get("bet", game.bet)),
                        "balance_after_bet": int(meta.get("balance_after_bet", 0)),
                        "balance_before": int(meta.get("balance_before", 0)),
                        "player": meta.get("player"),
                    }
                    self.active_games[user_id] = data
                    return data
                except Exception as exc:
                    logger.error(f"[Snakes] Failed to deserialize game: {exc}")
        return None

    def save_game_state(self, user_id: str, data: Optional[Dict]):
        user_id = str(user_id)
        if not (hasattr(self, "cache") and self.cache):
            return
        if not data:
            self.cache.delete_game_state(user_id, self.game_name)
            return
        game: SnakesGame = data.get("game")
        payload = {
            "game": game.serialize() if game else None,
            "meta": {
                "bet": int(data.get("bet", 0)),
                "balance_after_bet": int(data.get("balance_after_bet", 0)),
                "balance_before": int(data.get("balance_before", 0)),
                "player": data.get("player"),
            },
        }
        self.cache.save_game_state(user_id, self.game_name, payload)

    def _clear_game(self, user_id: str):
        user_id = str(user_id)
        self.active_games.pop(user_id, None)
        if hasattr(self, "cache") and self.cache:
            self.cache.delete_game_state(user_id, self.game_name)

    def get_user_background_path(self, user_id: str, user: Dict) -> Optional[str]:
        if not user:
            return None
        
        if hasattr(self, 'cache') and self.cache:
            background_path = self.cache.get_background_path(user_id)
            if background_path and os.path.exists(background_path):
                return background_path
        
        return None

    def _send_animation(self, sender: str, file_queue, cache, user_id: str, user: Dict,
                        bet: int, win_amount: int, balance: int, animation_path: str,
                        game: SnakesGame):
        try:
            if not animation_path or not os.path.exists(animation_path):
                logger.error(f"[Snakes] Animation file not found: {animation_path}")
                return
            
            balance_before = balance - win_amount if win_amount > 0 else balance
            if win_amount < 0:
                balance_before = balance - win_amount
            
            user_info_before = self.create_user_info(sender, bet, 0, balance_before, user)
            user_info_after = self.create_user_info(sender, bet, win_amount, balance, user)
            
            show_win = win_amount != 0

            result_path, error = self.generate_animation(
                base_animation_path=animation_path,
                user_id=user_id,
                user=user,
                user_info_before=user_info_before,
                user_info_after=user_info_after,
                animated=True,
                frame_duration=75,
                last_frame_multiplier=20,
                show_win_text=show_win,
                win_text_height=5,
                font_scale=0.7,
                avatar_size=45
            )
            
            if result_path:
                file_queue.put(result_path)
            
            try:
                os.remove(animation_path)
            except:
                pass
            
        except Exception as e:
            logger.error(f"[Snakes] Error sending animation: {e}")

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache

        user_id, user, err = self.validate_user(cache, sender, avatar_url)
        if err or not user_id:
            return

        sender_display = sender
        balance_before = int(user.get("balance", 0))

        if not args:
            help_text = (
                "SNAKES GAME\n\n"
                "Use:\n"
                "/snakes <bet> [difficulty]\n"
                "/snakes roll\n"
                "/snakes cashout\n\n"
                "Difficulties: easy, medium, hard, expert, master"
            )
            self.send_message_image(
                nickname=sender_display,
                file_queue=file_queue,
                message=help_text,
                title="Snakes - Help",
                cache=cache,
                user_id=user_id,
            )
            return

        sub = args[0].lower()

        if sub in ("start", "bet"):
            args = args[1:]
            if not args:
                self.send_message_image(
                    nickname=sender_display,
                    file_queue=file_queue,
                    message="Use: /snakes start <bet> [difficulty]\nExample: /snakes 100 medium",
                    title="Snakes - Start",
                    cache=cache,
                    user_id=user_id,
                )
                return
            sub = args[0].lower()

        if sub == "bet":
            args = args[1:]
            if not args:
                self.send_message_image(
                    nickname=sender_display,
                    file_queue=file_queue,
                    message="Use: /snakes bet <bet> [difficulty]\nExample: /snakes bet 100 medium",
                    title="Snakes - Start",
                    cache=cache,
                    user_id=user_id,
                )
                return
            sub = args[0].lower()

        if sub in ("start", "s"):
            args = args[1:]
            if not args:
                self.send_message_image(
                    nickname=sender_display,
                    file_queue=file_queue,
                    message="Use: /snakes start <bet> [difficulty]\nExample: /snakes start 100 medium",
                    title="Snakes - Start",
                    cache=cache,
                    user_id=user_id,
                )
                return
            sub = args[0].lower()

        if sub in ("roll", "r"):
            if user_id not in self.active_games:
                self.load_game_state(user_id)

            if user_id not in self.active_games:
                self.send_message_image(
                    nickname=sender_display,
                    file_queue=file_queue,
                    message="No active game.\n\nStart with: /snakes <bet> [difficulty]",
                    title="Snakes - No Game",
                    cache=cache,
                    user_id=user_id,
                )
                return

            data = self.active_games.get(user_id)
            game: SnakesGame = data["game"]
            bet = data["bet"]
            balance_after_bet = data["balance_after_bet"]

            old_game_state = SnakesGame(bet=bet, difficulty=game.difficulty)
            old_game_state.round_index = game.round_index
            old_game_state.cumulative_multiplier = game.cumulative_multiplier
            old_game_state.last_roll = game.last_roll
            old_game_state.last_sum = game.last_sum
            old_game_state.last_outcome = game.last_outcome
            old_game_state.last_multiplier = game.last_multiplier
            old_game_state.last_table_round_index = game.last_table_round_index

            result = game.roll()
            if not result.get("ok"):
                self.send_message_image(
                    nickname=sender_display,
                    file_queue=file_queue,
                    message=result.get("error", "Unknown error"),
                    title="Snakes - Error",
                    cache=cache,
                    user_id=user_id,
                )
                return

            if result["outcome"] == "snake":
                net_win = -bet
                try:
                    new_level, new_progress = self.cache.add_experience(user_id, -bet, sender_display, file_queue)
                    user["level"] = new_level
                    user["level_progress"] = new_progress
                except Exception as e:
                    logger.warning(f"[Snakes] add_experience failed: {e}")

                anim_path = self.animation_generator.generate_animation_frames(
                    game, 'game_over',
                    user_background_path=self.get_user_background_path(user_id, user),
                    old_game_state=old_game_state
                )
                if anim_path:
                    self._send_animation(sender_display, file_queue, cache, user_id, user, 
                                        bet, net_win, balance_after_bet, anim_path, game)
                
                self._clear_game(user_id)
                return

            anim_path = self.animation_generator.generate_animation_frames(
                game, 'roll',
                user_background_path=self.get_user_background_path(user_id, user),
                old_game_state=old_game_state
            )
             
            if result.get("is_maxed"):
                payout = game.current_payout()
                net_win = payout - bet
                new_balance = balance_after_bet + payout
                try:
                    self.update_user_balance(user_id, new_balance)
                except Exception as e:
                    logger.error(f"[Snakes] Balance update failed on max payout: {e}")
                if net_win > 0:
                    record_weekly_win(self.cache, user_id, "snakes", net_win)

                try:
                    new_level, new_progress = self.cache.add_experience(user_id, net_win, sender_display, file_queue)
                    user["level"] = new_level
                    user["level_progress"] = new_progress
                except Exception as e:
                    logger.warning(f"[Snakes] add_experience failed: {e}")

                if anim_path:
                    self._send_animation(sender_display, file_queue, cache, user_id, user, 
                                        bet, net_win, new_balance, anim_path, game)
                
                self._clear_game(user_id)
                return

            if anim_path:
                self._send_animation(sender_display, file_queue, cache, user_id, user, 
                                    bet, 0, balance_after_bet, anim_path, game)

            self.save_game_state(user_id, data)
            return

        if sub in ("cashout", "c", "co"):
            if user_id not in self.active_games:
                self.load_game_state(user_id)

            if user_id not in self.active_games:
                self.send_message_image(
                    nickname=sender_display,
                    file_queue=file_queue,
                    message="No active game.\n\nStart with: /snakes <bet> [difficulty]",
                    title="Snakes - No Game",
                    cache=cache,
                    user_id=user_id,
                )
                return

            data = self.active_games.pop(user_id)
            game: SnakesGame = data["game"]
            bet = data["bet"]
            balance_after_bet = data["balance_after_bet"]

            if game.round_index <= 0:
                self.active_games[user_id] = data
                self.save_game_state(user_id, data)
                self.send_message_image(
                    nickname=sender_display,
                    file_queue=file_queue,
                    message="You can't cashout before a win.\n\nUse: /snakes roll",
                    title="Snakes - Cashout",
                    cache=cache,
                    user_id=user_id,
                )
                return

            payout = game.current_payout()
            net_win = payout - bet
            new_balance = balance_after_bet + payout
            try:
                self.update_user_balance(user_id, new_balance)
            except Exception as e:
                logger.error(f"[Snakes] Balance update failed on cashout: {e}")

            if net_win > 0:
                record_weekly_win(self.cache, user_id, "snakes", net_win)

            try:
                new_level, new_progress = self.cache.add_experience(user_id, net_win, sender_display, file_queue)
                user["level"] = new_level
                user["level_progress"] = new_progress
            except Exception as e:
                logger.warning(f"[Snakes] add_experience failed: {e}")

            anim_path = self.animation_generator.generate_animation_frames(
                game, 'cashout',
                user_background_path=self.get_user_background_path(user_id, user)
            )
            if anim_path:
                self._send_animation(sender_display, file_queue, cache, user_id, user, 
                                    bet, net_win, new_balance, anim_path, game)

            self.save_game_state(user_id, None)
            return

        try:
            bet = int(sub)
        except ValueError:
            self.send_message_image(
                nickname=sender_display,
                file_queue=file_queue,
                message="Invalid command.\n\nUse:\n"
                        "/snakes <bet> [difficulty]\n"
                        "/snakes roll\n"
                        "/snakes cashout",
                title="Snakes - Error",
                cache=cache,
                user_id=user_id,
            )
            return

        if bet < 1:
            self.send_message_image(
                nickname=sender_display,
                file_queue=file_queue,
                message="Minimum bet is $1.",
                title="Snakes - Bet",
                cache=cache,
                user_id=user_id,
            )
            return

        if user_id in self.active_games:
            self.send_message_image(
                nickname=sender_display,
                file_queue=file_queue,
                message="You already have an active game.\n\nUse /snakes roll or /snakes cashout.",
                title="Snakes - Active Game",
                cache=cache,
                user_id=user_id,
            )
            return

        if self.load_game_state(user_id):
            self.send_message_image(
                nickname=sender_display,
                file_queue=file_queue,
                message="You already have an active game.\n\nUse /snakes roll or /snakes cashout.",
                title="Snakes - Active Game",
                cache=cache,
                user_id=user_id,
            )
            return

        if bet > balance_before:
            self.send_message_image(
                nickname=sender_display,
                file_queue=file_queue,
                message=f"Insufficient funds.\n\nBet: ${bet}\nBalance: ${balance_before}",
                title="Snakes - Insufficient Funds",
                cache=cache,
                user_id=user_id,
            )
            return

        difficulty = self._parse_difficulty(args[1] if len(args) > 1 else None)
        game = SnakesGame(bet=bet, difficulty=difficulty)

        balance_after_bet = balance_before - bet
        try:
            self.update_user_balance(user_id, balance_after_bet)
        except Exception as e:
            logger.error(f"[Snakes] Balance update failed on start: {e}")
            self.send_message_image(
                nickname=sender_display,
                file_queue=file_queue,
                message="Error updating balance. Try again.",
                title="Snakes - System Error",
                cache=cache,
                user_id=user_id,
            )
            return

        self.active_games[user_id] = {
            "game": game,
            "bet": bet,
            "balance_after_bet": balance_after_bet,
            "balance_before": balance_before,
            "player": sender_display,
        }
        self.save_game_state(user_id, self.active_games[user_id])

        result = game.roll()
        if not result.get("ok"):
            self.active_games.pop(user_id, None)
            self.send_message_image(
                nickname=sender_display,
                file_queue=file_queue,
                message=result.get("error", "Unknown error"),
                title="Snakes - Error",
                cache=cache,
                user_id=user_id,
            )
            return

        if result["outcome"] == "snake":
            net_win = -bet
            try:
                new_level, new_progress = self.cache.add_experience(user_id, -bet, sender_display, file_queue)
                user["level"] = new_level
                user["level_progress"] = new_progress
            except Exception as e:
                logger.warning(f"[Snakes] add_experience failed: {e}")

            anim_path = self.animation_generator.generate_animation_frames(
                game, 'game_over',
                user_background_path=self.get_user_background_path(user_id, user)
            )
            if anim_path:
                self._send_animation(sender_display, file_queue, cache, user_id, user, 
                                    bet, net_win, balance_after_bet, anim_path, game)
            
            self._clear_game(user_id)
            return

        anim_path = self.animation_generator.generate_animation_frames(
            game, 'start',
            user_background_path=self.get_user_background_path(user_id, user)
        )
        
        if result.get("is_maxed"):
            payout = game.current_payout()
            net_win = payout - bet
            new_balance = balance_after_bet + payout
            try:
                self.update_user_balance(user_id, new_balance)
            except Exception as e:
                logger.error(f"[Snakes] Balance update failed on max payout: {e}")
            if net_win > 0:
                record_weekly_win(self.cache, user_id, "snakes", net_win)
            
            if anim_path:
                self._send_animation(sender_display, file_queue, cache, user_id, user, 
                                    bet, net_win, new_balance, anim_path, game)
            
            self._clear_game(user_id)
            return

        if anim_path:
            self._send_animation(sender_display, file_queue, cache, user_id, user, 
                                bet, 0, balance_after_bet, anim_path, game)

        self.save_game_state(user_id, self.active_games[user_id])


def register():
    plugin = SnakesPlugin()
    return {
        "name": "snakes",
        "aliases": ["/sn","/snake"],
        "description": (
            "  SNAKES GAME  \n\n"
            "Roll 2 dice, avoid SNAKE tiles, hit multipliers!\n\n"
            "  Commands:\n"
            "  /snakes <bet> [difficulty] - Start new game\n"
            "  /snakes roll - Roll the dice\n"
            "  /snakes cashout - Cashout your winnings\n"
            "  /snakes help - Show this help\n\n"
            "  Difficulties:\n"
            "  easy, medium, hard, expert, master\n\n"
            "  How to play:\n"
            "  • Roll 2 dice, land on multiplier tiles\n"
            "  • Avoid SNAKE tiles or you lose!\n"
            "  • Each win increases your multiplier\n"
            "  • Cashout anytime after a win\n"
            "  • 5 wins max for big payout!\n\n"
            "  Expected RTP: 98%"
        ),
        "execute": plugin.execute_game,
    }
