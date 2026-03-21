import os
import random
from PIL import Image, ImageDraw
from base_game_plugin import BaseGamePlugin
from logger import logger
import time
import json

class BlackjackTableGenerator:
    def __init__(self, text_renderer=None):
        self.loaded_elements = {}
        self.text_renderer = text_renderer
            
    def load_elements(self, elements_folder, assets_folder):
        self.elements_folder = elements_folder
        self.assets_folder = assets_folder
        
        self.card_mapping = self._create_card_mapping()
        
        for card_code, filename in self.card_mapping.items():
            try:
                self.loaded_elements[card_code] = Image.open(
                    os.path.join(assets_folder, filename)
                ).convert('RGBA')
            except Exception as e:
                logger.error(f"[BlackJack] Cannot load card {filename}: {e}")
        
        try:
            self.loaded_elements['card_back.png'] = Image.open(
                os.path.join(assets_folder, "card_back.png")
            ).convert('RGBA')
        except Exception as e:
            logger.error(f"[BlackJack] Cannot load card_back.png: {e}")
        
        buttons = ['hit', 'stand', 'double', 'split']
        
        for button in buttons:
            try:
                self.loaded_elements[f'button_{button}.png'] = Image.open(
                    os.path.join(elements_folder, f"button_{button}.png")
                ).convert('RGBA')
            except Exception as e:
                logger.error(f"[BlackJack] Cannot load button_{button}.png: {e}")
        
    def _create_card_mapping(self):
        mapping = {}
        
        suit_map = {
            'S': 'spades',
            'H': 'hearts', 
            'D': 'diamonds',
            'C': 'clubs'
        }
        
        value_map = {
            'A': 'A',
            '2': '02', '3': '03', '4': '04', '5': '05', '6': '06',
            '7': '07', '8': '08', '9': '09', '10': '10',
            'J': 'J', 'Q': 'Q', 'K': 'K'
        }
        
        for suit_symbol, suit_name in suit_map.items():
            for value_symbol, value_code in value_map.items():
                card_code = f"{value_symbol}{suit_symbol}"
                filename = f"card_{suit_name}_{value_code}.png"
                mapping[card_code] = filename
        
        return mapping
    
    def _calculate_table_width(self, player_cards, dealer_cards, is_split=False, split_hands=None):
        BASE_WIDTH = 500
        CARD_WIDTH = 112
        VISIBLE_WIDTH = 80
        CARD_OVERLAP = 40
        MIN_MARGIN = 15
        
        if is_split and split_hands:
            max_cards = 0
            for hand in split_hands:
                max_cards = max(max_cards, len(hand))
        else:
            max_player_cards = len(player_cards)
            max_dealer_cards = len(dealer_cards)
            max_cards = max(max_player_cards, max_dealer_cards)
        
        if max_cards == 0:
            return BASE_WIDTH
        
        if max_cards == 1:
            cards_width = CARD_WIDTH
        else:
            cards_width = VISIBLE_WIDTH + (max_cards - 1) * (VISIBLE_WIDTH - CARD_OVERLAP)
        
        required_width = cards_width + MIN_MARGIN * 2
        
        if is_split and split_hands:
            required_width += 200
        
        final_width = max(BASE_WIDTH, required_width)
        
        return final_width
    
    def _create_checkerboard_pattern(self, width, height, cell_size=10, color1=(25, 35, 45), color2=(15, 25, 35)):
        pattern = Image.new('RGB', (width, height), color1)
        draw = ImageDraw.Draw(pattern)
        
        for y in range(0, height, cell_size):
            for x in range(0, width, cell_size):
                if (x // cell_size + y // cell_size) % 2 == 0:
                    draw.rectangle([x, y, x + cell_size, y + cell_size], fill=color2)
        
        return pattern
        
    def generate_table_image(self, game_state, output_path, user_background_path=None, font_scale=1.0):
        player_cards = game_state.get('player_cards', [])
        dealer_cards = game_state.get('dealer_cards', [])
        is_split = game_state.get('is_split', False)
        split_hands = game_state.get('split_hands', [])
        split_points = game_state.get('split_points', [])
        current_hand = game_state.get('current_hand', 0)
        
        TABLE_WIDTH = self._calculate_table_width(player_cards, dealer_cards, is_split, split_hands)
        TABLE_HEIGHT = 400
                
        COLORS = {
            'table_bg': (10, 10, 20),
            'panel_border': (70, 70, 90),
            'text_primary': (255, 255, 255, 255),
            'text_semitransparent': (180, 180, 180, 255),
            'text_danger': (255, 80, 80, 255),
            'text_success': (80, 200, 120, 255),
            'text_highlight': (255, 215, 0, 255),
            'player_area_dark1': (40, 50, 60),
            'player_area_dark2': (30, 40, 50),
            'dealer_area_dark1': (50, 45, 55),
            'dealer_area_dark2': (40, 35, 45),
            'status_bg': (0, 0, 0, 200),
            'result_bg': (0, 0, 0, 180)
        }
        
        status_font_size = int(28 * font_scale)
        points_font_size = int(24 * font_scale)
        label_font_size = int(20 * font_scale)
        result_font_size = int(32 * font_scale)
        
        if user_background_path and os.path.exists(user_background_path):
            try:
                user_bg = Image.open(user_background_path).convert('RGBA')
                user_bg_resized = user_bg.resize((TABLE_WIDTH, TABLE_HEIGHT))
                table_img = Image.new('RGBA', (TABLE_WIDTH, TABLE_HEIGHT), (0, 0, 0, 0))
                table_img.paste(user_bg_resized, (0, 0))
            except Exception as e:
                logger.warning(f"[BlackJack] Failed to load user background: {e}, using default")
                table_img = Image.new('RGBA', (TABLE_WIDTH, TABLE_HEIGHT), (*COLORS['table_bg'], 255))
        else:
            table_img = Image.new('RGBA', (TABLE_WIDTH, TABLE_HEIGHT), (*COLORS['table_bg'], 255))
        
        draw = ImageDraw.Draw(table_img)
        
        dealer_y = 50
        dealer_area_width = TABLE_WIDTH - 30
        dealer_area_height = 100
                
        dealer_pattern = self._create_checkerboard_pattern(
            dealer_area_width, dealer_area_height, 
            cell_size=8,
            color1=COLORS['dealer_area_dark1'],
            color2=COLORS['dealer_area_dark2']
        )
        
        dealer_area = Image.new('RGBA', (dealer_area_width, dealer_area_height), (0, 0, 0, 0))
        dealer_area.paste(dealer_pattern, (0, 0))
        
        table_img.paste(dealer_area, (15, dealer_y), dealer_area)
        
        draw.rectangle([15, dealer_y, TABLE_WIDTH - 15, dealer_y + 100], 
                    outline=COLORS['panel_border'], width=2)
        
        player_y = TABLE_HEIGHT - 150
        player_area_width = TABLE_WIDTH - 30
        player_area_height = 100
                
        player_pattern = self._create_checkerboard_pattern(
            player_area_width, player_area_height,
            cell_size=8,
            color1=COLORS['player_area_dark1'],
            color2=COLORS['player_area_dark2']
        )
        
        player_area = Image.new('RGBA', (player_area_width, player_area_height), (0, 0, 0, 0))
        player_area.paste(player_pattern, (0, 0))
        
        table_img.paste(player_area, (15, player_y), player_area)
        
        draw.rectangle([15, player_y, TABLE_WIDTH - 15, player_y + 100], 
                    outline=COLORS['panel_border'], width=2)
        
        game_status = game_state.get('game_status', 'player_turn')
        status_colors = {
            'player_turn': COLORS['text_primary'],
            'dealer_turn': COLORS['text_primary'],
            'player_blackjack': COLORS['text_success'],
            'dealer_blackjack': COLORS['text_danger'],
            'player_bust': COLORS['text_danger'],
            'dealer_bust': COLORS['text_success'],
            'player_win': COLORS['text_success'],
            'dealer_win': COLORS['text_danger'],
            'push': COLORS['text_highlight']
        }
        
        status_text = game_state.get('message', 'Your turn')
        status_color = status_colors.get(game_status, COLORS['text_primary'])
        
        if self.text_renderer:
            status_img = self.text_renderer.render_text(
                text=status_text,
                font_size=status_font_size,
                color=status_color,
                stroke_width=int(2 * font_scale),
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_offset=(int(2 * font_scale), int(2 * font_scale))
            )
            
            status_width = status_img.width
            status_height = status_img.height
            
            status_bg_width = status_width + int(30 * font_scale)
            status_bg_height = status_height + int(15 * font_scale)
            status_bg_x = TABLE_WIDTH // 2 - status_bg_width // 2
            status_bg_y = 25 - status_bg_height // 2
                        
            status_bg = Image.new('RGBA', (status_bg_width, status_bg_height), COLORS['status_bg'])
            table_img.alpha_composite(status_bg, (int(status_bg_x), int(status_bg_y)))
            
            status_x = TABLE_WIDTH // 2 - status_width // 2
            status_y = 25 - status_height // 2
            table_img.alpha_composite(status_img, (status_x, status_y))
        
        dealer_label_x = 20
        dealer_label_y = dealer_y + 15
        
        dealer_label_text = "DEALER"
        dealer_points = game_state.get('dealer_points', 0)
        dealer_points_text = f"{dealer_points}"
        
        if self.text_renderer:
            dealer_label_img = self.text_renderer.render_text(
                text=dealer_label_text,
                font_size=label_font_size,
                color=COLORS['text_semitransparent']
            )
            table_img.alpha_composite(dealer_label_img, (dealer_label_x, dealer_label_y))
            
            dealer_points_img = self.text_renderer.render_text(
                text=dealer_points_text,
                font_size=points_font_size,
                color=COLORS['text_primary'],
                stroke_width=int(2 * font_scale),
                stroke_color=(0, 0, 0, 255)
            )
            
            dealer_points_x = TABLE_WIDTH - 20 - dealer_points_img.width
            table_img.alpha_composite(dealer_points_img, (dealer_points_x, dealer_label_y))
        
        player_label_x = 20
        player_label_y = player_y + 15
        
        player_label_text = "PLAYER"
        
        if self.text_renderer:
            player_label_img = self.text_renderer.render_text(
                text=player_label_text,
                font_size=label_font_size,
                color=COLORS['text_semitransparent']
            )
            table_img.alpha_composite(player_label_img, (player_label_x, player_label_y))
        
        self._draw_cards(table_img, dealer_cards, TABLE_WIDTH // 2, dealer_y + 50)
        
        if is_split and split_hands:
            left_center_x = TABLE_WIDTH // 2 - 120
            left_hand = split_hands[0] if len(split_hands) > 0 else []
            self._draw_cards(table_img, left_hand, left_center_x, player_y + 50)
            
            if split_points and len(split_points) > 0:
                points_color = COLORS['text_danger'] if split_points[0] > 21 else COLORS['text_primary']
                points_text = f"{split_points[0]}"
                if self.text_renderer:
                    points_img = self.text_renderer.render_text(
                        text=points_text,
                        font_size=points_font_size,
                        color=points_color,
                        stroke_width=int(2 * font_scale),
                        stroke_color=(0, 0, 0, 255)
                    )
                    points_x = left_center_x - points_img.width // 2
                    points_y = player_y + 15
                    table_img.alpha_composite(points_img, (points_x, points_y))
                    
                    hand_num_img = self.text_renderer.render_text(
                        text="Hand 1",
                        font_size=14,
                        color=(255, 215, 0) if current_hand == 0 and game_status == "player_turn" else (180, 180, 180),
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )
                    num_x = left_center_x - hand_num_img.width // 2
                    num_y = player_y - 25
                    table_img.alpha_composite(hand_num_img, (num_x, num_y))
            
            right_center_x = TABLE_WIDTH // 2 + 120
            right_hand = split_hands[1] if len(split_hands) > 1 else []
            self._draw_cards(table_img, right_hand, right_center_x, player_y + 50)
            
            if split_points and len(split_points) > 1:
                points_color = COLORS['text_danger'] if split_points[1] > 21 else COLORS['text_primary']
                points_text = f"{split_points[1]}"
                if self.text_renderer:
                    points_img = self.text_renderer.render_text(
                        text=points_text,
                        font_size=points_font_size,
                        color=points_color,
                        stroke_width=int(2 * font_scale),
                        stroke_color=(0, 0, 0, 255)
                    )
                    points_x = right_center_x - points_img.width // 2
                    points_y = player_y + 15
                    table_img.alpha_composite(points_img, (points_x, points_y))
                    
                    hand_num_img = self.text_renderer.render_text(
                        text="Hand 2",
                        font_size=14,
                        color=(255, 215, 0) if current_hand == 1 and game_status == "player_turn" else (180, 180, 180),
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )
                    num_x = right_center_x - hand_num_img.width // 2
                    num_y = player_y - 25
                    table_img.alpha_composite(hand_num_img, (num_x, num_y))
                    
        else:
            self._draw_cards(table_img, player_cards, TABLE_WIDTH // 2, player_y + 50)
            
            player_points = game_state.get('player_points', 0)
            player_points_color = COLORS['text_danger'] if player_points > 21 else COLORS['text_primary']
            player_points_text = f"{player_points}"
            
            if self.text_renderer:
                player_points_img = self.text_renderer.render_text(
                    text=player_points_text,
                    font_size=points_font_size,
                    color=player_points_color,
                    stroke_width=int(2 * font_scale),
                    stroke_color=(0, 0, 0, 255)
                )
                
                player_points_x = TABLE_WIDTH - 20 - player_points_img.width
                table_img.alpha_composite(player_points_img, (player_points_x, player_label_y))
        
        if game_status == 'player_turn':
            buttons_center_y = dealer_y + 100 + (player_y - (dealer_y + 100)) // 2
            self._draw_buttons_horizontal(table_img, TABLE_WIDTH // 2, buttons_center_y, game_state)
        
        elif game_status not in ['player_turn', 'dealer_turn']:
            result_center_y = dealer_y + 100 + (player_y - (dealer_y + 100)) // 2
            
            bet = game_state.get('bet', 0)
            win_amount = game_state.get('win_amount', 0)
            
            if win_amount > 0:
                result_text = f"WIN: +{win_amount}$"
                result_color = COLORS['text_success']
            elif win_amount < 0:
                result_text = f"LOSE: {win_amount}$"
                result_color = COLORS['text_danger']
            else:
                result_text = "PUSH: 0$"
                result_color = COLORS['text_highlight']
            
            if self.text_renderer:
                result_img = self.text_renderer.render_text(
                    text=result_text,
                    font_size=result_font_size,
                    color=result_color,
                    stroke_width=int(3 * font_scale),
                    stroke_color=(0, 0, 0, 255),
                    shadow=True,
                    shadow_offset=(int(3 * font_scale), int(3 * font_scale))
                )
                
                result_width = result_img.width
                result_height = result_img.height
                
                result_bg_width = result_width + int(40 * font_scale)
                result_bg_height = result_height + int(20 * font_scale)
                result_bg_x = TABLE_WIDTH // 2 - result_bg_width // 2
                result_bg_y = result_center_y - result_bg_height // 2
                
                result_bg = Image.new('RGBA', (result_bg_width, result_bg_height), COLORS['result_bg'])
                table_img.alpha_composite(result_bg, (int(result_bg_x), int(result_bg_y)))
                
                result_x = TABLE_WIDTH // 2 - result_width // 2
                result_y = result_center_y - result_height // 2
                table_img.alpha_composite(result_img, (result_x, result_y))
                    
        table_img_rgb = table_img.convert('RGB')
        table_img_rgb.save(output_path, format='PNG')

    def _draw_cards(self, table_img, cards, center_x, center_y):
        CARD_WIDTH = 112
        CARD_HEIGHT = 112
        VISIBLE_WIDTH = 80
        CARD_OVERLAP = 40
        
        if not cards:
            return
                    
        if len(cards) == 1:
            total_width = CARD_WIDTH
        else:
            total_width = VISIBLE_WIDTH + (len(cards) - 1) * (VISIBLE_WIDTH - CARD_OVERLAP)
        
        start_x = center_x - total_width // 2
        
        for i, card in enumerate(cards):
            if i == 0:
                card_x = start_x
            else:
                card_x = start_x + i * (VISIBLE_WIDTH - CARD_OVERLAP)
                
            if card == '?':
                card_img = self.loaded_elements.get('card_back.png')
            else:
                card_img = self.loaded_elements.get(card)
            
            if card_img:
                card_img_resized = card_img.resize((CARD_WIDTH, CARD_HEIGHT))
                table_img.alpha_composite(card_img_resized, (int(card_x), int(center_y - CARD_HEIGHT // 2)))
    
    def _draw_buttons_horizontal(self, table_img, center_x, center_y, game_state):
        button_width = 80
        button_height = 30
        button_spacing = 10
        
        buttons = []
        buttons.append('hit')
        buttons.append('stand')
        
        player_cards = game_state.get('player_cards', [])
        is_split = game_state.get('is_split', False)
        split_hands = game_state.get('split_hands', [])
        current_hand = game_state.get('current_hand', 0)
        
        if not is_split:
            if len(player_cards) == 2:
                buttons.append('double')
            if len(player_cards) == 2 and player_cards[0][0] == player_cards[1][0]:
                buttons.append('split')
        else:
            if current_hand < len(split_hands):
                current_hand_cards = split_hands[current_hand]
                if len(current_hand_cards) == 2:
                    buttons.append('double')
                
        total_width = len(buttons) * button_width + (len(buttons) - 1) * button_spacing
        start_x = center_x - total_width // 2
        
        for i, button in enumerate(buttons):
            button_img = self.loaded_elements.get(f'button_{button}.png')
            if button_img:
                button_img_resized = button_img.resize((button_width, button_height))
                button_x = start_x + i * (button_width + button_spacing)
                button_y = center_y - button_height // 2
                table_img.alpha_composite(button_img_resized, (int(button_x), int(button_y)))


class BlackjackGame:
    def __init__(self, user_id, sender_name, bet, num_decks=4):
        self.deck = []
        self.player_cards = []
        self.dealer_cards = []
        self.player_points = 0
        self.dealer_points = 0
        self.game_status = "player_turn"
        self.bet = bet
        self.message = "Your turn"
        self.user_id = user_id
        self.sender_name = sender_name
        self.num_decks = num_decks
        
        self.split_hands = []
        self.is_split = False
        self.current_hand_index = 0
        self.hand_bets = []
        self.hand_status = []
        self.hand_points = []
        
        self.initialize_deck()
    
    def initialize_deck(self):
        suits = ['S', 'H', 'D', 'C']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        self.deck = []
        for _ in range(self.num_decks):
            single_deck = [f"{value}{suit}" for suit in suits for value in values]
            self.deck.extend(single_deck)
        
        random.shuffle(self.deck)
    
    def deal_initial_cards(self):
        self.player_cards = [self.deck.pop(), self.deck.pop()]
        self.dealer_cards = [self.deck.pop(), self.deck.pop()]
        
        self.calculate_points()
        
        self.hand_bets = [self.bet]
        self.hand_status = ["active"]
        self.hand_points = [self.player_points]
                
        if self.player_points == 21:
            self.game_status = "player_blackjack"
            self.message = "Blackjack!"
            
            dealer_has_blackjack = self.dealer_points == 21
            
            if dealer_has_blackjack:
                self.game_status = "push"
                self.message = "Both have Blackjack! Push!"
    
    def calculate_points(self):
        self.player_points = self._calculate_hand_points(self.player_cards)
        self.dealer_points = self._calculate_hand_points(self.dealer_cards)
    
    def _calculate_hand_points(self, cards):
        points = 0
        aces = 0
        
        for card in cards:
            if card == '?':
                continue
                
            value = card[:-1]
            
            if value in ['J', 'Q', 'K']:
                points += 10
            elif value == 'A':
                aces += 1
                points += 11
            else:
                points += int(value)
        
        while points > 21 and aces > 0:
            points -= 10
            aces -= 1
        
        return points
    
    def hit(self):
        if self.game_status != "player_turn":
            return False
        
        current_status = self._get_current_hand_status()
        if current_status != "active":
            return False
        
        new_card = self.deck.pop()
        current_cards = self._get_current_hand_cards()
        current_cards.append(new_card)
        
        new_points = self._calculate_hand_points(current_cards)
        self._set_current_hand_points(new_points)
        
        if new_points > 21:
            self._set_current_hand_status("bust")
            hand_num = self.current_hand_index + 1 if self.is_split else 1
            self.message = f"Bust! Hand {hand_num} busted!"
            self._next_hand()
        elif new_points == 21:
            self._set_current_hand_status("stand")
            hand_num = self.current_hand_index + 1 if self.is_split else 1
            self.message = f"Hand {hand_num} reached 21!"
            self._next_hand()
        else:
            hand_num = self.current_hand_index + 1 if self.is_split else 1
            self.message = f"Hand {hand_num}: {new_points} points"
        
        return True
    
    def stand(self):
        if self.game_status != "player_turn":
            return False
        
        current_status = self._get_current_hand_status()
        if current_status != "active":
            return False
        
        self._set_current_hand_status("stand")
        current_points = self._get_current_hand_points()
        hand_num = self.current_hand_index + 1 if self.is_split else 1
        self.message = f"Hand {hand_num} stands with {current_points} points"
        self._next_hand()
        
        return True
    
    def double(self):
        if self.game_status != "player_turn":
            return False
        
        current_cards = self._get_current_hand_cards()
        if len(current_cards) != 2:
            return False
        
        current_status = self._get_current_hand_status()
        if current_status != "active":
            return False
        
        if not self.is_split:
            self.bet *= 2
            self.hand_bets[0] = self.bet
        else:
            self.hand_bets[self.current_hand_index] *= 2
        
        new_card = self.deck.pop()
        current_cards.append(new_card)
        new_points = self._calculate_hand_points(current_cards)
        self._set_current_hand_points(new_points)
        
        hand_num = self.current_hand_index + 1 if self.is_split else 1
        
        if new_points > 21:
            self._set_current_hand_status("bust")
            self.message = f"Hand {hand_num} busted after double!"
        else:
            self._set_current_hand_status("stand")
            self.message = f"Hand {hand_num} doubled and stands with {new_points} points!"
        
        self._next_hand()
        return True
    
    def split(self):
        if (self.game_status != "player_turn" or len(self.player_cards) != 2 or 
            self.player_cards[0][0] != self.player_cards[1][0] or self.is_split):
            return False
        
        card1 = self.player_cards[0]
        card2 = self.player_cards[1]
        
        hand1 = [card1]
        hand2 = [card2]
        
        hand1.append(self.deck.pop())
        hand2.append(self.deck.pop())
        
        self.split_hands = [hand1, hand2]
        self.is_split = True
        self.current_hand_index = 0
        
        self.hand_bets = [self.bet, self.bet]
        self.hand_status = ["active", "active"]
        
        self.hand_points = [
            self._calculate_hand_points(hand1),
            self._calculate_hand_points(hand2)
        ]
        
        self.player_cards = []
        self.player_points = 0
        
        for i, points in enumerate(self.hand_points):
            if points == 21:
                self.hand_status[i] = "stand"
        
        self.message = f"Split! Now playing hand 1 of 2"
        
        if all(status != "active" for status in self.hand_status):
            self._next_hand()
        
        return True
    
    def _get_current_hand_cards(self):
        if not self.is_split:
            return self.player_cards
        else:
            return self.split_hands[self.current_hand_index]
    
    def _get_current_hand_points(self):
        if not self.is_split:
            return self.player_points
        else:
            return self.hand_points[self.current_hand_index]
    
    def _set_current_hand_points(self, points):
        if not self.is_split:
            self.player_points = points
        else:
            self.hand_points[self.current_hand_index] = points
    
    def _get_current_hand_status(self):
        if not self.is_split:
            return self.game_status if self.game_status != "player_turn" else "active"
        else:
            return self.hand_status[self.current_hand_index]
    
    def _set_current_hand_status(self, status):
        if not self.is_split:
            self.game_status = status
        else:
            self.hand_status[self.current_hand_index] = status
    
    def _next_hand(self):
        if not self.is_split:
            self._dealer_turn()
            return
        
        self.current_hand_index += 1
        
        if self.current_hand_index >= len(self.split_hands):
            self._dealer_turn()
        else:
            if self.hand_status[self.current_hand_index] == "active":
                self.message = f"Playing split hand {self.current_hand_index + 1} of {len(self.split_hands)}"
            else:
                self._next_hand()
    
    def _dealer_turn(self):
        self.game_status = "dealer_turn"
        self.message = "Dealer's turn"
        
        self.calculate_points()
        
        while self.dealer_points < 17:
            new_card = self.deck.pop()
            self.dealer_cards.append(new_card)
            self.calculate_points()
        
        self.game_status = "finished"
        
        if not self.is_split:
            if self.player_points > 21:
                self.message = "Bust! You lose!"
            elif self.dealer_points > 21:
                self.message = "Dealer busts! You win!"
            elif self.player_points > self.dealer_points:
                self.message = "You win!"
            elif self.player_points < self.dealer_points:
                self.message = "Dealer wins!"
            else:
                self.message = "Push! It's a tie."
        else:
            win_count = 0
            lose_count = 0
            push_count = 0
            bust_count = 0
            
            for i, points in enumerate(self.hand_points):
                if points > 21:
                    bust_count += 1
                elif self.dealer_points > 21 or points > self.dealer_points:
                    win_count += 1
                elif points < self.dealer_points:
                    lose_count += 1
                else:
                    push_count += 1
            
            self.message = f"{win_count} win, {lose_count} lose, {push_count} push, {bust_count} bust"
    
    def calculate_win_amount(self):
        if self.game_status != "finished":
            return 0
        
        if not self.is_split:
            if self.player_points > 21:
                return 0
            elif self.dealer_points > 21 or self.player_points > self.dealer_points:
                if self.player_points == 21 and len(self.player_cards) == 2:
                    return int(self.bet * 2.5)
                else:
                    return self.bet * 2
            elif self.player_points == self.dealer_points:
                return self.bet
            else:
                return 0
        else:
            total_win = 0
            for i, points in enumerate(self.hand_points):
                bet = self.hand_bets[i]
                if points > 21:
                    continue
                elif self.dealer_points > 21 or points > self.dealer_points:
                    if points == 21 and len(self.split_hands[i]) == 2:
                        total_win += int(bet * 2.5)
                    else:
                        total_win += bet * 2
                elif points == self.dealer_points:
                    total_win += bet
            return total_win
    
    def get_game_state(self):
        display_dealer_cards = self.dealer_cards.copy()
        if self.game_status == "player_turn" and len(display_dealer_cards) > 1:
            display_dealer_cards[1] = '?'
        
        if self.is_split:
            all_cards = []
            for hand in self.split_hands:
                all_cards.extend(hand)
            
            current_points = self.hand_points[self.current_hand_index] if self.current_hand_index < len(self.hand_points) else 0
            
            game_state = {
                'player_cards': all_cards,
                'dealer_cards': display_dealer_cards,
                'player_points': current_points,
                'dealer_points': self.dealer_points if self.game_status != "player_turn" else self._calculate_hand_points([display_dealer_cards[0]]),
                'game_status': self.game_status,
                'message': self.message,
                'bet': self.bet,
                'is_split': True,
                'split_hands': self.split_hands,
                'split_points': self.hand_points,
                'split_status': self.hand_status,
                'current_hand': self.current_hand_index,
                'win_amount': self.calculate_win_amount() if self.game_status == "finished" else 0
            }
        else:
            game_state = {
                'player_cards': self.player_cards,
                'dealer_cards': display_dealer_cards,
                'player_points': self.player_points,
                'dealer_points': self.dealer_points if self.game_status != "player_turn" else self._calculate_hand_points([display_dealer_cards[0]]),
                'game_status': self.game_status,
                'message': self.message,
                'bet': self.bet,
                'is_split': False,
                'win_amount': self.calculate_win_amount() if self.game_status == "finished" else 0
            }
        
        return game_state


class BlackjackPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="blackjack")
        self.active_games = {}
        self.elements_folder = self.get_asset_path("blackjack", "board_elements")
        self.table_generator = BlackjackTableGenerator(self.text_renderer)
        
        try:
            self.table_generator.load_elements(self.elements_folder, self.elements_folder)
        except Exception as e:
            logger.error(f"[BlackJack] Failed to load blackjack elements: {e}")

    def load_game_state(self, user_id):
        user_id = str(user_id)
        
        if user_id in self.active_games:
            return self.active_games[user_id]
        
        if hasattr(self, 'cache') and self.cache:
            game_data = self.cache.get_game_state(user_id, self.game_name)
            if game_data:
                game = self._deserialize_game(user_id, game_data)
                if game:
                    self.active_games[user_id] = game
                    return game
        
        return None
    
    def save_game_state(self, user_id, game):
        user_id = str(user_id)
        if hasattr(self, 'cache') and self.cache:
            game_data = self._serialize_game(game)
            if game_data:
                self.cache.save_game_state(user_id, self.game_name, game_data)
    
    def _serialize_game(self, game):
        try:
            return {
                'player_cards': game.player_cards,
                'dealer_cards': game.dealer_cards,
                'player_points': game.player_points,
                'dealer_points': game.dealer_points,
                'game_status': game.game_status,
                'bet': game.bet,
                'message': game.message,
                'is_split': game.is_split,
                'split_hands': game.split_hands,
                'hand_bets': game.hand_bets,
                'hand_status': game.hand_status,
                'hand_points': game.hand_points,
                'current_hand_index': game.current_hand_index,
                'deck': game.deck
            }
        except Exception as e:
            logger.error(f"[BlackJack] Error serializing game: {e}")
            return None
    
    def _deserialize_game(self, user_id, data):
        try:
            game = BlackjackGame(user_id, data.get('sender_name', 'Player'), data.get('bet', 0))
            
            game.player_cards = data.get('player_cards', [])
            game.dealer_cards = data.get('dealer_cards', [])
            game.player_points = data.get('player_points', 0)
            game.dealer_points = data.get('dealer_points', 0)
            game.game_status = data.get('game_status', 'player_turn')
            game.bet = data.get('bet', 0)
            game.message = data.get('message', 'Your turn')
            game.is_split = data.get('is_split', False)
            game.split_hands = data.get('split_hands', [])
            game.hand_bets = data.get('hand_bets', [])
            game.hand_status = data.get('hand_status', [])
            game.hand_points = data.get('hand_points', [])
            game.current_hand_index = data.get('current_hand_index', 0)
            game.deck = data.get('deck', [])
            
            return game
        except Exception as e:
            logger.error(f"[BlackJack] Error deserializing game: {e}")
            return None

    def get_user_background_path(self, user_id, user):
        if not user:
            return None
        
        if hasattr(self, 'cache') and self.cache:
            background_path = self.cache.get_background_path(user_id)
            if os.path.exists(background_path):
                return background_path
        
        return None
    
    def _send_game_image(self, user_id, user, sender, game, file_queue, win_amount=0, final_balance=None):
        img_path = os.path.join(self.results_folder, f"blackjack_{user_id}_{int(time.time())}.png")
        user_background_path = self.get_user_background_path(user_id, user)
        
        self.table_generator.generate_table_image(game.get_game_state(), img_path, user_background_path, font_scale=0.9)
        
        if final_balance is None:
            final_balance = user["balance"] if user else 0
        
        overlay_path, error = self.apply_user_overlay(
            img_path, user_id, sender, game.bet, win_amount, final_balance, user,
            show_win_text=False, font_scale=0.9, avatar_size=60
        )
        
        if overlay_path:
            file_queue.put(overlay_path)
            return True
        return False

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        import time
        
        self.cache = cache
        
        if len(args) == 0:
            user_id, user, error = self.validate_user(cache, sender, avatar_url)
            if error:
                self.send_message_image(sender, file_queue, 
                    "No active game. Use /bj start <bet> to start a new game!", 
                    "Blackjack", cache, user_id)
                return ""
            
            game = self.load_game_state(user_id)
            if not game:
                game = self.active_games.get(user_id)
            
            if game:
                self._send_game_image(user_id, user, sender, game, file_queue, 0, user["balance"])
                return f"Your current blackjack game:\nBet: {game.bet}"
            else:
                self.send_message_image(sender, file_queue, 
                    "No active game. Use /bj start <bet> to start a new game!", 
                    "Blackjack", cache, user_id)
                return ""

        cmd = args[0].lower()

        if cmd == "start" or cmd == "bet" or cmd == "b":
            if len(args) < 2:
                self.send_message_image(sender, file_queue, "Usage: /bj start <bet>", "Blackjack Error", cache, None)
                return ""
            
            try:
                bet = int(args[1])
            except ValueError:
                self.send_message_image(sender, file_queue, "Bet must be a number", "Blackjack Error", cache, None)
                return ""
            
            if bet <= 0:
                self.send_message_image(sender, file_queue, "Bet must be positive", "Blackjack Error", cache, None)
                return ""
            
            user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, bet)
            if error:
                self.send_message_image(sender, file_queue, error, "Blackjack Error", cache, None)
                return ""
            
            existing_game = self.load_game_state(user_id)
            if existing_game or user_id in self.active_games:
                self.send_message_image(sender, file_queue, "You already have an active game! Use /bj to see status.", 
                                    "Blackjack Error", cache, user_id)
                return ""
            
            balance_before = user["balance"]
            
            if bet > balance_before:
                self.send_message_image(sender, file_queue, f"Insufficient funds! You have: {balance_before}", 
                                    "Blackjack Error", cache, user_id)
                return ""
            
            game = BlackjackGame(user_id, sender, bet, num_decks=4)
            game.sender_name = sender
            game.deal_initial_cards()
            self.active_games[user_id] = game
            
            new_balance = balance_before - bet
            self.update_user_balance(user_id, new_balance)
            
            logger.info(f"[BlackJack] New blackjack game started for {sender}, bet: {bet}, balance: {balance_before} -> {new_balance}")
            
            is_game_finished = game.game_status in ["player_blackjack", "push"]
            win_amount = 0
            final_balance = new_balance
            
            if is_game_finished:
                win_amount = game.calculate_win_amount()
                if win_amount > 0:
                    final_balance = new_balance + win_amount
                    self.update_user_balance(user_id, final_balance)
                
                newLevel, newLevelProgress = self.cache.add_experience(user_id, win_amount, sender, file_queue)
                user["level"] = newLevel
                user["level_progress"] = newLevelProgress
                
                self.active_games.pop(user_id, None)
            else:
                self.save_game_state(user_id, game)
            
            self._send_game_image(user_id, user, sender, game, file_queue, win_amount, final_balance)
            
            if is_game_finished:
                if game.game_status == "player_blackjack":
                    return f"**BLACKJACK!**\nYou won {win_amount} ({bet} × 2.5)!"
                else:
                    return f"**Push!** Both have Blackjack!\nYour bet of {bet} is returned."
            else:
                return f"Blackjack started! Bet: {bet}"

        elif cmd in ["split", "sp"]:
            user_id, user, error = self.validate_user(cache, sender, avatar_url)
            if error:
                self.send_message_image(sender, file_queue, error, "Blackjack Error", cache, user_id)
                return ""
            
            game = self.active_games.get(user_id)
            if not game:
                game = self.load_game_state(user_id)
                if game:
                    self.active_games[user_id] = game
            
            if not game:
                self.send_message_image(sender, file_queue, "No active game. Use /bj start <bet>", 
                                    "Blackjack Error", cache, user_id)
                return ""
            
            success = game.split()
            
            if not success:
                self.send_message_image(sender, file_queue, "Cannot split this hand!", "Blackjack Error", cache, user_id)
                return ""
            
            self.save_game_state(user_id, game)
            
            user = self.cache.get_user(user_id)
            self._send_game_image(user_id, user, sender, game, file_queue)
            
            return "Split successful! Now playing hand 1."

        elif cmd in ["hit", "h", "stand", "s", "double", "d"]:
            user_id, user, error = self.validate_user(cache, sender, avatar_url)
            if error:
                self.send_message_image(sender, file_queue, error, "Blackjack Error", cache, user_id)
                return ""
            
            game = self.active_games.get(user_id)
            if not game:
                game = self.load_game_state(user_id)
                if game:
                    self.active_games[user_id] = game
            
            if not game:
                self.send_message_image(sender, file_queue, "No active game. Use /bj start <bet>", 
                                    "Blackjack Error", cache, user_id)
                return ""
            
            action_completed = False
            action_msg = ""
                        
            if cmd == "hit" or cmd == "h":
                action_completed = game.hit()
                action_msg = "Hit"
                
            elif cmd == "stand" or cmd == "s":
                action_completed = game.stand()
                action_msg = "Stand"
            
            elif cmd == "double" or cmd == "d":
                user = self.cache.get_user(user_id)
                if not user:
                    self.active_games.pop(user_id, None)
                    if hasattr(self, 'cache') and self.cache:
                        self.cache.save_game_state(user_id, self.game_name, None)
                    self.send_message_image(sender, file_queue, "User not found. Please start a new game.", 
                                        "Blackjack Error", cache, user_id)
                    return ""
                
                if not game.is_split:
                    additional_bet = game.bet
                else:
                    if game.current_hand_index < len(game.hand_bets):
                        additional_bet = game.hand_bets[game.current_hand_index]
                    else:
                        additional_bet = game.bet
                
                if user["balance"] < additional_bet:
                    self.send_message_image(sender, file_queue, f"Not enough funds to double! Need: {additional_bet}", 
                                        "Blackjack Error", cache, user_id)
                    return ""
                
                action_completed = game.double()
                if action_completed:
                    new_balance = user["balance"] - additional_bet
                    self.update_user_balance(user_id, new_balance)
                    user["balance"] = new_balance
                action_msg = "Double"
            
            if not action_completed:
                self.send_message_image(sender, file_queue, "Cannot perform this action now!", "Blackjack Error", cache, user_id)
                return ""
            
            self.save_game_state(user_id, game)
            
            is_game_finished = game.game_status == "finished"
            win_amount = 0
            final_balance = user["balance"] if user else 0
            
            if is_game_finished:
                win_amount = game.calculate_win_amount()
                user = self.cache.get_user(user_id)
                if user:
                    final_balance = user["balance"] + win_amount
                    self.update_user_balance(user_id, final_balance)
                    
                    new_level, new_progress = self.cache.add_experience(user_id, win_amount, sender, file_queue)
                    user["level"] = new_level
                    user["level_progress"] = new_progress
                
                self.active_games.pop(user_id, None)
                if hasattr(self, 'cache') and self.cache:
                    self.cache.save_game_state(user_id, self.game_name, None)
            
            user = self.cache.get_user(user_id)
            self._send_game_image(user_id, user, sender, game, file_queue, win_amount, final_balance)
            
            if is_game_finished:
                return f"{action_msg}! {game.message}\nTotal win: {win_amount}$"
            else:
                return f"{action_msg}! {game.message}"

        else:
            self.send_message_image(sender, file_queue, "Unknown command. Use: /bj start <bet>, /bj hit, /bj stand, /bj double, /bj split", 
                                "Blackjack Error", cache, user_id)
            return ""

def register():
    logger.info("[BlackJack] Registering Blackjack plugin")
    plugin = BlackjackPlugin()
    return {
        "name": "blackjack",
        "aliases": ["/bj"],
        "description": "Blackjack Card Game\n\n**Commands:**\n- /bj start <bet> - Start new game\n- /bj hit - Take another card\n- /bj stand - Keep current hand\n- /bj double - Double your bet (on first turn)\n- /bj split - Split your hand (matching cards)\n\n**Payouts:**\n- Blackjack (21): 2.5× bet\n- Normal win: 2× bet\n- Push: Bet returned",
        "execute": plugin.execute_game
    }