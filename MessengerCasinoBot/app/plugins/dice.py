import os
import random
import re
from collections import Counter
from typing import List, Dict, Optional
from PIL import Image, ImageDraw, ImageSequence
from base_game_plugin import BaseGamePlugin
from logger import logger

class DiceGame:
    def __init__(self, user_id: str, sender_name: str, bet: int):
        self.user_id = user_id
        self.sender_name = sender_name
        self.bet = bet
        self.player_dice = []
        self.croupier_dice = []
        self.game_status = "initial_roll"
        self.message = "Rolling dice..."
        self.player_rerolls_used = 0
        self.croupier_rerolls_used = 0
        self.max_rerolls = 1
        self.winner = None
        self.win_amount = 0
        
        self.roll_history = {
            'initial': {'player': None, 'croupier': None},
            'player_rerolls': [],
            'croupier_rerolls': []
        }
    
    def roll_dice(self, initial=False, player_indices=None, croupier_indices=None, save_history=True):
        if initial:
            self.player_dice = [random.randint(1, 6) for _ in range(5)]
            self.croupier_dice = [random.randint(1, 6) for _ in range(5)]
            
            if save_history:
                self.roll_history['initial']['player'] = self.player_dice.copy()
                self.roll_history['initial']['croupier'] = self.croupier_dice.copy()
        else:
            if player_indices:
                old_player = self.player_dice.copy()
                for idx in player_indices:
                    if 0 <= idx < len(self.player_dice):
                        self.player_dice[idx] = random.randint(1, 6)
                
                if save_history:
                    self.roll_history['player_rerolls'].append({
                        'indices': player_indices.copy(),
                        'before': old_player,
                        'after': self.player_dice.copy()
                    })
            
            if croupier_indices:
                old_croupier = self.croupier_dice.copy()
                for idx in croupier_indices:
                    if 0 <= idx < len(self.croupier_dice):
                        self.croupier_dice[idx] = random.randint(1, 6)
                
                if save_history:
                    self.roll_history['croupier_rerolls'].append({
                        'indices': croupier_indices.copy(),
                        'before': old_croupier,
                        'after': self.croupier_dice.copy()
                    })
        
        self.check_game_status()
    
    def player_reroll(self, indices_str: str) -> bool:
        if self.game_status != "player_turn":
            self.message = "It's not your turn!"
            return False
        
        if self.player_rerolls_used >= self.max_rerolls:
            self.message = f"You've used all {self.max_rerolls} rerolls!"
            return False
        
        indices = self._parse_indices(indices_str)
        
        if not indices:
            self.message = "Invalid dice numbers! Use: /dice 1,2,3 or /dice 1 2 3"
            return False
        
        zero_based = [i-1 for i in indices if 1 <= i <= 5]
        
        if not zero_based:
            self.message = "Dice numbers must be between 1 and 5"
            return False
        
        self.player_rerolls_used += 1
        self.roll_dice(player_indices=zero_based)
        
        if self.game_status == "player_turn":
            self.game_status = "croupier_turn"
            self.message = "Croupier's turn..."
        
        return True
    
    def player_stand(self) -> bool:
        if self.game_status != "player_turn":
            self.message = "It's not your turn!"
            return False
        
        self.game_status = "croupier_turn"
        self.message = "Croupier's turn..."
        return True
    
    def croupier_turn(self):
        if self.game_status != "croupier_turn":
            return
        
        while self.croupier_rerolls_used < self.max_rerolls:
            player_score = self._evaluate_hand(self.player_dice)
            
            indices_to_reroll = self._get_reroll_indices(self.croupier_dice, player_score)
            
            if not indices_to_reroll:
                break
            
            self.croupier_rerolls_used += 1
            self.roll_dice(croupier_indices=indices_to_reroll)
        
        self.game_status = "finished"
        self._determine_winner()
    
    def _determine_winner(self):
        player_score = self._evaluate_hand(self.player_dice)
        croupier_score = self._evaluate_hand(self.croupier_dice)
        
        if croupier_score > player_score:
            self.winner = "croupier"
            self.message = "Croupier wins!"
            self.win_amount = -self.bet
        elif player_score > croupier_score:
            self.winner = "player"
            self.message = "You win!"
            self.win_amount = self.bet
        else:
            self.winner = "tie"
            self.message = "It's a tie!"
            self.win_amount = 0

    def check_game_status(self):
        
        if self._is_perfect_hand(self.player_dice):
            self.game_status = "finished"
            self.winner = "player"
            self.message = "Perfect hand! You win immediately!"
            self.win_amount = self.bet
            return
        
        if self.game_status == "initial_roll":
            self.game_status = "player_turn"
            self.message = "Your turn - select dice to reroll or wait"
            return
        
        if self.game_status == "player_turn":
            return
        
        if self.game_status == "croupier_turn":
            if self.croupier_rerolls_used < self.max_rerolls:
                pass
            return
        
    def _parse_indices(self, indices_str: str) -> List[int]:
        indices = []
        
        if ',' in indices_str:
            parts = indices_str.split(',')
            for part in parts:
                part = part.strip()
                if part.isdigit():
                    indices.append(int(part))
        else:
            parts = indices_str.split()
            for part in parts:
                part = part.strip()
                if part.isdigit():
                    indices.append(int(part))
        
        return indices
    
    def _evaluate_hand(self, dice: List[int]) -> int:
        counts = Counter(dice)
        sorted_dice = sorted(dice)
        
        if len(counts) == 1:
            return 9000 + dice[0] * 100
        if 4 in counts.values():
            four_value = [k for k, v in counts.items() if v == 4][0]
            return 8000 + four_value * 100
        if 3 in counts.values() and 2 in counts.values():
            three_value = [k for k, v in counts.items() if v == 3][0]
            return 7000 + three_value * 100
        if self._is_straight(sorted_dice):
            return 6000 + max(dice) * 100
        if 3 in counts.values():
            three_value = [k for k, v in counts.items() if v == 3][0]
            return 5000 + three_value * 100
        if list(counts.values()).count(2) == 2:
            pairs = sorted([k for k, v in counts.items() if v == 2], reverse=True)
            return 4000 + pairs[0] * 100 + pairs[1] * 10
        if 2 in counts.values():
            pair_value = [k for k, v in counts.items() if v == 2][0]
            return 3000 + pair_value * 100
        return 2000 + max(dice) * 100 + sum(dice) % 100
    
    def _get_hand_type(self, dice: List[int]) -> str:
        counts = Counter(dice)
        sorted_dice = sorted(dice)
        
        if len(counts) == 1:
            return f"Five of a Kind ({dice[0]})"
        if 4 in counts.values():
            return "Four of a Kind"
        if 3 in counts.values() and 2 in counts.values():
            return "Full House"
        if self._is_straight(sorted_dice):
            return "Straight"
        if 3 in counts.values():
            return "Three of a Kind"
        if list(counts.values()).count(2) == 2:
            return "Two Pair"
        if 2 in counts.values():
            return "One Pair"
        return "High Card"
    
    def _is_straight(self, sorted_dice: List[int]) -> bool:
        return all(sorted_dice[i] == sorted_dice[0] + i for i in range(5))
    
    def _is_perfect_hand(self, dice: List[int]) -> bool:
        return len(set(dice)) == 1

    def _get_reroll_indices(self, dice: List[int], player_score: int) -> List[int]:
        counts = Counter(dice)
        current_score = self._evaluate_hand(dice)
        
        if current_score > player_score:
            return []
        
        if len(counts) == 1:
            return []
        
        if 4 in counts.values():
            keep_value = [k for k, v in counts.items() if v == 4][0]
            return [i for i, val in enumerate(dice) if val != keep_value]
        
        if 3 in counts.values() and 2 in counts.values():
            
            if player_score >= 8000:
                three_value = [k for k, v in counts.items() if v == 3][0]
                pair_value = [k for k, v in counts.items() if v == 2][0]
                return [i for i, val in enumerate(dice) if val == pair_value]
            else:
                return []
        
        if 3 in counts.values():
            keep_value = [k for k, v in counts.items() if v == 3][0]
            return [i for i, val in enumerate(dice) if val != keep_value]
        
        if list(counts.values()).count(2) == 2:
            if player_score >= 7000:
                pairs = [k for k, v in counts.items() if v == 2]
                higher_pair = max(pairs)
                lower_pair = min(pairs)
                return [i for i, val in enumerate(dice) if val == lower_pair]
            else:
                pair_values = [k for k, v in counts.items() if v == 2]
                return [i for i, val in enumerate(dice) if val not in pair_values]
        
        if 2 in counts.values():
            pair_value = [k for k, v in counts.items() if v == 2][0]
            return [i for i, val in enumerate(dice) if val != pair_value]
        
        sorted_with_idx = sorted([(val, i) for i, val in enumerate(dice)], reverse=True)
        return [idx for val, idx in sorted_with_idx[1:]]

    def get_game_state(self) -> Dict:
        return {
            'player_dice': self.player_dice.copy(),
            'croupier_dice': self.croupier_dice.copy(),
            'player_hand': self._get_hand_type(self.player_dice),
            'croupier_hand': self._get_hand_type(self.croupier_dice),
            'player_score': self._evaluate_hand(self.player_dice),
            'croupier_score': self._evaluate_hand(self.croupier_dice),
            'game_status': self.game_status,
            'message': self.message,
            'bet': self.bet,
            'player_rerolls_left': self.max_rerolls - self.player_rerolls_used,
            'croupier_rerolls_left': self.max_rerolls - self.croupier_rerolls_used,
            'winner': self.winner,
            'win_amount': self.win_amount,
            'roll_history': self.roll_history
        }


