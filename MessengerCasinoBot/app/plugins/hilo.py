import os
import random
import textwrap
import time
import logging
from typing import Dict, List, Optional

from PIL import Image, ImageDraw

from base_game_plugin import BaseGamePlugin
from logger import logger

# Dodajmy oddzielny logger dla hilo
hilo_logger = logging.getLogger("hilo_debug")
hilo_logger.setLevel(logging.DEBUG)
if not hilo_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - HILO DEBUG - %(message)s'))
    hilo_logger.addHandler(handler)


class HiLoGame:
    HOUSE_EDGE = 0.02

    def __init__(
        self,
        user_id: str,
        sender_name: str,
        bet: int,
        deck: Optional[List[str]] = None,
        current_card: Optional[str] = None,
        streak: int = 0,
        last_card: Optional[str] = None,
        last_direction: Optional[str] = None,
        last_result: Optional[str] = None,
        message: Optional[str] = None,
        status: Optional[str] = None,
        multiplier: Optional[float] = None,
        next_guess_card: Optional[str] = None,
    ):
        self.user_id = str(user_id)
        self.sender_name = sender_name
        self.bet = bet
        self.deck = deck[:] if deck else self._build_deck()
        self.current_card = current_card or self._draw_card()  # Lewa strona (do wyświetlenia)
        self.streak = streak
        self.last_card = last_card  # Prawa strona (wynik)
        self.last_direction = last_direction
        self.last_result = last_result
        self.game_status = status or "waiting_guess"
        self.message = message or "Guess if the next card will be higher or lower."
        self.multiplier = multiplier if multiplier is not None else 1.0
        self.next_guess_card = next_guess_card  # Karta na którą będzie następne typowanie
        
        hilo_logger.debug(f"=== GAME INIT ===")
        hilo_logger.debug(f"user_id: {user_id}")
        hilo_logger.debug(f"current_card: {self.current_card}")
        hilo_logger.debug(f"last_card: {self.last_card}")
        hilo_logger.debug(f"next_guess_card: {self.next_guess_card}")
        hilo_logger.debug(f"game_status: {self.game_status}")
        hilo_logger.debug(f"deck size: {len(self.deck)}")

    def _build_deck(self) -> List[str]:
        suits = ["S", "H", "D", "C"]
        # As jako najmniejszy (1), Król jako największy (13)
        values = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        deck = [f"{value}{suit}" for suit in suits for value in values]
        random.shuffle(deck)
        return deck

    def _draw_card(self) -> str:
        if not self.deck:
            hilo_logger.debug("Deck empty, rebuilding...")
            self.deck = self._build_deck()
            random.shuffle(self.deck)
        card = self.deck.pop()
        hilo_logger.debug(f"Drew card: {card}, remaining deck size: {len(self.deck)}")
        return card

    def _card_rank(self, card: str) -> int:
        # As = 1, 2=2, ..., 10=10, J=11, Q=12, K=13
        rank_map = {"A": 1, "J": 11, "Q": 12, "K": 13}
        value = card[:-1]
        if value.isdigit():
            return int(value)
        return rank_map.get(value, 0)

    def _calculate_direction_multiplier(self, probability: float) -> Optional[float]:
        if probability <= 0:
            return None
        return (1.0 / probability) * (1.0 - self.HOUSE_EDGE)

    def _calculate_direction_info(self) -> Dict[str, Dict[str, Optional[float]]]:
        card_for_calc = self.next_guess_card if self.next_guess_card else self.current_card
        
        info = {"high": {}, "low": {}, "same": {}}
        total = len(self.deck)
        if not card_for_calc or total == 0:
            for direction in info:
                info[direction] = {
                    "prob": 0.0,
                    "multiplier": None,
                    "next_total": self.get_multiplier(),
                }
            return info

        counts: Dict[int, int] = {}
        for card in self.deck:
            rank = self._card_rank(card)
            counts[rank] = counts.get(rank, 0) + 1

        current_rank = self._card_rank(card_for_calc)
        higher = sum(cnt for rank, cnt in counts.items() if rank > current_rank)
        lower = sum(cnt for rank, cnt in counts.items() if rank < current_rank)
        same = counts.get(current_rank, 0)

        for direction, value in (("high", higher), ("low", lower), ("same", same)):
            if value <= 0:
                info[direction] = {
                    "prob": 0.0,
                    "multiplier": None,
                    "next_total": self.get_multiplier(),
                }
                continue

            prob = value / total
            stage_mult = self._calculate_direction_multiplier(prob)
            
            # KURWA MNOŻENIE A NIE DODAWANIE
            next_total = self.get_multiplier()
            if stage_mult:
                next_total *= stage_mult

            info[direction] = {
                "prob": prob,
                "multiplier": stage_mult,
                "next_total": next_total,
            }

        return info

    def _compare(self, prev_card: str, next_card: str) -> str:
        prev_rank = self._card_rank(prev_card)
        next_rank = self._card_rank(next_card)
        hilo_logger.debug(f"Compare: {prev_card}({prev_rank}) vs {next_card}({next_rank})")
        if next_rank > prev_rank:
            return "high"
        if next_rank < prev_rank:
            return "low"
        return "tie"

    def _normalize_direction(self, direction: str) -> Optional[str]:
        if not direction:
            return None
        direction = direction.lower()
        if direction in ("high", "h", "up", "higher"):
            return "high"
        if direction in ("low", "l", "down", "lower"):
            return "low"
        if direction in ("same", "s", "equal", "tie"):
            return "same"
        return None

    def make_guess(self, direction: str) -> Dict[str, Optional[str]]:
        hilo_logger.debug(f"=== MAKE GUESS: {direction} ===")
        hilo_logger.debug(f"Before guess - current_card: {self.current_card}, last_card: {self.last_card}, next_guess_card: {self.next_guess_card}")
        
        normalized = self._normalize_direction(direction)
        if not normalized:
            return {"valid": False, "reason": "direction"}

        if self.game_status != "waiting_guess":
            return {"valid": False, "reason": "finished"}

        if self.next_guess_card:
            guess_card = self.next_guess_card
            hilo_logger.debug(f"Typujemy na przygotowaną kartę: {guess_card}")
        else:
            guess_card = self.current_card
            hilo_logger.debug(f"Typujemy na current_card: {guess_card}")
        
        new_card = self._draw_card()
        hilo_logger.debug(f"Wylosowano: {new_card}")
        
        comparison = self._compare(guess_card, new_card)
        
        self.last_card = new_card
        
        direction_info = self._calculate_direction_info()
        direction_data = direction_info.get(normalized)
        stage_multiplier = direction_data.get("multiplier") if direction_data else None
        
        has_low = direction_info.get("low", {}).get("multiplier") is not None
        has_high = direction_info.get("high", {}).get("multiplier") is not None
        
        is_extreme = (has_high and not has_low) or (has_low and not has_high)
        
        if comparison == "tie":
            if normalized == "same":
                self.streak += 1
                self.next_guess_card = guess_card
                if stage_multiplier:
                    self.multiplier *= stage_multiplier
                self.last_result = "win"
                self.message = (
                    f"Correct! {self._format_card_name(new_card)} is the same. "
                    f"Streak: {self.streak} (x{self.multiplier:.2f})"
                )
                hilo_logger.debug(f"WIN SAME - next_guess_card: {self.next_guess_card}")
                return {"valid": True, "result": "win", "card": new_card}
            elif not is_extreme:
                self.streak += 1
                self.next_guess_card = guess_card
                if stage_multiplier:
                    self.multiplier *= stage_multiplier
                self.last_result = "win"
                self.message = (
                    f"Correct! {self._format_card_name(new_card)} is the same. "
                    f"Streak: {self.streak} (x{self.multiplier:.2f})"
                )
                hilo_logger.debug(f"WIN SAME (middle card, guessed {normalized}) - next_guess_card: {self.next_guess_card}")
                return {"valid": True, "result": "win", "card": new_card}
            else:
                self.game_status = "finished"
                self.last_result = "tie"
                self.message = (
                    f"Tie! {self._format_card_name(new_card)} matches "
                    f"{self._format_card_name(guess_card)}. You lose your bet."
                )
                hilo_logger.debug(f"LOSS TIE (extreme card)")
                return {"valid": True, "result": "tie", "card": new_card}

        if comparison == normalized:
            self.streak += 1
            self.next_guess_card = new_card
            
            if stage_multiplier:
                self.multiplier *= stage_multiplier
            
            self.last_result = "win"
            self.message = (
                f"Correct! {self._format_card_name(new_card)} is {normalized}. "
                f"Streak: {self.streak} (x{self.multiplier:.2f})"
            )
            hilo_logger.debug(f"WIN - następne typowanie będzie na: {self.next_guess_card}")
            return {"valid": True, "result": "win", "card": new_card}

        self.game_status = "finished"
        self.last_result = "loss"
        self.message = (
            f"Wrong! {self._format_card_name(new_card)} is {comparison}, not {normalized}. "
            f"You lose your bet of {self.bet}."
        )
        hilo_logger.debug(f"LOSS")
        return {"valid": True, "result": "loss", "card": new_card}

    def prepare_next_round(self):
        """Przygotuj następną rundę - przesuń karty"""
        if self.next_guess_card:
            self.current_card = self.next_guess_card
            self.next_guess_card = None
            self.last_card = None  # Resetuj prawą stronę (będzie zakryta)
            hilo_logger.debug(f"Następna runda - typujemy na: {self.current_card}")
            return True
        return False

    def _format_card_name(self, card_code: str) -> str:
        value_map = {"A": "Ace", "J": "Jack", "Q": "Queen", "K": "King"}
        suit_map = {"S": "Spades", "H": "Hearts", "D": "Diamonds", "C": "Clubs"}
        value = card_code[:-1]
        suit = card_code[-1]
        value_name = value_map.get(value, value)
        suit_name = suit_map.get(suit, suit)
        return f"{value_name} of {suit_name}"

    def collect(self) -> int:
        if self.streak == 0 or self.game_status != "waiting_guess":
            return 0
        payout = int(self.bet * self.get_multiplier())
        self.game_status = "finished"
        self.last_result = "collect"
        self.message = (
            f"Cash out! {self.streak} correct guess(es) locked in x{self.get_multiplier():.2f}. "
            f"You won {payout}!"
        )
        return payout

    def get_multiplier(self) -> float:
        return self.multiplier

    def serialize(self) -> Dict:
        return {
            "bet": self.bet,
            "deck": self.deck,
            "current_card": self.current_card,
            "last_card": self.last_card,
            "streak": self.streak,
            "last_direction": self.last_direction,
            "last_result": self.last_result,
            "status": self.game_status,
            "message": self.message,
            "multiplier": self.multiplier,
            "next_guess_card": self.next_guess_card,
        }

    @classmethod
    def deserialize(cls, user_id: str, sender_name: str, data: Dict) -> "HiLoGame":
        return cls(
            user_id=user_id,
            sender_name=sender_name,
            bet=data.get("bet", 0),
            deck=data.get("deck", []),
            current_card=data.get("current_card"),
            streak=data.get("streak", 0),
            last_card=data.get("last_card"),
            last_direction=data.get("last_direction"),
            last_result=data.get("last_result"),
            status=data.get("status"),
            message=data.get("message"),
            multiplier=data.get("multiplier", 1.0),
            next_guess_card=data.get("next_guess_card"),
        )

    def get_render_state(self) -> Dict:
        # Karta do wyświetlenia na lewo: current_card
        # Karta do wyświetlenia na prawo: last_card
        state = {
            "current_card": self.current_card,
            "last_card": self.last_card,
            "message": self.message,
            "streak": self.streak,
            "status": self.game_status,
            "last_direction": self.last_direction,
            "last_result": self.last_result,
            "bet": self.bet,
            "multiplier": self.get_multiplier(),
            "direction_info": self._calculate_direction_info(),
        }
        hilo_logger.debug(f"=== RENDER STATE ===")
        hilo_logger.debug(f"current_card: {state['current_card']}")
        hilo_logger.debug(f"last_card: {state['last_card']}")
        hilo_logger.debug(f"status: {state['status']}")
        return state


