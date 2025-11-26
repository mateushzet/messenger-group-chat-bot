from PIL import Image, ImageDraw, ImageFont
import os

BASE_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, "assets", "coinflip", "static_assets")
COIN_ANIMATIONS_DIR = os.path.join(BASE_DIR, "assets", "coinflip")
balance_icon_path = os.path.join(ASSETS_DIR, "balance_icon.png")
bet_icon_path = os.path.join(ASSETS_DIR, "bet_icon.png")
AVATARS_DIR = os.path.join(BASE_DIR, "assets", "avatars")
default_avatar_path = os.path.join(AVATARS_DIR, "default-avatar.png")

def create_angular_gradient_background(output_path="angular_gradient_background.webp", width=600, height=300, 
                                     left_avatar_path=None, right_avatar_path=None,
                                     coin_result=None, left_player_data=None, right_player_data=None):
    if coin_result:
        return create_coin_animation_background(output_path, width, height, left_avatar_path, right_avatar_path, coin_result, left_player_data, right_player_data)
    else:
        return create_static_background(output_path, width, height, left_avatar_path, right_avatar_path, left_player_data, right_player_data)

def create_static_background(output_path, width, height, left_avatar_path, right_avatar_path, left_player_data=None, right_player_data=None):
    img = Image.open(os.path.join(ASSETS_DIR, "gradient_background.webp")).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    draw_elements(draw, img, width, height, left_avatar_path, right_avatar_path, left_player_data, right_player_data)
    
    img.save(output_path, "webp", quality=95)
    return output_path

def create_coin_animation_background(output_path, width, height, left_avatar_path, right_avatar_path, coin_result, left_player_data=None, right_player_data=None):
    if coin_result == 'red':
        coin_animation_path = os.path.join(COIN_ANIMATIONS_DIR, "coin_red_1.webp")
    else:
        coin_animation_path = os.path.join(COIN_ANIMATIONS_DIR, "coin_yellow_1.webp")
    
    if not os.path.exists(coin_animation_path):
        return create_static_background(output_path, width, height, left_avatar_path, right_avatar_path, left_player_data, right_player_data)
    
    try:
        coin_animation = Image.open(coin_animation_path)
        
        frames = []
        try:
            while True:
                frame = coin_animation.copy().convert("RGBA")
                frames.append(frame)
                coin_animation.seek(coin_animation.tell() + 1)
        except EOFError:
            pass
        
        if not frames:
            return create_static_background(output_path, width, height, left_avatar_path, right_avatar_path, left_player_data, right_player_data)
        
        gradient_bg = Image.open(os.path.join(ASSETS_DIR, "gradient_background.webp")).convert('RGB')
        winner_bg = Image.open(os.path.join(ASSETS_DIR, f"winner_background_{coin_result}.webp")).convert('RGB')
        
        final_frames = []
        coin_size = 65
        center_x = width * 0.5
        center_y = height * 0.5
        
        for coin_frame in frames:
            bg_img = gradient_bg.copy()
            bg_draw = ImageDraw.Draw(bg_img)
            
            draw_elements(bg_draw, bg_img, width, height, left_avatar_path, right_avatar_path, left_player_data, right_player_data, show_result=False, is_animation_frame=True)
            
            scaled_coin = coin_frame.resize((coin_size * 2, coin_size * 2), Image.LANCZOS)
            coin_position = (int(center_x - coin_size), int(center_y - coin_size))
            bg_img.paste(scaled_coin, coin_position, scaled_coin)
            
            final_frames.append(bg_img)
        
        last_coin_frame = frames[-1]
        
        result_frame = winner_bg.copy()
        result_draw = ImageDraw.Draw(result_frame)
        
        updated_left_data = left_player_data.copy() if left_player_data else {'level': 1, 'bet': 100, 'name': 'RUBY', 'balance': 1000}
        updated_right_data = right_player_data.copy() if right_player_data else {'level': 1, 'bet': 100, 'name': 'GOLD', 'balance': 1000}
        
        if coin_result == 'red':
            updated_left_data['balance'] = updated_left_data.get('balance', 1000) + updated_left_data.get('bet', 100)
            updated_right_data['balance'] = updated_right_data.get('balance', 1000) - updated_right_data.get('bet', 100)
        else:
            updated_left_data['balance'] = updated_left_data.get('balance', 1000) - updated_left_data.get('bet', 100)
            updated_right_data['balance'] = updated_right_data.get('balance', 1000) + updated_right_data.get('bet', 100)
        
        draw_elements(result_draw, result_frame, width, height, left_avatar_path, right_avatar_path, updated_left_data, updated_right_data, show_result=True, winner=coin_result, is_animation_frame=False)
        
        scaled_final_coin = last_coin_frame.resize((coin_size * 2, coin_size * 2), Image.LANCZOS)
        result_frame.paste(scaled_final_coin, (int(center_x - coin_size), int(center_y - coin_size)), scaled_final_coin)
        
        for _ in range(50):
            final_frames.append(result_frame)
        
        if len(final_frames) > 1:
            final_frames[0].save(
                output_path,
                format='WEBP',
                save_all=True,
                append_images=final_frames[1:],
                duration=50,
                loop=0,
                quality=95
            )
            return output_path
        else:
            return create_static_background(output_path, width, height, left_avatar_path, right_avatar_path, left_player_data, right_player_data)
            
    except Exception:
        return create_static_background(output_path, width, height, left_avatar_path, right_avatar_path, left_player_data, right_player_data)

