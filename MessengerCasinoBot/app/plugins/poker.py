import os
import random
import time
from collections import Counter
from itertools import combinations
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw

from base_game_plugin import BaseGamePlugin
from logger import logger
from plugins.weekly import record_weekly_win


RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = ["S", "H", "D", "C"]
RANK_VALUES = {rank: index + 2 for index, rank in enumerate(RANKS)}
RED_SUITS = {"H", "D"}
STAGES = ["preflop", "flop", "turn", "river"]


class PokerHand:
    def __init__(self, cards: List[str]):
        self.cards = cards[:]
        self.score, self.label, self.best_cards = self.best_hand(cards)

    @staticmethod
    def _rank(card: str) -> str:
        return card[:-1]

    @staticmethod
    def _suit(card: str) -> str:
        return card[-1]

    @classmethod
    def _card_value(cls, card: str) -> int:
        return RANK_VALUES[cls._rank(card)]

    @classmethod
    def _straight_high(cls, values: List[int]) -> Optional[int]:
        unique_values = sorted(set(values), reverse=True)
        if len(unique_values) != 5:
            return None

        if unique_values == [14, 5, 4, 3, 2]:
            return 5

        if unique_values[0] - unique_values[-1] == 4:
            return unique_values[0]

        return None

    @classmethod
    def evaluate_five(cls, cards: List[str]) -> Tuple[Tuple[int, ...], str]:
        values = [cls._card_value(card) for card in cards]
        suits = [cls._suit(card) for card in cards]
        counts = Counter(values)

        groups = sorted(
            counts.items(),
            key=lambda item: (item[1], item[0]),
            reverse=True,
        )
        flush = len(set(suits)) == 1
        straight_high = cls._straight_high(values)

        if flush and straight_high:
            if straight_high == 14:
                return (9, 14), "Royal Flush"
            return (8, straight_high), "Straight Flush"

        if groups[0][1] == 4:
            four_value = groups[0][0]
            kicker = max(value for value in values if value != four_value)
            return (7, four_value, kicker), "Four of a Kind"

        if groups[0][1] == 3 and groups[1][1] == 2:
            return (6, groups[0][0], groups[1][0]), "Full House"

        if flush:
            return (5, *sorted(values, reverse=True)), "Flush"

        if straight_high:
            return (4, straight_high), "Straight"

        if groups[0][1] == 3:
            triple_value = groups[0][0]
            kickers = sorted([value for value in values if value != triple_value], reverse=True)
            return (3, triple_value, *kickers), "Three of a Kind"

        pairs = sorted([value for value, count in counts.items() if count == 2], reverse=True)
        if len(pairs) == 2:
            kicker = max(value for value in values if value not in pairs)
            return (2, *pairs, kicker), "Two Pair"

        if len(pairs) == 1:
            pair_value = pairs[0]
            kickers = sorted([value for value in values if value != pair_value], reverse=True)
            return (1, pair_value, *kickers), "One Pair"

        return (0, *sorted(values, reverse=True)), "High Card"

    @classmethod
    def best_hand(cls, cards: List[str]) -> Tuple[Tuple[int, ...], str, List[str]]:
        if len(cards) < 5:
            sorted_cards = sorted(cards, key=cls._card_value, reverse=True)
            high_values = tuple(cls._card_value(card) for card in sorted_cards)
            return (0, *high_values), "High Card", sorted_cards

        best_score = None
        best_label = "High Card"
        best_cards = []

        for combo in combinations(cards, 5):
            score, label = cls.evaluate_five(list(combo))
            if best_score is None or score > best_score:
                best_score = score
                best_label = label
                best_cards = list(combo)

        return best_score or (0,), best_label, cls.sort_cards(best_cards)

    @classmethod
    def sort_cards(cls, cards: List[str]) -> List[str]:
        return sorted(
            cards,
            key=lambda card: (cls._card_value(card), cls._suit(card)),
            reverse=True,
        )


