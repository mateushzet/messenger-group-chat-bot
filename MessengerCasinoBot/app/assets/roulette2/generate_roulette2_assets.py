import os
from PIL import Image, ImageDraw, ImageFont

FIELDS = [0, 7, 2, 10, 4, 12, 6, 1, 9, 3, 11, 5, 8]
FIELD_COLORS = {
    0: "green",
    7: "red",
    2: "black",
    10: "red",
    4: "black",
    12: "red",
    6: "black",
    1: "red",
    9: "black",
    3: "red",
    11: "black",
    5: "red",
    8: "black",
}
COLOR_RGB = {
    "green": (0, 177, 88, 255),
    "red": (207, 57, 64, 255),
    "black": (45, 48, 54, 255),
}
GOLD = (255, 210, 75, 255)
PANEL = (28, 33, 45, 230)
DARK = (18, 20, 26, 255)

WIDTH = 572
HEIGHT = 220
FIELD_W = 56
FIELD_H = 56
GAP = 5
VISIBLE_FIELDS = 9
STRIP_Y = 90
CENTER_X = WIDTH // 2
TARGET_VISIBLE_INDEX = VISIBLE_FIELDS // 2

FRAMES = 60
TOTAL_FIELDS = 170
BASE_TARGET = 117
SPIN_DISTANCE = 54
DURATION = 40

OFFSETS = {
    "start": -FIELD_W * 0.36,
    "center": 0,
    "end": FIELD_W * 0.36,
}


def get_font(size):
    for name in ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


FONT_BIG = get_font(24)
FONT_MED = get_font(20)


def draw_text_center(img, text, x, y, width, height, font, fill=(255, 255, 255, 255), stroke_width=2):
    draw = ImageDraw.Draw(img)
    
    center_x = x + width // 2
    center_y = y + height // 2
    
    draw.text(
        (center_x, center_y), 
        text, 
        font=font, 
        fill=fill, 
        stroke_width=stroke_width, 
        stroke_fill=(0, 0, 0, 255),
        anchor="mm"
    )
def draw_field(img, value, x, y, highlighted=False):
    draw = ImageDraw.Draw(img)
    fill = COLOR_RGB[FIELD_COLORS[value]]
    outline = GOLD if highlighted else DARK
    outline_width = 3 if highlighted else 2
    draw.rectangle([x, y, x + FIELD_W, y + FIELD_H], fill=fill, outline=outline, width=outline_width)
    draw.rectangle([x + 5, y + 5, x + FIELD_W - 5, y + FIELD_H - 5], outline=(255, 255, 255, 52), width=1)
    
    font = FONT_BIG if value not in (10, 11, 12) else FONT_MED
    text = str(value)
    
    draw_text_center(img, text, x, y, FIELD_W, FIELD_H, font)


def draw_strip_frame(strip, pos, result, reveal):
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    item_step = FIELD_W + GAP
    frame_w = VISIBLE_FIELDS * item_step + 28
    frame_left = CENTER_X - frame_w // 2
    frame_right = CENTER_X + frame_w // 2

    draw.rectangle(
        [frame_left, STRIP_Y - 12, frame_right, STRIP_Y + FIELD_H + 12],
        fill=PANEL,
        outline=(88, 96, 118, 255),
        width=2,
    )

    base = int(pos)
    offset = (pos - base) * item_step
    first_x = CENTER_X - (VISIBLE_FIELDS // 2) * item_step - FIELD_W // 2

    for i in range(VISIBLE_FIELDS + 2):
        idx = (base + i) % len(strip)
        value = strip[idx]
        x = int(first_x + i * item_step - offset)
        highlighted = reveal and value == result and abs((x + FIELD_W // 2) - CENTER_X) < item_step // 2
        draw_field(img, value, x, STRIP_Y, highlighted)

    draw.line([(CENTER_X, STRIP_Y - 28), (CENTER_X, STRIP_Y + FIELD_H + 28)], fill=GOLD, width=3)
    draw.polygon([(CENTER_X - 12, STRIP_Y - 30), (CENTER_X + 12, STRIP_Y - 30), (CENTER_X, STRIP_Y - 10)], fill=GOLD)
    draw.polygon([(CENTER_X - 12, STRIP_Y + FIELD_H + 30), (CENTER_X + 12, STRIP_Y + FIELD_H + 30), (CENTER_X, STRIP_Y + FIELD_H + 10)], fill=GOLD)

    return img


def generate_animation(result, offset_name, offset_px, out_path):
    strip = [FIELDS[i % len(FIELDS)] for i in range(TOTAL_FIELDS)]
    target_index = BASE_TARGET + FIELDS.index(result)
    centered_end_pos = target_index - TARGET_VISIBLE_INDEX
    end_pos = centered_end_pos - (offset_px / (FIELD_W + GAP))
    start_pos = max(0, end_pos + SPIN_DISTANCE)

    frames = []
    for frame_no in range(FRAMES):
        t = frame_no / max(1, FRAMES - 1)
        ease = 1 - (1 - t) ** 5
        pos = start_pos + (end_pos - start_pos) * ease
        reveal = frame_no >= FRAMES - 6
        frames.append(draw_strip_frame(strip, pos, result, reveal))

    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION,
        loop=0,
        format="WEBP",
        quality=65,
        method=4,
    )


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(root, "results")
    os.makedirs(out_dir, exist_ok=True)

    for result in FIELDS:
        for offset_name, offset_px in OFFSETS.items():
            out_path = os.path.join(out_dir, f"result_{result}_{offset_name}.webp")
            generate_animation(result, offset_name, offset_px, out_path)
            print(out_path)


if __name__ == "__main__":
    main()