from PIL import Image, ImageDraw, ImageFont
import random
import os
import glob
import math

BASE_DIR = os.path.dirname(__file__)
SLOTS_DIR = os.path.join(BASE_DIR, "games", "slots")

EFFECTS_FOLDER = os.path.join(SLOTS_DIR, "slots_effects")
COMBINATIONS_PATH = os.path.join(SLOTS_DIR, "all_combinations")

_effects_cache = {}
_FONT_CACHE = None

SYMBOL_SIZE = 75
WIDTH, HEIGHT = 225, 225
COLUMN_WIDTH = 75

AVAILABLE_WINS = [0, 0.4, 0.8, 2.0, 2.2, 2.4, 2.8, 3.0, 3.2, 3.6, 4.0, 4.4, 4.8, 5.0, 5.2, 5.6, 6.0, 6.4, 6.8, 7.0, 7.4, 7.8, 8.0, 9.0]

def get_cached_font():
    global _FONT_CACHE
    if _FONT_CACHE is None:
        try:
            _FONT_CACHE = ImageFont.truetype("arial.ttf", 32)
        except:
            try:
                _FONT_CACHE = ImageFont.truetype("arialbd.ttf", 32)
            except:
                _FONT_CACHE = ImageFont.load_default()
    return _FONT_CACHE

def create_zero_win_effect():
    img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_cached_font()
    
    text = "x 0 BET"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (WIDTH - text_width) // 2
    y = (75 - text_height) // 2
    
    draw.text((x+1, y+1), text, fill=(0, 0, 0, 128), font=font)
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    filepath = os.path.join(EFFECTS_FOLDER, "win_0.png")
    img.save(filepath)

def preload_all_effects():
    zero_effect_path = os.path.join(EFFECTS_FOLDER, "win_0.png")
    if not os.path.exists(zero_effect_path):
        create_zero_win_effect()
    
    for i in range(3):
        load_line_effect('horizontal', i)
        load_line_effect('vertical', i)
    
    load_line_effect('diagonal', 'main')
    load_line_effect('diagonal', 'anti')
    
    for row in range(3):
        for col in range(3):
            load_cross_effect(row, col)
    
    for win_amount in AVAILABLE_WINS[:10]:
        load_win_text_effect(win_amount)

def load_line_effect(line_type, position):
    cache_key = f"{line_type}_{position}"
    
    if cache_key in _effects_cache:
        return _effects_cache[cache_key]
    
    if line_type == 'horizontal':
        filename = f"horizontal_{position}.png"
    elif line_type == 'vertical':
        filename = f"vertical_{position}.png"
    elif line_type == 'diagonal':
        filename = f"diagonal_{position}.png"
    else:
        return None
    
    filepath = os.path.join(EFFECTS_FOLDER, filename)
    if os.path.exists(filepath):
        effect_img = Image.open(filepath).convert('RGBA')
        _effects_cache[cache_key] = effect_img
        return effect_img
    
    return None

def load_cross_effect(row, col):
    cache_key = f"cross_{row}_{col}"
    
    if cache_key in _effects_cache:
        return _effects_cache[cache_key]
    
    filename = f"cross_{row}_{col}.png"
    filepath = os.path.join(EFFECTS_FOLDER, filename)
    if os.path.exists(filepath):
        effect_img = Image.open(filepath).convert('RGBA')
        _effects_cache[cache_key] = effect_img
        return effect_img
    
    return None

def load_win_text_effect(win_amount):
    cache_key = f"win_{win_amount}"
    
    if cache_key in _effects_cache:
        return _effects_cache[cache_key]
    
    if win_amount == int(win_amount):
        filename = f"win_{int(win_amount)}.png"
    else:
        filename = f"win_{win_amount:.1f}.png"
    
    filepath = os.path.join(EFFECTS_FOLDER, filename)
    if os.path.exists(filepath):
        effect_img = Image.open(filepath).convert('RGBA')
        _effects_cache[cache_key] = effect_img
        return effect_img
    
    return None

