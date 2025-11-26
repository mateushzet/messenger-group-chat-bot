from PIL import Image
import random
import os
import itertools

BASE_DIR = os.path.dirname(__file__)
SLOTS_DIR = os.path.join(BASE_DIR, "games", "slots")

SYMBOL_IMAGES_FOLDER = os.path.join(SLOTS_DIR, "symbols")

def generate_all_combinations(symbol_images_folder="symbols", output_folder="all_combinations"):
    def load_animated_symbols():
        symbols = []
        if not os.path.exists(symbol_images_folder):
            return symbols
            
        symbol_files = []
        for f in os.listdir(symbol_images_folder):
            if f.startswith("slots_symbol_") and f.endswith(".gif"):
                symbol_files.append(f)
        
        symbol_files.sort(key=lambda x: int(x.split('_')[2].split('.')[0]))
        
        for img_file in symbol_files:
            try:
                img_path = os.path.join(symbol_images_folder, img_file)
                img = Image.open(img_path)
                frames = []
                
                if hasattr(img, 'n_frames') and img.n_frames > 1:
                    for frame in range(img.n_frames):
                        img.seek(frame)
                        frame_img = img.convert('RGBA')
                        frame_img = frame_img.resize((75, 75), Image.LANCZOS)
                        frames.append(frame_img)
                else:
                    frame_img = img.convert('RGBA')
                    frame_img = frame_img.resize((75, 75), Image.LANCZOS)
                    frames.append(frame_img)
                
                symbols.append(frames)
                
            except Exception as e:
                print(f"Error loading {img_file}: {e}")
        
        return symbols

    animated_symbols = load_animated_symbols()

    if not animated_symbols:
        return

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    symbol_count = len(animated_symbols)
    all_combinations = list(itertools.product(range(symbol_count), repeat=3))
    
    BONUS_SYMBOLS = [0]
    WILD_SYMBOLS = [1]

    filtered_combinations = []
    for comb in all_combinations:
        bonus_count = sum(1 for symbol in comb if symbol in BONUS_SYMBOLS)
        wild_count = sum(1 for symbol in comb if symbol in WILD_SYMBOLS)
        
        if bonus_count <= 1 and wild_count <= 1:
            filtered_combinations.append(comb)
    
    FPS = 60
    SYMBOL_SIZE = 75
    ROW_COUNT = 3
    REEL_POSITIONS = 32
    REEL_PIXEL_LENGTH = REEL_POSITIONS * SYMBOL_SIZE

    class SlotColumn:
        def __init__(self, target_symbols):
            self.symbols = [random.randint(0, len(animated_symbols)-1) for _ in range(REEL_POSITIONS)]
            
            if target_symbols and len(target_symbols) == 3:
                target_position = 10
                for i in range(3):
                    self.symbols[(target_position + i) % REEL_POSITIONS] = target_symbols[i]
            
            self.target_symbols = target_symbols
            self.position = SYMBOL_SIZE * 5
            self.speed = -12
            self.target_position = 0
            self.stopped = False
            self.spin_time = 0
            self.auto_stop_time = 60
            self.stopping = False
            self.frame_count = 0
            self.final_symbols = []
            self.overshoot_phase = False
            self.overshoot_distance = 0
            self.return_phase = False
            self.return_speed = 0
            self.stop_time = 0
            self.animation_played_once = False
            self.max_animation_frames = 0

        def set_stop(self):
            if self.target_symbols and len(self.target_symbols) == 3:
                target_position = 10
                self.target_position = target_position * SYMBOL_SIZE
            else:
                stop_index = 10
                self.target_position = stop_index * SYMBOL_SIZE
            
            self.stopping = True

        def update(self):
            if self.stopped:
                self.stop_time += 1
                return
                
            if self.stopping:
                target_pos = self.target_position
                current_pos = self.position
                diff = target_pos - current_pos
                distance_to_target = abs(diff)
                
                if not self.overshoot_phase and not self.return_phase:
                    self.position = (self.position + self.speed) % REEL_PIXEL_LENGTH
                    
                    if distance_to_target < 50:
                        self.speed = min(self.speed * 0.92, -3)
                    
                    if distance_to_target < 5 and abs(self.speed) > 1:
                        self.overshoot_phase = True
                        self.overshoot_distance = random.randint(10, 18)
                
                elif self.overshoot_phase and not self.return_phase:
                    self.position += self.speed
                    self.overshoot_distance += self.speed
                    
                    if self.overshoot_distance <= 0:
                        self.return_phase = True
                        self.return_speed = abs(self.speed) * 0.6
                        self.speed = 0
                
                elif self.return_phase:
                    self.position += self.return_speed
                    self.return_speed *= 0.9
                    
                    current_diff = target_pos - self.position
                    if abs(current_diff) <= 1 or self.return_speed < 0.3:
                        self.position = target_pos
                        self.speed = 0
                        self.return_speed = 0
                        self.stopped = True
                        self.stop_time = 0
                        self.save_final_symbols()
                        
                        self.max_animation_frames = 0
                        for symbol_idx in self.final_symbols:
                            if symbol_idx < len(animated_symbols):
                                symbol_frames = animated_symbols[symbol_idx]
                                self.max_animation_frames = max(self.max_animation_frames, len(symbol_frames))
            else:
                self.position = (self.position + self.speed) % REEL_PIXEL_LENGTH
                self.spin_time += 1
                
                if self.spin_time >= self.auto_stop_time and not self.stopping:
                    self.set_stop()

        def save_final_symbols(self):
            center_symbol_index = int(self.position // SYMBOL_SIZE) % REEL_POSITIONS
            self.final_symbols = []
            for j in range(ROW_COUNT):
                symbol_index_pos = (center_symbol_index + j) % REEL_POSITIONS
                symbol_idx = self.symbols[symbol_index_pos]
                self.final_symbols.append(symbol_idx)

        def get_symbol_frame(self, symbol_idx, position):
            if 0 <= symbol_idx < len(animated_symbols):
                symbol_frames = animated_symbols[symbol_idx]
                if self.stopped:
                    if not self.animation_played_once:
                        if self.stop_time < len(symbol_frames):
                            frame_idx = self.stop_time
                        else:
                            self.animation_played_once = True
                            frame_idx = len(symbol_frames) - 1
                    else:
                        frame_idx = len(symbol_frames) - 1
                else:
                    frame_idx = len(symbol_frames) - 1
                return symbol_frames[frame_idx]
            return None

        def draw_symbol(self, symbol_index, x, y, base_image):
            symbol_frame = self.get_symbol_frame(symbol_index, y)
            if symbol_frame:
                base_image.paste(symbol_frame, (int(x), int(y)), symbol_frame)

        def draw(self, base_image):
            center_symbol_index = int(self.position // SYMBOL_SIZE) % REEL_POSITIONS
            width, height = base_image.size
            
            for j in range(-2, 6):
                symbol_index_pos = (center_symbol_index + j) % REEL_POSITIONS
                symbol_index = self.symbols[symbol_index_pos]
                
                y_offset = self.position % SYMBOL_SIZE
                y_pos = j * SYMBOL_SIZE - y_offset
                
                x_pos = (width - SYMBOL_SIZE) // 2
                
                if y_pos + SYMBOL_SIZE > 0 and y_pos < height:
                    self.draw_symbol(symbol_index, int(x_pos), int(y_pos), base_image)

    for combination in filtered_combinations:
        column = SlotColumn(target_symbols=combination)
        images = []
        max_frames = 500
        stopped_frames = 0
        
        for frame in range(max_frames):
            column.update()
            img = Image.new('RGB', (75, 225), (20, 20, 30))
            column.draw(img)
            images.append(img)
            
            if column.stopped:
                stopped_frames += 1
                if stopped_frames >= column.max_animation_frames + 20:
                    break

        if images:
            filename = f"slots_{combination[0]}_{combination[1]}_{combination[2]}.webp"
            output_path = os.path.join(output_folder, filename)
            images[0].save(
                output_path,
                save_all=True,
                append_images=images[1:],
                duration=1000//FPS,
                loop=0,
                format="WEBP"
            )
            print(f"Zapisano: {filename}")

if __name__ == "__main__":
    generate_all_combinations(
        symbol_images_folder=SYMBOL_IMAGES_FOLDER,
        output_folder="all_combinations"
    )