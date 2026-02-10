import os
import random
from PIL import Image, ImageDraw
from base_game_plugin import BaseGamePlugin
from logger import logger

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
    
    def _calculate_table_width(self, player_cards, dealer_cards):
        BASE_WIDTH = 500
        CARD_WIDTH = 112
        VISIBLE_WIDTH = 80
        CARD_OVERLAP = 40
        MIN_MARGIN = 15
        
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
        
        TABLE_WIDTH = self._calculate_table_width(player_cards, dealer_cards)
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
            logger.warning("[BlackJack] Using default table background")
        
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
        player_points = game_state.get('player_points', 0)
        player_points_text = f"{player_points}"
        player_points_color = COLORS['text_danger'] if player_points > 21 else COLORS['text_primary']
        
        if self.text_renderer:
            player_label_img = self.text_renderer.render_text(
                text=player_label_text,
                font_size=label_font_size,
                color=COLORS['text_semitransparent']
            )
            table_img.alpha_composite(player_label_img, (player_label_x, player_label_y))
            
            player_points_img = self.text_renderer.render_text(
                text=player_points_text,
                font_size=points_font_size,
                color=player_points_color,
                stroke_width=int(2 * font_scale),
                stroke_color=(0, 0, 0, 255)
            )
            
            player_points_x = TABLE_WIDTH - 20 - player_points_img.width
            table_img.alpha_composite(player_points_img, (player_points_x, player_label_y))
        
        self._draw_cards(table_img, dealer_cards, TABLE_WIDTH // 2, dealer_y + 50)
        self._draw_cards(table_img, player_cards, TABLE_WIDTH // 2, player_y + 50)
        
        if game_status == 'player_turn':
            buttons_center_y = dealer_y + 100 + (player_y - (dealer_y + 100)) // 2
            self._draw_buttons_horizontal(table_img, TABLE_WIDTH // 2, buttons_center_y, game_state)
        
        elif game_status not in ['player_turn', 'dealer_turn']:
            result_center_y = dealer_y + 100 + (player_y - (dealer_y + 100)) // 2
            
            bet = game_state.get('bet', 0)
            win_amount = 0
            
            if game_status in ["player_blackjack"]:
                win_amount = int(bet * 2.5) - BaseException
            elif game_status in ["player_win", "dealer_bust"]:
                win_amount = bet
            elif game_status in ["player_bust", "dealer_win"]:
                win_amount = -bet
            elif game_status == "push":
                win_amount = 0
            
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
            logger.warning("[BlackJack] No cards to draw")
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
            else:
                logger.warning(f"[BlackJack] Missing image for card: {card}")
    
    def _draw_buttons_horizontal(self, table_img, center_x, center_y, game_state):
        button_width = 80
        button_height = 30
        button_spacing = 10
        
        buttons = []
        buttons.append('hit')
        buttons.append('stand')
        
        player_cards = game_state.get('player_cards', [])
        if len(player_cards) == 2:
            buttons.append('double')
        
        if len(player_cards) == 2 and player_cards[0][0] == player_cards[1][0]:
            buttons.append('split')
                
        total_width = len(buttons) * button_width + (len(buttons) - 1) * button_spacing
        start_x = center_x - total_width // 2
        
        for i, button in enumerate(buttons):
            button_img = self.loaded_elements.get(f'button_{button}.png')
            if button_img:
                button_img_resized = button_img.resize((button_width, button_height))
                button_x = start_x + i * (button_width + button_spacing)
                button_y = center_y - button_height // 2
                table_img.alpha_composite(button_img_resized, (int(button_x), int(button_y)))
            else:
                logger.warning(f"[BlackJack] Missing image for button: {button}")

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
            
        new_card = self.deck.pop()
        self.player_cards.append(new_card)
        self.calculate_points()
                
        if self.player_points > 21:
            self.game_status = "player_bust"
            self.message = "Bust!"
            return True
        elif self.player_points == 21:
            return self.stand()
            
        return True
    
    def stand(self):
        if self.game_status != "player_turn":
            return False
            
        self.game_status = "dealer_turn"
        self.message = "Dealer's turn"
        
        self.calculate_points()
        
        dealer_hits = 0
        while self.dealer_points < 17:
            new_card = self.deck.pop()
            self.dealer_cards.append(new_card)
            self.calculate_points()
            dealer_hits += 1
                
        if self.dealer_points > 21:
            self.game_status = "dealer_bust"
            self.message = "Dealer busts! You win!"
        elif self.dealer_points > self.player_points:
            self.game_status = "dealer_win"
            self.message = "Dealer wins!"
        elif self.player_points > self.dealer_points:
            self.game_status = "player_win"
            self.message = "You win!"
        else:
            self.game_status = "push"
            self.message = "Push! It's a tie."
        
        return True
    
    def double(self):
        if self.game_status != "player_turn" or len(self.player_cards) != 2:
            return False
                    
        self.bet *= 2
        
        new_card = self.deck.pop()
        self.player_cards.append(new_card)
        self.calculate_points()
                
        if self.player_points > 21:
            self.game_status = "player_bust"
            self.message = "Bust after double!"
            return True
        
        return self.stand()
    
    def split(self):
        if (self.game_status != "player_turn" or len(self.player_cards) != 2 or 
            self.player_cards[0][0] != self.player_cards[1][0]):
            return False
            
        logger.warning("[BlackJack] Split requested but not implemented yet")
        return False
    
    def get_game_state(self):
        display_dealer_cards = self.dealer_cards.copy()
        if self.game_status == "player_turn" and len(display_dealer_cards) > 1:
            display_dealer_cards[1] = '?'
        
        game_state = {
            'player_cards': self.player_cards,
            'dealer_cards': display_dealer_cards,
            'player_points': self.player_points,
            'dealer_points': self.dealer_points if self.game_status != "player_turn" else self._calculate_hand_points([display_dealer_cards[0]]),
            'game_status': self.game_status,
            'message': self.message,
            'bet': self.bet
        }
        
        return game_state

class BlackjackPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="blackjack"
        )
        self.active_games = {}
        self.elements_folder = self.get_asset_path("blackjack", "board_elements")
        self.table_generator = BlackjackTableGenerator(self.text_renderer)
        
        try:
            self.table_generator.load_elements(self.elements_folder, self.elements_folder)
        except Exception as e:
            logger.error(f"[BlackJack] Failed to load blackjack elements: {e}")
        
    def get_user_background_path(self, user_id, user):
        if not user:
            logger.warning(f"[BlackJack] No user data for user_id: {user_id}")
            return None
        
        background_path = self.cache.get_background_path(user_id)

        if os.path.exists(background_path):
            return background_path
        else:
            logger.warning(f"[BlackJack] Background file not found: {background_path}")
        
        user_backgrounds_dir = self.get_asset_path("users", "backgrounds")
        if os.path.exists(user_backgrounds_dir):
            user_bg_path = os.path.join(user_backgrounds_dir, f"{user_id}.png")
            if os.path.exists(user_bg_path):
                return user_bg_path
            
            for ext in ['.jpg', '.jpeg', '.webp', '.gif']:
                user_bg_path = os.path.join(user_backgrounds_dir, f"{user_id}{ext}")
                if os.path.exists(user_bg_path):
                    return user_bg_path
        
        return None

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        
        self.cache = cache
        
        if len(args) == 0:
            user_id, user, error = self.validate_user(cache, sender, avatar_url)
            if error:
                return "Blackjack Commands: /bj start <bet>, /bj hit, /bj stand, /bj double"
            
            if user_id in self.active_games:
                game = self.active_games[user_id]
                
                img_path = os.path.join(self.results_folder, f"blackjack_{user_id}_status.png")
                
                user_background_path = self.get_user_background_path(user_id, user)
                
                self.table_generator.generate_table_image(game.get_game_state(), img_path, user_background_path, font_scale=0.9)
                
                user = self.cache.get_user(user_id)
                if user:
                    current_balance = user["balance"]
                else:
                    current_balance = 0
                
                overlay_path, error = self.apply_user_overlay(
                    img_path, user_id, sender, game.bet, 0, current_balance, user,
                    show_win_text=False, font_scale=0.9, avatar_size=60
                )
                
                if overlay_path:
                    file_queue.put(overlay_path)
                    return f"Your current blackjack game:\nBet: {game.bet}\nYour cards: {', '.join(game.player_cards)} ({game.player_points} points)\nDealer shows: {game.dealer_cards[0]}"
                else:
                    return f"Your current blackjack game:\nBet: {game.bet}\nYour cards: {', '.join(game.player_cards)} ({game.player_points} points)\nDealer shows: {game.dealer_cards[0]}"
            else:
                return "Blackjack Commands: /bj start <bet>, /bj hit, /bj stand, /bj double"

        cmd = args[0].lower()

        if cmd == "start" or cmd == "bet" or cmd == "b":
            if len(args) < 2:
                self.send_message_image(sender, file_queue, "Usage: /bj start <bet>", "Blackjack Error", cache, None)
                return ""
            
            try:
                bet = int(args[1])
            except ValueError as e:
                self.send_message_image(sender, file_queue, "Bet must be a number", "Blackjack Error", cache, None)
                return ""
            
            if bet <= 0:
                self.send_message_image(sender, file_queue, "Bet must be positive", "Blackjack Error", cache, None)
                return ""
            
            user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, bet)
            if error:
                self.send_message_image(sender, file_queue, error, "Blackjack Error", cache, None)
                return ""
            
            if user_id in self.active_games:
                self.send_message_image(sender, file_queue, "You already have an active game!", "Blackjack Error", cache, user_id)
                return ""
            
            balance_before = user["balance"]
            
            if bet > balance_before:
                self.send_message_image(sender, file_queue, f"Insufficient funds! \nYou have: {balance_before}", 
                                      "Blackjack Error", cache, user_id)
                return ""
            
            game = BlackjackGame(user_id, sender, bet, num_decks=4)
            game.deal_initial_cards()
            self.active_games[user_id] = game
            
            new_balance = balance_before - bet
            self.update_user_balance(user_id, new_balance)
            
            logger.info(f"[BlackJack] New blackjack game started for {sender}, bet: {bet}, balance: {balance_before} -> {new_balance}")
            
            is_game_finished = game.game_status in ["player_blackjack", "push"]
            win_amount = 0
            final_balance = new_balance
            
            if is_game_finished:
                win_amount = self._calculate_win_amount(game)
                logger.info(f"[BlackJack] Game finished immediately with status: {game.game_status}, win amount: {win_amount}")
                
                if win_amount > 0:
                    final_balance = new_balance + win_amount
                    self.update_user_balance(user_id, final_balance)
                
                newLevel, newLevelProgress = self.cache.add_experience(user_id, win_amount, sender, file_queue)
                user["level"] = newLevel
                user["level_progress"] = newLevelProgress
                
                self.active_games.pop(user_id, None)
                        
            img_path = os.path.join(self.results_folder, f"blackjack_{user_id}.png")
            
            user_background_path = self.get_user_background_path(user_id, user)
            
            self.table_generator.generate_table_image(game.get_game_state(), img_path, user_background_path, font_scale=0.9)
            
            overlay_path, error = self.apply_user_overlay(img_path, user_id, sender, bet, win_amount, final_balance, user,
                                                          show_win_text=False, font_scale=0.9, avatar_size=60)
            if overlay_path:
                file_queue.put(overlay_path)
            else:
                logger.warning(f"[BlackJack] Failed to create overlay for {sender}")
            
            if is_game_finished:
                if game.game_status == "player_blackjack":
                    return f"**BLACKJACK!**\nYou won {win_amount} ({bet} × 2.5)!\nYour cards: {', '.join(game.player_cards)}"
                else:
                    return f"**Push!** Both have Blackjack!\nYour bet of {bet} is returned.\nYour cards: {', '.join(game.player_cards)}"
            else:
                return f"Blackjack started! Bet: {bet}\nYour cards: {', '.join(game.player_cards)} ({game.player_points} points)"

        elif cmd in ["hit", "h", "stand", "s", "double", "d"]:
            
            user_id, user, error = self.validate_user(cache, sender, avatar_url)
            if error:
                logger.warning(f"[BlackJack] User validation failed for {sender}: {error}")
                self.send_message_image(sender, file_queue, error, "Blackjack Error", cache, user_id)
                return ""
                        
            if user_id not in self.active_games:
                self.send_message_image(sender, file_queue, "No active game. \nUse /bj start <bet>", 
                                      "Blackjack Error", cache, user_id)
                return ""
            
            game = self.active_games[user_id]
            action_completed = False
            action_msg = ""
                        
            if cmd == "hit" or cmd == "h":
                action_completed = game.hit()
                action_msg = "Hit"
                
                if game.game_status != "player_turn":
                    win_amount = self._calculate_win_amount(game)
                    
                    self.active_games.pop(user_id, None)
            
            elif cmd == "stand" or cmd == "s":
                action_completed = game.stand()
                action_msg = "Stand"
            
            elif cmd == "double" or cmd == "d":
                user = self.cache.get_user(user_id)
                if not user:
                    logger.error(f"[BlackJack] User {sender} (id: {user_id}) not found in cache")
                    self.active_games.pop(user_id, None)
                    self.send_message_image(sender, file_queue, "User not found. Please start a new game.", 
                                          "Blackjack Error", cache, user_id)
                    return ""
                
                current_balance = user["balance"]
                if current_balance < game.bet:
                    self.send_message_image(sender, file_queue, f"Not enough funds to double! \n Need additional: {game.bet}", 
                                          "Blackjack Error", cache, user_id)
                    return ""
                
                action_completed = game.double()
                if action_completed:
                    new_balance = current_balance - game.bet
                    self.update_user_balance(user_id, new_balance)
                action_msg = "Double"
            
            img_path = os.path.join(self.results_folder, f"blackjack_{user_id}_{cmd}.png")
            
            win_amount = 0
            if game.game_status not in ["player_turn", "dealer_turn"]:
                win_amount = self._calculate_win_amount(game)
                
                user = self.cache.get_user(user_id)
                if not user:
                    logger.error(f"[BlackJack] User {sender} (id: {user_id}) not found in cache")
                    self.active_games.pop(user_id, None)
                    self.send_message_image(sender, file_queue, "User not found. Please start a new game.", 
                                          "Blackjack Error", cache, user_id)
                    return ""
                
                current_balance = user["balance"]
                final_balance = current_balance
                
                if win_amount > 0:
                    final_balance = current_balance + win_amount
                    self.update_user_balance(user_id, final_balance)
                    logger.info(f"[BlackJack] {sender} won {win_amount} from blackjack, new balance: {final_balance}")
                
                newLevel, newLevelProgress = self.cache.add_experience(user_id, win_amount, sender, file_queue)
                user["level"] = newLevel
                user["level_progress"] = newLevelProgress
                
                self.active_games.pop(user_id, None)
            else:
                user = self.cache.get_user(user_id)
                if user:
                    final_balance = user["balance"]
                else:
                    final_balance = 0

            user = self.cache.get_user(user_id)
            user_background_path = self.get_user_background_path(user_id, user)
            
            self.table_generator.generate_table_image(game.get_game_state(), img_path, user_background_path, font_scale=0.9)
            
            overlay_path, error = self.apply_user_overlay(img_path, user_id, sender, game.bet, win_amount if 'win_amount' in locals() else 0, final_balance, user,
                                                                      show_win_text=False, font_scale=0.9, avatar_size=60)
            if overlay_path:
                file_queue.put(overlay_path)
            
            return f"{action_msg}! {game.message}\nYour cards: {', '.join(game.player_cards)} ({game.player_points} points)"

        else:
            self.send_message_image(sender, file_queue, "Unknown command. Use: \n/bj start <bet> \n/bj hit \n/bj stand \n/bj double", 
                                  "Blackjack Error", cache, user_id)
            return ""

    def _calculate_win_amount(self, game):
        
        if game.game_status in ["player_bust", "dealer_win"]:
            net_result = -game.bet
            return net_result
        elif game.game_status == "player_blackjack":
            net_result = int(game.bet * 2.5)
            return net_result
        elif game.game_status in ["player_win", "dealer_bust"]:
            net_result = 2 * game.bet
            return net_result
        elif game.game_status == "push":
            net_result = game.bet
            return net_result
        
        return 0
    
def register():
    logger.info("[BlackJack] Registering Blackjack plugin")
    plugin = BlackjackPlugin()
    return {
        "name": "blackjack",
        "aliases": ["/bj"],
        "description": "Blackjack Card Game\n\n**Commands:**\n- /bj start <bet> - Start new game\n- /bj hit - Take another card\n- /bj stand - Keep current hand\n- /bj double - Double your bet (on first turn)\n- /bj split - Split your hand (matching cards)\n\n**Payouts:**\n- Blackjack (21): 2.5× bet\n- Normal win: 2× bet\n- Push: Bet returned",
        "execute": plugin.execute_game
    }