def find_closest_win(win_amount):
    if win_amount in AVAILABLE_WINS:
        return win_amount
    
    closest = min(AVAILABLE_WINS, key=lambda x: abs(x - win_amount))
    return closest

def load_column_frames_optimized(file_path, trim_frames=0):
    try:
        with Image.open(file_path) as gif:
            frames = []
            for frame_idx in range(gif.n_frames):
                gif.seek(frame_idx)
                frame = gif.copy()
                if frame.mode != 'RGB':
                    frame = frame.convert('RGB')
                frames.append(frame)
            
            if trim_frames > 0 and trim_frames < len(frames):
                return frames[trim_frames:]
            return frames
            
    except Exception as e:
        return None

def combine_frames_optimized(column_frames):
    target_length = max(len(frames) for frames in column_frames)
    combined_frames = []
    
    positions = [(i * COLUMN_WIDTH, 0) for i in range(3)]
    
    for frame_idx in range(target_length):
        frame = Image.new('RGB', (WIDTH, HEIGHT), (20, 20, 30))
        
        for col_idx in range(3):
            frames = column_frames[col_idx]
            if frame_idx < len(frames):
                frame.paste(frames[frame_idx], positions[col_idx])
            else:
                frame.paste(frames[-1], positions[col_idx])
        
        combined_frames.append(frame)
    
    return combined_frames

def check_line_win(symbols):
    return (symbols[0] == symbols[1] == symbols[2]) or \
           (symbols[0] == symbols[1] and symbols[2] == 0) or \
           (symbols[0] == symbols[2] and symbols[1] == 0) or \
           (symbols[1] == symbols[2] and symbols[0] == 0) or \
           (symbols[0] == 0 and symbols[1] == symbols[2]) or \
           (symbols[1] == 0 and symbols[0] == symbols[2]) or \
           (symbols[2] == 0 and symbols[0] == symbols[1]) or \
           (sum(1 for s in symbols if s == 0) >= 2)

def calculate_winning_data_optimized(symbols_matrix):
    winning_lines = {'horizontal': [], 'vertical': [], 'diagonal': []}
    bonus_count = 0
    wild_count = 0
    
    for i in range(3):
        symbols_h = [symbols_matrix[i][0], symbols_matrix[i][1], symbols_matrix[i][2]]
        if check_line_win(symbols_h):
            winning_lines['horizontal'].append(i)
        
        symbols_v = [symbols_matrix[0][i], symbols_matrix[1][i], symbols_matrix[2][i]]
        if check_line_win(symbols_v):
            winning_lines['vertical'].append(i)
        
        for j in range(3):
            if symbols_matrix[i][j] == 1:
                bonus_count += 1
            elif symbols_matrix[i][j] == 0:
                wild_count += 1
    
    symbols_d1 = [symbols_matrix[0][0], symbols_matrix[1][1], symbols_matrix[2][2]]
    symbols_d2 = [symbols_matrix[0][2], symbols_matrix[1][1], symbols_matrix[2][0]]
    
    if check_line_win(symbols_d1):
        winning_lines['diagonal'].append('main')
    if check_line_win(symbols_d2):
        winning_lines['diagonal'].append('anti')
    
    winning_lines = {k: v for k, v in winning_lines.items() if v}
    
    base_win = sum(len(v) for v in winning_lines.values())
    if base_win >= 1:
        base_win += 1
    
    total_win = base_win + (bonus_count * 0.4)
    
    return {
        'winning_lines': winning_lines,
        'bonus_count': bonus_count,
        'wild_count': wild_count,
        'total_win': total_win,
        'symbols_matrix': symbols_matrix,
        'has_win': bool(winning_lines) or bonus_count > 0
    }

