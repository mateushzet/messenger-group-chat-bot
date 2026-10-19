# plugins/poker2.py

import os
import random
import time
from functools import lru_cache
from typing import Dict, List, Optional

from PIL import Image, ImageDraw, ImageFilter

from base_game_plugin import BaseGamePlugin
from logger import logger
from plugins.monthly import record_monthly_win
from plugins.weekly import record_weekly_win
from plugins.dailyquest import record_daily_win
from plugins.poker import PokerHand


RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = ["S", "H", "D", "C"]
RANK_VALUES = {rank: index + 2 for index, rank in enumerate(RANKS)}
RED_SUITS = {"H", "D"}

HAND_COUNT = 4
MC_PREFLOP = 800
MC_POSTFLOP = 400

F_HOLD_PREFLOP = 6
F_TRANS_CARD = 12
F_HOLD_CARD = 5
F_PAUSE_BETWEEN = 3
F_SHOWDOWN = 12

PREVIEW_HEIGHT = 310


@lru_cache(maxsize=200000)
def _cached_hand_score(cards_tuple):
    return PokerHand(list(cards_tuple)).score


class Poker2Game:
    def __init__(self, bet: int, seed: Optional[int] = None):
        self.bet = bet
        self.rng = random.Random(seed if seed is not None else time.time_ns())

        self.deck = self._build_deck()
        self.hands: List[List[str]] = []
        self.board: List[str] = []
        self.equity_preflop: List[float] = []
        self.multipliers: List[float] = []
        self.equity_by_stage: List[List[float]] = []

        self.chosen_hand: Optional[int] = None
        self.winners: List[int] = []
        self.payout: int = 0
        self.net_win: int = 0
        self.stage: str = "awaiting_pick"
        self.finished: bool = False

        self._deal_hands()
        self._compute_preflop_equity()
        self._precompute_board_and_equities()

    def _build_deck(self) -> List[str]:
        deck = [f"{rank}{suit}" for suit in SUITS for rank in RANKS]
        self.rng.shuffle(deck)
        return deck

    def _draw(self) -> str:
        if not self.deck:
            self.deck = self._build_deck()
        return self.deck.pop()

    def _deal_hands(self):
        self.hands = []
        for _ in range(HAND_COUNT):
            self.hands.append([self._draw(), self._draw()])

    def _compute_preflop_equity(self):
        wins = [0] * HAND_COUNT
        ties = [0.0] * HAND_COUNT
        trials = MC_PREFLOP

        for _ in range(trials):
            temp_deck = self.deck[:]
            self.rng.shuffle(temp_deck)
            board = [temp_deck.pop() for _ in range(5)]
            scores = [_cached_hand_score(tuple(sorted(hand + board))) for hand in self.hands]
            best = max(scores)
            winners = [i for i, s in enumerate(scores) if s == best]
            if len(winners) == 1:
                wins[winners[0]] += 1
            else:
                for w in winners:
                    ties[w] += 1.0 / len(winners)

        equities = [(wins[i] + ties[i]) / trials for i in range(HAND_COUNT)]
        self.equity_preflop = equities
        self.multipliers = [1.0 / (eq + 0.02) for eq in equities]

    def _precompute_board_and_equities(self):
        while len(self.board) < 5:
            self.board.append(self._draw())

        self.equity_by_stage = [self.equity_preflop[:]]
        for k in range(1, 6):
            if k == 5:
                eq = self._river_equity(self.board[:5])
            else:
                eq = self._mc_equity(self.board[:k], MC_POSTFLOP)
            self.equity_by_stage.append(eq)

    def _mc_equity(self, partial_board, trials):
        wins = [0] * HAND_COUNT
        ties = [0.0] * HAND_COUNT
        needed = 5 - len(partial_board)

        for _ in range(trials):
            temp_deck = self.deck[:]
            self.rng.shuffle(temp_deck)
            extra = [temp_deck.pop() for _ in range(needed)]
            full_board = partial_board + extra
            scores = [_cached_hand_score(tuple(sorted(hand + full_board))) for hand in self.hands]
            best = max(scores)
            winners = [i for i, s in enumerate(scores) if s == best]
            if len(winners) == 1:
                wins[winners[0]] += 1
            else:
                for w in winners:
                    ties[w] += 1.0 / len(winners)

        return [(wins[i] + ties[i]) / trials for i in range(HAND_COUNT)]

    def _river_equity(self, board):
        scores = [_cached_hand_score(tuple(sorted(hand + board))) for hand in self.hands]
        best = max(scores)
        winners = [i for i, s in enumerate(scores) if s == best]
        eq = [0.0] * HAND_COUNT
        for w in winners:
            eq[w] = 1.0 / len(winners)
        return eq

    def settle(self):
        if self.chosen_hand is None:
            return
        scores = [_cached_hand_score(tuple(sorted(hand + self.board[:5]))) for hand in self.hands]
        best = max(scores)
        self.winners = [i for i, s in enumerate(scores) if s == best]

        mult = self.multipliers[self.chosen_hand]
        if self.chosen_hand in self.winners:
            gross = self.bet * mult
            share = gross / len(self.winners)
            self.payout = int(share)
            self.net_win = self.payout - self.bet
        else:
            self.payout = 0
            self.net_win = -self.bet

        self.finished = True
        self.stage = "finished"

    def serialize(self) -> Dict:
        return {
            "bet": self.bet,
            "deck": self.deck,
            "hands": self.hands,
            "board": self.board,
            "equity_preflop": self.equity_preflop,
            "equity_by_stage": self.equity_by_stage,
            "multipliers": self.multipliers,
            "chosen_hand": self.chosen_hand,
            "winners": self.winners,
            "payout": self.payout,
            "net_win": self.net_win,
            "stage": self.stage,
            "finished": self.finished,
        }

    @classmethod
    def deserialize(cls, data: Dict) -> "Poker2Game":
        game = cls.__new__(cls)
        game.bet = data.get("bet", 0)
        game.rng = random.Random()
        game.deck = data.get("deck", [])
        game.hands = data.get("hands", [])
        game.board = data.get("board", [])
        game.equity_preflop = data.get("equity_preflop", [])
        game.equity_by_stage = data.get("equity_by_stage", [])
        game.multipliers = data.get("multipliers", [])
        game.chosen_hand = data.get("chosen_hand")
        game.winners = data.get("winners", [])
        game.payout = data.get("payout", 0)
        game.net_win = data.get("net_win", 0)
        game.stage = data.get("stage", "awaiting_pick")
        game.finished = data.get("finished", False)
        return game


