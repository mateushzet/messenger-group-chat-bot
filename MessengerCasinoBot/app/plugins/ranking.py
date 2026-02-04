import os
import time
from PIL import Image, ImageFont, ImageDraw
from base_game_plugin import BaseGamePlugin
from logger import logger

class RankingPlugin(BaseGamePlugin):
    def __init__(self):
        
        super().__init__(
            game_name="ranking"
        )
        
        self.avatars_folder = self.get_asset_path("avatars")
        self.backgrounds_folder = self.get_asset_path("backgrounds")
    
    def _load_user_avatar(self, user_id, avatar_file, size=80):
        try:
            if avatar_file and avatar_file != "default-avatar.png":
                avatar_path = os.path.join(self.avatars_folder, avatar_file)
                if os.path.exists(avatar_path):
                    avatar_img = Image.open(avatar_path).convert('RGBA')
                    avatar_img = avatar_img.resize((size, size), Image.LANCZOS)
                    
                    mask = Image.new('L', (size, size), 0)
                    draw_mask = ImageDraw.Draw(mask)
                    draw_mask.ellipse((0, 0, size, size), fill=255)
                    
                    avatar_circle = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                    avatar_circle.paste(avatar_img, (0, 0), mask)
                    
                    return avatar_circle
        except Exception as e:
            logger.error(f"[Ranking] Error loading avatar for user {user_id}: {e}")
        
        return self._create_fallback_avatar(user_id, size)
    
    def _create_fallback_avatar(self, user_id, size=80):
        img = Image.new('RGBA', (size, size), (70, 70, 80, 255))
        draw = ImageDraw.Draw(img)
        
        initial = str(user_id)[-1] if str(user_id) else "?"
        
        initial_img = self.text_renderer.render_text(
            text=initial,
            font_size=int(size * 0.6),
            color=(200, 200, 220, 255),
            stroke_width=2,
            stroke_color=(0, 0, 0, 255)
        )
        
        x = (size - initial_img.width) // 2
        y = (size - initial_img.height) // 2
        
        img.paste(initial_img, (x, y), initial_img)
        
        mask = Image.new('L', (size, size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, size, size), fill=255)
        
        avatar_circle = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        avatar_circle.paste(img, (0, 0), mask)
        
        return avatar_circle
    
    def _format_number(self, num):
        return f"{num:,}".replace(",", " ")
    
    def _calculate_level_bar(self, level_progress, width=200, height=12):
        bar_img = Image.new('RGBA', (width, height), (40, 40, 50, 255))
        draw = ImageDraw.Draw(bar_img)
        
        draw.rounded_rectangle([0, 0, width, height], radius=height//2, fill=(50, 50, 60))
        
        progress_width = int(width * min(level_progress, 1.0))
        if progress_width > 0:
            if level_progress < 0.5:
                color = (255, 150, 50)
            elif level_progress < 0.8:
                color = (100, 200, 255)
            else:
                color = (100, 255, 150)
            
            draw.rounded_rectangle([0, 0, progress_width, height], 
                                  radius=height//2, fill=color)
        
        draw.rounded_rectangle([0, 0, width, height], 
                              radius=height//2, outline=(80, 80, 90), width=1)
        
        return bar_img
    
    def _format_duration(self, seconds):
        if seconds < 60:
            return f"{int(seconds)}S"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}M {secs}S"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}H {minutes}M"
        else:
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            return f"{days}D {hours}H"
    
    def _update_leader_record(self, cache, leader_id, ranking_type="balance"):
        current_time = time.time()
        
        setting_key = f"ranking_leader_record_{ranking_type}"
        leader_record = cache.get_setting(setting_key, {})
        
        if leader_id:
            if leader_record.get("user_id") != leader_id:
                leader_record = {
                    "user_id": leader_id,
                    "start_time": current_time,
                    "last_check": current_time
                }
                cache.set_setting(setting_key, leader_record)
            else:
                leader_record["last_check"] = current_time
                cache.set_setting(setting_key, leader_record)
        
        leader_time = 0
        if leader_record and "start_time" in leader_record:
            leader_time = current_time - leader_record["start_time"]
        
        return leader_time, leader_record
    
    def get_sorted_ranking(self, cache, ranking_type="balance", max_users=None):
        if not hasattr(cache, 'users'):
            return []
        
        users = cache.users
        user_list = []
        
        for user_id, user_data in users.items():
            if isinstance(user_data, dict):
                user_data['id'] = user_id
                user_data['balance'] = user_data.get('balance', 0)
                user_data['level'] = user_data.get('level', 1)
                user_data['level_progress'] = user_data.get('level_progress', 0.0)
                user_data['name'] = user_data.get('name', f'User {user_id}')
                user_data['avatar'] = user_data.get('avatar', 'default-avatar.png')
                
                user_list.append(user_data)
        
        if ranking_type == "level":
            sorted_users = sorted(
                user_list, 
                key=lambda x: (x['level'], x['level_progress']), 
                reverse=True
            )
        else:
            sorted_users = sorted(user_list, key=lambda x: x['balance'], reverse=True)
        
        if max_users:
            return sorted_users[:max_users]
        return sorted_users
    
    def get_user_position(self, cache, user_id, ranking_type="balance"):
        ranking = self.get_sorted_ranking(cache, ranking_type)
        
        for i, user in enumerate(ranking, 1):
            if user['id'] == str(user_id):
                return i, user
        
        return None, None

    def _render_text_with_shadow(self, text, font_size, color, shadow_color=(0, 0, 0, 180)):
        return self.text_renderer.render_text(
            text=text,
            font_size=font_size,
            color=color,
            stroke_width=2,
            stroke_color=(0, 0, 0, 255),
            shadow=True,
            shadow_color=shadow_color,
            shadow_offset=(2, 2)
        )

    def create_ranking_image(self, output_path, cache, user_id=None, ranking_type="balance"):
        for rt in ["balance", "level"]:
            ranking = self.get_sorted_ranking(cache, rt)
            leader_id = ranking[0]['id'] if ranking else None
            self._update_leader_record(cache, leader_id, rt)

        ranking = self.get_sorted_ranking(cache, ranking_type)

        leader_id = ranking[0]['id'] if ranking else None
        leader_time, leader_record = self._update_leader_record(cache, leader_id, ranking_type)
        
        AVATAR_SIZE = 70
        ROW_HEIGHT = 100
        MARGIN = 20
        MAX_ROWS = 10
        
        total_height = (ROW_HEIGHT * min(len(ranking), MAX_ROWS) + 
                    MARGIN * 3 + 130)
        total_width = 900
        
        img = Image.new('RGBA', (total_width, total_height), (30, 30, 30, 255))
        draw = ImageDraw.Draw(img)
        
        if ranking_type == "level":
            title_text = "LEVEL RANKING"
        else:
            title_text = "BALANCE RANKING"
            
        title_img = self._render_text_with_shadow(
            text=title_text,
            font_size=32,
            color=(255, 215, 0, 255)
        )
        
        title_x = (total_width - title_img.width) // 2
        img.alpha_composite(title_img, (title_x, MARGIN + 10))
        
        headers_y = MARGIN + 75
        
        rank_text_img = self.text_renderer.render_text(
            text="RANK",
            font_size=20,
            color=(200, 200, 220, 255),
            stroke_width=1,
            stroke_color=(0, 0, 0, 255),
            shadow=True,
            shadow_color=(0, 0, 0, 150),
            shadow_offset=(1, 1)
        )
        
        rank_x = MARGIN + 10
        img.alpha_composite(rank_text_img, (rank_x, headers_y))
        
        player_text_img = self.text_renderer.render_text(
            text="PLAYER",
            font_size=20,
            color=(200, 200, 220, 255),
            stroke_width=1,
            stroke_color=(0, 0, 0, 255),
            shadow=True,
            shadow_color=(0, 0, 0, 150),
            shadow_offset=(1, 1)
        )
        
        player_x = MARGIN + 100
        img.alpha_composite(player_text_img, (player_x, headers_y))
        
        level_text_img = self.text_renderer.render_text(
            text="LEVEL",
            font_size=20,
            color=(200, 200, 220, 255),
            stroke_width=1,
            stroke_color=(0, 0, 0, 255),
            shadow=True,
            shadow_color=(0, 0, 0, 150),
            shadow_offset=(1, 1)
        )
        
        level_x = total_width - 380
        img.alpha_composite(level_text_img, (level_x, headers_y))
        
        balance_text_img = self.text_renderer.render_text(
            text="BALANCE",
            font_size=20,
            color=(200, 200, 220, 255),
            stroke_width=1,
            stroke_color=(0, 0, 0, 255),
            shadow=True,
            shadow_color=(0, 0, 0, 150),
            shadow_offset=(1, 1)
        )
        
        balance_x = total_width - 180
        img.alpha_composite(balance_text_img, (balance_x, headers_y))
        
        draw.line([(MARGIN, headers_y + 30), (total_width - MARGIN, headers_y + 30)], 
                fill=(100, 100, 120, 180), width=2)
        
        start_y = headers_y + 50

        for i, user in enumerate(ranking[:MAX_ROWS]):
            y_pos = start_y + (i * ROW_HEIGHT)
            
            user_bg_img = None
            try:
                user_bg_path = cache.get_background_path(user['id']) if hasattr(cache, 'get_background_path') else None
                if user_bg_path and os.path.exists(user_bg_path):
                    user_bg = Image.open(user_bg_path).convert('RGBA')
                    user_bg = user_bg.resize((total_width - MARGIN*2, ROW_HEIGHT - 10), Image.LANCZOS)
                    
                    darken_factor = 0.7
                    if user_bg.mode == 'RGBA':
                        r, g, b, a = user_bg.split()
                        r = r.point(lambda x: int(x * darken_factor))
                        g = g.point(lambda x: int(x * darken_factor))
                        b = b.point(lambda x: int(x * darken_factor))
                        user_bg_img = Image.merge('RGBA', (r, g, b, a))
                    else:
                        user_bg = user_bg.convert('RGB')
                        r, g, b = user_bg.split()
                        r = r.point(lambda x: int(x * darken_factor))
                        g = g.point(lambda x: int(x * darken_factor))
                        b = b.point(lambda x: int(x * darken_factor))
                        user_bg_img = Image.merge('RGB', (r, g, b)).convert('RGBA')
                    
                    if user_bg_img.mode == 'RGBA':
                        alpha = user_bg_img.split()[3]
                        alpha = alpha.point(lambda x: 255)
                        user_bg_img.putalpha(alpha)
            except Exception as e:
                logger.error(f"[Ranking] Error loading user background for {user['id']}: {e}")
                user_bg_img = None
            
            row_img = Image.new('RGBA', (total_width - MARGIN*2, ROW_HEIGHT - 10), (0, 0, 0, 0))
            row_draw = ImageDraw.Draw(row_img)
            
            mask = Image.new('L', (total_width - MARGIN*2, ROW_HEIGHT - 10), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle(
                [0, 0, total_width - MARGIN*2 - 1, ROW_HEIGHT - 11],
                radius=15,
                fill=255
            )
            
            if user_bg_img:
                user_bg_with_mask = Image.new('RGBA', (total_width - MARGIN*2, ROW_HEIGHT - 10), (0, 0, 0, 0))
                user_bg_with_mask.paste(user_bg_img, (0, 0), mask)
                row_img.paste(user_bg_with_mask, (0, 0))
            else:
                if i % 2 == 0:
                    row_color = (35, 40, 50, 255)
                else:
                    row_color = (45, 50, 60, 255)
                
                colored_bg = Image.new('RGBA', (total_width - MARGIN*2, ROW_HEIGHT - 10), row_color)
                colored_bg_with_mask = Image.new('RGBA', (total_width - MARGIN*2, ROW_HEIGHT - 10), (0, 0, 0, 0))
                colored_bg_with_mask.paste(colored_bg, (0, 0), mask)
                row_img.paste(colored_bg_with_mask, (0, 0))
            
            row_draw.rounded_rectangle(
                [0, 0, total_width - MARGIN*2 - 1, ROW_HEIGHT - 11],
                radius=15,
                fill=None,
                outline=(0, 0, 0),
                width=2
            )
            
            img.paste(row_img, (MARGIN, y_pos), row_img)
            
            rank_text = f"#{i+1}"
            rank_color = (255, 215, 0) if i == 0 else (220, 220, 240) if i == 1 else (205, 127, 50) if i == 2 else (180, 180, 200)
            
            rank_img = self.text_renderer.render_text(
                text=rank_text,
                font_size=24,
                color=rank_color,
                stroke_width=2,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_color=(0, 0, 0, 150),
                shadow_offset=(1, 1)
            )
            
            rank_x_pos = MARGIN + 30 - rank_img.width // 2
            rank_y_pos = y_pos + (ROW_HEIGHT - rank_img.height) // 2 - 5
            img.alpha_composite(rank_img, (rank_x_pos, rank_y_pos))
            
            avatar = self._load_user_avatar(user['id'], user.get('avatar'), AVATAR_SIZE)
            avatar_x = MARGIN + 80
            avatar_y = y_pos + (ROW_HEIGHT - AVATAR_SIZE) // 2 - 5
            
            img.paste(avatar, (avatar_x, avatar_y), avatar)
            
            name = user['name']
            if len(name) > 20:
                name = name[:17] + "..."
            
            name_img = self.text_renderer.render_text(
                text=name,
                font_size=24,
                color=(240, 240, 255, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_color=(0, 0, 0, 150),
                shadow_offset=(1, 1)
            )
            
            name_x = avatar_x + AVATAR_SIZE + 15
            name_y = y_pos + 20
            img.alpha_composite(name_img, (name_x, name_y))
            
            if i == 0 and leader_time > 0:
                time_text = f"{self._format_duration(leader_time)}"
                time_img = self.text_renderer.render_text(
                    text=time_text,
                    font_size=20,
                    color=(255, 200, 100, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255),
                    shadow=True,
                    shadow_color=(0, 0, 0, 150),
                    shadow_offset=(1, 1)
                )
                
                time_x = name_x + 5
                time_y = name_y + 25
                img.alpha_composite(time_img, (time_x, time_y))
            
            level_text = f"Level {user['level']}"
            level_img = self.text_renderer.render_text(
                text=level_text,
                font_size=18,
                color=(100, 200, 255, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_color=(0, 0, 0, 150),
                shadow_offset=(1, 1)
            )
            
            level_x_pos = total_width - 430
            level_y_pos = y_pos + 20
            img.alpha_composite(level_img, (level_x_pos, level_y_pos))
            
            progress_bar = self._calculate_level_bar(user['level_progress'], width=200, height=10)
            img.paste(progress_bar, (level_x_pos, level_y_pos + 25), progress_bar)
            
            progress_text = f"{int(user['level_progress'] * 100)}%"
            progress_img = self.text_renderer.render_text(
                text=progress_text,
                font_size=16,
                color=(150, 200, 150, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_color=(0, 0, 0, 150),
                shadow_offset=(1, 1)
            )
            
            progress_x_pos = level_x_pos + 100 - progress_img.width // 2
            progress_y_pos = level_y_pos + 40
            img.alpha_composite(progress_img, (progress_x_pos, progress_y_pos))
            
            balance_text = f"{self._format_number(user['balance'])} $"
            balance_color = (100, 255, 100) if user['balance'] >= 0 else (255, 100, 100)
            
            balance_img = self.text_renderer.render_text(
                text=balance_text,
                font_size=18,
                color=balance_color,
                stroke_width=1,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
                shadow_color=(0, 0, 0, 150),
                shadow_offset=(1, 1)
            )
            
            balance_x_pos = total_width - MARGIN - 50 - balance_img.width
            balance_y_pos = y_pos + (ROW_HEIGHT - balance_img.height) // 2 - 5
            img.alpha_composite(balance_img, (balance_x_pos, balance_y_pos))
        
        if user_id and len(ranking) > MAX_ROWS:
            position, user_data = self.get_user_position(cache, user_id, ranking_type)
            if position and position > MAX_ROWS:
                info_y = start_y + (MAX_ROWS * ROW_HEIGHT) + 20
                
                info_bg = Image.new('RGBA', (total_width - MARGIN*2, 60), (40, 40, 50, 255))
                img.paste(info_bg, (MARGIN, info_y), info_bg)
                draw.rounded_rectangle([MARGIN, info_y, total_width - MARGIN, info_y + 60], 
                                    radius=10, outline=(0, 0, 0), width=2)
                
                info_text = f"Your position: #{position}"
                info_img = self.text_renderer.render_text(
                    text=info_text,
                    font_size=20,
                    color=(255, 200, 100, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255),
                    shadow=True,
                    shadow_color=(0, 0, 0, 150),
                    shadow_offset=(1, 1)
                )
                
                info_x = (total_width - info_img.width) // 2
                info_y_pos = info_y + 20
                img.alpha_composite(info_img, (info_x, info_y_pos))
        
        img.save(output_path, format='WEBP', quality=90, optimize=True)
        logger.info(f"[Ranking] Ranking image saved to: {output_path}")
        return output_path

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        user_id, user, error = self.validate_user_and_balance(cache, sender, avatar_url, 0)
        if error:
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message=error,
                title="RANKING ERROR",
                cache=cache,
                user_id=user_id
            )
            return None
        
        ranking_type = "balance"
        
        if args:
            arg = args[0].lower()
            if arg in ["level", "lvl", "levels"]:
                ranking_type = "level"
            elif arg in ["money", "balance", "bal", "cash", "coins"]:
                ranking_type = "balance"
        
        img_path = os.path.join(self.results_folder, f"ranking_{ranking_type}_{user_id}.webp")
        self.create_ranking_image(img_path, cache, user_id, ranking_type)
        
        file_queue.put(img_path)
        
        position, user_data = self.get_user_position(cache, user_id, ranking_type)
        total_users = len(cache.users) if hasattr(cache, 'users') else 0
        
        leader_record_key = f"ranking_leader_record_{ranking_type}"
        leader_record = cache.get_setting(leader_record_key, {})
        current_time = time.time()
        leader_time = 0
        if leader_record and "start_time" in leader_record:
            leader_time = current_time - leader_record["start_time"]
        
        if ranking_type == "level":
            response = f"**LEVEL RANKING**\n\n"
            top_users = self.get_sorted_ranking(cache, ranking_type="level", max_users=3)
            
            for i, top_user in enumerate(top_users):
                name = top_user['name'][:20] + "..." if len(top_user['name']) > 20 else top_user['name']
                if i == 0 and leader_time > 0:
                    time_str = self._format_duration(leader_time)
                    response += f"**#{i+1}** {name} - Level {top_user['level']} ({int(top_user['level_progress']*100)}%) {time_str}\n"
                else:
                    response += f"**#{i+1}** {name} - Level {top_user['level']} ({int(top_user['level_progress']*100)}%)\n"
            
            response += f"\n**Your Position:** #{position}/{total_users}\n"
            response += f"• Level: {user['level']} ({int(user['level_progress']*100)}%)\n"
            response += f"• Balance: {self._format_number(user['balance'])} coins\n"
            
        else:
            response = f"**BALANCE RANKING**\n\n"
            top_users = self.get_sorted_ranking(cache, ranking_type="balance", max_users=3)
            
            for i, top_user in enumerate(top_users):
                name = top_user['name'][:20] + "..." if len(top_user['name']) > 20 else top_user['name']
                if i == 0 and leader_time > 0:
                    time_str = self._format_duration(leader_time)
                    response += f"**#{i+1}** {name} - {self._format_number(top_user['balance'])} coins {time_str}\n"
                else:
                    response += f"**#{i+1}** {name} - {self._format_number(top_user['balance'])} coins\n"
            
            response += f"\n**Your Position:** #{position}/{total_users}\n"
            response += f"• Balance: {self._format_number(user['balance'])} coins\n"
            response += f"• Level: {user['level']} ({int(user['level_progress']*100)}%)\n"
        
        return None


def register():
    plugin = RankingPlugin()
    return {
        "name": "ranking",
        "aliases": ["/ranking", "/rank"],
        "description": "Player Rankings & Leaderboards\n\n**Commands:**\n- `/rank` or `/ranking` - Balance ranking (default)\n- `/rank balance` - Players ranked by coins\n- `/rank level` - Players ranked by level\n\n**Features:**\n• Top 10 players with avatars and backgrounds\n• Your current position highlighted\n• Leader duration tracking for top players",
        "execute": plugin.execute_game
    }