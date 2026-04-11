import os
import random
import time
from PIL import Image, ImageDraw
from base_game_plugin import BaseGamePlugin
from logger import logger

class TreeGame:
    
    TREES = [
        {"id": 0, "name": "x2", "cost": 10, "multiplier": 2},
        {"id": 1, "name": "x3", "cost": 50, "multiplier": 3},
        {"id": 2, "name": "x5", "cost": 200, "multiplier": 5},
        {"id": 3, "name": "x10", "cost": 1000, "multiplier": 10}
    ]
    
    SLOT_COSTS = [0, 1000, 5000]
    
    MIN_TIME_PER_STAGE = 1 * 60 * 60 
    MAX_TIME_PER_STAGE = 3 * 60 * 60 
    
    GROWTH_STAGES = 16
    GROWTH_IMAGES = 8
    
    def __init__(self, user_id):
        self.user_id = user_id
        
        self.unlocked_trees = 1
        self.unlocked_slots = 1
        
        self.slots = [
            {"plant": None, "unlocked": True},
            {"plant": None, "unlocked": False},
            {"plant": None, "unlocked": False} 
        ]
    
    def to_dict(self):
        return {
            "unlocked_trees": self.unlocked_trees,
            "unlocked_slots": self.unlocked_slots,
            "slots": self.slots
        }
    
    @classmethod
    def from_dict(cls, user_id, data):
        game = cls(user_id)
        game.unlocked_trees = data.get("unlocked_trees", 1)
        game.unlocked_slots = data.get("unlocked_slots", 1)
        game.slots = data.get("slots", [
            {"plant": None, "unlocked": True},
            {"plant": None, "unlocked": False},
            {"plant": None, "unlocked": False}
        ])
        return game
    
    def find_first_empty_slot(self):
        for i, slot in enumerate(self.slots):
            if slot["unlocked"] and slot["plant"] is None:
                return i
        return -1
    
    def buy_slot(self, slot_index):
        if slot_index < 0 or slot_index >= len(self.slots):
            return False, "Invalid slot number"
        
        if self.slots[slot_index]["unlocked"]:
            return False, "This slot is already unlocked"
        
        cost = self.SLOT_COSTS[slot_index]
        return True, cost
    
    def unlock_slot(self, slot_index):
        if slot_index < len(self.slots):
            self.slots[slot_index]["unlocked"] = True
            self.unlocked_slots += 1
            return True
        return False
    
    def generate_tree_multiplier(self, max_multiplier):
        r = random.random()
        raw_multiplier = 1.1 / (1.0 - r)
        
        final_multiplier = min(raw_multiplier, max_multiplier)
        
        if final_multiplier < 1.0:
            final_multiplier = 1.0
        
        return round(final_multiplier, 2)
    
    def plant_tree(self, tree_id):
        slot_index = self.find_first_empty_slot()
        
        if slot_index == -1:
            return False, "No empty slots available! Buy a new slot or harvest existing trees."
        
        if tree_id < 0 or tree_id >= self.unlocked_trees:
            return False, "This tree is not unlocked"
        
        tree = self.TREES[tree_id]
        cost = tree["cost"]
        max_multiplier = tree["multiplier"]
        
        final_multiplier = self.generate_tree_multiplier(max_multiplier)
        
        if final_multiplier >= max_multiplier:
            final_stage = self.GROWTH_STAGES
            will_succeed = True
        else:
            will_succeed = False
            progress = (final_multiplier - 1.0) / (max_multiplier - 1.0)
            final_stage = int(progress * self.GROWTH_STAGES)
            final_stage = max(1, min(final_stage, self.GROWTH_STAGES - 1))
        
        min_total_time = final_stage * self.MIN_TIME_PER_STAGE
        max_total_time = final_stage * self.MAX_TIME_PER_STAGE
        growth_time = random.randint(int(min_total_time), int(max_total_time))
        
        stage_timestamps = self._generate_uneven_growth(growth_time, final_stage)
        
        plant = {
            "tree_id": tree_id,
            "planted_at": time.time(),
            "growth_time": growth_time,
            "current_stage": 0,
            "final_stage": final_stage,
            "final_multiplier": final_multiplier,
            "stage_timestamps": stage_timestamps,
            "will_succeed": will_succeed,
            "withered": False,
            "harvested": False
        }
        
        self.slots[slot_index]["plant"] = plant
        return True, (cost, slot_index + 1)
    
    def _calculate_multiplier_at_stage(self, max_multiplier, stage):
        if stage <= 0:
            return 1.0
        if stage >= self.GROWTH_STAGES:
            return max_multiplier
        
        progress = stage / self.GROWTH_STAGES
        multiplier = 1.0 + (max_multiplier - 1.0) * progress
        return round(multiplier, 1)
    
    def _generate_uneven_growth(self, total_time, final_stage):
        if final_stage == 0:
            return []
        
        timestamps = []
        current_time = 0
        
        for stage in range(1, final_stage + 1):
            if stage == final_stage:
                time_to_next = total_time - current_time
            else:
                remaining_time = total_time - current_time
                remaining_stages = final_stage - stage + 1
                avg_time = remaining_time / remaining_stages
                factor = random.uniform(0.5, 1.5)
                time_to_next = min(avg_time * factor, remaining_time * 0.8)
            
            current_time += time_to_next
            timestamps.append(current_time)
        
        return timestamps
    
    def water_plants(self):
        any_updated = False
        current_time = time.time()
        
        for slot in self.slots:
            if slot["plant"] and not slot["plant"]["harvested"]:
                plant = slot["plant"]
                
                if plant["withered"] or plant["current_stage"] >= plant["final_stage"]:
                    continue
                
                new_stage = plant["current_stage"]
                for i, timestamp in enumerate(plant["stage_timestamps"]):
                    stage_idx = i + 1
                    if stage_idx > plant["current_stage"] and current_time >= plant["planted_at"] + timestamp:
                        new_stage = stage_idx
                
                if new_stage > plant["current_stage"]:
                    plant["current_stage"] = new_stage
                    any_updated = True
                    
                    if new_stage == plant["final_stage"] and not plant["will_succeed"]:
                        plant["withered"] = True
        
        return any_updated
        
    def harvest_tree(self, slot_index):
        if slot_index < 0 or slot_index >= len(self.slots):
            return None, "Invalid slot number", 0
        
        slot = self.slots[slot_index]
        if not slot["plant"]:
            return None, "Nothing growing in this slot", 0
        
        plant = slot["plant"]
        if plant["harvested"]:
            return None, "This tree has already been harvested", 0
        
        self.water_plants()
        
        tree = self.TREES[plant["tree_id"]]
        base_cost = tree["cost"]
        
        loss_amount = 0
        
        if plant["withered"]:
            current_multiplier = 0
            win_amount = 0
            loss_amount = base_cost
        else:
            current_multiplier = self._calculate_multiplier_at_stage(
                tree["multiplier"], plant["current_stage"]
            )
            win_amount = int(base_cost * current_multiplier)
        
        next_tree_unlocked = False
        if (not plant["withered"] and 
            plant["current_stage"] >= plant["final_stage"] and 
            plant["will_succeed"] and
            plant["tree_id"] == self.unlocked_trees - 1 and
            self.unlocked_trees < len(self.TREES)):
            self.unlocked_trees += 1
            next_tree_unlocked = True
        
        plant["harvested"] = True
        slot["plant"] = None
        
        message = f"You harvested the tree! Earned: {win_amount} coins (x{current_multiplier} multiplier)"
        if plant["withered"]:
            message = f"The tree withered! You lost: {loss_amount} coins"
        if next_tree_unlocked:
            next_tree = self.TREES[plant["tree_id"] + 1]
            message += f"\nYou unlocked {next_tree['name']} tree!"
        
        return win_amount, message, loss_amount

    def get_slot_status(self, slot_index):
        if slot_index < 0 or slot_index >= len(self.slots):
            return None
        
        slot = self.slots[slot_index]
        if not slot["unlocked"]:
            return {
                "unlocked": False,
                "cost": self.SLOT_COSTS[slot_index]
            }
        
        if not slot["plant"]:
            return {
                "unlocked": True,
                "empty": True
            }
        
        plant = slot["plant"]
        tree = self.TREES[plant["tree_id"]]
        
        self.water_plants()
        
        if plant["withered"]:
            current_multiplier = 0
            status = "withered"
        elif plant["current_stage"] >= plant["final_stage"]:
            if plant["will_succeed"]:
                current_multiplier = tree["multiplier"]
                status = "ready"
            else:
                current_multiplier = self._calculate_multiplier_at_stage(
                    tree["multiplier"], plant["current_stage"]
                )
                status = "withered"
        else:
            current_multiplier = self._calculate_multiplier_at_stage(
                tree["multiplier"], plant["current_stage"]
            )
            status = "growing"
        
        progress = plant["current_stage"] / self.GROWTH_STAGES
        
        time_left = None
        if status == "growing" and plant["current_stage"] < plant["final_stage"]:
            next_stage_idx = plant["current_stage"]
            if next_stage_idx < len(plant["stage_timestamps"]):
                next_time = plant["planted_at"] + plant["stage_timestamps"][next_stage_idx]
                time_left = max(0, next_time - time.time())
        
        return {
            "unlocked": True,
            "empty": False,
            "tree_id": plant["tree_id"],
            "tree_name": tree["name"],
            "current_stage": plant["current_stage"],
            "current_multiplier": current_multiplier,
            "max_multiplier": tree["multiplier"],
            "progress": progress,
            "status": status,
            "time_left": time_left,
            "withered": plant["withered"]
        }

