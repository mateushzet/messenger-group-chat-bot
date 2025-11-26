from PIL import Image, ImageDraw, ImageFilter
import math
import random
import os

W, H = 500, 500
frames = 150
accel_frames = 15
decel_start_frame = 25
show_result_frames = 46

ball_radius = 13
ball_distance = 150
max_wheel_speed = 10
max_ball_speed = 25

reversed_orders = [
    [33, 1, 20, 14, 31, 9, 22, 18, 29, 7,
     28, 12, 35, 3, 26, 0, 32, 15, 19, 4,
     21, 2, 25, 17, 34, 6, 27, 13, 36, 11,
     30, 8, 23, 10, 5, 24, 16],

    [7, 28, 12, 35, 3, 26, 0, 32, 15, 19, 4,
     21, 2, 25, 17, 34, 6, 27, 13, 36, 11,
     30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 
     14, 31, 9, 22, 18, 29],

    [19, 4, 21, 2, 25, 17, 34, 6, 27, 13,
     36, 11, 30, 8, 23, 10, 5, 24, 16, 33,
     1, 20, 14, 31, 9, 22, 18, 29, 7,
     28, 12, 35, 3, 26, 0, 32, 15],
    
    [36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 
     1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 
     12, 35, 3, 26, 0, 32, 15, 19, 4, 21, 
     2, 25, 17, 34, 6, 27, 13]
]

angle_shifts = [1, 88, 176, 273]

angle_per_number = (360 / 37)
number_angles = {i: angle_per_number * i for i in range(37)}

try:
    wheel_orig = Image.open("wheel.png").convert("RGBA")
    wheel_orig = wheel_orig.resize((500, 500), Image.LANCZOS)
except FileNotFoundError:
    exit(1)

def draw_ball(radius):
    size = radius * 4
    ball_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    gradient_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw_gradient = ImageDraw.Draw(gradient_layer)

    center = size // 2

    mask = Image.new('L', (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse(
        (center - radius, center - radius, center + radius, center + radius),
        fill=255
    )

    for r in range(radius * 2, 0, -1):
        factor = r / (radius * 2)
        gray_level = int(255 * (0.7 + 0.3 * factor))
        color = (gray_level, gray_level, gray_level, 255)
        draw_gradient.ellipse(
            (center - r, center - r, center + r, center + r),
            fill=color
        )

    highlight_size = radius // 1.5
    for r in range(int(highlight_size), 0, -1):
        alpha = int(255 * (1 - r / highlight_size) * 0.7)
        draw_gradient.ellipse((
            center - radius//2 - r,
            center - radius//2 - r,
            center - radius//2 + r,
            center - radius//2 + r
        ), fill=(255, 255, 255, alpha))

    gradient_layer.putalpha(mask)

    draw = ImageDraw.Draw(ball_img)
    draw.ellipse(
        (center - radius, center - radius, center + radius, center + radius),
        outline=(0, 0, 0, 255), width=4
    )

    shadow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_size = radius * 1.2
    shadow_draw.ellipse(
        (center - shadow_size, center - shadow_size//3 + 8,
         center + shadow_size, center + shadow_size//3 + 8),
        fill=(0, 0, 0, 120)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))

    ball_img = Image.alpha_composite(shadow, ball_img)
    ball_img = Image.alpha_composite(ball_img, gradient_layer)

    return ball_img

def decel_factor(speed, slow_factor=0.99, fast_factor=0.90, threshold=5):
    s = abs(speed)
    if s >= threshold:
        return fast_factor
    else:
        return slow_factor + (fast_factor - slow_factor) * (s / threshold)

os.makedirs("roulette_results", exist_ok=True)
ball_img = draw_ball(ball_radius)

for set_num in range(4):
    current_order = reversed_orders[set_num]
    shift_angle = angle_shifts[set_num]
    
    for target_number in range(37):
        ball_target_angle = (number_angles[target_number]) % 360
        
        wheel_angle = shift_angle
        ball_angle = (angle_per_number * target_number + 180) % 360
        ball_speed = 0.0
        wheel_speed = 0.0
        images = []
        
        random.seed(target_number)
        max_ball_speed_var = max_ball_speed
        max_wheel_speed_var = max_wheel_speed
        
        for i in range(frames):
            frame = Image.new('RGBA', (W, H), (0, 0, 0, 0))

            wheel_img = wheel_orig.rotate(wheel_angle, resample=Image.BILINEAR, expand=True)
            wx = (W - wheel_img.width) // 2
            wy = (H - wheel_img.height) // 2
            frame.alpha_composite(wheel_img, (wx, wy))

            rad = math.radians(ball_angle)
            ball_x = int(W / 2 + math.cos(rad) * ball_distance - ball_img.width // 2)
            ball_y = int(H / 2 + math.sin(rad) * ball_distance - ball_img.height // 2)
            frame.alpha_composite(ball_img, (ball_x, ball_y))

            images.append(frame)

            if i < accel_frames:
                factor = (i + 1) / accel_frames
                ball_speed = max_ball_speed_var * factor
                wheel_speed = max_wheel_speed_var * factor

                ball_angle += ball_speed
                wheel_angle += wheel_speed

            elif i < decel_start_frame:
                ball_speed = max_ball_speed_var
                wheel_speed = max_wheel_speed_var

                ball_angle += ball_speed
                wheel_angle += wheel_speed

            elif i < decel_start_frame + show_result_frames:
                if abs(ball_speed) > 0.1:
                    ball_angle += ball_speed
                    ball_speed *= decel_factor(ball_speed)
                else:
                    ball_angle = ball_target_angle
                    ball_speed = 0

                if abs(wheel_speed) > 0.05:
                    wheel_angle += wheel_speed
                    wheel_speed *= decel_factor(wheel_speed)
                else:
                    wheel_speed = 0

            else:
                ball_speed = 0
                wheel_speed = 0

        filename = f"roulette_results/result_{current_order[target_number]}_{set_num+1}.webp"
        images[0].save(
            filename,
            save_all=True,
            append_images=images[1:],
            duration=50,
            loop=0,
            disposal=2,
            lossless=False,
            method=5,
            minimize_size=True
        )