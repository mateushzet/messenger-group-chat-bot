import os
import time
import re
import configparser
import threading
from datetime import datetime
from collections import defaultdict
from PIL import Image, ImageDraw
from base_game_plugin import BaseGamePlugin
from logger import logger

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    logger.info("[ASK] google.generativeai imported successfully")
except ImportError as e:
    GEMINI_AVAILABLE = False
    logger.error(f"[ASK] google.generativeai not installed: {e}")


class ConfigReader:
    
    @staticmethod
    def get_gemini_api_key():
        try:
            app_path = os.path.dirname(os.path.abspath(__file__))
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(app_path)))
            config_path = os.path.join(base_dir, 'MessengerCasinoBot', 'app', 'config', 'config.ini')
            
            logger.info(f"[ASK] Reading config from: {config_path}")
            
            if not os.path.exists(config_path):
                logger.error(f"[ASK] Config file not found")
                return None
            
            config = configparser.ConfigParser()
            config.read(config_path, encoding='utf-8')
            
            if config.has_section('gemini') and config.has_option('gemini', 'api_key'):
                api_key = config.get('gemini', 'api_key').strip()
                if api_key:
                    logger.info(f"[ASK] Found Gemini API key (length: {len(api_key)})")
                    return api_key
                
            return None
                
        except Exception as e:
            logger.error(f"[ASK] Error reading config file: {e}")
            return None


class RateLimiter:
    
    def __init__(self, cooldown_seconds=3):
        self.cooldown = cooldown_seconds
        self.last_ask_time = defaultdict(float)
        self.lock = threading.Lock()
    
    def can_ask(self, user_id):
        with self.lock:
            current_time = time.time()
            last_time = self.last_ask_time[user_id]
            
            if current_time - last_time < self.cooldown:
                remaining = int(self.cooldown - (current_time - last_time))
                return False, remaining
            
            self.last_ask_time[user_id] = current_time
            return True, 0

