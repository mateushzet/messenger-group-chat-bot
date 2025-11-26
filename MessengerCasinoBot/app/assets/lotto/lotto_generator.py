from PIL import Image, ImageDraw, ImageFont
import random
import os
import glob

BASE_DIR = os.path.dirname(__file__)
LOTTO_DIR = os.path.join(BASE_DIR, "games", "lotto")

ASSETS_FOLDER = os.path.join(LOTTO_DIR, "balls")
OUTPUT_BASE_FOLDER = os.path.join(LOTTO_DIR, "generated_animations")
OUTPUT_FOLDER = LOTTO_DIR

def create_animated_lotto_ticket(player_numbers, drawn_numbers, output_path, assets_folder):
    available_balls = {}
    for ball_path in glob.glob(os.path.join(assets_folder, "[0-9]*_[0-4].*")):
        filename = os.path.basename(ball_path)
        name_without_ext = os.path.splitext(filename)[0]
        available_balls[name_without_ext] = ball_path
    
    BOX_SIZE = 32
    SPACING = 5
    MARGIN = 10
    BALL_SIZE = 40
    
    numbers_per_row = 10
    grid_width = 10 * (BOX_SIZE + SPACING) - SPACING + 2 * MARGIN
    grid_height = 5 * (BOX_SIZE + SPACING) - SPACING + 2 * MARGIN
    W, H = grid_width, grid_height
    
    BACKGROUND_COLOR = (240, 248, 255)
    BORDER_COLOR = (173, 216, 230)
    TEXT_COLOR = (70, 130, 180)
    SELECTED_BG_COLOR = (255, 228, 225)
    SELECTED_BORDER_COLOR = (219, 112, 147)
    MULTIPLIER_COLOR = (70, 130, 180)
    
    frames = []
    durations = []
    
    FRAME_DURATION = 50
    
    ball_positions = []
    for number in drawn_numbers:
        row = (number - 1) // numbers_per_row
        col = (number - 1) % numbers_per_row
        target_x = MARGIN + col * (BOX_SIZE + SPACING) + (BOX_SIZE - BALL_SIZE) // 2
        target_y = MARGIN + row * (BOX_SIZE + SPACING) + (BOX_SIZE - BALL_SIZE) // 2
        ball_positions.append((target_x, target_y))
    
    def create_base_frame(current_hits=0):
        base_img = Image.new('RGB', (W, H), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(base_img)
        
        border_width = 4
        draw.rectangle([0, 0, W-1, H-1], outline=BORDER_COLOR, width=border_width)
        
        try:
            number_font = ImageFont.truetype("arial.ttf", 10)
            multiplier_font = ImageFont.truetype("arial.ttf", 16)
        except:
            number_font = ImageFont.load_default()
            multiplier_font = ImageFont.load_default()
        
        start_y = MARGIN
        
        for number in range(1, 51):
            row = (number - 1) // numbers_per_row
            col = (number - 1) % numbers_per_row
            
            x = MARGIN + col * (BOX_SIZE + SPACING)
            y = start_y + row * (BOX_SIZE + SPACING)
            
            is_selected = number in player_numbers
            
            if number == 50:
                field_bg_color = BACKGROUND_COLOR
                field_border_color = BORDER_COLOR
                border_width_field = 1
                
                draw.rectangle([x, y, x + BOX_SIZE, y + BOX_SIZE], 
                              fill=field_bg_color, outline=field_border_color, width=border_width_field)
                
                multiplier_text = f"x{current_hits}"
                multiplier_bbox = draw.textbbox((0, 0), multiplier_text, font=multiplier_font)
                multiplier_tw = multiplier_bbox[2] - multiplier_bbox[0]
                multiplier_th = multiplier_bbox[3] - multiplier_bbox[1]
                
                multiplier_x = x + (BOX_SIZE - multiplier_tw) // 2
                multiplier_y = y + (BOX_SIZE - multiplier_th) // 2
                
                draw.text((multiplier_x, multiplier_y), multiplier_text, fill=MULTIPLIER_COLOR, font=multiplier_font)
                
            else:
                if is_selected:
                    field_bg_color = SELECTED_BG_COLOR
                    field_border_color = SELECTED_BORDER_COLOR
                    border_width_field = 1
                else:
                    field_bg_color = (255, 255, 255)
                    field_border_color = BORDER_COLOR
                    border_width_field = 1
                
                draw.rectangle([x, y, x + BOX_SIZE, y + BOX_SIZE], 
                              fill=field_bg_color, outline=field_border_color, width=border_width_field)
                
                number_text = f"[{number}]"
                text_color = TEXT_COLOR
                
                bbox = draw.textbbox((0, 0), number_text, font=number_font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                draw.text((x + (BOX_SIZE - tw) // 2, y + (BOX_SIZE - th) // 2), 
                         number_text, fill=text_color, font=number_font)
        
        return base_img
    
    base_frame_initial = create_base_frame(current_hits=0)
    frames.append(base_frame_initial.copy())
    durations.append(FRAME_DURATION)
    
    static_balls = []
    
    for i, number in enumerate(drawn_numbers):
        target_x, target_y = ball_positions[i]
        
        available_versions = [f"{number}_{v}" for v in range(5) if f"{number}_{v}" in available_balls]
        if not available_versions:
            continue
        
        ball_variants = []
        for version in available_versions:
            ball_img = Image.open(available_balls[version]).convert('RGBA')
            ball_img = ball_img.resize((BALL_SIZE, BALL_SIZE))
            ball_variants.append(ball_img)
        
        final_ball_img = random.choice(ball_variants)
        
        start_x = W // 2 - BALL_SIZE // 2
        start_y_anim = H + BALL_SIZE
        
        current_hits_before = len(set(player_numbers) & set([ball[2] for ball in static_balls]))
        
        steps = 20
        
        for step in range(steps + 1):
            frame_img = create_base_frame(current_hits=current_hits_before)
            frame_draw = ImageDraw.Draw(frame_img)
            
            border_width = 4
            frame_draw.rectangle([0, 0, W-1, H-1], outline=BORDER_COLOR, width=border_width)
            
            progress = step / steps
            eased_progress = 1 - (1 - progress) ** 2
            current_x = start_x + (target_x - start_x) * eased_progress
            current_y = start_y_anim + (target_y - start_y_anim) * eased_progress
            
            for static_data in static_balls:
                prev_x, prev_y, prev_number, prev_ball_img = static_data
                frame_img.paste(prev_ball_img, (int(prev_x), int(prev_y)), prev_ball_img)
            
            if step < steps:
                current_ball_img = random.choice(ball_variants)
                frame_img.paste(current_ball_img, (int(current_x), int(current_y)), current_ball_img)
            else:
                frame_img.paste(final_ball_img, (int(current_x), int(current_y)), final_ball_img)
            
            frames.append(frame_img)
            durations.append(FRAME_DURATION)
        
        static_balls.append((target_x, target_y, number, final_ball_img))
        
        current_hits_after = len(set(player_numbers) & set([ball[2] for ball in static_balls]))
        
        static_frame = create_base_frame(current_hits=current_hits_after)
        static_draw = ImageDraw.Draw(static_frame)
        border_width = 4
        static_draw.rectangle([0, 0, W-1, H-1], outline=BORDER_COLOR, width=border_width)
        
        for static_data in static_balls:
            prev_x, prev_y, prev_number, prev_ball_img = static_data
            static_frame.paste(prev_ball_img, (int(prev_x), int(prev_y)), prev_ball_img)
        
        frames.append(static_frame)
        durations.append(FRAME_DURATION)
    
    final_hits = len(set(player_numbers) & set(drawn_numbers))
    
    final_frame = create_base_frame(current_hits=final_hits)
    final_draw = ImageDraw.Draw(final_frame)
    border_width = 4
    final_draw.rectangle([0, 0, W-1, H-1], outline=BORDER_COLOR, width=border_width)
    
    for static_data in static_balls:
        target_x, target_y, number, ball_img = static_data
        final_frame.paste(ball_img, (int(target_x), int(target_y)), ball_img)
    
    frames.append(final_frame)
    durations.append(FRAME_DURATION)
    
    if len(frames) != len(durations):
        min_length = min(len(frames), len(durations))
        frames = frames[:min_length]
        durations = durations[:min_length]
    
    frames[0].save(
        output_path,
        format='WEBP',
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        quality=85,
        optimize=True
    )

def generate_specific_hits_animations():
    if not os.path.exists(ASSETS_FOLDER):
        return
    
    hit_configs = [
        (0, 150),
        (1, 100),
        (2, 100),
        (3, 50),
        (4, 25),
        (5, 3),
        (6, 1)
    ]
    
    total_animations = sum(count for _, count in hit_configs)
    
    for target_hits, count in hit_configs:
        output_folder = os.path.join(OUTPUT_BASE_FOLDER, f"{target_hits}_hits")
        os.makedirs(output_folder, exist_ok=True)
        
        generated_count = 0
        
        while generated_count < count:
            try:
                player_numbers = random.sample(range(1, 50), 6)
                
                if target_hits == 0:
                    available_numbers = [x for x in range(1, 50) if x not in player_numbers]
                    drawn_numbers = random.sample(available_numbers, 6)
                elif target_hits == 6:
                    drawn_numbers = player_numbers.copy()
                else:
                    common_numbers = random.sample(player_numbers, target_hits)
                    remaining_numbers = [x for x in range(1, 50) if x not in player_numbers]
                    additional_numbers = random.sample(remaining_numbers, 6 - target_hits)
                    drawn_numbers = common_numbers + additional_numbers
                    random.shuffle(drawn_numbers)
                
                actual_hits = len(set(player_numbers) & set(drawn_numbers))
                if actual_hits != target_hits:
                    continue
                
                output_path = os.path.join(output_folder, f"lotto_{target_hits}hits_{generated_count+1:03d}.webp")
                
                create_animated_lotto_ticket(player_numbers, drawn_numbers, output_path, ASSETS_FOLDER)
                
                generated_count += 1
                
            except Exception:
                continue

def generate_random_lotto_ticket(assets_folder, output_folder):
    player_numbers = random.sample(range(1, 50), 6)
    drawn_numbers = random.sample(range(1, 50), 6)
    
    os.makedirs(output_folder, exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_folder, f"lotto_ticket_{timestamp}.webp")
    
    create_animated_lotto_ticket(player_numbers, drawn_numbers, output_path, assets_folder)

def main():
    if not os.path.exists(ASSETS_FOLDER):
        return
    
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    print("1 - Random ticket")
    print("2 - Custom numbers")
    print("3 - Generate hit animations")
    choice = input("Select option (1, 2 or 3): ")
    
    if choice == "1":
        generate_random_lotto_ticket(ASSETS_FOLDER, OUTPUT_FOLDER)
    elif choice == "2":
        print("Enter 6 numbers (1-49), separated by spaces:")
        try:
            player_input = input().strip()
            player_numbers = [int(x) for x in player_input.split()]
            
            if len(player_numbers) != 6 or any(x < 1 or x > 49 for x in player_numbers):
                return
            
            if len(set(player_numbers)) != 6:
                return
            
            drawn_numbers = random.sample(range(1, 50), 6)
            
            output_path = os.path.join(OUTPUT_FOLDER, "my_lotto_ticket.webp")
            create_animated_lotto_ticket(player_numbers, drawn_numbers, output_path, ASSETS_FOLDER)
            
        except ValueError:
            return
    elif choice == "3":
        generate_specific_hits_animations()
    else:
        return

if __name__ == "__main__":
    main()