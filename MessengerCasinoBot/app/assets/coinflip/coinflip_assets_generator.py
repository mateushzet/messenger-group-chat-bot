from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import math

def generate_static_assets(width=600, height=300):
    assets_dir = "static_assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    gradient_bg = Image.new('RGB', (width, height), (8, 5, 12))
    gradient_draw = ImageDraw.Draw(gradient_bg)
    draw_gradient_background(gradient_draw, width, height)
    draw_central_platform(gradient_draw, width, height)
    gradient_bg.save(f"{assets_dir}/gradient_background.webp", "WEBP", quality=95)
    
    red_bg = Image.new('RGB', (width, height), (8, 5, 12))
    red_draw = ImageDraw.Draw(red_bg)
    draw_red_winner_background(red_draw, width, height)
    draw_central_platform(red_draw, width, height)
    red_bg.save(f"{assets_dir}/winner_background_red.webp", "WEBP", quality=95)
    
    yellow_bg = Image.new('RGB', (width, height), (8, 5, 12))
    yellow_draw = ImageDraw.Draw(yellow_bg)
    draw_yellow_winner_background(yellow_draw, width, height)
    draw_central_platform(yellow_draw, width, height)
    yellow_bg.save(f"{assets_dir}/winner_background_yellow.webp", "WEBP", quality=95)

def draw_gradient_background(draw, width, height):
    ruby_base = (120, 10, 40)
    gold_base = (180, 150, 20)
    
    step = 2
    
    for x in range(0, width, step):
        for y in range(0, height, step):
            dist_from_top_left = math.sqrt((x)**2 + (y - height*0.3)**2)
            dist_from_top_right = math.sqrt((width - x)**2 + (y - height*0.3)**2)
            
            max_dist_tl = math.sqrt(width**2 + (height*0.7)**2)
            max_dist_tr = max_dist_tl
            
            ruby_intensity = max(0, 0.8 - (dist_from_top_left / max_dist_tl) * 1.5)
            gold_intensity = max(0, 0.8 - (dist_from_top_right / max_dist_tr) * 1.5)
            
            base_color = (8, 5, 12)
            
            final_red = int(base_color[0] + (ruby_base[0] * ruby_intensity) + (gold_base[0] * gold_intensity * 0.4))
            final_green = int(base_color[1] + (ruby_base[1] * ruby_intensity * 0.2) + (gold_base[1] * gold_intensity * 0.6))
            final_blue = int(base_color[2] + (ruby_base[2] * ruby_intensity * 0.3) + (gold_base[2] * gold_intensity * 0.2))
            
            final_red = min(70, max(0, final_red))
            final_green = min(50, max(0, final_green))
            final_blue = min(40, max(0, final_blue))
            
            draw.rectangle([x, y, x+step, y+step], fill=(final_red, final_green, final_blue))

def draw_red_winner_background(draw, width, height):
    red_light = (160, 20, 50)
    red_dark = (80, 5, 20)
    base_color = (8, 5, 12)
    
    step = 2
    center_x = width / 2
    
    for x in range(0, width, step):
        for y in range(0, height, step):
            dist_from_center = abs(x - center_x)
            max_dist = center_x
            
            intensity = max(0, 1.0 - (dist_from_center / max_dist) * 0.8)
            
            if intensity > 0.05:
                color_red = int(red_dark[0] + (red_light[0] - red_dark[0]) * intensity)
                color_green = int(red_dark[1] + (red_light[1] - red_dark[1]) * intensity)
                color_blue = int(red_dark[2] + (red_light[2] - red_dark[2]) * intensity)
                
                mix_factor = min(1.0, intensity * 1.2)
                final_red = int(base_color[0] * (1 - mix_factor) + color_red * mix_factor)
                final_green = int(base_color[1] * (1 - mix_factor) + color_green * mix_factor)
                final_blue = int(base_color[2] * (1 - mix_factor) + color_blue * mix_factor)
                
                draw.rectangle([x, y, x+step, y+step], fill=(final_red, final_green, final_blue))
            else:
                faint_red = int(base_color[0] * 0.7 + red_dark[0] * 0.3)
                faint_green = int(base_color[1] * 0.7 + red_dark[1] * 0.3)
                faint_blue = int(base_color[2] * 0.7 + red_dark[2] * 0.3)
                draw.rectangle([x, y, x+step, y+step], fill=(faint_red, faint_green, faint_blue))

