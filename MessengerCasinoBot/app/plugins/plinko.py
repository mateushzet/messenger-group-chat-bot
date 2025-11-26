import os
import random
import re
from datetime import datetime
from base_game_plugin import BaseGamePlugin
from logger import logger

class PlinkoPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="plinko",
            results_folder=self.get_asset_path("plinko", "plinko_results"),
        )
        self.min_bet = 10
        self.max_bet = 1000
        self.buckets_count = 15
        self.risk_levels = {
            'low': {
                'multipliers': [20.0, 4.0, 1.6, 1.3, 1.2, 1.1, 1.0, 0.5, 1.0, 1.1, 1.2, 1.3, 1.6, 4.0, 20.0],
                'description': 'Low risk - balanced multipliers'
            },
            'medium': {
                'multipliers': [60.0, 12.0, 5.6, 3.2, 1.6, 1.1, 0.7, 0.2, 0.7, 1.1, 1.6, 3.2, 5.6, 12.0, 60.0],
                'description': 'Medium risk - higher variance'
            },
            'high': {
                'multipliers': [420.0, 50.0, 14.0, 5.3, 2.1, 0.5, 0.2, 0.0, 0.2, 0.5, 2.1, 5.3, 14.0, 50.0, 420.0],
                'description': 'High risk - extreme multipliers'
            }
        }
        self.plinko_animations = {}
        
    def calculate_bucket_probabilities(self, risk_level):
        multipliers = self.risk_levels[risk_level]['multipliers']
        
        weights = []
        for multiplier in multipliers:
            if multiplier == 0:
                weights.append(0.001)
            else:
                weights.append(1.0 / multiplier)
        
        return weights
    
    def draw_bucket(self, risk_level):
        weights = self.calculate_bucket_probabilities(risk_level)
        bucket = random.choices(
            range(self.buckets_count),
            weights=weights,
            k=1
        )[0]
        return bucket
    
    def load_plinko_animations(self, bucket):
        animations_folder = self.get_asset_path("plinko", "plinko_animations")
        
        if not os.path.exists(animations_folder):
            logger.error(f"Plinko animations folder not found: {animations_folder}")
            return []
        
        animation_files = []
        pattern = f"plinko_bucket_{bucket}_"
        
        for file in os.listdir(animations_folder):
            if file.startswith(pattern) and file.endswith('.webp'):
                animation_files.append(file)
        
        animation_files.sort(key=lambda x: self._extract_animation_variant(x))
        
        logger.info(f"Loaded {len(animation_files)} animations for bucket {bucket}")
        return [os.path.join(animations_folder, f) for f in animation_files]
    
    def _extract_animation_variant(self, filename):
        match = re.search(r'plinko_bucket_\d+_(\d+)', filename)
        if match:
            return int(match.group(1))
        return 0
    
    def get_random_plinko_animation(self, bucket):
        if bucket not in self.plinko_animations:
            self.plinko_animations[bucket] = self.load_plinko_animations(bucket)
        
        animations = self.plinko_animations[bucket]
        if not animations:
            logger.error(f"No animations found for bucket {bucket}")
            return None
        
        return random.choice(animations)
    
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, self.min_bet)
        if error:
            return error

        balance_before = user["balance"]

        animated = True
        if len(args) >= 3 and args[-1].lower() == "x":
            animated = False
            args = args[:-1]
        
        if len(args) < 2:
            return self._get_help_message()
        
        risk_level = args[0].lower()
        try:
            bet_amount = int(args[1])
        except ValueError:
            return f"Invalid bet amount. Use: /plinko <low|medium|high> <amount>"
        
        if risk_level not in self.risk_levels:
            return f"Invalid risk level. Available: low, medium, high"
        
        if bet_amount < self.min_bet:
            return f"Minimum bet is ${self.min_bet}"
        
        if bet_amount > self.max_bet:
            return f"Maximum bet is ${self.max_bet}"
        
        if bet_amount > balance_before:
            return f"Cannot afford ${bet_amount} Plinko game. Your balance: ${balance_before}"
        
        bucket = self.draw_bucket(risk_level)
        
        animation_path = self.get_random_plinko_animation(bucket)
        
        if not animation_path:
            return f"Error loading plinko animations for bucket {bucket}"
        
        multiplier = self.risk_levels[risk_level]['multipliers'][bucket]
        win_amount = int(bet_amount * multiplier)
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
            result_text = self._get_result_text(risk_level, bet_amount, bucket, multiplier, win_amount, net_win, new_balance)
            return result_text
        
        file_queue.put(result_path)
        
        return self._get_result_text(risk_level, bet_amount, bucket, multiplier, win_amount, net_win, new_balance)
    
    def _get_help_message(self):
        return (
            "PLINKO GAME\n"
            "Drop the ball and watch it bounce to win multipliers!\n\n"
            "Commands:\n"
            f"/plinko low <amount> - Low risk ({self.risk_levels['low']['description']})\n"
            f"/plinko medium <amount> - Medium risk ({self.risk_levels['medium']['description']})\n"
            f"/plinko high <amount> - High risk ({self.risk_levels['high']['description']})\n\n"
            f"Bet Range: ${self.min_bet}-${self.max_bet}\n\n"
            "Multipliers:\n"
            "Low: 0.5x to 20.0x (balanced)\n"
            "Medium: 0.2x to 60.0x (higher variance)\n" 
            "High: 0.0x to 420.0x (extreme risk/reward)\n\n"
            f"Example: /plinko high 100 - High risk with $100 bet"
        )
    
    def _get_result_text(self, risk_level, bet_amount, bucket, multiplier, win_amount, net_win, new_balance):
        risk_display = risk_level.upper()
        
        if net_win > 0:
            result_text = f"WIN +${net_win}"
        elif net_win < 0:
            result_text = f"LOSE -${abs(net_win)}"
        else:
            result_text = "BREAK EVEN"
        
        formatted_win = f"{win_amount:,}" if win_amount >= 1000 else win_amount
        formatted_balance = f"{new_balance:,}" if new_balance >= 1000 else new_balance
        formatted_multiplier = f"{multiplier:,.1f}" if multiplier >= 1000 else f"{multiplier:.1f}"
        
        position = bucket + 1
        
        return (
            f"PLINKO RESULT\n"
            f"Risk: {risk_display}\n"
            f"Bet: ${bet_amount}\n"
            f"Ball landed in position: {position}/15\n"
            f"Multiplier: x{formatted_multiplier}\n"
            f"Prize: ${formatted_win}\n"
            f"Result: {result_text}\n"
            f"Balance: ${formatted_balance}"
        )

def register():
    plugin = PlinkoPlugin()
    logger.info("Plinko plugin registered")
    return {
        "name": "plinko",
        "description": f"Plinko game: /plinko <low|medium|high> <amount> (${plugin.min_bet}-${plugin.max_bet})",
        "execute": plugin.execute_game
    }