class GamesKnowledgeBase:
    
    @staticmethod
    def get_all_games_descriptions():
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            games_file = os.path.join(current_dir, 'games_descriptions.txt')
            
            logger.info(f"[ASK] Looking for games file at: {games_file}")
            
            if not os.path.exists(games_file):
                logger.error(f"[ASK] games_descriptions.txt not found at {games_file}")
                return "Games descriptions file not found."
            
            file_size = os.path.getsize(games_file)
            logger.info(f"[ASK] Games file size: {file_size} bytes")
            
            games_info = []
            current_game = {}
            current_section = None
            current_content = []
            game_count = 0
            
            with open(games_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                logger.info(f"[ASK] Total lines in file: {len(lines)}")
                
                for line_num, line in enumerate(lines, 1):
                    original_line = line.rstrip()
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    if line.endswith(':') and line.isupper() and '_' not in line:
                        game_count += 1
                        logger.info(f"[ASK] Found game header at line {line_num}: {line}")
                        
                        if current_game and 'command' in current_game:
                            logger.info(f"[ASK] Saving game: {current_game.get('name', 'Unknown')} with keys: {list(current_game.keys())}")
                            
                            games_info.append(f"\n--- {current_game.get('name', 'Unknown')} ---")
                            games_info.append(f"Command: {current_game['command']}")
                            if 'aliases' in current_game:
                                aliases = current_game['aliases']
                                if isinstance(aliases, list):
                                    games_info.append(f"Aliases: {', '.join(aliases)}")
                                else:
                                    games_info.append(f"Aliases: {aliases}")
                            if 'description' in current_game:
                                games_info.append(f"Description: {current_game['description']}")
                            
                            for key in sorted(current_game.keys()):
                                if key not in ['name', 'command', 'aliases', 'description']:
                                    value = current_game[key]
                                    display_key = key.replace('_', ' ').title()
                                    games_info.append(f"\n{display_key}:")
                                    if isinstance(value, list):
                                        for item in value:
                                            games_info.append(f"  {item}")
                                    else:
                                        for line in value.split('\n'):
                                            games_info.append(f"  {line}")
                            
                            games_info.append("")
                        
                        game_name = line.replace(':', '').strip()
                        current_game = {'name': game_name}
                        current_section = None
                        current_content = []
                        logger.info(f"[ASK] Started new game: {game_name}")
                    
                    elif ':' in line and '_' in line and line.isupper():
                        if current_section and current_content:
                            section_key = current_section.lower()
                            current_game[section_key] = '\n'.join(current_content)
                            logger.info(f"[ASK]   Saved section '{current_section}' with {len(current_content)} lines")
                        
                        current_section = line.replace(':', '').strip()
                        current_content = []
                        logger.info(f"[ASK] Found section at line {line_num}: {line}")
                    
                    elif current_section:
                        current_content.append(line)
                    
                    else:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip().lower()
                            value = value.strip()
                            
                            logger.info(f"[ASK] Found key-value at line {line_num}: {key} = {value[:30]}...")
                            
                            if key == 'aliases':
                                aliases = [a.strip() for a in value.split(',')]
                                current_game[key] = aliases
                                logger.info(f"[ASK]   Aliases: {aliases}")
                            else:
                                current_game[key] = value
                        elif line.startswith('-') or line.startswith('*') or line.startswith('•') or line[0].isdigit():
                            if 'other' not in current_game:
                                current_game['other'] = []
                            current_game['other'].append(line)
            
            if current_section and current_content:
                section_key = current_section.lower()
                current_game[section_key] = '\n'.join(current_content)
                logger.info(f"[ASK]   Saved final section '{current_section}' with {len(current_content)} lines")
            
            if current_game and 'command' in current_game:
                logger.info(f"[ASK] Saving final game: {current_game.get('name', 'Unknown')}")
                games_info.append(f"\n--- {current_game.get('name', 'Unknown')} ---")
                games_info.append(f"Command: {current_game['command']}")
                if 'aliases' in current_game:
                    aliases = current_game['aliases']
                    if isinstance(aliases, list):
                        games_info.append(f"Aliases: {', '.join(aliases)}")
                    else:
                        games_info.append(f"Aliases: {aliases}")
                if 'description' in current_game:
                    games_info.append(f"Description: {current_game['description']}")
                
                for key in sorted(current_game.keys()):
                    if key not in ['name', 'command', 'aliases', 'description']:
                        value = current_game[key]
                        display_key = key.replace('_', ' ').title()
                        games_info.append(f"\n{display_key}:")
                        if isinstance(value, list):
                            for item in value:
                                games_info.append(f"  {item}")
                        else:
                            for line in value.split('\n'):
                                games_info.append(f"  {line}")
            
            if games_info:
                final_text = "\n".join(games_info)
                logger.info(f"[ASK] SUCCESS! Loaded {len(games_info)} lines, {game_count} games")
                logger.info(f"[ASK] Final text length: {len(final_text)} characters")
                logger.info(f"[ASK] First 500 chars: {final_text[:500]}...")
                return final_text
            
            logger.warning("[ASK] No games found in file!")
            return "No games available."
                
        except Exception as e:
            logger.error(f"[ASK] Error loading games from file: {e}", exc_info=True)
            return f"Cannot load games list. Error: {str(e)}"

class AskAssistant:
    
    MODELS_TO_TRY = [
        "models/gemma-3-27b-it",
        "models/gemma-3-12b-it",
        "models/gemma-3-4b-it",
        "models/gemma-3-1b-it"
    ]
    
    _instance = None
    _init_lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._init_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, api_key):
        if not hasattr(self, 'initialized'):
            with self._init_lock:
                if hasattr(self, 'initialized'):
                    return
                    
                self.api_key = api_key
                self.models = [] 
                self.current_model_index = 0
                self.gemini_available = False
                self.error_message = None
                self.system_prompt = None
                
                self.shared_history = []
                self.history_lock = threading.Lock()
                self.max_history = 10
                
                self.model_errors = {}
                self.model_lock = threading.Lock()
                
                logger.info("[ASK] Initializing SINGLETON assistant with SHARED history for ALL users")
                
                games_descriptions = GamesKnowledgeBase.get_all_games_descriptions()
                
                self.system_prompt = f"""You are Ela - an assistant at Sunday Casino messenger casino.

ABOUT YOU:
- Your name is Ela, you're an assistant at Sunday Casino
- Your main language is polish
- You adapt to the language of the question
- You speak directly, sometimes with irony, but remain helpful
- You don't avoid controversial topics - you discuss politics, religion, society
- Try to be specific, write short answers, but if necessary, elaborate on the topic.

YOU ARE TALKING TO PLAYERS OF THE CASINO - this is a shared conversation that everyone sees!

AVAILABLE GAMES IN THE CASINO:
{games_descriptions}

WHAT YOU CAN DO:
- Talk about games and help with commands
- Discuss ANY topic
- Express your opinion
- Use different speaking styles - from casual to serious
- Answer in the language of the question

IMPORTANT RULES:
1. Use the language of the question
2. ALWAYS answer questions - no taboo topics
3. You have context of the last {self.max_history} messages in this shared chat
4. Be helpfull and nice

IF YOU DON'T KNOW:
- Say "I don't know" instead of making things up
- Suggest where to look for information
- You can recommend contacting admin, other players or checking /help command
"""
                
                if GEMINI_AVAILABLE and self.api_key:
                    self._init_all_models()
                else:
                    self.error_message = "No API key"
                    
                self.initialized = True
    
    def _init_all_models(self):
        try:
            genai.configure(api_key=self.api_key)
            
            for model_name in self.MODELS_TO_TRY:
                try:
                    test_model = genai.GenerativeModel(model_name)
                    test_response = test_model.generate_content("Test")
                    if test_response and test_response.text:
                        self.models.append({
                            'name': model_name,
                            'model': test_model,
                            'errors': 0,
                            'last_used': 0
                        })
                        logger.info(f"[ASK] Successfully initialized model: {model_name}")
                    else:
                        logger.warning(f"[ASK] Model {model_name} returned empty response, skipping")
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                        logger.warning(f"[ASK] Model {model_name} has rate limit/quota issues: {error_msg[:100]}")
                    elif "not found" in error_msg.lower() or "404" in error_msg:
                        logger.warning(f"[ASK] Model {model_name} not available: {error_msg[:100]}")
                    else:
                        logger.warning(f"[ASK] Failed to initialize model {model_name}: {error_msg[:100]}")
                    continue
            
            if self.models:
                self.gemini_available = True
                model_names = [m['name'] for m in self.models]
                logger.info(f"[ASK] Successfully initialized {len(self.models)} models in order: {model_names}")
            else:
                self.error_message = "No working models found"
                logger.error("[ASK] No working models found!")
                
        except Exception as e:
            self.error_message = str(e)
            logger.error(f"[ASK] Gemini init error: {e}")
    
    def _get_next_model(self):
        if not self.models:
            return None, None
        
        with self.model_lock:
            for i, model_info in enumerate(self.models):
                if model_info.get('errors', 0) < 3:
                    model_info['last_used'] = time.time()
                    logger.info(f"[ASK] Using model {model_info['name']} (priority {i+1})")
                    return model_info['model'], model_info['name']
                else:
                    logger.warning(f"[ASK] Model {model_info['name']} has {model_info['errors']} errors, skipping")
            
            logger.warning("[ASK] All models have errors, resetting error counters")
            for model_info in self.models:
                model_info['errors'] = 0
            
            if self.models:
                self.models[0]['last_used'] = time.time()
                logger.info(f"[ASK] Using fallback model {self.models[0]['name']}")
                return self.models[0]['model'], self.models[0]['name']
            
            return None, None
    
    def _record_model_error(self, model_name, error):
        with self.model_lock:
            for model_info in self.models:
                if model_info['name'] == model_name:
                    model_info['errors'] = model_info.get('errors', 0) + 1
                    error_count = model_info['errors']
                    logger.warning(f"[ASK] Model {model_name} error #{error_count}: {error[:100]}")
                    
                    if error_count >= 5:
                        logger.error(f"[ASK] Model {model_name} has {error_count} errors, marking as degraded")
                    break
    
    def _build_prompt_with_history(self, user_message, sender_name):
        
        history_section = ""
        if self.shared_history:
            history_lines = ["\nRECENT CONVERSATION HISTORY (shared chat):"]
            for entry in self.shared_history[-self.max_history:]:
                role = "Player" if entry["role"] == "user" else "Ela"
                history_lines.append(f"{role}: {entry['content']}")
            history_section = "\n".join(history_lines)
        
        current_message = f"\nCURRENT MESSAGE FROM {sender_name}: {user_message}"
        
        prompt = f"{self.system_prompt}{history_section}{current_message}\nEla:"
        
        return prompt
    
    def get_answer(self, user_message, sender_name):
        
        if not self.gemini_available:
            return None, self.error_message or "Assistant unavailable"
        
        for attempt in range(len(self.models)):
            model, model_name = self._get_next_model()
            if not model:
                continue
            
            try:
                prompt = self._build_prompt_with_history(user_message, sender_name)
                
                logger.info(f"[ASK] Attempt {attempt + 1} using model: {model_name}")
                
                response = model.generate_content(prompt)
                
                if response and response.text:
                    answer = response.text.strip()
                    
                    self.add_to_history(user_message, answer, sender_name)
                    
                    logger.info(f"[ASK] Successfully got answer from {model_name} (tokens used: {attempt + 1} attempt)")
                    return answer, None
                else:
                    logger.warning(f"[ASK] Empty response from {model_name}")
                    self._record_model_error(model_name, "Empty response")
                    
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"[ASK] Error with {model_name}: {error_msg[:200]}")
                
                if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    logger.warning(f"[ASK] Rate limit/quota exceeded on {model_name} - switching to next model")
                elif "500" in error_msg or "503" in error_msg or "unavailable" in error_msg.lower():
                    logger.warning(f"[ASK] Model {model_name} unavailable - switching to next model")
                elif "timeout" in error_msg.lower():
                    logger.warning(f"[ASK] Timeout on {model_name} - switching to next model")
                elif "resource exhausted" in error_msg.lower():
                    logger.warning(f"[ASK] Resource exhausted on {model_name} - switching to next model")
                
                self._record_model_error(model_name, error_msg)
                continue
        
        logger.error(f"[ASK] All {len(self.models)} models failed")
        return None, "All AI models are currently unavailable. Please try again later."
    
    def add_to_history(self, user_message, answer, sender_name):
        with self.history_lock:
            self.shared_history.append({
                "role": "user",
                "content": f"{sender_name}: {user_message}",
                "time": datetime.now().isoformat()
            })
            
            self.shared_history.append({
                "role": "assistant",
                "content": answer,
                "time": datetime.now().isoformat()
            })
            
            if len(self.shared_history) > self.max_history:
                self.shared_history = self.shared_history[-self.max_history:]
            
            logger.debug(f"[ASK] Shared history now has {len(self.shared_history)} messages")

