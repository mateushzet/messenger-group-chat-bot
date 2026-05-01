import os
import json
import random
import shutil
import math
import re
import asyncio
import threading
import time
from datetime import datetime
from PIL import Image, ImageDraw
from base_game_plugin import BaseGamePlugin
from logger import logger
from enum import Enum

class MatchStatus(Enum):
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class MatchEvent(Enum):
    KICKOFF = "kickoff"
    GOAL = "goal"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"
    FOUL = "foul"
    CORNER = "corner"
    OFFSIDE = "offside"
    INJURY = "injury"
    SUBSTITUTION = "substitution"
    HALF_TIME = "half_time"
    FULL_TIME = "full_time"

class FifaCard:
    def __init__(self, filename, filepath, card_id=None):
        self.filename = filename
        self.filepath = filepath
        self.id = card_id
        self.parse_filename()

    def parse_filename(self):
        try:
            parts = self.filename.split('__')
            self.player_name = parts[0]
            rest = parts[1]
            rating_part = rest.split('_')[0]
            self.rating = int(rating_part)
            rest_parts = rest.split('_')
            self.position = rest_parts[1]

            if '_bronze_' in self.filename:
                self.type = 'bronze'
            elif '_silver_' in self.filename:
                self.type = 'silver'
            elif '_gold_' in self.filename:
                self.type = 'gold'
            else:
                self.type = 'unknown'

            if '\\normal\\' in self.filepath or '/normal/' in self.filepath:
                self.category = 'normal'
            else:
                self.category = 'premium'

            self.flag = None
            self.league = None
            self.club = None

            flag_match = re.search(r'flag_(\d+)', self.filename)
            if flag_match:
                self.flag = int(flag_match.group(1))

            league_match = re.search(r'league_(\d+)', self.filename)
            if league_match:
                self.league = int(league_match.group(1))

            club_match = re.search(r'club_(\d+)', self.filename)
            if club_match:
                self.club = int(club_match.group(1))

            if 'Left' in self.filename:
                self.preferred_foot = 'Left'
            elif 'Right' in self.filename:
                self.preferred_foot = 'Right'
            else:
                self.preferred_foot = 'Right'

            self.pac = self._extract_stat('PAC', rest)
            self.sho = self._extract_stat('SHO', rest)
            self.pas = self._extract_stat('PAS', rest)
            self.dri = self._extract_stat('DRI', rest)
            self.defense = self._extract_stat('DEF', rest)
            self.phy = self._extract_stat('PHY', rest)

            price_part = self.filename.split('price_')[-1].split('.')[0]
            self.price = int(price_part)
            self.image_path = self.filepath

            logger.debug(f"[FIFA] Parsed card: {self.player_name}, pos: {self.position}, rating: {self.rating}")

        except Exception as e:
            logger.error(f"[FIFA] Error parsing filename {self.filename}: {e}")
            self.player_name = "Unknown"
            self.rating = 0
            self.position = "Unknown"
            self.type = "unknown"
            self.category = "unknown"
            self.flag = None
            self.league = None
            self.club = None
            self.preferred_foot = 'Right'
            self.pac = self.sho = self.pas = self.dri = self.defense = self.phy = 0
            self.price = 0

    def _extract_stat(self, stat_name, text):
        pattern = f'{stat_name}(\\d+)'
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
        return 0

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'player_name': self.player_name,
            'rating': self.rating,
            'position': self.position,
            'type': self.type,
            'category': self.category,
            'flag': self.flag,
            'league': self.league,
            'club': self.club,
            'preferred_foot': self.preferred_foot,
            'pac': self.pac,
            'sho': self.sho,
            'pas': self.pas,
            'dri': self.dri,
            'defense': self.defense,
            'phy': self.phy,
            'price': self.price,
            'image_path': self.image_path
        }

    @classmethod
    def from_dict(cls, data):
        card = cls(data['filename'], data['image_path'], data.get('id'))
        card.player_name = data['player_name']
        card.rating = data['rating']
        card.position = data['position']
        card.type = data['type']
        card.category = data['category']
        card.flag = data.get('flag')
        card.league = data.get('league')
        card.club = data.get('club')
        card.preferred_foot = data.get('preferred_foot', 'Right')
        card.pac = data.get('pac', 0)
        card.sho = data.get('sho', 0)
        card.pas = data.get('pas', 0)
        card.dri = data.get('dri', 0)
        card.defense = data.get('defense', 0)
        card.phy = data.get('phy', 0)
        card.price = data['price']
        return card

    def __str__(self):
        return f"{self.player_name} ({self.rating}) - {self.position} - {self.price} coins"

