from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math
import os

WIDTH = 210
HEIGHT = 100

BOX_X = 10
BOX_Y = 0
BOX_WIDTH = WIDTH - 20
BOX_HEIGHT = 60

BAR_HEIGHT = 15
BAR_Y = BOX_Y + 25
SEGMENTS = 9

FRAME_DELAY_MS = 50
FINAL_PAUSE_MS = 2000
MAX_FRAMES = 100

def load_font(bold=False, size=12):
    try:
        if bold:
            return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        else:
            return ImageFont.truetype("DejaVuSans.ttf", size)
    except Exception:
        return ImageFont.load_default()


REWARD_FONT = load_font(bold=True, size=22)
BALANCE_FONT = load_font(bold=False, size=14)

def draw_centered_text(draw, text, font, y, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w_text = bbox[2] - bbox[0]
    h_text = bbox[3] - bbox[1]
    x = (WIDTH - w_text) // 2
    draw.text((x, y - (h_text // 2)), text, font=font, fill=fill)


def draw_text_with_shadow(draw, text, position, font, fill,
                          shadow_fill=(0, 0, 0, 200), offset=1):

    x, y = position
    for dx in (-offset, 0, offset):
        for dy in (-offset, 0, offset):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font, fill=shadow_fill)
    draw.text((x, y), text, font=font, fill=fill)


def create_frame(reward, progress, highlight, pulse_value):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.rounded_rectangle([BOX_X, BAR_Y, BOX_X + BOX_WIDTH, BAR_Y + BAR_HEIGHT],
                           radius=10, fill=(50, 50, 50, 160))

    for i in range(1, SEGMENTS + 1):
        x = BOX_X + (BOX_WIDTH * i // (SEGMENTS + 1))
        draw.line([(x, BAR_Y + 2), (x, BAR_Y + BAR_HEIGHT - 2)],
                  fill=(255, 255, 255, 40))

    fill_width = int(BOX_WIDTH * progress)
    gold = (255, 215, 0)
    r = min(255, int(gold[0] * pulse_value))
    g = min(255, int(gold[1] * pulse_value))
    b = min(255, int(gold[2] * pulse_value))
    fill_color = (r, g, b, 230)

    if fill_width > 0:
        draw.rounded_rectangle([BOX_X, BAR_Y, BOX_X + fill_width,
                                BAR_Y + BAR_HEIGHT],
                               radius=10, fill=fill_color)

        shine_w = min(30, fill_width)
        shine_x = max(BOX_X, BOX_X + fill_width - 20)
        shine = Image.new("RGBA", (shine_w, BAR_HEIGHT), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shine)
        for i in range(shine_w):
            alpha = int(130 * (1 - (i / max(1, shine_w - 1))))
            sd.line([(i, 0), (i, BAR_HEIGHT)], fill=(255, 223, 50, alpha))
        img.paste(shine, (shine_x, BAR_Y), shine)

    draw_text_with_shadow(draw, "0", (BOX_X, BAR_Y + BAR_HEIGHT + 10),
                          font=BALANCE_FONT, fill=(255, 255, 255, 255))
    mid_str = "50"
    bbox_mid = draw.textbbox((0, 0), mid_str, font=BALANCE_FONT)
    w_mid = bbox_mid[2] - bbox_mid[0]
    draw_text_with_shadow(draw, mid_str,
                          (BOX_X + BOX_WIDTH // 2 - w_mid // 2, BAR_Y + BAR_HEIGHT + 10),
                          font=BALANCE_FONT, fill=(255, 255, 255, 255))
    max_str = "100"
    bbox_max = draw.textbbox((0, 0), max_str, font=BALANCE_FONT)
    w_max = bbox_max[2] - bbox_max[0]
    draw_text_with_shadow(draw, max_str,
                          (BOX_X + BOX_WIDTH - w_max, BAR_Y + BAR_HEIGHT + 10),
                          font=BALANCE_FONT, fill=(255, 255, 255, 255))

    if highlight:
        text_reward = f"Reward: {reward} coins"
        bbox_r = draw.textbbox((0, 0), text_reward, font=REWARD_FONT)
        w_r = bbox_r[2] - bbox_r[0]
        x_r = (WIDTH - w_r) // 2
        y_r = BAR_Y + BAR_HEIGHT + 38
        draw_text_with_shadow(draw, text_reward, (x_r, y_r),
                              font=REWARD_FONT, fill=(255, 230, 60, 255),
                              shadow_fill=(0, 0, 0, 255), offset=2)

    img = img.filter(ImageFilter.SMOOTH)
    return img


def generate_webp(reward, output_path):
    target_progress = reward / 100.0
    progress_step = 0.02
    animated_frames = int(math.ceil(target_progress / progress_step))
    animated_frames = min(animated_frames, MAX_FRAMES - 1)

    pulses = [0.7 + 0.3 * ((math.sin(2 * math.pi * i / MAX_FRAMES) + 1) / 2)
              for i in range(MAX_FRAMES)]

    frames = []
    durations = []

    for i in range(animated_frames):
        progress = min(i * progress_step, target_progress)
        frame = create_frame(reward, progress, highlight=False, pulse_value=1.0)
        frames.append(frame)
        durations.append(FRAME_DELAY_MS)

    last_index = animated_frames
    last_frame = create_frame(reward, target_progress, highlight=True,
                              pulse_value=pulses[last_index % MAX_FRAMES])
    frames.append(last_frame)

    durations.append(FINAL_PAUSE_MS)

    frames[0].save(
        output_path,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        quality=90,
        transparency=0
    )

def main():
    os.makedirs("rewards", exist_ok=True)
    for reward in range(10, 101, 10):
        filename = f"rewards/reward_{reward}.webp"
        generate_webp(reward, filename)
        print(f"{filename} done")


if __name__ == "__main__":
    main()
