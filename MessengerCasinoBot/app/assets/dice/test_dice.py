from PIL import Image
import os
import random

def ultra_fast_dice(dice_results, dice_folder, output_path="dice_ultra_fast.webp"):

    frames = []
    positions = [(60,50), (160,50), (260,50), (60,150), (160,150), (260,150)]
    
    for i in range(8):
        bg = Image.new('RGBA', (400, 300), (30, 30, 60, 255))
        for pos in positions:
            x, y = pos
            placeholder = Image.new('RGBA', (80, 80), (100, 100, 100, 150))
            bg.paste(placeholder, (x-40, y-40), placeholder)
        frames.append(bg)
    
    for dice_index in range(6):
        for _ in range(3):
            bg = Image.new('RGBA', (400, 300), (30, 30, 60, 255))
            for i, pos in enumerate(positions):
                x, y = pos
                if i <= dice_index:
                    gif_path = os.path.join(dice_folder, f"dice_{dice_results[i]}.gif")
                    gif = Image.open(gif_path)
                    gif.seek(gif.n_frames - 1)
                    dice_frame = gif.convert('RGBA').resize((80, 80))
                    bg.paste(dice_frame, (x-40, y-40), dice_frame)
                    gif.close()
                else:
                    placeholder = Image.new('RGBA', (80, 80), (100, 100, 100, 150))
                    bg.paste(placeholder, (x-40, y-40), placeholder)
            frames.append(bg)
    
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0,
        format="WEBP"
    )
    
BASE_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
dice_folder = os.path.join(ASSETS_DIR, "dice")
results = [random.randint(1,6) for _ in range(6)]
ultra_fast_dice(results, dice_folder)