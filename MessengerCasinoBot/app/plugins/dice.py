import os
import random
import re
from typing import List, Dict, Optional
from PIL import Image, ImageDraw, ImageSequence
from base_game_plugin import BaseGamePlugin
from logger import logger
from plugins.monthly import record_monthly_win
from plugins.weekly import record_weekly_win
from decimal import Decimal, ROUND_HALF_UP
from plugins.dailyquest import record_daily_win

DICE_MULTIPLIERS = {
    "five_of_a_kind": 10,
    "four_of_a_kind": 3,
    "straight": 3,
    "full_house": 2,
    "three_of_a_kind": 0.5,
    "two_pair": 0,
    "one_pair": 0,
    "high_card": 0
}

class DiceGame:
    def __init__(self, user_id: str, sender_name: str, bet: int):
        self.user_id = user_id
        self.sender_name = sender_name
        self.bet = bet
        self.dice = []
        self.game_status = "waiting"
        self.message = "Roll dice to start!"
        self.win_amount = 0.0
        self.multiplier = 0
        self.hand_type = "high_card"
        self.rerolls_used = 0
        self.max_rerolls = 1
        self.finished = False
        self.rolled = False
        self.cashed_out = False
    
    def roll_dice(self):
        self.dice = [random.randint(1, 6) for _ in range(5)]
        self._evaluate_hand()
        self.rolled = True
        self.game_status = "waiting_for_reroll"
        self.finished = False
        self.cashed_out = False
    
    def reroll(self, indices_str: str) -> bool:
        if self.rerolls_used >= self.max_rerolls:
            self.message = "You've used all rerolls!"
            return False
        
        if self.finished:
            self.message = "Game already finished!"
            return False
        
        indices = self._parse_indices(indices_str)
        
        if not indices:
            self.message = "Invalid dice numbers! Use: /dice 1 2 3"
            return False
        
        zero_based = [i-1 for i in indices if 1 <= i <= 5]
        
        if not zero_based:
            self.message = "Dice numbers must be between 1 and 5"
            return False
        
        if len(zero_based) > 5:
            self.message = "You can only reroll up to 5 dice"
            return False
        
        self.rerolls_used += 1
        
        for idx in zero_based:
            if 0 <= idx < len(self.dice):
                self.dice[idx] = random.randint(1, 6)
        
        self._evaluate_hand()
        self.game_status = "finished"
        self.finished = True
        return True
    
    def cashout(self) -> bool:
        if self.finished:
            return False
        if not self.rolled:
            return False
        
        self.game_status = "finished"
        self.finished = True
        self.cashed_out = True
        return True
    
    def _parse_indices(self, indices_str: str) -> List[int]:
        indices = []
        cleaned = re.sub(r'[,\s]+', ' ', indices_str)
        parts = cleaned.split()
        
        for part in parts:
            if part.isdigit():
                indices.append(int(part))
        
        return indices

    def _evaluate_hand(self):
        self.hand_type = self._get_hand_type(self.dice)
        self.multiplier = DICE_MULTIPLIERS.get(self.hand_type, 0)
        
        # OBLICZANIE Z ZAOKRĄGLENIEM DO LICZB CAŁKOWITYCH
        raw_win = float(self.bet * self.multiplier)
        
        # Zaokrąglenie do najbliższej liczby całkowitej (0.5 zaokrągla w górę)
        self.win_amount = int(Decimal(str(raw_win)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
        
        hand_display = self.hand_type.replace('_', ' ').title()
        
        if self.multiplier > 1:
            self.message = f"{hand_display}! +${self.win_amount} (x{self.multiplier})!"
        elif self.multiplier == 1:
            self.message = f"{hand_display}! Break even! +${self.win_amount}"
        elif self.multiplier > 0 and self.multiplier < 1:
            net_loss = self.bet - self.win_amount
            self.message = f"{hand_display}! Won ${self.win_amount} (lost ${net_loss} net)"
        else:
            self.message = f"{hand_display}! Lost ${self.bet}"        


    def _get_hand_type(self, dice: List[int]) -> str:
        counts = {}
        for d in dice:
            counts[d] = counts.get(d, 0) + 1
        
        values = list(counts.values())
        
        if 5 in values:
            return "five_of_a_kind"
        if 4 in values:
            return "four_of_a_kind"
        if 3 in values and 2 in values:
            return "full_house"
        if self._is_straight(sorted(dice)):
            return "straight"
        if 3 in values:
            return "three_of_a_kind"
        if values.count(2) == 2:
            return "two_pair"
        if 2 in values:
            return "one_pair"
        return "high_card"
    
    def _is_straight(self, sorted_dice: List[int]) -> bool:
        return all(sorted_dice[i] == sorted_dice[0] + i for i in range(5))
    
    def get_game_state(self) -> Dict:
        return {
            'dice': self.dice.copy(),
            'hand_type': self.hand_type,
            'hand_display': self.hand_type.replace('_', ' ').title(),
            'multiplier': self.multiplier,
            'win_amount': self.win_amount,
            'bet': self.bet,
            'game_status': self.game_status,
            'message': self.message,
            'rerolls_used': self.rerolls_used,
            'max_rerolls': self.max_rerolls,
            'finished': self.finished,
            'rolled': self.rolled,
            'cashed_out': self.cashed_out
        }


class DiceAnimationGenerator:
    def __init__(self, text_renderer, dice_animations):
        self.text_renderer = text_renderer
        self.dice_animations = dice_animations
        self.dice_animation_frames = {}
        self._load_animation_frames()
        
        self.CARD_WIDTH = 300
        self.CARD_HEIGHT = 250
        self.DICE_SIZE = 40
        self.DICE_SPACING = 5
        self.PADDING = 5
        
        self.COLORS = {
            'bg_dark': (10, 10, 20, 255),
            'text_primary': (255, 255, 255, 255),
            'text_secondary': (180, 180, 180, 255),
            'text_success': (80, 200, 120, 255),
            'text_danger': (255, 80, 80, 255),
            'text_highlight': (255, 215, 0, 255),
            'border': (70, 70, 90, 255),
            'hand_bg': (0, 0, 0, 180),
            'table_bg': (0, 0, 0, 200),
            'table_border': (100, 100, 120, 255),
            'row_even': (20, 20, 30, 200),
            'row_odd': (30, 30, 45, 200),
            'row_highlight': (60, 40, 20, 220),
            'number_bg': (0, 0, 0, 150),
            'dice_mat': (255, 255, 255, 90)  # Przezroczysta podkładka pod kostki
        }
        
        self.table_data = [
            ("five_of_a_kind", "Five of a Kind", "x9"),
            ("four_of_a_kind", "Four of a Kind", "x3"),
            ("straight", "Straight", "x3"),
            ("full_house", "Full House", "x2"),
            ("three_of_a_kind", "Three of a Kind", "x0.5"),
            ("two_pair", "Two Pair", "x0"),
            ("one_pair", "One Pair", "x0"),
            ("high_card", "High Card", "x0")
        ]
    
    def _load_animation_frames(self):
        for value, path in self.dice_animations.items():
            try:
                frames = []
                if not os.path.exists(path):
                    logger.error(f"[Dice] File does not exist: {path}")
                    self.dice_animation_frames[value] = []
                    continue
                
                with Image.open(path) as img:
                    for frame in ImageSequence.Iterator(img):
                        frame_rgba = frame.convert('RGBA')
                        frames.append(frame_rgba)
                
                self.dice_animation_frames[value] = frames
            except Exception as e:
                logger.error(f"[Dice] Failed to load animation for dice_{value}: {e}", exc_info=True)
                self.dice_animation_frames[value] = []
    
    def create_base_image(self, user_background_path=None) -> Image.Image:
        if user_background_path and os.path.exists(user_background_path):
            try:
                bg = Image.open(user_background_path).convert('RGBA')
                bg = bg.resize((self.CARD_WIDTH, self.CARD_HEIGHT))
                img = Image.new('RGBA', (self.CARD_WIDTH, self.CARD_HEIGHT), (0, 0, 0, 0))
                img.paste(bg, (0, 0))
                return img
            except Exception as e:
                logger.error(f"[Dice] Error loading background: {e}")
        
        return Image.new('RGBA', (self.CARD_WIDTH, self.CARD_HEIGHT), self.COLORS['bg_dark'])
    
    def draw_dice_mat(self, img):
        """Rysuje przezroczystą podkładkę pod kostkami."""
        draw = ImageDraw.Draw(img)
        
        # Oblicz pozycję podkładki
        total_width = 5 * self.DICE_SIZE + 4 * self.DICE_SPACING
        start_x = (self.CARD_WIDTH - total_width) // 2
        y = self._get_dice_y()
        
        # Dodaj padding do podkładki
        mat_padding = 8
        mat_x = start_x - mat_padding
        mat_y = y - mat_padding
        mat_width = total_width + mat_padding * 2
        mat_height = self.DICE_SIZE + mat_padding * 2
        
        # Rysuj zaokrąglony prostokąt z przezroczystością
        draw.rounded_rectangle(
            [mat_x, mat_y, mat_x + mat_width, mat_y + mat_height],
            radius=10,
            fill=self.COLORS['dice_mat'],
            outline=(255, 255, 255, 60),  # Lekko widoczna obwódka
            width=1
        )
        
        # Dodaj delikatny cień pod kostkami - mały gradient
        shadow_height = 3
        for i in range(shadow_height):
            alpha = int(20 * (1 - i / shadow_height))
            draw.rounded_rectangle(
                [mat_x, mat_y + mat_height + i, mat_x + mat_width, mat_y + mat_height + i + 1],
                radius=2,
                fill=(0, 0, 0, alpha)
            )
    
    def draw_multiplier_table(self, img, highlight_hand=None):
        if not self.text_renderer:
            return
        
        table_width = self.CARD_WIDTH - self.PADDING * 2
        table_height = len(self.table_data) * 10 + 14
        table_x = self.PADDING
        table_y = self.CARD_HEIGHT - table_height - self.PADDING - 2
        
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            [table_x, table_y, table_x + table_width, table_y + table_height],
            radius=2,
            fill=self.COLORS['table_bg'],
            outline=self.COLORS['table_border'],
            width=1
        )
        
        title = self.text_renderer.render_text("MULTIPLIERS", 5, self.COLORS['text_highlight'])
        img.alpha_composite(title, (table_x + (table_width - title.width) // 2, table_y + 1))
        
        y = table_y + 11
        for hand_type, hand, mult in self.table_data:
            if highlight_hand and hand_type == highlight_hand:
                bg_color = self.COLORS['row_highlight']
                text_color = self.COLORS['text_highlight']
                mult_color = self.COLORS['text_success']
            else:
                bg_color = self.COLORS['row_even'] if (self.table_data.index((hand_type, hand, mult)) % 2 == 0) else self.COLORS['row_odd']
                text_color = self.COLORS['text_secondary']
                mult_color = self.COLORS['text_highlight']
            
            draw.rectangle(
                [table_x + 2, y, table_x + table_width - 2, y + 8],
                fill=bg_color
            )
            
            hand_text = self.text_renderer.render_text(hand, 4, text_color)
            img.alpha_composite(hand_text, (table_x + 2, y))
            
            mult_text = self.text_renderer.render_text(mult, 4, mult_color)
            img.alpha_composite(mult_text, (table_x + table_width - mult_text.width - 2, y))
            
            y += 10
    
    def draw_dice_numbers(self, img):
        if not self.text_renderer:
            return
        
        y = self._get_dice_y() + self.DICE_SIZE + 2
        
        for i in range(5):
            x = self._get_dice_x(i) + self.DICE_SIZE // 2 - 3
            
            num_text = self.text_renderer.render_text(str(i+1), 4, self.COLORS['text_secondary'])
            
            padding = 1
            bg_width = num_text.width + padding * 2
            bg_height = num_text.height + padding * 2
            
            bg = Image.new('RGBA', (bg_width, bg_height), self.COLORS['number_bg'])
            img.alpha_composite(bg, (x - padding + 1, y - padding))
            img.alpha_composite(num_text, (x + 1, y))
    
    def draw_info_text(self, img, text: str, color=(255, 215, 0, 255)):
        if not self.text_renderer:
            return
        
        text_img = self.text_renderer.render_text(text, 6, color)
        
        padding = 2
        bg_width = min(text_img.width + padding * 2, self.CARD_WIDTH - 20)
        bg_height = text_img.height + padding * 2
        
        bg = Image.new('RGBA', (bg_width, bg_height), self.COLORS['hand_bg'])
        
        x = (self.CARD_WIDTH - bg_width) // 2
        y = 30
        
        img.alpha_composite(bg, (x, y))
        img.alpha_composite(text_img, (x + padding, y + padding))
    
    def draw_single_dice(self, img, value, x, y, frame_idx=0, use_last_frame=False, is_rolling=False):
        if value == 0:
            return
        
        frames = self.dice_animation_frames.get(value, [])
        
        if not frames:
            draw = ImageDraw.Draw(img)
            draw.ellipse([x, y, x + self.DICE_SIZE, y + self.DICE_SIZE], 
                        fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=1)
            if self.text_renderer:
                text_img = self.text_renderer.render_text(str(value), 14, (0, 0, 0, 255))
                text_x = x + (self.DICE_SIZE - text_img.width) // 2
                text_y = y + (self.DICE_SIZE - text_img.height) // 2
                img.alpha_composite(text_img, (text_x, text_y))
            return
        
        if not is_rolling or use_last_frame:
            dice_img = frames[-1]
        else:
            idx = frame_idx % len(frames)
            dice_img = frames[idx]
        
        dice_img = dice_img.resize((self.DICE_SIZE, self.DICE_SIZE))
        img.alpha_composite(dice_img, (x, y))
    
    def _get_dice_x(self, index: int) -> int:
        total_width = 5 * self.DICE_SIZE + 4 * self.DICE_SPACING
        start_x = (self.CARD_WIDTH - total_width) // 2
        return start_x + index * (self.DICE_SIZE + self.DICE_SPACING)
    
    def _get_dice_y(self) -> int:
        return (self.CARD_HEIGHT - self.DICE_SIZE) // 2 - 15
    
    def generate_dice_animation_frames(self, game_state, user_background_path=None, is_reroll=False, reroll_indices=None, show_result=True, cashout=False, static=False) -> str:
        logger.info(f"[Dice] Generating dice roll animation")
        frames = []
        
        dice = game_state['dice']
        hand_type = game_state['hand_type']
        
        if static or cashout:
            img = self.create_base_image(user_background_path)
            self.draw_dice_mat(img)  # Dodaj podkładkę
            self.draw_multiplier_table(img, highlight_hand=hand_type)
            self.draw_dice_numbers(img)
            
            for i in range(5):
                x = self._get_dice_x(i)
                y = self._get_dice_y()
                self.draw_single_dice(
                    img, dice[i], x, y, 
                    use_last_frame=True
                )
            
            frames.append(img)
            
            temp_path = os.path.join(os.path.dirname(__file__), "..", "results", 
                                    f"dice_{random.randint(1000,9999)}.webp")
            try:
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                
                frames[0].save(
                    temp_path,
                    format='WEBP',
                    quality=90
                )
                return temp_path
            except Exception as e:
                logger.error(f"[Dice] Error saving image: {e}")
                return None
        
        if is_reroll and reroll_indices:
            old_dice = game_state.get('old_dice', dice)
            
            for _ in range(3):
                img = self.create_base_image(user_background_path)
                self.draw_dice_mat(img)  # Dodaj podkładkę
                self.draw_info_text(img, "REROLLING...", self.COLORS['text_highlight'])
                self.draw_multiplier_table(img, highlight_hand=None)
                self.draw_dice_numbers(img)
                
                for i in range(5):
                    x = self._get_dice_x(i)
                    y = self._get_dice_y()
                    self.draw_single_dice(
                        img, old_dice[i] if i < len(old_dice) else 1, x, y, 
                        use_last_frame=True
                    )
                
                frames.append(img)
            
            ANIMATION_LENGTH = 50
            HOLD_FRAMES = 8
            
            for frame_idx in range(ANIMATION_LENGTH):
                img = self.create_base_image(user_background_path)
                self.draw_dice_mat(img)  # Dodaj podkładkę
                
                if frame_idx < 35:
                    dice_revealed = min(len(reroll_indices), frame_idx // 7 + 1)
                    
                    self.draw_info_text(img, "REROLLING...", self.COLORS['text_highlight'])
                    
                    self.draw_multiplier_table(img, highlight_hand=None)
                    self.draw_dice_numbers(img)
                    
                    for i in range(5):
                        x = self._get_dice_x(i)
                        y = self._get_dice_y()
                        
                        if i in reroll_indices:
                            idx_in_reroll = list(reroll_indices).index(i)
                            if idx_in_reroll < dice_revealed:
                                self.draw_single_dice(
                                    img, dice[i], x, y, 
                                    use_last_frame=True
                                )
                            else:
                                self.draw_single_dice(
                                    img, random.randint(1, 6), x, y, 
                                    frame_idx=frame_idx, is_rolling=True
                                )
                        else:
                            self.draw_single_dice(
                                img, old_dice[i] if i < len(old_dice) else 1, x, y, 
                                use_last_frame=True
                            )
                else:
                    self.draw_multiplier_table(img, highlight_hand=hand_type)
                    self.draw_dice_numbers(img)
                    
                    for i in range(5):
                        x = self._get_dice_x(i)
                        y = self._get_dice_y()
                        self.draw_single_dice(
                            img, dice[i], x, y, 
                            use_last_frame=True
                        )
                
                frames.append(img)
            
            for _ in range(HOLD_FRAMES):
                img = self.create_base_image(user_background_path)
                self.draw_dice_mat(img)  # Dodaj podkładkę
                
                self.draw_multiplier_table(img, highlight_hand=hand_type)
                self.draw_dice_numbers(img)
                
                for i in range(5):
                    x = self._get_dice_x(i)
                    y = self._get_dice_y()
                    self.draw_single_dice(
                        img, dice[i], x, y, 
                        use_last_frame=True
                    )
                
                frames.append(img)
            
            if frames:
                temp_path = os.path.join(os.path.dirname(__file__), "..", "results", 
                                        f"dice_{random.randint(1000,9999)}.webp")
                try:
                    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                    
                    frames[0].save(
                        temp_path,
                        format='WEBP',
                        save_all=True,
                        append_images=frames[1:],
                        duration=50,
                        loop=0,
                        quality=90
                    )
                    return temp_path
                except Exception as e:
                    logger.error(f"[Dice] Error saving animation: {e}")
                    return None
            
            return None
        
        ANIMATION_LENGTH = 50
        HOLD_FRAMES = 8
        
        for frame_idx in range(ANIMATION_LENGTH):
            img = self.create_base_image(user_background_path)
            self.draw_dice_mat(img)  # Dodaj podkładkę
            
            if frame_idx < 35:
                dice_revealed = min(5, frame_idx // 7 + 1)
                
                self.draw_info_text(img, "ROLLING...", self.COLORS['text_highlight'])
                
                self.draw_multiplier_table(img, highlight_hand=None)
                self.draw_dice_numbers(img)
                
                for i in range(5):
                    x = self._get_dice_x(i)
                    y = self._get_dice_y()
                    
                    if i < dice_revealed:
                        self.draw_single_dice(
                            img, dice[i], x, y, 
                            use_last_frame=True
                        )
                    else:
                        self.draw_single_dice(
                            img, random.randint(1, 6), x, y, 
                            frame_idx=frame_idx, is_rolling=True
                        )
            else:
                self.draw_info_text(img, "Use /dice 1 2 3 or /dice cashout", self.COLORS['text_highlight'])
                self.draw_multiplier_table(img, highlight_hand=hand_type)
                self.draw_dice_numbers(img)
                
                for i in range(5):
                    x = self._get_dice_x(i)
                    y = self._get_dice_y()
                    self.draw_single_dice(
                        img, dice[i], x, y, 
                        use_last_frame=True
                    )
            
            frames.append(img)
        
        for _ in range(HOLD_FRAMES):
            img = self.create_base_image(user_background_path)
            self.draw_dice_mat(img)  # Dodaj podkładkę
            
            self.draw_info_text(img, "Use /dice 1 2 3 or /dice cashout", self.COLORS['text_highlight'])
            self.draw_multiplier_table(img, highlight_hand=hand_type)
            self.draw_dice_numbers(img)
            
            for i in range(5):
                x = self._get_dice_x(i)
                y = self._get_dice_y()
                self.draw_single_dice(
                    img, dice[i], x, y, 
                    use_last_frame=True
                )
            
            frames.append(img)
        
        if frames:
            temp_path = os.path.join(os.path.dirname(__file__), "..", "results", 
                                    f"dice_{random.randint(1000,9999)}.webp")
            try:
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                
                frames[0].save(
                    temp_path,
                    format='WEBP',
                    save_all=True,
                    append_images=frames[1:],
                    duration=50,
                    loop=0,
                    quality=90
                )
                return temp_path
            except Exception as e:
                logger.error(f"[Dice] Error saving animation: {e}")
                return None
        
        return None


class DicePlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="dice")
        self.min_bet = 1
        self.dice_animations = {}
        self.animation_generator = None
        self.active_games = {}
        self._load_dice_animations()
        self.animation_generator = DiceAnimationGenerator(self.text_renderer, self.dice_animations)
    
    def _load_dice_animations(self):
        dice_folder = self.get_asset_path("dice")
        if not os.path.exists(dice_folder):
            logger.error(f"[Dice] Dice folder not found: {dice_folder}")
            return
        
        for i in range(1, 7):
            animation_path = os.path.join(dice_folder, f"dice_{i}.webp")
            if os.path.exists(animation_path):
                self.dice_animations[i] = animation_path
            else:
                logger.warning(f"[Dice] Missing dice animation: dice_{i}.webp")
    
    def get_user_background_path(self, user_id: str, user: Dict) -> Optional[str]:
        if not user:
            return None
        
        if hasattr(self, 'cache') and self.cache:
            background_path = self.cache.get_background_path(user_id)
            if os.path.exists(background_path):
                return background_path
        
        return None
    
    def _get_help_text(self) -> str:
        return (
            "DICE GAME\n\n"
            "How to play:\n"
            "Roll 5 dice and get a winning combination!\n"
            "You have 1 reroll or you can cashout\n\n"
            "Multipliers:\n"
            "Five of a Kind: x9\n"
            "Four of a Kind: x3\n"
            "Straight: x3\n"
            "Full House: x2\n"
            "Three of a Kind: x0.5\n"
            "Two Pair: x0\n"
            "One Pair: x0\n"
            "High Card: x0\n\n"
            "Commands:\n"
            "/dice bet <amount> - Roll dice with bet\n"
            "/dice - Roll dice (default bet 10)\n"
            "/dice 1 2 3 - Reroll selected dice\n"
            "/dice roll 1 2 3 - Reroll selected dice (same)\n"
            "/dice cashout - End game and take result"
        )
    
    def _finish_game(self, user_id, game, sender, file_queue, cache, user, win_amount, final_balance, is_reroll=False, reroll_indices=None, cashout=False, static=False):
        fresh_user = cache.get_user(user_id)
        if fresh_user:
            user = fresh_user
        
        game_state = game.get_game_state()
        game_state['old_dice'] = game.dice.copy() if is_reroll else None
        
        bet = float(game.bet)
        win_amount = float(win_amount)
        
        # Tworzymy user_info z odpowiednim opisem
        if win_amount > bet:
            # WYGRAŁ - zysk
            profit = win_amount - bet
            result_text = f"WON +${int(profit)}"
            user_info_before = self.create_user_info(sender, int(bet), 0, int(user["balance"] + bet), user)
            user_info_after = self.create_user_info(sender, int(bet), int(profit), int(final_balance), user)
        elif win_amount == bet:
            # BREAK EVEN
            result_text = f"BREAK EVEN (${int(win_amount)})"
            user_info_before = self.create_user_info(sender, int(bet), 0, int(user["balance"] + bet), user)
            user_info_after = self.create_user_info(sender, int(bet), 0, int(final_balance), user)
        elif win_amount > 0:
            # CZĘŚCIOWA STRATA (np. 0.5x) - przekazujemy ujemną wartość
            net_loss = bet - win_amount
            result_text = f"LOST ${int(net_loss)} (won ${int(win_amount)})"
            user_info_before = self.create_user_info(sender, int(bet), 0, int(user["balance"] + bet), user)
            # Przekazujemy ujemną wartość, żeby pokazać stratę
            user_info_after = self.create_user_info(sender, int(bet), -int(net_loss), int(final_balance), user)
        else:
            # PEŁNA PRZEGRANA (0x) - przekazujemy ujemną wartość
            result_text = f"LOST ${int(bet)}"
            user_info_before = self.create_user_info(sender, int(bet), 0, int(user["balance"] + bet), user)
            # Przekazujemy ujemną wartość, żeby pokazać stratę
            user_info_after = self.create_user_info(sender, int(bet), -int(bet), int(final_balance), user)
        
        anim_path = self.animation_generator.generate_dice_animation_frames(
            game_state,
            user_background_path=self.get_user_background_path(user_id, user),
            is_reroll=is_reroll,
            reroll_indices=reroll_indices,
            show_result=True,
            cashout=cashout,
            static=static
        )
        
        if anim_path:
            custom_kwargs = {
                'custom_text': f"DICE",
                'result_text': result_text
            }
            
            result_path, error = self.generate_animation(
                base_animation_path=anim_path,
                user_id=user_id,
                user=user,
                user_info_before=user_info_before,
                user_info_after=user_info_after,
                animated=not static and not cashout,
                frame_duration=50 if not static and not cashout else 0,
                last_frame_multiplier=130 if not static and not cashout else 0,
                custom_overlay_kwargs=custom_kwargs,
                show_win_text=True,
                win_text_height=35,
                font_scale=0.45,
                avatar_size=45,
                overlay_position='top'
            )
            
            if result_path:
                file_queue.put(result_path)
            
            try:
                os.remove(anim_path)
            except:
                pass
        
        if user_id in self.active_games:
            del self.active_games[user_id]
    
    def _show_waiting_state(self, user_id, game, sender, file_queue, cache, user, static=False):
        game_state = game.get_game_state()
        
        user_info = self.create_user_info(sender, game.bet, 0, user["balance"], user)
        
        anim_path = self.animation_generator.generate_dice_animation_frames(
            game_state,
            user_background_path=self.get_user_background_path(user_id, user),
            show_result=False,
            static=static
        )
        
        if anim_path:
            custom_kwargs = {
                'custom_text': f"DICE",
                'result_text': ""
            }
            
            result_path, error = self.generate_animation(
                base_animation_path=anim_path,
                user_id=user_id,
                user=user,
                user_info_before=user_info,
                user_info_after=user_info,
                animated=not static,
                frame_duration=50 if not static else 0,
                last_frame_multiplier=130 if not static else 0,
                custom_overlay_kwargs=custom_kwargs,
                show_win_text=False,
                font_scale=0.45,
                avatar_size=45,
                overlay_position='top'
            )
            
            if result_path:
                file_queue.put(result_path)
            
            try:
                os.remove(anim_path)
            except:
                pass
    
    def execute_game(self, command_name: str, args: List[str], file_queue, 
                    cache=None, sender: str = None, avatar_url: str = None) -> str:
        self.cache = cache
        
        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        
        if error:
            self.send_message_image(sender, file_queue, error, "Dice Error", cache, user_id)
            return ""
        
        if len(args) == 0:
            bet = 10
            if user["balance"] < bet:
                self.send_message_image(sender, file_queue, 
                                    f"Insufficient funds! You have ${user['balance']}, need ${bet}", 
                                    "Dice Error", cache, user_id)
                return ""
            
            if user_id in self.active_games:
                game = self.active_games[user_id]
                if not game.finished:
                    self.send_message_image(sender, file_queue, 
                                        "You already have an active game! Use /dice 1 2 3 or /dice cashout", 
                                        "Dice Error", cache, user_id)
                    return ""
                else:
                    del self.active_games[user_id]
            
            balance_before = user["balance"]
            new_balance = balance_before - bet
            self.update_user_balance(user_id, new_balance)
            
            game = DiceGame(user_id, sender, bet)
            game.roll_dice()
            self.active_games[user_id] = game
            
            self._show_waiting_state(user_id, game, sender, file_queue, cache, user)
            return ""
        
        static = False
        if args and args[-1].lower() == "x":
            static = True
            args = args[:-1]
        
        if len(args) == 0:
            help_text = self._get_help_text()
            self.send_message_image(sender, file_queue, help_text, "Dice Help", cache, user_id)
            return ""
        
        cmd = args[0].lower()
        
        is_roll_command = False
        if cmd == "roll" or cmd == "reroll" or cmd == "r":
            is_roll_command = True
            args = args[1:]
        elif len(args) >= 1:
            all_digits = True
            for arg in args:
                cleaned = re.sub(r'[,\s]+', '', arg)
                if not cleaned.isdigit():
                    all_digits = False
                    break
            if all_digits:
                is_roll_command = True
        
        if is_roll_command:
            if user_id not in self.active_games:
                self.send_message_image(sender, file_queue, 
                                    "No active game! Start one with /dice bet <amount> or /dice", 
                                    "Dice Error", cache, user_id)
                return ""
            
            game = self.active_games[user_id]
            
            if game.finished:
                self.send_message_image(sender, file_queue, 
                                    "Game already finished! Start a new one with /dice bet <amount>", 
                                    "Dice Error", cache, user_id)
                return ""
            
            if game.rerolls_used >= game.max_rerolls:
                self.send_message_image(sender, file_queue, 
                                    "You've used all rerolls! Use /dice cashout", 
                                    "Dice Error", cache, user_id)
                return ""
            
            if not game.rolled:
                self.send_message_image(sender, file_queue, 
                                    "Roll dice first! Use /dice bet <amount>", 
                                    "Dice Error", cache, user_id)
                return ""
            
            all_digits_list = []
            for arg in args:
                cleaned = re.sub(r'[,\s]+', '', arg)
                if cleaned.isdigit():
                    all_digits_list.extend([int(d) for d in cleaned])
            
            if not all_digits_list:
                self.send_message_image(sender, file_queue, 
                                    "Usage: /dice 1 2 3 or /dice roll 1 2 3", 
                                    "Dice Error", cache, user_id)
                return ""
            
            if len(all_digits_list) > 5:
                self.send_message_image(sender, file_queue, 
                                    "You can only reroll up to 5 dice! Use numbers 1-5", 
                                    "Dice Error", cache, user_id)
                return ""
            
            zero_based = [i-1 for i in all_digits_list if 1 <= i <= 5]
            
            if not zero_based:
                self.send_message_image(sender, file_queue, 
                                    "Invalid dice numbers! Use numbers 1-5", 
                                    "Dice Error", cache, user_id)
                return ""
            
            old_dice = game.dice.copy()
            
            indices_str = ' '.join(str(i) for i in all_digits_list)
            success = game.reroll(indices_str)
            
            if not success:
                self.send_message_image(sender, file_queue, 
                                    game.message, 
                                    "Dice Error", cache, user_id)
                return ""
            
            win_amount = game.win_amount
            final_balance = user["balance"] + win_amount
            
            if win_amount > 0:
                self.update_user_balance(user_id, final_balance)
                record_daily_win(self.cache, user_id, "dice", win_amount)
                record_weekly_win(self.cache, user_id, "dice", win_amount)
                record_monthly_win(self.cache, user_id, "dice", win_amount)
            else:
                self.update_user_balance(user_id, final_balance)
            
            self._finish_game(user_id, game, sender, file_queue, cache, user, win_amount, final_balance, True, zero_based, False, static)
            return ""
        
        if cmd == "bet":
            if len(args) < 2:
                self.send_message_image(sender, file_queue, 
                                    "Usage: /dice bet <amount>", 
                                    "Dice Error", cache, user_id)
                return ""
            
            try:
                bet = int(args[1])
            except ValueError:
                self.send_message_image(sender, file_queue, 
                                    "Bet must be a number!", 
                                    "Dice Error", cache, user_id)
                return ""
            
            if bet < 1:
                self.send_message_image(sender, file_queue, 
                                    "Bet must be at least 1 coin!", 
                                    "Dice Error", cache, user_id)
                return ""
            
            if user["balance"] < bet:
                self.send_message_image(sender, file_queue, 
                                    f"Insufficient funds! You have ${user['balance']}, need ${bet}", 
                                    "Dice Error", cache, user_id)
                return ""
            
            if user_id in self.active_games:
                game = self.active_games[user_id]
                if not game.finished:
                    self.send_message_image(sender, file_queue, 
                                        "You already have an active game! Use /dice 1 2 3 or /dice cashout", 
                                        "Dice Error", cache, user_id)
                    return ""
                else:
                    del self.active_games[user_id]
            
            balance_before = user["balance"]
            new_balance = balance_before - bet
            self.update_user_balance(user_id, new_balance)
            
            game = DiceGame(user_id, sender, bet)
            game.roll_dice()
            self.active_games[user_id] = game
            
            self._show_waiting_state(user_id, game, sender, file_queue, cache, user, static)
            return ""
        
        if cmd in ["cashout", "cash", "c"]:
            if user_id not in self.active_games:
                self.send_message_image(sender, file_queue, 
                                    "No active game! Start one with /dice bet <amount>", 
                                    "Dice Error", cache, user_id)
                return ""
            
            game = self.active_games[user_id]
            
            if game.finished:
                self.send_message_image(sender, file_queue, 
                                    "Game already finished! Start a new one with /dice bet <amount>", 
                                    "Dice Error", cache, user_id)
                return ""
            
            if not game.rolled:
                self.send_message_image(sender, file_queue, 
                                    "Roll dice first! Use /dice bet <amount>", 
                                    "Dice Error", cache, user_id)
                return ""
            
            success = game.cashout()
            
            if not success:
                self.send_message_image(sender, file_queue, 
                                    "Cannot cashout!", 
                                    "Dice Error", cache, user_id)
                return ""
            
            win_amount = game.win_amount
            final_balance = user["balance"] + win_amount
            
            if win_amount > 0:
                self.update_user_balance(user_id, final_balance)
                record_daily_win(self.cache, user_id, "dice", win_amount)
                record_weekly_win(self.cache, user_id, "dice", win_amount)
                record_monthly_win(self.cache, user_id, "dice", win_amount)
            else:
                self.update_user_balance(user_id, final_balance)
            
            self._finish_game(user_id, game, sender, file_queue, cache, user, win_amount, final_balance, False, None, True, static)
            return ""
        
        if cmd in ["start", "s", "bet2", "b"]:
            if len(args) < 2:
                self.send_message_image(sender, file_queue, 
                                    "Usage: /dice start <bet>", 
                                    "Dice Error", cache, user_id)
                return ""
            
            try:
                bet = int(args[1])
            except ValueError:
                self.send_message_image(sender, file_queue, 
                                    "Bet must be a number!", 
                                    "Dice Error", cache, user_id)
                return ""
            
            if bet < 1:
                self.send_message_image(sender, file_queue, 
                                    f"Minimum bet is 1 coin!", 
                                    "Dice Error", cache, user_id)
                return ""
            
            if user["balance"] < bet:
                self.send_message_image(sender, file_queue, 
                                    f"Insufficient funds! You have ${user['balance']}, need ${bet}", 
                                    "Dice Error", cache, user_id)
                return ""
            
            if user_id in self.active_games:
                game = self.active_games[user_id]
                if not game.finished:
                    self.send_message_image(sender, file_queue, 
                                        "You already have an active game! Use /dice 1 2 3 or /dice cashout", 
                                        "Dice Error", cache, user_id)
                    return ""
                else:
                    del self.active_games[user_id]
            
            balance_before = user["balance"]
            new_balance = balance_before - bet
            self.update_user_balance(user_id, new_balance)
            
            game = DiceGame(user_id, sender, bet)
            game.roll_dice()
            self.active_games[user_id] = game
            
            self._show_waiting_state(user_id, game, sender, file_queue, cache, user, static)
            return ""
        
        else:
            help_text = self._get_help_text()
            self.send_message_image(sender, file_queue, help_text, "Dice Help", cache, user_id)
            return ""


def register():
    logger.info("[Dice] Registering Dice plugin")
    plugin = DicePlugin()
    return {
        "name": "dice",
        "aliases": ["/d", "/dices"],
        "description": "Roll dice and win multipliers - five of a kind x9, four of a kind x3, full house x2, straight x3, three of a kind x0.5, two pair x0, one pair x0",
        "execute": plugin.execute_game
    }