class TreeTableGenerator:
    """Image generator for Tree game"""
    
    SLOT_POSITIONS = [
        (230, 538),
        (580, 538),
        (930, 538)
    ]
    
    PLANT_WIDTH = 190
    PLANT_HEIGHT = 336
    
    TEXT_POSITIONS = {
        'slot1_mult': (233, 378),
        'slot2_mult': (580, 378),
        'slot3_mult': (933, 378)
    }
    
    def __init__(self, text_renderer=None):
        self.text_renderer = text_renderer
        self.loaded_plants = {}
        self.loaded_backgrounds = {}
        
    def load_elements(self, assets_folder):
        """Load graphic elements"""
        self.assets_folder = assets_folder
        self.plants_folder = os.path.join(assets_folder, "plants")
        self.backgrounds_folder = os.path.join(assets_folder, "backgrounds")
        
        logger.info(f"[Tree] Loading plants from: {self.plants_folder}")
        logger.info(f"[Tree] Loading backgrounds from: {self.backgrounds_folder}")
        
        if os.path.exists(self.plants_folder):
            files = os.listdir(self.plants_folder)
            logger.info(f"[Tree] Found {len(files)} files in plants folder")
            
            for filename in files:
                if filename.endswith('.png') and filename.startswith('plant_'):
                    try:
                        self.loaded_plants[filename] = Image.open(
                            os.path.join(self.plants_folder, filename)
                        ).convert('RGBA')
                        logger.info(f"[Tree] Loaded plant: {filename}")
                    except Exception as e:
                        logger.error(f"[Tree] Cannot load plant {filename}: {e}")
            
            logger.info(f"[Tree] Total plants loaded: {len(self.loaded_plants)}")
        else:
            logger.error(f"[Tree] Plants folder does not exist: {self.plants_folder}")
        
        if os.path.exists(self.backgrounds_folder):
            for filename in os.listdir(self.backgrounds_folder):
                if filename.endswith('.png') and filename.startswith('background_'):
                    try:
                        self.loaded_backgrounds[filename] = Image.open(
                            os.path.join(self.backgrounds_folder, filename)
                        ).convert('RGBA')
                        logger.info(f"[Tree] Loaded background: {filename}")
                    except Exception as e:
                        logger.error(f"[Tree] Cannot load background {filename}: {e}")
        else:
            logger.error(f"[Tree] Backgrounds folder does not exist: {self.backgrounds_folder}")

    def get_plant_filename(self, tree_id, image_stage, is_withered=False):
        if is_withered:
            return f"plant_-1_{image_stage}.png"
        else:
            return f"plant_{tree_id}_{image_stage}.png"

    def get_background_filename(self, game_state):
        unlocked_trees = game_state.get('unlocked_trees', 1)
        unlocked_slots = game_state.get('unlocked_slots', 1)
        
        trees_binary = []
        for i in range(4):
            trees_binary.append('1' if i < unlocked_trees else '0')
        
        slots_binary = []
        for i in range(3):
            slots_binary.append('1' if i < unlocked_slots else '0')
        
        return f"background_{'_'.join(trees_binary)}_{'_'.join(slots_binary)}.png"

    def _map_stage_to_image(self, current_stage, final_stage=None, is_withered=False):
        if is_withered:
            
            if current_stage == 0:
                return 1, True
            elif current_stage == 1:
                return 2, True
            elif current_stage == 2:
                return 3, True
            elif current_stage == 3:
                return 4, True
            elif current_stage == 4:
                return 5, True
            elif current_stage == 5:
                return 6, True
            elif current_stage == 6:
                return 7, True
            else:
                return 8, True
        
        if current_stage == 0:
            return 1, False
        elif current_stage == 1:
            return 2, False
        elif current_stage == 2:
            return 3, False
        elif current_stage == 3:
            return 4, False
        elif current_stage == 4:
            return 5, False
        elif current_stage == 5:
            return 6, False
        elif 6 <= current_stage <= 15:
            return 7, False
        elif current_stage >= 16:
            return 8, False
        
        return 1, False

    def _create_progress_bar(self, width, height, progress):
        bar = Image.new('RGBA', (width, height), (60, 60, 60, 255))
        draw = ImageDraw.Draw(bar)
        
        fill_width = int(width * progress)
        if fill_width > 0:
            draw.rectangle([0, 0, fill_width, height], fill=(76, 175, 80, 255))
        
        draw.rectangle([0, 0, width-1, height-1], outline=(200, 200, 200), width=2)
        return bar
    
    def generate_table_image(self, game_state, output_path, font_scale=1.0):
        
        multiplier_font_size = int(24 * font_scale)
        
        bg_filename = self.get_background_filename(game_state)
        logger.info(f"[Tree] Looking for background: {bg_filename}")
        
        bg_image = None
        
        if bg_filename in self.loaded_backgrounds:
            bg_image = self.loaded_backgrounds[bg_filename].copy()
            logger.info(f"[Tree] Using background: {bg_filename}")
        elif self.loaded_backgrounds:
            first_bg = list(self.loaded_backgrounds.keys())[0]
            bg_image = self.loaded_backgrounds[first_bg].copy()
            logger.info(f"[Tree] Using fallback background: {first_bg}")
        else:
            logger.error(f"[Tree] No backgrounds loaded, using gray fallback")
            bg_image = Image.new('RGBA', (1168, 784), (30, 40, 50, 255))
        
        if bg_image.size != (1168, 784):
            bg_image = bg_image.resize((1168, 784))
        
        if bg_image.mode != 'RGBA':
            bg_image = bg_image.convert('RGBA')
        
        table_img = bg_image.copy()
        
        slots = game_state.get('slots', [])
        unlocked_slots = game_state.get('unlocked_slots', 1)
        
        logger.info(f"[Tree] Processing {len(slots)} slots, unlocked: {unlocked_slots}")
        
        for i, slot_data in enumerate(slots):
            if i >= unlocked_slots:
                logger.info(f"[Tree] Slot {i+1} is locked")
                continue
            
            slot_x, slot_y = self.SLOT_POSITIONS[i]
            
            if slot_data and not slot_data.get('empty', True):
                plant = slot_data
                logger.info(f"[Tree] Slot {i+1} has plant: {plant.get('tree_name')}, stage: {plant.get('current_stage')}")
                
                tree_id = plant.get('tree_id', 0)
                current_stage = plant.get('current_stage', 0)
                is_withered = plant.get('withered', False)
                
                if is_withered:
                    image_stage, _ = self._map_stage_to_image(current_stage, is_withered=True)
                    plant_filename = self.get_plant_filename(tree_id, image_stage, is_withered=True)
                    logger.info(f"[Tree] Withered tree stage {current_stage} -> image stage {image_stage}: {plant_filename}")
                else:
                    image_stage, _ = self._map_stage_to_image(current_stage)
                    plant_filename = self.get_plant_filename(tree_id, image_stage, is_withered=False)
                    logger.info(f"[Tree] Internal stage {current_stage} -> image stage {image_stage}: {plant_filename}")
                
                if plant_filename in self.loaded_plants:
                    plant_img = self.loaded_plants[plant_filename].resize((self.PLANT_WIDTH, self.PLANT_HEIGHT))
                    
                    plant_x = slot_x - self.PLANT_WIDTH // 2
                    plant_y = slot_y - self.PLANT_HEIGHT // 2
                    
                    table_img.alpha_composite(plant_img, (plant_x, plant_y))
                    logger.info(f"[Tree] Planted image at ({plant_x}, {plant_y})")
                    
                    mult_x, mult_y = self.TEXT_POSITIONS[f'slot{i+1}_mult']
                    current_mult = plant.get('current_multiplier', 1.0)
                    
                    status = plant.get('status', '')
                    if status == 'withered':
                        mult_color = (255, 80, 80)
                    elif status == 'ready':
                        mult_color = (255, 215, 0)
                    else:
                        mult_color = (255, 255, 255)
                    
                    if self.text_renderer:
                        mult_img = self.text_renderer.render_text(
                            text=f"x{current_mult}",
                            font_size=multiplier_font_size,
                            color=mult_color,
                            stroke_width=2,
                            stroke_color=(0, 0, 0, 255)
                        )
                        text_x = mult_x - mult_img.width // 2
                        text_y = mult_y
                        table_img.alpha_composite(mult_img, (text_x, text_y))
                        
                        if status == 'growing':
                            progress = plant.get('progress', 0)
                            progress_bar = self._create_progress_bar(120, 12, progress)
                            bar_x = mult_x - 60
                            bar_y = mult_y + 30
                            table_img.alpha_composite(progress_bar, (bar_x, bar_y))
                else:
                    logger.error(f"[Tree] Plant image not found: {plant_filename}")
            else:
                logger.info(f"[Tree] Slot {i+1} is empty")
        
        table_img.save(output_path, format='PNG')
        logger.info(f"[Tree] Saved image to: {output_path}")

