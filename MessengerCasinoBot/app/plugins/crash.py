import random
import os
import time
import math
from PIL import Image
from base_game_plugin import BaseGamePlugin
from logger import logger

class CrashPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="crash"
        )
        
        self.multipliers = [
            1.00, 1.01, 1.02, 1.03, 1.04, 1.05, 1.06, 1.07, 1.08, 1.09,
            1.10, 1.11, 1.12, 1.13, 1.14, 1.15, 1.16, 1.17, 1.18, 1.19,
            1.20, 1.21, 1.22, 1.23, 1.24, 1.25, 1.26, 1.27, 1.28, 1.29,
            1.30, 1.31, 1.32, 1.33, 1.34, 1.35, 1.36, 1.37, 1.38, 1.39,
            1.40, 1.41, 1.42, 1.43, 1.44, 1.45, 1.46, 1.47, 1.48, 1.49,
            1.50, 1.51, 1.52, 1.53, 1.54, 1.55, 1.56, 1.57, 1.58, 1.59,
            1.60, 1.61, 1.62, 1.63, 1.64, 1.65, 1.66, 1.67, 1.68, 1.69,
            1.70, 1.71, 1.72, 1.73, 1.74, 1.75, 1.76, 1.77, 1.78, 1.79,
            1.80, 1.81, 1.82, 1.83, 1.84, 1.85, 1.86, 1.87, 1.88, 1.89,
            1.90, 1.91, 1.92, 1.93, 1.94, 1.95, 1.96, 1.97, 1.98, 1.99,
            2.00, 2.01, 2.02, 2.03, 2.04, 2.05, 2.06, 2.07, 2.08, 2.09,
            2.10, 2.11, 2.12, 2.13, 2.14, 2.15, 2.16, 2.17, 2.18, 2.19,
            2.20, 2.21, 2.22, 2.23, 2.24, 2.25, 2.26, 2.27, 2.28, 2.29,
            2.30, 2.31, 2.32, 2.33, 2.34, 2.35, 2.36, 2.37, 2.38, 2.39,
            2.40, 2.41, 2.42, 2.43, 2.44, 2.45, 2.46, 2.47, 2.48, 2.49,
            2.50, 2.51, 2.52, 2.53, 2.54, 2.55, 2.56, 2.57, 2.58, 2.59,
            2.60, 2.61, 2.62, 2.63, 2.64, 2.65, 2.66, 2.67, 2.68, 2.69,
            2.70, 2.71, 2.72, 2.73, 2.74, 2.75, 2.76, 2.77, 2.78, 2.79,
            2.80, 2.81, 2.82, 2.83, 2.84, 2.85, 2.86, 2.87, 2.88, 2.89,
            2.90, 2.91, 2.92, 2.93, 2.94, 2.95, 2.96, 2.97, 2.98, 2.99,
            3.00, 3.00, 3.05, 3.10, 3.15, 3.20, 3.25, 3.30, 3.35, 3.40,
            3.45, 3.50, 3.55, 3.60, 3.65, 3.70, 3.75, 3.80, 3.85, 3.90,
            3.95, 4.00, 4.05, 4.10, 4.15, 4.20, 4.25, 4.31, 4.36, 4.40,
            4.45, 4.51, 4.55, 4.60, 4.66, 4.70, 4.75, 4.80, 4.85, 4.90,
            4.95, 5.00, 5.05, 5.11, 5.15, 5.20, 5.25, 5.30, 5.35, 5.41,
            5.45, 5.50, 5.55, 5.61, 5.66, 5.71, 5.76, 5.81, 5.86, 5.90,
            5.95, 6.00, 6.06, 6.10, 6.15, 6.21, 6.25, 6.31, 6.35, 6.41,
            6.45, 6.50, 6.56, 6.61, 6.65, 6.70, 6.76, 6.81, 6.86, 6.91,
            6.96, 7.01, 7.06, 7.11, 7.16, 7.21, 7.25, 7.30, 7.36, 7.41,
            7.45, 7.50, 7.56, 7.60, 7.66, 7.71, 7.75, 7.81, 7.85, 7.91,
            7.96, 8.00, 8.06, 8.10, 8.16, 8.21, 8.25, 8.30, 8.36, 8.41,
            8.46, 8.50, 8.55, 8.61, 8.66, 8.71, 8.76, 8.81, 8.86, 8.91,
            8.96, 9.01, 9.06, 9.11, 9.16, 9.20, 9.25, 9.30, 9.36, 9.41,
            9.46, 9.50, 9.56, 9.61, 9.66, 9.70, 9.76, 9.81, 9.85, 9.91,
            9.96, 10.01, 10.01, 10.10, 10.20, 10.30, 10.40, 10.50, 10.61, 10.71,
            10.81, 10.90, 11.01, 11.10, 11.21, 11.30, 11.41, 11.51, 11.60, 11.71,
            11.81, 11.91, 12.01, 12.11, 12.21, 12.31, 12.41, 12.51, 12.61, 12.72,
            12.80, 12.91, 13.01, 13.10, 13.21, 13.32, 13.41, 13.52, 13.61, 13.70,
            13.81, 13.91, 14.00, 14.12, 14.21, 14.31, 14.40, 14.50, 14.62, 14.72,
            14.82, 14.92, 15.02, 15.12, 15.20, 15.30, 15.41, 15.51, 15.61, 15.72,
            15.80, 15.91, 16.01, 16.10, 16.21, 16.32, 16.40, 16.51, 16.60, 16.71,
            16.80, 16.91, 17.00, 17.12, 17.21, 17.32, 17.41, 17.51, 17.62, 17.72,
            17.81, 17.91, 18.00, 18.12, 18.22, 18.31, 18.41, 18.51, 18.60, 18.70,
            18.80, 18.90, 19.02, 19.10, 19.20, 19.30, 19.40, 19.51, 19.61, 19.71,
            19.82, 19.92, 20.02, 20.02, 21.02, 22.02, 23.02, 24.02, 25.03, 26.01,
            27.03, 28.01, 29.02, 30.03, 31.04, 32.03, 33.01, 34.02, 35.01, 36.03,
            37.04, 38.02, 39.02, 40.05, 41.05, 42.02, 43.02, 44.04, 45.02, 46.03,
            47.05, 48.04, 49.05, 50.01, 51.06, 52.06, 53.02, 54.06, 55.05, 56.05,
            57.01, 58.05, 59.04, 60.04, 61.06, 62.02, 63.07, 64.06, 65.07, 66.01,
            67.04, 68.01, 69.07, 70.07, 71.08, 72.01, 73.05, 74.01, 75.07, 76.05,
            77.05, 78.06, 79.08, 80.02, 81.07, 82.03, 83.00, 84.09, 85.08, 86.09,
            87.00, 88.03, 89.07, 90.02, 91.08, 92.05, 93.02, 94.01, 95.00, 96.01,
            97.02, 98.05, 99.08, 100.00,
        ]
        
        self.crash_animation_path = self.get_asset_path("crash", "crash_animation.webp")
        self.house_edge = 0.01
        self.max_history = 20

    def _get_text_position(self, text_img, frame_width, frame_height):
        if not text_img:
            return (0, 0)
        
        text_x = (frame_width - text_img.width) // 2
        text_y = int(frame_height * 0.35)
        
        return (text_x, text_y)

    def generate_crash_multiplier(self):
        r = random.random()
        multiplier = (1 - self.house_edge) / (1 - r)
        
        closest_multiplier = min(self.multipliers, key=lambda x: abs(x - multiplier))
        
        if closest_multiplier < 1.00:
            closest_multiplier = 1.00
            
        return closest_multiplier
    
    def get_multiplier_index(self, multiplier):
        for i, m in enumerate(self.multipliers):
            if abs(m - multiplier) < 0.001:
                return i
        return 0
    
    def calculate_win(self, bet_amount, cashout_multiplier, crash_multiplier):
        if cashout_multiplier is None:
            return 0, -bet_amount, crash_multiplier
        
        if cashout_multiplier < crash_multiplier:
            payout_float = bet_amount * cashout_multiplier
            payout = int(math.floor(payout_float))
            net_win = payout - bet_amount
            return payout, net_win, cashout_multiplier
        else:
            return 0, -bet_amount, crash_multiplier

    def calculate_split_win(self, bet_amount, mult1, mult2, crash_multiplier):
        half_bet = bet_amount // 2
        remainder = bet_amount % 2
        
        if mult1 < crash_multiplier:
            win1_float = half_bet * mult1
            win1 = int(math.floor(win1_float))
            cashout1 = True
        else:
            win1 = 0
            cashout1 = False
        
        if mult1 < crash_multiplier and mult2 < crash_multiplier:
            win2_float = (half_bet + remainder) * mult2
            win2 = int(math.floor(win2_float))
            cashout2 = True
        else:
            win2 = 0
            cashout2 = False
        
        total_payout = win1 + win2
        net_win = total_payout - bet_amount
        
        if cashout1 and cashout2:
            cashouts = [mult1, mult2]
            did_win = True
        elif cashout1:
            cashouts = [mult1, None]
            did_win = True
        else:
            cashouts = [None, None]
            did_win = False
        
        return total_payout, net_win, cashouts, did_win

    def _get_frame_for_multiplier(self, img, multiplier):
        n_frames = getattr(img, "n_frames", 1)
        
        if n_frames == 1:
            return 0
        
        multiplier_index = self.get_multiplier_index(multiplier)
        max_index = len(self.multipliers) - 1
        
        if n_frames <= max_index + 1:
            frame_index = int((multiplier_index / max_index) * (n_frames - 2))
        else:
            frame_index = multiplier_index
        
        return min(frame_index, n_frames - 2)

    def _create_history_overlay(self, history, show_current=False):
        try:
            width = 60
            height = 300
            line_height = 16
            top_padding = 4
            
            overlay = self.text_renderer.render_text(
                text="",
                font_size=1,
                color=(0, 0, 0, 0)
            )
            
            overlay = overlay.crop((0, 0, width, height))
            
            total_items = min(len(history), self.max_history)
            
            for i in range(total_items):
                history_item = history[i]
                multiplier = history_item.get("multiplier", 1.0)
                cashout_multiplier = history_item.get("cashout_multiplier")
                did_win = history_item.get("did_win", False)
                is_current = history_item.get('is_current', False) and show_current
                
                if multiplier >= 100:
                    text = f"{multiplier:.0f}x"
                elif multiplier >= 10:
                    text = f"{multiplier:.1f}x"
                else:
                    text = f"{multiplier:.2f}x"
                
                if is_current:
                    if cashout_multiplier is None:
                        color = (255, 150, 150, 255)
                    elif did_win:
                        color = (150, 255, 150, 255)
                    else:
                        color = (255, 150, 150, 255)
                else:
                    if multiplier < 2.0:
                        color = (255, 50, 50, 200)
                    elif multiplier <= 3.0:
                        color = (150, 150, 150, 200)
                    else:
                        color = (100, 255, 100, 200)
                
                text_img = self.text_renderer.render_text(
                    text=text,
                    font_size=12,
                    color=color,
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                
                text_y_pos = top_padding + i * line_height
                text_x = (width - text_img.width) // 2
                
                overlay.paste(text_img, (text_x, text_y_pos), text_img)
            
            return overlay
            
        except Exception as e:
            logger.error(f"[Crash] Error creating history overlay: {e}")
            return None

    def _create_result_text_image(self, crash_multiplier, cashout_multiplier, did_win, bet_amount=None):
        try:            
            win_amount = 0
            loss_amount = 0
            
            if cashout_multiplier is not None and bet_amount:
                if did_win:
                    win_amount = int(bet_amount * cashout_multiplier) - bet_amount
                else:
                    loss_amount = bet_amount
            
            if cashout_multiplier is None:
                main_text = f"CRASHED"
                result_text = f"${bet_amount if bet_amount else 0}"
                status_text = "NO CASHOUT!"
                main_color = (255, 100, 100, 255)
                result_color = (255, 150, 150, 255)
                status_color = (220, 140, 140, 255)
            elif did_win:
                main_text = f"CASHOUT"
                result_text = f"${win_amount}"
                status_text = f"CRASHED AT {crash_multiplier:.2f}x"
                main_color = (100, 255, 100, 255)
                result_color = (180, 255, 180, 255)
                status_color = (140, 220, 140, 255)
            else:
                main_text = f"CRASHED"
                result_text = f"${loss_amount}"
                status_text = f"CASHOUT AT {cashout_multiplier:.2f}x"
                main_color = (255, 100, 100, 255)
                result_color = (255, 150, 150, 255)
                status_color = (220, 140, 140, 255)
            
            if not bet_amount:
                if cashout_multiplier is None:
                    result_text = f"{crash_multiplier:.2f}x"
                elif did_win:
                    result_text = f"{cashout_multiplier:.2f}x"
                else:
                    result_text = f"{crash_multiplier:.2f}x"
            
            main_text_img = self.text_renderer.render_text(
                text=main_text,
                font_size=30,
                color=main_color,
                stroke_width=3,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_offset=(2, 2)
            )
            
            result_text_img = self.text_renderer.render_text(
                text=result_text,
                font_size=36,
                color=result_color,
                stroke_width=4,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_offset=(3, 3)
            )
            
            status_text_img = self.text_renderer.render_text(
                text=status_text,
                font_size=20,
                color=status_color,
                stroke_width=2,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_offset=(1, 1)
            )
            
            spacing = 8
            total_height = main_text_img.height + result_text_img.height + status_text_img.height + (2 * spacing)
            total_width = max(main_text_img.width, result_text_img.width, status_text_img.width)
            
            result_img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
            
            main_x = (total_width - main_text_img.width) // 2
            main_y = 0
            
            result_x = (total_width - result_text_img.width) // 2
            result_y = main_text_img.height + spacing
            
            status_x = (total_width - status_text_img.width) // 2
            status_y = main_text_img.height + result_text_img.height + (2 * spacing)
            
            result_img.paste(main_text_img, (main_x, main_y), main_text_img)
            result_img.paste(result_text_img, (result_x, result_y), result_text_img)
            result_img.paste(status_text_img, (status_x, status_y), status_text_img)
            
            return result_img
            
        except Exception as e:
            logger.error(f"[Crash] Error creating result text: {e}")
            return None

    def _create_split_result_text_image(self, crash_multiplier, cashouts, did_win, bet_amount):
        try:            
            cashout1, cashout2 = cashouts
            half_bet = bet_amount // 2
            
            total_win = 0
            if cashout1 and cashout2:
                win1 = int(math.floor(half_bet * cashout1))
                win2 = int(math.floor((half_bet + (bet_amount % 2)) * cashout2))
                total_win = win1 + win2
                status = "BOTH CASHOUTS"
                detail = f""
            elif cashout1:
                win1 = int(math.floor(half_bet * cashout1))
                total_win = win1
                status = "1ST CASHOUT ONLY"
                detail = f""
            else:
                total_win = 0
                status = "NO CASHOUT"
                detail = f""
            
            net_win = total_win - bet_amount
            
            if net_win > 0:
                main_text = "SPLIT WIN!"
                main_color = (100, 255, 100, 255)
                result_color = (180, 255, 180, 255)
            elif net_win < 0:
                main_text = "SPLIT LOSE"
                main_color = (255, 100, 100, 255)
                result_color = (255, 150, 150, 255)
            else:
                main_text = "SPLIT BET"
                main_color = (255, 255, 100, 255)
                result_color = (255, 255, 180, 255)
            
            main_text_img = self.text_renderer.render_text(
                text=main_text,
                font_size=28,
                color=main_color,
                stroke_width=3,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_offset=(2, 2)
            )
            
            result_text = f"${net_win}" if net_win <= 0 else f"${net_win}"
            result_text_img = self.text_renderer.render_text(
                text=result_text,
                font_size=34,
                color=result_color,
                stroke_width=4,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_offset=(3, 3)
            )
            
            status_text_img = self.text_renderer.render_text(
                text=status,
                font_size=20,
                color=(200, 200, 200, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_offset=(1, 1)
            )
            
            detail_text_img = self.text_renderer.render_text(
                text=detail,
                font_size=18,
                color=(180, 180, 200, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255),
                shadow=False
            )
            
            crash_text_img = self.text_renderer.render_text(
                text=f"Crashed at {crash_multiplier:.2f}x",
                font_size=16,
                color=(150, 150, 150, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255),
                shadow=False
            )
            
            spacing = 6
            total_height = (main_text_img.height + result_text_img.height + 
                          status_text_img.height + detail_text_img.height + 
                          crash_text_img.height + (4 * spacing))
            total_width = max(main_text_img.width, result_text_img.width, 
                            status_text_img.width, detail_text_img.width,
                            crash_text_img.width)
            
            result_img = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
            
            current_y = 0
            
            main_x = (total_width - main_text_img.width) // 2
            result_img.paste(main_text_img, (main_x, current_y), main_text_img)
            current_y += main_text_img.height + spacing
            
            result_x = (total_width - result_text_img.width) // 2
            result_img.paste(result_text_img, (result_x, current_y), result_text_img)
            current_y += result_text_img.height + spacing
            
            status_x = (total_width - status_text_img.width) // 2
            result_img.paste(status_text_img, (status_x, current_y), status_text_img)
            current_y += status_text_img.height + spacing
            
            detail_x = (total_width - detail_text_img.width) // 2
            result_img.paste(detail_text_img, (detail_x, current_y), detail_text_img)
            current_y += detail_text_img.height + spacing
            
            crash_x = (total_width - crash_text_img.width) // 2
            result_img.paste(crash_text_img, (crash_x, current_y), crash_text_img)
            
            return result_img
            
        except Exception as e:
            logger.error(f"[Crash] Error creating split result text: {e}")
            return None

    def _create_complete_result_overlay(self, history, crash_multiplier=None, cashout_multiplier=None, 
                                    did_win=False, bet_amount=None, show_current=False, 
                                    frame_width=400, frame_height=400, split_bet=False,
                                    cashouts=None):
        try:            
            history_overlay = self._create_history_overlay(history, show_current)
            
            if crash_multiplier is None:
                return history_overlay
            
            if split_bet:
                result_text_img = self._create_split_result_text_image(
                    crash_multiplier, cashouts, did_win, bet_amount
                )
            else:
                result_text_img = self._create_result_text_image(
                    crash_multiplier, cashout_multiplier, did_win, bet_amount
                )
            
            if not result_text_img:
                return history_overlay
            
            text_x = (frame_width - result_text_img.width) // 2
            text_y = (frame_height - result_text_img.height) // 2
            
            history_x = frame_width - history_overlay.width - 10
            history_y = 50
            
            text_right = text_x + result_text_img.width
            history_left = history_x
            
            if text_right > history_left - 20:
                text_x = history_left - result_text_img.width - 20
                text_x = max(10, text_x)
            
            complete_overlay = Image.new('RGBA', (frame_width, frame_height), (0, 0, 0, 0))
            
            complete_overlay.alpha_composite(result_text_img, (text_x, text_y))
            complete_overlay.alpha_composite(history_overlay, (history_x, history_y))
            
            return complete_overlay
            
        except Exception as e:
            logger.error(f"[Crash] Error creating complete overlay: {e}")
            return None

    def get_custom_overlay(self, **kwargs):
        try:            
            frame_width = kwargs.get('frame_width', 400)
            frame_height = kwargs.get('frame_height', 400)
            
            crash_multiplier = kwargs.get('crash_multiplier')
            cashout_multiplier = kwargs.get('cashout_multiplier')
            did_win = kwargs.get('did_win', False)
            bet_amount = kwargs.get('bet_amount')
            
            split_bet = kwargs.get('split_bet', False)
            cashouts = kwargs.get('cashouts')
                        
            history = self.get_history()
            
            overlay_before = self._create_history_overlay(history)
            
            history_with_new = history.copy()
            if crash_multiplier is not None:
                cashout_for_history = cashout_multiplier
                if split_bet and cashouts:
                    cashout_for_history = cashouts[0] if cashouts[0] else None
                
                new_entry = {
                    "multiplier": crash_multiplier,
                    "cashout_multiplier": cashout_for_history,
                    "did_win": did_win,
                    "timestamp": time.time(),
                    "is_current": True
                }
                history_with_new.insert(0, new_entry)
            
            if len(history_with_new) > self.max_history:
                history_with_new = history_with_new[:self.max_history]
            
            overlay_after = self._create_complete_result_overlay(
                history=history_with_new,
                crash_multiplier=crash_multiplier,
                cashout_multiplier=cashout_multiplier,
                did_win=did_win,
                bet_amount=bet_amount,
                show_current=True,
                frame_width=frame_width,
                frame_height=frame_height,
                split_bet=split_bet,
                cashouts=cashouts
            )
            
            before_x = frame_width - overlay_before.width - 10 if overlay_before else frame_width - 70
            before_y = 50
            
            after_x = 0
            after_y = 0
            
            return {
                'before': {
                    'image': overlay_before,
                    'position': (before_x, before_y),
                    'type': 'crash_history'
                },
                'after': {
                    'image': overlay_after,
                    'position': (after_x, after_y),
                    'type': 'crash_complete'
                }
            }
            
        except Exception as e:
            logger.error(f"[Crash] Error in get_custom_overlay: {e}", exc_info=True)
            return None

    def _trim_animation_to_frame(self, animation_path, target_frame_idx, output_path=None):
        try:
            if output_path is None:
                output_path = os.path.join(self.get_app_path("temp"), f"trimmed_crash_{int(time.time()*1000)}.webp")
            
            with Image.open(animation_path) as img:
                n_frames = getattr(img, "n_frames", 1)
                
                if n_frames == 1:
                    img.save(output_path, format='WEBP', save_all=True, quality=80)
                    return output_path
                
                target_frame_idx = min(target_frame_idx, n_frames - 1)
                
                frames = []
                for i in range(target_frame_idx + 1):
                    img.seek(i)
                    frames.append(img.copy().convert("RGBA"))
                
                if len(frames) > 0:
                    frames[0].save(
                        output_path,
                        format='WEBP',
                        save_all=True,
                        append_images=frames[1:] if len(frames) > 1 else [],
                        duration=50,
                        loop=0,
                        quality=80
                    )
                    
                    return output_path
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"[Crash] Error trimming animation: {e}")
            return None

    def create_animation_with_custom_frames(self, crash_multiplier, cashout_multiplier, 
                                        user_info_before, user_info_after, 
                                        avatar_path, bg_path, animated=True,
                                        split_bet=False, cashouts=None, wins=None):
        try:
            if split_bet and cashouts:
                cashout1, cashout2 = cashouts
                did_win = cashout1 is not None
            else:
                did_win = cashout_multiplier is not None and cashout_multiplier < crash_multiplier
            
            bet_amount = user_info_before.get('bet', 0)
                        
            custom_overlay_kwargs = {
                'crash_multiplier': crash_multiplier,
                'cashout_multiplier': cashout_multiplier,
                'did_win': did_win,
                'bet_amount': bet_amount,
                'split_bet': split_bet,
                'cashouts': cashouts,
                'wins': wins
            }
            
            with Image.open(self.crash_animation_path) as img:
                if split_bet and cashouts:
                    cashout1, cashout2 = cashouts
                    if cashout1 and cashout2:
                        final_multiplier = cashout2
                    elif cashout1:
                        final_multiplier = crash_multiplier
                    else:
                        final_multiplier = crash_multiplier
                else:
                    if did_win:
                        final_multiplier = cashout_multiplier
                    else:
                        final_multiplier = crash_multiplier
                
                final_frame = self._get_frame_for_multiplier(img, final_multiplier)

            if not animated:
                temp_dir = self.get_app_path("temp")
                temp_path = os.path.join(temp_dir, f"temp_crash_{int(time.time()*1000)}.webp")
                
                with Image.open(self.crash_animation_path) as img:
                    img.seek(final_frame)
                    frame = img.convert("RGBA")
                    frame.save(temp_path, format='WEBP', quality=80)
                
                user_id = user_info_after.get('user_id', '')
                
                final_path = self.generate_static(
                    image_path=temp_path,
                    avatar_path=avatar_path,
                    bg_path=bg_path,
                    user_info=user_info_after,
                    custom_overlay_kwargs=custom_overlay_kwargs,
                    show_bet_amount=True,
                    show_win_text=False,
                    font_scale=0.8,
                    avatar_size=90,
                    win_text_scale=1.0
                )
                
                try:
                    os.remove(temp_path)
                except:
                    pass
                
                if final_path:
                    return final_path, None
                else:
                    return None, "Failed to generate static image"
            
            temp_animation_path = self._trim_animation_to_frame(
                self.crash_animation_path,
                final_frame,
                os.path.join(self.get_app_path("temp"), f"trimmed_anim_{int(time.time()*1000)}.webp")
            )
            
            if not temp_animation_path:
                return None, "Failed to trim animation"
            
            user_id = user_info_after.get('user_id', '')
            user = {
                'id': user_id,
                'level': user_info_after.get('level', 1),
                'level_progress': user_info_after.get('level_progress', 0)
            }
            
            output_path, error = self.generate_animation(
                base_animation_path=temp_animation_path,
                user_id=user_id,
                user=user,
                user_info_before=user_info_before,
                user_info_after=user_info_after,
                animated=True,
                frame_duration=50,
                last_frame_multiplier=50,
                custom_overlay_kwargs=custom_overlay_kwargs,
                show_win_text=False,
                font_scale=0.8,
                avatar_size=90,
                show_bet_amount=True,
                win_text_height=80
            )
            
            try:
                os.remove(temp_animation_path)
            except:
                pass
            
            if error:
                return None, error
            return output_path, None
            
        except Exception as e:
            logger.error(f"[Crash] Error creating animation: {e}", exc_info=True)
            return None, str(e)
        
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        if not os.path.exists(self.crash_animation_path):
            self.send_message_image(
                sender, file_queue, 
                "Crash animation file not found!", 
                "Fatal Error", cache, None
            )
            return ""
        
        if len(args) < 1:
            help_text = (
                "CRASH GAME\n\n"
                "Cash out before the multiplier crashes!\n\n"
                "**Usage:**\n"
                "/crash <bet> <cashout_multiplier>\n"
                "/crash <bet> <mult1>,<mult2> - Split bet mode\n\n"
                "**Examples:**\n"
                "/crash 100 2.5 - Bet $100, cashout at 2.5x\n"
                "/crash 100 1.5,3.0 - Split $100: half at 1.5x, half at 3.0x\n"
                "/crash 50 1.5 x - Static image version\n\n"
                "**Split Bet Rules:**\n"
                "• One bet, two cashout multipliers\n"
                "• Half cashout at mult1\n"
                "• Remaining half cashout at mult2\n"
                "• If crash before mult1 - lose whole bet\n"
                "• If crash between mult1 and mult2 - win only first half\n"
                "• If reach mult2 - win both halves\n"
                "• Winnings rounded down (no decimals)\n"
                "• Animation shows higher multiplier reached\n"
                "• Multiplier: 1.0x to 100.0x"
            )
            self.send_message_image(sender, file_queue, help_text, "Crash Game", cache, None)
            return ""
        
        bet_info, error = self.parse_bet(args)
        if error:
            self.send_message_image(sender, file_queue, error, "Invalid Usage", cache, None)
            return ""
        
        bet_type, amount, cashout_multiplier, static_mode, mult1, mult2 = bet_info
        
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, amount)
            
        if error == "Invalid user":
            self.send_message_image(sender, file_queue, "Invalid user!", "Validation Error", cache, user_id)
            return ""
        elif error:
            self.send_message_image(
                sender, file_queue, 
                f"Insufficient funds!\n\nRequired: ${amount}\nYour balance: ${user.get('balance', 0) if user else 0}",
                "Insufficient Funds", cache, user_id
            )
            return ""
        
        balance_before = user["balance"]
        
        crash_multiplier = self.generate_crash_multiplier()
        
        if bet_type == "split":
            payout, net_win, cashouts, did_win = self.calculate_split_win(
                amount, mult1, mult2, crash_multiplier
            )
            cashout_multiplier = cashouts[0] if cashouts[0] else None
        else:
            payout, net_win, effective_multiplier = self.calculate_win(
                amount, cashout_multiplier, crash_multiplier
            )
            did_win = cashout_multiplier is not None and cashout_multiplier < crash_multiplier
            cashouts = [cashout_multiplier] if cashout_multiplier else [None]
        
        new_balance = balance_before + net_win
        self.update_user_balance(user_id, new_balance)
        
        user_info_before = self.create_user_info(sender, amount, 0, balance_before, user.copy())
        
        try:
            newLevel, newLevelProgress = self.cache.add_experience(user_id, net_win, sender, file_queue)
        except Exception as e:
            logger.error(f"[Crash] Error adding experience: {e}")
            newLevel = user.get("level", 1)
            newLevelProgress = user.get("level_progress", 0.1)
        
        user["level"] = newLevel
        user["level_progress"] = newLevelProgress
        
        if net_win > 0:
            user_info_after = self.create_user_info(sender, amount, payout, new_balance, user)
        elif net_win < 0:
            user_info_after = self.create_user_info(sender, amount, -abs(net_win), new_balance, user)
        else:
            user_info_after = self.create_user_info(sender, amount, 0, new_balance, user)
        
        avatar_path = self.cache.get_avatar_path(user_id) if hasattr(self.cache, 'get_avatar_path') else None
        bg_path = self.cache.get_background_path(user_id) if hasattr(self.cache, 'get_background_path') else None
        
        if not avatar_path or not bg_path:
            self.send_message_image(
                sender, file_queue,
                "User resources not found!",
                "Resource Error", cache, user_id
            )
            return ""
        
        result_path, error = self.create_animation_with_custom_frames(
            crash_multiplier=crash_multiplier,
            cashout_multiplier=cashout_multiplier,
            user_info_before=user_info_before,
            user_info_after=user_info_after,
            avatar_path=avatar_path,
            bg_path=bg_path,
            animated=not static_mode,
            split_bet=(bet_type == "split"),
            cashouts=cashouts if bet_type == "split" else None
        )
        
        self.add_to_history(
            crash_multiplier=crash_multiplier,
            cashout_multiplier=cashout_multiplier,
            did_win=did_win
        )
        
        if error:
            self.send_message_image(sender, file_queue, f"Animation error: {error}", "Animation Error", cache, user_id)
            return ""
        
        file_queue.put(result_path)
        
        if bet_type == "split":
            bet_info_str = f"${amount} @ {mult1}x,{mult2}x"
            cashout_info = f"Cashouts: {cashouts}"
        else:
            bet_info_str = f"${amount}@{cashout_multiplier}x"
            cashout_info = f"Cashout: {cashout_multiplier}x"
        
        if net_win > 0:
            result_status = f"WIN ${net_win}"
        elif net_win < 0:
            result_status = f"LOSE ${abs(net_win)}"
        else:
            result_status = "BREAK EVEN"
        
        logger.info(
            f"[Crash{' SPLIT' if bet_type == 'split' else ''}] {sender} {bet_info_str} | "
            f"Crash: {crash_multiplier:.2f}x | {cashout_info} | "
            f"{result_status} | Balance: {balance_before} -> {new_balance}"
        )
        
        return ""

    def add_to_history(self, crash_multiplier, cashout_multiplier=None, did_win=False):
        if not hasattr(self, 'cache'):
            return
        
        history_key = "crash_history"
        history = self.cache.get_setting(history_key, [])
        
        history.insert(0, {
            "multiplier": crash_multiplier,
            "cashout_multiplier": cashout_multiplier,
            "did_win": did_win,
            "timestamp": time.time()
        })
        
        if len(history) > self.max_history:
            history = history[:self.max_history]
        
        self.cache.set_setting(history_key, history)
    
    def get_history(self):
        if not hasattr(self, 'cache'):
            return []
        
        history = self.cache.get_setting("crash_history", [])
        
        for item in history:
            if isinstance(item, dict):
                if "cashout_multiplier" not in item:
                    item["cashout_multiplier"] = None
                if "did_win" not in item:
                    item["did_win"] = False
            else:
                history[history.index(item)] = {
                    "multiplier": float(item) if isinstance(item, (int, float)) else 1.0,
                    "cashout_multiplier": None,
                    "did_win": False,
                    "timestamp": time.time()
                }
        
        while len(history) < self.max_history:
            history.append({
                "multiplier": 1.0,
                "cashout_multiplier": None,
                "did_win": False,
                "timestamp": 0
            })
        
        return history[:self.max_history]
    
    def parse_bet(self, args):
        if len(args) < 2:
            return None, "Usage: /crash <bet> <multiplier> OR /crash <bet> <mult1>,<mult2>"
        
        static_mode = False
        if args[-1].lower() == 'x':
            static_mode = True
            args = args[:-1]
        
        try:
            amount = int(args[0])
            if amount <= 0:
                return None, "Bet amount must be positive"
            
            if ',' in args[1]:
                mults = args[1].split(',')
                
                if len(mults) != 2:
                    return None, "Split bet format: /crash <bet> <mult1>,<mult2>"
                
                mult1 = float(mults[0])
                mult2 = float(mults[1])
                
                if mult1 < 1.0 or mult2 < 1.0:
                    return None, "Cashout multipliers must be at least 1.0"
                if mult1 > 100.0 or mult2 > 100.0:
                    return None, "Cashout multipliers cannot exceed 100.0"
                if mult2 <= mult1:
                    return None, "Second multiplier (mult2) must be greater than first multiplier (mult1)"
                
                return ("split", amount, None, static_mode, mult1, mult2), None
            else:
                cashout = float(args[1])
                if cashout < 1.0:
                    return None, "Cashout multiplier must be at least 1.0"
                if cashout > 100.0:
                    return None, "Cashout multiplier cannot exceed 100.0"
                
                return ("single", amount, cashout, static_mode, None, None), None
                
        except ValueError as e:
            logger.error(f"[Crash] Parse error: {e}")
            return None, "Invalid format. Use: /crash <bet> <multiplier> OR /crash <bet> <mult1>,<mult2>"
    
    def create_user_info(self, sender, amount, win, balance, user):
        return {  
            "user_id": str(user.get('id', '')),
            "username": sender,
            "bet": amount,
            "win": win,
            "balance": balance,
            "level": user.get("level", 1),
            "level_progress": user.get("level_progress", 0),
            "is_win": win > 0,
            "avatar_path": user.get("avatar_path", "")
        }

def register():
    plugin = CrashPlugin()
    logger.info("[Crash] Crash plugin registered")
    return {
        "name": "crash",
        "aliases": ["/cr"],
        "description": "CRASH GAME\n\n"
                "Cash out before the multiplier crashes!\n\n"
                "**Usage:**\n"
                "/crash <bet> <cashout_multiplier>\n"
                "/crash <bet> <mult1>,<mult2> - Split bet mode\n\n"
                "**Examples:**\n"
                "/crash 100 2.5 - Bet $100, cashout at 2.5x\n"
                "/crash 100 1.5,3.0 - Split $100: half at 1.5x, half at 3.0x\n"
                "/crash 50 1.5 x - Static image version\n\n"
                "**Split Bet Rules:**\n"
                "• One bet, two cashout multipliers\n"
                "• Half cashout at mult1\n"
                "• Remaining half cashout at mult2\n"
                "• If crash before mult1 - lose whole bet\n"
                "• If crash between mult1 and mult2 - win only first half\n"
                "• If reach mult2 - win both halves\n"
                "• Winnings rounded down (no decimals)\n"
                "• Animation shows higher multiplier reached\n"
                "• Multiplier: 1.0x to 100.0x",
        "execute": plugin.execute_game
    }