def _lerp(a, b, t):
    return a + (b - a) * t


def _lerp_list(a_list, b_list, t):
    return [_lerp(a_list[i], b_list[i], t) for i in range(len(a_list))]


def _card_rank(card: str) -> str:
    """Zwraca rangę karty bez koloru (np. 'AH' -> 'A', '10S' -> '10')."""
    return card[:-1]


class Poker2Renderer:
    # render od razu w mniejszym rozmiarze (~0.55 oryginału)
    WIDTH = 420
    HEIGHT = 432
    CARD_W_HAND = 60
    CARD_W_BOARD = 56
    CARD_H = 72
    CARD_GAP = 3

    def __init__(self, text_renderer, card_assets_dir: str):
        self.text_renderer = text_renderer
        self.card_assets_dir = card_assets_dir
        self._card_cache: Dict[str, Image.Image] = {}

    def _card_filename(self, card: str) -> Optional[str]:
        if not card or len(card) < 2:
            return None
        suit = card[-1].upper()
        rank = card[:-1].upper()
        suit_map = {"S": "spades", "H": "hearts", "D": "diamonds", "C": "clubs"}
        suit_name = suit_map.get(suit)
        if not suit_name:
            return None
        if rank in {"J", "Q", "K", "A"}:
            rank_part = rank
        else:
            try:
                value = int(rank)
            except ValueError:
                return None
            if value < 2 or value > 10:
                return None
            rank_part = f"{value:02d}"
        return f"card_{suit_name}_{rank_part}.png"

    def _load_card_raw(self, filename: str) -> Optional[Image.Image]:
        if not filename:
            return None
        cached = self._card_cache.get(filename)
        if cached is not None:
            return cached
        path = os.path.join(self.card_assets_dir, filename)
        try:
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                self._card_cache[filename] = img
                return img
        except Exception as exc:
            logger.warning(f"[Poker2] Failed to load card {filename}: {exc}")
        self._card_cache[filename] = None
        return None

    def _text(self, text, size, color, stroke=0):
        return self.text_renderer.render_text(
            text=text,
            font_size=size,
            color=color,
            stroke_width=stroke,
            stroke_color=(0, 0, 0, 220),
            shadow=stroke == 0,
            shadow_color=(0, 0, 0, 160),
            shadow_offset=(1, 1),
        )

    def _load_background(self, background_path: Optional[str], shade_alpha: int = 190, height: Optional[int] = None):
        h = height or self.HEIGHT
        if background_path and os.path.exists(background_path):
            try:
                bg = Image.open(background_path).convert("RGBA")
                bg = bg.resize((self.WIDTH, h), Image.Resampling.LANCZOS)
                shade = Image.new("RGBA", (self.WIDTH, h), (5, 8, 14, shade_alpha))
                return Image.alpha_composite(bg, shade).convert("RGBA")
            except Exception as exc:
                logger.warning(f"[Poker2] Background error: {exc}")
        return Image.new("RGBA", (self.WIDTH, h), (9, 14, 24, 255))

    def _draw_card(self, canvas, card, x, y, card_w, alpha=255):
        if card == "BACK":
            filename = "card_back.png"
        else:
            filename = self._card_filename(card)

        asset = self._load_card_raw(filename) if filename else None
        if asset is not None:
            orig_w, orig_h = asset.size
            orig_ratio = orig_w / orig_h
            target_ratio = card_w / self.CARD_H
            if orig_ratio > target_ratio:
                new_w = card_w
                new_h = int(card_w / orig_ratio)
            else:
                new_h = self.CARD_H
                new_w = int(self.CARD_H * orig_ratio)
            resized = asset.resize((new_w, new_h), Image.Resampling.LANCZOS)

            if alpha < 255:
                r, g, b, a = resized.split()
                a = a.point(lambda v: int(v * alpha / 255))
                resized = Image.merge("RGBA", (r, g, b, a))

            offset_x = x + (card_w - new_w) // 2
            offset_y = y + (self.CARD_H - new_h) // 2
            canvas.alpha_composite(resized, (offset_x, offset_y))
            return

        if card == "BACK":
            return
        draw = ImageDraw.Draw(canvas)
        rect = [x, y, x + card_w, y + self.CARD_H]
        suit = card[-1]
        rank = card[:-1]
        color = (210, 45, 55, 255) if suit in RED_SUITS else (24, 28, 34, 255)
        draw.rounded_rectangle(rect, radius=5, fill=(248, 248, 242, 255),
                               outline=(42, 42, 48, 255), width=1)
        label = self._text(f"{rank}{suit}", 14, color, stroke=1)
        canvas.alpha_composite(
            label,
            (x + (card_w - label.width) // 2,
             y + (self.CARD_H - label.height) // 2)
        )

    def _highlight_card(self, canvas, x, y, card_w, card_h,
                        color=(255, 255, 255, 90), spread=8, radius=10,
                        alpha=255, blur=6):
        """Rysuje bardzo subtelny, rozmyty glow wokół karty."""
        if alpha <= 0:
            return

        pad = spread * 2
        glow_w = card_w + pad * 2
        glow_h = card_h + pad * 2
        glow = Image.new("RGBA", (glow_w, glow_h), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)

        c = color if len(color) == 4 else (*color, 255)
        if alpha < 255:
            c = (c[0], c[1], c[2], int(c[3] * alpha / 255))

        gdraw.rounded_rectangle(
            [pad, pad, pad + card_w, pad + card_h],
            radius=radius, fill=c
        )

        glow = glow.filter(ImageFilter.GaussianBlur(blur))
        canvas.alpha_composite(glow, (x - pad, y - pad))

    def _draw_hand_cards(self, canvas, hand, center_x, y):
        total = 2 * self.CARD_W_HAND + self.CARD_GAP
        start_x = center_x - total // 2
        positions = []
        for i, card in enumerate(hand):
            cx = start_x + i * (self.CARD_W_HAND + self.CARD_GAP)
            self._draw_card(canvas, card, cx, y, self.CARD_W_HAND)
            positions.append((cx, card))
        return start_x, total, positions

    def _render_frame(self, base_bg, game, chosen_hand, board_count,
                      equity_now, show_result, winners=None, preview=False,
                      reveal_alpha=1.0):
        canvas = base_bg.copy().convert("RGBA")
        draw = ImageDraw.Draw(canvas)

        W = self.WIDTH
        H = canvas.height

        panel_alpha = 120 if preview else 255
        draw.rounded_rectangle(
            [10, 9, W - 10, H - 9],
            radius=14, fill=(15, 28, 35, panel_alpha),
            outline=(85, 95, 110, 180), width=1
        )

        if not show_result:
            headline = "POKER 2"
            headline_color = (255, 215, 0, 255)
        else:
            if winners and len(winners) == 1:
                headline = f"WINNER: HAND {winners[0] + 1}"
            else:
                headline = "SPLIT POT"
            chosen_won = (chosen_hand is not None and winners and chosen_hand in winners)
            headline_color = (90, 220, 130, 255) if chosen_won else (255, 90, 90, 255)

        head_img = self._text(headline, 14, headline_color, stroke=1)
        canvas.alpha_composite(head_img, ((W - head_img.width) // 2, 16))

        grid_top = 38
        if preview:
            grid_bottom = H - 28
        else:
            grid_bottom = H - 128
        grid_left = 20
        grid_right = W - 20
        col_w = (grid_right - grid_left) // 2
        row_h = (grid_bottom - grid_top) // 2

        chosen_won = (show_result and chosen_hand is not None
                      and winners and chosen_hand in winners)

        hand_ranks_set = set()
        for hand in game.hands:
            for c in hand:
                hand_ranks_set.add(_card_rank(c))

        board_revealed_ranks = set(
            _card_rank(c) for c in game.board[:board_count]
        ) if board_count > 0 else set()

        hand_card_positions = []

        for i, hand in enumerate(game.hands):
            row = i // 2
            col = i % 2
            cell_cx = grid_left + col * col_w + col_w // 2
            cell_cy = grid_top + row * row_h + row_h // 2

            is_chosen = (chosen_hand == i)
            is_winner = show_result and winners and i in winners

            cell_pad = 6
            cell_box = [
                grid_left + col * col_w + cell_pad,
                grid_top + row * row_h + cell_pad,
                grid_left + (col + 1) * col_w - cell_pad,
                grid_top + (row + 1) * row_h - cell_pad,
            ]

            if preview:
                cell_fill = (20, 30, 42, 200)
                cell_outline = (60, 75, 100, 200)
                cell_width = 1
                if is_winner:
                    if chosen_won:
                        cell_fill = (25, 60, 40, 220)
                        cell_outline = (90, 220, 130, 255)
                        cell_width = 2
                    else:
                        cell_fill = (60, 25, 25, 220)
                        cell_outline = (220, 90, 90, 255)
                        cell_width = 2
                elif is_chosen:
                    cell_outline = (255, 215, 0, 255)
                    cell_width = 2
            else:
                cell_fill = (20, 30, 42, 255)
                cell_outline = (60, 75, 100, 255)
                cell_width = 1
                if is_winner:
                    if chosen_won:
                        cell_fill = (25, 60, 40, 255)
                        cell_outline = (90, 220, 130, 255)
                        cell_width = 2
                    else:
                        cell_fill = (60, 25, 25, 255)
                        cell_outline = (220, 90, 90, 255)
                        cell_width = 2
                elif is_chosen:
                    cell_outline = (255, 215, 0, 255)
                    cell_width = 2

            draw.rounded_rectangle(cell_box, radius=8,
                                   fill=cell_fill, outline=cell_outline,
                                   width=cell_width)

            label_color = (220, 225, 235, 255)
            if is_chosen:
                label_color = (255, 215, 0, 255)
            if is_winner:
                label_color = (90, 220, 130, 255) if chosen_won else (255, 90, 90, 255)

            num_label = self._text(f"#{i + 1}", 10, label_color, stroke=1)
            canvas.alpha_composite(num_label, (cell_box[0] + 6, cell_box[1] + 4))

            mult_label = self._text(f"{game.multipliers[i]:.2f}x", 10, label_color, stroke=1)
            mult_y = cell_box[1] + 4
            canvas.alpha_composite(mult_label, (cell_cx - mult_label.width // 2, mult_y))

            cards_y = mult_y + mult_label.height + 4
            start_x, total_w, positions = self._draw_hand_cards(
                canvas, hand, cell_cx, cards_y
            )
            for cx, card in positions:
                hand_card_positions.append((card, cx, cards_y))

            if equity_now is not None:
                eq = equity_now[i]
                bar_w = total_w
                bar_x = cell_cx - bar_w // 2
                bar_y = cards_y + self.CARD_H + 4
                draw.rounded_rectangle(
                    [bar_x, bar_y, bar_x + bar_w, bar_y + 4],
                    radius=2, fill=(40, 45, 60, 255)
                )
                fill_w = int(bar_w * max(0.0, min(1.0, eq)))
                if fill_w > 0:
                    if is_winner:
                        bar_color = (90, 220, 130, 255) if chosen_won else (220, 90, 90, 255)
                    elif is_chosen:
                        bar_color = (255, 215, 0, 255)
                    else:
                        bar_color = (90, 150, 220, 255)
                    draw.rounded_rectangle(
                        [bar_x, bar_y, bar_x + fill_w, bar_y + 4],
                        radius=2, fill=bar_color
                    )

        for card, cx, cy in hand_card_positions:
            if _card_rank(card) in board_revealed_ranks:
                self._highlight_card(
                    canvas, cx, cy,
                    self.CARD_W_HAND, self.CARD_H,
                    color=(255, 255, 255, 90), spread=8, radius=10,
                    alpha=255, blur=6,
                )

        if not preview:
            board_label_y = H - 116
            board_label = self._text("BOARD", 8, (190, 198, 210, 255), stroke=1)
            canvas.alpha_composite(board_label,
                                   ((W - board_label.width) // 2,
                                    board_label_y))

            board_y = board_label_y + 12
            total = 5 * self.CARD_W_BOARD + 4 * self.CARD_GAP
            start_x = (W - total) // 2

            for i in range(5):
                x = start_x + i * (self.CARD_W_BOARD + self.CARD_GAP)

                if i >= board_count:
                    self._draw_card(canvas, "BACK", x, board_y, self.CARD_W_BOARD)
                elif i == board_count - 1 and reveal_alpha < 1.0:
                    back_alpha = int(255 * (1.0 - reveal_alpha))
                    if back_alpha > 0:
                        self._draw_card(canvas, "BACK", x, board_y,
                                        self.CARD_W_BOARD, alpha=back_alpha)
                    card_alpha = int(255 * reveal_alpha)
                    if card_alpha > 0:
                        self._draw_card(canvas, game.board[i], x, board_y,
                                        self.CARD_W_BOARD, alpha=card_alpha)

                    if _card_rank(game.board[i]) in hand_ranks_set and reveal_alpha > 0:
                        self._highlight_card(
                            canvas, x, board_y,
                            self.CARD_W_BOARD, self.CARD_H,
                            color=(255, 255, 255, 90), spread=8, radius=10,
                            alpha=int(255 * reveal_alpha), blur=6,
                        )
                else:
                    self._draw_card(canvas, game.board[i], x, board_y, self.CARD_W_BOARD)
                    if _card_rank(game.board[i]) in hand_ranks_set:
                        self._highlight_card(
                            canvas, x, board_y,
                            self.CARD_W_BOARD, self.CARD_H,
                            color=(255, 255, 255, 90), spread=8, radius=10,
                            alpha=255, blur=6,
                        )

        if preview:
            note = "Pick a hand:   /pk2 <1-4>"
            note_img = self._text(note, 10, (255, 215, 0, 255), stroke=1)
            canvas.alpha_composite(
                note_img,
                ((W - note_img.width) // 2, H - 28)
            )

        return canvas

    def generate_animation(self, game: Poker2Game, output_path: str,
                           background_path: Optional[str] = None,
                           chosen_hand: Optional[int] = None) -> bool:
        base_bg = self._load_background(background_path)

        frames: List[Image.Image] = []
        durations: List[int] = []

        eq_stages = game.equity_by_stage
        if not eq_stages or len(eq_stages) < 6:
            logger.error("[Poker2] equity_by_stage missing or incomplete")
            return False

        for _ in range(F_HOLD_PREFLOP):
            frames.append(self._render_frame(
                base_bg, game, chosen_hand, 0, eq_stages[0], False,
                reveal_alpha=1.0
            ))
            durations.append(150)

        for k in range(1, 6):
            eq_from = eq_stages[k - 1]
            eq_to = eq_stages[k]

            for j in range(F_TRANS_CARD):
                t = (j + 1) / F_TRANS_CARD
                eq_now = _lerp_list(eq_from, eq_to, t)
                frames.append(self._render_frame(
                    base_bg, game, chosen_hand, k, eq_now, False,
                    reveal_alpha=t
                ))
                durations.append(120)

            for _ in range(F_HOLD_CARD):
                frames.append(self._render_frame(
                    base_bg, game, chosen_hand, k, eq_to, False,
                    reveal_alpha=1.0
                ))
                durations.append(200)

            if k < 5:
                for _ in range(F_PAUSE_BETWEEN):
                    frames.append(self._render_frame(
                        base_bg, game, chosen_hand, k, eq_to, False,
                        reveal_alpha=1.0
                    ))
                    durations.append(500)

        for _ in range(F_SHOWDOWN):
            frames.append(self._render_frame(
                base_bg, game, chosen_hand, 5, eq_stages[5], True,
                winners=game.winners, reveal_alpha=1.0
            ))
            durations.append(200)

        if not frames:
            return False

        try:
            frames[0].save(
                output_path,
                format="WEBP",
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=0,
                quality=82,
                method=3,
                minimize_size=True,
            )
            return True
        except Exception as exc:
            logger.error(f"[Poker2] save animation error: {exc}")
            return False


class Poker2Plugin(BaseGamePlugin):
    CACHE_KEY = "poker2_active_games"

    def __init__(self):
        super().__init__(game_name="poker2")
        os.makedirs(self.results_folder, exist_ok=True)
        self.active_games: Dict[str, Poker2Game] = {}
        self.cache_loaded = False
        self.cache = None
        self.card_assets_dir = self.get_asset_path("blackjack", "board_elements")
        self.renderer = Poker2Renderer(self.text_renderer, self.card_assets_dir)

    def _save_games(self):
        if not self.cache:
            return
        try:
            data = {uid: g.serialize() for uid, g in self.active_games.items()}
            self.cache.set_setting(self.CACHE_KEY, data)
        except Exception as exc:
            logger.error(f"[Poker2] save error: {exc}")

    def _load_games(self):
        if not self.cache or self.cache_loaded:
            return
        self.cache_loaded = True
        try:
            data = self.cache.get_setting(self.CACHE_KEY) or {}
            if not isinstance(data, dict):
                return
            for uid, raw in data.items():
                try:
                    game = Poker2Game.deserialize(raw)
                    if not game.finished:
                        self.active_games[str(uid)] = game
                except Exception as exc:
                    logger.error(f"[Poker2] restore {uid}: {exc}")
            self._save_games()
        except Exception as exc:
            logger.error(f"[Poker2] load error: {exc}")

    def _user_bg(self, user_id):
        if self.cache:
            path = self.cache.get_background_path(user_id)
            if path and os.path.exists(path):
                return path
        return None

    def _send_preview(self, user_id, sender, game, file_queue):
        path = os.path.join(
            self.results_folder,
            f"poker2_{user_id}_preview_{int(time.time() * 1000)}.png"
        )
        base_bg = self.renderer._load_background(
            self._user_bg(user_id), shade_alpha=110, height=PREVIEW_HEIGHT
        )
        frame = self.renderer._render_frame(
            base_bg, game, None, 0, None, False, preview=True,
            reveal_alpha=1.0
        )
        final = Image.new("RGB", frame.size, (0, 0, 0))
        final.paste(frame, (0, 0), frame)
        final.save(path, "PNG")

        avatar = self.cache.get_avatar_path(user_id) if self.cache else None
        bg = self.cache.get_background_path(user_id) if self.cache else None

        if not avatar or not bg or not os.path.exists(avatar) or not os.path.exists(bg):
            file_queue.put(path)
            return

        user = self.cache.get_user(user_id)
        user_info = self.create_user_info(
            sender, game.bet, 0,
            user.get("balance", 0) if user else 0, user
        )
        try:
            result_path = self.generate_static(
                image_path=path,
                avatar_path=avatar,
                bg_path=bg,
                user_info=user_info,
                show_bet_amount=True,
                show_win_text=False,
                font_scale=0.8,
                avatar_size=55,
                win_text_scale=0.8,
                win_text_height=90,
            )
            if result_path:
                file_queue.put(result_path)
            else:
                file_queue.put(path)
        except Exception as exc:
            logger.error(f"[Poker2] preview overlay error: {exc}", exc_info=True)
            file_queue.put(path)

    def _send_animation(self, user_id, sender, game, file_queue):
        path = os.path.join(
            self.results_folder,
            f"poker2_{user_id}_{int(time.time() * 1000)}.webp"
        )
        ok = self.renderer.generate_animation(
            game, path,
            background_path=self._user_bg(user_id),
            chosen_hand=game.chosen_hand,
        )
        if not ok:
            logger.error("[Poker2] animation generation failed")
            return

        avatar = self.cache.get_avatar_path(user_id) if self.cache else None
        bg = self.cache.get_background_path(user_id) if self.cache else None

        if not avatar or not bg or not os.path.exists(avatar) or not os.path.exists(bg):
            file_queue.put(path)
            return

        user = self.cache.get_user(user_id)
        balance_after = user.get("balance", 0) if user else 0
        balance_before = balance_after - game.net_win

        # NEUTRALNY overlay — używany na wszystkich klatkach oprócz ostatniej
        user_info_before = self.create_user_info(
            sender, game.bet,
            0,                    # win = 0 → is_win = False → neutralny kolor
            balance_before,
            user
        )

        # OVERLAY Z WYNIKIEM — używany tylko na ostatniej klatce
        user_info_after = self.create_user_info(
            sender, game.bet,
            game.net_win,         # tutaj dopiero win → is_win = net_win > 0
            balance_after,
            user
        )

        try:
            result_path = self.generate_animation(
                base_animation_path=path,
                user_id=user_id,
                user=user,
                user_info_before=user_info_before,
                user_info_after=user_info_after,
                animated=True,
                frame_duration=90,
                last_frame_multiplier=8,
                show_win_text=True,
                font_scale=0.8,
                avatar_size=55,
                win_text_height=290,
                quality=50,
            )
            if result_path:
                file_queue.put(result_path[0] if isinstance(result_path, tuple) else result_path)
            else:
                file_queue.put(path)
        except Exception as exc:
            logger.error(f"[Poker2] overlay error: {exc}", exc_info=True)
            file_queue.put(path)
       
    def _send_help(self, sender, file_queue, cache, user_id):
        self.send_message_image(
            sender, file_queue,
            "Poker 2 (pk2)\n\n"
            "4 hands are dealt face-up with multipliers.\n"
            "Pick ONE hand. If it wins the showdown, you get bet x multiplier.\n"
            "Ties split the pot between winners.\n\n"
            "Commands:\n"
            "- /pk2 <bet>      start a new round\n"
            "- /pk2 <1-4>      pick a hand\n"
            "- /pk2            show current round\n"
            "- /pk2 help       this message\n\n"
            "Example:\n"
            "/pk2 200\n"
            "/pk2 2",
            "Poker 2 - Help", cache, user_id
        )

    def execute_game(self, command_name, args, file_queue, cache=None,
                     sender=None, avatar_url=None):
        self.cache = cache
        self._load_games()

        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        user_id = str(user_id)
        if error:
            self.send_message_image(sender, file_queue, error,
                                    "Poker 2 - Error", cache, user_id)
            return ""

        if not args:
            game = self.active_games.get(user_id)
            if not game:
                self._send_help(sender, file_queue, cache, user_id)
                return ""
            self._send_preview(user_id, sender, game, file_queue)
            return ""

        cmd = args[0].lower()

        if cmd in {"help", "h", "?"}:
            self._send_help(sender, file_queue, cache, user_id)
            return ""

        if not cmd.isdigit():
            self._send_help(sender, file_queue, cache, user_id)
            return ""

        number = int(cmd)
        existing = self.active_games.get(user_id)

        if existing and existing.stage == "awaiting_pick":
            if number < 1 or number > HAND_COUNT:
                self.send_message_image(
                    sender, file_queue,
                    f"Pick a hand between 1 and {HAND_COUNT}.",
                    "Poker 2 - Error", cache, user_id
                )
                return ""

            game = existing
            game.chosen_hand = number - 1
            game.stage = "playing"
            game.settle()
            self._save_games()

            if game.payout > 0:
                new_balance = int(user.get("balance", 0)) + game.payout
                self.update_user_balance(user_id, new_balance)
                user["balance"] = new_balance

            try:
                self.cache.add_experience(user_id, game.net_win, sender, file_queue)
            except Exception as exc:
                logger.warning(f"[Poker2] xp error: {exc}")

            if game.net_win > 0:
                record_daily_win(self.cache, user_id, "poker", game.net_win)
                record_weekly_win(self.cache, user_id, "poker", game.net_win)
                record_monthly_win(self.cache, user_id, "poker", game.net_win)

            self._send_animation(user_id, sender, game, file_queue)

            self.active_games.pop(user_id, None)
            self._save_games()

            logger.info(
                f"[Poker2] {sender} bet={game.bet} pick={number} "
                f"winners={[w + 1 for w in game.winners]} "
                f"mult={game.multipliers[number - 1]:.2f} "
                f"payout={game.payout} net={game.net_win}"
            )
            return ""

        if existing:
            self.send_message_image(
                sender, file_queue,
                "You already have an active round. Pick a hand first with /pk2 <1-4>.",
                "Poker 2", cache, user_id
            )
            return ""

        bet = number
        if bet <= 0:
            self.send_message_image(sender, file_queue, "Bet must be positive.",
                                    "Poker 2 - Error", cache, user_id)
            return ""

        balance = int(user.get("balance", 0))
        if balance < bet:
            self.send_message_image(
                sender, file_queue,
                f"Insufficient funds.\nBet: {bet}\nBalance: {balance}",
                "Poker 2 - Error", cache, user_id
            )
            return ""

        self.update_user_balance(user_id, balance - bet)
        user["balance"] = balance - bet

        game = Poker2Game(bet)
        game.stage = "awaiting_pick"
        self.active_games[user_id] = game
        self._save_games()

        self._send_preview(user_id, sender, game, file_queue)
        return ""


def register():
    logger.info("[Poker2] Registering Poker 2 plugin")
    plugin = Poker2Plugin()
    return {
        "name": "poker2",
        "aliases": ["/pk2"],
        "description": (
            "Poker 2\n\n"
            "4 hands are dealt face-up with multipliers based on their preflop equity.\n"
            "Pick ONE hand. If it wins the showdown, you get bet x multiplier.\n"
            "Ties split the pot between winners.\n\n"
            "Commands:\n"
            "- /pk2 <bet>  start a new round\n"
            "- /pk2 <1-4>  pick a hand\n"
            "- /pk2        show current round\n"
            "- /pk2 help   help"
        ),
        "execute": plugin.execute_game,
    }