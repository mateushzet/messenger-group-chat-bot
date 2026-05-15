import random
from datetime import datetime, timedelta
import os

from PIL import Image, ImageDraw

from base_game_plugin import BaseGamePlugin
from utils import _get_unique_id


CORE_WEEKLY_QUESTS = [

    ("colors_wheel", "Colors Wheel", 700),
    ("colors_wheel_800", "Colors Wheel", 800),
    ("colors_wheel_1000", "Colors Wheel", 1000),
    ("colors_wheel_1600", "Colors Wheel", 1600),
    ("colors_wheel_2000", "Colors Wheel", 2000),

    ("blackjack_300", "Blackjack", 300),
    ("blackjack_600", "Blackjack", 600),
    ("blackjack_700", "Blackjack", 700),
    ("blackjack_1200", "Blackjack", 1200),
    ("blackjack_1800", "Blackjack", 1800),

    ("plinko_400", "Plinko", 400),
    ("plinko_800", "Plinko", 800),
    ("plinko_1000", "Plinko", 1000),
    ("plinko_1600", "Plinko", 1600),
    ("plinko_2000", "Plinko", 2000),

    ("case_750", "Case", 750),
    ("case_1000", "Case", 1000),
    ("case_1500", "Case", 1500),
    ("case_2000", "Case", 2000),

    ("crash_750", "Crash", 750),
    ("crash_1000", "Crash", 1000),
    ("crash_1500", "Crash", 1500),
    ("crash_2000", "Crash", 2000),

    ("dice_750", "Dice", 750),
    ("dice_1000", "Dice", 1000),
    ("dice_1500", "Dice", 1500),
    ("dice_2000", "Dice", 2000),

    ("hilo_750", "Hi-Lo", 750),
    ("hilo_1000", "Hi-Lo", 1000),
    ("hilo_1500", "Hi-Lo", 1500),
    ("hilo_2000", "Hi-Lo", 2000),

    ("lotto_50", "Lotto", 50),
    ("lotto_100", "Lotto", 100),
    ("lotto_200", "Lotto", 200),
    ("lotto_400", "Lotto", 400),

    ("mines_750", "Mines", 750),
    ("mines_1000", "Mines", 1000),
    ("mines_1500", "Mines", 1500),
    ("mines_2000", "Mines", 2000),

    ("roulette_750", "Roulette", 750),
    ("roulette_1000", "Roulette", 1000),
    ("roulette_1500", "Roulette", 1500),
    ("roulette_2000", "Roulette", 2000),

    ("slots_500", "Slots", 500),
    ("slots_800", "Slots", 800),
    ("slots_1000", "Slots", 1000),
    ("slots_1600", "Slots", 1600),

    ("snakes_500", "snakes", 500),
    ("snakes_800", "snakes", 800),
    ("snakes_1000", "snakes", 1000),
    ("snakes_1600", "snakes", 1600),
]


