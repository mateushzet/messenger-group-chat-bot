import random
import os
from base_game_plugin import BaseGamePlugin
from logger import logger

RED_NUMBERS = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK_NUMBERS = set(range(1,37)) - RED_NUMBERS

class RoulettePlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="roulette",
            results_folder = self.get_asset_path("roulette", "roulette_results"),
            valid_bets=[str(n) for n in range(37)] + ["red","black","even","odd","high","low","green"]
        )

    def calculate_win(self, bet_type, amount, result_number):
        result_color = "red" if result_number in RED_NUMBERS else "black" if result_number in BLACK_NUMBERS else "green"
        
        if bet_type.isdigit() and int(bet_type) == result_number:
            return amount * 35
        elif bet_type in ["red","black"] and bet_type == result_color:
            return amount * 2
        elif bet_type in ["even","odd"] and result_number != 0 and bet_type == ("even" if result_number % 2 == 0 else "odd"):
            return amount * 2
        elif bet_type == "high" and 19 <= result_number <= 36:
            return amount * 2
        elif bet_type == "low" and 1 <= result_number <= 18:
            return amount * 2
        elif bet_type == "green" and result_number == 0:
            return amount * 35
        return 0

    def get_base_animation_path(self, result_number):
        animation_variant = random.randint(1, 4)
        base_path = os.path.join(self.results_folder, f"result_{result_number}_{animation_variant}.webp")
        
        return base_path

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache

        animated = True
        if len(args) >= 3 and args[-1].lower() == "x":
            animated = False
            args = args[:-1]

        if len(args) < 2:
            return f"Usage: /roulette <bet_type> <amount> [x]"

        bet_type, amount_str = args[0], args[1]

        error = self.validate_bet(bet_type, amount_str)
        if error:
            return error

        amount = int(amount_str)

        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, amount)
        if error:
            return error

        balance_before = user["balance"]

        result_number = random.randint(0, 36)
        win = self.calculate_win(bet_type, amount, result_number)
        new_balance = balance_before + win - amount
        
        self.update_user_balance(user_id, new_balance)

        user_info_before = self.create_user_info(sender, amount, 0, balance_before, user.copy())
        newLevel, newLevelProgress = self.cache.add_experience(user_id, win - amount)

        base_animation_path = self.get_base_animation_path(result_number)
        
        user["level"] = newLevel
        user["level_progress"] = newLevelProgress
        user_info_after = self.create_user_info(sender, amount, win, new_balance, user)

        result_path, error = self.generate_animation(base_animation_path, user_id, user, user_info_before, user_info_after, animated=animated)
        if error:
            return error

        file_queue.put(result_path)
        
        result_color = "red" if result_number in RED_NUMBERS else "black" if result_number in BLACK_NUMBERS else "green"
        print(f"ROULETTE: {sender} bet {amount} on {bet_type} | Result: {result_number} {result_color} | Win: {win} | Balance: {balance_before} -> {new_balance}")
        
        return None

def register():
    plugin = RoulettePlugin()
    return {
        "name": "roulette",
        "aliases": ["/r"],
        "description": "Roulette game: /roulette <bet_type> <amount> or /r <bet_type> <amount>",
        "execute": plugin.execute_game
    }