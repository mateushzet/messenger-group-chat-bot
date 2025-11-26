from PIL import Image, ImageDraw, ImageFont
import os

def generate_blackjack_elements():

    BASE_DIR = os.path.dirname(__file__)

    BLACKJACK_DIR = os.path.join(BASE_DIR, "games", "blackjack")

    ELEMENTS_FOLDER = os.path.join(BLACKJACK_DIR, "board_elements")

    COLORS = {
        'card_bg': (30, 30, 40),
        'card_border': (80, 80, 100),
        'card_red': (220, 80, 80),
        'card_black': (200, 200, 220),
        'card_white': (240, 240, 255),
        'table_bg': (20, 20, 30),
        'panel_bg': (40, 40, 50, 220),
        'panel_border': (70, 70, 90),
        'text_primary': (220, 220, 240),
        'text_secondary': (180, 180, 200),
        'button_bg': (60, 60, 80),
        'button_hover': (80, 80, 100),
        'chip_color': (200, 160, 60)
    }
    
    def create_rounded_rectangle(size, radius, color):
        width, height = size
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        draw.rectangle([radius, 0, width - radius, height], fill=color)
        draw.rectangle([0, radius, width, height - radius], fill=color)
        
        draw.pieslice([0, 0, radius * 2, radius * 2], 180, 270, fill=color)
        draw.pieslice([width - radius * 2, 0, width, radius * 2], 270, 360, fill=color)
        draw.pieslice([0, height - radius * 2, radius * 2, height], 90, 180, fill=color)
        draw.pieslice([width - radius * 2, height - radius * 2, width, height], 0, 90, fill=color)
        
        return image
    
    try:
        card_font_small = ImageFont.truetype("arial.ttf", 24)
    except:
        card_font_small = ImageFont.load_default()
    
    buttons = ['hit', 'stand', 'double', 'split', 'deal']
    button_width, button_height = 120, 40
    
    for button in buttons:
        btn_img = create_rounded_rectangle((button_width, button_height), 10, COLORS['button_bg'])
        draw = ImageDraw.Draw(btn_img)
        
        button_text = button.upper()
        bbox = draw.textbbox((0, 0), button_text, font=card_font_small)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = (button_width - text_width) // 2
        text_y = (button_height - text_height) // 2
        
        draw.text((text_x, text_y), button_text, fill=COLORS['text_primary'], font=card_font_small)
        
        draw.rectangle([2, 2, button_width - 2, button_height - 2], outline=COLORS['panel_border'], width=1)
        
        btn_img.save(os.path.join(ELEMENTS_FOLDER, f"button_{button}.png"), "PNG")
    
if __name__ == "__main__":
    generate_blackjack_elements()