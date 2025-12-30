import os
import random
import math
from datetime import datetime, timedelta
from base_game_plugin import BaseGamePlugin
from logger import logger
from PIL import Image, ImageDraw, ImageFont
from utils import _get_unique_id
import threading
import time

class MathChallengePlugin(BaseGamePlugin):
    def __init__(self):
        results_folder = self.get_app_path("temp")
        super().__init__(
            game_name="math",
            results_folder=results_folder,
        )
        
        self.answer_anim_folder = self.get_asset_path("reward/answer")
        self.math_bg_folder = self.get_asset_path("reward/math_question_bg")
        error_folder = self.get_asset_path("errors")
        self.error_folder = error_folder

        os.makedirs(self.results_folder, exist_ok=True)
        
        self.min_reward = 10
        self.max_reward = 100
        self.avg_target = 30
        
        self.new_balance_frames = 20
        self.question_generator = QuestionGenerator()
        
        self.available_backgrounds = self._load_available_backgrounds()
        
        self.scheduler_thread = None
        self.stop_scheduler = False
        self.file_queue = None
        self.next_challenge_pending = False

    def _load_available_backgrounds(self):
        if not os.path.exists(self.math_bg_folder):
            return []
        
        backgrounds = []
        for file in os.listdir(self.math_bg_folder):
            if file.lower().endswith('.png') and file.startswith('math_bg_'):
                try:
                    bg_number = int(file.split('_')[2].split('.')[0])
                    backgrounds.append({
                        'number': bg_number,
                        'path': os.path.join(self.math_bg_folder, file),
                        'file': file
                    })
                except (ValueError, IndexError):
                    continue
        
        backgrounds.sort(key=lambda x: x['number'])
        return backgrounds

    def _get_random_background(self):
        if not self.available_backgrounds:
            return None
        
        return random.choice(self.available_backgrounds)

    def _calculate_probabilities(self):
        rewards = list(range(self.min_reward, self.max_reward + 1, 10))
        avg = self.avg_target
        
        probs = []
        for reward in rewards:
            distance = abs(reward - avg)
            prob = max(0.05, 0.3 * (1 - distance / (self.max_reward - self.min_reward)))
            probs.append(prob)
        
        total = sum(probs)
        normalized_probs = [p/total for p in probs]
        
        return list(zip(rewards, normalized_probs))

    def _get_random_reward(self):
        rewards, probs = zip(*self._calculate_probabilities())
        return random.choices(rewards, weights=probs, k=1)[0]

    def _get_answer_animation_path(self, reward_amount):
        if not os.path.exists(self.answer_anim_folder):
            return None
        
        for file in os.listdir(self.answer_anim_folder):
            if file.lower().endswith('.webp'):
                if f"_{reward_amount:03d}" in file or f"_{reward_amount}" in file:
                    return os.path.join(self.answer_anim_folder, file)
        
        for file in os.listdir(self.answer_anim_folder):
            if file.lower().endswith('.webp') and file.startswith('reward_'):
                return os.path.join(self.answer_anim_folder, file)
        
        for file in os.listdir(self.answer_anim_folder):
            if file.lower().endswith('.webp'):
                return os.path.join(self.answer_anim_folder, file)
        
        return None

    def _generate_question_image(self, question, question_id):
        try:
            bg_info = self._get_random_background()
            if not bg_info:
                return self._generate_question_image_fallback(question, question_id)
            
            bg_img = Image.open(bg_info['path']).convert('RGB')
            draw = ImageDraw.Draw(bg_img)
            
            try:
                font_sizes = [48, 52, 56, 60]
                font = None
                for size in font_sizes:
                    try:
                        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size)
                        bbox = draw.textbbox((0, 0), question, font=font)
                        text_width = bbox[2] - bbox[0]
                        if text_width < 700:
                            break
                    except:
                        continue
                
                if font is None:
                    font = ImageFont.load_default()
            except:
                font = ImageFont.load_default()
            
            question_area = (100, 150, 700, 250)
            bbox = draw.textbbox((0, 0), question, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            if text_width < (question_area[2] - question_area[0] - 40):
                text_x = question_area[0] + (question_area[2] - question_area[0] - text_width) // 2
                text_y = question_area[1] + (question_area[3] - question_area[1] - text_height) // 2
                
                shadow_offset = 2
                draw.text((text_x + shadow_offset, text_y + shadow_offset), 
                         question, font=font, fill=(0, 0, 0))
                draw.text((text_x, text_y), question, font=font, fill=(255, 255, 255))
            else:
                if "=" in question:
                    parts = question.split("=", 1)
                    line1 = parts[0].strip() + " ="
                    line2 = "= " + parts[1].strip() if parts[1].strip() else "?"
                else:
                    mid = len(question) // 2
                    split_points = ['+', '-', '×', '÷']
                    split_pos = -1
                    
                    for i in range(mid - 10, mid + 10):
                        if 0 <= i < len(question):
                            if question[i] in split_points and i > 0 and i < len(question) - 1:
                                split_pos = i + 1
                                break
                    
                    if split_pos > 0:
                        line1 = question[:split_pos].strip()
                        line2 = question[split_pos:].strip()
                    else:
                        line1 = question[:mid]
                        line2 = question[mid:]
                
                for i, line in enumerate([line1, line2]):
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    line_x = question_area[0] + (question_area[2] - question_area[0] - line_width) // 2
                    line_y = question_area[1] + 20 + (i * 60)
                    
                    draw.text((line_x + shadow_offset, line_y + shadow_offset), 
                             line, font=font, fill=(0, 0, 0))
                    draw.text((line_x, line_y), line, font=font, fill=(255, 255, 255))
            
            output_path = os.path.join(self.results_folder, f"math_question_{question_id}.png")
            bg_img.save(output_path, 'PNG', quality=95)
            
            return output_path
            
        except Exception as e:
            return self._generate_question_image_fallback(question, question_id)

    def _generate_question_image_fallback(self, question, question_id):
        try:
            width, height = 800, 400
            bg_color1 = (random.randint(20, 40), random.randint(20, 40), random.randint(40, 80))
            bg_color2 = (random.randint(40, 60), random.randint(40, 60), random.randint(80, 120))
            
            bg_img = Image.new('RGB', (width, height), bg_color1)
            draw = ImageDraw.Draw(bg_img)
            
            for y in range(height):
                ratio = y / height
                r = int(bg_color1[0] + (bg_color2[0] - bg_color1[0]) * ratio)
                g = int(bg_color1[1] + (bg_color2[1] - bg_color1[1]) * ratio)
                b = int(bg_color1[2] + (bg_color2[2] - bg_color1[2]) * ratio)
                
                for x in range(width):
                    bg_img.putpixel((x, y), (r, g, b))
            
            symbols = ["+", "-", "×", "÷", "=", "√", "π"]
            try:
                symbol_font = ImageFont.truetype("arial.ttf", 24)
            except:
                symbol_font = ImageFont.load_default()
            
            for _ in range(30):
                symbol = random.choice(symbols)
                x = random.randint(0, width - 30)
                y = random.randint(0, height - 30)
                opacity = random.randint(30, 80)
                color = (220, 220, 255, opacity)
                
                symbol_img = Image.new('RGBA', (50, 50), (0, 0, 0, 0))
                symbol_draw = ImageDraw.Draw(symbol_img)
                symbol_draw.text((10, 10), symbol, font=symbol_font, fill=color)
                
                angle = random.randint(-30, 30)
                rotated = symbol_img.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0))
                bg_img.paste(rotated, (x, y), rotated)
                draw = ImageDraw.Draw(bg_img)
            
            try:
                title_font = ImageFont.truetype("arialbd.ttf", 42)
            except:
                title_font = ImageFont.load_default()
            
            title = "MATH QUESTION"
            title_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, 45), title, font=title_font, fill=(255, 255, 255))
            
            qx1, qy1 = 100, 150
            qx2, qy2 = width - 100, 250
            draw.rectangle([qx1, qy1, qx2, qy2], fill=(40, 50, 80))
            draw.rectangle([qx1, qy1, qx2, qy2], outline=(255, 255, 255), width=3)
            
            try:
                font = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), question, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = qx1 + (qx2 - qx1 - text_width) // 2
            text_y = qy1 + (qy2 - qy1 - 48) // 2
            
            draw.text((text_x + 2, text_y + 2), question, font=font, fill=(0, 0, 0))
            draw.text((text_x, text_y), question, font=font, fill=(255, 255, 255))
            
            instruction = "Answer using: /answer [number] or /a [number]"
            try:
                small_font = ImageFont.truetype("arial.ttf", 18)
            except:
                small_font = ImageFont.load_default()
            
            inst_bbox = draw.textbbox((0, 0), instruction, font=small_font)
            inst_x = (width - (inst_bbox[2] - inst_bbox[0])) // 2
            draw.text((inst_x, 300), instruction, font=small_font, fill=(0, 255, 100))
            
            output_path = os.path.join(self.results_folder, f"math_question_{question_id}.png")
            bg_img.save(output_path, 'PNG', quality=95)
            
            return output_path
            
        except Exception as e:
            return None

    def _generate_new_challenge(self):
        question, correct_answer = self.question_generator.generate_4number_question()
        reward = self._get_random_reward()
        challenge_id = _get_unique_id()
        
        challenge_data = {
            "id": challenge_id,
            "question": question,
            "correct_answer": correct_answer,
            "reward": reward,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "solved_by": None,
            "scheduled_for": None,
            "image_generated": False
        }
        
        return challenge_data

    def _check_answer(self, user_id, user_answer):
        challenge = self.cache.get_active_math_challenge()
        
        if not challenge:
            return False, None, None, "No active challenge"
        
        if challenge.get("solved_by"):
            return False, None, None, "Someone already solved this challenge"
        
        try:
            user_answer_num = float(user_answer)
            correct_answer = float(challenge["correct_answer"])
            
            if abs(user_answer_num - correct_answer) < 0.0001:
                reward = challenge["reward"]
                
                challenge["solved_by"] = user_id
                challenge["solved_at"] = datetime.now().isoformat()
                challenge["status"] = "solved"
                
                self.cache.set_active_math_challenge(challenge)
                
                self.next_challenge_pending = True
                
                self._schedule_next_challenge()
                
                return True, reward, challenge, None
            else:
                return False, None, None, "Wrong answer"
                
        except ValueError:
            return False, None, None, "Invalid answer format"

    def _schedule_next_challenge(self):
        now = datetime.now()
        
        next_hour = (now.replace(minute=0, second=0, microsecond=0) + 
                    timedelta(hours=1))
        random_minute = random.randint(0, 59)
        send_time = next_hour.replace(minute=random_minute)
        
        if send_time <= now:
            send_time += timedelta(hours=1)
        
        delay_seconds = (send_time - now).total_seconds()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.stop_scheduler = True
            self.scheduler_thread.join(timeout=1)
        
        self.stop_scheduler = False
        self.scheduler_thread = threading.Thread(
            target=self._send_challenge_after_delay,
            args=(delay_seconds, send_time),
            daemon=True
        )
        self.scheduler_thread.start()

    def _send_challenge_after_delay(self, delay_seconds, scheduled_time):
        try:
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            
            if self.stop_scheduler:
                return
            
            if self.next_challenge_pending or not self.cache.get_active_math_challenge():
                challenge = self._generate_new_challenge()
                challenge["scheduled_for"] = scheduled_time.isoformat()
                self.cache.set_active_math_challenge(challenge)
                self.next_challenge_pending = False
            else:
                challenge = self.cache.get_active_math_challenge()
                if not challenge:
                    return
            
            if challenge.get("solved_by"):
                challenge = self._generate_new_challenge()
                challenge["scheduled_for"] = scheduled_time.isoformat()
                self.cache.set_active_math_challenge(challenge)
            
            if self.file_queue:
                image_path = self._generate_question_image(
                    challenge["question"], 
                    challenge["id"]
                )
                
                if image_path:
                    self.file_queue.put(image_path)
                
        except Exception as e:
            pass

    def start_scheduler(self, file_queue):
        self.file_queue = file_queue
        
        challenge = self.cache.get_active_math_challenge()
        
        if challenge and challenge.get("scheduled_for"):
            scheduled_time = datetime.fromisoformat(challenge["scheduled_for"])
            now = datetime.now()
            
            if scheduled_time > now:
                delay_seconds = (scheduled_time - now).total_seconds()
                
                self.stop_scheduler = False
                self.scheduler_thread = threading.Thread(
                    target=self._send_challenge_after_delay,
                    args=(delay_seconds, scheduled_time),
                    daemon=True
                )
                self.scheduler_thread.start()
                return True
            else:
                self._send_challenge_after_delay(0, now)
                return True
        else:
            self._schedule_first_random_challenge()
            return True
    
    def _schedule_first_random_challenge(self):
        now = datetime.now()
        
        current_hour_start = now.replace(minute=0, second=0, microsecond=0)
        random_minute = random.randint(0, 59)
        
        send_time = current_hour_start.replace(minute=random_minute)
        
        if send_time <= now:
            send_time += timedelta(hours=1)
            random_minute = random.randint(0, 59)
            send_time = send_time.replace(minute=random_minute)
        
        delay_seconds = (send_time - now).total_seconds()
        
        self.stop_scheduler = False
        self.scheduler_thread = threading.Thread(
            target=self._send_challenge_after_delay,
            args=(delay_seconds, send_time),
            daemon=True
        )
        self.scheduler_thread.start()

    def _generate_win_animation(self, user_id, reward_amount, user_info_before, user_info_after):
        anim_path = self._get_answer_animation_path(reward_amount)
        
        if not anim_path:
            return None, "No animation available"
        
        user = self.cache.get_user(user_id)
        
        result_path, error = self.generate_animation(
            anim_path, 
            user_id, 
            user, 
            user_info_before, 
            user_info_after,
            animated=True,
            game_type="math"
        )
        
        return result_path, error

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        if command_name not in ["/answer", "/a"]:
            return "Use: /answer [number] or /a [number]"
        
        if not args:
            return "Provide answer: `/answer [number]`"
        
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 0)
        
        if error:
            self._send_error_image("validation_error", sender, file_queue)
            return ""
        
        answer = args[0].strip()
        
        is_correct, reward, challenge, error_msg = self._check_answer(user_id, answer)
        
        if error_msg:
            if "Wrong answer" in error_msg:
                self._send_error_image("math_wrong_answer", sender, file_queue)
            return f"{error_msg}"
        
        if is_correct:
            balance_before = user.get("balance", 0)
            
            self.cache.update_balance(user_id, reward)
            
            user = self.cache.get_user(user_id)
            balance_after = user["balance"]
            
            user_info_before = self.create_user_info(
                sender, 0, 0, balance_before, user.copy()
            )
            
            newLevel, newLevelProgress = self.cache.add_experience(
                user_id, reward, sender, file_queue
            )
            
            user["level"] = newLevel
            user["level_progress"] = newLevelProgress
            
            user_info_after = self.create_user_info(
                sender, 0, reward, balance_after, user
            )
            
            anim_path, anim_error = self._generate_win_animation(
                user_id, reward, user_info_before, user_info_after
            )
            
            if anim_path and not anim_error:
                file_queue.put(anim_path)
                
                return (
                    f"CORRECT ANSWER!\n"
                    f"Player: {sender}\n"
                    f"+{reward} coins\n"
                    f"New balance: {balance_after}\n"
                    f"Next math challenge will appear randomly in the next hour!"
                )
            else:
                return (
                    f"CORRECT ANSWER!\n"
                    f"Player: {sender}\n"
                    f"+{reward} coins\n"
                    f"New balance: {balance_after}"
                )
        
        return "Unexpected error"


class QuestionGenerator:
    
    def generate_4number_question(self):
        numbers = [random.randint(1, 9) for _ in range(4)]
        operators = []
        for _ in range(3):
            operators.append('+' if random.random() > 0.4 else '-')
        
        result = numbers[0]
        for i in range(3):
            if operators[i] == '+':
                result += numbers[i+1]
            else:
                result -= numbers[i+1]
        
        question_parts = []
        for i in range(4):
            question_parts.append(str(numbers[i]))
            if i < 3:
                question_parts.append(operators[i])
        
        question = " ".join(question_parts) + " = ?"
        
        return question, result
    
    def generate_question(self, difficulty="medium"):
        return self.generate_4number_question()
    
    def _generate_easy(self):
        return self.generate_4number_question()
    
    def _generate_medium(self):
        return self.generate_4number_question()
    
    def _generate_hard(self):
        return self.generate_4number_question()


def register():
    plugin = MathChallengePlugin()
    return {
        "name": "math",
        "aliases": ["/answer", "/a"],
        "description": "Answer the active math challenge",
        "execute": plugin.execute_game
    }