class TexasHoldemGame:
    def __init__(
        self,
        user_id: str,
        sender_name: str,
        ante: int,
        deck: Optional[List[str]] = None,
        player_cards: Optional[List[str]] = None,
        bot_cards: Optional[List[str]] = None,
        community_cards: Optional[List[str]] = None,
        stage: str = "preflop",
        pot: Optional[int] = None,
        player_committed: Optional[int] = None,
        bot_committed: Optional[int] = None,
        street_player_bet: int = 0,
        street_bot_bet: int = 0,
        to_call: int = 0,
        message: Optional[str] = None,
        status: str = "active",
        winner: Optional[str] = None,
        net_win: int = 0,
        payout: int = 0,
        finish_reason: Optional[str] = None,
        player_hand_label: Optional[str] = None,
        bot_hand_label: Optional[str] = None,
    ):
        self.user_id = str(user_id)
        self.sender_name = sender_name
        self.ante = ante
        self.deck = deck[:] if deck else self._build_deck()
        self.player_cards = player_cards[:] if player_cards else [self._draw_card(), self._draw_card()]
        self.bot_cards = bot_cards[:] if bot_cards else [self._draw_card(), self._draw_card()]
        self.community_cards = community_cards[:] if community_cards else []
        self.stage = stage
        self.pot = pot if pot is not None else ante * 2
        self.player_committed = player_committed if player_committed is not None else ante
        self.bot_committed = bot_committed if bot_committed is not None else ante
        self.street_player_bet = street_player_bet
        self.street_bot_bet = street_bot_bet
        self.to_call = to_call
        self.message = message or self._stage_prompt("Texas Hold'em started. You posted the ante.")
        self.status = status
        self.winner = winner
        self.net_win = net_win
        self.payout = payout
        self.finish_reason = finish_reason
        self.player_hand_label = player_hand_label
        self.bot_hand_label = bot_hand_label

    def _build_deck(self) -> List[str]:
        deck = [f"{rank}{suit}" for suit in SUITS for rank in RANKS]
        random.shuffle(deck)
        return deck

    def _draw_card(self) -> str:
        if not self.deck:
            self.deck = self._build_deck()
        return self.deck.pop()

    def _stage_prompt(self, prefix: str = "") -> str:
        stage_name = self.stage.upper()
        action = "Action: /poker check, /poker bet <amount>, or /poker fold."
        if self.to_call > 0:
            action = f"Bot bet. Call {self.to_call}, raise, or fold."
        if prefix:
            return f"{prefix}\n{stage_name}: {action}"
        return f"{stage_name}: {action}"

    def _reset_street_bets(self):
        self.street_player_bet = 0
        self.street_bot_bet = 0
        self.to_call = 0

    def _next_stage_name(self) -> Optional[str]:
        if self.stage not in STAGES:
            return None
        index = STAGES.index(self.stage)
        if index + 1 >= len(STAGES):
            return None
        return STAGES[index + 1]

    def _reveal_next_stage(self):
        next_stage = self._next_stage_name()
        self._reset_street_bets()

        if self.stage == "preflop":
            self.stage = "flop"
            while len(self.community_cards) < 3:
                self.community_cards.append(self._draw_card())
            self.message = self._stage_prompt("Flop revealed.")
            return

        if self.stage == "flop":
            self.stage = "turn"
            if len(self.community_cards) < 4:
                self.community_cards.append(self._draw_card())
            self.message = self._stage_prompt("Turn revealed.")
            return

        if self.stage == "turn":
            self.stage = "river"
            if len(self.community_cards) < 5:
                self.community_cards.append(self._draw_card())
            self.message = self._stage_prompt("River revealed.")
            return

        if next_stage is None:
            self.finish_showdown()

    def _estimate_strength(self, cards: List[str]) -> float:
        known_cards = cards + self.community_cards

        if len(self.community_cards) >= 3:
            score = PokerHand(known_cards).score
            category = score[0]
            category_strength = {
                9: 0.98,
                8: 0.95,
                7: 0.90,
                6: 0.84,
                5: 0.76,
                4: 0.70,
                3: 0.62,
                2: 0.52,
                1: 0.40,
                0: 0.24,
            }.get(category, 0.25)
            high_card_bonus = min(0.12, max(score[1:]) / 120.0 if len(score) > 1 else 0)
            return min(0.98, category_strength + high_card_bonus)

        first, second = cards
        v1 = RANK_VALUES[first[:-1]]
        v2 = RANK_VALUES[second[:-1]]
        high = max(v1, v2)
        low = min(v1, v2)
        suited = first[-1] == second[-1]
        pair = v1 == v2
        connected = abs(v1 - v2) <= 1

        strength = 0.18 + (high / 22.0) + (low / 40.0)
        if pair:
            strength += 0.28 + high / 60.0
        if suited:
            strength += 0.07
        if connected:
            strength += 0.05
        return max(0.05, min(0.95, strength))

    def _bot_bet_amount(self) -> int:
        base = max(1, self.ante)
        if self.stage == "preflop":
            return base
        if self.stage == "flop":
            return max(1, base)
        if self.stage == "turn":
            return max(1, int(round(base * 1.5)))
        return max(1, base * 2)

    def _bot_should_bet(self) -> bool:
        strength = self._estimate_strength(self.bot_cards)
        chance = 0.10 + (strength * 0.55)
        if self.stage in {"turn", "river"}:
            chance += 0.08
        return random.random() < min(0.80, chance)

    def _bot_call_chance(self, amount_to_call: int) -> float:
        strength = self._estimate_strength(self.bot_cards)
        pressure = amount_to_call / max(1, self.ante)
        chance = strength + 0.25 - pressure * 0.08
        return max(0.12, min(0.95, chance))

    def _bot_may_raise(self, player_amount: int) -> bool:
        if self.street_bot_bet > 0:
            return False
        if self.stage == "river":
            return False
        strength = self._estimate_strength(self.bot_cards)
        if strength < 0.72:
            return False
        pressure = player_amount / max(1, self.ante)
        chance = min(0.30, (strength - 0.70) * 0.75)
        if pressure > 3:
            chance *= 0.4
        return random.random() < chance

    def player_check(self) -> Tuple[bool, str]:
        if self.status != "active":
            return False, "This poker hand is already finished."
        if self.to_call > 0:
            return False, f"You must call {self.to_call}, raise, or fold."

        if self._bot_should_bet():
            bot_bet = self._bot_bet_amount()
            self.street_bot_bet += bot_bet
            self.bot_committed += bot_bet
            self.pot += bot_bet
            self.to_call = bot_bet
            self.message = self._stage_prompt(f"You check. Bot bets {bot_bet}.")
            return True, self.message

        previous_stage = self.stage
        self.message = f"You check. Bot checks behind on {previous_stage}."
        self._reveal_next_stage()
        if self.status == "finished":
            return True, self.message
        return True, f"Both players checked {previous_stage}. {self.message}"

    def player_bet(self, amount: int) -> Tuple[bool, str]:
        if self.status != "active":
            return False, "This poker hand is already finished."
        if amount <= 0:
            return False, "Bet must be greater than zero."
        if self.to_call > 0:
            return False, f"Use /poker call, /poker raise <amount>, or /poker fold. To call: {self.to_call}."

        self.street_player_bet += amount
        self.player_committed += amount
        self.pot += amount

        if self._bot_may_raise(amount):
            raise_amount = max(1, min(amount, self._bot_bet_amount()))
            bot_total = amount + raise_amount
            self.street_bot_bet += bot_total
            self.bot_committed += bot_total
            self.pot += bot_total
            self.to_call = raise_amount
            self.message = self._stage_prompt(f"You bet {amount}. Bot raises by {raise_amount}.")
            return True, self.message

        if random.random() <= self._bot_call_chance(amount):
            self.street_bot_bet += amount
            self.bot_committed += amount
            self.pot += amount
            previous_stage = self.stage
            self._reveal_next_stage()
            if self.status == "finished":
                return True, self.message
            return True, f"You bet {amount}. Bot calls. {previous_stage.upper()} betting is closed."

        self.finish_bot_fold()
        return True, f"You bet {amount}. Bot folds."

    def player_call(self) -> Tuple[bool, str]:
        if self.status != "active":
            return False, "This poker hand is already finished."
        if self.to_call <= 0:
            return False, "There is nothing to call. You can check or bet."

        call_amount = self.to_call
        self.street_player_bet += call_amount
        self.player_committed += call_amount
        self.pot += call_amount
        self.to_call = 0

        previous_stage = self.stage
        self._reveal_next_stage()
        if self.status == "finished":
            return True, self.message
        return True, f"You call {call_amount}. {previous_stage.upper()} betting is closed."

    def player_raise(self, amount: int) -> Tuple[bool, str]:
        if self.status != "active":
            return False, "This poker hand is already finished."
        if amount <= 0:
            return False, "Raise must be greater than zero."

        if self.to_call <= 0:
            return self.player_bet(amount)

        call_amount = self.to_call
        total_player_add = call_amount + amount
        self.street_player_bet += total_player_add
        self.player_committed += total_player_add
        self.pot += total_player_add
        self.to_call = 0

        if random.random() <= self._bot_call_chance(amount):
            self.street_bot_bet += amount
            self.bot_committed += amount
            self.pot += amount
            previous_stage = self.stage
            self._reveal_next_stage()
            if self.status == "finished":
                return True, self.message
            return True, f"You call {call_amount} and raise {amount}. Bot calls."

        self.finish_bot_fold()
        return True, f"You call {call_amount} and raise {amount}. Bot folds."

    def player_fold(self) -> Tuple[bool, str]:
        if self.status != "active":
            return False, "This poker hand is already finished."
        self.status = "finished"
        self.winner = "bot"
        self.finish_reason = "player_fold"
        self.payout = 0
        self.net_win = -self.player_committed
        self.message = f"You fold. Bot wins the pot. You lose {self.player_committed}."
        return True, self.message

    def finish_bot_fold(self):
        self.status = "finished"
        self.winner = "player"
        self.finish_reason = "bot_fold"
        self.payout = self.pot
        self.net_win = self.payout - self.player_committed
        self.message = f"Bot folds. You win the pot of {self.pot}."

    def finish_showdown(self):
        player_hand = PokerHand(self.player_cards + self.community_cards)
        bot_hand = PokerHand(self.bot_cards + self.community_cards)
        self.player_hand_label = player_hand.label
        self.bot_hand_label = bot_hand.label
        self.status = "finished"
        self.finish_reason = "showdown"

        if player_hand.score > bot_hand.score:
            self.winner = "player"
            self.payout = self.pot
            self.net_win = self.payout - self.player_committed
            self.message = f"Showdown! You win with {player_hand.label}."
        elif player_hand.score < bot_hand.score:
            self.winner = "bot"
            self.payout = 0
            self.net_win = -self.player_committed
            self.message = f"Showdown! Bot wins with {bot_hand.label}."
        else:
            self.winner = "tie"
            self.payout = self.pot // 2
            self.net_win = self.payout - self.player_committed
            self.message = f"Showdown push. Both players have {player_hand.label}."

    def serialize(self) -> Dict:
        return {
            "ante": self.ante,
            "deck": self.deck,
            "player_cards": self.player_cards,
            "bot_cards": self.bot_cards,
            "community_cards": self.community_cards,
            "stage": self.stage,
            "pot": self.pot,
            "player_committed": self.player_committed,
            "bot_committed": self.bot_committed,
            "street_player_bet": self.street_player_bet,
            "street_bot_bet": self.street_bot_bet,
            "to_call": self.to_call,
            "message": self.message,
            "status": self.status,
            "winner": self.winner,
            "net_win": self.net_win,
            "payout": self.payout,
            "finish_reason": self.finish_reason,
            "player_hand_label": self.player_hand_label,
            "bot_hand_label": self.bot_hand_label,
        }

    @classmethod
    def deserialize(cls, user_id: str, sender_name: str, data: Dict) -> "TexasHoldemGame":
        return cls(
            user_id=user_id,
            sender_name=sender_name,
            ante=data.get("ante", 0),
            deck=data.get("deck", []),
            player_cards=data.get("player_cards", []),
            bot_cards=data.get("bot_cards", []),
            community_cards=data.get("community_cards", []),
            stage=data.get("stage", "preflop"),
            pot=data.get("pot", 0),
            player_committed=data.get("player_committed", 0),
            bot_committed=data.get("bot_committed", 0),
            street_player_bet=data.get("street_player_bet", 0),
            street_bot_bet=data.get("street_bot_bet", 0),
            to_call=data.get("to_call", 0),
            message=data.get("message"),
            status=data.get("status", "active"),
            winner=data.get("winner"),
            net_win=data.get("net_win", 0),
            payout=data.get("payout", 0),
            finish_reason=data.get("finish_reason"),
            player_hand_label=data.get("player_hand_label"),
            bot_hand_label=data.get("bot_hand_label"),
        )