def draw_yellow_winner_background(draw, width, height):
    yellow_light = (200, 160, 30)
    yellow_dark = (100, 80, 10)
    base_color = (8, 5, 12)
    
    step = 2
    center_x = width / 2
    
    for x in range(0, width, step):
        for y in range(0, height, step):
            dist_from_center = abs(x - center_x)
            max_dist = center_x
            
            intensity = max(0, 1.0 - (dist_from_center / max_dist) * 0.8)
            
            if intensity > 0.05:
                color_red = int(yellow_dark[0] + (yellow_light[0] - yellow_dark[0]) * intensity)
                color_green = int(yellow_dark[1] + (yellow_light[1] - yellow_dark[1]) * intensity)
                color_blue = int(yellow_dark[2] + (yellow_light[2] - yellow_dark[2]) * intensity)
                
                mix_factor = min(1.0, intensity * 1.2)
                final_red = int(base_color[0] * (1 - mix_factor) + color_red * mix_factor)
                final_green = int(base_color[1] * (1 - mix_factor) + color_green * mix_factor)
                final_blue = int(base_color[2] * (1 - mix_factor) + color_blue * mix_factor)
                
                draw.rectangle([x, y, x+step, y+step], fill=(final_red, final_green, final_blue))
            else:
                faint_red = int(base_color[0] * 0.7 + yellow_dark[0] * 0.3)
                faint_green = int(base_color[1] * 0.7 + yellow_dark[1] * 0.3)
                faint_blue = int(base_color[2] * 0.7 + yellow_dark[2] * 0.3)
                draw.rectangle([x, y, x+step, y+step], fill=(faint_red, faint_green, faint_blue))

def draw_central_platform(draw, width, height):
    center_x = width * 0.5
    center_y = height * 0.5
    coin_size = 65
    platform_size = coin_size + 15
    
    steps = 20
    for i in range(steps, 0, -1):
        current_size = platform_size * (i / steps)
        alpha = int(150 * (1 - i/steps))
        
        color = (
            max(0, 20 + int(alpha * 0.2)),
            max(0, 15 + int(alpha * 0.15)), 
            max(0, 25 + int(alpha * 0.25))
        )
        draw.ellipse([
            center_x - current_size, center_y - current_size,
            center_x + current_size, center_y + current_size
        ], fill=color)
    
    edge_width = 3
    for angle in range(90, 270):
        rad = math.radians(angle)
        x1 = center_x + math.cos(rad) * platform_size
        y1 = center_y + math.sin(rad) * platform_size
        x2 = center_x + math.cos(rad) * (platform_size - edge_width)
        y2 = center_y + math.sin(rad) * (platform_size - edge_width)
        draw.line([x1, y1, x2, y2], fill=(180, 25, 60), width=edge_width)
    
    for angle in list(range(0, 90)) + list(range(270, 360)):
        rad = math.radians(angle)
        x1 = center_x + math.cos(rad) * platform_size
        y1 = center_y + math.sin(rad) * platform_size
        x2 = center_x + math.cos(rad) * (platform_size - edge_width)
        y2 = center_y + math.sin(rad) * (platform_size - edge_width)
        draw.line([x1, y1, x2, y2], fill=(200, 170, 40), width=edge_width)
    
    inner_ring = platform_size - 10
    ring_width = 2
    draw.ellipse([
        center_x - inner_ring, center_y - inner_ring,
        center_x + inner_ring, center_y + inner_ring
    ], outline=(80, 65, 95), width=ring_width)
    
    ray_count = 12
    ray_width = 2
    for angle in range(0, 360, int(360/ray_count)):
        rad = math.radians(angle)
        start_x = center_x + math.cos(rad) * (inner_ring - 3)
        start_y = center_y + math.sin(rad) * (inner_ring - 3)
        end_x = center_x + math.cos(rad) * (platform_size - 5)
        end_y = center_y + math.sin(rad) * (platform_size - 5)
        draw.line([start_x, start_y, end_x, end_y], fill=(90, 75, 105), width=ray_width)
    
    center_steps = 10
    for i in range(center_steps, 0, -1):
        current_coin_size = coin_size * (i / center_steps)
        brightness = 20 + int(30 * (1 - i/center_steps))
        color = (
            max(0, brightness + 5),
            max(0, brightness - 5), 
            max(0, brightness + 10)
        )
        draw.ellipse([
            center_x - current_coin_size, center_y - current_coin_size,
            center_x + current_coin_size, center_y + current_coin_size
        ], fill=color)
    
    inner_circle_size = coin_size - 5
    draw.ellipse([
        center_x - inner_circle_size, center_y - inner_circle_size,
        center_x + inner_circle_size, center_y + inner_circle_size
    ], outline=(60, 50, 70), width=1)

def generate_additional_assets():
    assets_dir = "static_assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    balance_icon = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    balance_draw = ImageDraw.Draw(balance_icon)
    balance_draw.ellipse([0, 0, 15, 15], fill=(50, 200, 100, 255))
    balance_draw.rectangle([4, 7, 12, 9], fill=(255, 255, 255, 255))
    balance_draw.rectangle([7, 4, 9, 12], fill=(255, 255, 255, 255))
    balance_icon.save(f"{assets_dir}/balance_icon.png", "PNG")
    
    bet_icon = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    bet_draw = ImageDraw.Draw(bet_icon)
    bet_draw.rectangle([2, 2, 14, 14], fill=(255, 200, 50, 255))
    bet_draw.text((5, 3), "$", fill=(0, 0, 0, 255), font=ImageFont.load_default())
    bet_icon.save(f"{assets_dir}/bet_icon.png", "PNG")

if __name__ == "__main__":
    generate_static_assets(600, 300)
    generate_additional_assets()