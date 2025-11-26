from PIL import Image, ImageDraw, ImageFont
import os

def generate_and_save_board_elements():
    BASE_DIR = os.path.dirname(__file__)
    MINES_DIR = os.path.join(BASE_DIR, "games", "mines")

    ELEMENTS_FOLDER = os.path.join(MINES_DIR, "board_elements")
    ASSETS_FOLDER = os.path.join(MINES_DIR, "assets")
    
    CELL_SIZE = 70
    BORDER = 3
    
    COLORS = {
        'multiplier_active1': (76, 175, 80),
        'multiplier_active2': (56, 142, 60),
        'multiplier_inactive1': (50, 50, 60),
        'multiplier_inactive2': (70, 70, 80),
        'multiplier_border': (100, 100, 120),
        'border': (60, 60, 80),
        'grid_bg': (35, 35, 45),
        'hidden1': (60, 70, 90),
        'hidden2': (40, 50, 70),
        'revealed_safe1': (40, 80, 60),
        'revealed_safe2': (30, 60, 45),
        'revealed_mine1': (80, 40, 50),
        'revealed_mine2': (60, 30, 40),
        'exploded_mine1': (120, 40, 40),
        'exploded_mine2': (90, 20, 20),
        'highlight': (80, 90, 110),
        'shadow': (30, 40, 50),
        'counter_bg': (40, 40, 50, 220),
        'counter_border': (80, 80, 100),
        'number_text': (200, 200, 220),
        'number_border': (80, 80, 100)
    }
    
    cached_images = {}
    try:
        bomb_img = Image.open(os.path.join(ASSETS_FOLDER, "bomb.png")).convert('RGBA')
        cached_images['bomb'] = bomb_img.resize((CELL_SIZE - 15, CELL_SIZE - 15))
    except:
        cached_images['bomb'] = None
    
    try:
        explosion_img = Image.open(os.path.join(ASSETS_FOLDER, "explosion.png")).convert('RGBA')
        cached_images['explosion'] = explosion_img.resize((CELL_SIZE - 10, CELL_SIZE - 10))
    except:
        cached_images['explosion'] = None
    
    try:
        diamond_img = Image.open(os.path.join(ASSETS_FOLDER, "diamond.png")).convert('RGBA')
        cached_images['diamond'] = diamond_img.resize((CELL_SIZE - 15, CELL_SIZE - 15))
    except:
        cached_images['diamond'] = None
    
    def draw_gradient_rectangle(draw, x1, y1, x2, y2, color1, color2, direction='horizontal'):
        if direction == 'horizontal':
            for x in range(int(x1), int(x2)):
                ratio = (x - x1) / (x2 - x1)
                r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                draw.line([(x, y1), (x, y2)], fill=(r, g, b))
        else:
            for y in range(int(y1), int(y2)):
                ratio = (y - y1) / (y2 - y1)
                r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                draw.line([(x1, y), (x2, y)], fill=(r, g, b))
    
    cell_types = [
        ('hidden', COLORS['hidden1'], COLORS['hidden2']),
        ('safe', COLORS['revealed_safe1'], COLORS['revealed_safe2']),
        ('mine', COLORS['revealed_mine1'], COLORS['revealed_mine2']),
        ('exploded', COLORS['exploded_mine1'], COLORS['exploded_mine2'])
    ]
    
    for cell_type, color1, color2 in cell_types:
        img = Image.new('RGBA', (CELL_SIZE, CELL_SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        draw_gradient_rectangle(draw, BORDER, BORDER, 
                               CELL_SIZE - BORDER, CELL_SIZE - BORDER,
                               color1, color2, 'vertical')
        
        if cell_type == 'hidden':
            draw.line([BORDER, BORDER, CELL_SIZE - BORDER - 1, BORDER], 
                     fill=COLORS['highlight'], width=2)
            draw.line([BORDER, BORDER, BORDER, CELL_SIZE - BORDER - 1], 
                     fill=COLORS['highlight'], width=2)
            
            draw.line([BORDER, CELL_SIZE - BORDER - 1, CELL_SIZE - BORDER, CELL_SIZE - BORDER - 1], 
                     fill=COLORS['shadow'], width=2)
            draw.line([CELL_SIZE - BORDER - 1, BORDER, CELL_SIZE - BORDER - 1, CELL_SIZE - BORDER], 
                     fill=COLORS['shadow'], width=2)
        
        if cell_type == 'safe' and cached_images['diamond']:
            diamond_img = cached_images['diamond']
            x = (CELL_SIZE - diamond_img.width) // 2
            y = (CELL_SIZE - diamond_img.height) // 2
            img.paste(diamond_img, (x, y), diamond_img)
        elif cell_type == 'mine' and cached_images['bomb']:
            bomb_img = cached_images['bomb']
            x = (CELL_SIZE - bomb_img.width) // 2
            y = (CELL_SIZE - bomb_img.height) // 2
            img.paste(bomb_img, (x, y), bomb_img)
        elif cell_type == 'exploded' and cached_images['explosion']:
            explosion_img = cached_images['explosion']
            x = (CELL_SIZE - explosion_img.width) // 2
            y = (CELL_SIZE - explosion_img.height) // 2
            img.paste(explosion_img, (x, y), explosion_img)
        
        img.save(os.path.join(ELEMENTS_FOLDER, f"cell_{cell_type}.png"), "PNG")
    
    try:
        number_font = ImageFont.truetype("arial.ttf", 10)
    except:
        number_font = ImageFont.load_default()
    
    hidden_cell_base = Image.open(os.path.join(ELEMENTS_FOLDER, "cell_hidden.png"))
    
    for number in range(1, 26):
        hidden_cell = hidden_cell_base.copy()
        draw = ImageDraw.Draw(hidden_cell)
        
        number_bg_size = 16
        number_bg_x = 2
        number_bg_y = 2
        
        draw.rectangle([
            number_bg_x, number_bg_y,
            number_bg_x + number_bg_size, number_bg_y + number_bg_size
        ], fill=COLORS['counter_bg'], outline=COLORS['number_border'], width=1)
        
        number_text = str(number)
        bbox = draw.textbbox((0, 0), number_text, font=number_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        text_x = number_bg_x + (number_bg_size - text_width) // 2
        text_y = number_bg_y + (number_bg_size - text_height) // 2
        
        draw.text((text_x, text_y), number_text, fill=COLORS['number_text'], font=number_font)
        
        hidden_cell.save(os.path.join(ELEMENTS_FOLDER, f"cell_hidden_{number}.png"), "PNG")
    
    if cached_images['bomb']:
        mine_icon = cached_images['bomb'].resize((20, 20))
        mine_icon.save(os.path.join(ELEMENTS_FOLDER, "mine_icon.png"), "PNG")

if __name__ == "__main__":
    generate_and_save_board_elements()