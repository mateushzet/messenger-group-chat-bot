import os
from PIL import Image, ImageDraw, ImageFont

class AnimationGenerator:
    BASE_DIR = os.path.dirname(__file__)
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    BET_ICON_PATH = os.path.join(ASSETS_DIR, "bet_icon.png")
    BALANCE_ICON_PATH = os.path.join(ASSETS_DIR, "balance_icon.png")

    def __init__(self, avatar_size: int = 90, bar_height: int = 40, overlay_frames: int = 1, extra_bottom: int = 50):
        self.avatar_size = avatar_size
        self.bar_height = bar_height
        self.overlay_frames = overlay_frames
        self.extra_bottom = extra_bottom
        self.dark_gray = (40, 40, 40, 255)
        self.min_bar_width = 80

    def _load_and_preprocess_image(self, path, resize=None, convert_mode="RGBA"):
        img = Image.open(path)
        if convert_mode:
            img = img.convert(convert_mode)
        if resize:
            img = img.resize(resize)
        return img

    def _get_text_width(self, text, font):
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]

    def _create_avatar_bar(self, avatar, avatar_mask, user_info, font_small):
        bar = Image.new("RGBA", (self.avatar_size, self.avatar_size), (0, 0, 0, 0))
        bar.paste(avatar, (0, 0), avatar_mask)
        draw = ImageDraw.Draw(bar)

        level_text = str(user_info["level"])
        level_width = self._get_text_width(level_text, font_small)
        level_x = self.avatar_size - level_width - 3
        draw.text(
            (level_x, 3),
            level_text,
            font=font_small,
            fill=(255, 255, 255, 255),
            stroke_width=1,
            stroke_fill=(0, 0, 0, 255),
        )

        bar_height_px = 6
        bar_x0 = 3
        bar_y0 = self.avatar_size - bar_height_px - 3
        bar_width_full = self.avatar_size - 6
        progress = user_info.get("level_progress", 0.1)
        bar_x1 = int(bar_width_full * progress)
        bar_y1 = bar_y0 + bar_height_px
        draw.rectangle((bar_x0, bar_y0, bar_x1, bar_y1), fill=(0, 120, 255, 255))
        draw.rectangle(
            (bar_x0, bar_y0, bar_width_full, bar_y1),
            outline=(255, 255, 255, 255),
            width=1,
        )

        return bar

    def _create_bars(self, user_info, font_small, bet_icon, balance_icon):
        bars = []

        nick_lines = user_info["username"].split(" ")
        max_width = max([self._get_text_width(w, font_small) for w in nick_lines])
        width = max(max_width + 20, self.min_bar_width)
        height = self.bar_height
        nick_bar = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(nick_bar)
        draw.rounded_rectangle((0, 0, width, height), radius=7, fill=self.dark_gray)

        total_height = sum([font_small.getbbox(w)[3] - font_small.getbbox(w)[1] for w in nick_lines])
        y_offset = (height - total_height) // 2 - 5
        for w in nick_lines:
            bbox = font_small.getbbox(w)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text(
                (x, y_offset),
                w,
                font=font_small,
                fill=(255, 255, 255, 255),
                stroke_width=1,
                stroke_fill=(0, 0, 0, 255),
            )
            y_offset += bbox[3] - bbox[1]
        bars.append(nick_bar)

        for text, icon in [(f"{user_info['bet']}", bet_icon), (f"{user_info['balance']}", balance_icon)]:
            text_width = self._get_text_width(text, font_small)
            width = max(icon.width + 5 + text_width + 10, self.min_bar_width)
            height = self.bar_height
            bar = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(bar)
            draw.rounded_rectangle((0, 0, width, height), radius=7, fill=self.dark_gray)
            y_icon = (height - icon.height) // 2
            bar.paste(icon, (5, y_icon), icon)
            x_text = icon.width + 10
            y_text = (height - (font_small.getbbox(text)[3] - font_small.getbbox(text)[1])) // 2 - 5
            draw.text(
                (x_text, y_text),
                text,
                font=font_small,
                fill=(255, 255, 255, 255),
                stroke_width=1,
                stroke_fill=(0, 0, 0, 255),
            )
            bars.append(bar)

        return bars
    
    def generate_static_image_with_overlay(self, base_image_path, avatar_path, bg_path, user_info, output_path):
        final_path = self.generate_static(
            image_path=base_image_path,
            avatar_path=avatar_path,
            bg_path=bg_path,
            user_info_before=user_info,
            user_info_after=user_info,
            output_path=output_path
        )
        return final_path

    def generate(self, anim_path, avatar_path, bg_path, user_info_before, user_info_after, output_path="output.webp", game_type=None):
        img = Image.open(anim_path)
        n_frames = getattr(img, "n_frames", 1)
        is_animated = n_frames > 1
        img.seek(0)
        first_frame = img.convert("RGBA")

        background_base = self._load_and_preprocess_image(bg_path, resize=first_frame.size)
        bet_icon = self._load_and_preprocess_image(self.BET_ICON_PATH, resize=(25, 25))
        balance_icon = self._load_and_preprocess_image(self.BALANCE_ICON_PATH, resize=(25, 25))
        avatar = self._load_and_preprocess_image(avatar_path, resize=(self.avatar_size, self.avatar_size))

        try:
            font_small = ImageFont.truetype("DejaVuSans-Bold.ttf", first_frame.size[0] // 26)
            font_result = ImageFont.truetype("DejaVuSans-Bold.ttf", first_frame.size[0] // 10)
        except:
            font_small = font_result = ImageFont.load_default()

        avatar_mask = Image.new("L", (self.avatar_size, self.avatar_size), 0)
        mask_draw = ImageDraw.Draw(avatar_mask)
        mask_draw.rounded_rectangle((0, 0, self.avatar_size, self.avatar_size), radius=5, fill=255)

        bars_before = self._create_bars(user_info_before, font_small, bet_icon, balance_icon)
        bars_after = self._create_bars(user_info_after, font_small, bet_icon, balance_icon)
        avatar_bar_before = self._create_avatar_bar(avatar, avatar_mask, user_info_before, font_small)
        avatar_bar_after = self._create_avatar_bar(avatar, avatar_mask, user_info_after, font_small)

        win_value = user_info_after["win"]
        if win_value > 0:
            label, color = "Win:", (0, 255, 0, 255)
        elif win_value < 0:
            label, color = "Lose:", (255, 0, 0, 255)
        else:
            label, color = "Win:", (200, 200, 200, 255)
        win_text = f"{label} {abs(win_value)}$"
        
        bbox = font_result.getbbox(win_text)
        win_text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x_center = (first_frame.width - win_text_width) // 2
        y_center = (first_frame.height - text_height) // 2

        new_height = first_frame.height + self.extra_bottom
        background_base_extended = Image.new("RGBA", (first_frame.width, new_height))
        background_base_extended.paste(background_base, (0, 0))
        draw_bg = ImageDraw.Draw(background_base_extended)
        draw_bg.rectangle([0, first_frame.height, first_frame.width, new_height], fill=(30, 30, 30, 255))

        frames, durations = [], []
        frame_skip = 2

        included_frames = list(range(0, n_frames, frame_skip))
        
        last_frame_index = n_frames - 1
        if is_animated and last_frame_index not in included_frames:
            included_frames.append(last_frame_index)
        
        included_frames.sort()

        for i in included_frames:
            if is_animated:
                img.seek(i)
                frame = img.convert("RGBA")
            else:
                frame = first_frame.copy()

            combined = Image.new("RGBA", (first_frame.width, new_height))
            combined.paste(background_base_extended, (0, 0))
            combined.paste(frame, (0, 0), frame)

            if i < n_frames - self.overlay_frames or not is_animated:
                avatar_bar, bars = avatar_bar_before, bars_before
            else:
                avatar_bar, bars = avatar_bar_after, bars_after

            avatar_x = first_frame.width - avatar_bar.width - 15
            avatar_y = new_height - avatar_bar.height - 5
            combined.paste(avatar_bar, (avatar_x, avatar_y), avatar_bar)

            x = (first_frame.width - sum([b.width for b in bars]) - avatar_bar.width - 30) // (len(bars) + 1)
            y = new_height - self.bar_height - 5
            for b in bars:
                combined.paste(b, (x, y), b)
                x += b.width + 10

            if (i >= n_frames - self.overlay_frames or not is_animated) and game_type != "case" and game_type != "hourly" and game_type != "math":
                draw_center = ImageDraw.Draw(combined)
                draw_center.text(
                    (x_center, y_center),
                    win_text,
                    font=font_result,
                    fill=color,
                    stroke_width=1,
                    stroke_fill=(0, 0, 0, 255),
                )

            frames.append(combined)
            
            if is_animated:
                base_duration = img.info.get("duration", 100)
                
                is_last_frame = (i == last_frame_index)
                
                if is_last_frame and game_type == "plinko":
                    duration = base_duration * 20.0
                elif is_last_frame and game_type == "lotto":
                    duration = base_duration * 20.0
                elif is_last_frame:
                    duration = base_duration * 1.4
                else:
                    duration = base_duration * 1.4
            else:
                duration = 100
            
            durations.append(duration)

        if is_animated and len(frames) > 1:
            if game_type == "plinko" or game_type == "lotto":
                last_frame = frames[-1]
                
                extra_frames_count = 2 if game_type == "plinko" else 3
                
                for _ in range(extra_frames_count):
                    frames.append(last_frame)
                    durations.append(300)
            
            frames[0].save(
                output_path,
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=0,
                format="WEBP",
                quality=60,
                method=5,
                lossless=False,
                minimize_size=True,
            )
        else:
            frames[0].save(output_path, format="WEBP", quality=60, method=5)

        return output_path

    def generate_static(self, image_path, avatar_path, bg_path, user_info, output_path="output.webp"):
        base_img = Image.open(image_path).convert("RGBA")
        
        background_base = self._load_and_preprocess_image(bg_path, resize=base_img.size)
        bet_icon = self._load_and_preprocess_image(self.BET_ICON_PATH, resize=(25, 25))
        balance_icon = self._load_and_preprocess_image(self.BALANCE_ICON_PATH, resize=(25, 25))
        avatar = self._load_and_preprocess_image(avatar_path, resize=(self.avatar_size, self.avatar_size))

        try:
            font_small = ImageFont.truetype("DejaVuSans-Bold.ttf", base_img.size[0] // 32)
        except:
            font_small = ImageFont.load_default()

        avatar_mask = Image.new("L", (self.avatar_size, self.avatar_size), 0)
        mask_draw = ImageDraw.Draw(avatar_mask)
        mask_draw.rounded_rectangle((0, 0, self.avatar_size, self.avatar_size), radius=5, fill=255)

        bars = self._create_bars(user_info, font_small, bet_icon, balance_icon)
        avatar_bar = self._create_avatar_bar(avatar, avatar_mask, user_info, font_small)

        new_height = base_img.height + self.extra_bottom
        
        background_base_extended = Image.new("RGBA", (base_img.width, new_height))
        background_base_extended.paste(background_base, (0, 0))
        draw_bg = ImageDraw.Draw(background_base_extended)
        
        draw_bg.rectangle(
            [0, base_img.height, base_img.width, new_height], 
            fill=(30, 30, 30, 255)
        )
        
        final_img = Image.new("RGBA", (base_img.width, new_height))
        final_img.paste(background_base_extended, (0, 0))
        final_img.paste(base_img, (0, 0), base_img)
        
        avatar_x = base_img.width - avatar_bar.width - 15
        avatar_y = new_height - avatar_bar.height - 5
        final_img.paste(avatar_bar, (avatar_x, avatar_y), avatar_bar)

        x = (base_img.width - sum([b.width for b in bars]) - avatar_bar.width - 30) // (len(bars) + 1)
        y = new_height - self.bar_height - 5
        for b in bars:
            final_img.paste(b, (x, y), b)
            x += b.width + 10

        final_img.save(output_path, format="WEBP")
        return output_path
    
    def generate_last_frame_static(self, anim_path, avatar_path, bg_path, user_info_after, output_path):
        img = Image.open(anim_path)

        if getattr(img, "is_animated", False):
            img.seek(img.n_frames - 1)

        base_frame = img.convert("RGBA")

        background_base = self._load_and_preprocess_image(bg_path, resize=base_frame.size)

        bet_icon = self._load_and_preprocess_image(self.BET_ICON_PATH, resize=(25, 25))
        balance_icon = self._load_and_preprocess_image(self.BALANCE_ICON_PATH, resize=(25, 25))

        avatar = self._load_and_preprocess_image(avatar_path, resize=(self.avatar_size, self.avatar_size))

        try:
            font_small = ImageFont.truetype("DejaVuSans-Bold.ttf", base_frame.size[0] // 26)
            font_result = ImageFont.truetype("DejaVuSans-Bold.ttf", base_frame.size[0] // 10)
        except:
            font_small = font_result = ImageFont.load_default()

        avatar_mask = Image.new("L", (self.avatar_size, self.avatar_size), 0)
        mask_draw = ImageDraw.Draw(avatar_mask)
        mask_draw.rounded_rectangle((0, 0, self.avatar_size, self.avatar_size), radius=5, fill=255)

        bars = self._create_bars(user_info_after, font_small, bet_icon, balance_icon)
        avatar_bar = self._create_avatar_bar(avatar, avatar_mask, user_info_after, font_small)

        new_height = base_frame.height + self.extra_bottom
        final_img = Image.new("RGBA", (base_frame.width, new_height))
        final_img.paste(background_base, (0, 0))

        draw_bg = ImageDraw.Draw(final_img)
        draw_bg.rectangle([0, base_frame.height, base_frame.width, new_height], fill=(30, 30, 30, 255))

        final_img.paste(base_frame, (0, 0), base_frame)

        avatar_x = base_frame.width - avatar_bar.width - 15
        avatar_y = new_height - avatar_bar.height - 5
        final_img.paste(avatar_bar, (avatar_x, avatar_y), avatar_bar)

        x = (base_frame.width - sum([b.width for b in bars]) - avatar_bar.width - 30) // (len(bars) + 1)
        y = new_height - self.bar_height - 5
        for b in bars:
            final_img.paste(b, (x, y), b)
            x += b.width + 10

        win_value = user_info_after["win"]
        if win_value > 0:
            label, color = "Win:", (0, 255, 0, 255)
        elif win_value < 0:
            label, color = "Lose:", (255, 0, 0, 255)
        else:
            label, color = "Win:", (200, 200, 200, 255)

        win_text = f"{label} {abs(win_value)}$"
        win_text_width = self._get_text_width(win_text, font_result)
        x_center = (base_frame.width - win_text_width) // 2
        y_center = (base_frame.height - (font_result.getbbox(win_text)[3] - font_result.getbbox(win_text)[1])) // 2

        draw_center = ImageDraw.Draw(final_img)
        draw_center.text(
            (x_center, y_center),
            win_text,
            font=font_result,
            fill=color,
            stroke_width=1,
            stroke_fill=(0, 0, 0, 255)
        )

        final_img.save(output_path, format="WEBP")
        return output_path