class AskPlugin(BaseGamePlugin):
    
    def __init__(self):
        super().__init__(game_name="ask")
        self.api_key = ConfigReader.get_gemini_api_key()
        self.rate_limiter = RateLimiter(cooldown_seconds=3)
        
        self.assistant = None
        self.assistant_lock = threading.Lock()
        
        if self.api_key:
            logger.info("[ASK] API key loaded")
        else:
            logger.warning("[ASK] No API key found")
    
    def _get_assistant(self):
        with self.assistant_lock:
            if self.assistant is None:
                self.assistant = AskAssistant(self.api_key)
            return self.assistant
    
    def remove_emojis(self, text):

        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"
            u"\U0001F300-\U0001F5FF" 
            u"\U0001F680-\U0001F6FF"
            u"\U0001F1E0-\U0001F1FF"
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001F900-\U0001F9FF"
            u"\U0001FA70-\U0001FAFF"
            u"\U00002600-\U000026FF"
            u"\U00002700-\U000027BF"
            "]+", flags=re.UNICODE)
        
        return emoji_pattern.sub(r'', text)
    
    def remove_markdown(self, text):
        if not text:
            return text
        
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        text = re.sub(r'\*\*\*(.*?)\*\*\*', r'\1', text)
        text = re.sub(r'___(.*?)___', r'\1', text)
        
        text = re.sub(r'`(.*?)`', r'\1', text)
        
        text = re.sub(r'```(.*?)```', r'\1', text, flags=re.DOTALL)
        
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
        
        text = re.sub(r'!\[(.*?)\]\(.*?\)', r'\1', text)
        
        text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
        
        text = re.sub(r'^[-*•]\s+', '', text, flags=re.MULTILINE)
        
        text = re.sub(r'^([-*_]){3,}$', '', text, flags=re.MULTILINE)
        
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
        
        return text
    
    def _create_text_image(self, text, is_error=False):
        if not self.text_renderer:
            return None
        
        text = self.remove_emojis(text)
        
        clean_text = self.remove_markdown(text)
        
        words = clean_text.split()
        lines = []
        current_line = ""
        max_length = 40
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_length:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        
        if not lines:
            lines = [text[:40]]
        
        top_margin = 30
        bottom_margin = 30
        side_margin = 40
        line_height = 38
        line_spacing = 5
        
        text_height = len(lines) * (line_height + line_spacing) - line_spacing
        total_height = top_margin + text_height + bottom_margin
        width = 720
        
        text_img = Image.new('RGBA', (width, total_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(text_img)
        
        background_color = (0, 0, 0, 240) if not is_error else (40, 0, 0, 240)
        draw.rectangle(
            [side_margin//2, top_margin//2, width - side_margin//2, total_height - bottom_margin//2],
            fill=background_color
        )
        
        y_pos = top_margin
        text_color = (255, 255, 255) if not is_error else (255, 150, 150)
        
        for line in lines:
            line_img = self.text_renderer.render_text(
                text=line,
                font_size=20,
                color=text_color,
                stroke_width=1,
                stroke_color=(0, 0, 0, 255)
            )
            
            x_pos = (width - line_img.width) // 2
            text_img.alpha_composite(line_img, (x_pos, y_pos))
            y_pos += line_height + line_spacing
        
        border_color = (100, 100, 100, 100) if not is_error else (150, 50, 50, 100)
        draw.rectangle(
            [0, 0, width-1, total_height-1],
            outline=border_color,
            width=1
        )
        
        return text_img
        
    def _process_question_async(self, user_id, user, sender, question, file_queue, avatar_url):

        try:
            assistant = self._get_assistant()
            
            answer, error_msg = assistant.get_answer(question, sender)
            
            img_path = os.path.join(self.results_folder, f"ask_{user_id}_{int(time.time())}.png")
            
            if answer and self.text_renderer:
                text_img = self._create_text_image(answer, is_error=False)
                if text_img:
                    text_img.save(img_path)
                    
                    overlay_path, error = self.apply_user_overlay(
                        img_path, user_id, sender, 0, 0, user["balance"], user,
                        show_win_text=False, font_scale=0.9, avatar_size=60
                    )
                    
                    if overlay_path:
                        file_queue.put(overlay_path)
                    else:
                        file_queue.put(img_path)
            else:
                error_text = f"Error: {error_msg}"
                if self.text_renderer:
                    text_img = self._create_text_image(error_text, is_error=True)
                    if text_img:
                        text_img.save(img_path)
                        
                        overlay_path, error = self.apply_user_overlay(
                            img_path, user_id, sender, 0, 0, user["balance"], user,
                            show_win_text=False, font_scale=0.9, avatar_size=60
                        )
                        
                        if overlay_path:
                            file_queue.put(overlay_path)
                        else:
                            file_queue.put(img_path)
        
        except Exception as e:
            logger.error(f"[ASK] Error in async processing: {e}")
            
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        if error:
            return ""
        
        if len(args) == 0:
            return "Ask me anything! Usage: /ask your question"
        
        can_ask, remaining = self.rate_limiter.can_ask(user_id)
        if not can_ask:
            limit_msg = f"Please wait {remaining} seconds before your next question!"
            
            if self.text_renderer:
                img_path = os.path.join(self.results_folder, f"ask_{user_id}_{int(time.time())}_limit.png")
                text_img = self._create_text_image(limit_msg, is_error=True)
                
                if text_img:
                    text_img.save(img_path)
                    overlay_path, error = self.apply_user_overlay(
                        img_path, user_id, sender, 0, 0, user["balance"], user,
                        show_win_text=False, font_scale=0.9, avatar_size=60
                    )
                    
                    if overlay_path:
                        file_queue.put(overlay_path)
                    else:
                        file_queue.put(img_path)
            return ""
        
        question = " ".join(args)
        thread = threading.Thread(
            target=self._process_question_async,
            args=(user_id, user, sender, question, file_queue, avatar_url)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"[ASK] Started async processing for user {user_id}")
        
        return ""


def register():
    logger.info("[ASK] Registering Ask plugin")
    plugin = AskPlugin()
    return {
        "name": "ask",
        "aliases": ["/ask"],
        "description": "AI assistant, ask questions using command /ask",
        "execute": plugin.execute_game
    }