class TreePlugin(BaseGamePlugin):
    
    def __init__(self):
        super().__init__(game_name="tree")
        self.games = {}
        self.table_generator = TreeTableGenerator(self.text_renderer)
        
        try:
            assets_folder = self.get_asset_path("tree")
            logger.info(f"[Tree] Loading assets from: {assets_folder}")
            self.table_generator.load_elements(assets_folder)
        except Exception as e:
            logger.error(f"[Tree] Failed to load tree elements: {e}", exc_info=True)

    def load_game_state(self, user_id):
        user_id = str(user_id)
        
        if user_id in self.games:
            return self.games[user_id]
        
        if hasattr(self, 'cache') and self.cache:
            game_data = self.cache.get_game_state(user_id, self.game_name)
            if game_data:
                game = TreeGame.from_dict(user_id, game_data)
                self.games[user_id] = game
                return game
        
        game = TreeGame(user_id)
        self.games[user_id] = game
        return game
    
    def save_game_state(self, user_id):
        user_id = str(user_id)
        if user_id in self.games and hasattr(self, 'cache') and self.cache:
            game_data = self.games[user_id].to_dict()
            self.cache.save_game_state(user_id, self.game_name, game_data)
    
    def show_game_status(self, user_id, user, sender, file_queue):
        game = self.load_game_state(user_id)
        game.water_plants()
        self.save_game_state(user_id)
        
        img_path = os.path.join(self.results_folder, f"tree_{user_id}_status.png")
        
        slots_status = [game.get_slot_status(i) for i in range(3)]
        game_state = {
            'unlocked_trees': game.unlocked_trees,
            'unlocked_slots': game.unlocked_slots,
            'slots': slots_status
        }
        
        self.table_generator.generate_table_image(game_state, img_path, font_scale=0.9)
        
        with Image.open(img_path) as img:
            padded_img = Image.new('RGBA', (img.width + 40, img.height + 40), (0, 0, 0, 0))
            padded_img.paste(img, (20, 20))
            
            resized_img = padded_img.resize((800, 550), Image.Resampling.LANCZOS)
            
            resized_img.save(img_path)
        
        current_balance = user["balance"] if user else 0
        overlay_path, error = self.apply_user_overlay(
            img_path, user_id, sender, 0, 0, current_balance, user,
            show_win_text=False, font_scale=0.9, avatar_size=60
        )
        
        if overlay_path:
            file_queue.put(overlay_path)
            return True
        return False

    def _parse_multiple_values(self, args, start_index=1):
        if len(args) <= start_index:
            return []
        
        values = []
        remaining = ' '.join(args[start_index:])
        
        if ',' in remaining:
            parts = remaining.split(',')
            for part in parts:
                part = part.strip()
                if part:
                    try:
                        values.append(int(part))
                    except ValueError:
                        continue
        else:
            for arg in args[start_index:]:
                try:
                    values.append(int(arg))
                except ValueError:
                    continue
        
        return values
    
    def _parse_slots(self, args, start_index=1):
        if len(args) <= start_index:
            return []
        
        values = self._parse_multiple_values(args, start_index)
        slots = []
        
        for val in values:
            slot_num = val - 1
            if 0 <= slot_num <= 2:
                slots.append(slot_num)
        
        return list(set(slots))

    def _parse_costs(self, args, start_index=1):
        if len(args) <= start_index:
            return []
        
        values = self._parse_multiple_values(args, start_index)
        tree_ids = []
        
        for val in values:
            for tree in TreeGame.TREES:
                if tree["cost"] == val:
                    tree_ids.append(tree["id"])
                    break
        
        return tree_ids

    def _plant_multiple_trees(self, tree_ids, user_id, user, sender, file_queue):
        game = self.load_game_state(user_id)
        game.water_plants()
        
        total_cost = 0
        for tree_id in tree_ids:
            if tree_id >= game.unlocked_trees:
                self.send_message_image(sender, file_queue, 
                    f"Tree x{TreeGame.TREES[tree_id]['multiplier']} not unlocked yet",
                    "Tree Game", self.cache, user_id)
                self.show_game_status(user_id, user, sender, file_queue)
                return False
            
            tree = TreeGame.TREES[tree_id]
            total_cost += tree["cost"]
        
        if user["balance"] < total_cost:
            self.send_message_image(sender, file_queue, 
                f"Not enough coins! Need: {total_cost}, have: {user['balance']}",
                "Tree Game", self.cache, user_id)
            self.show_game_status(user_id, user, sender, file_queue)
            return False
        
        results = []
        planted_count = 0
        
        for tree_id in tree_ids:
            success, result = game.plant_tree(tree_id)
            
            if not success:
                results.append(f"Failed to plant: {result}")
                continue
            
            cost, slot_num = result
            planted_count += 1
            results.append(f"Planted x{TreeGame.TREES[tree_id]['multiplier']} in slot {slot_num}")
        
        new_balance = user["balance"] - total_cost
        self.update_user_balance(user_id, new_balance)
        user["balance"] = new_balance
        self.save_game_state(user_id)
        
        result_msg = "\n".join(results)
        if planted_count > 0:
            result_msg = f"Planted {planted_count} tree(s)!\n{result_msg}"
        
        self.send_message_image(sender, file_queue, result_msg, "Tree Game", self.cache, user_id)
        self.show_game_status(user_id, user, sender, file_queue)
        return True

    def _cut_multiple_trees(self, slots, user_id, user, sender, file_queue):
        game = self.load_game_state(user_id)
        game.water_plants()
        
        results = []
        total_win = 0
        total_loss = 0
        cut_count = 0
        withered_count = 0
        
        for slot in slots:
            win_amount, message, loss_amount = game.harvest_tree(slot)
            
            if win_amount is None:
                results.append(f"Slot {slot+1}: {message}")
                continue
            
            if win_amount > 0:
                total_win += win_amount
                cut_count += 1
                results.append(f"Slot {slot+1}: {message}")
            elif loss_amount > 0:
                total_loss += loss_amount
                withered_count += 1
                results.append(f"Slot {slot+1}: {message}")
            else:
                results.append(f"Slot {slot+1}: {message}")
        
        if total_win > 0:
            new_balance = user["balance"] + total_win
            self.update_user_balance(user_id, new_balance)
            user["balance"] = new_balance
        
        if total_loss > 0:
            new_level, new_progress = self.cache.add_experience(
                user_id, total_loss, sender, file_queue
            )
            user["level"] = new_level
            user["level_progress"] = new_progress
        
        self.save_game_state(user_id)
        
        result_msg = f"Harvested {cut_count} tree(s)!\nTotal earned: {total_win}\n\n" + "\n".join(results)
        
        self.send_message_image(sender, file_queue, result_msg, "Tree Game", self.cache, user_id)
        self.show_game_status(user_id, user, sender, file_queue)
        return True

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        
        self.cache = cache
        
        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        if error:
            self.send_message_image(sender, file_queue, 
                "Tree Commands:\n"
                "/tree - show garden\n"
                "/tree plant <cost> - plant a tree\n"
                "   Examples: /tree plant 10 50  (plant x2 and x3)\n"
                "             /tree plant 10,50,200 (plant x2, x3, x5)\n"
                "             /tree plant 200 1000 (plant x5 and x10)\n"
                "/tree cut <slot> - harvest tree(s)\n"
                "   Examples: /tree cut 1,2,3  (cut slots 1,2,3)\n"
                "             /tree cut 12 (cut slots 1 and 2)\n"
                "/tree buy slot <nr> - buy a slot\n"
                "/tree help - show this help",
                "Tree Game", cache, None)
            return ""
        
        game = self.load_game_state(user_id)
        
        if len(args) == 0:
            self.show_game_status(user_id, user, sender, file_queue)
            return ""
        
        cmd = args[0].lower()
                
        if cmd in ["help", "h", "?"]:
            self.send_message_image(sender, file_queue,
                "Tree Game Commands:\n\n"
                "PLANTING:\n"
                "/tree plant <cost> - Plant by cost (10,50,200,1000)\n"
                "Multiple planting: /tree plant 10 50 200\n"
                "                  /tree plant 10,50,200\n\n"
                "HARVESTING:\n"
                "/tree cut <slot> - Harvest specific slot\n"
                "/tree cut 1,2,3 - Harvest multiple slots\n"
                "/tree cut 13 - Harvest slots 1 and 3\n\n"
                "SLOTS:\n"
                "/tree buy slot <nr> - Unlock slot (2:1000, 3:5000)\n\n"
                "OTHER:\n"
                "/tree - Show garden\n"
                "/tree water - Update growth\n"
                "/tree help - This help\n\n"
                "Trees unlock automatically when you harvest at full multiplier!",
                "Tree Help", cache, user_id)
            return ""
                
        if cmd in ["plant", "p"]:
            if len(args) < 2:
                self.send_message_image(sender, file_queue, 
                    "Usage: /tree plant <cost> [more...]\n"
                    "Examples:\n"
                    "  /tree plant 10        - plant x2 tree\n"
                    "  /tree plant 10 50     - plant x2 and x3\n"
                    "  /tree plant 10,50,200 - plant x2, x3, x5\n"
                    "  /tree plant 200 1000  - plant x5 and x10\n"
                    "Available costs: 10 (x2), 50 (x3), 200 (x5), 1000 (x10)",
                    "Tree Game", cache, user_id)
                self.show_game_status(user_id, user, sender, file_queue)
                return ""
            
            tree_ids = self._parse_costs(args, 1)
            
            if not tree_ids:
                self.send_message_image(sender, file_queue, 
                    "Invalid cost! Available: 10 (x2), 50 (x3), 200 (x5), 1000 (x10)",
                    "Tree Game", cache, user_id)
                self.show_game_status(user_id, user, sender, file_queue)
                return ""
            
            self._plant_multiple_trees(tree_ids, user_id, user, sender, file_queue)
            return ""
        
        elif cmd in ["cut", "c", "harvest", "h"]:
            if len(args) < 2:
                self.send_message_image(sender, file_queue, 
                    "Usage: /tree cut <slot> [more...]\n"
                    "Examples:\n"
                    "  /tree cut 1      - cut slot 1\n"
                    "  /tree cut 1,2,3  - cut slots 1,2,3\n"
                    "  /tree cut 13     - cut slots 1 and 3",
                    "Tree Game", cache, user_id)
                self.show_game_status(user_id, user, sender, file_queue)
                return ""
            
            slots = self._parse_slots(args, 1)
            
            if not slots:
                self.send_message_image(sender, file_queue, 
                    "Invalid slot numbers! Use 1,2,3",
                    "Tree Game", cache, user_id)
                self.show_game_status(user_id, user, sender, file_queue)
                return ""
            
            self._cut_multiple_trees(slots, user_id, user, sender, file_queue)
            return ""
        
        elif cmd in ["buy", "b"]:
            if len(args) < 3:
                self.send_message_image(sender, file_queue,
                    "Usage: /tree buy slot <nr>",
                    "Tree Game", cache, user_id)
                self.show_game_status(user_id, user, sender, file_queue)
                return ""
            
            buy_type = args[1].lower()
            
            if buy_type in ["slot", "s"]:
                try:
                    slot = int(args[2]) - 1
                except ValueError:
                    self.send_message_image(sender, file_queue, "Slot number must be a number!", "Tree Game", cache, user_id)
                    self.show_game_status(user_id, user, sender, file_queue)
                    return ""
                
                if slot < 0 or slot > 2:
                    self.send_message_image(sender, file_queue, "Slot must be 1-3", "Tree Game", cache, user_id)
                    self.show_game_status(user_id, user, sender, file_queue)
                    return ""
                
                success, cost = game.buy_slot(slot)
                
                if not success:
                    self.send_message_image(sender, file_queue, cost, "Tree Game", cache, user_id)
                    self.show_game_status(user_id, user, sender, file_queue)
                    return ""
                
                if user["balance"] < cost:
                    self.send_message_image(sender, file_queue,
                        f"Not enough coins! You need: {cost}",
                        "Tree Game", cache, user_id)
                    self.show_game_status(user_id, user, sender, file_queue)
                    return ""
                
                game.unlock_slot(slot)
                new_balance = user["balance"] - cost
                self.update_user_balance(user_id, new_balance)
                user["balance"] = new_balance
                self.save_game_state(user_id)
                
                self.send_message_image(sender, file_queue,
                    f"You unlocked slot {slot+1} for {cost}!",
                    "Tree Game", cache, user_id)
                self.show_game_status(user_id, user, sender, file_queue)
                return ""
            
            else:
                self.send_message_image(sender, file_queue,
                    "Usage: /tree buy slot <nr>",
                    "Tree Game", cache, user_id)
                self.show_game_status(user_id, user, sender, file_queue)
                return ""
        
        elif cmd in ["water", "w", "update"]:
            game.water_plants()
            self.save_game_state(user_id)
            self.show_game_status(user_id, user, sender, file_queue)
            return ""
        
        else:
            self.send_message_image(sender, file_queue,
                "Unknown command. Use /tree help for commands.",
                "Tree Game", cache, user_id)
            self.show_game_status(user_id, user, sender, file_queue)
            return ""