def draw_elements(draw, img, width, height, left_avatar_path, right_avatar_path, left_player_data=None, right_player_data=None, show_result=False, winner=None, is_animation_frame=True):
    accent_ruby = (220, 30, 80)
    accent_gold = (255, 225, 50)
    glow_ruby = (180, 20, 60, 150)
    glow_gold = (220, 190, 40, 150)
    white = (255, 255, 255)
    light_gray = (180, 180, 180)
    dark_gray = (100, 100, 100)
    green_win = (50, 200, 50)
    red_lose = (200, 50, 50)
    
    center_y = height * 0.5
    center_x = width * 0.5
    
    avatar_size = 50
    coin_size = 65
    
    if left_player_data is None:
        left_player_data = {'level': 1, 'bet': 100, 'name': 'RUBY', 'balance': 1000}
    if right_player_data is None:
        right_player_data = {'level': 1, 'bet': 100, 'name': 'GOLD', 'balance': 1000}
    
    if os.path.exists(balance_icon_path):
        balance_icon = Image.open(balance_icon_path).convert("RGBA")
        balance_icon = balance_icon.resize((14, 14), Image.LANCZOS)
    
    if os.path.exists(bet_icon_path):
        bet_icon = Image.open(bet_icon_path).convert("RGBA")
        bet_icon = bet_icon.resize((14, 14), Image.LANCZOS)
    
    try:
        font_large = ImageFont.truetype("arial.ttf", 18)
        font_medium = ImageFont.truetype("arial.ttf", 14)
        font_small = ImageFont.truetype("arial.ttf", 11)
        font_bold = ImageFont.truetype("arialbd.ttf", 16)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_bold = ImageFont.load_default()
    
    left_name = left_player_data.get('name', 'RUBY')
    left_level = left_player_data.get('level', 1)
    left_bet = left_player_data.get('bet', 100)
    left_balance = left_player_data.get('balance', 1000)
    
    right_name = right_player_data.get('name', 'GOLD')
    right_level = right_player_data.get('level', 1)
    right_bet = right_player_data.get('bet', 100)
    right_balance = right_player_data.get('balance', 1000)
    
    avatar_left_x = width * 0.15
    avatar_right_x = width * 0.85
    avatar_y = center_y + 15
    
    nickname_y = avatar_y - avatar_size - 30
    
    left_nickname_text = left_name.upper()
    left_nickname_bbox = draw.textbbox((0, 0), left_nickname_text, font=font_large)
    left_nickname_width = left_nickname_bbox[2] - left_nickname_bbox[0]
    
    left_nickname_x = avatar_left_x - left_nickname_width / 2
    draw.text((left_nickname_x, nickname_y), left_nickname_text, fill=accent_ruby, font=font_large)
    
    left_level_text = f"LVL {left_level}"
    left_level_bbox = draw.textbbox((0, 0), left_level_text, font=font_small)
    left_level_width = left_level_bbox[2] - left_level_bbox[0]
    
    left_level_x = avatar_left_x - left_level_width / 2
    draw.text((left_level_x, nickname_y + 22), left_level_text, fill=light_gray, font=font_small)
    
    right_nickname_text = right_name.upper()
    right_nickname_bbox = draw.textbbox((0, 0), right_nickname_text, font=font_large)
    right_nickname_width = right_nickname_bbox[2] - right_nickname_bbox[0]
    
    right_nickname_x = avatar_right_x - right_nickname_width / 2
    draw.text((right_nickname_x, nickname_y), right_nickname_text, fill=accent_gold, font=font_large)
    
    right_level_text = f"LVL {right_level}"
    right_level_bbox = draw.textbbox((0, 0), right_level_text, font=font_small)
    right_level_width = right_level_bbox[2] - right_level_bbox[0]
    
    right_level_x = avatar_right_x - right_level_width / 2
    draw.text((right_level_x, nickname_y + 22), right_level_text, fill=light_gray, font=font_small)
    
    load_avatar_with_glow(img, draw, left_avatar_path, accent_ruby, avatar_left_x, avatar_y, avatar_size, glow_ruby)
    load_avatar_with_glow(img, draw, right_avatar_path, accent_gold, avatar_right_x, avatar_y, avatar_size, glow_gold)
    
    balance_y = avatar_y + avatar_size + 15
    
    left_balance_text = f"{left_balance}"
    left_balance_bbox = draw.textbbox((0, 0), left_balance_text, font=font_small)
    left_balance_width = left_balance_bbox[2] - left_balance_bbox[0]
    
    total_balance_width = left_balance_width + 18
    
    balance_left_x = avatar_left_x - total_balance_width / 2
    
    if balance_icon:
        img.paste(balance_icon, (int(balance_left_x), int(balance_y)), balance_icon)
    
    balance_color = green_win if show_result and winner == 'red' else (red_lose if show_result and winner == 'yellow' else white)
    draw.text((int(balance_left_x + 18), int(balance_y)), left_balance_text, fill=balance_color, font=font_small)
    
    right_balance_text = f"{right_balance}"
    right_balance_bbox = draw.textbbox((0, 0), right_balance_text, font=font_small)
    right_balance_width = right_balance_bbox[2] - right_balance_bbox[0]
    
    total_balance_width_right = right_balance_width + 18
    
    balance_right_x = avatar_right_x - total_balance_width_right / 2
    
    if balance_icon:
        img.paste(balance_icon, (int(balance_right_x), int(balance_y)), balance_icon)
    
    balance_color = green_win if show_result and winner == 'yellow' else (red_lose if show_result and winner == 'red' else white)
    draw.text((int(balance_right_x + 18), int(balance_y)), right_balance_text, fill=balance_color, font=font_small)
    
    bet_y = center_y - 5
    
    left_bet_text = f"{left_bet}"
    left_bet_bbox = draw.textbbox((0, 0), left_bet_text, font=font_medium)
    left_bet_width = left_bet_bbox[2] - left_bet_bbox[0]
    
    total_bet_width_left = left_bet_width + 18
    
    left_bet_x = avatar_left_x + avatar_size + (center_x - coin_size - (avatar_left_x + avatar_size)) * 0.4
    left_bet_x_centered = left_bet_x - total_bet_width_left / 2
    
    if bet_icon:
        img.paste(bet_icon, (int(left_bet_x_centered), int(bet_y)), bet_icon)
    
    bet_color_left = white if is_animation_frame or not show_result else (green_win if winner == 'red' else (red_lose if winner == 'yellow' else white))
    draw.text((int(left_bet_x_centered + 18), int(bet_y)), left_bet_text, fill=bet_color_left, font=font_medium)
    
    right_bet_text = f"{right_bet}"
    right_bet_bbox = draw.textbbox((0, 0), right_bet_text, font=font_medium)
    right_bet_width = right_bet_bbox[2] - right_bet_bbox[0]
    
    total_bet_width_right = right_bet_width + 18
    
    right_bet_x = center_x + coin_size + (avatar_right_x - avatar_size - (center_x + coin_size)) * 0.6
    right_bet_x_centered = right_bet_x - total_bet_width_right / 2
    
    if bet_icon:
        img.paste(bet_icon, (int(right_bet_x_centered), int(bet_y)), bet_icon)
    
    bet_color_right = white if is_animation_frame or not show_result else (green_win if winner == 'yellow' else (red_lose if winner == 'red' else white))
    draw.text((int(right_bet_x_centered + 18), int(bet_y)), right_bet_text, fill=bet_color_right, font=font_medium)
    
    line_start_left = avatar_left_x + avatar_size + 5
    line_end_left = center_x - coin_size - 5
    line_start_right = center_x + coin_size + 5
    line_end_right = avatar_right_x - avatar_size - 5
    
    if line_start_left < line_end_left:
        draw.line([line_start_left, center_y, line_end_left, center_y], 
                  fill=accent_ruby, width=3)
    
    if line_start_right < line_end_right:
        draw.line([line_start_right, center_y, line_end_right, center_y], 
                  fill=accent_gold, width=3)

