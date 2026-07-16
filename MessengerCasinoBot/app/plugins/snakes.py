import os
import random
import json
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List

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

    def is_finished(self) -> bool:
        return self.round_index >= self.TOTAL_ROUNDS or self.last_outcome == "snake"

    def distinct_multiplier_count(self) -> int:
        return (11 - self.difficulty.snakes) // 2

    def _generate_distinct_multipliers(self) -> List[float]:
        if self.difficulty.key == "easy":
            return [2.00, 1.30, 1.20, 1.10, 1.01]

        k = self.distinct_multiplier_count()
        if k <= 1:
            return [self.difficulty.max_mult]

        min_m = self.difficulty.min_mult
        max_m = self.difficulty.max_mult

        values: List[float] = []
        for i in range(k):
            t = i / (k - 1)
            v = max_m * ((min_m / max_m) ** t)
            values.append(round(v + 1e-9, 2))

        values[0] = round(max_m, 2)
        values[-1] = round(min_m, 2)
        return values

    def build_outcome_map(self) -> Dict[int, Optional[float]]:
        snakes = self.difficulty.snakes
        distinct = self._generate_distinct_multipliers()
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
        outcomes = self.build_outcome_map()
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

        logger.info(f"[Snakes] Roll: sum={s}, mult={m}, cumulative={self.cumulative_multiplier}, round={self.round_index}")

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
        return game


class SnakesAnimationCache:
    def __init__(self):
        self.base_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "assets", 
            "snake", 
            "pre_generated_animations"
        )
        self.metadata_path = os.path.join(self.base_path, "metadata.json")
        self.metadata = {}
        self.cache = {}
        self._load_metadata()
        
    def _load_metadata(self):
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                logger.info(f"[Snakes] Loaded metadata with {len(self.metadata)} entries")
            except Exception as e:
                logger.error(f"[Snakes] Error loading metadata: {e}")
                self.metadata = {}
        else:
            logger.warning(f"[Snakes] Metadata not found at {self.metadata_path}")
            self.metadata = {}
    
    def get_animation_path(self, difficulty: str, round_num: int, sum_val: int, 
                          prev_mult: float, outcome: str = 'multiplier') -> Optional[str]:
        prev_mult_rounded = round(prev_mult, 2)
        
        if round_num == 1 and outcome == 'snake':
            prev_mult_rounded = 1.0
        
        if outcome == 'snake':
            key = f"{difficulty}_round{round_num}_sum{sum_val}_snake_{prev_mult_rounded:.2f}x"
        else:
            key = f"{difficulty}_round{round_num}_sum{sum_val}_mult_{prev_mult_rounded:.2f}x"
        
        if key in self.cache:
            return self.cache[key]
        
        if key in self.metadata:
            filepath = self.metadata[key]['filepath']
            full_path = os.path.join(self.base_path, difficulty, filepath)
            if os.path.exists(full_path):
                self.cache[key] = full_path
                return full_path
        
        diff_path = os.path.join(self.base_path, difficulty)
        if os.path.exists(diff_path):
            best_match = None
            best_diff = float('inf')
            
            if outcome == 'snake':
                pattern = f"round{round_num}_sum{sum_val}_snake_"
            else:
                pattern = f"round{round_num}_sum{sum_val}_mult_"
            
            for filename in os.listdir(diff_path):
                if filename.endswith('.webp') and pattern in filename:
                    try:
                        parts = filename.replace('.webp', '').split('_')
                        for part in parts:
                            if part.endswith('x'):
                                val_str = part.replace('x', '')
                                file_mult = float(val_str)
                                diff = abs(file_mult - prev_mult)
                                if diff < best_diff:
                                    best_diff = diff
                                    best_match = filename
                    except:
                        continue
            
            if best_match:
                full_path = os.path.join(diff_path, best_match)
                self.cache[key] = full_path
                logger.info(f"[Snakes] Found closest match: {best_match} (diff={best_diff:.4f})")
                return full_path
        
        logger.warning(f"[Snakes] Animation not found: {key}")
        return None


class SnakesPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="snakes")
        self.active_games: Dict[str, Dict] = {}
        self.animation_cache = SnakesAnimationCache()
        logger.info("[Snakes] Plugin initialized")

    def _parse_difficulty(self, value: Optional[str]) -> SnakesDifficulty:
        if not value:
            return _DIFFICULTIES["medium"]
        key = value.strip().lower()
        if key in _DIFFICULTIES:
            return _DIFFICULTIES[key]
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

    def _get_animation_path(self, game: SnakesGame, round_num: int, sum_val: int, 
                           prev_mult: float, outcome: str = 'multiplier') -> Optional[str]:
        difficulty = game.difficulty.key
        
        if round_num == 1:
            prev_mult = 1.0
        
        return self.animation_cache.get_animation_path(
            difficulty, round_num, sum_val, prev_mult, outcome
        )

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache

        user_id, user, err = self.validate_user(cache, sender, avatar_url)
        if err or not user_id:
            return

        sender_display = sender
        balance_before = int(user.get("balance", 0))

        if not args:
            help_text = "SNAKES GAME\n\nUse:\n/sn <bet> [difficulty]\n/sn roll\n/sn cashout"
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

        if sub in ("roll", "r"):
            if user_id not in self.active_games:
                self.load_game_state(user_id)

            if user_id not in self.active_games:
                self.send_message_image(
                    nickname=sender_display,
                    file_queue=file_queue,
                    message="No active game. Start with: /sn <bet>",
                    title="Snakes - No Game",
                    cache=cache,
                    user_id=user_id,
                )
                return

            data = self.active_games.get(user_id)
            game: SnakesGame = data["game"]
            bet = data["bet"]
            balance_after_bet = data["balance_after_bet"]

            prev_mult = game.cumulative_multiplier
            prev_round = game.round_index

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

            base_anim_path = self._get_animation_path(
                game, game.round_index, game.last_sum, prev_mult, game.last_outcome
            )
            
            if not base_anim_path:
                logger.error(f"[Snakes] No animation: round={game.round_index}, sum={game.last_sum}, prev={prev_mult}")
                self.send_message_image(
                    nickname=sender_display,
                    file_queue=file_queue,
                    message="Animation not available. Please try again.",
                    title="Snakes - Error",
                    cache=cache,
                    user_id=user_id,
                )
                return

            if game.last_outcome == "snake":
                net_win = -bet
                try:
                    self.cache.add_experience(user_id, -bet, sender_display, file_queue)
                except:
                    pass

                user_info_before = self.create_user_info(sender_display, bet, 0, balance_after_bet, user)
                user_info_after = self.create_user_info(sender_display, bet, net_win, balance_after_bet, user)
                
                result_path, error = self.generate_animation(
                    base_animation_path=base_anim_path,
                    user_id=user_id,
                    user=user,
                    user_info_before=user_info_before,
                    user_info_after=user_info_after,
                    animated=True,
                    frame_duration=85,
                    last_frame_multiplier=20,
                    show_win_text=True,
                    win_text_height=5,
                    font_scale=0.7,
                    avatar_size=45
                )
                
                if result_path:
                    file_queue.put(result_path)
                self._clear_game(user_id)
                return

            if result.get("is_maxed"):
                payout = game.current_payout()
                net_win = payout - bet
                new_balance = balance_after_bet + payout
                try:
                    self.update_user_balance(user_id, new_balance)
                except Exception as e:
                    logger.error(f"[Snakes] Balance update failed: {e}")
                if net_win > 0:
                    record_weekly_win(self.cache, user_id, "snakes", net_win)

                try:
                    self.cache.add_experience(user_id, net_win, sender_display, file_queue)
                except:
                    pass

                user_info_before = self.create_user_info(sender_display, bet, 0, balance_after_bet, user)
                user_info_after = self.create_user_info(sender_display, bet, net_win, new_balance, user)
                
                result_path, error = self.generate_animation(
                    base_animation_path=base_anim_path,
                    user_id=user_id,
                    user=user,
                    user_info_before=user_info_before,
                    user_info_after=user_info_after,
                    animated=True,
                    frame_duration=85,
                    last_frame_multiplier=20,
                    show_win_text=True,
                    win_text_height=5,
                    font_scale=0.7,
                    avatar_size=45
                )
                
                if result_path:
                    file_queue.put(result_path)
                self._clear_game(user_id)
                return

            user_info_before = self.create_user_info(sender_display, bet, 0, balance_after_bet, user)
            user_info_after = self.create_user_info(sender_display, bet, 0, balance_after_bet, user)
            
            result_path, error = self.generate_animation(
                base_animation_path=base_anim_path,
                user_id=user_id,
                user=user,
                user_info_before=user_info_before,
                user_info_after=user_info_after,
                animated=True,
                frame_duration=85,
                last_frame_multiplier=20,
                show_win_text=False,
                font_scale=0.7,
                avatar_size=45
            )
            
            if result_path:
                file_queue.put(result_path)

            self.save_game_state(user_id, data)
            return

        if sub in ("cashout", "c", "co"):
            if user_id not in self.active_games:
                self.load_game_state(user_id)

            if user_id not in self.active_games:
                self.send_message_image(
                    nickname=sender_display,
                    file_queue=file_queue,
                    message="No active game.",
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
                    message="You can't cashout before a win.",
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
                logger.error(f"[Snakes] Balance update failed: {e}")

            if net_win > 0:
                record_weekly_win(self.cache, user_id, "snakes", net_win)

            try:
                self.cache.add_experience(user_id, net_win, sender_display, file_queue)
            except:
                pass

            prev_mult = game.cumulative_multiplier / game.last_multiplier if game.last_multiplier else 1.0
            base_anim_path = self._get_animation_path(
                game, game.round_index, game.last_sum, prev_mult, game.last_outcome
            )
            
            if base_anim_path:
                user_info_before = self.create_user_info(sender_display, bet, 0, balance_after_bet, user)
                user_info_after = self.create_user_info(sender_display, bet, net_win, new_balance, user)
                
                result_path, error = self.generate_animation(
                    base_animation_path=base_anim_path,
                    user_id=user_id,
                    user=user,
                    user_info_before=user_info_before,
                    user_info_after=user_info_after,
                    animated=False,
                    frame_duration=85,
                    last_frame_multiplier=20,
                    show_win_text=True,
                    win_text_height=5,
                    font_scale=0.7,
                    avatar_size=45
                )
                
                if result_path:
                    file_queue.put(result_path)

            self.save_game_state(user_id, None)
            return

        try:
            bet = int(sub)
        except ValueError:
            self.send_message_image(
                nickname=sender_display,
                file_queue=file_queue,
                message="Invalid command. Use: /sn <bet>",
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
                message="You already have an active game.",
                title="Snakes - Active Game",
                cache=cache,
                user_id=user_id,
            )
            return

        if bet > balance_before:
            self.send_message_image(
                nickname=sender_display,
                file_queue=file_queue,
                message=f"Insufficient funds.\nBet: ${bet}\nBalance: ${balance_before}",
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
            logger.error(f"[Snakes] Balance update failed: {e}")
            self.send_message_image(
                nickname=sender_display,
                file_queue=file_queue,
                message="Error updating balance.",
                title="Snakes - Error",
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

        base_anim_path = self._get_animation_path(
            game, 1, game.last_sum, 1.0, game.last_outcome
        )
        
        if not base_anim_path:
            logger.error(f"[Snakes] No animation for start: sum={game.last_sum}")
            self.send_message_image(
                nickname=sender_display,
                file_queue=file_queue,
                message="Animation not available.",
                title="Snakes - Error",
                cache=cache,
                user_id=user_id,
            )
            return

        if game.last_outcome == "snake":
            net_win = -bet
            try:
                self.cache.add_experience(user_id, -bet, sender_display, file_queue)
            except:
                pass

            user_info_before = self.create_user_info(sender_display, bet, 0, balance_after_bet, user)
            user_info_after = self.create_user_info(sender_display, bet, net_win, balance_after_bet, user)
            
            result_path, error = self.generate_animation(
                base_animation_path=base_anim_path,
                user_id=user_id,
                user=user,
                user_info_before=user_info_before,
                user_info_after=user_info_after,
                animated=True,
                frame_duration=85,
                last_frame_multiplier=20,
                show_win_text=True,
                win_text_height=5,
                font_scale=0.7,
                avatar_size=45
            )
            
            if result_path:
                file_queue.put(result_path)
            self._clear_game(user_id)
            return

        if result.get("is_maxed"):
            payout = game.current_payout()
            net_win = payout - bet
            new_balance = balance_after_bet + payout
            try:
                self.update_user_balance(user_id, new_balance)
            except:
                pass
            if net_win > 0:
                record_weekly_win(self.cache, user_id, "snakes", net_win)
            
            user_info_before = self.create_user_info(sender_display, bet, 0, balance_after_bet, user)
            user_info_after = self.create_user_info(sender_display, bet, net_win, new_balance, user)
            
            result_path, error = self.generate_animation(
                base_animation_path=base_anim_path,
                user_id=user_id,
                user=user,
                user_info_before=user_info_before,
                user_info_after=user_info_after,
                animated=True,
                frame_duration=85,
                last_frame_multiplier=20,
                show_win_text=True,
                win_text_height=5,
                font_scale=0.7,
                avatar_size=45
            )
            
            if result_path:
                file_queue.put(result_path)
            self._clear_game(user_id)
            return

        user_info_before = self.create_user_info(sender_display, bet, 0, balance_after_bet, user)
        user_info_after = self.create_user_info(sender_display, bet, 0, balance_after_bet, user)
        
        result_path, error = self.generate_animation(
            base_animation_path=base_anim_path,
            user_id=user_id,
            user=user,
            user_info_before=user_info_before,
            user_info_after=user_info_after,
            animated=True,
            frame_duration=85,
            last_frame_multiplier=20,
            show_win_text=False,
            font_scale=0.7,
            avatar_size=45
        )
        
        if result_path:
            file_queue.put(result_path)

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