def register():
    logger.info("[Tree] Registering Tree plugin")
    plugin = TreePlugin()
    return {
        "name": "tree",
        "aliases": ["/tree"],
        "description": "Tree Garden Game\n\n"
                      "Trees (cost):\n"
                      "10 - x2 tree\n"
                      "50 - x3 tree\n"
                      "200 - x5 tree\n"
                      "1000 - x10 tree\n\n"
                      "How it works:\n"
                      "Each tree has a random final multiplier determined at planting time\n"
                      "The multiplier is generated using a special formula that favors lower multipliers\n"
                      "Trees start at x1.0 and grow through 16 stages to reach their final multiplier\n"
                      "You never lose your investment - the minimum multiplier is always x1.0\n\n"
                      "Multiplier chances for x10 tree:\n"
                      "73% chance to reach at least x1.5\n"
                      "55% chance to reach at least x2.0\n"
                      "36% chance to reach at least x3.0\n"
                      "22% chance to reach at least x5.0\n"
                      "11% chance to reach x10.0\n\n"
                      "Growth:\n"
                      "16 stages (8 images, 2 stages per image)\n"
                      "Each stage takes 1.5-3 hours (total 24-48h for full tree)\n\n"
                      "Unlocking:\n"
                      "Trees unlock automatically when you harvest the previous tree at full multiplier\n"
                      "Example: Harvest x2 tree at x2 to unlock x3 tree\n\n"
                      "Slots:\n"
                      "- Slot 1: free\n"
                      "- Slot 2: 1000 coins\n"
                      "- Slot 3: 5000 coins\n\n"
                      "Commands:\n"
                      "/tree - show garden\n"
                      "/tree plant <cost> - plant a tree (auto slot)\n"
                      "/tree cut <slot> - harvest a tree\n"
                      "/tree buy slot <nr> - buy a slot\n"
                      "/tree water - update status\n"
                      "/tree help - show this help",
        "execute": plugin.execute_game
    }