class DiceAnimationGenerator:
    def __init__(self, text_renderer, dice_animations):
        self.text_renderer = text_renderer
        self.dice_animations = dice_animations
        self.dice_animation_frames = {}
        
        self._load_animation_frames()
        
        self.CARD_WIDTH = 500
        self.CARD_HEIGHT = 400
        self.DICE_SIZE = 70
        self.DICE_SPACING = 10
        self.PADDING = 30
        
        self.COLORS = {
            'bg_dark': (10, 10, 20, 255),
            'player_area': (30, 40, 50, 200),
            'croupier_area': (40, 30, 50, 200),
            'text_primary': (255, 255, 255, 255),
            'text_secondary': (180, 180, 180, 255),
            'text_success': (80, 200, 120, 255),
            'text_danger': (255, 80, 80, 255),
            'text_highlight': (255, 215, 0, 255),
            'border': (70, 70, 90, 255),
            'highlight_reroll': (100, 200, 255, 150),
            'hand_bg': (0, 0, 0, 180)
        }
    
    def _load_animation_frames(self):
        logger.info("[Dice] Starting to load animation frames...")
        
        for value, path in self.dice_animations.items():
            try:
                logger.info(f"[Dice] Loading animation for dice_{value} from {path}")
                frames = []
                
                if not os.path.exists(path):
                    logger.error(f"[Dice] File does not exist: {path}")
                    self.dice_animation_frames[value] = []
                    continue
                
                with Image.open(path) as img:
                    logger.info(f"[Dice] Image format: {img.format}, mode: {img.mode}")
                    logger.info(f"[Dice] Image size: {img.size}")
                    logger.info(f"[Dice] Is animated: {getattr(img, 'is_animated', False)}")
                    logger.info(f"[Dice] N frames: {getattr(img, 'n_frames', 1)}")
                    
                    frame_count = 0
                    for frame in ImageSequence.Iterator(img):
                        frame_rgba = frame.convert('RGBA')
                        frames.append(frame_rgba)
                        frame_count += 1
                        logger.info(f"[Dice] Loaded frame {frame_count}")
                    
                    logger.info(f"[Dice] Total frames loaded: {frame_count}")
                
                self.dice_animation_frames[value] = frames
                logger.info(f"[Dice] FINAL: Loaded {len(frames)} frames for dice_{value}")
                
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
    
    def draw_areas(self, img):
        draw = ImageDraw.Draw(img)
        
        croupier_y = self.PADDING
        croupier_height = 150
        draw.rectangle([self.PADDING, croupier_y, self.CARD_WIDTH - self.PADDING, croupier_y + croupier_height],
                      fill=self.COLORS['croupier_area'], outline=self.COLORS['border'], width=2)
        
        player_y = self.CARD_HEIGHT - self.PADDING - 150
        player_height = 150
        draw.rectangle([self.PADDING, player_y, self.CARD_WIDTH - self.PADDING, player_y + player_height],
                      fill=self.COLORS['player_area'], outline=self.COLORS['border'], width=2)
        
        if self.text_renderer:
            croupier_label = self.text_renderer.render_text("CROUPIER", 20, self.COLORS['text_secondary'])
            img.alpha_composite(croupier_label, (self.PADDING + 10, croupier_y + 5))
            
            player_label = self.text_renderer.render_text("PLAYER", 20, self.COLORS['text_secondary'])
            img.alpha_composite(player_label, (self.PADDING + 10, player_y + 5))
    
    def draw_hand_label(self, img, hand_text: str, is_croupier: bool):
        if not self.text_renderer:
            return
        
        if is_croupier:
            area_y = self.PADDING
            area_height = 150
        else:
            area_y = self.CARD_HEIGHT - self.PADDING - 150
            area_height = 150
        
        hand_display = f"{hand_text}"
        text_img = self.text_renderer.render_text(hand_display, 16, self.COLORS['text_highlight'])
        
        padding = 5
        bg_width = text_img.width + padding * 2
        bg_height = text_img.height + padding * 2
        
        bg = Image.new('RGBA', (bg_width, bg_height), self.COLORS['hand_bg'])
        
        x = self.CARD_WIDTH - self.PADDING - bg_width - 10
        y = area_y + 10
        
        img.alpha_composite(bg, (x, y))
        img.alpha_composite(text_img, (x + padding, y + padding))
    
    def draw_single_dice(self, img, value, x, y, frame_idx=0, use_last_frame=False, is_rerolling=False):
        if value == 0:
            return
        
        frames = self.dice_animation_frames.get(value, [])
        
        if not frames:
            logger.warning(f"[Dice] No frames for value {value}, using fallback")
            draw = ImageDraw.Draw(img)
            draw.ellipse([x, y, x + self.DICE_SIZE, y + self.DICE_SIZE], 
                        fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=2)
            if self.text_renderer:
                text_img = self.text_renderer.render_text(str(value), 30, (0, 0, 0, 255))
                text_x = x + (self.DICE_SIZE - text_img.width) // 2
                text_y = y + (self.DICE_SIZE - text_img.height) // 2
                img.alpha_composite(text_img, (text_x, text_y))
            return
        
        if not is_rerolling or use_last_frame:
            dice_img = frames[-1]
        else:
            idx = frame_idx % len(frames)
            dice_img = frames[idx]
        
        dice_img = dice_img.resize((self.DICE_SIZE, self.DICE_SIZE))
        img.alpha_composite(dice_img, (x, y))
    
    def _get_dice_x(self, index: int, is_croupier: bool) -> int:
        total_width = 5 * self.DICE_SIZE + 4 * self.DICE_SPACING
        start_x = (self.CARD_WIDTH - total_width) // 2
        return start_x + index * (self.DICE_SIZE + self.DICE_SPACING)
    
    def _get_dice_y(self, is_croupier: bool) -> int:
        if is_croupier:
            area_y = self.PADDING
            area_height = 150
        else:
            area_y = self.CARD_HEIGHT - self.PADDING - 150
            area_height = 150
        
        return area_y + (area_height - self.DICE_SIZE) // 2
    
    def generate_dice_animation_frames(self, game_state, action_type, player_reroll_indices=None, 
                                      croupier_reroll_indices=None, user_background_path=None) -> str:
        logger.info(f"[Dice] Generating animation for action: {action_type}")
        frames = []
        
        ANIMATION_LENGTH = 20
        HOLD_FRAMES = 8
        
        player_dice = game_state['player_dice']
        croupier_dice = game_state['croupier_dice']
        
        if action_type == 'initial':
            for frame_idx in range(ANIMATION_LENGTH):
                img = self.create_base_image(user_background_path)
                self.draw_areas(img)
                
                for i in range(5):
                    x = self._get_dice_x(i, True)
                    y = self._get_dice_y(True)
                    self.draw_single_dice(
                        img, random.randint(1, 6), x, y, 
                        frame_idx=frame_idx, is_rerolling=True
                    )
                
                frames.append(img)
            
            for frame_idx in range(ANIMATION_LENGTH):
                img = self.create_base_image(user_background_path)
                self.draw_areas(img)
                
                for i in range(5):
                    x = self._get_dice_x(i, True)
                    y = self._get_dice_y(True)
                    self.draw_single_dice(
                        img, croupier_dice[i], x, y, 
                        use_last_frame=True
                    )
                
                for i in range(5):
                    x = self._get_dice_x(i, False)
                    y = self._get_dice_y(False)
                    self.draw_single_dice(
                        img, random.randint(1, 6), x, y, 
                        frame_idx=frame_idx, is_rerolling=True
                    )
                
                self.draw_hand_label(img, game_state['croupier_hand'], True)
                
                frames.append(img)
            
            for _ in range(HOLD_FRAMES):
                img = self.create_base_image(user_background_path)
                self.draw_areas(img)
                
                for i in range(5):
                    x = self._get_dice_x(i, True)
                    y = self._get_dice_y(True)
                    self.draw_single_dice(
                        img, croupier_dice[i], x, y, 
                        use_last_frame=True
                    )
                
                for i in range(5):
                    x = self._get_dice_x(i, False)
                    y = self._get_dice_y(False)
                    self.draw_single_dice(
                        img, player_dice[i], x, y, 
                        use_last_frame=True
                    )
                
                self.draw_hand_label(img, game_state['player_hand'], False)
                self.draw_hand_label(img, game_state['croupier_hand'], True)
                
                frames.append(img)
        
        elif action_type == 'full_turn' and player_reroll_indices is not None:
            history = game_state.get('roll_history', {})
            
            player_before = game_state['player_dice'].copy()
            croupier_before = game_state['croupier_dice'].copy()
            
            player_rerolls = history.get('player_rerolls', [])
            if player_rerolls:
                player_before = player_rerolls[-1].get('before', player_before)
            
            croupier_rerolls = history.get('croupier_rerolls', [])
            if croupier_rerolls:
                croupier_before = croupier_rerolls[-1].get('before', croupier_before)
                if 'indices' in croupier_rerolls[-1]:
                    croupier_reroll_indices = croupier_rerolls[-1]['indices']
            
            for _ in range(HOLD_FRAMES):
                img = self.create_base_image(user_background_path)
                self.draw_areas(img)
                
                for i in range(5):
                    x = self._get_dice_x(i, True)
                    y = self._get_dice_y(True)
                    self.draw_single_dice(
                        img, croupier_before[i], x, y, 
                        use_last_frame=True
                    )
                
                for i in range(5):
                    x = self._get_dice_x(i, False)
                    y = self._get_dice_y(False)
                    self.draw_single_dice(
                        img, player_before[i], x, y, 
                        use_last_frame=True
                    )
                
                self.draw_hand_label(img, game_state.get('player_hand_before', '?'), False)
                self.draw_hand_label(img, game_state.get('croupier_hand_before', '?'), True)
                
                frames.append(img)
            
            for frame_idx in range(ANIMATION_LENGTH):
                img = self.create_base_image(user_background_path)
                self.draw_areas(img)
                
                for i in range(5):
                    x = self._get_dice_x(i, True)
                    y = self._get_dice_y(True)
                    self.draw_single_dice(
                        img, croupier_before[i], x, y, 
                        use_last_frame=True
                    )
                
                for i in range(5):
                    x = self._get_dice_x(i, False)
                    y = self._get_dice_y(False)
                    is_rerolling = i in player_reroll_indices
                    
                    if is_rerolling:
                        self.draw_single_dice(
                            img, random.randint(1, 6), x, y, 
                            frame_idx=frame_idx, is_rerolling=True
                        )
                    else:
                        self.draw_single_dice(
                            img, player_before[i], x, y, 
                            use_last_frame=True
                        )
                
                self.draw_hand_label(img, '?', False)
                self.draw_hand_label(img, game_state.get('croupier_hand_before', '?'), True)
                
                frames.append(img)
            
            for _ in range(HOLD_FRAMES // 2):
                img = self.create_base_image(user_background_path)
                self.draw_areas(img)
                
                for i in range(5):
                    x = self._get_dice_x(i, True)
                    y = self._get_dice_y(True)
                    self.draw_single_dice(
                        img, croupier_before[i], x, y, 
                        use_last_frame=True
                    )
                
                for i in range(5):
                    x = self._get_dice_x(i, False)
                    y = self._get_dice_y(False)
                    self.draw_single_dice(
                        img, player_dice[i], x, y, 
                        use_last_frame=True
                    )
                
                self.draw_hand_label(img, game_state['player_hand'], False)
                self.draw_hand_label(img, game_state.get('croupier_hand_before', '?'), True)
                
                frames.append(img)
            
            if croupier_rerolls and croupier_reroll_indices is not None:
                for frame_idx in range(ANIMATION_LENGTH):
                    img = self.create_base_image(user_background_path)
                    self.draw_areas(img)
                    
                    for i in range(5):
                        x = self._get_dice_x(i, True)
                        y = self._get_dice_y(True)
                        is_rerolling = i in croupier_reroll_indices
                        
                        if is_rerolling:
                            self.draw_single_dice(
                                img, random.randint(1, 6), x, y, 
                                frame_idx=frame_idx, is_rerolling=True
                            )
                        else:
                            self.draw_single_dice(
                                img, croupier_before[i], x, y, 
                                use_last_frame=True
                            )
                    
                    for i in range(5):
                        x = self._get_dice_x(i, False)
                        y = self._get_dice_y(False)
                        self.draw_single_dice(
                            img, player_dice[i], x, y, 
                            use_last_frame=True
                        )
                    
                    self.draw_hand_label(img, game_state['player_hand'], False)
                    self.draw_hand_label(img, '?', True)
                    
                    frames.append(img)
            
            for _ in range(HOLD_FRAMES):
                img = self.create_base_image(user_background_path)
                self.draw_areas(img)
                
                for i in range(5):
                    x = self._get_dice_x(i, True)
                    y = self._get_dice_y(True)
                    self.draw_single_dice(
                        img, croupier_dice[i], x, y, 
                        use_last_frame=True
                    )
                
                for i in range(5):
                    x = self._get_dice_x(i, False)
                    y = self._get_dice_y(False)
                    self.draw_single_dice(
                        img, player_dice[i], x, y, 
                        use_last_frame=True
                    )
                
                self.draw_hand_label(img, game_state['player_hand'], False)
                self.draw_hand_label(img, game_state['croupier_hand'], True)
                
                frames.append(img)
        
        if frames:
            temp_path = os.path.join(os.path.dirname(__file__), "..", "results", 
                                    f"dice_{action_type}_{random.randint(1000,9999)}.webp")
            
            logger.info(f"[Dice] Saving animation with {len(frames)} frames to {temp_path}")
            
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
                logger.info(f"[Dice] Successfully saved animation")
                return temp_path
            except Exception as e:
                logger.error(f"[Dice] Error saving animation: {e}")
                return None
        
        return None


class DicePlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="dice")
        self.active_games = {}
        self.min_bet = 10
        self.dice_animations = {}
        self.animation_generator = None
        
        self._load_dice_animations()
        self.animation_generator = DiceAnimationGenerator(self.text_renderer, self.dice_animations)
    
    def _load_dice_animations(self):
        dice_folder = self.get_asset_path("dice")
        
        logger.info(f"[Dice] Looking for dice animations in: {dice_folder}")
        
        if not os.path.exists(dice_folder):
            logger.error(f"[Dice] Dice folder not found: {dice_folder}")
            return
        
        try:
            files = os.listdir(dice_folder)
            logger.info(f"[Dice] Files in dice folder: {files}")
        except Exception as e:
            logger.error(f"[Dice] Error listing dice folder: {e}")
        
        for i in range(1, 7):
            animation_path = os.path.join(dice_folder, f"dice_{i}.webp")
            if os.path.exists(animation_path):
                self.dice_animations[i] = animation_path
                logger.info(f"[Dice] Found dice animation: dice_{i}.webp")
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
    
    def get_custom_overlay(self, **kwargs):
        try:
            frame_width = kwargs.get('frame_width', 500)
            frame_height = kwargs.get('frame_height', 400)
            
            overlay = Image.new('RGBA', (frame_width, frame_height), (0, 0, 0, 0))
            
            return {
                'before': {
                    'image': overlay,
                    'position': (0, 0),
                    'type': 'before',
                    'per_frame': True
                },
                'after': {
                    'image': overlay,
                    'position': (0, 0),
                    'type': 'after',
                    'per_frame': True
                }
            }
            
        except Exception as e:
            logger.error(f"[Dice] Error in get_custom_overlay: {e}", exc_info=True)
            return None
        
    def _is_reroll_pattern(self, cmd: str, args: List[str]) -> bool:
        first_arg = args[0] if args else ""
        
        # Format "/dice 1,2,3" lub "/dice 1 2 3" lub "/dice 123"
        if re.match(r'^[\d,\s]+$', first_arg):
            return True
        
        # Format "/dice r 1,2,3" lub "/dice reroll 1,2,3"
        if len(args) >= 2 and cmd in ["r", "reroll", "roll"]:
            return True
        
        return False

    def _parse_dice_indices(self, args: List[str]) -> Optional[List[int]]:
        indices = []
        
        full_args = ' '.join(args)
        
        full_args = re.sub(r'^(r|reroll|roll)\s+', '', full_args, flags=re.IGNORECASE)
        
        digits_only = re.sub(r'[^\d]', '', full_args)
        
        if digits_only:
            return [int(d) for d in digits_only if 1 <= int(d) <= 5]
        
        return None
   
    def _handle_status_or_help(self, sender: str, file_queue, cache, avatar_url: str) -> str:
        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        
        if error:
            self.send_message_image(sender, file_queue, error, "Dice Error", cache, user_id)
            return ""
        
        if user_id in self.active_games:
            game = self.active_games[user_id]
            return self._show_game_status(game, sender, file_queue, cache, user_id, user)
        else:
            help_text = self._get_help_text()
            self.send_message_image(sender, file_queue, help_text, "Dice Help", cache, user_id)
            return ""

    def execute_game(self, command_name: str, args: List[str], file_queue, 
                    cache=None, sender: str = None, avatar_url: str = None) -> str:
        self.cache = cache
        
        static_mode = False
        if args and args[-1].lower() == 'x':
            static_mode = True
            args = args[:-1]
        
        if len(args) == 0:
            return self._handle_status_or_help(sender, file_queue, cache, avatar_url, static_mode)
        
        cmd = args[0].lower()
        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        
        if error:
            self.send_message_image(sender, file_queue, error, "Dice Error", cache, user_id)
            return ""
        
        if cmd in ["start", "s", "bet", "b"]:
            return self._handle_start_command(args, sender, file_queue, cache, avatar_url, user_id, user, static_mode)
        
        if user_id not in self.active_games:
            self.send_message_image(sender, file_queue, 
                                "You don't have an active game! Start one with /dice start <bet>", 
                                "No Game", cache, user_id)
            return ""
        
        game = self.active_games[user_id]
        
        if self._is_reroll_pattern(cmd, args):
            return self._handle_reroll_command(args, game, sender, file_queue, cache, user_id, user, static_mode)
        
        if cmd in ["stand", "wait", "check", "cashout", "stop", "pass"]:
            return self._handle_stand_command(game, sender, file_queue, cache, user_id, user, static_mode)
        
        return self._show_game_status(game, sender, file_queue, cache, user_id, user, static_mode)

    def _handle_reroll_command(self, args: List[str], game, sender: str, file_queue, 
                            cache, user_id: str, user: Dict, static_mode: bool = False) -> str:
        
        if game.game_status != "player_turn":
            return ""
        
        if game.player_rerolls_used >= game.max_rerolls:
            return ""
        
        indices = self._parse_dice_indices(args)
        
        if not indices:
            return ""
        
        zero_based = [i-1 for i in indices if 1 <= i <= 5]
        
        if not zero_based:
            return ""
        
        zero_based = list(set(zero_based))
        old_player_dice = game.player_dice.copy()
        old_croupier_dice = game.croupier_dice.copy()
        
        success = game.player_reroll(','.join(str(i+1) for i in zero_based))
        
        if not success:
            return ""
        
        if game.game_status == "croupier_turn":
            game.croupier_turn()
        
        final_balance = user["balance"]
        win_amount = 0
        
        if game.winner == "player":
            win_amount = game.win_amount
            final_balance = user["balance"] + 2 * win_amount
        elif game.winner == "croupier":
            win_amount = -game.bet
            final_balance = user["balance"]
        else:
            final_balance = user["balance"] + game.bet
            win_amount = 0
        
        if game.winner == "player":
            self.update_user_balance(user_id, final_balance)
            if win_amount < 0:
                self.cache.add_experience(user_id, win_amount, sender, file_queue)
        elif game.winner == "tie":
            self.update_user_balance(user_id, final_balance)
        
        fresh_user = cache.get_user(user_id)
        if fresh_user:
            user = fresh_user
        
        game_state = game.get_game_state()
        game_state['player_hand_before'] = game._get_hand_type(old_player_dice)
        game_state['croupier_hand_before'] = game._get_hand_type(old_croupier_dice)
        
        user_info_before = self.create_user_info(sender, game.bet, 0, user["balance"] - game.win_amount if game.winner == "player" else user["balance"], user)
        user_info_after = self.create_user_info(sender, game.bet, win_amount, final_balance, user)
        
        action_type = 'initial' if static_mode else 'full_turn'
        player_indices = None if static_mode else zero_based
        
        anim_path = self.animation_generator.generate_dice_animation_frames(
            game_state, action_type,
            player_reroll_indices=player_indices,
            user_background_path=self.get_user_background_path(user_id, user)
        )
        
        if anim_path:
            custom_kwargs = {
                'custom_text': f"DICE GAME",
                'result_text': ""
            }
            
            result_path, error = self.generate_animation(
                base_animation_path=anim_path,
                user_id=user_id,
                user=user,
                user_info_before=user_info_before,
                user_info_after=user_info_after,
                animated=not static_mode,
                frame_duration=50,
                last_frame_multiplier=130,
                custom_overlay_kwargs=custom_kwargs,
                show_win_text=True,
                win_text_height=180,
                font_scale=0.9,
                avatar_size=60
            )
            
            if result_path:
                file_queue.put(result_path)
            
            try:
                os.remove(anim_path)
            except:
                pass
        
        if game.game_status == "finished":
            self.active_games.pop(user_id, None)
        
        return ""

    def _handle_stand_command(self, game, sender: str, file_queue, cache, 
                            user_id: str, user: Dict, static_mode: bool = False) -> str:
                
        if game.game_status != "player_turn":
            return ""
        
        old_croupier_dice = game.croupier_dice.copy()
        
        success = game.player_stand()
        
        if not success:
            return ""
        
        game.croupier_turn()
        
        final_balance = user["balance"]
        win_amount = 0
        
        if game.winner == "player":
            win_amount = game.win_amount
            final_balance = user["balance"] + 2 * win_amount
        elif game.winner == "croupier":
            win_amount = -game.bet
            final_balance = user["balance"]
        else:
            final_balance = user["balance"] + game.bet
            win_amount = 0
        
        if game.winner == "player":
            self.update_user_balance(user_id, final_balance)
            if win_amount < 0:
                self.cache.add_experience(user_id, win_amount, sender, file_queue)
        elif game.winner == "tie":
            self.update_user_balance(user_id, final_balance)
        
        fresh_user = cache.get_user(user_id)
        if fresh_user:
            user = fresh_user
        
        game_state = game.get_game_state()
        game_state['croupier_hand_before'] = game._get_hand_type(old_croupier_dice)
        
        user_info_before = self.create_user_info(sender, game.bet, 0, user["balance"] - game.win_amount if game.winner == "player" else user["balance"], user)
        user_info_after = self.create_user_info(sender, game.bet, win_amount, final_balance, user)
        
        action_type = 'initial' if static_mode else 'full_turn'
        player_indices = None if static_mode else []
        
        anim_path = self.animation_generator.generate_dice_animation_frames(
            game_state, action_type,
            player_reroll_indices=player_indices,
            user_background_path=self.get_user_background_path(user_id, user)
        )
        
        if anim_path:
            custom_kwargs = {
                'custom_text': f"DICE GAME",
                'result_text': ""
            }
            
            result_path, error = self.generate_animation(
                base_animation_path=anim_path,
                user_id=user_id,
                user=user,
                user_info_before=user_info_before,
                user_info_after=user_info_after,
                animated=not static_mode,
                frame_duration=50,
                last_frame_multiplier=130,
                custom_overlay_kwargs=custom_kwargs,
                show_win_text=True,
                win_text_height=180,
                font_scale=0.9,
                avatar_size=60
            )
            
            if result_path:
                file_queue.put(result_path)
            
            try:
                os.remove(anim_path)
            except:
                pass
        
        if game.game_status == "finished":
            self.active_games.pop(user_id, None)
        
        return ""

    def _handle_start_command(self, args: List[str], sender: str, file_queue, 
                            cache, avatar_url: str, user_id: str, user: Dict, static_mode: bool = False) -> str:
        
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
        
        if bet < self.min_bet:
            self.send_message_image(sender, file_queue, 
                                f"Minimum bet is ${self.min_bet}!", 
                                "Dice Error", cache, user_id)
            return ""
        
        if user_id in self.active_games:
            self.send_message_image(sender, file_queue, 
                                "You already have an active game! Use /dice to see status.", 
                                "Dice Error", cache, user_id)
            return ""
        
        if user["balance"] < bet:
            self.send_message_image(sender, file_queue, 
                                f"Insufficient funds! You have ${user['balance']}, need ${bet}", 
                                "Dice Error", cache, user_id)
            return ""
        
        balance_before = user["balance"]
        new_balance = balance_before - bet
        self.update_user_balance(user_id, new_balance)
        
        game = DiceGame(user_id, sender, bet)
        game.max_rerolls = 1
        game.roll_dice(initial=True)
        self.active_games[user_id] = game
        
        logger.info(f"[Dice] New game started for {sender}, bet: {bet}, balance: {balance_before} -> {new_balance}")
        
        game_state = game.get_game_state()
        user_info_after = self.create_user_info(sender, bet, 0, new_balance, user)
        
        anim_path = self.animation_generator.generate_dice_animation_frames(
            game_state, 'initial',
            user_background_path=self.get_user_background_path(user_id, user)
        )
        
        if anim_path:
            custom_kwargs = {
                'custom_text': f"NEW GAME - BET: ${bet}",
                'result_text': "Rolling dice..."
            }
            
            result_path, error = self.generate_animation(
                base_animation_path=anim_path,
                user_id=user_id,
                user=user,
                user_info_before=user_info_after,
                user_info_after=user_info_after,
                animated=not static_mode,
                frame_duration=50,
                last_frame_multiplier=130,
                custom_overlay_kwargs=custom_kwargs,
                show_win_text=False,
                font_scale=0.9,
                avatar_size=60
            )
            
            if result_path:
                file_queue.put(result_path)
            
            try:
                os.remove(anim_path)
            except:
                pass
        
        if game.game_status == "finished":
            self._finish_game(game, sender, file_queue, cache, user_id, user)
        
        return f"Game started! Bet: ${bet}"

    def _show_game_status(self, game, sender: str, file_queue, cache, user_id: str, user: Dict, static_mode: bool = False) -> str:
        game_state = game.get_game_state()
        
        anim_path = self.animation_generator.generate_dice_animation_frames(
            game_state, 'initial',
            user_background_path=self.get_user_background_path(user_id, user)
        )
        
        if anim_path:
            user_info = self.create_user_info(sender, game.bet, 0, user["balance"], user)
            
            status_message = f"Game Status"
            if game.game_status == "player_turn":
                status_message = f"Your turn! Rerolls left: {game.max_rerolls - game.player_rerolls_used}"
            elif game.game_status == "finished":
                status_message = game.message
            
            custom_kwargs = {
                'custom_text': f"GAME STATUS",
                'result_text': status_message
            }
            
            result_path, error = self.generate_animation(
                base_animation_path=anim_path,
                user_id=user_id,
                user=user,
                user_info_before=user_info,
                user_info_after=user_info,
                animated=False,
                frame_duration=0,
                last_frame_multiplier=130,
                custom_overlay_kwargs=custom_kwargs,
                show_win_text=False,
                font_scale=0.9,
                avatar_size=60
            )
            
            if result_path:
                file_queue.put(result_path)
            
            try:
                os.remove(anim_path)
            except:
                pass
        
        return ""

    def _get_help_text(self) -> str:
        return (
            "DICE GAME\n\n"
            f"Minimum bet: ${self.min_bet}\n\n"
            "**How to play:**\n"
            "1. Both players roll 5 dice\n"
            "2. You see croupier's dice\n"
            "3. You can reroll selected dice (1 reroll max)\n"
            "4. Croupier rerolls (1 reroll max) to try to beat you\n\n"
            "**Commands:**\n"
            "• /dice start <bet> - Start new game\n"
            "• /dice 1,2,3 - Reroll selected dice\n"
            "• /dice 1 2 3 - Reroll selected dice\n"
            "• /dice 123 - Reroll selected dice\n"
            "• /dice stand - Stop rerolling and let croupier play\n"
            "• /dice - Show current game status"
        )


def register():
    logger.info("[Dice] Registering Dice plugin")
    plugin = DicePlugin()
    return {
        "name": "dice",
        "aliases": ["/d", "/dices"],
        "description": "Dice Poker Game - reroll dice to beat the croupier",
        "execute": plugin.execute_game
    }