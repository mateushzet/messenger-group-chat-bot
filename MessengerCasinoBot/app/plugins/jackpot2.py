import os
import time
import random
import math
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
from base_game_plugin import BaseGamePlugin
from plugins.monthly import record_monthly_win
from logger import logger


class Jackpot2Plugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="jackpot2")
        self.results_folder = self.get_asset_path("temp")
        self.pot = 0
        self.last_add_date = None
        self._load_state()

    def _load_state(self):
        try:
            if self.cache:
                pot = self.cache.get_setting("jackpot2_pot")
                last_add = self.cache.get_setting("jackpot2_last_add")
                if pot is not None:
                    self.pot = pot
                if last_add:
                    self.last_add_date = datetime.fromisoformat(last_add)
                else:
                    self.last_add_date = datetime.now()
                    self._save_state()
        except Exception as e:
            logger.error(f"[Jackpot2] Error loading state: {e}")
            self.pot = 0
            self.last_add_date = datetime.now()

    def _save_state(self):
        try:
            if self.cache:
                self.cache.set_setting("jackpot2_pot", self.pot)
                if self.last_add_date:
                    self.cache.set_setting("jackpot2_last_add", self.last_add_date.isoformat())
        except Exception as e:
            logger.error(f"[Jackpot2] Error saving state: {e}")

    def _add_daily_bonus(self):
        now = datetime.now()
        
        if not self.last_add_date:
            self.last_add_date = now
            self._save_state()
            return

        time_diff = now - self.last_add_date
        hours_diff = time_diff.total_seconds() / 3600
        periods = int(hours_diff // 6)
        
        if periods > 0:
            bonus = periods * 100
            self.pot += bonus
            self.last_add_date += timedelta(hours=periods * 6)
            self._save_state()
            logger.info(f"[Jackpot2] Added {bonus} bonus over {periods} periods (6h each). Pot: {self.pot}")

    def _calculate_win_chance(self, bet):
        total = self.pot + bet
        if total <= 0:
            return 0.5
        chance = bet / total
        return max(chance, 0.01)

    def _get_win_angle(self, bet, pot_for_angles):
        """Zwraca kąt złotego sektora z minimum 1% (3.6 stopnia)."""
        if pot_for_angles == 0:
            return 180
        total = pot_for_angles + bet
        win_ratio = bet / total
        win_angle = win_ratio * 360
        return max(win_angle, 3.6)

    def _spin(self, bet):
        self._add_daily_bonus()
        pot_before = self.pot

        if self.pot == 0:
            if random.random() < 0.5:
                stop_angle = -random.uniform(10, 170)
                return "win", 0, 0, stop_angle, pot_before, True
            else:
                self.pot += bet
                self._save_state()
                stop_angle = -random.uniform(190, 350)
                return "loss", bet, 0, stop_angle, pot_before, False
        else:
            chance = self._calculate_win_chance(bet)
            
            win_angle = self._get_win_angle(bet, pot_before)
            
            if random.random() < chance:
                winnings = self.pot
                self.pot = 0
                self._save_state()
                stop_angle = -random.uniform(0, win_angle)
                return "win", winnings, winnings, stop_angle, pot_before, False
            else:
                self.pot += bet
                self._save_state()
                loss_angle = 360 - win_angle
                stop_angle = -win_angle - random.uniform(0, loss_angle)
                return "loss", bet, 0, stop_angle, pot_before, False

    def _draw_golden_gradient(self, draw, x, y, radius, start_angle, end_angle):
        steps = 30
        for i in range(steps):
            progress = i / steps
            r = int(255 - progress * 40)
            g = int(200 - progress * 30)
            b = int(50 - progress * 20)
            color = (r, g, b, 230)
            current_start = start_angle + (end_angle - start_angle) * (i / steps)
            current_end = start_angle + (end_angle - start_angle) * ((i + 1) / steps)
            draw.pieslice(
                [x, y, x + radius * 2, y + radius * 2],
                start=current_start,
                end=current_end,
                fill=color,
                outline=None,
                width=0
            )

    def _create_static_frame(self, bet, pot_display, pot_for_angles, won, win_amount, stop_angle=None, show_pot=True):
        width = 400
        height = 420
        
        center_x = width // 2
        center_y = height // 2 - 10
        radius = 140

        win_angle = self._get_win_angle(bet, pot_for_angles)
        loss_angle = 360 - win_angle

        start_angle = -90

        if stop_angle is not None:
            rotation = stop_angle
        else:
            if won:
                rotation = -random.uniform(0, win_angle)
            else:
                rotation = -win_angle - random.uniform(0, loss_angle)

        img = Image.new('RGBA', (width, height), (20, 22, 32, 255))
        draw = ImageDraw.Draw(img)

        draw.ellipse(
            [center_x - radius - 4, center_y - radius - 4, center_x + radius + 4, center_y + radius + 4],
            fill=None,
            outline=(255, 215, 0, 200),
            width=2
        )
        draw.ellipse(
            [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
            fill=(20, 22, 32, 255),
            outline=(100, 100, 110, 255),
            width=1
        )

        if win_angle > 0:
            self._draw_golden_gradient(
                draw,
                center_x - radius,
                center_y - radius,
                radius,
                start_angle + rotation,
                start_angle + rotation + win_angle
            )

        if loss_angle > 0:
            draw.pieslice(
                [center_x - radius + 2, center_y - radius + 2, center_x + radius - 2, center_y + radius - 2],
                start=start_angle + rotation + win_angle,
                end=start_angle + rotation + win_angle + loss_angle,
                fill=(25, 25, 30, 230),
                outline=(0, 0, 0, 100),
                width=1
            )

        draw.ellipse(
            [center_x - radius + 1, center_y - radius + 1, center_x + radius - 1, center_y + radius - 1],
            fill=None,
            outline=(200, 200, 200, 80),
            width=1
        )

        center_radius = int(radius * 0.15)
        draw.ellipse(
            [center_x - center_radius, center_y - center_radius, center_x + center_radius, center_y + center_radius],
            fill=(20, 22, 32, 255),
            outline=(255, 215, 0, 150),
            width=2
        )

        arrow_y = center_y - radius - 12
        arrow_size = 14
        
        draw.polygon(
            [
                (center_x, arrow_y + arrow_size),
                (center_x - arrow_size, arrow_y - 4),
                (center_x + arrow_size, arrow_y - 4),
            ],
            fill=(255, 215, 0, 230),
            outline=(255, 255, 255, 180),
            width=1
        )

        if show_pot:
            try:
                font = self.text_renderer.get_font(20) if hasattr(self, 'text_renderer') else None
                if font:
                    pot_text = f"JACKPOT POOL: ${pot_display}"
                    text_width = font.getlength(pot_text)
                    
                    shadow_x = width//2 - text_width//2 + 1
                    shadow_y = 13
                    draw.text((shadow_x, shadow_y), pot_text, fill=(0, 0, 0, 200), font=font)
                    
                    draw.text((width//2 - text_width//2, 12), pot_text, fill=(255, 215, 0, 255), font=font)
                else:
                    draw.text((width//2 - 70, 12), f"JACKPOT POOL: ${pot_display}", fill=(255, 215, 0, 255))
            except:
                draw.text((width//2 - 70, 12), f"JACKPOT POOL: ${pot_display}", fill=(255, 215, 0, 255))

        return img

    def create_jackpot2_animation(self, user_id, bet, pot_before, pot_after, won, win_amount, final_stop_angle=None, is_break_even=False):
        width = 400
        height = 420
        frames = []
        frame_count = 50
        
        center_x = width // 2
        center_y = height // 2 - 10
        radius = 140

        win_angle = self._get_win_angle(bet, pot_before)
        loss_angle = 360 - win_angle

        start_angle = -90

        if final_stop_angle is not None:
            target_rotation = final_stop_angle
        else:
            if won:
                final_offset = random.uniform(0, win_angle)
                target_rotation = -final_offset
            else:
                final_offset = random.uniform(0, loss_angle)
                target_rotation = -win_angle - final_offset

        full_turns = random.randint(2, 4)
        random_start_offset = random.uniform(-25, 25)
        start_rotation = target_rotation - (360 * full_turns) - random_start_offset

        for frame_idx in range(frame_count):
            progress = frame_idx / (frame_count - 1)
            is_last_frame = (frame_idx == frame_count - 1)
            
            current_pot = pot_after if is_last_frame else pot_before

            if progress < 0.4:
                eased = progress / 0.4 * 0.7
            else:
                p = (progress - 0.4) / 0.6
                eased = 0.7 + 0.3 * (1 - ((1 - p) ** 6))

            eased = min(1.0, max(0.0, eased))
            rotation = start_rotation + ((target_rotation - start_rotation) * eased)

            img = Image.new('RGBA', (width, height), (20, 22, 32, 255))
            draw = ImageDraw.Draw(img)

            draw.ellipse(
                [center_x - radius - 4, center_y - radius - 4, center_x + radius + 4, center_y + radius + 4],
                fill=None,
                outline=(255, 215, 0, 200),
                width=2
            )
            draw.ellipse(
                [center_x - radius, center_y - radius, center_x + radius, center_y + radius],
                fill=(20, 22, 32, 255),
                outline=(100, 100, 110, 255),
                width=1
            )

            if win_angle > 0:
                self._draw_golden_gradient(
                    draw,
                    center_x - radius,
                    center_y - radius,
                    radius,
                    start_angle + rotation,
                    start_angle + rotation + win_angle
                )

            if loss_angle > 0:
                draw.pieslice(
                    [center_x - radius + 2, center_y - radius + 2, center_x + radius - 2, center_y + radius - 2],
                    start=start_angle + rotation + win_angle,
                    end=start_angle + rotation + win_angle + loss_angle,
                    fill=(25, 25, 30, 230),
                    outline=(0, 0, 0, 100),
                    width=1
                )

            draw.ellipse(
                [center_x - radius + 1, center_y - radius + 1, center_x + radius - 1, center_y + radius - 1],
                fill=None,
                outline=(200, 200, 200, 80),
                width=1
            )

            center_radius = int(radius * 0.15)
            draw.ellipse(
                [center_x - center_radius, center_y - center_radius, center_x + center_radius, center_y + center_radius],
                fill=(20, 22, 32, 255),
                outline=(255, 215, 0, 150),
                width=2
            )

            arrow_y = center_y - radius - 12
            arrow_size = 14
            
            draw.polygon(
                [
                    (center_x, arrow_y + arrow_size),
                    (center_x - arrow_size, arrow_y - 4),
                    (center_x + arrow_size, arrow_y - 4),
                ],
                fill=(255, 215, 0, 230),
                outline=(255, 255, 255, 180),
                width=1
            )

            try:
                font = self.text_renderer.get_font(20) if hasattr(self, 'text_renderer') else None
                if font:
                    pot_text = f"JACKPOT POOL: ${current_pot}"
                    text_width = font.getlength(pot_text)
                    
                    shadow_x = width//2 - text_width//2 + 1
                    shadow_y = 13
                    draw.text((shadow_x, shadow_y), pot_text, fill=(0, 0, 0, 200), font=font)
                    
                    draw.text((width//2 - text_width//2, 12), pot_text, fill=(255, 215, 0, 255), font=font)
                else:
                    draw.text((width//2 - 70, 12), f"JACKPOT POOL: ${current_pot}", fill=(255, 215, 0, 255))
            except:
                draw.text((width//2 - 70, 12), f"JACKPOT POOL: ${current_pot}", fill=(255, 215, 0, 255))

            frames.append(img)

        timestamp = int(time.time() * 1000)
        output_path = os.path.join(self.results_folder, f"jackpot2_anim_{user_id}_{timestamp}.webp")

        durations = [40] * len(frames)

        frames[0].save(
            output_path,
            format='WEBP',
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
            quality=85,
            method=2,
            optimize=True
        )
        
        return output_path

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        self._load_state()

        args, animated, low_quality = self.parse_static_quality_flag(args)

        if not args:
            args = ["spin"]

        cmd = args[0].lower()

        if cmd == "help" or cmd == "h":
            help_text = """JACKPOT 2

How to play:
  /jp2 or /jackpot2 - Spin for 100 coins
  /jp2 x - Static spin (no animation)

Rules:
  - Each spin costs 100 coins
  - Win chance = 100 / (pot + 100), minimum 1%
  - Win the entire pot if you win
  - Your 100 goes to pot if you lose
  - +100 coins added to pot every 6 hours

Examples:
  Pot: 100, Bet: 100 -> 50% win chance
  Pot: 900, Bet: 100 -> 10% win chance
  Pot: 0, Bet: 100 -> 50% win 0, 50% lose 100"""

            self.send_message_image(
                sender,
                file_queue,
                help_text,
                "Jackpot2 Help",
                cache,
                None
            )
            return ""

        if cmd == "spin" or cmd == "s" or cmd == "":
            bet_amount = 100
            
            user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, bet_amount)
            
            if error:
                if "Insufficient balance" in error:
                    self.send_message_image(
                        sender,
                        file_queue,
                        f"Insufficient funds!\n\nBet: ${bet_amount}\nBalance: ${user.get('balance', 0) if user else 0}",
                        "Jackpot2 - Insufficient Funds",
                        cache,
                        user_id
                    )
                else:
                    self.send_message_image(sender, file_queue, "User validation failed.", "Jackpot2 - Validation Error", cache, user_id)
                return ""

            balance_before = user["balance"]

            result_type, win_amount, winnings, stop_angle, pot_before, is_break_even = self._spin(bet_amount)
            pot_after = self.pot

            if result_type == "win":
                if winnings > 0:
                    new_balance = balance_before + winnings
                    net_win = winnings
                    record_monthly_win(self.cache, user_id, "jackpot", net_win)
                else:
                    new_balance = balance_before
                    net_win = 0
            else:
                new_balance = balance_before - bet_amount
                net_win = -bet_amount

            user["balance"] = new_balance
            self.update_user_balance(user_id, new_balance)

            try:
                new_level, new_progress = self.cache.add_experience(user_id, net_win, sender, file_queue)
                user["level"] = new_level
                user["level_progress"] = new_progress
            except Exception as e:
                logger.error(f"[Jackpot2] Error adding experience: {e}")

            if animated:
                anim_path = self.create_jackpot2_animation(
                    user_id,
                    bet_amount,
                    pot_before,
                    pot_after,
                    result_type == "win",
                    winnings,
                    stop_angle,
                    is_break_even
                )
                base_path = anim_path
            else:
                static_img = self._create_static_frame(
                    bet_amount, 
                    pot_after,
                    pot_before,
                    result_type == "win", 
                    winnings, 
                    stop_angle, 
                    show_pot=True
                )
                timestamp = int(time.time() * 1000)
                static_path = os.path.join(self.results_folder, f"jackpot2_static_{user_id}_{timestamp}.png")
                static_img.save(static_path, format='PNG', quality=85)
                base_path = static_path

            if base_path:
                user_before = user.copy()
                user_before["balance"] = balance_before
                user_info_before = self.create_user_info(sender, bet_amount, 0, balance_before, user_before)
                user_info_after = self.create_user_info(sender, bet_amount, net_win, new_balance, user)
                
                result_path, error = self.generate_animation(
                    base_animation_path=base_path,
                    user_id=user_id,
                    user=user,
                    user_info_before=user_info_before,
                    user_info_after=user_info_after,
                    animated=animated,
                    frame_duration=45,
                    last_frame_multiplier=4.0,
                    final_frames_start_index=9999,
                    custom_overlay_kwargs=None,
                    show_win_text=True,
                    font_scale=0.8,
                    avatar_size=50,
                    show_bet_amount=True,
                    win_text_height=350,
                    overlay_position="bottom",
                    quality=85,
                    lowQuality=low_quality,
                )
                
                if result_path and not error:
                    file_queue.put(result_path)
                else:
                    logger.error(f"[Jackpot2] Animation generation error: {error}")
                    file_queue.put(base_path)

            if result_type == "win" and winnings > 0:
                return f"JACKPOT WON! You won ${winnings}! Pot reset to $0"
            elif result_type == "win" and winnings == 0 and pot_before == 0:
                return f"You hit the jackpot! The pot was empty, so you got your ${bet_amount} back! (Break-even)"
            elif result_type == "win" and winnings == 0 and pot_before > 0:
                return f"You hit the jackpot! But something went wrong..."
            else:
                return f"You lost ${bet_amount}. Pot is now ${self.pot}"

        else:
            self.send_message_image(
                sender,
                file_queue,
                "Unknown command.\nUse /jp2 or /jp2 help",
                "Jackpot2 - Error",
                cache,
                None
            )
            return ""


def register():
    plugin = Jackpot2Plugin()
    return {
        "name": "jackpot2",
        "aliases": ["/jp2"],
        "description": """Jackpot 2 Game

Spin for 100 coins and try to win the pot!
Win chance depends on pot size.

Commands:
  /jp2 - Spin for 100 coins
  /jp2 x - Static spin (no animation)
  /jp2 help - Show rules

Rules:
  - Each spin costs 100 coins
  - Win chance = 100 / (pot + 100), minimum 1%
  - Win the entire pot if you win
  - Lose sends your 100 to the pot
  - +100 coins added every 6 hours""",
        "execute": plugin.execute_game
    }
