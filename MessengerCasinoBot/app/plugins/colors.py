import random
import os
from base_game_plugin import BaseGamePlugin
from logger import logger

class ColorsPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="colors",
            results_folder = self.get_asset_path("colors", "colors_results"),
            valid_bets=["black", "red", "blue", "gold"]
        )
        
        self.color_order = [
            0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 
            0, 2, 0, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1, 0, 1, 
            0, 1, 0, 2, 3, 2, 0, 1, 0, 1, 0, 1, 0, 2, 0, 2, 0, 1
        ]
        
        self.color_map = {
            0: "black",
            1: "red", 
            2: "blue",
            3: "gold"
        }
        
        self.multipliers = {
            "black": 2,
            "red": 3,
            "blue": 5, 
            "gold": 50
        }
        
        self.color_counts = {
            "black": self.color_order.count(0),
            "red": self.color_order.count(1),
            "blue": self.color_order.count(2), 
            "gold": self.color_order.count(3)
        }

    def get_color_at_position(self, position):
        if 0 <= position < len(self.color_order):
            color_number = self.color_order[position]
            return self.color_map[color_number]
        return "black"

    def calculate_win(self, bets, result_position):
        result_color = self.get_color_at_position(result_position)
        total_win = 0
        
        if isinstance(bets, str):
            if bets == result_color:
                return bets.get(bets, 0) * self.multipliers[result_color]
            return 0
        
        elif isinstance(bets, list) and len(bets) == 4:
            colors = ["black", "red", "blue", "gold"]
            for i, bet_amount in enumerate(bets):
                if colors[i] == result_color and bet_amount > 0:
                    total_win += bet_amount * self.multipliers[result_color]
            return total_win
        
        return 0

    def get_base_animation_path(self, result_position, result_color):
        animation_variant = random.randint(0, 2)
        base_path = os.path.join(
            self.results_folder, 
            f"colors_wheel_{result_color}_{result_position}_{animation_variant}.webp"
        )
        
        return base_path

    def parse_bet(self, args):
        if len(args) == 1:
            bet_type = args[0].lower()
            if bet_type not in self.valid_bets:
                return None, "Invalid color. Use: black, red, blue, gold"
            return bet_type, None
        
        elif len(args) == 4:
            try:
                bets = [int(arg) for arg in args]
                if any(bet < 0 for bet in bets):
                    return None, "All bets must be positive numbers"
                return bets, None
            except ValueError:
                return None, "All bets must be numbers"
        
        return None, "Invalid bet format. Use: /colors <color> <amount> OR /colors <black_bet> <red_bet> <blue_bet> <gold_bet>"

    def validate_bet_amount(self, bet_type, amount_str, user_balance):
        try:
            amount = int(amount_str)
        except ValueError:
            return None, "Bet amount must be a number"

        if amount <= 0:
            return None, "Bet amount must be positive"

        if isinstance(bet_type, str):
            if amount > user_balance:
                return None, f"Insufficient balance. You have: {user_balance}"
            total_bet = amount
        
        elif isinstance(bet_type, list):
            total_bet = sum(bet_type)
            if total_bet > user_balance:
                return None, f"Insufficient balance. Total bet: {total_bet}, you have: {user_balance}"
        
        else:
            return None, "Invalid bet type"

        return total_bet, None

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache

        animated = True
        if len(args) >= 2 and args[-1].lower() == "x":
            animated = False
            args = args[:-1]

        if len(args) < 1:
            return "Usage: /colors <color> <amount> OR /colors <black> <red> <blue> <gold>"

        bet_type, error = self.parse_bet(args)
        if error:
            return error

        if isinstance(bet_type, str):
            if len(args) < 2:
                return "Usage: /colors <color> <amount>"
            amount_str = args[1]
        else:
            amount_str = str(sum(bet_type))

        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 1)
        if error:
            return error

        balance_before = user["balance"]

        total_bet, error = self.validate_bet_amount(bet_type, amount_str, balance_before)
        if error:
            return error

        result_position = random.randint(0, 53)
        result_color = self.get_color_at_position(result_position)

        win_amount = self.calculate_win(bet_type, result_position)
        new_balance = balance_before + win_amount - total_bet

        self.update_user_balance(user_id, new_balance)

        user_info_before = self.create_user_info(sender, total_bet, 0, balance_before, user.copy())
        newLevel, newLevelProgress = self.cache.add_experience(user_id, win_amount - total_bet)

        base_animation_path = self.get_base_animation_path(result_position, result_color)
        
        user["level"] = newLevel
        user["level_progress"] = newLevelProgress
        user_info_after = self.create_user_info(sender, total_bet, win_amount, new_balance, user)

        result_path, error = self.generate_animation(base_animation_path, user_id, user, user_info_before, user_info_after, animated=animated)
        if error:
            return error

        file_queue.put(result_path)
        
        if isinstance(bet_type, str):
            bet_info = f"{total_bet} on {bet_type}"
        else:
            bet_info = f"multiple bets: black={bet_type[0]}, red={bet_type[1]}, blue={bet_type[2]}, gold={bet_type[3]}"
        
        print(f"COLORS: {sender} bet {bet_info} | Result: {result_color} (pos {result_position}) | Win: {win_amount} | Balance: {balance_before} -> {new_balance}")
        
        return None

def register():
    plugin = ColorsPlugin()
    return {
        "name": "colors",
        "aliases": ["/c"],
        "description": "Colors game: /colors <color> <amount> (black/red/blue/gold) OR /colors <black_bet> <red_bet> <blue_bet> <gold_bet>",
        "execute": plugin.execute_game
    }