def draw_effects_batch(image, winning_lines, symbols_matrix, current_line_index, current_bonus_index):
    if not winning_lines and current_bonus_index < 0:
        return image
    
    base_image = image.convert('RGBA')
    effects_to_apply = []
    
    all_lines = []
    for line_type, positions in winning_lines.items():
        for position in positions:
            all_lines.append((line_type, position))
    
    lines_to_draw = all_lines[:current_line_index + 1]
    for line_type, position in lines_to_draw:
        effect = load_line_effect(line_type, position)
        if effect:
            effects_to_apply.append(effect)
    
    if current_bonus_index >= 0:
        bonus_positions = []
        for row in range(3):
            for col in range(3):
                if symbols_matrix[row][col] == 1:
                    bonus_positions.append((row, col))
        
        bonuses_to_draw = bonus_positions[:current_bonus_index + 1]
        for row, col in bonuses_to_draw:
            effect = load_cross_effect(row, col)
            if effect:
                effects_to_apply.append(effect)
    
    result_image = base_image
    for effect in effects_to_apply:
        result_image = Image.alpha_composite(result_image, effect)
    
    return result_image.convert('RGB')

def draw_win_amount_ultra_fast(image, win_amount):
    if win_amount == 0:
        return draw_win_amount_optimized(image, 0, 255)
    
    closest_win = find_closest_win(win_amount)
    effect_img = load_win_text_effect(closest_win)
    
    if effect_img:
        result = Image.alpha_composite(image.convert('RGBA'), effect_img)
        return result.convert('RGB')
    
    return draw_win_amount_optimized(image, win_amount, 255)

