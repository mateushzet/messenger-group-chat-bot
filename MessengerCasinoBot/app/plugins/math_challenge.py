import os
import random
from datetime import datetime, timedelta
from base_game_plugin import BaseGamePlugin
from logger import logger
from PIL import Image
from utils import _get_unique_id
import threading
import time
from queue import Queue, Empty

class MathChallengePlugin(BaseGamePlugin):
    def __init__(self):

        super().__init__(
            game_name="math"
        )
        
        self.answer_anim_folder = self.get_asset_path("reward/answer")
        self.math_bg_folder = self.get_asset_path("reward/math_question_bg")
        error_folder = self.get_asset_path("errors")
        self.error_folder = error_folder
        
        self.min_reward = 10
        self.max_reward = 100
        self.avg_target = 30
        
        self.new_balance_frames = 20
        self.question_generator = QuestionGenerator()
        
        self.available_backgrounds = self._load_available_backgrounds()
        
        self.scheduler_thread = None
        self.scheduler_running = False
        self.task_queue = Queue()
        self.current_delay = None
        self.current_challenge_id = None
        
        self.file_queue = None
        self.next_challenge_pending = False
        
    def initialize_math_scheduler(self, cache, file_queue):
        try:
            
            plugin = get_math_plugin_instance()
            plugin.cache = cache
            
            if hasattr(plugin, 'scheduler_running') and plugin.scheduler_running:
                logger.info("[MathChallenge] Scheduler already running")
                return plugin
            
            success = plugin.start_scheduler(file_queue)
            
            if success:
                logger.info(f"[MathChallenge] Scheduler started. First challenge will be sent at random time.")
            else:
                logger.critical(f"[MathChallenge] Failed to start scheduler")
            
            return plugin
            
        except Exception as e:
            logger.critical(f"[MathChallenge] Error initializing scheduler: {e}", exc_info=True)
            return None

    def _load_available_backgrounds(self):
        if not os.path.exists(self.math_bg_folder):
            logger.error(f"[MathChallenge] Background folder does not exist: {self.math_bg_folder}")
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
                except (ValueError, IndexError) as e:
                    logger.warning(f"[MathChallenge] Error parsing background file {file}: {e}")
                    continue
        
        backgrounds.sort(key=lambda x: x['number'])
        return backgrounds

    def _get_random_background(self):
        if not self.available_backgrounds:
            logger.warning("[MathChallenge] No backgrounds available")
            return None
        
        bg = random.choice(self.available_backgrounds)
        return bg

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
        
        result = list(zip(rewards, normalized_probs))
        return result

    def _get_random_reward(self):
        rewards, probs = zip(*self._calculate_probabilities())
        reward = random.choices(rewards, weights=probs, k=1)[0]
        return reward

    def _get_answer_animation_path(self, reward_amount):
        if not os.path.exists(self.answer_anim_folder):
            logger.warning(f"[MathChallenge] Animation folder does not exist: {self.answer_anim_folder}")
            return None
        
        padded_amount = f"{reward_amount:03d}"
        filename = f"reward_{padded_amount}.webp"
        path = os.path.join(self.answer_anim_folder, filename)
        
        if os.path.exists(path):
            logger.info(f"[MathChallenge] Found animation for reward {reward_amount}: {filename}")
            return path
        else:
            logger.critical(f"[MathChallenge] No animation found for reward {reward_amount}")
            return None

    def _generate_question_image(self, question, question_id):
        
        try:
            bg_info = self._get_random_background()
            if not bg_info:
                logger.warning("[MathChallenge] No background available, using fallback")
                return None
            
            bg_img = Image.open(bg_info['path']).convert('RGBA')

            question_img = self.text_renderer.render_text(
                text=question,
                font_size=48,
                color=(255, 255, 255, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_color=(0, 0, 0, 150),
                shadow_offset=(2, 2)
            )
            
            question_area = (100, 150, 700, 250)
            text_x = question_area[0] + (question_area[2] - question_area[0] - question_img.width) // 2
            text_y = question_area[1] + (question_area[3] - question_area[1] - question_img.height) // 2
            
            bg_img.alpha_composite(question_img, (text_x, text_y))
            
            output_path = os.path.join(self.results_folder, f"math_question_{question_id}.png")
            bg_img.save(output_path, 'PNG', quality=95)
            logger.info(f"[MathChallenge] Image saved to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.critical(f"[MathChallenge] Error generating question image: {e}")
            return None

    def _generate_new_challenge(self):
        logger.info("[MathChallenge] Generating new challenge")
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
        
        logger.info(f"[MathChallenge] New challenge created: ID={challenge_id}, Question={question}, Reward={reward}")
        return challenge_data

    def start_scheduler(self, file_queue):
        self.file_queue = file_queue
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            return True
        
        self.scheduler_running = True
        
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_main_loop,
            daemon=True,
            name="MathScheduler"
        )
        self.scheduler_thread.start()
        
        time.sleep(0.3)
        
        challenge = self.cache.get_active_math_challenge()
        
        if challenge:
            logger.info(f"[MathChallenge] Found existing challenge: ID={challenge.get('id')}, Status={challenge.get('status')}")
            if challenge.get("status") == "scheduled" and challenge.get("scheduled_for"):
                logger.info(f"[MathChallenge] Adding scheduled task for existing challenge")
                self._add_scheduled_task(challenge)
            elif challenge.get("status") == "active":
                logger.info("[MathChallenge] Challenge is already active")
            elif challenge.get("status") == "solved":
                logger.info("[MathChallenge] Challenge solved, scheduling new task")
                self._schedule_random_task()
        else:
            logger.info("[MathChallenge] No existing challenge, scheduling new task")
            self._schedule_random_task()
        
        return True
    
    def _scheduler_main_loop(self):
        logger.info("[MathChallenge] Scheduler main loop started")
        next_task_time = None
        current_task_id = None
        
        while self.scheduler_running:
            try:
                
                try:
                    task = self.task_queue.get(timeout=1.0)
                    
                    if task and task.get("type") == "schedule":
                        next_task_time = task["send_time"]
                        current_task_id = task["challenge_id"]
                        
                        now = datetime.now()
                        delay = (next_task_time - now).total_seconds()
                        
                        if delay <= 0:
                            self._execute_send_task(current_task_id)
                            next_task_time = None
                            current_task_id = None
                    
                    elif task and task.get("type") == "execute":
                        self._execute_send_task(task["challenge_id"])
                        next_task_time = None
                        current_task_id = None
                    
                    self.task_queue.task_done()
                    
                except Empty:
                    pass
                
                if next_task_time and current_task_id:
                    now = datetime.now()
                    
                    if now >= next_task_time:
                        self._execute_send_task(current_task_id)
                        next_task_time = None
                        current_task_id = None
                
                time.sleep(60)
                
            except Exception as e:
                logger.critical(f"[MathChallenge] Scheduler loop error: {e}")
                time.sleep(5)
        
        logger.critical("[MathChallenge] Scheduler main loop ended")

    def _execute_send_task(self, challenge_id):
        try:
            challenge = self.cache.get_active_math_challenge()
            
            if not challenge:
                logger.error(f"[MathChallenge] No active challenge found")
                return
            
            if challenge.get("id") != challenge_id:
                logger.warning(f"[MathChallenge] Challenge ID mismatch, skipping")
                return
            
            if challenge.get("status") != "scheduled":
                logger.warning(f"[MathChallenge] Challenge status is {challenge.get('status')}, not 'scheduled'")
                return
            
            challenge["status"] = "active"
            self.cache.set_active_math_challenge(challenge)
            logger.info(f"[MathChallenge] Challenge {challenge_id} activated")
            
            if self.file_queue:
                logger.info(f"[MathChallenge] Generating question image")
                image_path = self._generate_question_image(
                    challenge["question"],
                    challenge["id"]
                )
                if image_path:
                    logger.info(f"[MathChallenge] Queueing image: {image_path}")
                    self.file_queue.put(image_path)
                    challenge["image_generated"] = True
                    self.cache.set_active_math_challenge(challenge)
                else:
                    logger.critical(f"[MathChallenge] Failed to generate image")
            else:
                logger.critical(f"[MathChallenge] No file queue available")
            
        except Exception as e:
            logger.critical(f"[MathChallenge] Error executing task: {e}")

    def _add_scheduled_task(self, challenge):
        try:
            send_time = datetime.fromisoformat(challenge["scheduled_for"])
            now = datetime.now()
            
            delay = (send_time - now).total_seconds()
            
            if delay <= 0:
                task_type = "execute"
                logger.warning(f"[MathChallenge] Task is overdue, scheduling for immediate execution")
            else:
                task_type = "schedule"
                logger.info(f"[MathChallenge] Scheduling task for {send_time} ({delay:.1f}s from now)")
            
            task = {
                "type": task_type,
                "challenge_id": challenge["id"],
                "send_time": send_time,
                "created": now
            }
            
            self.task_queue.put(task)
            logger.info(f"[MathChallenge] Task added to queue: {task}")
            
        except Exception as e:
            logger.error(f"[MathChallenge] Error adding task: {e}")

    def _schedule_random_task(self):
        now = datetime.now()
        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        random_minute = random.randint(0, 59)
        send_time = next_hour.replace(minute=random_minute)
        
        if send_time <= now:
            send_time += timedelta(hours=1)
        
        logger.info(f"[MathChallenge] Next challenge scheduled for {send_time}")
        
        new_challenge = self._generate_new_challenge()
        new_challenge["scheduled_for"] = send_time.isoformat()
        new_challenge["status"] = "scheduled"
        self.cache.set_active_math_challenge(new_challenge)
        
        self._add_scheduled_task(new_challenge)

    def _check_answer(self, user_id, user_answer):
        logger.info(f"[MathChallenge] Checking answer from user {user_id}: {user_answer}")
        
        challenge = self.cache.get_active_math_challenge()
        
        if not challenge:
            logger.info("[MathChallenge] No active challenge")
            return False, None, None, "No active challenge"
        
        if challenge.get("status") != "active":
            logger.info(f"[MathChallenge] Challenge not active (status: {challenge.get('status')})")
            if challenge.get("status") == "scheduled":
                return False, None, None, "Challenge not yet active. Wait for the image to appear!"
            elif challenge.get("status") == "solved":
                return False, None, None, "Challenge already solved!"
            else:
                return False, None, None, "Challenge not available"
        
        if not challenge.get("image_generated", False):
            logger.info(f"[MathChallenge] Challenge image not yet generated/sent")
            return False, None, None, "Challenge image not yet sent. Please wait..."
        
        if challenge.get("solved_by"):
            logger.info(f"[MathChallenge] Challenge already solved by {challenge.get('solved_by')}")
            return False, None, None, "Someone already solved this challenge!"
        
        try:
            user_answer_num = float(user_answer)
            correct_answer = float(challenge["correct_answer"])
            
            logger.debug(f"[MathChallenge] User answer: {user_answer_num}, Correct answer: {correct_answer}")
            
            if user_answer_num == correct_answer:
                reward = challenge["reward"]
                
                challenge["solved_by"] = user_id
                challenge["solved_at"] = datetime.now().isoformat()
                challenge["status"] = "solved"
                self.cache.set_active_math_challenge(challenge)
                logger.info(f"[MathChallenge] Challenge marked as solved by {user_id}")
                
                new_question, new_correct_answer = self.question_generator.generate_4number_question()
                new_reward = self._get_random_reward()
                new_challenge_id = _get_unique_id()
                
                now = datetime.now()
                next_hour = (now.replace(minute=0, second=0, microsecond=0) + 
                        timedelta(hours=1))
                random_minute = random.randint(0, 59)
                send_time = next_hour.replace(minute=random_minute)
                
                if send_time <= now:
                    send_time += timedelta(hours=1)
                
                new_challenge = {
                    "id": new_challenge_id,
                    "question": new_question,
                    "correct_answer": new_correct_answer,
                    "reward": new_reward,
                    "created_at": now.isoformat(),
                    "status": "scheduled",
                    "solved_by": None,
                    "scheduled_for": send_time.isoformat(),
                    "image_generated": False
                }
                
                self.cache.set_active_math_challenge(new_challenge)
                logger.info(f"[MathChallenge] New challenge created: ID={new_challenge_id}, Scheduled for {send_time}")
                
                task = {
                    "type": "schedule",
                    "challenge_id": new_challenge_id,
                    "send_time": send_time,
                    "created": now
                }
                
                self.task_queue.put(task)
                
                return True, reward, challenge, None
            else:
                logger.info(f"[MathChallenge] Wrong answer. User: {user_answer_num}, Correct: {correct_answer}")
                return False, None, None, "Wrong answer!"
                
        except ValueError as e:
            logger.info(f"[MathChallenge] Invalid answer format: {user_answer}, Error: {e}")
            return False, None, None, "Invalid answer format! Please provide a number."
        except Exception as e:
            logger.error(f"[MathChallenge] Error in _check_answer: {e}", exc_info=True)
            return False, None, None, "Internal error"

    def stop_scheduler(self):
        logger.critical("[MathChallenge] Stopping scheduler")
        self.scheduler_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
            logger.critical("[MathChallenge] Scheduler thread stopped")

    def _generate_win_animation(self, user_id, reward_amount, user_info_before, user_info_after):

        anim_path = self._get_answer_animation_path(reward_amount)
        
        if not anim_path:
            logger.error(f"[MathChallenge] No animation available for reward {reward_amount}")
            return None, "No animation available"
        
        user = self.cache.get_user(user_id)
        if not user:
            logger.error(f"[MathChallenge] User {user_id} not found in cache")
            return None, "User not found"
        
        result_path, error = self.generate_animation(
            anim_path, 
            user_id, 
            user, 
            user_info_before, 
            user_info_after,
            animated=True,
            avatar_size=48,
            font_scale=0.7,
            show_bet_amount=False,
            frame_duration=60,
            last_frame_multiplier=30.0,
            show_win_text=False
        )
        
        if result_path:
            logger.info(f"[MathChallenge] Reward animation generated: {result_path}")
        else:
            logger.error(f"[MathChallenge] Reward animation generation failed: {error}")
        
        return result_path, error

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 0)
        
        if not args:
            challenge = self.cache.get_active_math_challenge()
            
            if challenge and challenge.get("status") == "active":
                if challenge.get("image_generated", False):
                    image_path = os.path.join(self.results_folder, f"math_question_{challenge['id']}.png")
                    
                    if os.path.exists(image_path):
                        file_queue.put(image_path)
                        
                        reward = challenge.get("reward", 0)
                        return f"**Current Math Challenge**\nReward: {reward} coins\nAnswer using: `/a [number]`"
                    else:
                        new_image_path = self._generate_question_image(challenge["question"], challenge["id"])
                        if new_image_path:
                            file_queue.put(new_image_path)
                            return f"**Current Math Challenge**\nReward: {reward} coins\nAnswer using: `/a [number]`"
                else:
                    self.send_message_image(sender, file_queue, 
                        "Math challenge is active!\n\nPlease wait for the image to appear first.",
                        "Math Challenge", cache, user_id)
                    return ""
            else:
                
                self.send_message_image(sender, file_queue, 
                    f"No active math challenge at the moment!\nMath challenges appear randomly once per hour.",
                    "Math Challenge", cache, user_id)
                return ""
        
        if command_name not in ["/answer", "/a"]:
            return "Use: /answer [number] or /a [number]"
        
        answer = args[0].strip()
        
        if error:
            self.send_message_image(sender, file_queue, "User validation failed!", "Error", cache, user_id)
            return ""
        
        is_correct, reward, challenge, error_msg = self._check_answer(user_id, answer)
        
        if error_msg:
            logger.warning(f"MathChallengePlugin: Answer check failed: {error_msg}")
            
            if "No active challenge" in error_msg:
                active_challenge = self.cache.get_active_math_challenge()
                if active_challenge:
                    status = active_challenge.get("status", "unknown")
                    if status == "scheduled":                        
                        self.send_message_image(sender, file_queue, 
                            f"No active math challenge at the moment!\nMath challenges appear randomly once per hour.",
                            "Math Challenge", cache, user_id)
                    elif status == "solved":
                        self.send_message_image(sender, file_queue, 
                            "Challenge already solved!\n\nWait for the next math challenge.",
                            "Math Challenge", cache, user_id)
                    else:
                        self.send_message_image(sender, file_queue, 
                            f"No active math challenge! (Status: {status})\n\nMath challenges appear randomly once per hour.",
                            "Math Challenge", cache, user_id)
                else:
                    self.send_message_image(sender, file_queue, 
                        "No math challenge scheduled!\n\nMath challenges appear randomly once per hour.",
                        "Math Challenge", cache, user_id)
            elif "Wrong answer" in error_msg:
                self.send_message_image(sender, file_queue, 
                    "Wrong answer!\n\nTry again or wait for the next challenge.",
                    "Math Challenge", cache, user_id)
            elif "already solved" in error_msg:
                self.send_message_image(sender, file_queue, 
                    "Challenge already solved!\n\nWait for the next math challenge.",
                    "Math Challenge", cache, user_id)
            elif "Invalid answer format" in error_msg:
                self.send_message_image(sender, file_queue, 
                    "Invalid answer format!\n\nPlease provide a number.\nExample: /a 42",
                    "Math Challenge", cache, user_id)
            elif "Challenge not yet active" in error_msg:
                active_challenge = self.cache.get_active_math_challenge()
                if active_challenge and active_challenge.get("status") == "scheduled":                   
                    self.send_message_image(sender, file_queue, 
                        f"Challenge not yet active!\nWait for the image to appear first.",
                        "Math Challenge", cache, user_id)
                else:
                    self.send_message_image(sender, file_queue, 
                        "Challenge not yet active!\nWait for the image to appear first.",
                        "Math Challenge", cache, user_id)
            else:
                self.send_message_image(sender, file_queue, 
                    f"Error: {error_msg}", 
                    "Math Challenge", cache, user_id)
            return ""
        
        if is_correct:
            balance_before = user.get("balance", 0)
            
            self.cache.update_balance(user_id, reward)
            
            user = self.cache.get_user(user_id)
            balance_after = user["balance"]
            
            user_info_before = self.create_user_info(
                sender, 0, 0, balance_before, user
            )
            
            user_info_after = self.create_user_info(
                sender, 0, reward, balance_after, user
            )
            
            anim_path, anim_error = self._generate_win_animation(
                user_id, reward, user_info_before, user_info_after
            )
            
            if anim_path and not anim_error:
                file_queue.put(anim_path)
                
                response = (
                    f"**CORRECT ANSWER!**\n\n"
                    f"**Player:** {sender}\n"
                    f"**Reward:** +{reward} coins\n"
                    f"**New balance:** {balance_after}\n\n"
                    f"Next math challenge will appear randomly in the next hour!"
                )
                return response
            else:
                response = (
                    f"**CORRECT ANSWER!**\n\n"
                    f"**Player:** {sender}\n"
                    f"**Reward:** +{reward} coins\n"
                    f"**New balance:** {balance_after}"
                )
                logger.error(f"[MathChallenge] Reward animation (error: {anim_error})")
                return response
        
        logger.error("[MathChallenge] Unexpected state in execute_game")
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

_math_plugin_instance = None

def get_math_plugin_instance():
    global _math_plugin_instance
    if _math_plugin_instance is None:
        _math_plugin_instance = MathChallengePlugin()
    return _math_plugin_instance

def register():
    plugin = get_math_plugin_instance()
    result = {
        "name": "answer",
        "aliases": ["/answer", "/a"],
        "description": "Answer math challenge - appears randomly once per hour\nUse: /answer <number> or /a <number>",
        "execute": plugin.execute_game
    }
    return result