class WeeklyQuestManager:
    REWARD = 1000
    DEFAULT_TARGET = 700
    MAIN_COUNT = 3

    def __init__(self):
        self.quests = {}
        self.variant_data = {}
        self.base_variants = {}
        self._ensure_core_quests()

    def _current_week_start(self):
        today = datetime.now().date()
        return today - timedelta(days=today.weekday())

    def register_quest(self, game_key, label=None, target=None):
        if not game_key:
            return
        base = self._base_game_key(game_key)
        if target is None:
            target = self.DEFAULT_TARGET
        if target <= 0:
            return
        if not label:
            label = base.replace("_", " ").title()

        base_entry = self.quests.get(base)
        if base_entry:
            if target > base_entry["target"]:
                base_entry["target"] = target
            if base_entry.get("label") != label:
                base_entry["label"] = label
        else:
            self.quests[base] = {"label": label, "target": target}

        self.variant_data[game_key] = {"label": label, "target": target, "base": base}
        variants = self.base_variants.setdefault(base, [])
        if game_key not in variants:
            variants.append(game_key)

    def _ensure_core_quests(self):
        for game_key, label, target in CORE_WEEKLY_QUESTS:
            self.register_quest(game_key, label, target)

    def _base_game_key(self, game_key):
        return game_key.split("_", 1)[0] if "_" in game_key else game_key

    def _normalize_progress(self, existing_progress):
        normalized = {base: 0 for base in self.quests}
        if not existing_progress:
            return normalized

        for key, value in existing_progress.items():
            base = self._base_game_key(key)
            if base not in normalized:
                continue
            try:
                numeric = int(value)
            except (TypeError, ValueError):
                continue
            normalized[base] = max(normalized.get(base, 0), numeric)

        return normalized

    def _pick_random_active(self):
        available_bases = [base for base, variants in self.base_variants.items() if variants]
        if not available_bases:
            return []

        count = min(self.MAIN_COUNT, len(available_bases))
        selected_bases = random.sample(available_bases, count)

        active = []
        for base in selected_bases:
            variants = self.base_variants.get(base, [])
            if variants:
                active.append(random.choice(variants))

        return active

    def _ensure_weekly(self, cache, user_id):
        if not cache:
            return None, None

        user = cache.get_user(user_id)
        if not user:
            return None, None

        week_start = self._current_week_start()
        week_key = week_start.isoformat()
        weekly = user.get("weekly_quests")

        if not weekly or weekly.get("week_start") != week_key:
            weekly = {
                "week_start": week_key,
                "progress": {game: 0 for game in self.quests},
                "claimed": False
            }
            weekly["active_quests"] = self._pick_random_active()
            user["weekly_quests"] = weekly
            cache.update_user(user_id, weekly_quests=weekly)
            return user, weekly

        progress = weekly.get("progress", {})
        normalized = self._normalize_progress(progress)
        updated = normalized != progress
        if updated:
            weekly["progress"] = normalized
            user["weekly_quests"] = weekly
            cache.update_user(user_id, weekly_quests=weekly)

        if "active_quests" not in weekly or not weekly["active_quests"]:
            weekly["active_quests"] = self._pick_random_active()
            user["weekly_quests"] = weekly
            cache.update_user(user_id, weekly_quests=weekly)

        return user, weekly

    def record_win(self, cache, user_id, game_key, amount):
        if amount <= 0 or not cache:
            return
        base = self._base_game_key(game_key)
        if base not in self.quests:
            self.register_quest(base, target=self.DEFAULT_TARGET)

        user, weekly = self._ensure_weekly(cache, user_id)
        if not weekly:
            return

        progress = weekly.get("progress", {})
        target = self.quests.get(base, {}).get("target", 0)
        current = progress.get(base, 0)
        addition = int(round(amount))
        if addition <= 0:
            return

        new_value = min(target, current + addition)
        if new_value == current:
            return

        progress[base] = new_value
        weekly["progress"] = progress
        user["weekly_quests"] = weekly
        cache.update_user(user_id, weekly_quests=weekly)

    def get_status(self, cache, user_id):
        user, weekly = self._ensure_weekly(cache, user_id)
        if not weekly:
            return None

        active = weekly.get("active_quests", self._pick_random_active())
        progress = weekly.get("progress", {})
        variant_progress = {}
        targets = {}
        labels = {}
        completed_count = 0
        for variant in active:
            entry = self.variant_data.get(variant, {})
            target = entry.get("target", 0)
            label = entry.get("label", variant.title())
            base = entry.get("base")
            current = progress.get(base, 0)
            variant_progress[variant] = current
            targets[variant] = target
            labels[variant] = label
            if target and current >= target:
                completed_count += 1
        completed_all = completed_count == len(targets)
        week_key = self._current_week_start().isoformat()
        skip_available = weekly.get("last_rotated_week") != week_key

        return {
            "week_start": weekly.get("week_start"),
            "progress": variant_progress,
            "targets": targets,
            "labels": labels,
            "active_quests": active,
            "claimed": weekly.get("claimed", False),
            "skip_available": skip_available,
            "completed_all": completed_all,
            "can_claim": completed_all and not weekly.get("claimed", False),
            "reward": self.REWARD,
            "completed_count": completed_count
        }

    def claim_reward(self, cache, user_id):
        user, weekly = self._ensure_weekly(cache, user_id)
        if not weekly or not user:
            return False, "Weekly data missing"

        if weekly.get("claimed", False):
            return False, "Weekly reward already claimed"

        progress = weekly.get("progress", {})
        active = weekly.get("active_quests", self._pick_random_active())
        if not active:
            active = self._pick_random_active()

        for variant in active:
            entry = self.variant_data.get(variant, {})
            target = entry.get("target")
            base = entry.get("base")
            if not target or not base:
                continue
            if progress.get(base, 0) < target:
                return False, "Complete all weekly tasks first"

        balance = user.get("balance", 0) + self.REWARD
        weekly["claimed"] = True
        user["weekly_quests"] = weekly
        cache.update_user(user_id, balance=balance, weekly_quests=weekly)
        return True, self.REWARD

    def rotate_one_quest(self, cache, user_id, slot_index=None):
        user, weekly = self._ensure_weekly(cache, user_id)
        if not weekly:
            return False, "Weekly data missing"

        week_key = self._current_week_start().isoformat()
        if weekly.get("last_rotated_week") == week_key:
            return False, "Skip already done this week"

        active = weekly.get("active_quests", self._pick_random_active())
        if not active:
            active = self._pick_random_active()
        if not active:
            return False, "No active quests to rotate"

        if slot_index is not None:
            if slot_index < 0 or slot_index >= len(active):
                return False, f"Skip slot must be between 1 and {len(active)}."
            replace_idx = slot_index
        else:
            replace_idx = random.randrange(len(active))

        old_choice = active[replace_idx]

        excluded_bases = {
            self._base_game_key(active[i]) for i in range(len(active)) if i != replace_idx
        }
        pool = [
            key for key in self.variant_data
            if key != old_choice and self._base_game_key(key) not in excluded_bases
        ]

        if not pool:
            pool = [
                key for key in self.variant_data
                if key not in active and key != old_choice
            ]

        if not pool:
            pool = [key for key in self.variant_data if key != old_choice]

        if not pool:
            return False, "No quests available to swap"

        new_choice = random.choice(pool)

        active[replace_idx] = new_choice
        weekly["active_quests"] = active
        weekly["last_rotated_week"] = week_key
        cache.update_user(user_id, weekly_quests=weekly)

        return True, (old_choice, new_choice, replace_idx)