def draw_win_amount_optimized(image, win_amount, alpha=255):
    if alpha == 0:
        return image
    
    font = get_cached_font()
    
    text = f"x {int(win_amount)} BET" if win_amount == int(win_amount) else f"x {win_amount:.1f} BET"
    
    text_layer = Image.new('RGBA', image.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    
    bbox = text_draw.textbbox((0, 0), text, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (WIDTH - text_width) // 2
    y = (75 - text_height) // 2
    
    text_color = (255, 255, 255, alpha)
    text_draw.text((x+1, y+1), text, fill=(0, 0, 0, alpha//2), font=font)
    text_draw.text((x, y), text, fill=text_color, font=font)
    
    result = Image.alpha_composite(image.convert('RGBA'), text_layer)
    return result.convert('RGB')

def generate_effects_animation_optimized(base_frame, winning_data, total_animation_frames):
    frames = []
    winning_lines = winning_data['winning_lines']
    bonus_count = winning_data['bonus_count']
    total_win = winning_data['total_win']
    symbols_matrix = winning_data['symbols_matrix']
    
    line_frames = 10
    bonus_frames = 8
    display_frames = 25
    
    total_lines = sum(len(positions) for positions in winning_lines.values())
    
    for freeze_frame in range(total_animation_frames):
        current_bonus_index = -1
        current_line_index = -1
        current_win = 0
        
        if bonus_count > 0:
            if freeze_frame < bonus_frames:
                current_bonus_index = min(bonus_count - 1, freeze_frame // max(1, bonus_frames // bonus_count))
                current_win = (current_bonus_index + 1) * 0.4
            elif freeze_frame < bonus_frames + (total_lines * line_frames):
                current_line_index = (freeze_frame - bonus_frames) // line_frames
                current_bonus_index = bonus_count - 1
                base_win = current_line_index + 1
                if base_win >= 1:
                    base_win += 1
                current_win = base_win + (bonus_count * 0.4)
            else:
                current_line_index = total_lines - 1
                current_bonus_index = bonus_count - 1
                current_win = total_win
        else:
            if freeze_frame < total_lines * line_frames:
                current_line_index = freeze_frame // line_frames
                base_win = current_line_index + 1
                if base_win >= 1:
                    base_win += 1
                current_win = base_win
            else:
                current_line_index = total_lines - 1
                current_win = total_win
        
        frame_with_effects = draw_effects_batch(
            base_frame, winning_lines, symbols_matrix, 
            current_line_index, current_bonus_index
        )
        
        frame_with_effects = draw_win_amount_ultra_fast(frame_with_effects, current_win)
        frames.append(frame_with_effects)
    
    return frames

def save_ultra_optimized(frames, output_file, duration):
    if not frames:
        return
    
    rgb_frames = []
    for frame in frames:
        if frame.mode != 'RGB':
            rgb_frames.append(frame.convert('RGB'))
        else:
            rgb_frames.append(frame)
    
    rgb_frames[0].save(
        output_file,
        save_all=True,
        append_images=rgb_frames[1:],
        duration=duration,
        loop=0,
        format="WEBP"
    )

def verify_effects_exist():
    required_files = [
        'horizontal_0.png', 'horizontal_1.png', 'horizontal_2.png',
        'vertical_0.png', 'vertical_1.png', 'vertical_2.png',
        'diagonal_main.png', 'diagonal_anti.png',
        'win_0.png'
    ]
    
    for filename in required_files:
        if not os.path.exists(os.path.join(EFFECTS_FOLDER, filename)):
            return False
    return True

def generate_ultra_optimized_animation(output_file="slots_ultra_fast.webp",
                                     combinations_folder="all_combinations",
                                     target_combinations=None,
                                     start_trims=[92, 46, 0],
                                     frame_duration=20):
    
    if not verify_effects_exist():
        return None
    
    preload_all_effects()
    
    if not os.path.exists(combinations_folder):
        return None
    
    if target_combinations is None:
        all_files = glob.glob(os.path.join(combinations_folder, "slots_*.webp"))
        if not all_files:
            return None
        
        selected_files = random.sample(all_files, 3)
        target_combinations = []
        for file_path in selected_files:
            filename = os.path.basename(file_path).replace('.webp', '')
            symbols = [int(x) for x in filename.split('_')[1:4]]
            target_combinations.append(symbols)
    
    column_frames = []
    loaded_combinations = []
    
    for i, combo in enumerate(target_combinations):
        filename = f"slots_{combo[0]}_{combo[1]}_{combo[2]}.webp"
        file_path = os.path.join(combinations_folder, filename)
        
        trim_frames = start_trims[i] if i < len(start_trims) else 0
        frames = load_column_frames_optimized(file_path, trim_frames)
        
        if frames:
            column_frames.append(frames)
            loaded_combinations.append(combo)
        else:
            return None
    
    if len(column_frames) != 3:
        return None
    
    combined_frames = combine_frames_optimized(column_frames)
    
    symbols_matrix = [
        [loaded_combinations[0][0], loaded_combinations[1][0], loaded_combinations[2][0]],
        [loaded_combinations[0][1], loaded_combinations[1][1], loaded_combinations[2][1]],
        [loaded_combinations[0][2], loaded_combinations[1][2], loaded_combinations[2][2]]
    ]
    
    winning_data = calculate_winning_data_optimized(symbols_matrix)
    
    total_lines = sum(len(positions) for positions in winning_data['winning_lines'].values())
    
    if winning_data['has_win']:
        bonus_frames = 8 if winning_data['bonus_count'] > 0 else 0
        total_animation_frames = (total_lines * 10) + bonus_frames + 25
    else:
        total_animation_frames = 15
    
    effect_frames = generate_effects_animation_optimized(
        combined_frames[-1], winning_data, total_animation_frames
    )
    combined_frames.extend(effect_frames)
    
    save_ultra_optimized(combined_frames, output_file, frame_duration)
    
    return {
        'output_file': output_file,
        'frame_count': len(combined_frames),
        'combinations': loaded_combinations,
        'total_win': winning_data['total_win'],
        'winning_lines': winning_data['winning_lines'],
        'bonus_count': winning_data['bonus_count'],
        'frame_duration': frame_duration
    }

if __name__ == "__main__":
    result = generate_ultra_optimized_animation(
        output_file="slots_ultra_fast_20ms.webp",
        combinations_folder=COMBINATIONS_PATH,
        target_combinations=[
            [3, 4, 5],
            [6, 7, 5],
            [4, 5, 5]
        ],
        start_trims=[92, 46, 0],
        frame_duration=20
    )