class HiLoCardRenderer:
    def __init__(self, assets_folder: str, text_renderer):
        self.assets_folder = assets_folder
        self.text_renderer = text_renderer
        self.card_mapping = self._create_card_mapping()
        self.card_images: Dict[str, Image.Image] = {}
        self.card_back: Optional[Image.Image] = None
        self._load_cards()

    def _create_card_mapping(self) -> Dict[str, str]:
        mapping = {}
        suit_map = {
            "S": "spades",
            "H": "hearts",
            "D": "diamonds",
            "C": "clubs",
        }
        value_map = {
            "A": "A",
            "2": "02",
            "3": "03",
            "4": "04",
            "5": "05",
            "6": "06",
            "7": "07",
            "8": "08",
            "9": "09",
            "10": "10",
            "J": "J",
            "Q": "Q",
            "K": "K",
        }
        for suit_symbol, suit_name in suit_map.items():
            for value_symbol, value_code in value_map.items():
                key = f"{value_symbol}{suit_symbol}"
                filename = f"card_{suit_name}_{value_code}.png"
                mapping[key] = filename
        return mapping

    def _load_cards(self):
        for code, filename in self.card_mapping.items():
            card_path = os.path.join(self.assets_folder, filename)
            if os.path.exists(card_path):
                self.card_images[code] = Image.open(card_path).convert("RGBA")
        back_path = os.path.join(self.assets_folder, "card_back.png")
        if os.path.exists(back_path):
            self.card_back = Image.open(back_path).convert("RGBA")

    def _create_placeholder(self, width: int, height: int) -> Image.Image:
        placeholder = Image.new("RGBA", (width, height), (30, 40, 60, 230))
        draw = ImageDraw.Draw(placeholder)
        draw.rounded_rectangle([0, 0, width - 1, height - 1], radius=12, outline=(80, 80, 120, 255), width=3)
        return placeholder

    def _paste_card(self, canvas: Image.Image, card_code: Optional[str], position: tuple, size: tuple, side: str = ""):
        card_img = None
        if card_code and card_code in self.card_images:
            card_img = self.card_images[card_code]
            hilo_logger.debug(f"Pasting card {card_code} on {side} side")
        elif self.card_back:
            card_img = self.card_back
            hilo_logger.debug(f"Pasting back card on {side} side")
        else:
            card_img = self._create_placeholder(*size)
            hilo_logger.debug(f"Pasting placeholder on {side} side")

        if card_img:
            resized = card_img.resize(size, Image.Resampling.LANCZOS)
        else:
            resized = self._create_placeholder(*size)

        canvas.alpha_composite(resized, position)

    def generate_table_image(self, game_state: Dict, output_path: str, user_background_path: Optional[str] = None, font_scale: float = 1.0):
        hilo_logger.debug(f"=== GENERATE TABLE IMAGE ===")
        hilo_logger.debug(f"Game state current_card: {game_state.get('current_card')}")
        hilo_logger.debug(f"Game state last_card: {game_state.get('last_card')}")
        
        width = 700
        height = 520
        
        card_width = 200
        card_height = int(card_width * 1.2)
        cards_y = 120
        
        last_result = game_state.get("last_result")
        game_status = game_state.get("status")

        # Tło zmienia się natychmiast po wyniku
        if last_result == "win":
            bg_color = (40, 80, 40, 255)  # Zielone tło po wygranej
        elif last_result in ("loss", "tie"):
            bg_color = (80, 40, 40, 255)  # Czerwone tło po przegranej lub remisie
        else:
            bg_color = (12, 16, 28, 255)  # Domyślne #0C101C
        
        table_img = Image.new("RGBA", (width, height), bg_color)
        
        if user_background_path and os.path.exists(user_background_path) and game_status != "finished":
            try:
                user_bg = Image.open(user_background_path).convert("RGBA")
                user_bg = user_bg.resize((width, height), Image.Resampling.LANCZOS)
                overlay = Image.new("RGBA", (width, height), (8, 10, 18, 200))
                blended = Image.alpha_composite(user_bg, overlay)
                table_img = Image.alpha_composite(blended, table_img)
            except Exception as exc:
                logger.warning(f"[HiLo] Background load failed: {exc}")

        draw = ImageDraw.Draw(table_img)
        panel_margin = 30
        panel_rect = [panel_margin, 40, width - panel_margin, height - 70]
        draw.rounded_rectangle(panel_rect, radius=25, fill=(18, 24, 40, 220))

        current_pos = (
            int(width * 0.20 - card_width / 2),
            cards_y,
        )
        next_pos = (
            int(width * 0.80 - card_width / 2),
            cards_y,
        )

        # CURRENT CARD (lewa)
        current_card = game_state.get("current_card")
        hilo_logger.debug(f"Rendering LEFT (CURRENT) card: {current_card}")
        self._paste_card(
            table_img,
            current_card,
            current_pos,
            (card_width, card_height),
            side="LEFT"
        )

        # NEXT CARD (prawa)
        next_card = game_state.get("last_card")
        hilo_logger.debug(f"Rendering RIGHT (NEXT) card: {next_card}")
        if next_card:
            self._paste_card(
                table_img,
                next_card,
                next_pos,
                (card_width, card_height),
                side="RIGHT"
            )
        else:
            hilo_logger.debug(f"No last_card, showing back card on RIGHT side")
            self._paste_card(
                table_img,
                None,
                next_pos,
                (card_width, card_height),
                side="RIGHT"
            )

        # Podpisy pod kartami
        label_font_size = max(16, int(18 * font_scale))
        label_color = (235, 235, 245, 255)
        current_label = self.text_renderer.render_text(
            "CURRENT CARD",
            font_size=label_font_size,
            color=label_color,
            stroke_width=1,
            stroke_color=(0, 0, 0, 180),
        )
        next_label = self.text_renderer.render_text(
            "NEXT CARD",
            font_size=label_font_size,
            color=label_color,
            stroke_width=1,
            stroke_color=(0, 0, 0, 180),
        )

        table_img.alpha_composite(
            current_label,
            (int(current_pos[0] + (card_width - current_label.width) // 2), int(current_pos[1] + card_height + 10)),
        )
        table_img.alpha_composite(
            next_label,
            (int(next_pos[0] + (card_width - next_label.width) // 2), int(next_pos[1] + card_height + 10)),
        )

        direction_info = game_state.get("direction_info", {})
        
        high_info = direction_info.get("high", {})
        low_info = direction_info.get("low", {})
        same_info = direction_info.get("same", {})
        
        has_low = low_info and low_info.get("multiplier") is not None
        has_high = high_info and high_info.get("multiplier") is not None
        has_same = same_info and same_info.get("multiplier") is not None
        
        center_x = width // 2
        
        stats_y = cards_y + card_height - 200
        
        streak_text = f"Streak: {game_state.get('streak', 0)}"
        multiplier_text = f"Multiplier: x{game_state.get('multiplier', 1.0):.2f}"
        streak_img = self.text_renderer.render_text(
            streak_text,
            font_size=int(22 * font_scale),
            color=(235, 235, 235, 255),
            stroke_width=2,
            stroke_color=(0, 0, 0, 200),
        )
        multiplier_img = self.text_renderer.render_text(
            multiplier_text,
            font_size=int(22 * font_scale),
            color=(200, 190, 255, 255),
            stroke_width=2,
            stroke_color=(0, 0, 0, 200),
        )
        
        table_img.alpha_composite(
            streak_img,
            (int(center_x - streak_img.width // 2), stats_y),
        )
        table_img.alpha_composite(
            multiplier_img,
            (int(center_x - multiplier_img.width // 2), stats_y + streak_img.height + 8),
        )
        
        # Przyciski
        button_width = 200
        button_height = 55
        button_spacing = 15
        
        buttons_y = stats_y + 70
        
        # Sprawdź czy karta jest ekstremalna
        is_highest = has_high == False and has_low == True
        is_lowest = has_low == False and has_high == True
        is_middle = has_high and has_low
        
        if is_highest:
            # Tylko LOW i SAME
            if has_low:
                low_next_mult = low_info.get('next_total', game_state.get('multiplier', 1.0))
                draw.rounded_rectangle(
                    [int(center_x - button_width // 2), buttons_y, 
                     int(center_x + button_width // 2), buttons_y + button_height],
                    radius=12,
                    fill=(210, 95, 85, 230),
                )
                low_label = self.text_renderer.render_text(
                    "LOW",
                    font_size=max(18, int(1.0 * font_scale * 22)),
                    color=(255, 255, 255, 255),
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 200),
                )
                low_subtext = self.text_renderer.render_text(
                    f"x{low_next_mult:.2f}",
                    font_size=max(14, int(0.9 * font_scale * 22)),
                    color=(255, 255, 200, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 160),
                )
                table_img.alpha_composite(
                    low_label,
                    (int(center_x - low_label.width // 2), buttons_y + 8)
                )
                table_img.alpha_composite(
                    low_subtext,
                    (int(center_x - low_subtext.width // 2), buttons_y + low_label.height + 4)
                )
                buttons_y += button_height + button_spacing
            
            if has_same:
                same_next_mult = same_info.get('next_total', game_state.get('multiplier', 1.0))
                draw.rounded_rectangle(
                    [int(center_x - button_width // 2), buttons_y, 
                     int(center_x + button_width // 2), buttons_y + button_height],
                    radius=12,
                    fill=(110, 140, 210, 230),
                )
                same_label = self.text_renderer.render_text(
                    "SAME",
                    font_size=max(18, int(1.0 * font_scale * 22)),
                    color=(255, 255, 255, 255),
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 200),
                )
                same_subtext = self.text_renderer.render_text(
                    f"x{same_next_mult:.2f}",
                    font_size=max(14, int(0.9 * font_scale * 22)),
                    color=(255, 255, 200, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 160),
                )
                table_img.alpha_composite(
                    same_label,
                    (int(center_x - same_label.width // 2), buttons_y + 8)
                )
                table_img.alpha_composite(
                    same_subtext,
                    (int(center_x - same_subtext.width // 2), buttons_y + same_label.height + 4)
                )
        
        elif is_lowest:
            # Tylko HIGH i SAME
            if has_high:
                high_next_mult = high_info.get('next_total', game_state.get('multiplier', 1.0))
                draw.rounded_rectangle(
                    [int(center_x - button_width // 2), buttons_y, 
                     int(center_x + button_width // 2), buttons_y + button_height],
                    radius=12,
                    fill=(85, 190, 110, 230),
                )
                high_label = self.text_renderer.render_text(
                    "HIGH",
                    font_size=max(18, int(1.0 * font_scale * 22)),
                    color=(255, 255, 255, 255),
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 200),
                )
                high_subtext = self.text_renderer.render_text(
                    f"x{high_next_mult:.2f}",
                    font_size=max(14, int(0.9 * font_scale * 22)),
                    color=(255, 255, 200, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 160),
                )
                table_img.alpha_composite(
                    high_label,
                    (int(center_x - high_label.width // 2), buttons_y + 8)
                )
                table_img.alpha_composite(
                    high_subtext,
                    (int(center_x - high_subtext.width // 2), buttons_y + high_label.height + 4)
                )
                buttons_y += button_height + button_spacing
            
            if has_same:
                same_next_mult = same_info.get('next_total', game_state.get('multiplier', 1.0))
                draw.rounded_rectangle(
                    [int(center_x - button_width // 2), buttons_y, 
                     int(center_x + button_width // 2), buttons_y + button_height],
                    radius=12,
                    fill=(110, 140, 210, 230),
                )
                same_label = self.text_renderer.render_text(
                    "SAME",
                    font_size=max(18, int(1.0 * font_scale * 22)),
                    color=(255, 255, 255, 255),
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 200),
                )
                same_subtext = self.text_renderer.render_text(
                    f"x{same_next_mult:.2f}",
                    font_size=max(14, int(0.9 * font_scale * 22)),
                    color=(255, 255, 200, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 160),
                )
                table_img.alpha_composite(
                    same_label,
                    (int(center_x - same_label.width // 2), buttons_y + 8)
                )
                table_img.alpha_composite(
                    same_subtext,
                    (int(center_x - same_subtext.width // 2), buttons_y + same_label.height + 4)
                )
        
        elif is_middle:
            # HIGH i LOW (bez SAME)
            if has_high:
                high_next_mult = high_info.get('next_total', game_state.get('multiplier', 1.0))
                draw.rounded_rectangle(
                    [int(center_x - button_width // 2), buttons_y, 
                     int(center_x + button_width // 2), buttons_y + button_height],
                    radius=12,
                    fill=(85, 190, 110, 230),
                )
                high_label = self.text_renderer.render_text(
                    "HIGH",
                    font_size=max(18, int(1.0 * font_scale * 22)),
                    color=(255, 255, 255, 255),
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 200),
                )
                high_subtext = self.text_renderer.render_text(
                    f"x{high_next_mult:.2f}",
                    font_size=max(14, int(0.9 * font_scale * 22)),
                    color=(255, 255, 200, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 160),
                )
                table_img.alpha_composite(
                    high_label,
                    (int(center_x - high_label.width // 2), buttons_y + 8)
                )
                table_img.alpha_composite(
                    high_subtext,
                    (int(center_x - high_subtext.width // 2), buttons_y + high_label.height + 4)
                )
                buttons_y += button_height + button_spacing
            
            if has_low:
                low_next_mult = low_info.get('next_total', game_state.get('multiplier', 1.0))
                draw.rounded_rectangle(
                    [int(center_x - button_width // 2), buttons_y, 
                     int(center_x + button_width // 2), buttons_y + button_height],
                    radius=12,
                    fill=(210, 95, 85, 230),
                )
                low_label = self.text_renderer.render_text(
                    "LOW",
                    font_size=max(18, int(1.0 * font_scale * 22)),
                    color=(255, 255, 255, 255),
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 200),
                )
                low_subtext = self.text_renderer.render_text(
                    f"x{low_next_mult:.2f}",
                    font_size=max(14, int(0.9 * font_scale * 22)),
                    color=(255, 255, 200, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 160),
                )
                table_img.alpha_composite(
                    low_label,
                    (int(center_x - low_label.width // 2), buttons_y + 8)
                )
                table_img.alpha_composite(
                    low_subtext,
                    (int(center_x - low_subtext.width // 2), buttons_y + low_label.height + 4)
                )

        # Komunikat na dole
        status_message = game_state.get("message", "Guess high or low to continue.")
        wrapped = textwrap.wrap(status_message, width=45)
        message_images = []
        for line in wrapped:
            text_img = self.text_renderer.render_text(
                line,
                font_size=int(15 * font_scale),
                color=(255, 255, 255, 230),
                stroke_width=1,
                stroke_color=(0, 0, 0, 150),
            )
            message_images.append(text_img)

        total_height = sum(img.height for img in message_images) + max(0, (len(message_images) - 1) * 4)
        message_y = height - total_height - 20
        for img in message_images:
            table_img.alpha_composite(
                img,
                (int(center_x - img.width // 2), message_y),
            )
            message_y += img.height + 4

        try:
            table_img.save(output_path, "PNG")
            hilo_logger.debug(f"Image saved to {output_path}")
        except Exception as exc:
            logger.error(f"[HiLo] Failed to save table image: {exc}")


class HiLoPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="hilo")
        self.active_games: Dict[str, HiLoGame] = {}
        self.assets_folder = self.get_asset_path("blackjack", "board_elements")
        self.renderer = HiLoCardRenderer(self.assets_folder, self.text_renderer)

    def load_game_state(self, user_id: str) -> Optional[HiLoGame]:
        user_id = str(user_id)
        if user_id in self.active_games:
            hilo_logger.debug(f"Loading game from active_games for {user_id}")
            return self.active_games[user_id]

        if hasattr(self, "cache") and self.cache:
            stored = self.cache.get_game_state(user_id, self.game_name)
            if stored:
                user = self.cache.get_user(user_id)
                sender = user.get("name") if user else "Player"
                try:
                    game = HiLoGame.deserialize(user_id, sender, stored)
                    self.active_games[user_id] = game
                    hilo_logger.debug(f"Loaded game from cache for {user_id}")
                    return game
                except Exception as exc:
                    logger.error(f"[HiLo] Failed to deserialize game: {exc}")
        return None

    def save_game_state(self, user_id: str, game: Optional[HiLoGame]):
        user_id = str(user_id)
        if hasattr(self, "cache") and self.cache:
            if game:
                self.cache.save_game_state(user_id, self.game_name, game.serialize())
                hilo_logger.debug(f"Saved game state for {user_id}")
            else:
                self.cache.delete_game_state(user_id, self.game_name)
                hilo_logger.debug(f"Deleted game state for {user_id}")

    def _clear_game(self, user_id: str):
        user_id = str(user_id)
        self.active_games.pop(user_id, None)
        if hasattr(self, "cache") and self.cache:
            self.cache.delete_game_state(user_id, self.game_name)
        hilo_logger.debug(f"Cleared game for {user_id}")

    def _get_user_background_path(self, user_id: str, user: Dict) -> Optional[str]:
        if not user:
            return None
        if hasattr(self, "cache") and self.cache:
            bg_path = self.cache.get_background_path(user_id)
            if os.path.exists(bg_path):
                return bg_path
        return None

    def _send_game_image(
        self,
        user_id: str,
        user: Dict,
        sender: str,
        game: HiLoGame,
        file_queue,
        win_amount: int = 0,
        final_balance: Optional[int] = None,
        show_win_text: bool = False,
    ) -> bool:
        img_path = os.path.join(self.results_folder, f"hilo_{user_id}_{int(time.time())}.png")
        bg_path = self._get_user_background_path(user_id, user)
        state = game.get_render_state()
        self.renderer.generate_table_image(state, img_path, bg_path, font_scale=0.95)

        if final_balance is None:
            final_balance = user.get("balance", 0) if user else 0

        total_bet = game.bet
        is_loss = win_amount == 0 and game.game_status == "finished"

        user_info = {
            "user_id": str(user_id),
            "username": sender,
            "bet": total_bet,
            "win": win_amount,
            "balance": final_balance,
            "level": user.get("level", 1),
            "level_progress": user.get("level_progress", 0),
            "is_win": win_amount > 0,
            "avatar_path": user.get("avatar_path", ""),
        }

        if is_loss and win_amount == 0:
            user_info["win"] = -total_bet
            user_info["is_win"] = False

        avatar_path = None
        bg_asset = None
        if hasattr(self, "cache") and self.cache:
            avatar_path = self.cache.get_avatar_path(user_id)
            bg_asset = self.cache.get_background_path(user_id)

        if not avatar_path or not bg_asset:
            avatar_path = self.get_asset_path("default_avatar.png")
            bg_asset = self.get_asset_path("default_bg.png")

        final_path = self.generate_static(
            image_path=img_path,
            avatar_path=avatar_path,
            bg_path=bg_asset,
            user_info=user_info,
            show_bet_amount=True,
            show_win_text=show_win_text or is_loss or win_amount > 0,
            font_scale=0.9,
            avatar_size=70,
            win_text_height=60
        )

        if final_path:
            file_queue.put(final_path)
            return True
        return False

    def _notify_usage(self, sender: str, file_queue, cache, user_id: Optional[str]):
        self.send_message_image(
            sender,
            file_queue,
            " **Hi-Lo Card Game** \n\n"
            "**Commands:**\n"
            "• `/hilo start <bet>` - Start new game\n"
            "• `/hilo high` - Guess next card is higher\n"
            "• `/hilo low` - Guess next card is lower\n"
            "• `/hilo same` - Guess next card is same value\n"
            "• `/hilo collect` - Cash out your streak\n"
            "• `/hilo status` - Show current game\n\n"
            "**Rules:**\n"
            "• Each correct guess adds multiplier based on odds\n"
            "• Wrong guess or tie (without betting 'same') loses bet\n"
            "• Collect anytime after at least one win\n"
            "• Ace is the LOWEST card (1), King is the HIGHEST (13)",
            "Hi-Lo Help",
            cache,
            user_id,
        )

    def _get_game_or_notify(self, user_id: str, sender: str, file_queue, cache) -> Optional[HiLoGame]:
        game = self.active_games.get(user_id)
        if not game:
            game = self.load_game_state(user_id)
        if not game:
            self.send_message_image(sender, file_queue, " No active Hi-Lo game. Use `/hilo start <bet>` to begin!", "Hi-Lo", cache, user_id)
        return game

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache

        if not sender:
            return ""

        if len(args) == 0:
            user_id, user, error = self.validate_user(cache, sender, avatar_url)
            if error:
                self.send_message_image(sender, file_queue, error, "Hi-Lo Error", cache, user_id)
                return ""

            game = self.load_game_state(user_id)
            if game:
                self._send_game_image(user_id, user, sender, game, file_queue)
                return "Current Hi-Lo state shown above."
            self.send_message_image(sender, file_queue, " No active Hi-Lo game. Use `/hilo start <bet>` to begin!", "Hi-Lo", cache, user_id)
            return ""

        cmd = args[0].lower()

        if cmd in ("start", "play", "bet"):
            if len(args) < 2:
                self._notify_usage(sender, file_queue, cache, None)
                return ""

            try:
                bet = int(args[1])
            except ValueError:
                self.send_message_image(sender, file_queue, " Bet must be a number!", "Hi-Lo Error", cache, None)
                return ""

            if bet <= 0:
                self.send_message_image(sender, file_queue, " Bet must be greater than zero!", "Hi-Lo Error", cache, None)
                return ""

            user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, bet)
            if error:
                self.send_message_image(sender, file_queue, error, "Hi-Lo Error", cache, None)
                return ""

            if self.active_games.get(user_id) or self.load_game_state(user_id):
                self.send_message_image(sender, file_queue, " Finish your current Hi-Lo streak before starting a new game!", "Hi-Lo", cache, user_id)
                return ""

            new_balance = user["balance"] - bet
            self.update_user_balance(user_id, new_balance)
            user["balance"] = new_balance

            game = HiLoGame(user_id, sender, bet)
            self.active_games[user_id] = game
            self.save_game_state(user_id, game)
            self._send_game_image(user_id, user, sender, game, file_queue)
            return f" Hi-Lo started! Bet: {bet}. First card: {game.current_card}"

        if cmd in ("high", "h", "up", "higher"):
            user_id, user, error = self.validate_user(cache, sender, avatar_url)
            if error:
                self.send_message_image(sender, file_queue, error, "Hi-Lo Error", cache, user_id)
                return ""

            game = self._get_game_or_notify(user_id, sender, file_queue, cache)
            if not game:
                return ""

            result = game.make_guess("high")
            if not result.get("valid"):
                self.send_message_image(sender, file_queue, " Cannot make a guess right now!", "Hi-Lo Error", cache, user_id)
                return ""

            if result.get("result") in ("loss", "tie"):
                new_level, new_progress = self.cache.add_experience(
                    user_id, -game.bet, sender, file_queue
                )
                user["level"] = new_level
                user["level_progress"] = new_progress
                
                self._clear_game(user_id)
                final_balance = user["balance"]
                self._send_game_image(user_id, user, sender, game, file_queue, win_amount=0, final_balance=final_balance, show_win_text=True)
                return f" Game over! You lost your bet of {game.bet}. Start a new game with `/hilo start <bet>`."

            self.save_game_state(user_id, game)
            self._send_game_image(user_id, user, sender, game, file_queue)
            
            game.prepare_next_round()
            self.save_game_state(user_id, game)
            
            return f" Correct guess! Streak: {game.streak} | Multiplier: x{game.get_multiplier():.2f}"

        if cmd in ("low", "l", "down", "lower"):
            user_id, user, error = self.validate_user(cache, sender, avatar_url)
            if error:
                self.send_message_image(sender, file_queue, error, "Hi-Lo Error", cache, user_id)
                return ""

            game = self._get_game_or_notify(user_id, sender, file_queue, cache)
            if not game:
                return ""

            direction_info = game._calculate_direction_info()
            if direction_info.get("low", {}).get("multiplier") is None:
                self.send_message_image(sender, file_queue, " No lower cards available! Try `/hilo same` instead.", "Hi-Lo", cache, user_id)
                return ""

            result = game.make_guess("low")
            if not result.get("valid"):
                self.send_message_image(sender, file_queue, " Cannot make a guess right now!", "Hi-Lo Error", cache, user_id)
                return ""

            if result.get("result") in ("loss", "tie"):
                new_level, new_progress = self.cache.add_experience(
                    user_id, -game.bet, sender, file_queue
                )
                user["level"] = new_level
                user["level_progress"] = new_progress
                
                self._clear_game(user_id)
                final_balance = user["balance"]
                self._send_game_image(user_id, user, sender, game, file_queue, win_amount=0, final_balance=final_balance, show_win_text=True)
                return f" Game over! You lost your bet of {game.bet}. Start a new game with `/hilo start <bet>`."

            self.save_game_state(user_id, game)
            self._send_game_image(user_id, user, sender, game, file_queue)
            
            game.prepare_next_round()
            self.save_game_state(user_id, game)
            
            return f" Correct guess! Streak: {game.streak} | Multiplier: x{game.get_multiplier():.2f}"

        if cmd in ("same", "s", "equal", "tie"):
            user_id, user, error = self.validate_user(cache, sender, avatar_url)
            if error:
                self.send_message_image(sender, file_queue, error, "Hi-Lo Error", cache, user_id)
                return ""

            game = self._get_game_or_notify(user_id, sender, file_queue, cache)
            if not game:
                return ""

            result = game.make_guess("same")
            if not result.get("valid"):
                self.send_message_image(sender, file_queue, " Cannot make a guess right now!", "Hi-Lo Error", cache, user_id)
                return ""

            if result.get("result") in ("loss", "tie"):
                new_level, new_progress = self.cache.add_experience(
                    user_id, -game.bet, sender, file_queue
                )
                user["level"] = new_level
                user["level_progress"] = new_progress
                
                self._clear_game(user_id)
                final_balance = user["balance"]
                self._send_game_image(user_id, user, sender, game, file_queue, win_amount=0, final_balance=final_balance, show_win_text=True)
                return f" Game over! You lost your bet of {game.bet}. Start a new game with `/hilo start <bet>`."

            self.save_game_state(user_id, game)
            self._send_game_image(user_id, user, sender, game, file_queue)
            
            game.prepare_next_round()
            self.save_game_state(user_id, game)
            
            return f" Correct guess! Streak: {game.streak} | Multiplier: x{game.get_multiplier():.2f}"

        if cmd in ("collect", "cashout", "stop", "bank"):
            user_id, user, error = self.validate_user(cache, sender, avatar_url)
            if error:
                self.send_message_image(sender, file_queue, error, "Hi-Lo Error", cache, user_id)
                return ""

            game = self._get_game_or_notify(user_id, sender, file_queue, cache)
            if not game:
                return ""

            payout = game.collect()
            if payout == 0:
                self.send_message_image(sender, file_queue, " You need at least one correct guess before collecting!", "Hi-Lo", cache, user_id)
                return ""

            net_win = payout - game.bet 
            new_balance = user["balance"] + net_win
            self.update_user_balance(user_id, new_balance)
            user["balance"] = new_balance
            
            new_level, new_progress = self.cache.add_experience(
                user_id, net_win, sender, file_queue
            )
            user["level"] = new_level
            user["level_progress"] = new_progress
            
            self._clear_game(user_id)
            self._send_game_image(user_id, user, sender, game, file_queue, win_amount=net_win, final_balance=new_balance, show_win_text=True)
            
            if net_win > 0:
                return f"Hi-Lo cashout! You won {net_win} net (x{game.get_multiplier():.2f} multiplier). New balance: {new_balance}"
            else:
                return f"Hi-Lo cashout! You lost {abs(net_win)} net. New balance: {new_balance}"

        if cmd in ("status", "alone"):
            user_id, user, error = self.validate_user(cache, sender, avatar_url)
            if error:
                self.send_message_image(sender, file_queue, error, "Hi-Lo Error", cache, user_id)
                return ""

            game = self._get_game_or_notify(user_id, sender, file_queue, cache)
            if game:
                self._send_game_image(user_id, user, sender, game, file_queue)
            return ""

        self._notify_usage(sender, file_queue, cache, None)
        return ""

def register():
    logger.info("[HiLo] Registering Hi-Lo plugin")
    plugin = HiLoPlugin()
    return {
        "name": "hilo",
        "aliases": ["/hl"],
        "description": (
            " **Hi-Lo Card Challenge** \n\n"
            "**Commands:**\n"
            "• `/hilo start <bet>` - Start new game\n"
            "• `/hilo high` - Guess next card is higher\n"
            "• `/hilo low` - Guess next card is lower (only when available)\n"
            "• `/hilo same` - Guess next card is same value\n"
            "• `/hilo collect` - Cash out your streak\n"
            "• `/hilo status` - Show current game\n\n"
            "**Mechanics:**\n"
            "• Each correct guess adds odds-based multiplier (≈2% house edge)\n"
            "• Wrong guess or tie (without betting 'same') loses bet\n"
            "• Collect anytime after at least one win\n"
            "• Ace is the LOWEST card (1), King is the HIGHEST (13)\n"
            "• 'SAME' button appears when no lower cards are available"
        ),
        "execute": plugin.execute_game,
    }