class PokerTableRenderer:
    def __init__(self, text_renderer):
        self.text_renderer = text_renderer
        self.width = 760
        self.height = 560
        self.card_width = 76
        self.card_height = 108
        self.card_gap = 10

    def _text(self, text: str, font_size: int, color, stroke_width: int = 0):
        return self.text_renderer.render_text(
            text=text,
            font_size=font_size,
            color=color,
            stroke_width=stroke_width,
            stroke_color=(0, 0, 0, 220),
            shadow=stroke_width == 0,
            shadow_color=(0, 0, 0, 160),
            shadow_offset=(2, 2),
        )

    def _fit_text(self, text: str, font_size: int, max_width: int, color, min_size: int = 12):
        size = font_size
        rendered = self._text(text, size, color, stroke_width=1)
        while rendered.width > max_width and size > min_size:
            size -= 1
            rendered = self._text(text, size, color, stroke_width=1)
        return rendered

    def _draw_centered(self, canvas: Image.Image, text: str, y: int, font_size: int, color):
        text_img = self._fit_text(text, font_size, self.width - 70, color)
        canvas.alpha_composite(text_img, ((self.width - text_img.width) // 2, y))

    def _draw_card(self, canvas: Image.Image, card: Optional[str], x: int, y: int, hidden: bool = False):
        draw = ImageDraw.Draw(canvas)
        rect = [x, y, x + self.card_width, y + self.card_height]

        if hidden:
            draw.rounded_rectangle(rect, radius=10, fill=(34, 55, 92, 255), outline=(220, 180, 80, 240), width=2)
            draw.rounded_rectangle([x + 8, y + 8, x + self.card_width - 8, y + self.card_height - 8], radius=6, outline=(90, 120, 175, 255), width=2)
            back_text = self._text("?", 32, (255, 235, 160, 255), stroke_width=2)
            canvas.alpha_composite(back_text, (x + (self.card_width - back_text.width) // 2, y + (self.card_height - back_text.height) // 2))
            return

        if not card:
            draw.rounded_rectangle(rect, radius=10, fill=(18, 42, 36, 175), outline=(80, 120, 105, 180), width=2)
            return

        suit = card[-1]
        rank = card[:-1]
        color = (210, 45, 55, 255) if suit in RED_SUITS else (24, 28, 34, 255)

        draw.rounded_rectangle(rect, radius=10, fill=(248, 248, 242, 255), outline=(42, 42, 48, 255), width=2)
        draw.rounded_rectangle([x + 5, y + 5, x + self.card_width - 5, y + self.card_height - 5], radius=7, outline=(210, 210, 205, 255), width=1)

        rank_img = self._fit_text(rank, 24, self.card_width - 14, color, min_size=16)
        suit_img = self._text(suit, 18, color)
        canvas.alpha_composite(rank_img, (x + 7, y + 6))
        canvas.alpha_composite(suit_img, (x + 8, y + 8 + rank_img.height))

        center_img = self._fit_text(f"{rank}{suit}", 28, self.card_width - 10, color, min_size=17)
        canvas.alpha_composite(
            center_img,
            (x + (self.card_width - center_img.width) // 2, y + (self.card_height - center_img.height) // 2),
        )

    def _draw_cards(self, canvas: Image.Image, cards: List[Optional[str]], y: int, hidden: bool = False, slots: int = 0):
        count = max(slots, len(cards))
        total_width = count * self.card_width + max(0, count - 1) * self.card_gap
        x = (self.width - total_width) // 2
        for index in range(count):
            card = cards[index] if index < len(cards) else None
            self._draw_card(canvas, card, x, y, hidden=hidden and card is not None)
            x += self.card_width + self.card_gap

    def _load_background(self, background_path: Optional[str]):
        if background_path and os.path.exists(background_path):
            try:
                bg = Image.open(background_path).convert("RGBA")
                bg = bg.resize((self.width, self.height), Image.Resampling.LANCZOS)
                shade = Image.new("RGBA", (self.width, self.height), (5, 8, 14, 185))
                return Image.alpha_composite(bg, shade)
            except Exception as exc:
                logger.warning(f"[Poker] Could not load user background: {exc}")
        return Image.new("RGBA", (self.width, self.height), (9, 14, 24, 255))

    def _result_color(self, game: TexasHoldemGame):
        if game.winner == "player":
            return (90, 220, 130, 255)
        if game.winner == "bot":
            return (255, 90, 90, 255)
        if game.winner == "tie":
            return (255, 210, 70, 255)
        return (235, 238, 245, 255)

    def generate(self, game: TexasHoldemGame, sender: str, output_path: str, background_path: Optional[str] = None):
        canvas = self._load_background(background_path)
        draw = ImageDraw.Draw(canvas)

        draw.rounded_rectangle([22, 20, self.width - 22, self.height - 20], radius=28, fill=(15, 28, 35, 210), outline=(85, 95, 110, 180), width=2)
        draw.rounded_rectangle([58, 96, self.width - 58, self.height - 86], radius=150, fill=(18, 92, 72, 225), outline=(218, 170, 75, 230), width=5)
        draw.rounded_rectangle([78, 116, self.width - 78, self.height - 106], radius=130, outline=(20, 50, 42, 230), width=4)

        self._draw_centered(canvas, "TEXAS HOLD'EM", 28, 28, (255, 255, 255, 255))
        status_color = self._result_color(game)
        headline = game.message.split("\n", 1)[0]
        self._draw_centered(canvas, headline, 62, 20, status_color)

        info = f"Stage: {game.stage.upper()} | Pot: {game.pot} | You in: {game.player_committed}"
        if game.to_call > 0 and game.status == "active":
            info += f" | To call: {game.to_call}"
        self._draw_centered(canvas, info, 90, 16, (235, 238, 245, 255))

        bot_hidden = game.status != "finished"
        bot_label = "BOT"
        if game.status == "finished" and game.bot_hand_label:
            bot_label = f"BOT - {game.bot_hand_label}"
        self._draw_centered(canvas, bot_label, 122, 16, (190, 198, 210, 255))
        self._draw_cards(canvas, game.bot_cards, 148, hidden=bot_hidden, slots=2)

        self._draw_centered(canvas, "BOARD", 268, 16, (190, 198, 210, 255))
        board_slots = game.community_cards + [None] * (5 - len(game.community_cards))
        self._draw_cards(canvas, board_slots, 294, slots=5)

        player_label = sender.upper()
        if len(player_label) > 20:
            player_label = f"{player_label[:17]}..."
        if game.status == "finished" and game.player_hand_label:
            player_label = f"{player_label} - {game.player_hand_label}"
        self._draw_centered(canvas, player_label, 422, 16, (220, 225, 235, 255))
        self._draw_cards(canvas, game.player_cards, 448, slots=2)

        if game.status == "active":
            if game.to_call > 0:
                action = f"CALL {game.to_call} / RAISE <AMOUNT> / FOLD"
            else:
                action = "CHECK / BET <AMOUNT> / FOLD"
        else:
            if game.winner == "player":
                action = f"PAYOUT {game.payout} | NET +{game.net_win}"
            elif game.winner == "tie":
                action = f"SPLIT POT | NET {game.net_win}"
            else:
                action = f"LOST {abs(game.net_win)}"
        self._draw_centered(canvas, action, 522, 17, status_color)

        canvas.convert("RGB").save(output_path, "PNG", quality=95)


class PokerPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="poker")
        os.makedirs(self.results_folder, exist_ok=True)
        self.min_bet = 1
        self.active_games: Dict[str, TexasHoldemGame] = {}
        self.renderer = PokerTableRenderer(self.text_renderer)

    def load_game_state(self, user_id: str) -> Optional[TexasHoldemGame]:
        user_id = str(user_id)
        if user_id in self.active_games:
            return self.active_games[user_id]

        if hasattr(self, "cache") and self.cache:
            stored = self.cache.get_game_state(user_id, self.game_name)
            if stored:
                user = self.cache.get_user(user_id)
                sender = user.get("name") if user else "Player"
                try:
                    game = TexasHoldemGame.deserialize(user_id, sender, stored)
                    self.active_games[user_id] = game
                    return game
                except Exception as exc:
                    logger.error(f"[Poker] Failed to deserialize game: {exc}", exc_info=True)
        return None

    def save_game_state(self, user_id: str, game: Optional[TexasHoldemGame]):
        user_id = str(user_id)
        if hasattr(self, "cache") and self.cache:
            if game:
                self.cache.save_game_state(user_id, self.game_name, game.serialize())
            else:
                self.cache.delete_game_state(user_id, self.game_name)

    def _clear_game(self, user_id: str):
        user_id = str(user_id)
        self.active_games.pop(user_id, None)
        self.save_game_state(user_id, None)

    def _send_help(self, sender: str, file_queue, cache, user_id: Optional[str] = None):
        self.send_message_image(
            sender,
            file_queue,
            "Texas Hold'em vs Bot\n\n"
            "Commands:\n"
            "- /poker start <ante> - start a hand\n"
            "- /poker - show current table\n"
            "- /poker check - check when no bet is pending\n"
            "- /poker bet <amount> - open betting\n"
            "- /poker call - call bot bet\n"
            "- /poker raise <amount> - call and raise\n"
            "- /poker fold - fold the hand\n\n"
            "You get 2 hole cards. Board reveals flop, turn, and river. "
            "Showdown happens only after river betting closes, unless someone folds.",
            "Poker Help",
            cache,
            user_id,
        )

    def _parse_amount(self, args: List[str], index: int = 1) -> Tuple[Optional[int], Optional[str]]:
        if len(args) <= index:
            return None, "Amount is missing."
        try:
            amount = int(args[index])
        except ValueError:
            return None, "Amount must be a whole number."
        if amount < self.min_bet:
            return None, f"Minimum amount is {self.min_bet}."
        return amount, None

    def _get_user_background_path(self, user_id: str) -> Optional[str]:
        if hasattr(self, "cache") and self.cache:
            background_path = self.cache.get_background_path(user_id)
            if background_path and os.path.exists(background_path):
                return background_path
        return None

    def _send_game_image(
        self,
        user_id: str,
        user: Dict,
        sender: str,
        game: TexasHoldemGame,
        file_queue,
        final_balance: Optional[int] = None,
    ) -> bool:
        table_path = os.path.join(self.results_folder, f"poker_{user_id}_{int(time.time())}.png")
        self.renderer.generate(
            game=game,
            sender=sender,
            output_path=table_path,
            background_path=self._get_user_background_path(user_id),
        )

        if final_balance is None:
            final_balance = user.get("balance", 0) if user else 0

        win_value = game.net_win if game.status == "finished" else 0
        user_info = self.create_user_info(sender, game.player_committed, win_value, final_balance, user)

        avatar_path = None
        background_path = None
        if hasattr(self, "cache") and self.cache:
            avatar_path = self.cache.get_avatar_path(user_id)
            background_path = self.cache.get_background_path(user_id)

        if (
            not avatar_path
            or not background_path
            or not os.path.exists(avatar_path)
            or not os.path.exists(background_path)
        ):
            file_queue.put(table_path)
            return True

        try:
            result_path = self.generate_static(
                image_path=table_path,
                avatar_path=avatar_path,
                bg_path=background_path,
                user_info=user_info,
                show_bet_amount=True,
                show_win_text=game.status == "finished",
                font_scale=0.8,
                avatar_size=62,
                win_text_scale=0.8,
                win_text_height=66,
            )
            if result_path:
                file_queue.put(result_path)
                return True
        except Exception as exc:
            logger.error(f"[Poker] Could not apply user overlay: {exc}", exc_info=True)

        file_queue.put(table_path)
        return True

    def _finish_if_needed(self, user_id: str, user: Dict, sender: str, game: TexasHoldemGame, file_queue):
        if game.status != "finished":
            self.save_game_state(user_id, game)
            return user.get("balance", 0)

        final_balance = user.get("balance", 0)
        if game.payout > 0:
            final_balance += game.payout
            self.update_user_balance(user_id, final_balance)
            user["balance"] = final_balance

        try:
            new_level, new_progress = self.cache.add_experience(user_id, game.net_win, sender, file_queue)
            user["level"] = new_level
            user["level_progress"] = new_progress
        except Exception as exc:
            logger.error(f"[Poker] Could not add experience: {exc}", exc_info=True)

        if game.net_win > 0:
            record_weekly_win(self.cache, user_id, "poker", game.net_win)

        self._clear_game(user_id)
        return final_balance

    def _charge_player(self, user_id: str, user: Dict, amount: int) -> bool:
        if amount <= 0:
            return True
        if user.get("balance", 0) < amount:
            return False
        new_balance = user["balance"] - amount
        self.update_user_balance(user_id, new_balance)
        user["balance"] = new_balance
        return True

    def _pending_player_cost(self, game: TexasHoldemGame, cmd: str, amount: int = 0) -> int:
        if cmd == "start":
            return amount
        if cmd == "call":
            return game.to_call
        if cmd == "bet":
            return amount
        if cmd == "raise":
            if game.to_call > 0:
                return game.to_call + amount
            return amount
        return 0

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache

        if not sender:
            return ""

        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        if error:
            self.send_message_image(sender, file_queue, error, "Poker Error", cache, user_id)
            return ""

        if len(args) == 0:
            game = self.load_game_state(user_id)
            if game:
                self._send_game_image(user_id, user, sender, game, file_queue)
                return ""
            self._send_help(sender, file_queue, cache, user_id)
            return ""

        cmd = args[0].lower()

        if cmd in {"help", "h", "rules"}:
            self._send_help(sender, file_queue, cache, user_id)
            return ""

        if cmd in {"start", "play", "deal"} or cmd.isdigit():
            if self.load_game_state(user_id):
                self.send_message_image(sender, file_queue, "You already have an active poker hand.", "Poker", cache, user_id)
                return ""

            if cmd.isdigit():
                ante = int(cmd)
                ante_error = None if ante >= self.min_bet else f"Minimum ante is {self.min_bet}."
            else:
                ante, ante_error = self._parse_amount(args, 1)

            if ante_error:
                self.send_message_image(sender, file_queue, ante_error, "Poker Error", cache, user_id)
                return ""

            if not self._charge_player(user_id, user, ante):
                self.send_message_image(sender, file_queue, f"Insufficient funds. You need {ante}.", "Poker Error", cache, user_id)
                return ""

            game = TexasHoldemGame(user_id, sender, ante)
            self.active_games[user_id] = game
            self.save_game_state(user_id, game)
            self._send_game_image(user_id, user, sender, game, file_queue)
            logger.info(f"[Poker] Started Hold'em hand for {sender}, ante={ante}")
            return f"Texas Hold'em started. Ante: {ante}."

        game = self.load_game_state(user_id)
        if not game:
            self.send_message_image(sender, file_queue, "No active poker hand. Use /poker start <ante>.", "Poker", cache, user_id)
            return ""

        success = False
        message = ""
        amount = 0

        if cmd in {"status", "table"}:
            self._send_game_image(user_id, user, sender, game, file_queue)
            return ""

        if cmd in {"check", "ch"}:
            success, message = game.player_check()

        elif cmd in {"call", "c"}:
            cost = self._pending_player_cost(game, "call")
            if not self._charge_player(user_id, user, cost):
                self.send_message_image(sender, file_queue, f"Insufficient funds. Need {cost} to call.", "Poker Error", cache, user_id)
                return ""
            success, message = game.player_call()

        elif cmd in {"bet", "b"}:
            amount, amount_error = self._parse_amount(args, 1)
            if amount_error:
                self.send_message_image(sender, file_queue, amount_error, "Poker Error", cache, user_id)
                return ""
            cost = self._pending_player_cost(game, "bet", amount)
            if not self._charge_player(user_id, user, cost):
                self.send_message_image(sender, file_queue, f"Insufficient funds. Need {cost} to bet.", "Poker Error", cache, user_id)
                return ""
            success, message = game.player_bet(amount)
            if not success:
                user["balance"] += cost
                self.update_user_balance(user_id, user["balance"])

        elif cmd in {"raise", "r"}:
            amount, amount_error = self._parse_amount(args, 1)
            if amount_error:
                self.send_message_image(sender, file_queue, amount_error, "Poker Error", cache, user_id)
                return ""
            cost = self._pending_player_cost(game, "raise", amount)
            if not self._charge_player(user_id, user, cost):
                self.send_message_image(sender, file_queue, f"Insufficient funds. Need {cost} to raise.", "Poker Error", cache, user_id)
                return ""
            success, message = game.player_raise(amount)
            if not success:
                user["balance"] += cost
                self.update_user_balance(user_id, user["balance"])

        elif cmd in {"fold", "f"}:
            success, message = game.player_fold()

        else:
            self._send_help(sender, file_queue, cache, user_id)
            return ""

        if not success:
            self.send_message_image(sender, file_queue, message, "Poker Error", cache, user_id)
            return ""

        final_balance = self._finish_if_needed(user_id, user, sender, game, file_queue)
        self._send_game_image(user_id, user, sender, game, file_queue, final_balance=final_balance)

        logger.info(
            f"[Poker] {sender} action={cmd} amount={amount} stage={game.stage} "
            f"status={game.status} pot={game.pot} committed={game.player_committed} "
            f"net={game.net_win} balance={final_balance}"
        )
        return message


def register():
    logger.info("[Poker] Registering Texas Hold'em plugin")
    plugin = PokerPlugin()
    return {
        "name": "poker",
        "aliases": ["/pk"],
        "description": (
            "Texas Hold'em against the bot.\n\n"
            "Commands:\n"
            "- /poker start <ante> - Start a hand with 2 hole cards\n"
            "- /poker <ante> - Quick start\n"
            "- /poker - Show current table\n"
            "- /poker check - Check when no bet is pending\n"
            "- /poker bet <amount> - Open betting\n"
            "- /poker call - Call bot bet\n"
            "- /poker raise <amount> - Call and raise\n"
            "- /poker fold - Fold\n\n"
            "The hand plays through preflop, flop, turn, river, and showdown unless someone folds."
        ),
        "execute": plugin.execute_game,
    }