def load_avatar_with_glow(img, draw, avatar_path, default_color, position_x, position_y, size, glow_color):
    try:
        glow_size = size + 12
        glow_img = Image.new('RGBA', (glow_size * 2, glow_size * 2), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_img)
        
        glow_steps = 8
        for i in range(glow_steps):
            current_size = glow_size - i
            alpha = int(glow_color[3] * (1 - i / glow_steps))
            current_glow_color = (glow_color[0], glow_color[1], glow_color[2], alpha)
            
            glow_draw.ellipse([
                glow_size - current_size, glow_size - current_size,
                glow_size + current_size, glow_size + current_size
            ], fill=current_glow_color)
        
        img.paste(glow_img, (int(position_x - glow_size), int(position_y - glow_size)), glow_img)
        
        if avatar_path and os.path.exists(avatar_path):
            avatar = Image.open(avatar_path).convert("RGBA")
            avatar = avatar.resize((size * 2, size * 2), Image.LANCZOS)
            
            mask = Image.new("L", (size * 2, size * 2), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([0, 0, size * 2, size * 2], fill=255)
            
            result = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
            result.paste(avatar, (0, 0), mask)
            
            img.paste(result, (int(position_x - size), int(position_y - size)), result)
            return True
        else:
            draw.ellipse([
                position_x - size, position_y - size,
                position_x + size, position_y + size
            ], fill=default_color)
            
            inner_glow_steps = 3
            for i in range(inner_glow_steps):
                current_size = size - 2 - i * 2
                alpha = int(80 * (1 - i / inner_glow_steps))
                inner_glow_color = (255, 255, 255, alpha)
                
                inner_glow_img = Image.new('RGBA', (size * 2, size * 2), (0, 0, 0, 0))
                inner_glow_draw = ImageDraw.Draw(inner_glow_img)
                
                inner_glow_draw.ellipse([
                    size - current_size, size - current_size,
                    size + current_size, size + current_size
                ], fill=inner_glow_color)
                
                img.paste(inner_glow_img, (int(position_x - size), int(position_y - size)), inner_glow_img)
            
            return False
            
    except Exception:
        draw.ellipse([
            position_x - size, position_y - size,
            position_x + size, position_y + size
        ], fill=default_color)
        return False

if __name__ == "__main__":
    left_player = {
        'level': 5,
        'bet': 250,
        'name': 'USER1',
        'balance': 1250
    }
    
    right_player = {
        'level': 8,
        'bet': 500,
        'name': 'USER2', 
        'balance': 3200
    }
    
    result = create_angular_gradient_background(
        "animation_test.webp",
        left_avatar_path=default_avatar_path,
        right_avatar_path=default_avatar_path,
        coin_result='red',
        left_player_data=left_player,
        right_player_data=right_player
    )