weekly_manager = WeeklyQuestManager()


def register_weekly_quest(game_key, label=None, target=None):
    weekly_manager.register_quest(game_key, label, target)


def record_weekly_win(cache, user_id, game_key, amount):
    weekly_manager.record_win(cache, user_id, game_key, amount)


class WeeklyPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="weekly")
        self.reward_amount = weekly_manager.REWARD

    def _render_gradient_bar(self, width: int, height: int, left_rgba, right_rgba, radius: int = 10) -> Image.Image:
        width = max(1, int(width))
        height = max(1, int(height))

        base = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        px = base.load()

        lr, lg, lb, la = left_rgba
        rr, rg, rb, ra = right_rgba

        denom = max(1, width - 1)
        for x in range(width):
            t = x / denom
            r = int(lr + (rr - lr) * t)
            g = int(lg + (rg - lg) * t)
            b = int(lb + (rb - lb) * t)
            a = int(la + (ra - la) * t)
            for y in range(height):
                px[x, y] = (r, g, b, a)

        highlight = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        hdraw = ImageDraw.Draw(highlight)
        hdraw.rounded_rectangle([0, 0, width, max(1, height // 2)], radius=radius, fill=(255, 255, 255, 22))
        base = Image.alpha_composite(base, highlight)

        mask = Image.new("L", (width, height), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([0, 0, width, height], radius=radius, fill=255)
        base.putalpha(mask)
        return base

    def _format_week_dates(self, iso_start):
        week_start = iso_start or ""
        week_end = ""
        try:
            start_date = datetime.fromisoformat(iso_start).date()
            end_date = start_date + timedelta(days=6)
            week_start = start_date.strftime("%Y-%m-%d")
            week_end = end_date.strftime("%Y-%m-%d")
        except Exception:
            week_end = week_start
        return week_start, week_end

    def _build_status_message(self, status):
        if not status:
            return "Weekly quest data is unavailable."

        week_start, week_end = self._format_week_dates(status.get("week_start"))
        lines = [
            f"Weekly Quests ({week_start} - {week_end})",
            ""
        ]

        active_keys = status.get("active_quests", [])
        if active_keys:
            active_labels = [
                status.get("labels", {}).get(key, key.title()) for key in active_keys
            ]
            lines.append(f"Active quests: {', '.join(active_labels)}")
            if status.get("skip_available", True):
                lines.append("Skip one quest once/week with `/weekly skip <slot>` (1-3).")
            lines.append("")

        for game_key, label in status.get("labels", {}).items():
            target = status.get("targets", {}).get(game_key, 0)
            progress = status.get("progress", {}).get(game_key, 0)
            percent = int(min(100, (progress / target) * 100)) if target else 100
            status_mark = "DONE" if progress >= target else "PENDING"
            lines.append(f"- {label}: {progress}/{target} ({percent}%) {status_mark}")

        lines.append("")
        total_active = len(status.get("targets", {}))
        lines.append(f"Completed: {status.get('completed_count', 0)}/{total_active}")

        if status.get("can_claim"):
            lines.append(f"Reward ready: +{self.reward_amount} coins. Claim it with /weekly claim")
        elif status.get("claimed"):
            lines.append("Reward already claimed. Reset happens every Monday.")
        else:
            lines.append(f"Finish every quest to unlock +{self.reward_amount} coins.")

        return "\n".join(lines)

    def _load_game_icon(self, game_key: str, size: int = 64) -> Image.Image:
        base_key = weekly_manager._base_game_key(game_key or "")
        icon_path = self.get_asset_path("icons", f"{base_key}.png")

        try:
            if os.path.exists(icon_path):
                icon = Image.open(icon_path).convert("RGBA")
                return icon.resize((size, size), Image.Resampling.LANCZOS)
        except Exception:
            pass

        icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(icon)
        draw.ellipse([2, 2, size - 2, size - 2], fill=(60, 60, 80, 230))

        letter = (base_key[:1] or "?").upper()
        letter_img = self.text_renderer.render_text(
            text=letter,
            font_size=max(18, int(size * 0.45)),
            color=(255, 255, 255, 255),
            stroke_width=2,
            stroke_color=(0, 0, 0, 255),
            shadow=True,
        )
        icon.alpha_composite(
            letter_img,
            ((size - letter_img.width) // 2, (size - letter_img.height) // 2),
        )
        return icon

    def _generate_weekly_status_image(
        self,
        status: dict,
        username: str,
        background_path: str,
        output_folder: str,
        notice: dict | None = None,
    ) -> str | None:
        try:
            IMAGE_WIDTH = 600
            PADDING_X = 20
            HEADER_Y = 14

            week_start, week_end = self._format_week_dates(status.get("week_start"))
            header_text = f"Weekly Quests ({week_start} - {week_end})"

            title_img = self.text_renderer.render_text(
                text=header_text,
                font_size=26,
                color=(255, 255, 255, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
            )

            rows = []
            active_keys = status.get("active_quests", []) or list(status.get("labels", {}).keys())
            active_keys = active_keys[:3]

            for game_key in active_keys:
                label = status.get("labels", {}).get(game_key, game_key.title())
                target = int(status.get("targets", {}).get(game_key, 0) or 0)
                progress = int(status.get("progress", {}).get(game_key, 0) or 0)

                if target <= 0:
                    percent = 100
                else:
                    percent = int(max(0, min(100, (progress / target) * 100)))

                rows.append(
                    {
                        "game_key": game_key,
                        "label": label,
                        "target": target,
                        "progress": progress,
                        "percent": percent,
                        "done": target > 0 and progress >= target,
                    }
                )

            ROW_H = 92
            ROW_GAP = 12
            BODY_TOP = HEADER_Y + title_img.height + 14
            BODY_H = len(rows) * ROW_H + max(0, len(rows) - 1) * ROW_GAP

            footer_lines = []
            completed_count = int(status.get("completed_count", 0) or 0)
            total_active = len(status.get("targets", {}) or {}) or len(rows) or 3
            footer_lines.append(f"Completed: {completed_count}/{total_active}")
            if status.get("skip_available", False):
                footer_lines.append("Skip available: /weekly skip <slot> (1-3)")
            if status.get("can_claim"):
                footer_lines.append(f"Reward ready: +{self.reward_amount} coins")
            elif status.get("claimed"):
                footer_lines.append("Reward already claimed. Reset happens every Monday.")
            else:
                footer_lines.append(f"Finish every quest to unlock +{self.reward_amount} coins.")

            footer_imgs = [
                self.text_renderer.render_text(
                    text=line,
                    font_size=16,
                    color=(240, 240, 240, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255),
                    shadow=True,
                )
                for line in footer_lines
            ]
            footer_h = sum(img.height for img in footer_imgs) + (len(footer_imgs) - 1) * 4

            nick_img = self.text_renderer.render_text(
                text=username,
                font_size=16,
                color=(255, 255, 255, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
            )

            IMAGE_H = BODY_TOP + BODY_H + 18 + footer_h + 14 + nick_img.height + 18

            bg = Image.open(background_path).convert("RGB").resize((IMAGE_WIDTH, IMAGE_H), Image.Resampling.LANCZOS)
            canvas = bg.convert("RGBA")
            draw = ImageDraw.Draw(canvas)

            canvas.alpha_composite(title_img, ((IMAGE_WIDTH - title_img.width) // 2, HEADER_Y))

            dark = (8, 8, 12, 245)
            row_x = PADDING_X
            row_w = IMAGE_WIDTH - PADDING_X * 2
            icon_size = 64
            bar_h = 26

            y = BODY_TOP
            for row in rows:
                draw.rounded_rectangle(
                    [row_x, y, row_x + row_w, y + ROW_H],
                    radius=18,
                    fill=dark,
                )

                icon = self._load_game_icon(row["game_key"], size=icon_size)
                icon_x = row_x + 14
                icon_y = y + (ROW_H - icon_size) // 2
                canvas.alpha_composite(icon, (icon_x, icon_y))

                text_x = icon_x + icon_size + 14
                label_img = self.text_renderer.render_text(
                    text=str(row["label"]),
                    font_size=18,
                    color=(255, 255, 255, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255),
                    shadow=True,
                )
                canvas.alpha_composite(label_img, (text_x, y + 14))

                bar_x = text_x
                bar_y = y + ROW_H - 40
                bar_w = row_x + row_w - 16 - bar_x

                draw.rounded_rectangle(
                    [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                    radius=8,
                    fill=(24, 24, 32, 255),
                )

                fill_w = int(bar_w * (row["percent"] / 100.0))
                if fill_w > 0:
                    p = int(row["percent"])
                    if p < 25:
                        left, right = (230, 70, 70, 255), (200, 45, 45, 255)
                    elif p < 50:
                        left, right = (240, 140, 60, 255), (215, 110, 40, 255)
                    elif p < 75:
                        left, right = (245, 210, 70, 255), (230, 185, 55, 255)
                    elif p < 100:
                        left, right = (245, 210, 70, 255), (230, 185, 55, 255)
                    else:
                        left, right = (80, 200, 110, 255), (55, 170, 85, 255)

                    fill_img = self._render_gradient_bar(fill_w, bar_h, left, right, radius=10)
                    canvas.alpha_composite(fill_img, (bar_x, bar_y))

                if row["target"] > 0:
                    bar_text = f"{row['progress']}/{row['target']}"
                else:
                    bar_text = str(row["progress"])

                bar_text_img = self.text_renderer.render_text(
                    text=bar_text,
                    font_size=13,
                    color=(255, 255, 255, 255),
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 255),
                    shadow=False,
                )
                canvas.alpha_composite(
                    bar_text_img,
                    (
                        bar_x + (bar_w - bar_text_img.width) // 2,
                        bar_y + (bar_h - bar_text_img.height) // 2,
                    ),
                )

                y += ROW_H + ROW_GAP

            footer_y = BODY_TOP + BODY_H + 18
            x_center = IMAGE_WIDTH // 2
            cur_y = footer_y
            for img in footer_imgs:
                canvas.alpha_composite(img, (x_center - img.width // 2, cur_y))
                cur_y += img.height + 4

            sep_y = cur_y + 8
            draw.line([(0, sep_y), (IMAGE_WIDTH, sep_y)], fill=(30, 30, 40, 220), width=2)
            nick_y = sep_y + 12
            canvas.alpha_composite(nick_img, ((IMAGE_WIDTH - nick_img.width) // 2, nick_y))

            if notice:
                headline = str(notice.get("headline") or "")
                subline = str(notice.get("subline") or "")

                if headline:
                    headline_img = self.text_renderer.render_text(
                        text=headline,
                        font_size=56,
                        color=(255, 255, 255, 210),
                        stroke_width=4,
                        stroke_color=(0, 0, 0, 255),
                        shadow=True,
                        shadow_color=(0, 0, 0, 200),
                        shadow_offset=(3, 3),
                    )
                else:
                    headline_img = None

                if subline:
                    subline_img = self.text_renderer.render_text(
                        text=subline,
                        font_size=40,
                        color=(255, 255, 255, 210),
                        stroke_width=3,
                        stroke_color=(0, 0, 0, 255),
                        shadow=True,
                        shadow_color=(0, 0, 0, 200),
                        shadow_offset=(3, 3),
                    )
                else:
                    subline_img = None

                block_h = 0
                if headline_img:
                    block_h += headline_img.height
                if subline_img:
                    block_h += (14 if block_h else 0) + subline_img.height

                center_y = (canvas.height - block_h) // 2
                cur_y = center_y
                if headline_img:
                    canvas.alpha_composite(headline_img, ((IMAGE_WIDTH - headline_img.width) // 2, cur_y))
                    cur_y += headline_img.height + 14
                if subline_img:
                    canvas.alpha_composite(subline_img, ((IMAGE_WIDTH - subline_img.width) // 2, cur_y))

            output_path = os.path.join(output_folder, f"weekly_{username}_{_get_unique_id()}.png")
            canvas.convert("RGB").save(output_path, "PNG", quality=95)
            return output_path
        except Exception:
            return None

    def _respond(self, sender, file_queue, message, cache, user_id, status: dict | None = None, notice: dict | None = None):
        if status:
            background_path = None
            if cache and user_id and hasattr(cache, "get_background_path"):
                background_path = cache.get_background_path(user_id)

            if not background_path or not os.path.exists(background_path):
                background_path = self.get_asset_path("backgrounds", "default-bg.png")

            if background_path and os.path.exists(background_path):
                image_path = self._generate_weekly_status_image(
                    status=status,
                    username=sender,
                    background_path=background_path,
                    output_folder=self.results_folder,
                    notice=notice,
                )
                if image_path:
                    file_queue.put(image_path)
                    return

        self.send_message_image(sender, file_queue, message, "Weekly Quest", cache, user_id)

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        if error:
            self._respond(sender, file_queue, "You must be registered before using weekly quests.", cache, user_id)
            return ""

        if args and args[0].lower() in {"skip", "s", "rotate", "r"}:
            slot_index = None
            if len(args) > 1:
                try:
                    slot_index = int(args[1]) - 1
                except ValueError:
                    self._respond(sender, file_queue, "Skip slot must be a number (1-3).", cache, user_id)
                    return ""

            success, payload = weekly_manager.rotate_one_quest(cache, user_id, slot_index=slot_index)

            status = weekly_manager.get_status(cache, user_id)
            message = self._build_status_message(status)
            if not success and payload:
                message = f"{payload}\n\n{message}"
            self._respond(sender, file_queue, message, cache, user_id, status=status)
            return ""

        if args and args[0].lower() in {"claim", "c"}:
            status = weekly_manager.get_status(cache, user_id)
            message = self._build_status_message(status)
            self._respond(sender, file_queue, message, cache, user_id, status=status)
            return ""

        status = weekly_manager.get_status(cache, user_id)
        auto_claimed = False
        auto_claim_amount = None
        if status and status.get("can_claim"):
            success, payload = weekly_manager.claim_reward(cache, user_id)
            if success:
                auto_claimed = True
                auto_claim_amount = payload

        if auto_claimed:
            status = weekly_manager.get_status(cache, user_id)
        message = self._build_status_message(status)
        notice = None
        if auto_claimed and auto_claim_amount is not None:
            message = f"Auto-claimed weekly reward: +{auto_claim_amount} coins.\n\n{message}"
            notice = {"headline": "REWARD CLAIMED", "subline": f"+{auto_claim_amount} COINS"}
        self._respond(sender, file_queue, message, cache, user_id, status=status, notice=notice)
        return ""


def register():
    plugin = WeeklyPlugin()
    return {
        "name": "weekly",
        "aliases": ["/weekly", "/wq"],
        "description": (
            "Track weekly quests (3 active quests). Use `/weekly` to view status, "
            "and `/weekly skip <slot>` (or `/weekly rotate <slot>`) once per week to swap one active quest (1-3) for another random one."
        ),
        "execute": plugin.execute_game
    }
