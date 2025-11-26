from PIL import Image, ImageDraw, ImageFont
import os

BASE_DIR = os.path.dirname(__file__)
SLOTS_DIR = os.path.join(BASE_DIR, "games", "slots")

EFFECTS_FOLDER = os.path.join(SLOTS_DIR, "slots_effects")

def get_cached_font():
    try:
        return ImageFont.truetype("arial.ttf", 32)
    except:
        try:
            return ImageFont.truetype("arialbd.ttf", 32)
        except:
            return ImageFont.load_default()

def generate_win_text_effects():
    win_values = [0.0, 0.4, 0.8, 2.0, 2.2, 2.4, 2.8, 3.0, 3.2, 3.6, 4.0, 4.4, 4.8, 5.0, 5.2, 5.6, 6.0, 6.4, 6.8, 7.0, 7.4, 7.8, 8.0, 9.0]
    
    font = get_cached_font()
    effects_created = 0
    
    for win_amount in win_values:
        if win_amount == int(win_amount):
            text = f"x{int(win_amount)} BET"
        else:
            text = f"x{win_amount:.1f} BET"
        
        text_layer = Image.new('RGBA', (225, 225), (0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_layer)
        
        bbox = text_draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (225 - text_width) // 2
        y = (75 - text_height) // 2
        
        shadow_color = (0, 0, 0, 160)
        for offset_x in [-1, 0, 1]:
            for offset_y in [-1, 0, 1]:
                if offset_x == 0 and offset_y == 0:
                    continue
                text_draw.text((x + offset_x, y + offset_y), text, fill=shadow_color, font=font)
        
        text_draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        
        if win_amount == int(win_amount):
            filename = f"win_{int(win_amount)}.png"
        else:
            filename = f"win_{win_amount:.1f}.png"
        
        filepath = os.path.join(EFFECTS_FOLDER, filename)
        text_layer.save(filepath, optimize=True)
        effects_created += 1
    
    return effects_created

def verify_win_text_effects():
    required_files = [
        'win_0.4.png', 'win_0.8.png', 'win_1.2.png', 'win_1.6.png', 'win_2.0.png',
        'win_2.4.png', 'win_2.8.png', 'win_3.2.png', 'win_3.6.png', 'win_4.0.png'
    ]
    
    for filename in required_files:
        if not os.path.exists(os.path.join(EFFECTS_FOLDER, filename)):
            return False
    return True

if __name__ == "__main__":
    count = generate_win_text_effects()
    
    if verify_win_text_effects():
        print(f"Generated {count} win text effects")
    else:
        print("Error generating effects")