from PIL import Image, ImageDraw
import os

EFFECTS_FOLDER = "slots_effects"
os.makedirs(EFFECTS_FOLDER, exist_ok=True)

def generate_and_save_line_effects():
    effects_created = 0
    
    for row in range(3):
        img = Image.new('RGBA', (225, 225), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        y = row * 75 + 75 // 2
        
        draw.line([(5, y-1), (220, y-1)], fill=(127, 25, 25), width=2)
        draw.line([(5, y+1), (220, y+1)], fill=(127, 25, 25), width=2)
        draw.line([(8, y), (217, y)], fill=(255, 50, 50), width=1)
        
        filename = f"horizontal_{row}.png"
        img.save(os.path.join(EFFECTS_FOLDER, filename), optimize=True)
        effects_created += 1
    
    for col in range(3):
        img = Image.new('RGBA', (225, 225), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        x = col * 75 + 75 // 2
        
        draw.line([(x-1, 5), (x-1, 220)], fill=(25, 127, 25), width=2)
        draw.line([(x+1, 5), (x+1, 220)], fill=(25, 127, 25), width=2)
        draw.line([(x, 8), (x, 217)], fill=(50, 255, 50), width=1)
        
        filename = f"vertical_{col}.png"
        img.save(os.path.join(EFFECTS_FOLDER, filename), optimize=True)
        effects_created += 1
    
    img = Image.new('RGBA', (225, 225), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.line([(7, 7), (218, 218)], fill=(25, 25, 127), width=2)
    draw.line([(8, 8), (217, 217)], fill=(50, 50, 255), width=1)
    img.save(os.path.join(EFFECTS_FOLDER, "diagonal_main.png"), optimize=True)
    effects_created += 1
    
    img = Image.new('RGBA', (225, 225), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.line([(218, 7), (7, 218)], fill=(25, 25, 127), width=2)
    draw.line([(217, 8), (8, 217)], fill=(50, 50, 255), width=1)
    img.save(os.path.join(EFFECTS_FOLDER, "diagonal_anti.png"), optimize=True)
    effects_created += 1
    
    return effects_created

def generate_and_save_cross_effects():
    effects_created = 0
    SYMBOL_SIZE = 75
    
    for row in range(3):
        for col in range(3):
            img = Image.new('RGBA', (225, 225), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            x = col * SYMBOL_SIZE
            y = row * SYMBOL_SIZE
            center_x = x + SYMBOL_SIZE // 2
            center_y = y + SYMBOL_SIZE // 2
            cross_size = 25
            
            neon_color = (255, 50, 255)
            glow_color = (127, 25, 127)
            
            draw.line([
                (center_x - cross_size-1, center_y - cross_size-1),
                (center_x + cross_size+1, center_y + cross_size+1)
            ], fill=glow_color, width=3)
            draw.line([
                (center_x - cross_size+1, center_y - cross_size+1),
                (center_x + cross_size-1, center_y + cross_size-1)
            ], fill=glow_color, width=3)
            draw.line([
                (center_x - cross_size, center_y - cross_size),
                (center_x + cross_size, center_y + cross_size)
            ], fill=neon_color, width=1)
            
            draw.line([
                (center_x + cross_size+1, center_y - cross_size-1),
                (center_x - cross_size-1, center_y + cross_size+1)
            ], fill=glow_color, width=3)
            draw.line([
                (center_x + cross_size-1, center_y - cross_size+1),
                (center_x - cross_size+1, center_y + cross_size-1)
            ], fill=glow_color, width=3)
            draw.line([
                (center_x + cross_size, center_y - cross_size),
                (center_x - cross_size, center_y + cross_size)
            ], fill=neon_color, width=1)
            
            filename = f"cross_{row}_{col}.png"
            img.save(os.path.join(EFFECTS_FOLDER, filename), optimize=True)
            effects_created += 1
    
    return effects_created

def verify_effects():
    expected_files = []
    
    for i in range(3):
        expected_files.append(f"horizontal_{i}.png")
    
    for i in range(3):
        expected_files.append(f"vertical_{i}.png")
    
    expected_files.extend(["diagonal_main.png", "diagonal_anti.png"])
    
    for row in range(3):
        for col in range(3):
            expected_files.append(f"cross_{row}_{col}.png")
    
    missing_files = []
    for filename in expected_files:
        if not os.path.exists(os.path.join(EFFECTS_FOLDER, filename)):
            missing_files.append(filename)
    
    if missing_files:
        return False
    else:
        return True

def load_line_effect(line_type, position):
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
        return Image.open(filepath).convert('RGBA')
    return None

def load_cross_effect(row, col):
    filename = f"cross_{row}_{col}.png"
    filepath = os.path.join(EFFECTS_FOLDER, filename)
    if os.path.exists(filepath):
        return Image.open(filepath).convert('RGBA')
    return None

def draw_winning_lines_fast(image, winning_lines, current_line_index=0):
    all_lines = []
    for line_type, positions in winning_lines.items():
        for position in positions:
            all_lines.append((line_type, position))
    
    lines_to_draw = all_lines[:current_line_index + 1]
    
    result_image = image.convert('RGBA')
    
    for line_type, position in lines_to_draw:
        effect_img = load_line_effect(line_type, position)
        if effect_img:
            result_image = Image.alpha_composite(result_image, effect_img)
    
    return result_image.convert('RGB')

def draw_bonus_crosses_fast(image, symbols_matrix, current_bonus_index=0):
    bonus_positions = []
    for row in range(3):
        for col in range(3):
            if symbols_matrix[row][col] == 1:
                bonus_positions.append((row, col))
    
    bonuses_to_draw = bonus_positions[:current_bonus_index + 1]
    
    result_image = image.convert('RGBA')
    
    for row, col in bonuses_to_draw:
        effect_img = load_cross_effect(row, col)
        if effect_img:
            result_image = Image.alpha_composite(result_image, effect_img)
    
    return result_image.convert('RGB')

if __name__ == "__main__":
    line_count = generate_and_save_line_effects()
    cross_count = generate_and_save_cross_effects()
    
    success = verify_effects()
    
    if success:
        test_line = load_line_effect('horizontal', 0)
        test_cross = load_cross_effect(1, 1)