from PIL import Image, ImageDraw, ImageFont
import os
import math
import random

def create_varied_slowmo_flip(animation_folder, output_path="coin_flip_varied.webp", total_frames=160, frame_duration=50, final_result=None, variation_type=0):
    frames = []
    for i in range(1, 19):
        path = os.path.join(animation_folder, f"{i}.png")
        if os.path.exists(path):
            frames.append(Image.open(path).convert("RGBA"))
    
    if not frames:
        raise ValueError("No animation frames found!")

    w, h = frames[0].size
    max_scale = 1.8
    max_w, max_h = int(w * max_scale), int(h * max_scale)

    if final_result is None:
        final_result = random.choice([0, 1])
    
    if variation_type == 0:
        rotation_speed = 4.0
        spin_speed = 0.8
        slowmo_start = 0.45
        slowmo_duration = 0.3
        max_scale_var = 1.8
    elif variation_type == 1:
        rotation_speed = 5.0
        spin_speed = 1.2
        slowmo_start = 0.4
        slowmo_duration = 0.35
        max_scale_var = 1.9
    elif variation_type == 2:
        rotation_speed = 3.0
        spin_speed = 0.5
        slowmo_start = 0.5
        slowmo_duration = 0.25
        max_scale_var = 1.7
    elif variation_type == 3:
        rotation_speed = 6.0
        spin_speed = 1.5
        slowmo_start = 0.35
        slowmo_duration = 0.4
        max_scale_var = 2.0
    elif variation_type == 4:
        rotation_speed = 4.5
        spin_speed = 1.0
        slowmo_start = 0.48
        slowmo_duration = 0.28
        max_scale_var = 1.85

    vs_frames = int(total_frames * 0.1)
    countdown_frames = int(total_frames * 0.25)
    flip_frames = int(total_frames * 0.4)
    result_frames = total_frames - (vs_frames + countdown_frames + flip_frames)

    all_frames = []

    for i in range(total_frames):
        frame = Image.new("RGBA", (max_w, max_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)

        if i < vs_frames:
            t = i / vs_frames
            try:
                font = ImageFont.truetype("arial.ttf", max_w // 3)
            except:
                font = ImageFont.load_default()
            text = "VS"
            tw, th = draw.textbbox((0, 0), text, font=font)[2:]
            x = (max_w - tw) // 2
            y = (max_h - th) // 2
            alpha = int(255 * min(1.0, t * 2))
            draw.text((x + 3, y + 3), text, fill=(0, 0, 0, alpha), font=font)
            draw.text((x, y), text, fill=(255, 255, 255, alpha), font=font)

        elif i < vs_frames + countdown_frames:
            t = (i - vs_frames) / countdown_frames
            num = 3 - int(t * 3)
            if num > 0:
                try:
                    font = ImageFont.truetype("arial.ttf", max_w // 2)
                except:
                    font = ImageFont.load_default()
                text = str(num)
                tw, th = draw.textbbox((0, 0), text, font=font)[2:]
                x = (max_w - tw) // 2
                y = (max_h - th) // 2
                
                pulse_freq = 0.6 + (variation_type * 0.1)
                pulse = abs(math.sin(i * pulse_freq)) * 0.4 + 0.6
                color = (int(255 * pulse), int(255 * pulse), int(255 * pulse), 255)
                draw.text((x + 3, y + 3), text, fill=(0, 0, 0, 255), font=font)
                draw.text((x, y), text, fill=color, font=font)

        elif i < vs_frames + countdown_frames + flip_frames:
            t = (i - vs_frames - countdown_frames) / flip_frames
            
            if t < 0.5:
                scale = 1.0 + (max_scale_var - 1.0) * (t * 2)
            else:
                fall_t = (t - 0.5) * 2
                if fall_t < 0.15:
                    scale = max_scale_var - 0.4 * (fall_t * 6.67)
                else:
                    scale = 1.4
            
            slowmo_end = slowmo_start + slowmo_duration
            extreme_slowmo_start = slowmo_end - 0.1
            
            if t < slowmo_start:
                upward_t = t * 2
                total_progress = upward_t * rotation_speed
                frame_index = int(total_progress * len(frames)) % len(frames)
            elif t < extreme_slowmo_start:
                slowmo_t = (t - slowmo_start) / (extreme_slowmo_start - slowmo_start)
                if variation_type % 2 == 0:
                    slow_factor = 1.0 - slowmo_t * 0.8
                else:
                    slow_factor = 1.0 - (slowmo_t ** 1.5) * 0.8
                
                base_progress = slowmo_start * 2 * rotation_speed
                additional_progress = slowmo_t * rotation_speed * (extreme_slowmo_start - slowmo_start) * 2 * slow_factor
                total_progress = base_progress + additional_progress
                frame_index = int(total_progress * len(frames)) % len(frames)
            elif t < slowmo_end:
                extreme_slowmo_t = (t - extreme_slowmo_start) / (slowmo_end - extreme_slowmo_start)
                final_speed = 0.02 + (variation_type * 0.01)
                slow_factor = 0.2 - extreme_slowmo_t * (0.2 - final_speed)
                
                base_progress = slowmo_start * 2 * rotation_speed + (rotation_speed * (extreme_slowmo_start - slowmo_start) * 2 * 0.2)
                additional_progress = extreme_slowmo_t * rotation_speed * (slowmo_end - extreme_slowmo_start) * 2 * slow_factor
                total_progress = base_progress + additional_progress
                frame_index = int(total_progress * len(frames)) % len(frames)
            else:
                frame_index = 0 if final_result == 0 else 9
            
            coin = frames[frame_index].resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            
            if t < 0.5:
                spin_angle = t * 360 * spin_speed * 2
                rotated_coin = coin.rotate(spin_angle % 360, expand=True, resample=Image.BICUBIC)
                x = (max_w - rotated_coin.width) // 2
                y = (max_h - rotated_coin.height) // 2
                frame.paste(rotated_coin, (x, y), rotated_coin)
            else:
                x = (max_w - coin.width) // 2
                y = (max_h - coin.height) // 2
                frame.paste(coin, (x, y), coin)

        else:
            scale = 1.4
            result_index = 0 if final_result == 0 else 9
            coin = frames[result_index].resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            x = (max_w - coin.width) // 2
            y = (max_h - coin.height) // 2
            frame.paste(coin, (x, y), coin)

        all_frames.append(frame)

    all_frames[0].save(
        output_path,
        format="WEBP",
        save_all=True,
        append_images=all_frames[1:],
        duration=frame_duration,
        loop=0,
        optimize=True
    )

    return output_path

def generate_diverse_animations(animation_folder):
    variations = [
        "normal",
        "fast", 
        "slow",
        "extreme",
        "atypical"
    ]
    
    for i in range(1, 6):
        variation_type = i - 1
        output_name = f"coin_1_{variations[variation_type]}.webp"
        create_varied_slowmo_flip(animation_folder, output_name, final_result=0, variation_type=variation_type)
    
    for i in range(1, 6):
        variation_type = i - 1
        output_name = f"coin_10_{variations[variation_type]}.webp"
        create_varied_slowmo_flip(animation_folder, output_name, final_result=1, variation_type=variation_type)

def create_single_varied_flip(animation_folder, output_path="coin_test.webp", final_result=None):
    variation_type = random.randint(0, 4)
    return create_varied_slowmo_flip(animation_folder, output_path, final_result=final_result, variation_type=variation_type)

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(__file__)
    COINFLIP_DIR = os.path.join(BASE_DIR, "assets", "coinflip")
    folder = os.path.join(COINFLIP_DIR, "chip_animation")
    
    generate_diverse_animations(folder)
    create_single_varied_flip(folder, "coin_random_test.webp")