class FifaCoinsManager:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.coins_file = os.path.join(data_folder, "fifa_coins.json")
        self.coins_data = self._load_coins()

    def _load_coins(self):
        if os.path.exists(self.coins_file):
            try:
                with open(self.coins_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[FIFA] Error loading coins data: {e}")
                return {}
        return {}

    def _save_coins(self):
        try:
            os.makedirs(self.data_folder, exist_ok=True)
            with open(self.coins_file, 'w', encoding='utf-8') as f:
                json.dump(self.coins_data, f, indent=2)
        except Exception as e:
            logger.error(f"[FIFA] Error saving coins data: {e}")

    def get_coins(self, user_id):
        return self.coins_data.get(str(user_id), 0)

    def add_coins(self, user_id, amount):
        user_id_str = str(user_id)
        current = self.coins_data.get(user_id_str, 0)
        new_amount = max(0, current + amount)
        self.coins_data[user_id_str] = new_amount
        self._save_coins()
        return new_amount

    def remove_coins(self, user_id, amount):
        return self.add_coins(user_id, -amount)

    def initialize_user(self, user_id):
        user_id_str = str(user_id)
        if user_id_str not in self.coins_data:
            self.coins_data[user_id_str] = 2000
            self._save_coins()
            logger.info(f"[FIFA] Initialized new user {user_id} with 2000 FIFA coins")
            return 2000
        return self.coins_data.get(user_id_str, 0)

class FifaCollection:
    def __init__(self, user_id, data_folder):
        self.user_id = user_id
        self.data_folder = data_folder
        self.cards = []
        self.next_id = 1
        self.load()

    def get_collection_path(self):
        return os.path.join(self.data_folder, "collections", f"{self.user_id}.json")

    def load(self):
        collection_path = self.get_collection_path()
        if os.path.exists(collection_path):
            try:
                with open(collection_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cards = [FifaCard.from_dict(card_data) for card_data in data.get('cards', [])]
                    self.next_id = data.get('next_id', len(self.cards) + 1)
                logger.info(f"[FIFA] Loaded {len(self.cards)} cards for user {self.user_id}")
            except Exception as e:
                logger.error(f"[FIFA] Error loading collection for {self.user_id}: {e}")
                self.cards = []
                self.next_id = 1

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.get_collection_path()), exist_ok=True)
            data = {
                'user_id': self.user_id,
                'next_id': self.next_id,
                'cards': [card.to_dict() for card in self.cards]
            }
            with open(self.get_collection_path(), 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[FIFA] Error saving collection for {self.user_id}: {e}")

    def add_card(self, card):
        card.id = self.next_id
        self.next_id += 1
        self.cards.append(card)
        self.save()
        return card.id

    def add_cards(self, cards):
        ids = []
        for card in cards:
            card.id = self.next_id
            self.next_id += 1
            ids.append(card.id)
            self.cards.append(card)
        self.save()
        return ids

    def get_card(self, card_id):
        for card in self.cards:
            if card.id == card_id or str(card.id) == str(card_id):
                return card
        return None

    def remove_card(self, card_id):
        for i, card in enumerate(self.cards):
            if card.id == card_id:
                removed = self.cards.pop(i)
                self.save()
                return removed
        return None

    def remove_cards(self, card_ids):
        removed = []
        remaining = []
        for card in self.cards:
            if card.id in card_ids:
                removed.append(card)
            else:
                remaining.append(card)
        self.cards = remaining
        self.save()
        return removed

    def get_filtered_cards(self, sort_by='new', position=None, page=1, per_page=10):
        logger.info(f"[FIFA] get_filtered_cards called with position={position}, sort_by={sort_by}, page={page}")
        cards = self.cards.copy()

        if position:
            logger.info(f"[FIFA] Filtering cards by position: {position}")
            all_positions = set(c.position for c in cards)
            logger.info(f"[FIFA] Available positions in collection: {all_positions}")
            cards = [c for c in cards if c.position.upper() == position]
            logger.info(f"[FIFA] After position filter: {len(cards)} cards")

        if sort_by == 'new':
            cards.sort(key=lambda c: c.id if hasattr(c, 'id') else 0, reverse=True)
        elif sort_by == 'old':
            cards.sort(key=lambda c: c.id if hasattr(c, 'id') else 0)
        elif sort_by == 'rating':
            cards.sort(key=lambda c: c.rating, reverse=True)
        elif sort_by == 'price':
            cards.sort(key=lambda c: c.price, reverse=True)
        elif sort_by == 'name':
            cards.sort(key=lambda c: c.player_name)

        start = (page - 1) * per_page
        end = start + per_page
        paginated_cards = cards[start:end]
        total_pages = math.ceil(len(cards) / per_page) if cards else 1

        return paginated_cards, total_pages, len(cards)

class FifaPackOpener:
    def __init__(self, assets_folder):
        self.assets_folder = assets_folder
        self.cards_folder = os.path.join(assets_folder, "cards")
        self.cards_cache = self._load_all_cards()

    def _load_all_cards(self):
        cards = {
            'bronze': {'normal': [], 'premium': []},
            'silver': {'normal': [], 'premium': []},
            'gold': {'normal': [], 'premium': []}
        }

        for pack_type in ['bronze', 'silver', 'gold']:
            for category in ['normal', 'premium']:
                folder = os.path.join(self.cards_folder, pack_type, category)
                if os.path.exists(folder):
                    for filename in os.listdir(folder):
                        if filename.endswith('.png'):
                            filepath = os.path.join(folder, filename)
                            card = FifaCard(filename, filepath)
                            cards[pack_type][category].append(card)
        return cards

    def open_pack(self, pack_type):
        if pack_type not in self.cards_cache:
            return None

        normal_cards = self.cards_cache[pack_type]['normal']
        premium_cards = self.cards_cache[pack_type]['premium']

        if not normal_cards or not premium_cards:
            return None

        selected_normal = random.sample(normal_cards, min(6, len(normal_cards)))
        selected_premium = random.sample(premium_cards, min(2, len(premium_cards)))
        all_cards = selected_normal + selected_premium
        all_cards.sort(key=lambda c: c.rating, reverse=True)

        return all_cards

class FifaFormation:
    def __init__(self, formation_id, filename):
        self.id = formation_id
        self.filename = filename
        self.name = self._extract_name(filename)
        self.display_name = self._format_display_name(filename)
        self.is_active = False
        self.grid = self.get_position_grid()

    def _extract_name(self, filename):
        name = filename.replace('formation_', '').replace('.png', '')
        return name

    def _format_display_name(self, filename):
        name = self._extract_name(filename)
        if '(' in name:
            base = name.split('(')[0]
            variant = name.split('(')[1].replace(')', '')
            formatted_base = '-'.join(base)
            return f"{formatted_base} ({variant})"
        else:
            return '-'.join(name)

    def get_base_name(self):
        name = self._extract_name(self.filename)
        if '(' in name:
            return name.split('(')[0]
        return name

    def get_position_grid(self):
        base_name = self.get_base_name()

        formations_grid = {
            '3142': [
                ['ST', 'ST'], ['CAM'], ['LM', 'CM', 'RM'], ['CDM'], ['CB', 'CB', 'CB'], ['GK']
            ],
            '3412': [
                ['ST', 'ST'], ['CAM'], ['LM', 'CM', 'RM'], ['CDM'], ['CB', 'CB', 'CB'], ['GK']
            ],
            '3421': [
                ['ST'], ['CAM', 'CAM'], ['LM', 'CM', 'RM'], ['CDM'], ['CB', 'CB', 'CB'], ['GK']
            ],
            '343': [
                ['LW', 'ST', 'RW'], ['LM', 'CM', 'CM', 'RM'], ['CB', 'CB', 'CB'], ['GK']
            ],
            '352': [
                ['ST', 'ST'], ['CAM'], ['LM', 'CM', 'CM', 'RM'], ['CB', 'CB', 'CB'], ['GK']
            ],
            '41212': [
                ['ST', 'ST'], ['CAM'], ['CM', 'CM'], ['CDM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
            ],
            '4132': [
                ['ST', 'ST'], ['CM', 'CM', 'CM'], ['CDM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
            ],
            '4141': [
                ['ST'], ['LM', 'CM', 'CM', 'RM'], ['CDM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
            ],
            '4213': [
                ['LW', 'ST', 'RW'], ['CAM'], ['CDM', 'CDM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
            ],
            '4222': [
                ['ST', 'ST'], ['CAM', 'CAM'], ['CDM', 'CDM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
            ],
            '4231': [
                ['ST'], ['CAM', 'CAM', 'CAM'], ['CDM', 'CDM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
            ],
            '424': [
                ['LW', 'ST', 'ST', 'RW'], ['CM', 'CM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
            ],
            '4312': [
                ['ST', 'ST'], ['CAM'], ['CM', 'CM', 'CM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
            ],
            '4321': [
                ['ST'], ['CF', 'CF'], ['CM', 'CM', 'CM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
            ],
            '433': [
                ['LW', 'ST', 'RW'], ['CM', 'CM', 'CM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
            ],
            '4411': [
                ['ST'], ['CF'], ['LM', 'CM', 'CM', 'RM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
            ],
            '442': [
                ['ST', 'ST'], ['LM', 'CM', 'CM', 'RM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
            ],
            '451': [
                ['ST'], ['LM', 'CAM', 'CAM', 'RM'], ['CDM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
            ],
            '5212': [
                ['ST', 'ST'], ['CAM'], ['CM', 'CM'], ['LWB', 'CB', 'CB', 'CB', 'RWB'], ['GK']
            ],
            '523': [
                ['LW', 'ST', 'RW'], ['CM', 'CM'], ['LWB', 'CB', 'CB', 'CB', 'RWB'], ['GK']
            ],
            '532': [
                ['ST', 'ST'], ['CM', 'CM', 'CM'], ['LWB', 'CB', 'CB', 'CB', 'RWB'], ['GK']
            ],
            '541': [
                ['ST'], ['LM', 'CM', 'CM', 'RM'], ['LWB', 'CB', 'CB', 'CB', 'RWB'], ['GK']
            ]
        }

        if base_name in formations_grid:
            return formations_grid[base_name]

        return [
            ['ST', 'ST'], ['LM', 'CM', 'CM', 'RM'], ['LB', 'CB', 'CB', 'RB'], ['GK']
        ]

    def get_player_count(self):
        grid = self.get_position_grid()
        return sum(len(line) for line in grid)

class FifaTeam:
    def __init__(self, user_id, data_folder):
        self.user_id = user_id
        self.data_folder = data_folder
        self.active_formation_id = 0
        self.players = {}
        self.load()

    def get_team_path(self):
        return os.path.join(self.data_folder, "teams", f"{self.user_id}.json")

    def load(self):
        team_path = self.get_team_path()
        if os.path.exists(team_path):
            try:
                with open(team_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.active_formation_id = data.get('active_formation_id', 0)
                    self.players = data.get('players', {})
                logger.info(f"[FIFA] Loaded team for user {self.user_id}: players={self.players}")
            except Exception as e:
                logger.error(f"[FIFA] Error loading team for {self.user_id}: {e}")
                self.active_formation_id = 0
                self.players = {}

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.get_team_path()), exist_ok=True)
            data = {
                'user_id': self.user_id,
                'active_formation_id': self.active_formation_id,
                'players': self.players
            }
            with open(self.get_team_path(), 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"[FIFA] Error saving team for {self.user_id}: {e}")

    def set_formation(self, formation_id):
        self.active_formation_id = formation_id
        self.players = {}
        self.save()

    def set_player(self, slot_id, card_id):
        card_id_str = str(card_id)


        for existing_slot, existing_card_id in self.players.items():
            if existing_card_id == card_id_str and int(existing_slot) != slot_id:
                return False, f"Card ID {card_id} is already in your team at slot {existing_slot}! Remove it first before placing elsewhere."


        self.players[str(slot_id)] = card_id_str
        self.save()

        logger.info(f"[FIFA] Team saved for user {self.user_id}. Current players: {self.players}")

        return True, f"Player placed in slot {slot_id}."

    def remove_player(self, slot_id):
        if str(slot_id) in self.players:
            del self.players[str(slot_id)]
            self.save()

    def get_player_at_slot(self, slot_id):
        result = self.players.get(str(slot_id))

        if result is not None:
            try:
                return int(result)
            except ValueError:
                return result
        return None

class FifaFormationManager:
    def __init__(self, formations_folder, formations_images_folder):
        self.formations_folder = formations_folder
        self.formations_images_folder = formations_images_folder
        self.formations = []
        self.load_formations()

    def load_formations(self):
        if os.path.exists(self.formations_folder):
            formation_files = [
                '3142.png', '3412.png', '3421.png', '343.png', '352.png',
                '41212(2).png', '41212.png', '4132.png', '4141.png',
                '4213.png', '4222.png', '4231(2).png', '4231.png', '424.png',
                '4312.png', '4321.png', '433(2).png', '433(3).png', '433(4).png', '433.png',
                '4411(2).png', '442(2).png', '442.png', '451(2).png', '451.png',
                '5212.png', '523.png', '532.png', '541.png'
            ]

            for i, filename in enumerate(formation_files):
                file_path = os.path.join(self.formations_folder, filename)
                if os.path.exists(file_path):
                    formation = FifaFormation(i, filename)
                    self.formations.append(formation)

            logger.info(f"[FIFA] Loaded {len(self.formations)} formations")

    def get_formation(self, formation_id):
        if 0 <= formation_id < len(self.formations):
            return self.formations[formation_id]
        return None

    def get_formation_image_path(self, formation):
        return os.path.join(self.formations_images_folder, formation.filename)

    def get_formations_page(self, page=1, per_page=10):
        start = (page - 1) * per_page
        end = start + per_page
        paginated = self.formations[start:end]
        total_pages = math.ceil(len(self.formations) / per_page)
        return paginated, total_pages

class FifaImageGenerator:
    def __init__(self, text_renderer=None, fifa_coins_icon=None):
        self.text_renderer = text_renderer
        self.fifa_coins_icon = fifa_coins_icon

    def _add_fifa_coins_display(self, img, draw, width, height, fifa_coins):
        if self.text_renderer and self.fifa_coins_icon:
            try:
                coins_icon = self.fifa_coins_icon.copy()
                coins_icon = coins_icon.resize((20, 20))
                coins_text = str(fifa_coins)
                coins_img = self.text_renderer.render_text(
                    text=coins_text, font_size=14, color=(255, 215, 0, 255),
                    stroke_width=1, stroke_color=(0, 0, 0, 255)
                )
                icon_x = 10
                icon_y = height - 30
                text_x = icon_x + 25
                text_y = icon_y - 2
                draw.rectangle([icon_x-2, icon_y-2, text_x + coins_img.width + 2, icon_y + 22], fill=(0, 0, 0, 180))
                img.paste(coins_icon, (icon_x, icon_y), coins_icon)
                img.paste(coins_img, (text_x, text_y), coins_img)
            except Exception as e:
                logger.error(f"[FIFA] Error adding FIFA coins: {e}")

    def _add_command_info(self, img, draw, width, height):
        if self.text_renderer:
            try:
                command_text = "/fifa cards [page]  |  Sort: new/old/rating/price/name  |  Filter: GK/CB/ST etc. | /fifa sell <id>"
                command_img = self.text_renderer.render_text(
                    text=command_text, font_size=12, color=(200, 200, 200, 255),
                    stroke_width=1, stroke_color=(0, 0, 0, 100)
                )
                x = (width - command_img.width) // 2
                y = height - 25
                draw.rectangle([x-5, y-2, x + command_img.width + 5, y + command_img.height + 2], fill=(0, 0, 0, 150))
                img.paste(command_img, (x, y), command_img)
            except Exception as e:
                logger.error(f"[FIFA] Error adding command info: {e}")

    def generate_pack_image(self, cards, output_path, fifa_coins=0):
        if not cards:
            return None

        CARD_WIDTH = 110
        CARD_HEIGHT = 130
        PADDING = 10
        MARGIN = 10
        cols = 4
        rows = 2

        inner_width = cols * (CARD_WIDTH + PADDING) + PADDING
        inner_height = rows * (CARD_HEIGHT + PADDING) + PADDING + 50
        width = inner_width + (MARGIN * 2)
        height = inner_height + (MARGIN * 2) + 30

        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([MARGIN, MARGIN, MARGIN + inner_width, MARGIN + inner_height], fill=(27, 36, 38, 255))

        total_value = sum(card.price for card in cards)

        for i, card in enumerate(cards):
            row = i // cols
            col = i % cols
            x = MARGIN + col * (CARD_WIDTH + PADDING) + PADDING
            y = MARGIN + row * (CARD_HEIGHT + PADDING) + PADDING

            try:
                card_img = Image.open(card.image_path).convert('RGBA')
                card_img = card_img.resize((CARD_WIDTH, CARD_HEIGHT))
                img.paste(card_img, (x, y), card_img)

                if hasattr(card, 'id') and card.id and self.text_renderer:
                    id_text = f"id {card.id}"
                    id_img = self.text_renderer.render_text(text=id_text, font_size=10, color=(255, 255, 255, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
                    img.paste(id_img, (x + 3, y + 3), id_img)

                if self.text_renderer and self.fifa_coins_icon:
                    coin_icon = self.fifa_coins_icon.copy()
                    coin_icon = coin_icon.resize((12, 12))
                    price_text = f"{card.price}"
                    price_img = self.text_renderer.render_text(text=price_text, font_size=10, color=(255, 215, 0, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
                    icon_x = x + (CARD_WIDTH - (price_img.width + 15)) // 2
                    price_x = icon_x + 15
                    price_y = y + CARD_HEIGHT - 10
                    img.paste(coin_icon, (icon_x, price_y - 1), coin_icon)
                    img.paste(price_img, (price_x, price_y), price_img)
            except Exception as e:
                logger.error(f"[FIFA] Error loading card image: {e}")
                draw.rectangle([x, y, x + CARD_WIDTH, y + CARD_HEIGHT], fill=(50, 50, 60), outline=(100, 100, 120))

        if self.text_renderer and self.fifa_coins_icon:
            coin_icon = self.fifa_coins_icon.copy()
            coin_icon = coin_icon.resize((16, 16))
            total_text = f"Total value: {total_value}"
            total_img = self.text_renderer.render_text(text=total_text, font_size=14, color=(255, 215, 0, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
            icon_x = MARGIN + (inner_width - (total_img.width + 20)) // 2
            text_x = icon_x + 20
            text_y = MARGIN + inner_height - 35
            img.paste(coin_icon, (icon_x, text_y - 2), coin_icon)
            img.paste(total_img, (text_x, text_y), total_img)

        self._add_fifa_coins_display(img, draw, width, height, fifa_coins)
        img.save(output_path, format='PNG')
        return output_path

    def generate_formations_image(self, formations, page, total_pages, active_formation_id, formations_folder, output_path, fifa_coins=0):
        FORMATION_SIZE = 120
        PADDING = 10
        COLS = 3
        ROWS = 3
        MARGIN = 20
        ROW_SPACING = 60

        inner_width = COLS * FORMATION_SIZE + (COLS - 1) * PADDING
        inner_height = ROWS * FORMATION_SIZE + (ROWS - 1) * (PADDING + ROW_SPACING) + 80
        width = inner_width + MARGIN * 2
        height = inner_height + MARGIN * 2 + 40

        img = Image.new('RGBA', (width, height), (27, 36, 38, 255))
        draw = ImageDraw.Draw(img)

        if self.text_renderer:
            header_text = f"FIFA Formations - Page {page}/{total_pages}"
            header_img = self.text_renderer.render_text(text=header_text, font_size=20, color=(255, 215, 0, 255), stroke_width=2, stroke_color=(0, 0, 0, 255))
            x = (width - header_img.width) // 2
            y = 10
            img.paste(header_img, (x, y), header_img)

        for idx, formation in enumerate(formations[:9]):
            row = idx // COLS
            col = idx % COLS
            x = MARGIN + col * (FORMATION_SIZE + PADDING)
            y = MARGIN + 50 + row * (FORMATION_SIZE + PADDING + ROW_SPACING)

            formation_path = os.path.join(formations_folder, formation.filename)
            if os.path.exists(formation_path):
                formation_img = Image.open(formation_path).convert('RGBA')
                formation_img = formation_img.resize((FORMATION_SIZE, FORMATION_SIZE))

                if formation.id == active_formation_id:
                    draw.rectangle([x-3, y-3, x+FORMATION_SIZE+3, y+FORMATION_SIZE+3], outline=(255, 215, 0), width=4)

                img.paste(formation_img, (x, y), formation_img)

                if self.text_renderer:
                    id_text = f"[{formation.id}] {formation.display_name}"
                    id_img = self.text_renderer.render_text(text=id_text, font_size=12, color=(255, 255, 255, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
                    text_x = x + (FORMATION_SIZE - id_img.width) // 2
                    text_y = y + FORMATION_SIZE + 10
                    draw.rectangle([text_x-2, text_y-2, text_x + id_img.width + 2, text_y + id_img.height + 2], fill=(0, 0, 0, 150))
                    img.paste(id_img, (text_x, text_y), id_img)

        self._add_fifa_coins_display(img, draw, width, height, fifa_coins)

        if self.text_renderer:
            select_text = "/fifa formations set <id>"
            select_img = self.text_renderer.render_text(text=select_text, font_size=14, color=(255, 215, 0, 255), stroke_width=1, stroke_color=(0, 0, 0, 100))
            nav_text = ""
            if page > 1:
                nav_text += f"/fifa formations {page-1}"
            if page < total_pages:
                if nav_text:
                    nav_text += "  |  "
                nav_text += f"/fifa formations {page+1}"
            nav_img = self.text_renderer.render_text(text=nav_text, font_size=14, color=(200, 200, 200, 255), stroke_width=1, stroke_color=(0, 0, 0, 100))

            select_x = (width - select_img.width) // 2
            select_y = height - 55
            nav_x = (width - nav_img.width) // 2
            nav_y = height - 30

            draw.rectangle([select_x-5, select_y-2, select_x + select_img.width + 5, select_y + select_img.height + 2], fill=(0, 0, 0, 150))
            draw.rectangle([nav_x-5, nav_y-2, nav_x + nav_img.width + 5, nav_y + nav_img.height + 2], fill=(0, 0, 0, 150))
            img.paste(select_img, (select_x, select_y), select_img)
            img.paste(nav_img, (nav_x, nav_y), nav_img)

        img.save(output_path, format='PNG')
        return output_path

    def generate_collection_image(self, cards, page, total_pages, total_cards, sort_by, position, output_path, fifa_coins=0):
        if not cards:
            return None

        CARDS_PER_ROW = 5
        ROWS = 2
        CARD_WIDTH = 110
        CARD_HEIGHT = 130
        PADDING = 10
        MARGIN = 10

        inner_width = CARDS_PER_ROW * (CARD_WIDTH + PADDING) + PADDING
        inner_height = ROWS * (CARD_HEIGHT + PADDING) + PADDING + 80
        width = inner_width + (MARGIN * 2)
        height = inner_height + (MARGIN * 2) + 40

        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.rectangle([MARGIN, MARGIN, MARGIN + inner_width, MARGIN + inner_height], fill=(27, 36, 38, 255))

        if self.text_renderer:
            header_text = f"Your FIFA Collection - Page {page}/{total_pages}"
            header_img = self.text_renderer.render_text(text=header_text, font_size=16, color=(255, 215, 0, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
            x = MARGIN + (inner_width - header_img.width) // 2
            y = MARGIN + 10
            img.paste(header_img, (x, y), header_img)

            filter_text = f"Total: {total_cards} cards"
            if position:
                filter_text += f" | Filter: {position}"
            filter_text += f" | Sort: {sort_by}"
            filter_img = self.text_renderer.render_text(text=filter_text, font_size=10, color=(200, 200, 200, 255))
            x = MARGIN + (inner_width - filter_img.width) // 2
            y = MARGIN + 32
            img.paste(filter_img, (x, y), filter_img)

        for i, card in enumerate(cards[:10]):
            row = i // CARDS_PER_ROW
            col = i % CARDS_PER_ROW
            x = MARGIN + col * (CARD_WIDTH + PADDING) + PADDING
            y = MARGIN + row * (CARD_HEIGHT + PADDING) + PADDING + 50

            try:
                card_img = Image.open(card.image_path).convert('RGBA')
                card_img = card_img.resize((CARD_WIDTH, CARD_HEIGHT))
                img.paste(card_img, (x, y), card_img)

                if hasattr(card, 'id') and card.id and self.text_renderer:
                    id_text = f"id {card.id}"
                    id_img = self.text_renderer.render_text(text=id_text, font_size=10, color=(255, 255, 255, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
                    img.paste(id_img, (x + 3, y + 3), id_img)

                if self.text_renderer and self.fifa_coins_icon:
                    coin_icon = self.fifa_coins_icon.copy()
                    coin_icon = coin_icon.resize((12, 12))
                    price_text = f"{card.price}"
                    price_img = self.text_renderer.render_text(text=price_text, font_size=10, color=(255, 215, 0, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
                    icon_x = x + (CARD_WIDTH - (price_img.width + 15)) // 2
                    price_x = icon_x + 15
                    price_y = y + CARD_HEIGHT - 10
                    img.paste(coin_icon, (icon_x, price_y - 1), coin_icon)
                    img.paste(price_img, (price_x, price_y), price_img)
            except Exception as e:
                logger.error(f"[FIFA] Error loading card image: {e}")
                draw.rectangle([x, y, x + CARD_WIDTH, y + CARD_HEIGHT], fill=(50, 50, 60), outline=(100, 100, 120))

        self._add_fifa_coins_display(img, draw, width, height-20, fifa_coins)


        self._add_command_info(img, draw, width, height)

        if self.text_renderer and (page > 1 or page < total_pages):
            nav_parts = []
            if page > 1:
                nav_parts.append(f"/fifa cards {page-1}")
            if page < total_pages:
                nav_parts.append(f"/fifa cards {page+1}")
            nav_text = " | ".join(nav_parts)
            nav_img = self.text_renderer.render_text(text=nav_text, font_size=12, color=(150, 150, 150, 255), stroke_width=1, stroke_color=(0, 0, 0, 100))
            x = MARGIN + (inner_width - nav_img.width) // 2
            y = MARGIN + inner_height - 25
            img.paste(nav_img, (x, y), nav_img)

        img.save(output_path, format='PNG')
        return output_path

class FifaTeamImageGenerator:
    def __init__(self, text_renderer=None, fifa_coins_icon=None):
        self.text_renderer = text_renderer
        self.fifa_coins_icon = fifa_coins_icon
        self.match = None
        self.event_icons = {}
        self.opponent_logos_folder = None
        self._load_event_icons()

    def _load_event_icons(self):
        current_file = os.path.abspath(__file__)
        plugins_dir = os.path.dirname(current_file)
        app_dir = os.path.dirname(plugins_dir)
        assets_dir = os.path.join(app_dir, "assets")
        icons_folder = os.path.join(assets_dir, "fifa", "match_icons")


        icon_files = {
            'goal': 'goal.png',
            'yellow_card': 'yellow_card.png',
            'red_card': 'red_card.png',
            'substitution': 'substitution.png',
            'offside': 'offside.png',
            'injury': 'injury.png',
            'penalty': 'penalty.png',
            'foul': 'foul.png',
            'corner': 'corner.png',
            'shot': 'shot.png',
            'save': 'save.png',
            'counter': 'counter.png'
        }

        for event_type, filename in icon_files.items():
            icon_path = os.path.join(icons_folder, filename)
            if os.path.exists(icon_path):
                try:
                    icon = Image.open(icon_path).convert('RGBA')
                    icon = icon.resize((24, 24))
                    self.event_icons[event_type] = icon
                    logger.info(f"[FIFA] Loaded {event_type} icon")
                except Exception as e:
                    logger.error(f"[FIFA] Error loading icon {filename}: {e}")
            else:
                logger.warning(f"[FIFA] Icon not found: {filename} for {event_type}")

    def draw_chemistry_lines(self, draw, card_positions, team_data, collection, grid, is_user=True):
        slot_grid = {}
        slot_id = 1
        for row_idx, line in enumerate(grid):
            for col_idx, position in enumerate(line):
                slot_grid[slot_id] = {'row': row_idx, 'col': col_idx, 'position': position}
                slot_id += 1


        def get_w(pos):
            w = {'GK':1, 'CB':1, 'CDM':1, 'CM':1, 'CAM':1, 'ST':1, 'CF':1,
                 'LB':0, 'LWB':0, 'LM':0, 'LW':0, 'RB':2, 'RWB':2, 'RM':2, 'RW':2}
            return w.get(pos, 1)

        for slot_a, info_a in slot_grid.items():
            for slot_b, info_b in slot_grid.items():
                if slot_a >= slot_b: continue

                row_diff = abs(info_b['row'] - info_a['row'])
                col_diff = abs(info_b['col'] - info_a['col'])
                pos_a, pos_b = info_a['position'], info_b['position']

                is_connected = False
                if row_diff == 0 and col_diff == 1: is_connected = True
                elif row_diff == 1:
                    if col_diff <= 1 and abs(get_w(pos_a) - get_w(pos_b)) <= 1: is_connected = True
                    elif col_diff <= 2 and ({'CDM', 'CB'} <= {pos_a, pos_b} or {'CM', 'CB'} <= {pos_a, pos_b}): is_connected = True
                if not is_connected and row_diff <= 2 and {'GK', 'CB'} <= {pos_a, pos_b}: is_connected = True

                if is_connected:

                    if hasattr(team_data, 'get_player_at_slot'):
                        card_a = collection.get_card(team_data.get_player_at_slot(slot_a))
                        card_b = collection.get_card(team_data.get_player_at_slot(slot_b))
                    else:
                        card_a = team_data[slot_a-1] if slot_a-1 < len(team_data) else None
                        card_b = team_data[slot_b-1] if slot_b-1 < len(team_data) else None

                    if card_a and card_b:
                        chemistry = self.calculate_chemistry(card_a, card_b)
                        color = self.get_link_color(chemistry)
                        c_a, c_b = card_positions.get(slot_a, {}).get('center'), card_positions.get(slot_b, {}).get('center')
                        if c_a and c_b:
                            draw.line([c_a, c_b], fill=color, width=2)
                            mid_x, mid_y = (c_a[0] + c_b[0]) // 2, (c_a[1] + c_b[1]) // 2
                            draw.ellipse([mid_x-2, mid_y-2, mid_x+2, mid_y+2], fill=color)

    def _add_team_command_info(self, img, draw, width, height):
        if self.text_renderer:
            try:
                command_text = "/fc team set <slot> <card_id>  |  /fc team remove <slot>  |  /fc formations"
                command_img = self.text_renderer.render_text(
                    text=command_text, font_size=12, color=(200, 200, 200, 255),
                    stroke_width=1, stroke_color=(0, 0, 0, 100)
                )
                x = (width - command_img.width) // 2
                y = height - 25
                draw.rectangle([x-5, y-2, x + command_img.width + 5, y + command_img.height + 2], fill=(0, 0, 0, 150))
                img.paste(command_img, (x, y), command_img)
            except Exception as e:
                logger.error(f"[FIFA] Error adding team command info: {e}")

    def calculate_chemistry(self, card1, card2):
        if not card1 or not card2:
            return 0
        chemistry = 0
        if card1.club and card2.club and card1.club == card2.club:
            chemistry += 3
        if card1.league and card2.league and card1.league == card2.league:
            chemistry += 1
        if card1.flag and card2.flag and card1.flag == card2.flag:
            chemistry += 1
        return chemistry

    def get_link_color(self, chemistry):
        if chemistry >= 4:
            return (0, 255, 0, 255)
        elif chemistry >= 2:
            return (255, 255, 0, 255)
        elif chemistry >= 1:
            return (255, 165, 0, 255)
        else:
            return (255, 0, 0, 255)

    def _add_fifa_coins_display(self, img, draw, width, height, fifa_coins):
        if self.text_renderer and self.fifa_coins_icon:
            try:
                coins_icon = self.fifa_coins_icon.copy()
                coins_icon = coins_icon.resize((20, 20))
                coins_text = str(fifa_coins)
                coins_img = self.text_renderer.render_text(text=coins_text, font_size=14, color=(255, 215, 0, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
                icon_x = 10
                icon_y = height - 30
                text_x = icon_x + 25
                text_y = icon_y - 2
                draw.rectangle([icon_x-2, icon_y-2, text_x + coins_img.width + 2, icon_y + 22], fill=(0, 0, 0, 180))
                img.paste(coins_icon, (icon_x, icon_y), coins_icon)
                img.paste(coins_img, (text_x, text_y), coins_img)
            except Exception as e:
                logger.error(f"[FIFA] Error adding FIFA coins: {e}")

    def draw_connection_lines(self, draw, positions_with_coords, players, collection):


        slot_map = {}
        slot_id = 1
        for row_idx, row in enumerate(positions_with_coords):
            for col_idx, (pos_info, coords) in enumerate(row):
                slot_map[slot_id] = {
                    'row': row_idx,
                    'col': col_idx,
                    'position': pos_info['pos'],
                    'coords': coords
                }
                slot_id += 1


        connections = [
            (0, 1),
            (1, 0),
            (1, 1),
            (1, -1),
        ]


        for slot_a, info_a in slot_map.items():
            for slot_b, info_b in slot_map.items():
                if slot_a >= slot_b:
                    continue

                row_diff = info_b['row'] - info_a['row']
                col_diff = info_b['col'] - info_a['col']


                is_connected = False


                if row_diff == 0 and abs(col_diff) == 1:
                    is_connected = True

                elif row_diff == 1 and abs(col_diff) <= 1:

                    pos_a = info_a['position']
                    pos_b = info_b['position']


                    if self._should_connect_positions(pos_a, pos_b):
                        is_connected = True

                    elif abs(col_diff) <= 1:
                        is_connected = True

                if is_connected:
                    card_id_a = players.get(str(slot_a))
                    card_id_b = players.get(str(slot_b))
                    card_a = collection.get_card(card_id_a) if card_id_a else None
                    card_b = collection.get_card(card_id_b) if card_id_b else None

                    if card_a and card_b:
                        chemistry = self.calculate_chemistry(card_a, card_b)
                        color = self.get_link_color(chemistry)

                        x1, y1 = info_a['coords']
                        x2, y2 = info_b['coords']

                        start_x = x1 + 35
                        start_y = y1 + 42
                        end_x = x2 + 35
                        end_y = y2 + 42

                        draw.line([(start_x, start_y), (end_x, end_y)], fill=color, width=3)

    def _should_connect_positions(self, pos_a, pos_b):

        forward_positions = ['ST', 'CF', 'LW', 'RW']
        midfield_positions = ['CAM', 'CM', 'CDM', 'LM', 'RM']
        defense_positions = ['CB', 'LB', 'RB', 'LWB', 'RWB']


        def get_zone(pos):
            if pos in forward_positions:
                return 'forward'
            elif pos in midfield_positions:
                return 'midfield'
            elif pos in defense_positions or pos == 'GK':
                return 'defense'
            return 'other'

        zone_a = get_zone(pos_a)
        zone_b = get_zone(pos_b)


        if (zone_a == 'forward' and zone_b == 'midfield') or (zone_a == 'midfield' and zone_b == 'forward'):
            return True


        if (zone_a == 'midfield' and zone_b == 'defense') or (zone_a == 'defense' and zone_b == 'midfield'):
            return True


        if (pos_a == 'CDM' and pos_b == 'CB') or (pos_a == 'CB' and pos_b == 'CDM'):
            return True


        if (pos_a in ['LB', 'RB', 'LWB', 'RWB'] and pos_b in ['LM', 'RM']) or\
        (pos_a in ['LM', 'RM'] and pos_b in ['LB', 'RB', 'LWB', 'RWB']):
            return True

        return False

    def generate_team_image(self, formation, formation_image_path, team, collection, output_path, fifa_coins=0):
        if not formation:
            return None

        try:
            formation_img = Image.open(formation_image_path).convert('RGBA')
        except Exception as e:
            logger.error(f"[FIFA] Error loading formation image: {e}")
            return None

        FORMATION_WIDTH = 300
        PLAYER_WIDTH = 70
        PLAYER_HEIGHT = 85
        PADDING = 5
        MARGIN = 30

        formation_img = formation_img.resize((FORMATION_WIDTH, FORMATION_WIDTH))
        grid = formation.get_position_grid()
        grid_width = max(len(line) for line in grid) * (PLAYER_WIDTH + PADDING)
        game_width = FORMATION_WIDTH + grid_width + 3 * MARGIN
        game_height = max(FORMATION_WIDTH, len(grid) * (PLAYER_HEIGHT + PADDING) + 100) + 2 * MARGIN

        game_img = Image.new('RGBA', (game_width, game_height), (27, 36, 38, 255))
        draw = ImageDraw.Draw(game_img)
        game_img.paste(formation_img, (MARGIN, MARGIN), formation_img)


        card_positions = {}
        slot_id = 1
        for row_idx, line in enumerate(grid):
            line_width = len(line) * (PLAYER_WIDTH + PADDING) - PADDING
            x_start = FORMATION_WIDTH + 2 * MARGIN + (grid_width - line_width) // 2
            for col_idx, position in enumerate(line):
                x = x_start + col_idx * (PLAYER_WIDTH + PADDING)
                y = MARGIN + row_idx * (PLAYER_HEIGHT + PADDING)
                card_positions[slot_id] = {
                    'center': (x + PLAYER_WIDTH // 2, y + PLAYER_HEIGHT // 2),
                    'x': x, 'y': y
                }
                slot_id += 1


        self._draw_preview_chemistry_lines(draw, card_positions, team, collection, grid, is_user=True)


        slot_id = 1
        for row_idx, line in enumerate(grid):
            line_width = len(line) * (PLAYER_WIDTH + PADDING) - PADDING
            x_start = FORMATION_WIDTH + 2 * MARGIN + (grid_width - line_width) // 2
            for col_idx, position in enumerate(line):
                x = x_start + col_idx * (PLAYER_WIDTH + PADDING)
                y = MARGIN + row_idx * (PLAYER_HEIGHT + PADDING)

                card_id = team.get_player_at_slot(slot_id)
                player = collection.get_card(card_id) if card_id else None

                if player:
                    try:
                        p_img = Image.open(player.image_path).convert('RGBA').resize((PLAYER_WIDTH, PLAYER_HEIGHT))
                        game_img.paste(p_img, (x, y), p_img)

                    except:
                        draw.rectangle([x, y, x + PLAYER_WIDTH, y + PLAYER_HEIGHT], fill=(50, 100, 150))
                else:
                    draw.rectangle([x, y, x + PLAYER_WIDTH, y + PLAYER_HEIGHT], fill=(40, 40, 50), outline=(100, 100, 120))
                slot_id += 1

        self._add_fifa_coins_display(game_img, draw, game_width, game_height, fifa_coins)
        self._add_team_command_info(game_img, draw, game_width, game_height)

        game_img.save(output_path, format='PNG')
        return output_path

    def generate_team_preview(self, formation, formation_image_path, team, collection, output_path, fifa_coins=0):
        if not formation:
            return None

        try:
            formation_img = Image.open(formation_image_path).convert('RGBA')
        except Exception as e:
            logger.error(f"[FIFA] Error loading formation image: {e}")
            return None

        FORMATION_WIDTH = 300
        PLAYER_WIDTH = 70
        PLAYER_HEIGHT = 85
        PADDING = 5
        MARGIN = 30

        formation_img = formation_img.resize((FORMATION_WIDTH, FORMATION_WIDTH))
        grid = formation.get_position_grid()
        max_cols = max(len(line) for line in grid)
        grid_width = max_cols * (PLAYER_WIDTH + PADDING) - PADDING
        grid_height = len(grid) * (PLAYER_HEIGHT + PADDING) - PADDING
        game_width = FORMATION_WIDTH + grid_width + 3 * MARGIN
        game_height = max(FORMATION_WIDTH, grid_height) + 2 * MARGIN + 40

        game_img = Image.new('RGBA', (game_width, game_height), (27, 36, 38, 255))
        draw = ImageDraw.Draw(game_img)
        game_img.paste(formation_img, (MARGIN, MARGIN), formation_img)

        if self.text_renderer:
            title_text = "FORMATION"
            title_img = self.text_renderer.render_text(text=title_text, font_size=14, color=(255, 215, 0, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
            title_x = MARGIN + (FORMATION_WIDTH - title_img.width) // 2
            game_img.paste(title_img, (title_x, MARGIN - 15), title_img)

            title_text = "YOUR SQUAD"
            title_img = self.text_renderer.render_text(text=title_text, font_size=14, color=(255, 215, 0, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
            title_x = FORMATION_WIDTH + 2 * MARGIN + (grid_width - title_img.width) // 2
            game_img.paste(title_img, (title_x, MARGIN - 15), title_img)

        positions_with_coords = []
        slot_id = 1
        for row_idx, line in enumerate(grid):
            y = MARGIN + row_idx * (PLAYER_HEIGHT + PADDING)
            line_width = len(line) * (PLAYER_WIDTH + PADDING) - PADDING
            x_start = FORMATION_WIDTH + 2 * MARGIN + (grid_width - line_width) // 2
            row_positions = []
            for col_idx, position in enumerate(line):
                x = x_start + col_idx * (PLAYER_WIDTH + PADDING)
                row_positions.append(({'slot': slot_id, 'pos': position}, (x, y)))
                slot_id += 1
            positions_with_coords.append(row_positions)

        self.draw_connection_lines(draw, positions_with_coords, team.players, collection)

        slot_id = 1
        for row_idx, line in enumerate(grid):
            y = MARGIN + row_idx * (PLAYER_HEIGHT + PADDING)
            line_width = len(line) * (PLAYER_WIDTH + PADDING) - PADDING
            x_start = FORMATION_WIDTH + 2 * MARGIN + (grid_width - line_width) // 2
            for col_idx, position in enumerate(line):
                x = x_start + col_idx * (PLAYER_WIDTH + PADDING)
                card_id = team.get_player_at_slot(slot_id)
                player = collection.get_card(card_id) if card_id else None

                if player:
                    try:
                        player_img = Image.open(player.image_path).convert('RGBA')
                        player_img = player_img.resize((PLAYER_WIDTH, PLAYER_HEIGHT))
                        game_img.paste(player_img, (x, y), player_img)

                        if self.text_renderer:
                            id_text = f"id {player.id}"
                            id_img = self.text_renderer.render_text(text=id_text, font_size=8, color=(255, 255, 255, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
                            game_img.paste(id_img, (x + 2, y + 2), id_img)
                            rating_text = str(player.rating)
                            rating_img = self.text_renderer.render_text(text=rating_text, font_size=10, color=(255, 215, 0, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
                            rx = x + (PLAYER_WIDTH - rating_img.width) // 2
                            ry = y + PLAYER_HEIGHT - 15
                            game_img.paste(rating_img, (rx, ry), rating_img)
                    except Exception as e:
                        logger.error(f"[FIFA] Error loading player image: {e}")
                        draw.rectangle([x, y, x + PLAYER_WIDTH, y + PLAYER_HEIGHT], fill=(50, 100, 150), outline=(255, 215, 0), width=2)
                else:
                    draw.rectangle([x, y, x + PLAYER_WIDTH, y + PLAYER_HEIGHT], fill=(40, 40, 50), outline=(100, 100, 120), width=1)
                    if self.text_renderer:
                        slot_text = str(slot_id)
                        slot_img = self.text_renderer.render_text(text=slot_text, font_size=8, color=(150, 150, 150))
                        game_img.paste(slot_img, (x + 2, y + 2), slot_img)
                        pos_text = position
                        pos_img = self.text_renderer.render_text(text=pos_text, font_size=8, color=(255, 215, 0))
                        px = x + (PLAYER_WIDTH - pos_img.width) // 2
                        py = y + PLAYER_HEIGHT - 15
                        game_img.paste(pos_img, (px, py), pos_img)
                slot_id += 1

        self._add_fifa_coins_display(game_img, draw, game_width, game_height, fifa_coins)


        self._add_team_command_info(game_img, draw, game_width, game_height)

        game_img.save(output_path, format='PNG')
        return output_path

    def generate_match_preview_image(self, user_team, user_formation, user_collection, opponent, opponent_formation, output_path, fifa_coins=0, cache=None, user_id=None, opponent_logo=None):
        width = 1200
        height = 700

        img = Image.new('RGBA', (width, height), (27, 36, 38, 255))
        draw = ImageDraw.Draw(img)

        left_x = 50
        right_x = width // 2 + 50
        team_width = width // 2 - 100

        if self.text_renderer:
            header_text = "MATCH PREVIEW"
            header_img = self.text_renderer.render_text(text=header_text, font_size=32, color=(255, 215, 0, 255), stroke_width=2, stroke_color=(0, 0, 0, 255))
            x = (width - header_img.width) // 2
            y = 20
            img.paste(header_img, (x, y), header_img)

            vs_text = "VS"
            vs_img = self.text_renderer.render_text(text=vs_text, font_size=48, color=(255, 100, 100, 255), stroke_width=2, stroke_color=(0, 0, 0, 255))
            x = (width - vs_img.width) // 2
            y = height // 2 - 50
            img.paste(vs_img, (x, y), vs_img)

        user_avatar = None
        if cache and user_id:
            user_avatar = cache.get_avatar_path(user_id)

        self._draw_team_preview_with_chemistry(img, draw, left_x, 100, team_width, "YOUR TEAM", user_team, user_formation, user_collection, is_user=True, avatar_path=user_avatar)
        self._draw_team_preview_with_chemistry(img, draw, right_x, 100, team_width, opponent['name'].upper(), opponent['team'], opponent_formation, None, is_user=False, avatar_path=opponent_logo)

        self._draw_match_stats(img, draw, width, height)
        self._add_fifa_coins_display(img, draw, width, height, fifa_coins)

        img.save(output_path, format='PNG')
        return output_path

    def _draw_team_preview_with_chemistry(self, img, draw, x, y, width, team_name, team, formation, collection, is_user, avatar_path=None):
        CARD_WIDTH = 55
        CARD_HEIGHT = 65
        CARD_PADDING = 3
        START_Y = y + 80

        if avatar_path and os.path.exists(avatar_path):
            try:
                avatar_img = Image.open(avatar_path).convert('RGBA')
                avatar_size = 50
                avatar_img = avatar_img.resize((avatar_size, avatar_size))
                avatar_x = x + (width - avatar_size) // 2
                avatar_y = y - 5
                img.paste(avatar_img, (avatar_x, avatar_y), avatar_img)
            except Exception as e:
                logger.error(f"[FIFA] Error loading avatar: {e}")

        if self.text_renderer:
            name_img = self.text_renderer.render_text(text=team_name, font_size=24, color=(255, 215, 0, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
            name_x = x + (width - name_img.width) // 2
            img.paste(name_img, (name_x, y + 40), name_img)

            formation_name = formation['display_name'] if isinstance(formation, dict) else formation.display_name
            form_img = self.text_renderer.render_text(text=formation_name, font_size=16, color=(200, 200, 200, 255))
            form_x = x + (width - form_img.width) // 2
            img.paste(form_img, (form_x, y + 70), form_img)

        if isinstance(formation, dict):
            grid = formation.get('grid', [])
        else:
            grid = formation.get_position_grid()

        players_by_slot = {}
        if is_user and collection:
            slot_id = 1
            for line in grid:
                for pos in line:
                    card_id = team.get_player_at_slot(slot_id)
                    if card_id:
                        card = collection.get_card(card_id)
                        if card:
                            players_by_slot[slot_id] = card
                    slot_id += 1
        else:

            slot_id = 1
            for line in grid:
                for pos in line:

                    if hasattr(team, 'players'):
                        if slot_id - 1 < len(team.players):

                            card_id = team.get_player_at_slot(slot_id)
                            if card_id and collection:
                                card = collection.get_card(card_id)
                                if card:
                                    players_by_slot[slot_id] = card
                    else:
                        if slot_id - 1 < len(team):
                            players_by_slot[slot_id] = team[slot_id - 1]
                    slot_id += 1

        card_positions = {}
        slot_id = 1
        num_rows = len(grid)

        for row_idx, line in enumerate(grid):
            line_width = len(line) * (CARD_WIDTH + CARD_PADDING) - CARD_PADDING
            row_x = x + (width - line_width) // 2

            if num_rows <= 4:
                row_y = START_Y + row_idx * (CARD_HEIGHT + CARD_PADDING + 15)
            else:
                row_y = START_Y + row_idx * (CARD_HEIGHT + CARD_PADDING + 8)

            for col_idx, position in enumerate(line):
                card_x = row_x + col_idx * (CARD_WIDTH + CARD_PADDING)
                card_y = row_y

                player = players_by_slot.get(slot_id)

                card_center = (card_x + CARD_WIDTH // 2, card_y + CARD_HEIGHT // 2)
                card_positions[slot_id] = {
                    'center': card_center,
                    'position': position,
                    'player': player,
                    'x': card_x,
                    'y': card_y,
                    'row': row_idx,
                    'col': col_idx,
                    'line': line
                }

                slot_id += 1


        if is_user and collection:
            self._draw_preview_chemistry_lines(draw, card_positions, team, collection, grid, is_user=True)
        else:
            self._draw_preview_chemistry_lines(draw, card_positions, team, None, grid, is_user=False)


        slot_id = 1
        for row_idx, line in enumerate(grid):
            line_width = len(line) * (CARD_WIDTH + CARD_PADDING) - CARD_PADDING
            row_x = x + (width - line_width) // 2

            if num_rows <= 4:
                row_y = START_Y + row_idx * (CARD_HEIGHT + CARD_PADDING + 15)
            else:
                row_y = START_Y + row_idx * (CARD_HEIGHT + CARD_PADDING + 8)

            for col_idx, position in enumerate(line):
                card_x = row_x + col_idx * (CARD_WIDTH + CARD_PADDING)
                card_y = row_y

                player = players_by_slot.get(slot_id)

                if player and hasattr(player, 'image_path') and player.image_path and os.path.exists(player.image_path):
                    try:
                        card_img = Image.open(player.image_path).convert('RGBA')
                        card_img = card_img.resize((CARD_WIDTH, CARD_HEIGHT))
                        img.paste(card_img, (card_x, card_y), card_img)

                        if self.text_renderer:
                            rating_text = str(player.rating)
                            rating_img = self.text_renderer.render_text(text=rating_text, font_size=9, color=(255, 215, 0, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))
                            rx = card_x + (CARD_WIDTH - rating_img.width) // 2
                            ry = card_y + CARD_HEIGHT - 12
                            img.paste(rating_img, (rx, ry), rating_img)

                            if hasattr(player, 'id') and player.id:
                                id_text = str(player.id)
                                id_img = self.text_renderer.render_text(text=id_text, font_size=7, color=(200, 200, 200, 200))
                                img.paste(id_img, (card_x + 2, card_y + 2), id_img)
                    except Exception as e:
                        draw.rectangle([card_x, card_y, card_x + CARD_WIDTH, card_y + CARD_HEIGHT], fill=(50, 50, 60), outline=(100, 100, 120))
                        if self.text_renderer:
                            pos_text = position
                            pos_img = self.text_renderer.render_text(text=pos_text, font_size=8, color=(200, 200, 200))
                            px = card_x + (CARD_WIDTH - pos_img.width) // 2
                            py = card_y + CARD_HEIGHT - 12
                            img.paste(pos_img, (px, py), pos_img)
                else:
                    draw.rectangle([card_x, card_y, card_x + CARD_WIDTH, card_y + CARD_HEIGHT], fill=(40, 40, 50), outline=(100, 100, 120), width=1)
                    if self.text_renderer:
                        slot_text = str(slot_id)
                        slot_img = self.text_renderer.render_text(text=slot_text, font_size=8, color=(150, 150, 150))
                        img.paste(slot_img, (card_x + 2, card_y + 2), slot_img)
                        pos_text = position
                        pos_img = self.text_renderer.render_text(text=pos_text, font_size=8, color=(255, 215, 0))
                        px = card_x + (CARD_WIDTH - pos_img.width) // 2
                        py = card_y + CARD_HEIGHT - 12
                        img.paste(pos_img, (px, py), pos_img)

                slot_id += 1

        return card_positions

    def _draw_preview_chemistry_lines(self, draw, card_positions, team, collection, grid, is_user=True):
        slot_grid = {}
        slot_id = 1
        for row_idx, line in enumerate(grid):
            for col_idx, position in enumerate(line):
                slot_grid[slot_id] = {'row': row_idx, 'col': col_idx, 'position': position}
                slot_id += 1

        def get_w(pos):
            w = {'GK':1, 'CB':1, 'CDM':1, 'CM':1, 'CAM':1, 'ST':1, 'CF':1,
                 'LB':0, 'LWB':0, 'LM':0, 'LW':0, 'RB':2, 'RWB':2, 'RM':2, 'RW':2}
            return w.get(pos, 1)

        for slot_a, info_a in slot_grid.items():
            for slot_b, info_b in slot_grid.items():
                if slot_a >= slot_b: continue

                row_diff = abs(info_b['row'] - info_a['row'])
                col_diff = abs(info_b['col'] - info_a['col'])
                pos_a, pos_b = info_a['position'], info_b['position']

                is_connected = False
                if row_diff == 0 and col_diff == 1: is_connected = True
                elif row_diff == 1:
                    if col_diff <= 1 and abs(get_w(pos_a) - get_w(pos_b)) <= 1: is_connected = True
                    elif col_diff <= 2 and ({'CDM', 'CB'} <= {pos_a, pos_b} or {'CM', 'CB'} <= {pos_a, pos_b}): is_connected = True
                if not is_connected and row_diff <= 2 and {'GK', 'CB'} <= {pos_a, pos_b}: is_connected = True

                if is_connected:
                    card_a, card_b = None, None


                    if hasattr(team, 'get_player_at_slot') and collection is not None:

                        card_a = collection.get_card(team.get_player_at_slot(slot_a))
                        card_b = collection.get_card(team.get_player_at_slot(slot_b))
                    elif isinstance(team, list):

                        card_a = team[slot_a-1] if slot_a-1 < len(team) else None
                        card_b = team[slot_b-1] if slot_b-1 < len(team) else None


                    if card_a and card_b:
                        chemistry = self.calculate_chemistry(card_a, card_b)
                        color = self.get_link_color(chemistry)
                        c_a = card_positions.get(slot_a, {}).get('center')
                        c_b = card_positions.get(slot_b, {}).get('center')

                        if c_a and c_b:
                            draw.line([c_a, c_b], fill=color, width=2)
                            mid_x, mid_y = (c_a[0] + c_b[0]) // 2, (c_a[1] + c_b[1]) // 2
                            draw.ellipse([mid_x-2, mid_y-2, mid_x+2, mid_y+2], fill=color)

    def _get_pos_weight(self, pos):
        weights = {
            'GK': 1,
            'CB': 1, 'CDM': 1, 'CM': 1, 'CAM': 1, 'ST': 1, 'CF': 1,
            'LB': 0, 'LWB': 0, 'LM': 0, 'LW': 0,
            'RB': 2, 'RWB': 2, 'RM': 2, 'RW': 2
        }
        return weights.get(pos, 1)

    def _is_linking_to_defense(self, pos_a, pos_b):
        defense = ['CB', 'LB', 'RB', 'LWB', 'RWB']
        midfield = ['CDM', 'CM']

        if (pos_a in midfield and pos_b in defense) or (pos_b in midfield and pos_a in defense):
            return True
        if (pos_a == 'GK' and pos_b == 'CB') or (pos_b == 'GK' and pos_a == 'CB'):
            return True
        return False

    def _is_center_back_connection(self, pos_a, pos_b):


        positions = [pos_a, pos_b]
        if 'CDM' in positions or 'CM' in positions:
            if 'CB' in positions:
                return True
        return False

    def _draw_match_stats(self, img, draw, width, height):
        if not self.match:
            return

        y = height - 150
        stats = [
            ("Overall Rating", f"{self.match.user_stats['overall']} vs {self.match.opponent_stats['overall']}"),
            ("Attack", f"{self.match.user_stats['attack']} vs {self.match.opponent_stats['attack']}"),
            ("Midfield", f"{self.match.user_stats['midfield']} vs {self.match.opponent_stats['midfield']}"),
            ("Defense", f"{self.match.user_stats['defense']} vs {self.match.opponent_stats['defense']}"),
            ("Chemistry", f"{self.match.user_stats['chemistry']}% vs {self.match.opponent_stats['chemistry']}%"),
            ("Position Fit", f"{self.match.user_stats['position_fit']}% vs {self.match.opponent_stats['position_fit']}%")
        ]

        if self.text_renderer:
            for i, (stat_name, stat_value) in enumerate(stats):
                stat_img = self.text_renderer.render_text(text=f"{stat_name}: {stat_value}", font_size=12, color=(200, 200, 200, 255))
                x = (width - stat_img.width) // 2
                img.paste(stat_img, (x, y + i * 20), stat_img)

    def generate_match_fragment_image(self, match, fragment, fragment_index, output_path, cache=None, user_id=None):
        width = 800
        base_height = 350
        event_height = 35
        footer_height = 100

        total_height = base_height + (len(fragment['events']) * event_height) + footer_height

        img = Image.new('RGBA', (width, total_height), (27, 36, 38, 255))
        draw = ImageDraw.Draw(img)

        current_score = f"{fragment.get('user_score', 0)} - {fragment.get('opponent_score', 0)}"

        if self.text_renderer:
            score_img = self.text_renderer.render_text(text=current_score, font_size=48, color=(255, 215, 0, 255), stroke_width=2, stroke_color=(0, 0, 0, 255))
            x = (width - score_img.width) // 2
            img.paste(score_img, (x, 20), score_img)

        avatar_y = 100
        if cache and user_id:
            user_avatar = cache.get_avatar_path(user_id)
            if user_avatar and os.path.exists(user_avatar):
                try:
                    avatar = Image.open(user_avatar).convert('RGBA').resize((50, 50))
                    img.paste(avatar, (50, avatar_y), avatar)
                except Exception as e:
                    logger.error(f"[FIFA] Error loading user avatar: {e}")


        if match.opponent_logo and os.path.exists(match.opponent_logo):
            try:
                logo = Image.open(match.opponent_logo).convert('RGBA').resize((50, 50))
                img.paste(logo, (width - 100, avatar_y), logo)
            except Exception as e:
                logger.error(f"[FIFA] Error loading opponent logo: {e}")

        if self.text_renderer:
            user_name = "YOUR TEAM"
            opponent_name = match.opponent['name'].upper()

            user_name_img = self.text_renderer.render_text(text=user_name, font_size=14, color=(255, 255, 255, 255))
            img.paste(user_name_img, (50, avatar_y + 55), user_name_img)

            opponent_name_img = self.text_renderer.render_text(text=opponent_name, font_size=14, color=(255, 255, 255, 255))
            img.paste(opponent_name_img, (width - opponent_name_img.width - 50, avatar_y + 55), opponent_name_img)

        y_offset = 200
        row_height = 35

        for idx, event in enumerate(fragment['events']):
            y = y_offset + idx * row_height

            minute_match = re.search(r'\[(\d+)\']', event)
            minute_text = f"{minute_match.group(1)}'" if minute_match else ""
            event_text = re.sub(r'\[\d+\'\]\s*', '', event)

            event_upper = event_text.upper()


            alignment = 'center'
            color = (255, 255, 255, 255)


            if 'YOUR TEAM' in event_upper or 'YOU' in event_upper or 'YOUR' in event_upper:
                alignment = 'left'
                color = (100, 255, 100, 255)

            elif match.opponent['name'].upper() in event_upper:
                alignment = 'right'
                color = (255, 100, 100, 255)
            else:

                alignment = 'center'
                color = (255, 255, 255, 255)

            self._draw_event_with_minute(img, draw, minute_text, event_text, y, alignment, color)

        footer_y = total_height - 80
        if self.text_renderer:
            current_time = f"Minute {fragment['minute']}'"
            time_img = self.text_renderer.render_text(text=current_time, font_size=14, color=(200, 200, 200, 255))
            x = (width - time_img.width) // 2
            img.paste(time_img, (x, footer_y), time_img)

        img.save(output_path, format='PNG')
        return output_path

    def _draw_event_with_minute(self, img, draw, minute_text, event_text, y, alignment, color):
        if not self.text_renderer:
            return


        if minute_text:
            full_text = f"{minute_text} {event_text}"
        else:
            full_text = event_text


        max_width = 500
        words = full_text.split(' ')
        lines = []
        current_line = ''

        for word in words:
            test_line = current_line + ' ' + word if current_line else word
            test_img = self.text_renderer.render_text(text=test_line, font_size=12, color=color)
            if test_img.width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        img_width = img.width


        icon_to_show = None


        event_lower = event_text.lower()


        if 'goal' in event_lower and 'opens the scoring' in event_lower:
            icon_to_show = 'goal'
        elif 'goal' in event_lower and 'doubles the lead' in event_lower:
            icon_to_show = 'goal'
        elif 'goal' in event_lower and 'pulls one back' in event_lower:
            icon_to_show = 'goal'
        elif 'goal' in event_lower and 'crucial goal' in event_lower:
            icon_to_show = 'goal'
        elif 'goal' in event_lower and 'late strike' in event_lower:
            icon_to_show = 'goal'


        elif 'yellow card' in event_lower:
            icon_to_show = 'yellow_card'
        elif 'red card' in event_lower:
            icon_to_show = 'red_card'


        elif 'shoots from distance' in event_lower or 'takes a shot' in event_lower or 'tries his luck' in event_lower:
            icon_to_show = 'shot'


        elif 'great save' in event_lower or 'goalkeeper positions' in event_lower or 'goalkeeper catches' in event_lower:
            icon_to_show = 'save'


        elif 'foul' in event_lower:
            icon_to_show = 'foul'


        elif 'corner' in event_lower:
            icon_to_show = 'corner'


        elif 'offside' in event_lower:
            icon_to_show = 'offside'


        elif 'is down after' in event_lower or 'medical staff' in event_lower or 'unable to continue' in event_lower:
            icon_to_show = 'injury'


        elif 'substitution' in event_lower or 'comes on for' in event_lower:
            icon_to_show = 'substitution'


        elif 'counter' in event_lower:
            icon_to_show = 'counter'

        for line_idx, line in enumerate(lines):
            line_y = y + (line_idx * 20)
            event_img = self.text_renderer.render_text(
                text=line,
                font_size=12,
                color=color,
                stroke_width=1,
                stroke_color=(0, 0, 0, 100)
            )


            if alignment == 'left':
                x = 80
            elif alignment == 'right':
                x = img_width - event_img.width - 80
            else:
                x = (img_width - event_img.width) // 2


            if x < 10:
                x = 10
            if x + event_img.width > img_width - 10:
                x = img_width - event_img.width - 10


            if line_idx == 0 and icon_to_show and icon_to_show in self.event_icons:
                icon = self.event_icons[icon_to_show]

                if alignment == 'left':
                    icon_x = x - 32
                    if icon_x < 5:
                        icon_x = x + 5
                elif alignment == 'right':
                    icon_x = x + event_img.width + 8
                    if icon_x + 24 > img_width - 5:
                        icon_x = x - 32
                else:
                    icon_x = x - 32
                    if icon_x < 5:
                        icon_x = x + event_img.width + 8

                img.paste(icon, (icon_x, line_y - 2), icon)


            img.paste(event_img, (x, line_y), event_img)

    def _get_event_type(self, event_text):
        event_lower = event_text.lower()


        if 'goal' in event_lower:
            return 'goal'


        elif 'yellow card' in event_lower:
            return 'yellow_card'
        elif 'red card' in event_lower:
            return 'red_card'


        elif 'offside' in event_lower:
            return 'offside'
        elif 'foul' in event_lower:
            return 'foul'
        elif 'penalty' in event_lower:
            return 'penalty'


        elif 'substitution' in event_lower:
            return 'substitution'
        elif 'injury' in event_lower:
            return 'injury'


        elif 'corner' in event_lower:
            return 'corner'
        elif 'shot' in event_lower:
            return 'shot'
        elif 'save' in event_lower:
            return 'save'


        elif 'counter' in event_lower:
            return 'counter'

        return None

    def _draw_event_with_icon(self, img, draw, event_text, x, y, alignment):
        event_type = self._get_event_type(event_text)

        if event_type and event_type in self.event_icons:
            icon = self.event_icons[event_type]
            img.paste(icon, (x, y - 2), icon)
            text_x = x + 30
        else:
            text_x = x

        if self.text_renderer:
            clean_text = re.sub(r'\[\d+\'\]\s*', '', event_text)
            event_img = self.text_renderer.render_text(
                text=clean_text,
                font_size=12,
                color=(220, 220, 220, 255)
            )

            if event_img.width > 250:
                words = clean_text.split(' ')
                lines = []
                current_line = ''
                for word in words:
                    test_line = current_line + ' ' + word if current_line else word
                    test_img = self.text_renderer.render_text(text=test_line, font_size=12, color=(220, 220, 220, 255))
                    if test_img.width <= 250:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)

                for line_idx, line in enumerate(lines):
                    line_img = self.text_renderer.render_text(text=line, font_size=12, color=(220, 220, 220, 255))
                    img.paste(line_img, (text_x, y + line_idx * 20), line_img)
            else:
                img.paste(event_img, (text_x, y), event_img)

class Match:
    def __init__(self, match_id, user_id, user_team, user_formation, user_collection, fifa_plugin):
        self.match_id = match_id
        self.user_id = user_id
        self.user_team = user_team
        self.user_formation = user_formation
        self.user_collection = user_collection
        self.fifa_plugin = fifa_plugin
        self.update_intervals = [15, 30, 45, 60, 75, 90]

        self.opponent = self._generate_real_opponent()
        self.opponent_formation = self._generate_opponent_formation()

        self.opponent_logo = self._select_opponent_logo()

        self.user_stats = self._calculate_advanced_team_stats(user_team, user_formation, user_collection, is_user=True)
        self.opponent_stats = self._calculate_advanced_team_stats(self.opponent['team'], self.opponent_formation, None, is_user=False)

        self.user_score = 0
        self.opponent_score = 0
        self.minute = 0
        self.events = []
        self.status = MatchStatus.WAITING
        self.match_script = []
        self.current_event_index = 0
        self.reward = self._calculate_reward()

        self.user_categories = self._categorize_stats(self.user_stats)
        self.opponent_categories = self._categorize_stats(self.opponent_stats)

    def _select_opponent_logo(self):

        if self.fifa_plugin.team_image_generator.opponent_logos_folder and os.path.exists(self.fifa_plugin.team_image_generator.opponent_logos_folder):
            logos = [f for f in os.listdir(self.fifa_plugin.team_image_generator.opponent_logos_folder) if f.endswith('.png')]
            if logos:
                return os.path.join(self.fifa_plugin.team_image_generator.opponent_logos_folder, random.choice(logos))


        if hasattr(self, 'player2_id') and self.player2_id and self.fifa_plugin.cache:
            avatar_path = self.fifa_plugin.cache.get_avatar_path(self.player2_id)
            if avatar_path and os.path.exists(avatar_path):
                return avatar_path

        return None

    def _categorize_stats(self, stats):
        return {
            'attack_power': 'strong' if stats['attack'] > 80 else 'medium' if stats['attack'] > 60 else 'weak',
            'midfield_control': 'strong' if stats['midfield'] > 80 else 'medium' if stats['midfield'] > 60 else 'weak',
            'defense_solidity': 'strong' if stats['defense'] > 80 else 'medium' if stats['defense'] > 60 else 'weak',
            'chemistry': 'perfect' if stats['chemistry'] > 85 else 'good' if stats['chemistry'] > 70 else 'poor',
            'positioning': 'perfect' if stats['position_fit'] > 85 else 'good' if stats['position_fit'] > 70 else 'poor',
            'overall': stats['overall']
        }

    def generate_match_script_with_6_fragments(self):
        self.match_script = []
        user_advantage = self._calculate_user_advantage()

        for i, minute in enumerate(self.update_intervals):
            is_final = (minute == 90)
            fragment = self._generate_match_fragment_advanced(minute, user_advantage, is_final)
            self.match_script.append(fragment)

        return self.match_script

    def _generate_real_opponent(self):
        all_cards = []
        for pack_type in ['bronze', 'silver', 'gold']:
            for category in ['normal', 'premium']:
                folder = os.path.join(self.fifa_plugin.cards_folder, pack_type, category)
                if os.path.exists(folder):
                    for filename in os.listdir(folder):
                        if filename.endswith('.png'):
                            filepath = os.path.join(folder, filename)
                            card = FifaCard(filename, filepath)
                            all_cards.append(card)

        team_rating = random.randint(60, 85)
        positions_needed = ['GK', 'CB', 'CB', 'LB', 'RB', 'CDM', 'CM', 'CM', 'CAM', 'ST', 'ST']

        team = []
        for pos in positions_needed:
            suitable_cards = [c for c in all_cards if c.position == pos and abs(c.rating - team_rating) <= 8]
            if not suitable_cards:
                suitable_cards = [c for c in all_cards if c.position == pos]
            if suitable_cards:
                card = random.choice(suitable_cards)
                team.append(card)
            else:
                team.append(self._create_fallback_card(pos, team_rating))

        prefixes = [
            "FC", "Real", "Atlético", "Sporting", "Racing", "United", "City", "Athletic",
            "Deportivo", "Internacional", "Young", "Old", "Rapid", "Dynamo", "Spartak",
            "Lokomotiv", "CSKA", "Steaua", "Crvena", "Slavia", "Legia", "Wisła", "Lech",
            "Śląsk", "Górnik", "Zagłębie", "AC", "AS", "SC", "SV", "FK", "NK", "OFK", "AFC", "BSC", "TSV",
            "Borussia", "Bayern", "Juventus", "Benfica", "Porto", "Ajax", "Feyenoord",
            "PSV", "Anderlecht", "Celtic", "Rangers", "Basel", "Lazio", "Roma", "Napoli",
            "Milan", "Inter", "Torino", "Sampdoria", "Monaco", "Lyon", "Marseille",
            "Valencia", "Sevilla", "Villarreal", "Betis", "Espanyol", "Osasuna",
            "Dinamo", "Partizan", "Red", "Blue", "White", "Black", "Royal", "Imperial",
            "Olympic", "Olympique", "Universidad", "Nacional", "Club", "Union", "Unión",
            "Estrella", "Estudiantes", "Libertad", "Defensor", "River", "Boca", "San",
            "Santa", "Monte", "Villa", "Real Club", "Club Atlético", "Sport Club",
            "Pogoń", "Korona", "Jagiellonia", "Warta", "Odra", "Motor", "Arka", "Radomiak",
            "Ruch", "Piast", "Stal", "Resovia", "Sandecja", "Polonia", "Raków", "Chrobry",
            "Miedź", "Kotwica", "Błękitni", "Hutnik", "Chemik", "Sokół", "Orzeł", "Unia",
            "Victoria", "Concordia", "Iskra", "Znicz", "Spójnia", "Puszcza", "Noteć",
            "Iron", "Golden", "Silver", "Crimson", "Shadow", "Storm", "Thunder", "Fire",
            "Ice", "Wolf", "Eagle", "Falcon", "Titan", "Phoenix", "Dragon", "Vortex",
            "Galaxy", "Nova", "Blaze", "Inferno", "Glory", "Victory", "Legends"
        ]

        suffixes = [
            "United", "City", "FC", "Rovers", "Wanderers", "Athletic", "Academy", "Stars",
            "Legends", "Warriors", "Eagles", "Lions", "Tigers", "Dragons", "Phoenix",
            "Thunder", "Storm", "Hurricanes", "Tornado", "Cyclones", "CF", "SC", "AC", "BK", "SK", "FK", "IF", "Club", "Sporting", "Athletico",
            "Town", "Albion", "County", "Villa", "Hotspur", "Olympic", "Olympians",
            "Boys", "Juniors", "Seniors", "Reserves", "Academia", "Union", "Unión",
            "Deportivo", "Nacional", "Internacional", "Atletico", "Calcio", "Breda",
            "Dons", "Rangers", "Saints", "Giants", "Titans", "Royals", "Kings", "Knights",
            "Guardians", "Strikers", "Blazers", "Raiders", "Falcons", "Wolves", "Bulls",
            "Sharks", "Panthers", "Cobras", "Spartans", "Gladiators", "Comets", "Meteors",
            "Galaxy", "Cosmos", "United FC", "City FC", "Sport Club", "Football Club",
            "Kraków", "Warszawa", "Poznań", "Wrocław", "Gdańsk", "Łódź", "Lublin",
            "Szczecin", "Katowice", "Bytom", "Zabrze", "Gdynia", "Białystok", "Rzeszów",
            "Opole", "Kielce", "Radom", "Płock", "Legionowo", "Tarnów", "Nowy Sącz",
            "Bielsko", "Tychy", "Elbląg", "Siedlce", "Force", "Squad", "Elite", "Masters", "Dynasty", "Rebels", "Invincibles",
            "Champions", "Stormers", "Thunderbolts", "Firebirds", "Skyhawks", "Ironclads",
            "Red Devils", "White Wolves", "Black Eagles", "Golden Lions", "Silver Foxes",
            "Blue Sharks", "Crimson Kings", "Night Riders", "Solaris", "Vanguard"
        ]

        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        team_name = f"{prefix} {suffix}"

        return {'name': team_name, 'rating': team_rating, 'team': team, 'formation': None}

    def _create_fallback_card(self, position, rating):
        class FakeCard:
            def __init__(self, pos, rat):
                self.player_name = f"Generic {pos}"
                self.rating = rat
                self.position = pos
                self.pac = random.randint(50, 80)
                self.sho = random.randint(50, 80)
                self.pas = random.randint(50, 80)
                self.dri = random.randint(50, 80)
                self.defense = random.randint(50, 80)
                self.phy = random.randint(50, 80)
                self.club = random.randint(1, 1000)
                self.league = random.randint(1, 100)
                self.flag = random.randint(1, 200)
                self.price = rating * 10
                self.image_path = None
        return FakeCard(position, rating)

    def _generate_opponent_formation(self):
        formations = self.fifa_plugin.formation_manager.formations
        if formations:
            formation = random.choice(formations)
            return {'id': formation.id, 'name': formation.name, 'display_name': formation.display_name, 'grid': formation.get_position_grid()}
        return {'id': 0, 'name': '442', 'display_name': '4-4-2', 'grid': [['ST', 'ST'], ['LM', 'CM', 'CM', 'RM'], ['LB', 'CB', 'CB', 'RB'], ['GK']]}

    def _calculate_advanced_team_stats(self, team, formation, collection, is_user=True):
        stats = {
            'overall': 0,
            'attack': 0,
            'midfield': 0,
            'defense': 0,
            'chemistry': 0,
            'position_fit': 0,
            'players': [],
            'weaknesses': [],
            'strengths': []
        }
        players = []
        position_slots = {}

        if is_user and collection:
            slot_id = 1
            if hasattr(formation, 'get_position_grid'):
                position_grid = formation.get_position_grid()
            else:
                position_grid = formation.get('grid', [])

            for line in position_grid:
                for pos in line:
                    card_id = team.get_player_at_slot(slot_id)
                    if card_id:
                        card = collection.get_card(card_id)
                        if card:
                            players.append(card)
                            position_slots[card.id] = pos
                    slot_id += 1
        else:
            players = team
            slot_id = 0

            if isinstance(formation, dict):
                formation_grid = formation.get('grid', [])
            else:
                formation_grid = formation.get_position_grid() if hasattr(formation, 'get_position_grid') else []

            for line in formation_grid:
                for pos in line:
                    if slot_id < len(players):
                        player = players[slot_id]
                        position_slots[slot_id] = pos
                    slot_id += 1

        if not players:
            stats['overall'] = 70
            stats['attack'] = 70
            stats['midfield'] = 70
            stats['defense'] = 70
            stats['chemistry'] = 70
            stats['position_fit'] = 70
            return stats

        total_rating = sum(p.rating for p in players)
        stats['overall'] = total_rating // len(players)

        attack_contrib = 0
        midfield_contrib = 0
        defense_contrib = 0
        attack_weight = 0
        midfield_weight = 0
        defense_weight = 0
        position_fit_total = 0

        for idx, player in enumerate(players):
            if is_user:
                assigned_pos = position_slots.get(player.id, 'Unknown')
            else:
                assigned_pos = position_slots.get(idx, 'Unknown')

            position_fit = self._calculate_position_fit(player.position, assigned_pos)
            position_fit_total += position_fit

            if assigned_pos in ['ST', 'CF', 'LW', 'RW']:
                attack_val = (player.sho * 0.4 + player.pac * 0.3 + player.dri * 0.2 + player.pas * 0.1) * (0.8 + position_fit * 0.4)
                attack_contrib += attack_val
                attack_weight += 1
            elif assigned_pos in ['CAM', 'CM', 'CDM', 'LM', 'RM']:
                midfield_val = (player.pas * 0.35 + player.dri * 0.25 + player.sho * 0.2 + player.defense * 0.2) * (0.8 + position_fit * 0.4)
                midfield_contrib += midfield_val
                midfield_weight += 1
            elif assigned_pos in ['CB', 'LB', 'RB', 'LWB', 'RWB']:
                defense_val = (player.defense * 0.45 + player.phy * 0.3 + player.pac * 0.15 + player.pas * 0.1) * (0.8 + position_fit * 0.4)
                defense_contrib += defense_val
                defense_weight += 1
            elif assigned_pos == 'GK':
                defense_val = (player.dri * 0.4 + player.defense * 0.3 + player.phy * 0.2 + player.pas * 0.1) * (0.8 + position_fit * 0.4)
                defense_contrib += defense_val
                defense_weight += 1

        if attack_weight > 0:
            stats['attack'] = int(attack_contrib / attack_weight)
        else:
            stats['attack'] = 50

        if midfield_weight > 0:
            stats['midfield'] = int(midfield_contrib / midfield_weight)
        else:
            stats['midfield'] = 50

        if defense_weight > 0:
            stats['defense'] = int(defense_contrib / defense_weight)
        else:
            stats['defense'] = 50

        stats['position_fit'] = int((position_fit_total / len(players)) * 100) if players else 0

        chemistry = 0
        total_links = 0
        for i, p1 in enumerate(players):
            for p2 in players[i+1:]:
                link_value = 0
                if p1.club and p2.club and p1.club == p2.club:
                    link_value = 3
                elif p1.league and p2.league and p1.league == p2.league:
                    link_value = 2
                elif p1.flag and p2.flag and p1.flag == p2.flag:
                    link_value = 1
                if link_value > 0:
                    chemistry += link_value
                    total_links += 1

        if total_links > 0:
            stats['chemistry'] = min(100, int((chemistry / (total_links * 3)) * 100))
        else:
            stats['chemistry'] = 50

        if stats['attack'] < 60:
            stats['weaknesses'].append("Low attacking power")
        elif stats['attack'] > 80:
            stats['strengths'].append("Strong attack")
        if stats['midfield'] < 60:
            stats['weaknesses'].append("Weak midfield control")
        elif stats['midfield'] > 80:
            stats['strengths'].append("Dominant midfield")
        if stats['defense'] < 60:
            stats['weaknesses'].append("Vulnerable defense")
        elif stats['defense'] > 80:
            stats['strengths'].append("Solid defense")
        if stats['position_fit'] < 70:
            stats['weaknesses'].append("Players out of position")
        elif stats['position_fit'] > 85:
            stats['strengths'].append("Perfect positioning")

        return stats

    def _calculate_position_fit(self, player_pos, assigned_pos):
        if player_pos == assigned_pos:
            return 1.0

        position_mapping = {
            'ST': ['CF', 'LW', 'RW'],
            'CF': ['ST', 'CAM'],
            'LW': ['LM', 'ST'],
            'RW': ['RM', 'ST'],
            'CAM': ['CM', 'CF'],
            'CM': ['CAM', 'CDM'],
            'CDM': ['CM', 'CB'],
            'LM': ['LW', 'CM'],
            'RM': ['RW', 'CM'],
            'CB': ['CDM', 'LB', 'RB'],
            'LB': ['LWB', 'CB'],
            'RB': ['RWB', 'CB'],
            'GK': []
        }

        if assigned_pos in position_mapping.get(player_pos, []):
            return 0.7

        zones = {
            'attack': ['ST', 'CF', 'LW', 'RW'],
            'midfield': ['CAM', 'CM', 'CDM', 'LM', 'RM'],
            'defense': ['CB', 'LB', 'RB', 'LWB', 'RWB'],
            'gk': ['GK']
        }

        player_zone = None
        assigned_zone = None
        for zone, positions in zones.items():
            if player_pos in positions:
                player_zone = zone
            if assigned_pos in positions:
                assigned_zone = zone

        if player_zone == assigned_zone and player_zone != 'gk':
            return 0.5
        return 0.2

    def _calculate_reward(self):
        avg_rating = self.user_stats['overall']
        opponent_rating = self.opponent_stats['overall']

        base_reward = 500 + ((avg_rating - 50) / 40) * 4500

        difficulty_mult = max(0.8, min(1.2, 1 + ((opponent_rating - avg_rating) / 100)))
        chemistry_mult = max(0.8, min(1.2, 0.8 + (self.user_stats['chemistry'] / 250)))
        position_mult = max(0.7, min(1.1, 0.7 + (self.user_stats['position_fit'] / 200)))

        base_total = int(base_reward * difficulty_mult * chemistry_mult * position_mult)

        return base_total

    def _generate_match_fragment_advanced(self, minute, user_advantage, is_final):
        events = []


        start_user_score = self.user_score
        start_opponent_score = self.opponent_score

        intensity_mult = 1.0
        if self.user_categories['attack_power'] == 'strong':
            intensity_mult += 0.3
        if self.opponent_categories['attack_power'] == 'strong':
            intensity_mult += 0.3

        base_events = random.randint(4, 8)
        if minute >= 75:
            base_events += 2
        num_events = int(base_events * intensity_mult)

        previous_minute = minute - 14
        used_minutes = set()

        for i in range(num_events):
            minute_offset = random.randint(0, 14)
            event_minute = minute - 14 + minute_offset

            while event_minute in used_minutes or event_minute > minute or event_minute < previous_minute:
                minute_offset = random.randint(0, 14)
                event_minute = minute - 14 + minute_offset

            used_minutes.add(event_minute)

            team = self._determine_team_for_action(user_advantage)
            event = self._generate_stat_based_event(team, event_minute, include_minute=False)
            if event:
                events.append((event_minute, event))


        events.sort(key=lambda x: x[0])


        clean_events = [f"[{minute_val}] {event_text}" for minute_val, event_text in events]


        if minute == 45:
            clean_events.append(f"[45'] HALF TIME")
            if self.user_score > self.opponent_score:
                clean_events.append(f"[45'] Leading at half time!")
            elif self.user_score < self.opponent_score:
                clean_events.append(f"[45'] Trailing at half time - need to improve!")
            else:
                clean_events.append(f"[45'] All to play for in the second half!")
        elif minute == 90:
            clean_events.append(f"[90'] FULL TIME")


        end_user_score = self.user_score
        end_opponent_score = self.opponent_score

        summary = self._generate_detailed_summary(minute, is_final)

        return {
            'minute': minute,
            'events': clean_events,
            'summary': summary,
            'is_final': is_final,
            'user_score': end_user_score,
            'opponent_score': end_opponent_score
        }

    def _determine_team_for_action(self, user_advantage):
        return 'user' if random.random() * 100 < user_advantage else 'opponent'

    def _generate_stat_based_event(self, team, minute, include_minute=True):
        stats = self.user_stats if team == 'user' else self.opponent_stats
        categories = self.user_categories if team == 'user' else self.opponent_categories

        event_type = self._select_event_by_stats(stats, categories, minute)

        if event_type == 'goal':
            return self._generate_goal_event(team, stats, categories, minute, include_minute)
        elif event_type == 'yellow_card':
            return self._generate_yellow_card_event(team, minute, include_minute)
        elif event_type == 'red_card':
            return self._generate_red_card_event(team, minute, include_minute)
        elif event_type == 'shot':
            return self._generate_shot_event(team, stats, categories, minute, include_minute)
        elif event_type == 'save':
            return self._generate_save_event(team, stats, categories, minute, include_minute)
        elif event_type == 'tackle':
            return self._generate_tackle_event(team, stats, categories, minute, include_minute)
        elif event_type == 'foul':
            return self._generate_foul_event(team, stats, categories, minute, include_minute)
        elif event_type == 'corner':
            return self._generate_corner_event(team, stats, categories, minute, include_minute)
        elif event_type == 'offside':
            return self._generate_offside_event(team, stats, categories, minute, include_minute)
        elif event_type == 'injury':
            return self._generate_injury_event(team, stats, categories, minute, include_minute)
        elif event_type == 'counter':
            return self._generate_counter_attack_event(team, stats, categories, minute, include_minute)

        return self._generate_pass_event(team, stats, categories, minute, include_minute)

    def _select_event_by_stats(self, stats, categories, minute):
        weights = {
            'pass': 20, 'tackle': 15, 'shot': 10, 'foul': 10,
            'corner': 8, 'offside': 5, 'save': 5, 'goal': 5,
            'injury': 3, 'yellow_card': 2, 'red_card': 1
        }

        if stats['attack'] > 80:
            weights['shot'] += 10
            weights['goal'] += 5
        elif stats['attack'] < 60:
            weights['shot'] -= 5
            weights['pass'] += 5

        if stats['midfield'] > 80:
            weights['pass'] += 10
        elif stats['midfield'] < 60:
            weights['pass'] -= 5
            weights['tackle'] += 5

        if stats['defense'] > 80:
            weights['tackle'] += 10
            weights['save'] += 5
        elif stats['defense'] < 60:
            weights['tackle'] -= 5
            weights['foul'] += 5

        if minute > 75:
            weights['shot'] += 10
            weights['goal'] += 5

        total_weight = sum(weights.values())
        rand = random.randint(1, total_weight)

        cumulative = 0
        for event, weight in weights.items():
            cumulative += weight
            if rand <= cumulative:
                return event

        return 'pass'

    def _generate_goal_event(self, team, stats, categories, minute, include_minute=True):
        team_name = self._get_team_name(team)
        player = self._get_random_player(team)

        if team == 'user':
            self.user_score += 1
        else:
            self.opponent_score += 1

        score = f"{self.user_score}-{self.opponent_score}"

        if minute < 30:
            descriptions = [
                f"GOAL! {player} opens the scoring! ({score})",
                f"What a start! {player} scores for {team_name}! ({score})"
            ]
        elif minute < 60:
            descriptions = [
                f"GOAL! {player} doubles the lead! ({score})",
                f"{player} pulls one back! ({score})"
            ]
        else:
            descriptions = [
                f"GOAL! {player} scores a crucial goal! ({score})",
                f"{player} with a late strike! ({score})"
            ]

        if random.random() < 0.6:
            assistant = self._get_random_player(team)
            while assistant == player:
                assistant = self._get_random_player(team)
            description = random.choice(descriptions)
            event_text = f"{description} (Assist: {assistant})"
        else:
            event_text = random.choice(descriptions)

        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_yellow_card_event(self, team, minute, include_minute=True):
        player = self._get_random_player(team)
        team_name = self._get_team_name(team)

        descriptions = [
            f"Yellow card for {player} ({team_name}) - tactical foul.",
            f"{player} ({team_name}) goes into the book.",
            f"Late challenge by {player} ({team_name}) - yellow card."
        ]

        event_text = random.choice(descriptions)

        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_red_card_event(self, team, minute, include_minute=True):
        player = self._get_random_player(team)
        team_name = self._get_team_name(team)

        if team == 'user':
            descriptions = [
                f"RED CARD! {player} is sent off! Your team down to 10 players!",
                f"Disastrous! {player} sees red for a dangerous tackle!"
            ]
        else:
            descriptions = [
                f"RED CARD! {player} ({team_name}) is sent off! Advantage for YOUR TEAM!",
                f"{player} ({team_name}) receives a marching order!"
            ]

        event_text = random.choice(descriptions)

        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_shot_event(self, team, stats, categories, minute, include_minute=True):
        team_name = self._get_team_name(team)
        player = self._get_random_player(team)

        if minute > 85:
            descriptions = [
                f"{player} ({team_name}) shoots from distance - just wide!",
                f"{player} ({team_name}) with a late effort!"
            ]
        else:
            descriptions = [
                f"{player} ({team_name}) takes a shot - saved by the keeper!",
                f"{player} ({team_name}) tries his luck from outside the box!"
            ]

        event_text = random.choice(descriptions)

        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_save_event(self, team, stats, categories, minute, include_minute=True):
        team_name = self._get_team_name(team)

        descriptions = [
            f"Great save by {team_name} goalkeeper!",
            f"{team_name} goalkeeper positions well to make the save.",
            f"{team_name} goalkeeper catches the ball comfortably."
        ]

        event_text = random.choice(descriptions)

        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_tackle_event(self, team, stats, categories, minute, include_minute=True):
        team_name = self._get_team_name(team)
        player = self._get_random_player(team)

        descriptions = [
            f"{player} ({team_name}) makes a solid tackle.",
            f"{player} ({team_name}) wins the ball back for {team_name}.",
            f"Good defensive work by {player} ({team_name})."
        ]

        event_text = random.choice(descriptions)

        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_foul_event(self, team, stats, categories, minute, include_minute=True):
        player = self._get_random_player(team)
        team_name = self._get_team_name(team)

        descriptions = [
            f"Foul by {player} ({team_name})! Free kick in a dangerous position.",
            f"{player} ({team_name}) brings down an opponent - free kick.",
            f"Tactical foul by {player} ({team_name}) - referee plays advantage."
        ]

        event_text = random.choice(descriptions)

        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_corner_event(self, team, stats, categories, minute, include_minute=True):
        team_name = self._get_team_name(team)

        descriptions = [
            f"Corner kick for {team_name}.",
            f"{team_name} wins a corner - chance to score!",
            f"Set piece opportunity for {team_name} from the corner."
        ]

        event_text = random.choice(descriptions)

        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_offside_event(self, team, stats, categories, minute, include_minute=True):
        team_name = self._get_team_name(team)
        player = self._get_random_player(team)

        descriptions = [
            f"Offside! {player} ({team_name}) mistimed his run.",
            f"{player} ({team_name}) caught in the offside trap.",
            f"Linesman raises the flag - offside against {team_name}."
        ]

        event_text = random.choice(descriptions)

        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_injury_event(self, team, stats, categories, minute, include_minute=True):
        team_name = self._get_team_name(team)
        player = self._get_random_player(team)

        descriptions = [
            f"{player} ({team_name}) is down after that challenge.",
            f"Medical staff rushing onto the pitch for {player} ({team_name}).",
            f"{player} ({team_name}) seems unable to continue."
        ]

        event_text = random.choice(descriptions)

        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_pass_event(self, team, stats, categories, minute, include_minute=True):
        team_name = self._get_team_name(team)
        player = self._get_random_player(team)

        descriptions = [
            f"{team_name} controls possession through {player}.",
            f"Patient build-up play by {team_name}.",
            f"{player} ({team_name}) distributes the ball well."
        ]

        event_text = random.choice(descriptions)

        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_counter_attack_event(self, team, stats, categories, minute, include_minute=True):
        team_name = self._get_team_name(team)

        descriptions = [
            f"{team_name} tries to counter but the defense recovers.",
            f"{team_name} counter-attack is slowed down by good defending.",
            f"{team_name} breaks forward but the chance is gone."
        ]

        event_text = random.choice(descriptions)

        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_detailed_summary(self, minute, is_final):
        if is_final:
            base_reward = self.reward

            if self.user_score > self.opponent_score:
                final_reward = base_reward
                reward_percent = "100%"
                win_text = "VICTORY!"
            elif self.user_score < self.opponent_score:
                final_reward = int(base_reward * 0.1)
                if final_reward < 10:
                    final_reward = 10
                reward_percent = "10%"
                win_text = "DEFEAT!"
            else:
                final_reward = int(base_reward * 0.5)
                reward_percent = "50%"
                win_text = "DRAW!"


            if self.user_score > self.opponent_score:
                summary = f"YOU WON!\n\n"
                summary += f"Final score: {self.user_score} - {self.opponent_score}\n"
                summary += f"You earned: +{final_reward} FIFA coins\n"
                summary += f"(Reward: {reward_percent} of base reward)"
            elif self.user_score < self.opponent_score:
                summary = f"YOU LOST!\n\n"
                summary += f"Final score: {self.user_score} - {self.opponent_score}\n"
                summary += f"{self.opponent['name'].upper()} wins!\n"
                summary += f"You earned: +{final_reward} FIFA coins\n"
                summary += f"(Consolation reward: {reward_percent} of base reward)"
            else:
                summary = f"IT'S A DRAW!\n\n"
                summary += f"Final score: {self.user_score} - {self.opponent_score}\n"
                summary += f"You earned: +{final_reward} FIFA coins\n"
                summary += f"(Draw reward: {reward_percent} of base reward)"
        else:
            summary = f"⏱{minute}' - Score: {self.user_score} - {self.opponent_score}"

        return summary

    def _get_team_name(self, team):
        return "YOUR TEAM" if team == 'user' else self.opponent['name'].upper()

    def _get_random_player(self, team):
        if team == 'user':
            players = []
            for slot_id, card_id in self.user_team.players.items():
                card = self.user_collection.get_card(card_id)
                if card:
                    players.append(card.player_name)
            return random.choice(players) if players else "Unknown Player"
        else:
            return random.choice(self.opponent['team']).player_name

    def _calculate_user_advantage(self):
        advantage = 50
        advantage += (self.user_stats['overall'] - self.opponent_stats['overall']) * 0.5
        advantage += (self.user_stats['attack'] - self.opponent_stats['attack']) * 0.2
        advantage += (self.user_stats['midfield'] - self.opponent_stats['midfield']) * 0.2
        advantage += (self.user_stats['defense'] - self.opponent_stats['defense']) * 0.2
        advantage += (self.user_stats['chemistry'] - self.opponent_stats['chemistry']) * 0.1
        return max(0, min(100, advantage))

class MatchManager:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.active_matches = {}
        self.match_counter = 0
        self.match_tasks = {}
        self.match_threads = {}

    def create_match(self, user_id, user_team, user_formation, user_collection, fifa_plugin):
        self.match_counter += 1
        match = Match(self.match_counter, user_id, user_team, user_formation, user_collection, fifa_plugin)
        self.active_matches[match.match_id] = match
        return match

    def get_match(self, match_id):
        return self.active_matches.get(match_id)

    def remove_match(self, match_id):
        if match_id in self.match_threads:
            if self.match_threads[match_id].is_alive():
                self.match_threads[match_id].join(timeout=1)
            del self.match_threads[match_id]

        if match_id in self.match_tasks:
            if not self.match_tasks[match_id].done():
                self.match_tasks[match_id].cancel()
            del self.match_tasks[match_id]

        if match_id in self.active_matches:
            del self.active_matches[match_id]

class PlayerMatch:
    def __init__(self, match_id, player1_id, player2_id, player1_name, player2_name,
                 player1_team, player2_team, player1_formation, player2_formation,
                 player1_collection, player2_collection, fifa_plugin):
        self.match_id = match_id
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.player1_name = player1_name
        self.player2_name = player2_name
        self.player1_team = player1_team
        self.player2_team = player2_team
        self.player1_formation = player1_formation
        self.player2_formation = player2_formation
        self.player1_collection = player1_collection
        self.player2_collection = player2_collection
        self.fifa_plugin = fifa_plugin
        self.status = "waiting"
        self.player1_score = 0
        self.player2_score = 0
        self.minute = 0
        self.match_script = []
        self.opponent_logo = self._select_opponent_logo()


        self.player1_stats = fifa_plugin._calculate_team_stats_for_match(
            player1_team, player1_formation, player1_collection
        )
        self.player2_stats = fifa_plugin._calculate_team_stats_for_match(
            player2_team, player2_formation, player2_collection
        )


        self.player1_chance, self.player2_chance = self._calculate_win_chances()
        self.player1_reward, self.player2_reward, self.draw_reward = self._calculate_rewards()


        self.player1_categories = self._categorize_stats(self.player1_stats)
        self.player2_categories = self._categorize_stats(self.player2_stats)

    def _categorize_stats(self, stats):
        return {
            'attack_power': 'strong' if stats['attack'] > 80 else 'medium' if stats['attack'] > 60 else 'weak',
            'midfield_control': 'strong' if stats['midfield'] > 80 else 'medium' if stats['midfield'] > 60 else 'weak',
            'defense_solidity': 'strong' if stats['defense'] > 80 else 'medium' if stats['defense'] > 60 else 'weak',
            'chemistry': 'perfect' if stats['chemistry'] > 85 else 'good' if stats['chemistry'] > 70 else 'poor',
            'positioning': 'perfect' if stats['position_fit'] > 85 else 'good' if stats['position_fit'] > 70 else 'poor',
            'overall': stats['overall']
        }

    def _select_opponent_logo(self):
        if hasattr(self, 'player2_id') and self.player2_id and self.fifa_plugin.cache:
            avatar_path = self.fifa_plugin.cache.get_avatar_path(self.player2_id)
            if avatar_path and os.path.exists(avatar_path):
                return avatar_path

        return None

    def _calculate_win_chances(self):
        player1_power = self.player1_stats['overall'] * (self.player1_stats['chemistry'] / 100) * (self.player1_stats['position_fit'] / 100)
        player2_power = self.player2_stats['overall'] * (self.player2_stats['chemistry'] / 100) * (self.player2_stats['position_fit'] / 100)

        total_power = player1_power + player2_power
        if total_power == 0:
            return 200, 200

        player1_chance = int(100 + (player2_power / total_power) * 200)
        player2_chance = int(100 + (player1_power / total_power) * 200)

        player1_chance = max(100, min(300, player1_chance))
        player2_chance = max(100, min(300, player2_chance))

        return player1_chance, player2_chance

    def _calculate_rewards(self):
        base_reward = 100
        player1_win_reward = int(base_reward * (self.player1_chance / 100))
        player2_win_reward = int(base_reward * (self.player2_chance / 100))
        draw_reward = int(base_reward * 0.75)
        return player1_win_reward, player2_win_reward, draw_reward

    def _get_random_player(self, team):
        if team == 'player1':
            players = []
            for slot_id, card_id in self.player1_team.players.items():
                card = self.player1_collection.get_card(card_id)
                if card:
                    players.append(card.player_name)
            return random.choice(players) if players else "Unknown Player"
        else:
            players = []
            for slot_id, card_id in self.player2_team.players.items():
                card = self.player2_collection.get_card(card_id)
                if card:
                    players.append(card.player_name)
            return random.choice(players) if players else "Unknown Player"

    def generate_match_script(self):
        self.match_script = []
        update_intervals = [15, 30, 45, 60, 75, 90]
        user_advantage = self._calculate_user_advantage()

        for minute in update_intervals:
            is_final = (minute == 90)
            fragment = self._generate_match_fragment_advanced(minute, user_advantage, is_final)
            self.match_script.append(fragment)

        return self.match_script

    def _calculate_user_advantage(self):
        advantage = 50
        advantage += (self.player1_stats['overall'] - self.player2_stats['overall']) * 0.5
        advantage += (self.player1_stats['attack'] - self.player2_stats['attack']) * 0.2
        advantage += (self.player1_stats['midfield'] - self.player2_stats['midfield']) * 0.2
        advantage += (self.player1_stats['defense'] - self.player2_stats['defense']) * 0.2
        advantage += (self.player1_stats['chemistry'] - self.player2_stats['chemistry']) * 0.1
        return max(0, min(100, advantage))

    def _generate_match_fragment_advanced(self, minute, user_advantage, is_final):
        events = []

        intensity_mult = 1.0
        if self.player1_categories['attack_power'] == 'strong' or self.player2_categories['attack_power'] == 'strong':
            intensity_mult += 0.3

        base_events = random.randint(4, 8)
        if minute >= 75:
            base_events += 2
        num_events = int(base_events * intensity_mult)

        previous_minute = minute - 14
        used_minutes = set()

        for i in range(num_events):
            minute_offset = random.randint(0, 14)
            event_minute = minute - 14 + minute_offset

            while event_minute in used_minutes or event_minute > minute or event_minute < previous_minute:
                minute_offset = random.randint(0, 14)
                event_minute = minute - 14 + minute_offset

            used_minutes.add(event_minute)

            team = self._determine_team_for_action(user_advantage)
            event = self._generate_stat_based_event(team, event_minute, include_minute=False)
            if event:
                events.append((event_minute, event))

        events.sort(key=lambda x: x[0])
        clean_events = [f"[{minute_val}] {event_text}" for minute_val, event_text in events]

        if minute == 45:
            clean_events.append(f"[45'] HALF TIME")
        elif minute == 90:
            clean_events.append(f"[90'] FULL TIME")

        summary = self._generate_detailed_summary(minute, is_final)

        return {
            'minute': minute,
            'events': clean_events,
            'summary': summary,
            'is_final': is_final,
            'player1_score': self.player1_score,
            'player2_score': self.player2_score
        }

    def _determine_team_for_action(self, user_advantage):
        return 'player1' if random.random() * 100 < user_advantage else 'player2'

    def _generate_stat_based_event(self, team, minute, include_minute=True):
        if team == 'player1':
            stats = self.player1_stats
            categories = self.player1_categories
        else:
            stats = self.player2_stats
            categories = self.player2_categories

        event_type = self._select_event_by_stats(stats, minute)

        if event_type == 'goal':
            return self._generate_goal_event(team, minute, include_minute)
        elif event_type == 'yellow_card':
            return self._generate_yellow_card_event(team, minute, include_minute)
        elif event_type == 'red_card':
            return self._generate_red_card_event(team, minute, include_minute)
        elif event_type == 'shot':
            return self._generate_shot_event(team, minute, include_minute)
        elif event_type == 'save':
            return self._generate_save_event(team, minute, include_minute)
        elif event_type == 'tackle':
            return self._generate_tackle_event(team, minute, include_minute)
        elif event_type == 'foul':
            return self._generate_foul_event(team, minute, include_minute)
        elif event_type == 'corner':
            return self._generate_corner_event(team, minute, include_minute)
        elif event_type == 'offside':
            return self._generate_offside_event(team, minute, include_minute)
        elif event_type == 'injury':
            return self._generate_injury_event(team, minute, include_minute)

        return self._generate_pass_event(team, minute, include_minute)

    def _select_event_by_stats(self, stats, minute):
        weights = {
            'pass': 20, 'tackle': 15, 'shot': 10, 'foul': 10,
            'corner': 8, 'offside': 5, 'save': 5, 'goal': 5,
            'injury': 3, 'yellow_card': 2, 'red_card': 1
        }

        if stats['attack'] > 80:
            weights['shot'] += 10
            weights['goal'] += 5
        elif stats['attack'] < 60:
            weights['shot'] -= 5
            weights['pass'] += 5

        if stats['midfield'] > 80:
            weights['pass'] += 10
        elif stats['midfield'] < 60:
            weights['pass'] -= 5
            weights['tackle'] += 5

        if stats['defense'] > 80:
            weights['tackle'] += 10
            weights['save'] += 5
        elif stats['defense'] < 60:
            weights['tackle'] -= 5
            weights['foul'] += 5

        if minute > 75:
            weights['shot'] += 10
            weights['goal'] += 5

        total_weight = sum(weights.values())
        rand = random.randint(1, total_weight)

        cumulative = 0
        for event, weight in weights.items():
            cumulative += weight
            if rand <= cumulative:
                return event

        return 'pass'

    def _generate_goal_event(self, team, minute, include_minute=True):
        player = self._get_random_player(team)
        if team == 'player1':
            self.player1_score += 1
            score = f"{self.player1_score}-{self.player2_score}"
            team_name = self.player1_name
        else:
            self.player2_score += 1
            score = f"{self.player1_score}-{self.player2_score}"
            team_name = self.player2_name

        if minute < 30:
            descriptions = [
                f"GOAL! {player} opens the scoring! ({score})",
                f"What a start! {player} scores for {team_name}! ({score})"
            ]
        elif minute < 60:
            descriptions = [
                f"GOAL! {player} doubles the lead! ({score})",
                f"{player} pulls one back! ({score})"
            ]
        else:
            descriptions = [
                f"GOAL! {player} scores a crucial goal! ({score})",
                f"{player} with a late strike! ({score})"
            ]

        event_text = random.choice(descriptions)
        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_yellow_card_event(self, team, minute, include_minute=True):
        player = self._get_random_player(team)
        team_name = self.player1_name if team == 'player1' else self.player2_name
        descriptions = [
            f"Yellow card for {player} ({team_name}) - tactical foul.",
            f"{player} ({team_name}) goes into the book.",
            f"Late challenge by {player} ({team_name}) - yellow card."
        ]
        event_text = random.choice(descriptions)
        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_red_card_event(self, team, minute, include_minute=True):
        player = self._get_random_player(team)
        team_name = self.player1_name if team == 'player1' else self.player2_name
        if team == 'player1':
            descriptions = [
                f"RED CARD! {player} is sent off! {self.player1_name} down to 10 players!",
                f"Disastrous! {player} sees red for a dangerous tackle!"
            ]
        else:
            descriptions = [
                f"RED CARD! {player} ({team_name}) is sent off! Advantage for {self.player1_name}!",
                f"{player} ({team_name}) receives a marching order!"
            ]
        event_text = random.choice(descriptions)
        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_shot_event(self, team, minute, include_minute=True):
        player = self._get_random_player(team)
        team_name = self.player1_name if team == 'player1' else self.player2_name
        if minute > 85:
            descriptions = [
                f"{player} ({team_name}) shoots from distance - just wide!",
                f"{player} ({team_name}) with a late effort!"
            ]
        else:
            descriptions = [
                f"{player} ({team_name}) takes a shot - saved by the keeper!",
                f"{player} ({team_name}) tries his luck from outside the box!"
            ]
        event_text = random.choice(descriptions)
        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_save_event(self, team, minute, include_minute=True):
        team_name = self.player1_name if team == 'player1' else self.player2_name
        descriptions = [
            f"Great save by {team_name} goalkeeper!",
            f"{team_name} goalkeeper positions well to make the save.",
            f"{team_name} goalkeeper catches the ball comfortably."
        ]
        event_text = random.choice(descriptions)
        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_tackle_event(self, team, minute, include_minute=True):
        player = self._get_random_player(team)
        team_name = self.player1_name if team == 'player1' else self.player2_name
        descriptions = [
            f"{player} ({team_name}) makes a solid tackle.",
            f"{player} ({team_name}) wins the ball back.",
            f"Good defensive work by {player} ({team_name})."
        ]
        event_text = random.choice(descriptions)
        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_foul_event(self, team, minute, include_minute=True):
        player = self._get_random_player(team)
        team_name = self.player1_name if team == 'player1' else self.player2_name
        descriptions = [
            f"Foul by {player} ({team_name})! Free kick in a dangerous position.",
            f"{player} ({team_name}) brings down an opponent - free kick.",
            f"Tactical foul by {player} ({team_name}) - referee plays advantage."
        ]
        event_text = random.choice(descriptions)
        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_corner_event(self, team, minute, include_minute=True):
        team_name = self.player1_name if team == 'player1' else self.player2_name
        descriptions = [
            f"Corner kick for {team_name}.",
            f"{team_name} wins a corner - chance to score!",
            f"Set piece opportunity for {team_name} from the corner."
        ]
        event_text = random.choice(descriptions)
        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_offside_event(self, team, minute, include_minute=True):
        player = self._get_random_player(team)
        team_name = self.player1_name if team == 'player1' else self.player2_name
        descriptions = [
            f"Offside! {player} ({team_name}) mistimed his run.",
            f"{player} ({team_name}) caught in the offside trap.",
            f"Linesman raises the flag - offside against {team_name}."
        ]
        event_text = random.choice(descriptions)
        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_injury_event(self, team, minute, include_minute=True):
        player = self._get_random_player(team)
        team_name = self.player1_name if team == 'player1' else self.player2_name
        descriptions = [
            f"{player} ({team_name}) is down after that challenge.",
            f"Medical staff rushing onto the pitch for {player} ({team_name}).",
            f"{player} ({team_name}) seems unable to continue."
        ]
        event_text = random.choice(descriptions)
        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_pass_event(self, team, minute, include_minute=True):
        player = self._get_random_player(team)
        team_name = self.player1_name if team == 'player1' else self.player2_name
        descriptions = [
            f"{team_name} controls possession through {player}.",
            f"Patient build-up play by {team_name}.",
            f"{player} ({team_name}) distributes the ball well."
        ]
        event_text = random.choice(descriptions)
        if include_minute:
            return f"[{minute}'] {event_text}"
        return event_text

    def _generate_detailed_summary(self, minute, is_final):
        if is_final:
            if self.player1_score > self.player2_score:
                winner_name = self.player1_name
                loser_name = self.player2_name
                winner_reward = self.player1_reward
                loser_reward = 0
                result_text = "WIN"
            elif self.player1_score < self.player2_score:
                winner_name = self.player2_name
                loser_name = self.player1_name
                winner_reward = self.player2_reward
                loser_reward = 0
                result_text = "LOSS"
            else:

                return f"MATCH DRAW!\n\nFinal score: {self.player1_score}-{self.player2_score}\n\nBoth players earned: +{self.draw_reward} casino coins!"


            return f"{winner_name} WINS! \n\nFinal score: {self.player1_score}-{self.player2_score}\n\nWinner earns: +{winner_reward} casino coins!"
        else:
            return f"{minute}' - Score: {self.player1_score}-{self.player2_score}"

class LeagueManager:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.active_matches = {}
        self.match_counter = 0
        self.match_threads = {}
        self.players_ready = {}

    def add_ready_player(self, user_id, team, formation, collection):
        self.players_ready[user_id] = {
            'team': team,
            'formation': formation,
            'collection': collection,
            'joined_at': time.time()
        }

    def remove_ready_player(self, user_id):
        if user_id in self.players_ready:
            del self.players_ready[user_id]

    def find_match(self, user_id):
        for opponent_id, opponent_data in self.players_ready.items():
            if opponent_id != user_id:
                return opponent_id, opponent_data
        return None, None

    def create_match(self, user_id, opponent_id, player1_data, player2_data, player1_name, player2_name, fifa_plugin):
        self.match_counter += 1

        match = PlayerMatch(
            self.match_counter, user_id, opponent_id,
            player1_name, player2_name,
            player1_data['team'], player2_data['team'],
            player1_data['formation'], player2_data['formation'],
            player1_data['collection'], player2_data['collection'],
            fifa_plugin
        )

        self.active_matches[match.match_id] = match
        return match

    def get_match(self, match_id):
        return self.active_matches.get(match_id)

    def remove_match(self, match_id):
        if match_id in self.match_threads:
            if self.match_threads[match_id].is_alive():
                self.match_threads[match_id].join(timeout=1)
            del self.match_threads[match_id]

        if match_id in self.active_matches:
            del self.active_matches[match_id]

class DailyLimits:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.limits_file = os.path.join(data_folder, "daily_limits.json")
        self.limits_data = self._load_limits()

    def _load_limits(self):
        if os.path.exists(self.limits_file):
            try:
                with open(self.limits_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[FIFA] Error loading daily limits: {e}")
                return {}
        return {}

    def _save_limits(self):
        try:
            os.makedirs(self.data_folder, exist_ok=True)
            with open(self.limits_file, 'w', encoding='utf-8') as f:
                json.dump(self.limits_data, f, indent=2)
        except Exception as e:
            logger.error(f"[FIFA] Error saving daily limits: {e}")

    def _get_today(self):
        return datetime.now().strftime('%Y-%m-%d')

    def can_play_match(self, user_id, match_type):
        today = self._get_today()
        user_key = f"{user_id}_{match_type}"

        if user_key not in self.limits_data:
            self.limits_data[user_key] = {'date': today, 'count': 0}
            self._save_limits()
            return True

        data = self.limits_data[user_key]
        if data['date'] != today:
            data['date'] = today
            data['count'] = 0
            self._save_limits()
            return True

        return data['count'] < 1

    def increment_match(self, user_id, match_type):
        today = self._get_today()
        user_key = f"{user_id}_{match_type}"

        if user_key not in self.limits_data or self.limits_data[user_key]['date'] != today:
            self.limits_data[user_key] = {'date': today, 'count': 1}
        else:
            self.limits_data[user_key]['count'] += 1

        self._save_limits()

    def get_remaining_matches(self, user_id):
        today = self._get_today()
        remaining = {}

        for match_type in ['ai', 'pvp']:
            user_key = f"{user_id}_{match_type}"
            if user_key not in self.limits_data or self.limits_data[user_key]['date'] != today:
                remaining[match_type] = 1
            else:
                remaining[match_type] = max(0, 1 - self.limits_data[user_key]['count'])

        return remaining

class FifaPlugin(BaseGamePlugin):
    def __init__(self):
        logger.info("[FIFA] Initializing FIFA plugin")
        super().__init__(game_name="fifa")

        self.assets_folder = self.get_asset_path("fifa")
        self.cards_folder = os.path.join(self.assets_folder, "cards")
        self.data_folder = os.path.join(self.get_asset_path(""), "fifa_data")
        self.packs_image = os.path.join(self.assets_folder, "packs.png")
        self.fifa_coins_icon_path = os.path.join(self.assets_folder, "fifa_coins.png")
        self.formations_folder = os.path.join(self.assets_folder, "formation")
        self.formations_images_folder = os.path.join(self.assets_folder, "formations")
        self.opponent_logos_folder = os.path.join(self.assets_folder, "team_logos")
        self.match_icons_folder = os.path.join(self.assets_folder, "match_icons")
        self.daily_limits = DailyLimits(self.data_folder)
        os.makedirs(self.match_icons_folder, exist_ok=True)

        self.fifa_coins_icon = None
        if os.path.exists(self.fifa_coins_icon_path):
            try:
                self.fifa_coins_icon = Image.open(self.fifa_coins_icon_path).convert('RGBA')
                logger.info(f"[FIFA] Loaded FIFA coins icon")
            except Exception as e:
                logger.error(f"[FIFA] Failed to load FIFA coins icon: {e}")

        self.pack_opener = FifaPackOpener(self.assets_folder)
        self.image_generator = FifaImageGenerator(self.text_renderer, self.fifa_coins_icon)
        self.team_image_generator = FifaTeamImageGenerator(self.text_renderer, self.fifa_coins_icon)
        self.coins_manager = FifaCoinsManager(self.data_folder)
        self.formation_manager = FifaFormationManager(self.formations_folder, self.formations_images_folder)
        self.match_manager = MatchManager(self.data_folder)
        self.league_manager = LeagueManager(self.data_folder)

        self.team_image_generator.opponent_logos_folder = self.opponent_logos_folder

        self.pack_prices = {
            'bronze': {'fifa_coins': 750, 'casino_coins': 75},
            'silver': {'fifa_coins': 5000, 'casino_coins': 150},
            'gold': {'fifa_coins': 10000, 'casino_coins': 300}
        }

        os.makedirs(self.data_folder, exist_ok=True)
        os.makedirs(os.path.join(self.data_folder, "collections"), exist_ok=True)
        os.makedirs(os.path.join(self.data_folder, "teams"), exist_ok=True)
        os.makedirs(self.opponent_logos_folder, exist_ok=True)

    def _send_league_match_preview(self, sender, file_queue, match, cache, user_id, opponent_id):

        class TempMatch:
            pass

        temp_match = TempMatch()
        temp_match.user_stats = match.player1_stats
        temp_match.opponent_stats = match.player2_stats
        temp_match.opponent = {'name': match.player2_name}
        temp_match.user_id = user_id


        self.team_image_generator.match = temp_match


        preview_path = os.path.join(self.results_folder, f"fifa_league_preview_{match.match_id}.png")


        user_avatar = cache.get_avatar_path(user_id) if cache else None
        opponent_avatar = cache.get_avatar_path(opponent_id) if cache else None


        self.team_image_generator.generate_match_preview_image(
            match.player1_team, match.player1_formation, match.player1_collection,
            {'name': match.player2_name, 'team': match.player2_team},
            match.player2_formation,
            preview_path, 0, cache, user_id, opponent_avatar
        )

        final_preview = os.path.join(self.results_folder, f"fifa_league_preview_{match.match_id}_final.png")
        self.apply_background(preview_path, user_id, final_preview)
        if os.path.exists(preview_path):
            os.remove(preview_path)

        file_queue.put(final_preview)


    def _run_player_match_sync(self, sender, file_queue, match, cache, user_id, opponent_id=None):
        match.generate_match_script()
        match.status = "in_progress"

        preview_msg = f"**Match Started!**\n\n"
        preview_msg += f"{match.player1_name} vs {match.player2_name}\n"
        preview_msg += f"Updates every 15 minutes!"

        self.send_message_image(sender, file_queue, preview_msg, "FIFA League Match", cache, user_id)

        for i in range(6):
            time.sleep(15 * 60)

            fragment = match.match_script[i]
            match.minute = fragment['minute']
            match.player1_score = fragment['player1_score']
            match.player2_score = fragment['player2_score']

            self._send_league_match_fragment(sender, file_queue, match, i, cache, user_id, opponent_id)

        self._finish_player_match(sender, file_queue, match, cache, user_id)

    def _send_league_match_fragment(self, sender, file_queue, match, fragment_index, cache, user_id, opponent_id=None):
        if fragment_index >= len(match.match_script):
            return

        fragment = match.match_script[fragment_index]
        match.minute = fragment['minute']

        temp_path = os.path.join(self.results_folder, f"fifa_league_match_{match.match_id}_fragment_{fragment_index}_temp.png")
        final_path = os.path.join(self.results_folder, f"fifa_league_match_{match.match_id}_fragment_{fragment_index}.png")


        class TempMatch:
            pass

        temp_match = TempMatch()
        temp_match.user_score = fragment['player1_score']
        temp_match.opponent_score = fragment['player2_score']
        temp_match.user_stats = match.player1_stats
        temp_match.opponent_stats = match.player2_stats
        temp_match.opponent = {'name': match.player2_name}
        temp_match.opponent_logo = cache.get_avatar_path(opponent_id)


        self.team_image_generator.match = temp_match
        self.team_image_generator.generate_match_fragment_image(temp_match, fragment, fragment_index, temp_path, cache, user_id)
        self.apply_background(temp_path, user_id, final_path)
        file_queue.put(final_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def _finish_player_match(self, sender, file_queue, match, cache, user_id):
        match.status = "finished"

        if match.player1_score > match.player2_score:
            winner_id = match.player1_id
            winner_name = match.player1_name
            loser_id = match.player2_id
            winner_reward = match.player1_reward
            result_text = f"{match.player1_name} WINS! {match.player1_score}-{match.player2_score}"
        elif match.player2_score > match.player1_score:
            winner_id = match.player2_id
            winner_name = match.player2_name
            loser_id = match.player1_id
            winner_reward = match.player2_reward
            result_text = f"{match.player2_name} WINS! {match.player1_score}-{match.player2_score}"
        else:
            winner_id = None
            winner_reward = match.draw_reward
            result_text = f"DRAW! {match.player1_score}-{match.player2_score}"

        if winner_id:
            winner_balance = self.cache.get_user(winner_id)["balance"]

            self.update_user_balance(winner_id, winner_balance + winner_reward)
            if loser_id:
                msg_winner = f"🏆 **MATCH RESULT: WIN!** 🏆\n\n{result_text}\nYou earned: {winner_reward} casino coins!"
                msg_loser = f"😔 **MATCH RESULT: LOSS** 😔\n\n{result_text}\nBetter luck next time!"
                self.send_message_image(sender, file_queue, msg_winner, "FIFA League Result", cache, winner_id)
                self.send_message_image(sender, file_queue, msg_loser, "FIFA League Result", cache, loser_id)
        else:

            player1_balance = self.cache.get_user(match.player1_id)["balance"]
            player2_balance = self.cache.get_user(match.player2_id)["balance"]

            self.update_user_balance(match.player1_id, player1_balance + winner_reward)
            self.update_user_balance(match.player2_id, player2_balance + winner_reward)

            msg = f"**MATCH RESULT: DRAW**\n\n{result_text}\nYou earned: {winner_reward} casino coins each!"
            self.send_message_image(sender, file_queue, msg, "FIFA League Result", cache, match.player1_id)
            self.send_message_image(sender, file_queue, msg, "FIFA League Result", cache, match.player2_id)

        self.league_manager.remove_match(match.match_id)

    def _send_match_fragment_sync(self, sender, file_queue, match, fragment_index, cache, user_id):
        if fragment_index >= len(match.match_script):
            return

        fragment = match.match_script[fragment_index]
        match.minute = fragment['minute']


        if 'user_score' in fragment:
            match.user_score = fragment['user_score']
        if 'opponent_score' in fragment:
            match.opponent_score = fragment['opponent_score']

        temp_path = os.path.join(self.results_folder, f"fifa_match_{match.match_id}_fragment_{fragment_index}_temp.png")
        final_path = os.path.join(self.results_folder, f"fifa_match_{match.match_id}_fragment_{fragment_index}.png")

        self.team_image_generator.generate_match_fragment_image(match, fragment, fragment_index, temp_path, cache, user_id)
        self.apply_background(temp_path, user_id, final_path)
        file_queue.put(final_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)

    def _calculate_team_stats_for_match(self, team, formation, collection):
        from copy import deepcopy
        temp_match = Match(0, 0, team, formation, collection, self)
        stats = temp_match._calculate_advanced_team_stats(team, formation, collection, is_user=True)
        return stats

    def _get_user_name(self, user_id):
        if self.cache:
            try:
                user_data = self.cache.get_user(user_id)
                if user_data and 'name' in user_data:
                    return user_data['name']
            except Exception as e:
                logger.error(f"[FIFA] Error getting user name: {e}")
        return f"Player {user_id}"

    def _get_available_players(self, current_user_id):
        available = []
        for user_id, data in self.league_manager.players_ready.items():
            if user_id != current_user_id:
                formation = data['formation']
                team = data['team']
                collection = data['collection']

                stats = self._calculate_team_stats_for_match(team, formation, collection)
                rating = stats['overall']

                user_name = self._get_user_name(user_id)
                available.append({
                    'user_id': user_id,
                    'name': user_name,
                    'rating': rating
                })
        return available

    def _finish_match_sync(self, sender, file_queue, match, cache, user_id):
        if match.status == MatchStatus.FINISHED:
            return

        match.status = MatchStatus.FINISHED

        base_reward = match.reward

        if match.user_score > match.opponent_score:
            final_reward = base_reward
            new_balance = self.add_fifa_coins(user_id, final_reward)
            msg = f"MATCH RESULT: WIN!\n\nFinal score: {match.user_score} - {match.opponent_score}\n"
            msg += f"You earned: {final_reward} FIFA coins!\n"
            msg += f"New balance: {new_balance} FIFA coins"

        elif match.user_score < match.opponent_score:
            final_reward = int(base_reward * 0.1)
            if final_reward < 10:
                final_reward = 10
            new_balance = self.add_fifa_coins(user_id, final_reward)
            msg = f"MATCH RESULT: LOSS\n\nFinal score: {match.user_score} - {match.opponent_score}\n"
            msg += f"You earned: {final_reward} FIFA coins!\n"
            msg += f"New balance: {new_balance} FIFA coins"

        else:
            final_reward = int(base_reward * 0.5)
            new_balance = self.add_fifa_coins(user_id, final_reward)
            msg = f"MATCH RESULT: DRAW\n\nFinal score: {match.user_score} - {match.opponent_score}\n"
            msg += f"You earned: {final_reward} FIFA coins!\n"
            msg += f"New balance: {new_balance} FIFA coins"

        self.send_message_image(sender, file_queue, msg, "FIFA Match Result", cache, user_id)
        self.match_manager.remove_match(match.match_id)

    def get_user_collection(self, user_id):
        return FifaCollection(user_id, self.data_folder)

    def get_user_team(self, user_id):
        return FifaTeam(user_id, self.data_folder)

    def get_fifa_coins(self, user_id):
        return self.coins_manager.get_coins(user_id)

    def add_fifa_coins(self, user_id, amount):
        return self.coins_manager.add_coins(user_id, amount)

    def remove_fifa_coins(self, user_id, amount):
        return self.coins_manager.remove_coins(user_id, amount)

    def get_user_background(self, user_id):
        if self.cache:
            background_path = self.cache.get_background_path(user_id)
            if background_path and os.path.exists(background_path):
                return background_path
        return None

    def apply_background(self, image_path, user_id, output_path):
        try:
            if not os.path.exists(image_path):
                return None

            game_img = Image.open(image_path).convert('RGBA')
            game_width, game_height = game_img.size
            background_path = self.get_user_background(user_id)

            if background_path and os.path.exists(background_path):
                bg_image = Image.open(background_path).convert('RGBA')
                target_width = game_width + 20
                target_height = game_height + 20
                bg_image = bg_image.resize((target_width, target_height), Image.Resampling.LANCZOS)
                final_img = Image.new('RGBA', (target_width, target_height), (0, 0, 0, 0))
                final_img.paste(bg_image, (0, 0))
                final_img.alpha_composite(game_img, (10, 10))
                final_img.save(output_path, format='PNG')
                return output_path
            else:
                shutil.copy(image_path, output_path)
                return output_path
        except Exception as e:
            logger.error(f"[FIFA] Error applying background: {e}")
            if os.path.exists(image_path):
                shutil.copy(image_path, output_path)
                return output_path
            return None

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        if error:
            self.send_message_image(sender, file_queue, error, "FIFA - Error", cache, user_id)
            return ""

        logger.info(f"[FIFA] User {sender} ({user_id}) executed command: {args}")
        self.coins_manager.initialize_user(user_id)

        if len(args) == 0:
            self.send_message_image(sender, file_queue,
                                "FIFA Card Game Commands:\n\n"
                                "**Packs:**\n"
                                "/fifa packs - Show available packs\n"
                                "/fifa open bronze/silver/gold - Open pack with FIFA coins\n"
                                "/fifa buy bronze/silver/gold - Buy pack with casino coins\n\n"
                                "**Collection:**\n"
                                "/fifa cards [page] - Show your cards\n"
                                "/fifa cards new/old/rating/price - Sort\n"
                                "/fifa cards [position] - Filter (e.g., CB, ST)\n\n"
                                "**Team:**\n"
                                "/fifa formations [page] - Show formations\n"
                                "/fifa formations set <id> - Set active formation\n"
                                "/fifa team - Show your team\n"
                                "/fifa team set <slot> <card_id> - Put player in slot\n"
                                "/fifa team remove <slot> - Remove player\n\n"
                                "**Selling:**\n"
                                "/fifa sell <id> - Sell a card\n\n"
                                "**Matches:**\n"
                                "/fifa match start - Start a match vs AI\n"
                                "/fifa league - Play against other players\n\n"
                                "**Balance:**\n"
                                "/fifa balance - Show your FIFA coins",
                                "FIFA Help", cache, user_id)
            return ""

        cmd = args[0].lower()

        if cmd == "packs" or cmd == "shop" or cmd == "p" or cmd == "s" or cmd == "pack":
            if os.path.exists(self.packs_image):
                img_path = os.path.join(self.results_folder, f"fifa_packs_{user_id}.png")
                shutil.copy(self.packs_image, img_path)

                fifa_coins = self.get_fifa_coins(user_id)
                temp_path = os.path.join(self.results_folder, f"fifa_packs_{user_id}_temp.png")

                img = Image.open(img_path).convert('RGBA')
                draw = ImageDraw.Draw(img)
                width, height = img.size

                if self.text_renderer and self.fifa_coins_icon:
                    coins_icon = self.fifa_coins_icon.copy()
                    coins_icon = coins_icon.resize((20, 20))
                    coins_text = str(fifa_coins)
                    coins_img = self.text_renderer.render_text(text=coins_text, font_size=14, color=(255, 215, 0, 255), stroke_width=1, stroke_color=(0, 0, 0, 255))

                    icon_x = 10
                    icon_y = height - 30
                    text_x = icon_x + 25
                    text_y = icon_y - 2

                    draw.rectangle([icon_x-2, icon_y-2, text_x + coins_img.width + 2, icon_y + 22], fill=(0, 0, 0, 180))
                    img.paste(coins_icon, (icon_x, icon_y), coins_icon)
                    img.paste(coins_img, (text_x, text_y), coins_img)

                    command_text = "/fifa open bronze/silver/gold  |  /fifa buy bronze/silver/gold"
                    command_img = self.text_renderer.render_text(text=command_text, font_size=12, color=(200, 200, 200, 255), stroke_width=1, stroke_color=(0, 0, 0, 100))

                    cmd_x = (width - command_img.width) // 2
                    cmd_y = height - 55

                    draw.rectangle([cmd_x-5, cmd_y-2, cmd_x + command_img.width + 5, cmd_y + command_img.height + 2], fill=(0, 0, 0, 150))
                    img.paste(command_img, (cmd_x, cmd_y), command_img)

                    img.save(temp_path, format='PNG')
                    final_path = os.path.join(self.results_folder, f"fifa_packs_{user_id}_final.png")
                    self.apply_background(temp_path, user_id, final_path)

                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                else:
                    final_path = os.path.join(self.results_folder, f"fifa_packs_{user_id}_final.png")
                    self.apply_background(img_path, user_id, final_path)

                file_queue.put(final_path)
                return ""
            else:
                msg = "**Available FIFA Packs:**\n\n **BRONZE**\n• FIFA coins: 750\n• Casino coins: 75\n\ **SILVER**\n• FIFA coins: 5000\n• Casino coins: 150\n\n **GOLD**\n• FIFA coins: 10000\n• Casino coins: 300\n\n**Commands:**\n/fifa open bronze - open with FIFA coins\n/fifa buy bronze - buy with casino coins"
                self.send_message_image(sender, file_queue, msg, "FIFA Packs", cache, user_id)
                return ""

        elif cmd == "open" or cmd == "o":
            if len(args) < 2:
                self.send_message_image(sender, file_queue, "Usage: /fifa open bronze/silver/gold", "FIFA - Open Pack", cache, user_id)
                return ""

            pack_type = args[1].lower()
            if pack_type not in self.pack_prices:
                self.send_message_image(sender, file_queue, f"Invalid pack type: {pack_type}\n\nAvailable: bronze, silver, gold", "FIFA - Error", cache, user_id)
                return ""

            fifa_coins = self.get_fifa_coins(user_id)
            price = self.pack_prices[pack_type]['fifa_coins']

            if fifa_coins < price:
                casino_price = self.pack_prices[pack_type]['casino_coins']
                casino_balance = user.get('balance', 0)

                msg = f"**Not enough FIFA coins!**\n\nYou have: {fifa_coins} FIFA coins\nNeed: {price} FIFA coins\n\n**Buy with casino coins?**\nPrice: {casino_price} coins\nYour balance: {casino_balance} coins\n\nUse: `/fifa buy {pack_type}`"
                self.send_message_image(sender, file_queue, msg, "FIFA - Insufficient Funds", cache, user_id)
                return ""

            cards = self.pack_opener.open_pack(pack_type)
            if not cards:
                self.send_message_image(sender, file_queue, f"Error opening {pack_type} pack. Try again later.", "FIFA - Error", cache, user_id)
                return ""

            self.remove_fifa_coins(user_id, price)
            new_fifa_coins = fifa_coins - price

            collection = self.get_user_collection(user_id)
            card_ids = collection.add_cards(cards)

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            temp_path = os.path.join(self.results_folder, f"fifa_pack_{user_id}_{timestamp}_temp.png")
            final_path = os.path.join(self.results_folder, f"fifa_pack_{user_id}_{timestamp}.png")

            self.image_generator.generate_pack_image(cards, temp_path, new_fifa_coins)
            self.apply_background(temp_path, user_id, final_path)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            file_queue.put(final_path)
            return ""

        elif cmd == "buy" or cmd == "b":
            if len(args) < 2:
                self.send_message_image(sender, file_queue, "Usage: /fifa buy bronze/silver/gold", "FIFA - Buy Pack", cache, user_id)
                return ""

            pack_type = args[1].lower()
            if pack_type not in self.pack_prices:
                self.send_message_image(sender, file_queue, f"Invalid pack type: {pack_type}", "FIFA - Error", cache, user_id)
                return ""

            price = self.pack_prices[pack_type]['casino_coins']
            casino_balance = user.get('balance', 0)

            if casino_balance < price:
                self.send_message_image(sender, file_queue, f"Not enough coins!\n\nPrice: {price} coins\nYour balance: {casino_balance} coins", "FIFA - Insufficient Funds", cache, user_id)
                return ""

            cards = self.pack_opener.open_pack(pack_type)
            if not cards:
                self.send_message_image(sender, file_queue, f"Error opening {pack_type} pack. Try again later.", "FIFA - Error", cache, user_id)
                return ""

            new_balance = casino_balance - price
            self.update_user_balance(user_id, new_balance)

            collection = self.get_user_collection(user_id)
            card_ids = collection.add_cards(cards)

            fifa_coins = self.get_fifa_coins(user_id)

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            temp_path = os.path.join(self.results_folder, f"fifa_pack_{user_id}_{timestamp}_temp.png")
            final_path = os.path.join(self.results_folder, f"fifa_pack_{user_id}_{timestamp}.png")

            self.image_generator.generate_pack_image(cards, temp_path, fifa_coins)
            self.apply_background(temp_path, user_id, final_path)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            file_queue.put(final_path)
            return ""

        elif cmd == "cards" or cmd == "c":
            collection = self.get_user_collection(user_id)

            page = 1
            sort_by = 'new'
            position = None
            valid_positions = ['GK', 'CB', 'LB', 'RB', 'CDM', 'CM', 'CAM', 'LM', 'RM', 'LW', 'RW', 'ST', 'CF']

            if len(args) > 1:
                for arg in args[1:]:
                    arg_lower = arg.lower()
                    arg_upper = arg.upper()

                    if arg.isdigit():
                        page = int(arg)
                    elif arg_lower in ['new', 'old', 'rating', 'price', 'name']:
                        sort_by = arg_lower
                    elif arg_upper in valid_positions:
                        position = arg_upper

            cards, total_pages, total_cards = collection.get_filtered_cards(sort_by=sort_by, position=position, page=page, per_page=10)

            if not cards:
                self.send_message_image(sender, file_queue, "Your collection is empty!\n\nOpen a pack: /fifa open bronze/silver/gold", "FIFA Collection", cache, user_id)
                return ""

            fifa_coins = self.get_fifa_coins(user_id)
            temp_path = os.path.join(self.results_folder, f"fifa_collection_{user_id}_page{page}_temp.png")
            final_path = os.path.join(self.results_folder, f"fifa_collection_{user_id}_page{page}.png")

            self.image_generator.generate_collection_image(cards, page, total_pages, total_cards, sort_by, position, temp_path, fifa_coins)
            self.apply_background(temp_path, user_id, final_path)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            file_queue.put(final_path)
            return ""

        elif cmd == "formations" or cmd == "form" or cmd == "formation" or cmd == "f":
            page = 1
            if len(args) > 1 and args[1].isdigit():
                page = int(args[1])
            elif len(args) > 2 and args[1].lower() == "set":
                try:
                    formation_id = int(args[2])
                    formation = self.formation_manager.get_formation(formation_id)
                    if not formation:
                        self.send_message_image(sender, file_queue, f"Formation with ID {formation_id} not found.", "FIFA - Error", cache, user_id)
                        return ""

                    team = self.get_user_team(user_id)
                    team.set_formation(formation_id)

                    self.send_message_image(sender, file_queue, f" Active formation set to: {formation.display_name}", "FIFA - Formation Set", cache, user_id)
                    return
                except ValueError:
                    self.send_message_image(sender, file_queue, "Usage: /fifa formations set <id>", "FIFA - Error", cache, user_id)
                    return

            formations, total_pages = self.formation_manager.get_formations_page(page=page, per_page=9)

            if not formations:
                self.send_message_image(sender, file_queue, "No formations available.", "FIFA - Error", cache, user_id)
                return

            team = self.get_user_team(user_id)
            fifa_coins = self.get_fifa_coins(user_id)
            temp_path = os.path.join(self.results_folder, f"fifa_formations_{user_id}_page{page}_temp.png")
            final_path = os.path.join(self.results_folder, f"fifa_formations_{user_id}_page{page}.png")

            self.image_generator.generate_formations_image(formations, page, total_pages, team.active_formation_id, self.formations_folder, temp_path, fifa_coins)
            self.apply_background(temp_path, user_id, final_path)

            if os.path.exists(temp_path):
                os.remove(temp_path)

            file_queue.put(final_path)
            return ""

        elif cmd == "team" or cmd == "t":
            team = self.get_user_team(user_id)
            collection = self.get_user_collection(user_id)

            if len(args) == 1:
                formation = self.formation_manager.get_formation(team.active_formation_id)
                if not formation:
                    self.send_message_image(sender, file_queue, "No active formation. Select one with `/fifa formations set <id>`", "FIFA - Error", cache, user_id)
                    return

                formation_image_path = self.formation_manager.get_formation_image_path(formation)
                if not os.path.exists(formation_image_path):
                    self.send_message_image(sender, file_queue, f"Formation image not found: {formation.filename}", "FIFA - Error", cache, user_id)
                    return

                fifa_coins = self.get_fifa_coins(user_id)
                temp_path = os.path.join(self.results_folder, f"fifa_team_{user_id}_temp.png")
                final_path = os.path.join(self.results_folder, f"fifa_team_{user_id}.png")

                self.team_image_generator.generate_team_preview(formation, formation_image_path, team, collection, temp_path, fifa_coins)
                self.apply_background(temp_path, user_id, final_path)

                if os.path.exists(temp_path):
                    os.remove(temp_path)

                file_queue.put(final_path)
                return

            elif len(args) >= 4 and args[1].lower() == "set":
                try:
                    slot_id = int(args[2])
                    card_id = int(args[3])
                except ValueError:
                    self.send_message_image(sender, file_queue, "Slot and card ID must be numbers.", "FIFA - Error", cache, user_id)
                    return ""

                formation = self.formation_manager.get_formation(team.active_formation_id)
                if not formation:
                    self.send_message_image(sender, file_queue, "No active formation. Select one first.", "FIFA - Error", cache, user_id)
                    return ""

                grid = formation.get_position_grid()
                total_slots = sum(len(line) for line in grid)

                if slot_id < 1 or slot_id > total_slots:
                    self.send_message_image(sender, file_queue, f"Invalid slot. This formation has slots 1-{total_slots}.", "FIFA - Error", cache, user_id)
                    return ""

                card = collection.get_card(card_id)
                if not card:
                    self.send_message_image(sender, file_queue, f"Card with ID {card_id} not found in your collection.", "FIFA - Error", cache, user_id)
                    return ""

                success, message = team.set_player(slot_id, card_id)

                if not success:
                    self.send_message_image(sender, file_queue, message, "FIFA - Team Update", cache, user_id)
                    return ""

                self.send_message_image(sender, file_queue, f" {message}", "FIFA - Team Update", cache, user_id)


                team = self.get_user_team(user_id)
                collection = self.get_user_collection(user_id)

                formation_image_path = self.formation_manager.get_formation_image_path(formation)
                fifa_coins = self.get_fifa_coins(user_id)
                temp_path = os.path.join(self.results_folder, f"fifa_team_{user_id}_temp.png")
                final_path = os.path.join(self.results_folder, f"fifa_team_{user_id}.png")

                self.team_image_generator.generate_team_preview(formation, formation_image_path, team, collection, temp_path, fifa_coins)
                self.apply_background(temp_path, user_id, final_path)

                if os.path.exists(temp_path):
                    os.remove(temp_path)

                file_queue.put(final_path)
                return

            elif len(args) >= 3 and args[1].lower() == "remove":
                try:
                    slot_id = int(args[2])
                except ValueError:
                    self.send_message_image(sender, file_queue, "Slot must be a number.", "FIFA - Error", cache, user_id)
                    return

                team.remove_player(slot_id)
                self.send_message_image(sender, file_queue, f" Player removed from slot {slot_id}.", "FIFA - Team Update", cache, user_id)

                formation = self.formation_manager.get_formation(team.active_formation_id)
                if formation:
                    formation_image_path = self.formation_manager.get_formation_image_path(formation)
                    fifa_coins = self.get_fifa_coins(user_id)
                    temp_path = os.path.join(self.results_folder, f"fifa_team_{user_id}_temp.png")
                    final_path = os.path.join(self.results_folder, f"fifa_team_{user_id}.png")

                    self.team_image_generator.generate_team_preview(formation, formation_image_path, team, collection, temp_path, fifa_coins)
                    self.apply_background(temp_path, user_id, final_path)

                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                    file_queue.put(final_path)
                return

            else:
                self.send_message_image(sender, file_queue, "Usage:\n/fifa team - Show your team\n/fifa team set <slot> <card_id> - Put player in slot\n/fifa team remove <slot> - Remove player from slot", "FIFA - Team Help", cache, user_id)
                return

        elif cmd == "sell" or cmd == "s":
            if len(args) < 2:
                self.send_message_image(sender, file_queue, "Usage: /fifa sell <card_id>\n/fifa sell 1,2,3\n/fifa sell 12 23 4", "FIFA - Sell Cards", cache, user_id)
                return ""

            collection = self.get_user_collection(user_id)

            card_ids = []
            for arg in args[1:]:
                if ',' in arg:
                    for part in arg.split(','):
                        part = part.strip()
                        if part.isdigit():
                            card_ids.append(int(part))
                elif arg.isdigit():
                    card_ids.append(int(arg))

            if not card_ids:
                self.send_message_image(sender, file_queue, "No valid card IDs provided.", "FIFA - Error", cache, user_id)
                return ""

            cards_to_sell = []
            for card_id in card_ids:
                card = collection.get_card(card_id)
                if card:
                    cards_to_sell.append(card)
                else:
                    self.send_message_image(sender, file_queue, f"Card with ID {card_id} not found in your collection.", "FIFA - Error", cache, user_id)
                    return ""

            total_value = sum(card.price for card in cards_to_sell)
            removed = collection.remove_cards(card_ids)
            new_fifa_coins = self.add_fifa_coins(user_id, total_value)

            msg = f" **Sold {len(removed)} cards!**\n\nTotal value: {total_value} FIFA coins\nNew FIFA coins balance: {new_fifa_coins}\n\nSold cards:\n"
            for card in removed:
                if hasattr(card, 'id') and card.id:
                    msg += f"• [{card.id}] {card.player_name} - {card.price} coins\n"
                else:
                    msg += f"• {card.player_name} - {card.price} coins\n"

            self.send_message_image(sender, file_queue, msg, "FIFA - Sale Complete", cache, user_id)
            return ""

        elif cmd == "balance" or cmd == "coins":
            fifa_coins = self.get_fifa_coins(user_id)
            casino_balance = user.get('balance', 0)

            msg = f"**Your FIFA Balance**\n\n FIFA coins: {fifa_coins}\n Casino coins: {casino_balance}\n\nYou can buy packs with casino coins using /fifa buy"
            self.send_message_image(sender, file_queue, msg, "FIFA Balance", cache, user_id)
            return ""

        elif cmd == "league" or cmd == "l":
            if len(args) == 1:
                msg = "**FIFA League - Play Against Other Players!**\n\n"
                msg += "**Commands:**\n"
                msg += "/fc league join - Join the queue to find an opponent\n"
                msg += "/fc league leave - Leave the queue\n"
                msg += "/fc league players - Show players waiting for match\n"
                msg += "/fc league cancel - Cancel your current match\n\n"
                msg += "**How it works:**\n"
                msg += "1. Use /fc league join to enter the queue\n"
                msg += "2. System will match you with another player\n"
                msg += "3. Match rewards are based on team strength:\n"
                msg += "   - Weaker team gets higher reward for winning (100-300%)\n"
                msg += "   - Draw gives 75% of base reward to both players\n"
                msg += "   - Base reward: 100 coins\n\n"
                msg += "**Requirements:**\n"
                msg += "- Complete your team (all slots filled)\n"
                msg += "- Set an active formation"

                self.send_message_image(sender, file_queue, msg, "FIFA League", cache, user_id)
                return ""

            subcmd = args[1].lower()

            if subcmd == "join":


                if not self.daily_limits.can_play_match(user_id, 'pvp'):
                    remaining = self.daily_limits.get_remaining_matches(user_id)
                    msg = f"You have already played your daily PvP match!\n\n"
                    msg += f"Daily limits:\n"
                    msg += f"• AI matches: {remaining.get('ai', 0)} remaining\n"
                    msg += f"• PvP matches: {remaining.get('pvp', 0)} remaining\n\n"
                    msg += f"Limits reset at midnight!"
                    self.send_message_image(sender, file_queue, msg, "FIFA League - Daily Limit Reached", cache, user_id)
                    return ""


                team = self.get_user_team(user_id)
                formation = self.formation_manager.get_formation(team.active_formation_id)

                if not formation:
                    self.send_message_image(sender, file_queue, "You need to set a formation first!\nUse /fc formations set <id>", "FIFA League - Error", cache, user_id)
                    return ""

                grid = formation.get_position_grid()
                total_slots = sum(len(line) for line in grid)
                filled_slots = len([s for s in team.players.values() if s is not None])

                if filled_slots < total_slots:
                    self.send_message_image(sender, file_queue, f"Your team is incomplete! Need {total_slots} players, you have {filled_slots}.\nUse /fc team set <slot> <card_id> to fill your team.", "FIFA League - Error", cache, user_id)
                    return ""


                for match in self.league_manager.active_matches.values():
                    if match.player1_id == user_id or match.player2_id == user_id:
                        self.send_message_image(sender, file_queue, "You already have an active match! Wait for it to finish or use /fc league cancel", "FIFA League - Error", cache, user_id)
                        return ""

                collection = self.get_user_collection(user_id)


                stats = self._calculate_team_stats_for_match(team, formation, collection)
                team_rating = stats['overall']


                self.league_manager.add_ready_player(user_id, team, formation, collection)


                opponent_id, opponent_data = self.league_manager.find_match(user_id)

                if opponent_id:
                    player1_data = self.league_manager.players_ready.get(user_id)
                    player2_data = opponent_data

                    self.league_manager.remove_ready_player(user_id)
                    self.league_manager.remove_ready_player(opponent_id)


                    player1_name = self._get_user_name(user_id)
                    player2_name = self._get_user_name(opponent_id)

                    match = self.league_manager.create_match(
                        user_id, opponent_id,
                        player1_data, player2_data,
                        player1_name, player2_name,
                        self
                    )


                    self._send_league_match_preview(sender, file_queue, match, cache, user_id, opponent_id)


                    msg = f"**Match Found!**\n\n"
                    msg += f"Your opponent: {player2_name}\n"
                    msg += f"**Rewards:**\n"
                    msg += f"• If YOU win: {match.player1_reward} coins\n"
                    msg += f"• If opponent wins: {match.player2_reward} coins\n"
                    msg += f"• If draw: {match.draw_reward} coins each\n\n"
                    msg += f"Match will start automatically in 10 seconds!"

                    self.send_message_image(sender, file_queue, msg, "FIFA League - Match Found", cache, user_id)


                    def run_player_match():
                        time.sleep(10)
                        self._run_player_match_sync(sender, file_queue, match, cache, user_id, opponent_id)

                    thread = threading.Thread(target=run_player_match, daemon=True)
                    thread.start()
                    self.league_manager.match_threads[match.match_id] = thread

                else:

                    self.send_message_image(sender, file_queue, "Searching for opponent...\n\nUse /fc league leave to cancel search.", "FIFA League - Searching", cache, user_id)

                return ""

            elif subcmd == "leave":
                self.league_manager.remove_ready_player(user_id)
                self.send_message_image(sender, file_queue, "You left the queue.", "FIFA League - Left", cache, user_id)
                return ""

            elif subcmd == "players":
                available = self._get_available_players(user_id)

                if not available:
                    msg = "No players currently waiting for match.\n\nUse /fc league join to enter the queue!"
                else:
                    msg = f"**Players waiting ({len(available)}):**\n\n"
                    for p in available:
                        msg += f"• {p['name']} - Rating: {p['rating']}\n"

                self.send_message_image(sender, file_queue, msg, "FIFA League - Players", cache, user_id)
                return ""

            elif subcmd == "cancel":

                for match_id, match in list(self.league_manager.active_matches.items()):
                    if match.player1_id == user_id or match.player2_id == user_id:
                        self.league_manager.remove_match(match_id)
                        self.send_message_image(sender, file_queue, "Your match has been cancelled.", "FIFA League - Cancelled", cache, user_id)
                        return

                self.send_message_image(sender, file_queue, "No active match found.", "FIFA League", cache, user_id)
                return

            else:
                self.send_message_image(sender, file_queue, f"Unknown league command: {subcmd}\n\nUse /fc league for help", "FIFA League - Error", cache, user_id)
                return

        elif cmd == "match" or cmd == "m":
            if len(args) == 1:
                self.send_message_image(sender, file_queue,
                    "**FIFA Match**\n\n/fifa match start - Start a new match\n\n**Match Rewards:**\n• Win: 100% of base reward\n• Draw: 50% of base reward\n• Loss: 10% of base reward\n\nBase reward depends on your team rating, chemistry, and positioning",
                    "FIFA Match", cache, user_id)
                return ""

            subcmd = args[1].lower()

            if subcmd == "start":
                for match in self.match_manager.active_matches.values():
                    if match.user_id == user_id and match.status != MatchStatus.FINISHED:
                        self.send_message_image(sender, file_queue,
                            "You already have an active match! The match will update automatically every 15 minutes.",
                            "FIFA - Match Active", cache, user_id)
                        return ""

                if not self.daily_limits.can_play_match(user_id, 'ai'):
                    remaining = self.daily_limits.get_remaining_matches(user_id)
                    msg = f"You have already played your daily AI match!\n\n"
                    msg += f"Daily limits:\n"
                    msg += f"• AI matches: {remaining.get('ai', 0)} remaining\n"
                    msg += f"• PvP matches: {remaining.get('pvp', 0)} remaining\n\n"
                    msg += f"Limits reset at midnight!"
                    self.send_message_image(sender, file_queue, msg, "FIFA - Daily Limit Reached", cache, user_id)
                    return ""

                team = self.get_user_team(user_id)
                formation = self.formation_manager.get_formation(team.active_formation_id)
                if not formation:
                    self.send_message_image(sender, file_queue,
                        "You need to set a formation first!\nUse /fifa formations set <id>",
                        "FIFA - Match Error", cache, user_id)
                    return ""

                grid = formation.get_position_grid()
                total_slots = sum(len(line) for line in grid)
                filled_slots = len([s for s in team.players.values() if s is not None])
                if filled_slots < total_slots:
                    self.send_message_image(sender, file_queue,
                        f"Your team is incomplete! Need {total_slots} players, you have {filled_slots}.\nUse /fifa team set <slot> <card_id> to fill your team.",
                        "FIFA - Match Error", cache, user_id)
                    return ""

                collection = self.get_user_collection(user_id)
                match = self.match_manager.create_match(user_id, team, formation, collection, self)
                fifa_coins = self.get_fifa_coins(user_id)

                preview_path = os.path.join(self.results_folder, f"fifa_match_preview_{user_id}.png")
                self.team_image_generator.match = match
                self.team_image_generator.generate_match_preview_image(
                    team, formation, collection, match.opponent, match.opponent_formation,
                    preview_path, fifa_coins, cache, user_id,
                    opponent_logo=match.opponent_logo
                )

                final_preview = os.path.join(self.results_folder, f"fifa_match_preview_{user_id}_final.png")
                self.apply_background(preview_path, user_id, final_preview)
                if os.path.exists(preview_path):
                    os.remove(preview_path)
                file_queue.put(final_preview)

                match.generate_match_script_with_6_fragments()

                def schedule_match_with_6_updates():
                    for i in range(6):
                        time.sleep(15 * 60)
                        self._send_match_fragment_sync(sender, file_queue, match, i, cache, user_id)

                    time.sleep(3)
                    self._finish_match_sync(sender, file_queue, match, cache, user_id)

                thread = threading.Thread(target=schedule_match_with_6_updates, daemon=True)
                thread.start()
                self.match_manager.match_threads[match.match_id] = thread
                self.daily_limits.increment_match(user_id, 'ai')

                self.send_message_image(sender, file_queue,
                    "Match Started!\n\nUpdates will be sent automatically every 15 minutes\n\nGood luck!",
                    "FIFA Match Started", cache, user_id)

                return ""

            else:
                self.send_message_image(sender, file_queue,
                    f"Unknown match command: {subcmd}\n\nUse /fifa match start to begin a match",
                    "FIFA - Error", cache, user_id)
                return ""

        else:
            self.send_message_image(sender, file_queue, f"Unknown command: {cmd}\n\nUse /fifa for help", "FIFA - Error", cache, user_id)
            return ""

def register():
    logger.info("[FIFA] Registering FIFA plugin")
    plugin = FifaPlugin()
    return {
        "name": "fifa",
        "aliases": ["/f", "/fifa", "/fc"],
        "description": "FIFA Card Game - Open Packs, Collect Cards, Build Your Team\n\n**Packs:**\n• Bronze: 750 FIFA coins / 75 casino coins\n• Silver: 5000 FIFA coins / 150 casino coins\n• Gold: 10000 FIFA coins / 300 casino coins\n\n**Team Building:**\n• Choose formation with `/fifa formations`\n• Build squad with `/fifa team set <slot> <card_id>`\n• Chemistry links: Green (perfect), Yellow (strong), Orange (weak), Red (none)\n\n**Commands:**\n/fifa packs - Show available packs\n/fifa open bronze/silver/gold - Open pack\n/fifa buy bronze/silver/gold - Buy with casino coins\n/fifa cards - Show collection\n/fifa formations - Show formations\n/fifa team - Show your team with chemistry\n/fifa sell <id> - Sell a card\n/fifa match start - Start a match (updates automatically)\n/fifa balance - Show FIFA coins\n\n**Match Rewards:**\n• Win: 100% of base reward\n• Draw: 50% of base reward\n• Loss: 10% of base reward",
        "execute": plugin.execute_game
    }