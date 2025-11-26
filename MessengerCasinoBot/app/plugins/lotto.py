import os
import random
import re
from datetime import datetime
from base_game_plugin import BaseGamePlugin
from logger import logger

class LottoPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="lotto",
            results_folder=self.get_asset_path("lotto", "lotto_results"),
        )
        self.min_bet = 10
        self.total_numbers = 49
        self.player_numbers_count = 6
        self.multipliers = {
            0: 0,
            1: 0,
            2: 2,
            3: 20,
            4: 350,
            5: 10000,
            6: 100000
        }
        self.lotto_animations = {}
        
    def calculate_hit_probabilities(self):
        probabilities = {
            0: 0.435,
            1: 0.413,
            2: 0.132,
            3: 0.018,
            4: 0.001,
            5: 0.00002,
            6: 0.00000007
        }
        return probabilities
    
    def draw_hits(self):
        probabilities = self.calculate_hit_probabilities()
        hits = random.choices(
            list(probabilities.keys()),
            weights=list(probabilities.values()),
            k=1
        )[0]
        return hits
    
    def load_lotto_animations(self, hits):
        hits_folder = self.get_asset_path("lotto", "generated_animations", f"{hits}_hits")
        
        if not os.path.exists(hits_folder):
            logger.error(f"Lotto folder not found: {hits_folder}")
            return []
        
        animation_files = []
        for file in os.listdir(hits_folder):
            if file.startswith(f"lotto_{hits}hits_") and file.endswith('.webp'):
                animation_files.append(file)
        
        animation_files.sort(key=lambda x: self._extract_animation_number(x))
        
        logger.info(f"Loaded {len(animation_files)} animations for {hits} hits")
        return [os.path.join(hits_folder, f) for f in animation_files]
    
    def _extract_animation_number(self, filename):
        match = re.search(r'lotto_\dhits_(\d+)', filename)
        if match:
            return int(match.group(1))
        return 0
    
    def get_random_lotto_animation(self, hits):
        if hits not in self.lotto_animations:
            self.lotto_animations[hits] = self.load_lotto_animations(hits)
        
        animations = self.lotto_animations[hits]
        if not animations:
            logger.error(f"No animations found for {hits} hits")
            return None
        
        return random.choice(animations)
    
    def generate_player_numbers(self):
        return sorted(random.sample(range(1, self.total_numbers + 1), self.player_numbers_count))
    
    def generate_winning_numbers(self):
        return sorted(random.sample(range(1, self.total_numbers + 1), self.player_numbers_count))
    
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, self.min_bet)
        if error:
            return error

        balance_before = user["balance"]

        animated = True
        if len(args) >= 1 and args[-1].lower() == "x":
            animated = False
            args = args[:-1]
        
        if len(args) == 0:
            return self._get_help_message()
        
        try:
            bet_amount = int(args[0])
        except ValueError:
            return f"Invalid bet amount. Use: /lotto <amount> (min ${self.min_bet})"
        
        if bet_amount < self.min_bet:
            return f"Minimum bet is ${self.min_bet}"
        
        if bet_amount > balance_before:
            return f"Cannot afford ${bet_amount} Lotto ticket. Your balance: ${balance_before}"
        
        hits = self.draw_hits()
        
        player_numbers = self.generate_player_numbers()
        winning_numbers = self.generate_winning_numbers()
        
        animation_path = self.get_random_lotto_animation(hits)
        
        if not animation_path:
            return f"Error loading lotto animations for {hits} hits"
        
        multiplier = self.multipliers[hits]
        win_amount = bet_amount * multiplier
        net_win = win_amount - bet_amount
        new_balance = balance_before - bet_amount + win_amount
        
        self.update_user_balance(user_id, new_balance)

        user_info_before = self.create_user_info(sender, bet_amount, 0, balance_before, user.copy())
        newLevel, newLevelProgress = self.cache.add_experience(user_id, -bet_amount + win_amount)

        user["level"] = newLevel
        user["level_progress"] = newLevelProgress
        user_info_after = self.create_user_info(sender, bet_amount, net_win, new_balance, user)
        
        result_path, error = self.generate_animation(
            animation_path, user_id, user, user_info_before, user_info_after, animated=animated
        )
        
        if error:
            logger.error(f"Animation error: {error}")
            result_text = self._get_result_text(bet_amount, hits, multiplier, win_amount, net_win, new_balance, player_numbers, winning_numbers)
            return result_text
        
        file_queue.put(result_path)
        
        return self._get_result_text(bet_amount, hits, multiplier, win_amount, net_win, new_balance, player_numbers, winning_numbers)
    
    def _get_help_message(self):
        return (
            "LOTTO GAME\n"
            "Play lottery with custom bets!\n\n"
            "Commands:\n"
            f"/lotto <amount> - Play lotto with custom bet (min ${self.min_bet})\n\n"
            "Multipliers:\n"
            "0-1 hits: x0\n"
            "2 hits: x2\n" 
            "3 hits: x20\n"
            "4 hits: x350\n"
            "5 hits: x10,000\n"
            "6 hits: x100,000\n\n"
            f"Example: /lotto 50 - Play with $50 bet"
        )
    
    def _get_result_text(self, bet_amount, hits, multiplier, win_amount, net_win, new_balance, player_numbers, winning_numbers):
        player_nums = ", ".join(map(str, player_numbers))
        winning_nums = ", ".join(map(str, winning_numbers))
        
        if net_win > 0:
            result_text = f"WIN +${net_win}"
        elif net_win < 0:
            result_text = f"LOSE -${abs(net_win)}"
        else:
            result_text = "BREAK EVEN"
        
        formatted_win = f"{win_amount:,}" if win_amount >= 1000 else win_amount
        formatted_balance = f"{new_balance:,}" if new_balance >= 1000 else new_balance
        
        return (
            f"LOTTO RESULT\n"
            f"Ticket: ${bet_amount}\n"
            f"Your numbers: {player_nums}\n"
            f"Winning numbers: {winning_nums}\n"
            f"Hits: {hits}/6\n"
            f"Multiplier: x{multiplier:,}\n"
            f"Prize: ${formatted_win}\n"
            f"Result: {result_text}\n"
            f"Balance: ${formatted_balance}"
        )

def register():
    plugin = LottoPlugin()
    logger.info("Lotto plugin registered")
    return {
        "name": "lotto",
        "aliases": ["/l"],
        "description": f"Lotto game: /lotto <amount> (min ${plugin.min_bet})",
        "execute": plugin.execute_game
    }