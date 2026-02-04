import os
import random
import time
from PIL import Image, ImageDraw, ImageSequence
from base_game_plugin import BaseGamePlugin
from logger import logger
import math

class PlinkoPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="plinko"
        )
        
        self.buckets_count = 15
        self.risk_levels = {
            'low': {
                'multipliers': [20.0, 4.0, 1.6, 1.3, 1.2, 1.1, 1.0, 0.5, 1.0, 1.1, 1.2, 1.3, 1.6, 4.0, 20.0],
                'description': 'Low risk - balanced multipliers',
                'stripe_color': 'low'
            },
            'medium': {
                'multipliers': [60.0, 12.0, 5.6, 3.2, 1.6, 1.1, 0.7, 0.2, 0.7, 1.1, 1.6, 3.2, 5.6, 12.0, 60.0],
                'description': 'Medium risk - higher variance',
                'stripe_color': 'medium'
            },
            'high': {
                'multipliers': [420.0, 50.0, 14.0, 5.3, 2.1, 0.5, 0.2, 0.0, 0.2, 0.5, 2.1, 5.3, 14.0, 50.0, 420.0],
                'description': 'High risk - extreme multipliers',
                'stripe_color': 'high'
            },
            'l': {
                'multipliers': [20.0, 4.0, 1.6, 1.3, 1.2, 1.1, 1.0, 0.5, 1.0, 1.1, 1.2, 1.3, 1.6, 4.0, 20.0],
                'description': 'Low risk - balanced multipliers',
                'stripe_color': 'low'
            },
            'm': {
                'multipliers': [60.0, 12.0, 5.6, 3.2, 1.6, 1.1, 0.7, 0.2, 0.7, 1.1, 1.6, 3.2, 5.6, 12.0, 60.0],
                'description': 'Medium risk - higher variance',
                'stripe_color': 'medium'
            },
            'h': {
                'multipliers': [420.0, 50.0, 14.0, 5.3, 2.1, 0.5, 0.2, 0.0, 0.2, 0.5, 2.1, 5.3, 14.0, 50.0, 420.0],
                'description': 'High risk - extreme multipliers',
                'stripe_color': 'high'
            }
        }
        
        self.fixed_probabilities = self._calculate_fixed_probabilities()
        
        self.bucket_file_ranges = {
            0: (1, 1),
            1: (1, 2),
            2: (1, 11),
            3: (1, 44),
            4: (1, 122),
            5: (1, 244),
            6: (1, 367),
            7: (1, 419),
            8: (1, 367),
            9: (1, 244),
            10: (1, 122),
            11: (1, 44),
            12: (1, 11),
            13: (1, 2),
            14: (1, 1),
        }
        
        self.max_balls = 5
        
    def _calculate_fixed_probabilities(self):
        n = 14
        probabilities = []
        total_paths = 2 ** n
        
        for k in range(15):
            comb_count = math.comb(n, k)
            probability = comb_count / total_paths
            probabilities.append(probability)
        
        return probabilities
    
    def get_base_animation_path(self, result_position):
        bucket = result_position
        
        if bucket not in self.bucket_file_ranges:
            logger.error(f"[Plinko] Invalid bucket: {bucket}")
            return None
            
        start, end = self.bucket_file_ranges[bucket]
        variant = random.randint(start, end)
        variant_str = f"{variant:03d}"
        
        animations_folder = self.get_asset_path("plinko", "plinko_animations")
        filename = f"plinko_bucket_{bucket}_{variant_str}.webp"
        animation_path = os.path.join(animations_folder, filename)
        
        if not os.path.exists(animation_path):
            logger.error(f"[Plinko] Animation file not found: {animation_path}")
            for v in range(start, end + 1):
                variant_str = f"{v:03d}"
                filename = f"plinko_bucket_{bucket}_{variant_str}.webp"
                animation_path = os.path.join(animations_folder, filename)
                if os.path.exists(animation_path):
                    logger.info(f"[Plinko] Found alternative animation: {filename}")
                    return animation_path
            
            return None
        
        return animation_path
    
    def get_multiple_balls_animation(self, buckets):
        try:
            first_animation_path = self.get_base_animation_path(
                result_position=buckets[0]
            )
            
            if not first_animation_path:
                return None
            
            animation_frames_list = []
            for i, bucket in enumerate(buckets):
                if i == 0:
                    continue
                    
                anim_path = self.get_base_animation_path(
                    result_position=bucket
                )
                
                if anim_path:
                    frames = self._load_animation_frames(anim_path)
                    if frames:
                        animation_frames_list.append(frames)
            
            if len(animation_frames_list) == 0:
                return first_animation_path
            
            first_frames = self._load_animation_frames(first_animation_path)
            max_frames = len(first_frames)
            for frames in animation_frames_list:
                max_frames = max(max_frames, len(frames))
            
            combined_frames = []
            for frame_idx in range(max_frames):
                frames_to_combine = []
                
                if frame_idx < len(first_frames):
                    frames_to_combine.append(first_frames[frame_idx])
                else:
                    frames_to_combine.append(first_frames[-1])
                
                for frames in animation_frames_list:
                    if frame_idx < len(frames):
                        frames_to_combine.append(frames[frame_idx])
                    else:
                        frames_to_combine.append(frames[-1])
                
                combined_frame = frames_to_combine[0].copy()
                for i in range(1, len(frames_to_combine)):
                    frame = frames_to_combine[i].copy()
                    combined_frame = Image.alpha_composite(combined_frame, frame)
                
                combined_frames.append(combined_frame)
            
            timestamp = int(time.time())
            temp_path = os.path.join(self.get_app_path("temp"), f"plinko_multi_{timestamp}.webp")
            
            if len(combined_frames) > 1:
                combined_frames[0].save(
                    temp_path,
                    format='WEBP',
                    save_all=True,
                    append_images=combined_frames[1:],
                    duration=40,
                    loop=0,
                    quality=90
                )
            else:
                combined_frames[0].save(temp_path, format='WEBP', quality=90)
            
            return temp_path
            
        except Exception as e:
            logger.error(f"[Plinko] Error creating multi-ball animation: {e}")
            return None
    
    def _load_animation_frames(self, animation_path):
        try:
            frames = []
            with Image.open(animation_path) as img:
                if hasattr(img, 'n_frames') and img.n_frames > 1:
                    for frame in ImageSequence.Iterator(img):
                        frames.append(frame.copy().convert("RGBA"))
                else:
                    frames.append(img.copy().convert("RGBA"))
            return frames
        except Exception as e:
            logger.error(f"[Plinko] Error loading animation: {e}")
            return []
            
    def get_custom_overlay(self, **kwargs):
        try:
            frame_width = kwargs.get('frame_width', 300)
            frame_height = kwargs.get('frame_height', 360)
            request = kwargs.get('request', None)
            
            custom_kwargs = {}
            if request and hasattr(request.options, 'custom_overlay_kwargs'):
                custom_kwargs = request.options.custom_overlay_kwargs or {}
            
            risk_level = custom_kwargs.get('risk_level', 'medium')
            buckets = custom_kwargs.get('buckets', [])
            result_buckets = custom_kwargs.get('result_buckets', [])
            
            overlay_before = self._create_plinko_overlay(
                frame_width=frame_width,
                risk_level=risk_level,
                buckets=[],
                highlight_current=False
            )
            
            overlay_after = self._create_plinko_overlay(
                frame_width=frame_width,
                risk_level=risk_level,
                buckets=result_buckets,
                highlight_current=True if result_buckets else False
            )
            
            overlay_y_position = frame_height - 40 - 40
            
            return {
                'before': {
                    'image': overlay_before,
                    'position': (0, overlay_y_position),
                    'type': 'before'
                },
                'after': {
                    'image': overlay_after,
                    'position': (0, overlay_y_position),
                    'type': 'after'
                }
            }
            
        except Exception as e:
            logger.error(f"[Plinko] Error in get_custom_overlay: {e}", exc_info=True)
            return None

    def _create_plinko_overlay(self, frame_width, risk_level, buckets=None, highlight_current=False):
        try:
            if buckets is None:
                buckets = []
                
            risk_data = self.risk_levels.get(risk_level, self.risk_levels['medium'])
            multipliers = risk_data['multipliers']
            
            overlay_height = 40
            overlay = Image.new('RGBA', (frame_width, overlay_height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            
            bar_colors = {
                'low': (53, 172, 254, 240),
                'medium': (255, 204, 48, 240),
                'high': (207, 57, 64, 240)
            }
            
            base_bar_color = bar_colors.get(risk_data['stripe_color'], (100, 100, 100, 240))
            
            bar_spacing = 0
            bar_width = (frame_width - bar_spacing * (self.buckets_count - 1)) // self.buckets_count
            total_width_needed = bar_width * self.buckets_count + bar_spacing * (self.buckets_count - 1)
            extra_width = frame_width - total_width_needed
            
            bar_height = 20
            x_start = 0
            y_start = (overlay_height - bar_height) // 2
            
            for i in range(self.buckets_count):
                current_bar_width = bar_width
                if i < extra_width:
                    current_bar_width += 1
                
                x = x_start
                y = y_start
                
                bucket_highlighted = i in buckets and highlight_current
                
                if bucket_highlighted:
                    ball_count_in_bucket = buckets.count(i)
                    if ball_count_in_bucket > 1:
                        r, g, b, a = base_bar_color
                        fill_color = (
                            min(255, r + 50),
                            min(255, g + 50),
                            min(255, b + 50),
                            a
                        )
                    else:
                        fill_color = base_bar_color
                    outline_color = (255, 255, 255, 255)
                    outline_width = 2
                else:
                    r, g, b, a = base_bar_color
                    fill_color = (r//2, g//2, b//2, a//2)
                    outline_color = (60, 60, 60, 180)
                    outline_width = 1
                
                draw.rectangle([x, y, x + current_bar_width, y + bar_height], 
                            fill=fill_color,
                            outline=outline_color,
                            width=outline_width)
                
                multiplier = multipliers[i]
                if multiplier.is_integer():
                    multiplier_text = f"{int(multiplier)}"
                else:
                    multiplier_text = f"{multiplier:g}"
                
                multiplier_image = self.text_renderer.render_text(
                    text=multiplier_text,
                    font_size=8,
                    color=(255, 255, 255, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255)
                )
                
                text_x = x + (current_bar_width - multiplier_image.width) // 2
                text_y = y + (bar_height - multiplier_image.height) // 2
                
                if bucket_highlighted:
                    if ball_count_in_bucket > 1:
                        counter_text = f"{ball_count_in_bucket}×"
                        counter_image = self.text_renderer.render_text(
                            text=counter_text,
                            font_size=8,
                            color=(255, 255, 100, 255),
                            stroke_width=1,
                            stroke_color=(0, 0, 0, 255)
                        )
                        counter_x = x + current_bar_width - counter_image.width - 2
                        counter_y = y + 2
                        overlay.alpha_composite(counter_image, (counter_x, counter_y))
                    
                    text_color = (255, 255, 100, 255)
                    multiplier_image = self.text_renderer.render_text(
                        text=multiplier_text,
                        font_size=8,
                        color=text_color,
                        stroke_width=1,
                        stroke_color=(0, 0, 0, 255)
                    )
                
                overlay.alpha_composite(multiplier_image, (text_x, text_y))
                
                x_start += current_bar_width + bar_spacing
            
            return overlay
            
        except Exception as e:
            logger.error(f"[Plinko] Error creating overlay: {e}")
            return None

    def calculate_win(self, bet_amount, risk_level, buckets):
        total_win = 0
        individual_wins = []
        
        for bucket in buckets:
            multiplier = self.risk_levels[risk_level]['multipliers'][bucket]
            win_amount = int(bet_amount * multiplier)
            total_win += win_amount
            individual_wins.append(win_amount)
        
        return total_win, individual_wins
    
    def validate_bet(self, bet_amount_str, risk_level, ball_count=1):
        try:
            bet_amount = int(bet_amount_str)
            
            if bet_amount < 1:
                return "Bet amount must be at least $1"
            
            if risk_level not in self.risk_levels:
                return f"Invalid risk level. Valid: low (l), medium (m), high (h)"
            
            if ball_count < 1 or ball_count > self.max_balls:
                return f"Ball count must be between 1 and {self.max_balls}"
            
            return None
            
        except ValueError:
            return "Bet amount must be a number"
    
    def draw_buckets(self, ball_count):
        buckets = random.choices(
            range(self.buckets_count),
            weights=self.fixed_probabilities,
            k=ball_count
        )
        return buckets
    
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        if len(args) == 0:
            help_text = self._get_help_message()
            self.send_message_image(sender, file_queue, help_text, "Plinko Help", cache, None)
            return None
        
        ball_count = 1
        animated = True
        
        if len(args) >= 2 and args[-1].lower() == "x":
            animated = False
            args = args[:-1]
        
        if len(args) >= 3 and args[-1].isdigit():
            ball_count = int(args[-1])
            args = args[:-1]
            if ball_count < 1 or ball_count > self.max_balls:
                self.send_message_image(sender, file_queue,
                                      f"Ball count must be between 1 and {self.max_balls}",
                                      "Plinko Error", cache, None)
                return None
        
        if len(args) < 2:
            self.send_message_image(sender, file_queue,
                                  f"Invalid arguments.\n\nUse: /plinko <amount> <low|medium|high> [balls=1-{self.max_balls}] [x]\n\nExample: /plinko 100 high 2",
                                  "Plinko Error", cache, None)
            return None
        
        try:
            bet_amount_str = args[0]
            risk_level = args[1].lower()
        except (ValueError, IndexError):
            self.send_message_image(sender, file_queue,
                                  "Invalid arguments format",
                                  "Plinko Error", cache, None)
            return None
        
        error = self.validate_bet(bet_amount_str, risk_level, ball_count)
        if error:
            self.send_message_image(sender, file_queue, error, "Plinko - Invalid Bet", cache, None)
            return None
        
        try:
            bet_amount = int(bet_amount_str)
            total_bet = bet_amount * ball_count
        except ValueError:
            self.send_message_image(sender, file_queue,
                                  "Invalid amount format!",
                                  "Plinko - Invalid Amount", cache, None)
            return None
        
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, total_bet)
        if error:
            if error == "Invalid user":
                self.send_message_image(sender, file_queue, "Invalid user!", "Plinko - Validation Error", cache, None)
            else:
                balance = user.get('balance', 0) if user else 0
                self.send_message_image(sender, file_queue,
                                      f"Insufficient funds!\n\n"
                                      f"You need: ${total_bet} (${bet_amount} × {ball_count} balls)\n"
                                      f"Your balance: ${balance}",
                                      "Plinko - Insufficient Funds", cache, user_id)
            return None
        
        balance_before = user["balance"]
        
        buckets = self.draw_buckets(ball_count)
        
        total_win, individual_wins = self.calculate_win(bet_amount, risk_level, buckets)
        net_win = total_win - total_bet
        new_balance = balance_before + net_win
        
        try:
            self.update_user_balance(user_id, new_balance)
        except Exception as e:
            logger.error(f"[Plinko] Error updating balance: {e}")
            self.send_message_image(sender, file_queue,
                                  "Error updating balance!",
                                  "Plinko - System Error", cache, user_id)
            return None
        
        user_info_before = self.create_user_info(sender, total_bet, 0, balance_before, user.copy())
        
        try:
            exp_amount = net_win if net_win > 0 else -total_bet
            newLevel, newLevelProgress = self.cache.add_experience(user_id, exp_amount, sender, file_queue)
            user["level"] = newLevel
            user["level_progress"] = newLevelProgress
        except Exception as e:
            logger.error(f"[Plinko] Error adding experience: {e}")
        
        if ball_count == 1:
            base_animation_path = self.get_base_animation_path(
                result_position=buckets[0]
            )
        else:
            base_animation_path = self.get_multiple_balls_animation(buckets)
        
        if not base_animation_path:
            self.send_message_image(sender, file_queue,
                                  f"Animation generation failed!",
                                  "Plinko - Animation Error", cache, user_id)
            return None
        
        user_info_after = self.create_user_info(sender, total_bet, net_win, new_balance, user)
        
        result_path, error = self.generate_animation(
            base_animation_path=base_animation_path,
            user_id=user_id,
            user=user,
            user_info_before=user_info_before,
            user_info_after=user_info_after,
            animated=animated,
            frame_duration=40,
            last_frame_multiplier=30,
            custom_overlay_kwargs={
                'risk_level': risk_level,
                'buckets': [],
                'result_buckets': buckets,
                'multipliers': [self.risk_levels[risk_level]['multipliers'][b] for b in buckets],
                'ball_count': ball_count
            },
            show_win_text=True,
            font_scale=0.1,
            win_text_scale=0.7,
            avatar_size=50,
            win_text_height=150,
        )
        
        if error or not result_path:
            logger.error(f"[Plinko] Animation error: {error}")
            result_text = self._get_result_text(risk_level, bet_amount, ball_count, buckets,
                                              [self.risk_levels[risk_level]['multipliers'][b] for b in buckets],
                                              individual_wins, total_win, net_win, new_balance)
            self.send_message_image(sender, file_queue, result_text, "Plinko Result", cache, user_id)
            return None
        
        try:
            file_queue.put(result_path)
        except Exception as e:
            logger.error(f"[Plinko] Error sending animation: {e}")
            self.send_message_image(sender, file_queue,
                                  "Error sending animation!",
                                  "Plinko - System Error", cache, user_id)
            return None
        
        bucket_counts = {}
        for bucket in buckets:
            bucket_counts[bucket] = bucket_counts.get(bucket, 0) + 1
        
        bucket_summary = ", ".join([f"bucket {b}" + (f" (×{count})" if count > 1 else "") 
                                  for b, count in bucket_counts.items()])
        
        logger.info(f"PLINKO: {sender} bet ${bet_amount} × {ball_count} balls on {risk_level} | "
                   f"Results: {bucket_summary} | "
                   f"Total win: ${total_win} | Net: {net_win:+} | Balance: {balance_before} -> {new_balance}")
        
        return None
    
    def _get_help_message(self):
        return (
            f"PLINKO GAME (max {self.max_balls} balls)\n"
            "Drop multiple balls at once for bigger wins!\n\n"
            "Commands:\n"
            f"/plinko <amount> low [balls=1-{self.max_balls}] - Low risk\n"
            f"/plinko <amount> medium [balls=1-{self.max_balls}] - Medium risk\n"
            f"/plinko <amount> high [balls=1-{self.max_balls}] - High risk\n\n"
            "Options:\n"
            "- Add number at the end for multiple balls\n"
            "- Add 'x' at the end for static image\n\n"
            f"Examples:\n"
            f"/plinko 100 high - Single $100 ball, high risk\n"
            f"/plinko 50 medium 3 - Three $50 balls, medium risk\n"
            f"/plinko 25 low 5 x - Five $25 balls, low risk, static image\n"
            f"Minimum bet per ball: $1"
        )
    
    def _get_result_text(self, risk_level, bet_amount, ball_count, buckets, multipliers, 
                        individual_wins, total_win, net_win, new_balance):
        risk_display = risk_level.upper()
        
        if net_win > 0:
            result_text = f"WIN +${net_win}"
        elif net_win < 0:
            result_text = f"LOSE -${abs(net_win)}"
        else:
            result_text = "BREAK EVEN"
        
        ball_summary = []
        for i in range(ball_count):
            ball_num = i + 1
            bucket = buckets[i]
            multiplier = multipliers[i]
            win = individual_wins[i]
            ball_summary.append(f"Ball {ball_num}: Position {bucket+1}/15 ×{multiplier:.1f} = ${win}")
        
        ball_summary_text = "\n".join(ball_summary)
        
        formatted_total_win = f"{total_win:,}" if total_win >= 1000 else total_win
        formatted_balance = f"{new_balance:,}" if new_balance >= 1000 else new_balance
        formatted_total_bet = f"{bet_amount * ball_count:,}" if bet_amount * ball_count >= 1000 else bet_amount * ball_count
        
        return (
            f"PLINKO RESULT ({ball_count} {'ball' if ball_count == 1 else 'balls'})\n"
            f"Risk: {risk_display}\n"
            f"Bet per ball: ${bet_amount}\n"
            f"Total bet: ${formatted_total_bet}\n\n"
            f"{ball_summary_text}\n\n"
            f"Total prize: ${formatted_total_win}\n"
            f"Result: {result_text}\n"
            f"Balance: ${formatted_balance}"
        )

def register():
    plugin = PlinkoPlugin()
    logger.info("[Plinko] Plinko plugin registered")
    return {
        "name": "plinko",
        "aliases": ["/p"],
        "description": (
            f"PLINKO GAME - Drop multiple balls at once! (max {plugin.max_balls} balls)\n\n"
            "Usage: /plinko <amount> <risk_level> [balls=1-5] [x]\n\n"
            "Available risk levels:\n"
            "- low (l) - Balanced multipliers (1.0-20.0x)\n"
            "- medium (m) - Higher variance (0.2-60.0x)\n"
            "- high (h) - Extreme multipliers (0.0-420.0x)\n\n"
            "Options:\n"
            "- Add number (1-5) for multiple balls\n"
            "- Add 'x' for static image (no animation)\n\n"
            "Examples:\n"
            "- /plinko 100 high           (single ball)\n"
            "- /plinko 50 medium 3        (3 balls, animated)\n"
            "- /plinko 25 low 5 x         (5 balls, static image)\n"
            "- /plinko 200 high 2 x       (2 balls, static image)\n\n"
            "The ball bounces through pins and lands in 1 of 15 positions.\n"
            "Each position has a different multiplier based on risk level."
        ),
        "execute": plugin.execute_game
    }