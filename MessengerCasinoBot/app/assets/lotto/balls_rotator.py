import os
import shutil
from PIL import Image
import glob

def process_images(folder_path):
   
    patterns = [
        os.path.join(folder_path, "[0-9]*_0.*")
    ]
    
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            try:
                filename = os.path.basename(file_path)
                name_without_ext, ext = os.path.splitext(filename)
                parts = name_without_ext.split('_')
                
                if len(parts) != 2:
                    continue
                
                number_part = parts[0]
                
                with Image.open(file_path) as img:
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    
                    file_2 = os.path.join(folder_path, f"{number_part}_3{ext}")
                    file_3 = os.path.join(folder_path, f"{number_part}_4{ext}")
                    
                    img_rotated_left = img.rotate(30, expand=False, resample=Image.BICUBIC)
                    img_rotated_left.save(file_2)
                    
                    img_rotated_right = img.rotate(-30, expand=False, resample=Image.BICUBIC)
                    img_rotated_right.save(file_3)
                    
            except Exception as e:
                print(f"Error {filename}: {e}")

BASE_DIR = os.path.dirname(__file__)
LOTTO_DIR = os.path.join(BASE_DIR, "games", "lotto")

folder_path = os.path.join(LOTTO_DIR, "balls")
process_images(folder_path)