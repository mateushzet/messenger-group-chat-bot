import os
import random
import re
from datetime import datetime
from base_game_plugin import BaseGamePlugin
from logger import logger

class CasePlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="case",
            results_folder=self.get_asset_path("case", "case_results"),
        )
        self.case_prices = [10, 100, 1000]
        self.case_animations = {}
        
    def load_case_animations(self, case_price):
        case_folder = self.get_asset_path("case", str(case_price))
        
        if not os.path.exists(case_folder):
            logger.error(f"Case folder not found: {case_folder}")
            return []
        
        animation_files = []
        for file in os.listdir(case_folder):
            if file.startswith(f"case_{case_price}_") and file.endswith('.webp'):
                animation_files.append(file)
        
        animation_files.sort(key=lambda x: self._extract_animation_number(x))
        
        logger.info(f"Loaded {len(animation_files)} animations for case ${case_price}")
        return [os.path.join(case_folder, f) for f in animation_files]
    
    def _extract_animation_number(self, filename):
        match = re.search(r'case_\d+_(\d+)', filename)
        if match:
            return int(match.group(1))
        return 0
    
    def _extract_win_amount(self, filename):
        match = re.search(r'\((\d+)\)', filename)
        if match:
            return int(match.group(1))
        return 0
    
    def get_random_case_animation(self, case_price):
        if case_price not in self.case_animations:
            self.case_animations[case_price] = self.load_case_animations(case_price)
        
        animations = self.case_animations[case_price]
        if not animations:
            logger.error(f"No animations found for case ${case_price}")
            return None, 0
        
        animation_path = random.choice(animations)
        win_amount = self._extract_win_amount(os.path.basename(animation_path))
        
        return animation_path, win_amount
    
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 1)
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
            case_price = int(args[0])
        except ValueError:
            return "Invalid case price. Use: /case 10, /case 100, or /case 1000"
        
        if case_price not in self.case_prices:
            return f"Invalid case price. Available: {', '.join(f'${p}' for p in self.case_prices)}"
        
        if case_price > balance_before:
            return f"Cannot afford ${case_price} case. Your balance: ${balance_before}"
        
        animation_path, win_amount = self.get_random_case_animation(case_price)
        
        if not animation_path:
            return f"Error loading case animations for ${case_price}"
        
        final_win = win_amount
        net_win = final_win - case_price
        new_balance = balance_before - case_price + final_win
        
        self.update_user_balance(user_id, new_balance)

        user_info_before = self.create_user_info(sender, case_price, 0, balance_before, user.copy())
        newLevel, newLevelProgress = self.cache.add_experience(user_id, win_amount - case_price + final_win)

        user["level"] = newLevel
        user["level_progress"] = newLevelProgress
        user_info_after = self.create_user_info(sender, case_price, net_win, new_balance, user)
        
        result_path, error = self.generate_animation(
            animation_path, user_id, user, user_info_before, user_info_after, animated=animated
        )
        
        if error:
            logger.error(f"Animation error: {error}")
            result_text = self._get_result_text(case_price, win_amount, net_win, new_balance)
            return result_text
        
        file_queue.put(result_path)
        
        return self._get_result_text(case_price, win_amount, net_win, new_balance)
    
    def _get_help_message(self):
        return (
            "Case Game\n"
            "Commands:\n"
            "/case 10 - Open $10 case\n"
            "/case 100 - Open $100 case\n"
            "/case 1000 - Open $1000 case\n\n"
            "Prizes: Random rewards from each case!"
        )
    
    def _get_result_text(self, case_price, win_amount, net_win, new_balance):
        if net_win > 0:
            result_text = f"WIN +${net_win}"
        elif net_win < 0:
            result_text = f"LOSE -${abs(net_win)}"
        else:
            result_text = "BREAK EVEN"
        
        return (
            f"CASE RESULT\n"
            f"Case: ${case_price}\n"
            f"Prize: ${win_amount}\n"
            f"Result: {result_text}\n"
            f"Balance: ${new_balance}"
        )

def register():
    plugin = CasePlugin()
    logger.info("Case plugin registered")
    return {
        "name": "case",
        "description": "Open mystery cases: /case 10, /case 100, /case 1000",
        "execute": plugin.execute_game
    }