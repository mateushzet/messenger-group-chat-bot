import os
import random
from PIL import Image, ImageDraw, ImageFont
from base_game_plugin import BaseGamePlugin
from logger import logger

class BlackjackTableGenerator:
    def __init__(self):
        self.loaded_elements = {}
        
    def load_elements(self, elements_folder, assets_folder):
        self.elements_folder = elements_folder
        self.assets_folder = assets_folder
        
        self.card_mapping = self._create_card_mapping()
        
        logger.info("Loading cards...")
        for card_code, filename in self.card_mapping.items():
            try:
                self.loaded_elements[card_code] = Image.open(
                    os.path.join(assets_folder, filename)
                ).convert('RGBA')
            except Exception as e:
                logger.warning(f"Cannot load: {filename} - {e}")
        
        try:
            self.loaded_elements['card_back.png'] = Image.open(
                os.path.join(assets_folder, "card_back.png")
            ).convert('RGBA')
            logger.info("Loaded card_back.png")
        except:
            logger.warning("Cannot load card_back.png")
        
        buttons = ['hit', 'stand', 'double', 'split']
        for button in buttons:
            try:
                self.loaded_elements[f'button_{button}.png'] = Image.open(
                    os.path.join(elements_folder, f"button_{button}.png")
                ).convert('RGBA')
                logger.info(f"Loaded button_{button}.png")
            except:
                logger.warning(f"Cannot load button_{button}.png")
        
        logger.info("All elements loaded")
    
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
        
        return max(BASE_WIDTH, required_width)
    
    def _create_checkerboard_pattern(self, width, height, cell_size=10, color1=(25, 35, 45), color2=(15, 25, 35)):
        pattern = Image.new('RGBA', (width, height), color1)
        draw = ImageDraw.Draw(pattern)
        
        for y in range(0, height, cell_size):
            for x in range(0, width, cell_size):
                if (x // cell_size + y // cell_size) % 2 == 0:
                    draw.rectangle([x, y, x + cell_size, y + cell_size], fill=color2)
        
        return pattern
    
    def generate_table_image(self, game_state, output_path):
        player_cards = game_state.get('player_cards', [])
        dealer_cards = game_state.get('dealer_cards', [])
        
        TABLE_WIDTH = self._calculate_table_width(player_cards, dealer_cards)
        TABLE_HEIGHT = 400
        
        COLORS = {
            'table_bg': (0, 0, 0, 0),
            'panel_border': (70, 70, 90),
            'text_primary': (255, 255, 255),
            'text_semitransparent': (255, 255, 255, 180),
            'text_danger': (255, 80, 80),
            'text_success': (80, 200, 120),
            'text_highlight': (255, 215, 0),
            'player_area_dark1': (15, 25, 35),
            'player_area_dark2': (10, 20, 30),
            'dealer_area_dark1': (25, 20, 30),
            'dealer_area_dark2': (20, 15, 25),
            'status_bg': (0, 0, 0, 160)
        }
        
        table_img = Image.new('RGBA', (TABLE_WIDTH, TABLE_HEIGHT), COLORS['table_bg'])
        draw = ImageDraw.Draw(table_img)
        
        try:
            status_font = ImageFont.truetype("arial.ttf", 22)
            points_font = ImageFont.truetype("arialbd.ttf", 18)
            label_font = ImageFont.truetype("arial.ttf", 14)
        except:
            status_font = ImageFont.load_default()
            points_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
        
        dealer_y = 50
        dealer_area_width = TABLE_WIDTH - 30
        dealer_area_height = 100
        
        dealer_pattern = self._create_checkerboard_pattern(
            dealer_area_width, dealer_area_height, 
            cell_size=8,
            color1=COLORS['dealer_area_dark1'],
            color2=COLORS['dealer_area_dark2']
        )
        
        dealer_area_mask = Image.new('L', (dealer_area_width, dealer_area_height), 180)
        table_img.paste(dealer_pattern, (15, dealer_y), dealer_area_mask)
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
        
        player_area_mask = Image.new('L', (player_area_width, player_area_height), 180)
        table_img.paste(player_pattern, (15, player_y), player_area_mask)
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
        
        status_bbox = draw.textbbox((0, 0), status_text, font=status_font)
        status_width = status_bbox[2] - status_bbox[0]
        status_height = status_bbox[3] - status_bbox[1]
        
        status_bg_width = status_width + 30
        status_bg_height = status_height + 15
        status_bg_x = TABLE_WIDTH // 2 - status_bg_width // 2
        status_bg_y = 25 - status_bg_height // 2
        
        status_bg = Image.new('RGBA', (status_bg_width, status_bg_height), COLORS['status_bg'])
        table_img.paste(status_bg, (int(status_bg_x), int(status_bg_y)), status_bg)
        
        draw.text((TABLE_WIDTH // 2, 25), status_text, 
                 fill=status_color, font=status_font, anchor="mm")
        
        dealer_label_x = 20
        dealer_label_y = dealer_y + 15
        draw.text((dealer_label_x, dealer_label_y), "DEALER", 
                 fill=COLORS['text_semitransparent'], font=label_font)
        
        dealer_points = game_state.get('dealer_points', 0)
        dealer_points_text = f"{dealer_points}"
        dealer_points_bbox = draw.textbbox((0, 0), dealer_points_text, font=points_font)
        dealer_points_width = dealer_points_bbox[2] - dealer_points_bbox[0]
        dealer_points_x = TABLE_WIDTH - 20 - dealer_points_width
        
        outline_offset = 1
        for dx in [-outline_offset, 0, outline_offset]:
            for dy in [-outline_offset, 0, outline_offset]:
                if dx != 0 or dy != 0:
                    draw.text((dealer_points_x + dx, dealer_label_y + dy), dealer_points_text, 
                             fill=(0, 0, 0, 120), font=points_font)
        
        draw.text((dealer_points_x, dealer_label_y), dealer_points_text, 
                 fill=COLORS['text_primary'], font=points_font)
        
        player_label_x = 20
        player_label_y = player_y + 15
        draw.text((player_label_x, player_label_y), "PLAYER", 
                 fill=COLORS['text_semitransparent'], font=label_font)
        
        player_points = game_state.get('player_points', 0)
        player_points_text = f"{player_points}"
        player_points_color = COLORS['text_danger'] if player_points > 21 else COLORS['text_primary']
        
        player_points_bbox = draw.textbbox((0, 0), player_points_text, font=points_font)
        player_points_width = player_points_bbox[2] - player_points_bbox[0]
        player_points_x = TABLE_WIDTH - 20 - player_points_width
        
        for dx in [-outline_offset, 0, outline_offset]:
            for dy in [-outline_offset, 0, outline_offset]:
                if dx != 0 or dy != 0:
                    draw.text((player_points_x + dx, player_label_y + dy), player_points_text, 
                             fill=(0, 0, 0, 120), font=points_font)
        
        draw.text((player_points_x, player_label_y), player_points_text, 
                 fill=player_points_color, font=points_font)
        
        self._draw_cards(table_img, dealer_cards, TABLE_WIDTH // 2, dealer_y + 50)
        self._draw_cards(table_img, player_cards, TABLE_WIDTH // 2, player_y + 50)
        
        if game_status == 'player_turn':
            buttons_center_y = dealer_y + 100 + (player_y - (dealer_y + 100)) // 2
            self._draw_buttons_horizontal(table_img, TABLE_WIDTH // 2, buttons_center_y, game_state)
        
        table_img.save(output_path, format='PNG')
        logger.info(f"Saved table image: {output_path}")
    
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
                table_img.paste(card_img_resized, (int(card_x), int(center_y - CARD_HEIGHT // 2)), card_img_resized)
    
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
                table_img.paste(button_img_resized, (int(button_x), int(button_y)), button_img_resized)

class BlackjackGame:
    def __init__(self):
        self.deck = []
        self.player_cards = []
        self.dealer_cards = []
        self.player_points = 0
        self.dealer_points = 0
        self.game_status = "player_turn"
        self.bet = 0
        self.message = "Your turn"
        self.initialize_deck()
    
    def initialize_deck(self):
        suits = ['S', 'H', 'D', 'C']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        self.deck = [f"{value}{suit}" for suit in suits for value in values]
        random.shuffle(self.deck)
        logger.info("Deck initialized and shuffled")
    
    def deal_initial_cards(self):
        self.player_cards = [self.deck.pop(), self.deck.pop()]
        self.dealer_cards = [self.deck.pop(), self.deck.pop()]
        
        self.calculate_points()
        
        if self.player_points == 21:
            self.game_status = "player_blackjack"
            self.message = "Blackjack!"
            logger.info("Player got Blackjack!")
        
        logger.info(f"Cards dealt - Player: {self.player_cards} ({self.player_points}), Dealer: [{self.dealer_cards[0]}, ?]")
    
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
            logger.warning("Cannot hit - not player's turn")
            return False
            
        new_card = self.deck.pop()
        self.player_cards.append(new_card)
        self.calculate_points()
        
        logger.info(f"Player hit: {new_card} - Total: {self.player_points}")
        
        if self.player_points > 21:
            self.game_status = "player_bust"
            self.message = "Bust!"
            logger.info("Player busted!")
            return True
        elif self.player_points == 21:
            logger.info("Player reached 21 - auto standing")
            return self.stand()
            
        return True
    
    def stand(self):
        if self.game_status != "player_turn":
            logger.warning("Cannot stand - not player's turn")
            return False
            
        self.game_status = "dealer_turn"
        self.message = "Dealer's turn"
        logger.info("Player stands - dealer's turn")
        
        self.calculate_points()
        logger.info(f"Dealer reveals: {self.dealer_cards} ({self.dealer_points} points)")
        
        while self.dealer_points < 17:
            new_card = self.deck.pop()
            self.dealer_cards.append(new_card)
            self.calculate_points()
            logger.info(f"Dealer hits: {new_card} - Total: {self.dealer_points}")
        
        if self.dealer_points > 21:
            self.game_status = "dealer_bust"
            self.message = "Dealer busts! You win!"
            logger.info("Dealer busts - player wins!")
        elif self.dealer_points > self.player_points:
            self.game_status = "dealer_win"
            self.message = "Dealer wins!"
            logger.info("Dealer wins")
        elif self.player_points > self.dealer_points:
            self.game_status = "player_win"
            self.message = "You win!"
            logger.info("Player wins!")
        else:
            self.game_status = "push"
            self.message = "Push! It's a tie."
            logger.info("Push - it's a tie")
        
        return True
    
    def double(self):
        if self.game_status != "player_turn" or len(self.player_cards) != 2:
            logger.warning("Cannot double - invalid conditions")
            return False
            
        logger.info(f"Player doubles - bet: {self.bet} -> {self.bet * 2}")
        
        self.bet *= 2
        
        new_card = self.deck.pop()
        self.player_cards.append(new_card)
        self.calculate_points()
        
        logger.info(f"Player doubles and gets: {new_card} - Total: {self.player_points}")
        
        if self.player_points > 21:
            self.game_status = "player_bust"
            self.message = "Bust after double!"
            logger.info("Player busted after double!")
            return True
        
        logger.info("Double successful - auto standing")
        return self.stand()
    
    def split(self):
        if (self.game_status != "player_turn" or len(self.player_cards) != 2 or 
            self.player_cards[0][0] != self.player_cards[1][0]):
            logger.warning("Cannot split - invalid conditions")
            return False
            
        logger.info("Split requested but not implemented yet")
        return False
    
    def get_game_state(self):
        display_dealer_cards = self.dealer_cards.copy()
        if self.game_status == "player_turn" and len(display_dealer_cards) > 1:
            display_dealer_cards[1] = '?'
        
        return {
            'player_cards': self.player_cards,
            'dealer_cards': display_dealer_cards,
            'player_points': self.player_points,
            'dealer_points': self.dealer_points if self.game_status != "player_turn" else self._calculate_hand_points([display_dealer_cards[0]]),
            'game_status': self.game_status,
            'message': self.message,
            'bet': self.bet
        }

class BlackjackPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="blackjack",
            results_folder=self.get_app_path("temp"),
        )
        self.active_games = {}
        self.elements_folder = self.get_asset_path("blackjack", "board_elements")
        self.generator = BlackjackTableGenerator()
        
        try:
            self.generator.load_elements(self.elements_folder, self.elements_folder)
            logger.info("Blackjack elements loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load blackjack elements: {e}")

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 1)
        if error:
            return error

        balance_before = user["balance"]
        logger.info(f"Blackjack command from {sender}: {args}")

        if len(args) == 0:
            return "Blackjack Commands: /bj start <bet>, /bj hit, /bj stand, /bj double"

        cmd = args[0].lower()

        if cmd == "start":
            if len(args) < 2:
                return "Usage: /bj start <bet>"
            
            try:
                bet = int(args[1])
            except ValueError:
                return "Bet must be a number"
            
            if user_id in self.active_games:
                return "You already have an active game!"
            
            if bet > balance_before:
                return f"Insufficient funds! You have: {balance_before}"
            
            if bet <= 0:
                return "Bet must be positive"
            
            game = BlackjackGame()
            game.bet = bet
            game.deal_initial_cards()
            self.active_games[user_id] = game
            
            new_balance = balance_before - bet
            self.update_user_balance(user_id, new_balance)
            
            logger.info(f"New blackjack game started for {sender}, bet: {bet}")
            
            img_path = os.path.join(self.results_folder, f"blackjack_{user_id}.png")
            self.generator.generate_table_image(game.get_game_state(), img_path)
            
            overlay_path, error = self.apply_user_overlay(img_path, user_id, sender, bet, 0, new_balance, user)
            if overlay_path:
                file_queue.put(overlay_path)
            
            return f"Blackjack started! Bet: {bet}\nYour cards: {', '.join(game.player_cards)} ({game.player_points} points)"

        elif cmd in ["hit", "stand", "double"]:
            if user_id not in self.active_games:
                return "No active game. Use /bj start <bet>"
            
            game = self.active_games[user_id]
            action_completed = False
            
            logger.info(f"{sender} executing {cmd} in blackjack game")
            
            if cmd == "hit":
                action_completed = game.hit()
                action_msg = "Hit"
            elif cmd == "stand":
                action_completed = game.stand()
                action_msg = "Stand"
            elif cmd == "double":
                if balance_before < game.bet * 2:
                    return f"Not enough funds to double! Need: {game.bet * 2}"
                action_completed = game.double()
                if action_completed:
                    new_balance = balance_before - game.bet
                    self.update_user_balance(user_id, new_balance)
                action_msg = "Double"
            
            img_path = os.path.join(self.results_folder, f"blackjack_{user_id}_{cmd}.png")

            if game.game_status not in ["player_turn", "dealer_turn"]:
                win_amount = self._calculate_win_amount(game)
                if win_amount > 0:
                    new_balance = user["balance"] + win_amount
                    self.update_user_balance(user_id, new_balance)
                    logger.info(f"{sender} won {win_amount} from blackjack")
                else:
                    newLevel, newLevelProgress = self.cache.add_experience(user_id, win_amount)
                    user["level"] = newLevel
                    user["level_progress"] = newLevelProgress
                self.active_games.pop(user_id, None)
                logger.info(f"Blackjack game completed for {sender}, result: {game.game_status}")

            self.generator.generate_table_image(game.get_game_state(), img_path)
            
            current_balance = user["balance"] - (game.bet if cmd == "double" and action_completed else 0)
            overlay_path, error = self.apply_user_overlay(img_path, user_id, sender, game.bet, 0, current_balance, user)
            if overlay_path:
                file_queue.put(overlay_path)
            
            return f"{action_msg}! {game.message}\nYour cards: {', '.join(game.player_cards)} ({game.player_points} points)"

        else:
            logger.warning(f"Unknown blackjack command from {sender}: {cmd}")
            return "Unknown command. Use: /bj start <bet>, /bj hit, /bj stand, /bj double"

    def _calculate_win_amount(self, game):
        if game.game_status in ["player_bust", "dealer_win"]:
            return 0
        elif game.game_status in ["player_blackjack"]:
            return int(game.bet * 2.5)
        elif game.game_status in ["player_win", "dealer_bust"]:
            return game.bet * 2
        elif game.game_status == "push":
            return game.bet
        return 0

def register():
    plugin = BlackjackPlugin()
    logger.info("Blackjack plugin registered")
    return {
        "name": "blackjack",
        "aliases": ["/bj"],
        "description": "Blackjack game: /bj start <bet>, /bj hit, /bj stand, /bj double",
        "execute": plugin.execute_game
    }