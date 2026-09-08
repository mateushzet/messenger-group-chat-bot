import calendar
import os
import random
from datetime import date, datetime

from PIL import Image, ImageDraw

from base_game_plugin import BaseGamePlugin
from utils import _get_unique_id


MONTHLY_QUESTS = {
    "blackjack": ("Blackjack", 2000),
    "case": ("Case", 3000),
    "colors": ("Colors Wheel", 3000),
    "crash": ("Crash", 3000),
    "dice": ("Dice", 1000),
    "fifa": ("FIFA Pack", 500),
    "hilo": ("Hi-Lo", 1500),
    "jackpot": ("Jackpot", 200),
    "keno": ("Keno", 500),
    "lotto": ("Lotto", 500),
    "mines": ("Mines", 1500),
    "piggy": ("Piggy", 200),
    "plinko": ("Plinko", 3000),
    "poker": ("Poker", 200),
    "roulette": ("Roulette", 3000),
    "slots": ("Slots", 3000),
    "snakes": ("Snakes", 2000),
    "tree": ("Tree", 100),
}

MAX_ACTIVE_QUESTS = 15


class MonthlyQuestManager:
    REWARD = 2500

    def __init__(self):
        self.quests = {
            game_key: {"label": label, "target": target}
            for game_key, (label, target) in MONTHLY_QUESTS.items()
        }

    def _base_game_key(self, game_key):
        return game_key.split("_", 1)[0] if "_" in game_key else game_key

    def _current_month_start(self):
        today = datetime.now().date()
        return date(today.year, today.month, 1)

    def _select_active_quests(self):
        all_keys = list(self.quests.keys())
        random.shuffle(all_keys)
        return all_keys[:MAX_ACTIVE_QUESTS]

    def _normalize_progress(self, existing_progress, active_quests):
        normalized = {game_key: 0 for game_key in active_quests}
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

    def _ensure_monthly(self, cache, user_id):
        if not cache:
            return None, None

        user = cache.get_user(user_id)
        if not user:
            return None, None

        month_key = self._current_month_start().isoformat()
        monthly = user.get("monthly_quests")

        if not monthly or monthly.get("month_start") != month_key:
            active_quests = self._select_active_quests()
            monthly = {
                "month_start": month_key,
                "active_quests": active_quests,
                "progress": {game_key: 0 for game_key in active_quests},
                "claimed": False,
            }
            user["monthly_quests"] = monthly
            cache.update_user(user_id, monthly_quests=monthly)
            return user, monthly

        active_quests = monthly.get("active_quests", [])
        if not active_quests:
            active_quests = self._select_active_quests()
            monthly["active_quests"] = active_quests
            monthly["progress"] = {game_key: monthly.get("progress", {}).get(game_key, 0) for game_key in active_quests}
            user["monthly_quests"] = monthly
            cache.update_user(user_id, monthly_quests=monthly)

        progress = monthly.get("progress", {})
        normalized = self._normalize_progress(progress, active_quests)
        if normalized != progress:
            monthly["progress"] = normalized
            user["monthly_quests"] = monthly
            cache.update_user(user_id, monthly_quests=monthly)

        return user, monthly

    def record_win(self, cache, user_id, game_key, amount):
        if amount <= 0 or not cache:
            return

        base = self._base_game_key(game_key)
        user, monthly = self._ensure_monthly(cache, user_id)
        if not monthly:
            return

        active_quests = monthly.get("active_quests", [])
        if base not in active_quests:
            return

        target = self.quests[base]["target"]
        progress = monthly.get("progress", {})
        current = int(progress.get(base, 0) or 0)
        addition = int(round(amount))
        if addition <= 0:
            return

        new_value = min(target, current + addition)
        if new_value == current:
            return

        progress[base] = new_value
        monthly["progress"] = progress
        user["monthly_quests"] = monthly
        cache.update_user(user_id, monthly_quests=monthly)

    def skip_quest(self, cache, user_id, quest_to_skip):
        user, monthly = self._ensure_monthly(cache, user_id)
        if not monthly or not user:
            return False, "Monthly data missing"

        if monthly.get("claimed", False):
            return False, "Cannot skip quests after claiming reward"

        active_quests = monthly.get("active_quests", [])
        
        if quest_to_skip.isdigit():
            idx = int(quest_to_skip) - 1
            if idx < 0 or idx >= len(active_quests):
                return False, f"Invalid quest number. Use 1-{len(active_quests)}"
            quest_to_skip = active_quests[idx]
        elif quest_to_skip not in active_quests:
            return False, f"Quest '{quest_to_skip}' is not active"

        progress = monthly.get("progress", {})
        if progress.get(quest_to_skip, 0) >= self.quests[quest_to_skip]["target"]:
            return False, "Cannot skip a completed quest"

        available_quests = [q for q in self.quests.keys() if q not in active_quests]
        if not available_quests:
            return False, "No other quests available"

        new_quest = random.choice(available_quests)
        
        active_quests.remove(quest_to_skip)
        active_quests.append(new_quest)
        
        if quest_to_skip in progress:
            del progress[quest_to_skip]
        progress[new_quest] = 0
        
        monthly["active_quests"] = active_quests
        monthly["progress"] = progress
        user["monthly_quests"] = monthly
        cache.update_user(user_id, monthly_quests=monthly)
        
        return True, f"Replaced '{quest_to_skip}' with '{new_quest}'"

    def get_status(self, cache, user_id):
        user, monthly = self._ensure_monthly(cache, user_id)
        if not monthly:
            return None

        active_quests = monthly.get("active_quests", [])
        progress = monthly.get("progress", {})
        targets = {}
        labels = {}
        completed = {}
        completed_count = 0

        for game_key in active_quests:
            entry = self.quests[game_key]
            target = int(entry["target"])
            current = int(progress.get(game_key, 0) or 0)
            is_done = current >= target

            targets[game_key] = target
            labels[game_key] = entry["label"]
            completed[game_key] = is_done
            if is_done:
                completed_count += 1

        completed_all = completed_count == len(active_quests)

        return {
            "month_start": monthly.get("month_start"),
            "active_quests": active_quests,
            "all_quests_count": len(self.quests),
            "progress": progress,
            "targets": targets,
            "labels": labels,
            "completed": completed,
            "claimed": monthly.get("claimed", False),
            "completed_all": completed_all,
            "can_claim": completed_all and not monthly.get("claimed", False),
            "reward": self.REWARD,
            "completed_count": completed_count,
            "total_count": len(active_quests),
        }

    def claim_reward(self, cache, user_id):
        user, monthly = self._ensure_monthly(cache, user_id)
        if not monthly or not user:
            return False, "Monthly data missing"

        if monthly.get("claimed", False):
            return False, "Monthly reward already claimed"

        active_quests = monthly.get("active_quests", [])
        progress = monthly.get("progress", {})
        
        for game_key in active_quests:
            if int(progress.get(game_key, 0) or 0) < int(self.quests[game_key]["target"]):
                return False, "Complete all active quests first"

        balance = user.get("balance", 0) + self.REWARD
        monthly["claimed"] = True
        user["monthly_quests"] = monthly
        cache.update_user(user_id, balance=balance, monthly_quests=monthly)
        return True, self.REWARD


monthly_manager = MonthlyQuestManager()


def record_monthly_win(cache, user_id, game_key, amount):
    monthly_manager.record_win(cache, user_id, game_key, amount)


class MonthlyPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="monthly")
        self.reward_amount = monthly_manager.REWARD

    def _render_gradient_bar(self, width: int, height: int, left_rgba, right_rgba, radius: int = 8) -> Image.Image:
        width = max(1, int(width))
        height = max(1, int(height))
        base = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        px = base.load()

        lr, lg, lb, la = left_rgba
        rr, rg, rb, ra = right_rgba
        denom = max(1, width - 1)
        for x in range(width):
            t = x / denom
            color = (
                int(lr + (rr - lr) * t),
                int(lg + (rg - lg) * t),
                int(lb + (rb - lb) * t),
                int(la + (ra - la) * t),
            )
            for y in range(height):
                px[x, y] = color

        highlight = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        hdraw = ImageDraw.Draw(highlight)
        hdraw.rounded_rectangle([0, 0, width, max(1, height // 2)], radius=radius, fill=(255, 255, 255, 20))
        base = Image.alpha_composite(base, highlight)

        mask = Image.new("L", (width, height), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([0, 0, width, height], radius=radius, fill=255)
        base.putalpha(mask)
        return base

    def _format_month_dates(self, iso_start):
        try:
            start_date = datetime.fromisoformat(iso_start).date()
            last_day = calendar.monthrange(start_date.year, start_date.month)[1]
            end_date = date(start_date.year, start_date.month, last_day)
            return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
        except Exception:
            month_start = iso_start or ""
            return month_start, month_start

    def _build_status_message(self, status):
        if not status:
            return "Monthly quest data is unavailable."

        month_start, month_end = self._format_month_dates(status.get("month_start"))
        lines = [
            f"Monthly Quests ({month_start} - {month_end})",
            "",
            f"Active quests: {status.get('total_count', 0)}/{status.get('all_quests_count', 0)}",
            "",
        ]

        for idx, game_key in enumerate(status.get("active_quests", []), 1):
            label = status.get("labels", {}).get(game_key, game_key.title())
            target = status.get("targets", {}).get(game_key, 0)
            progress = status.get("progress", {}).get(game_key, 0)
            percent = int(min(100, (progress / target) * 100)) if target else 100
            status_mark = "DONE" if progress >= target else "PENDING"
            lines.append(f"{idx}. {label}: {progress}/{target} ({percent}%) {status_mark}")

        lines.append("")
        lines.append(f"Completed: {status.get('completed_count', 0)}/{status.get('total_count', 0)}")
        lines.append("")
        lines.append("Skip a quest: /monthly skip <number> or /monthly skip <game>")

        if status.get("can_claim"):
            lines.append(f"Reward ready: +{self.reward_amount} coins. Claim it with /monthly claim")
        elif status.get("claimed"):
            lines.append("Reward already claimed. Reset happens on the first day of next month.")
        else:
            lines.append(f"Finish every active quest to unlock +{self.reward_amount} coins.")

        return "\n".join(lines)

    def _load_game_icon(self, game_key: str, size: int = 42) -> Image.Image:
        base_key = monthly_manager._base_game_key(game_key or "")
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
            font_size=max(16, int(size * 0.42)),
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

    def _generate_monthly_status_image(
        self,
        status: dict,
        username: str,
        background_path: str,
        output_folder: str,
        notice: dict | None = None,
    ) -> str | None:
        try:
            image_width = 640
            padding_x = 18
            header_y = 14
            row_h = 62
            row_gap = 7

            month_start, month_end = self._format_month_dates(status.get("month_start"))
            title_img = self.text_renderer.render_text(
                text=f"Monthly Quests ({month_start} - {month_end})",
                font_size=22,
                color=(255, 255, 255, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
            )

            info_text = f"Active: {status.get('total_count', 0)}/{status.get('all_quests_count', 0)}"
            info_img = self.text_renderer.render_text(
                text=info_text,
                font_size=14,
                color=(200, 200, 200, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
            )

            rows = []
            for idx, game_key in enumerate(status.get("active_quests", []), 1):
                label = status.get("labels", {}).get(game_key, game_key.title())
                target = int(status.get("targets", {}).get(game_key, 0) or 0)
                progress = int(status.get("progress", {}).get(game_key, 0) or 0)
                percent = 100 if target <= 0 else int(max(0, min(100, (progress / target) * 100)))
                rows.append({
                    "number": idx,
                    "game_key": game_key,
                    "label": label,
                    "target": target,
                    "progress": progress,
                    "percent": percent,
                })

            body_top = header_y + title_img.height + info_img.height + 8
            body_h = len(rows) * row_h + max(0, len(rows) - 1) * row_gap
            footer_lines = [
                f"Completed: {status.get('completed_count', 0)}/{status.get('total_count', 0)}",
            ]
            if status.get("can_claim"):
                footer_lines.append(f"Reward ready: +{self.reward_amount} coins")
            elif status.get("claimed"):
                footer_lines.append("Reward already claimed. Reset happens next month.")
            else:
                footer_lines.append(f"Finish all active quests to unlock +{self.reward_amount} coins.")

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
            footer_h = sum(img.height for img in footer_imgs) + max(0, len(footer_imgs) - 1) * 4

            nick_img = self.text_renderer.render_text(
                text=username,
                font_size=16,
                color=(255, 255, 255, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
            )

            skip_info = "To skip a quest, use: /monthly skip <number> or /monthly skip <game>"
            skip_img = self.text_renderer.render_text(
                text=skip_info,
                font_size=12,
                color=(180, 180, 180, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
            )

            image_h = body_top + body_h + 16 + footer_h + 12 + nick_img.height + 12 + skip_img.height + 16
            bg = Image.open(background_path).convert("RGB").resize((image_width, image_h), Image.Resampling.LANCZOS)
            canvas = bg.convert("RGBA")
            draw = ImageDraw.Draw(canvas)

            canvas.alpha_composite(title_img, ((image_width - title_img.width) // 2, header_y))
            canvas.alpha_composite(info_img, ((image_width - info_img.width) // 2, header_y + title_img.height + 2))

            row_x = padding_x
            row_w = image_width - padding_x * 2
            icon_size = 42
            bar_h = 18
            y = body_top

            for row in rows:
                draw.rounded_rectangle(
                    [row_x, y, row_x + row_w, y + row_h],
                    radius=12,
                    fill=(8, 8, 12, 238),
                )

                number_img = self.text_renderer.render_text(
                    text=str(row["number"]),
                    font_size=14,
                    color=(150, 150, 170, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255),
                )
                canvas.alpha_composite(number_img, (row_x + 8, y + 4))

                icon = self._load_game_icon(row["game_key"], size=icon_size)
                icon_x = row_x + 32
                icon_y = y + (row_h - icon_size) // 2
                canvas.alpha_composite(icon, (icon_x, icon_y))

                text_x = icon_x + icon_size + 12
                label_img = self.text_renderer.render_text(
                    text=str(row["label"]),
                    font_size=16,
                    color=(255, 255, 255, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255),
                    shadow=True,
                )
                canvas.alpha_composite(label_img, (text_x, y + 8))

                bar_x = text_x
                bar_y = y + row_h - 27
                bar_w = row_x + row_w - 12 - bar_x
                draw.rounded_rectangle(
                    [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                    radius=7,
                    fill=(24, 24, 32, 255),
                )

                fill_w = int(bar_w * (row["percent"] / 100.0))
                if fill_w > 0:
                    if row["percent"] < 35:
                        left, right = (230, 70, 70, 255), (200, 45, 45, 255)
                    elif row["percent"] < 70:
                        left, right = (245, 170, 65, 255), (220, 130, 45, 255)
                    elif row["percent"] < 100:
                        left, right = (245, 215, 75, 255), (230, 185, 55, 255)
                    else:
                        left, right = (80, 200, 110, 255), (55, 170, 85, 255)

                    fill_img = self._render_gradient_bar(fill_w, bar_h, left, right, radius=7)
                    canvas.alpha_composite(fill_img, (bar_x, bar_y))

                bar_text = f"{row['progress']}/{row['target']}" if row["target"] > 0 else str(row["progress"])
                bar_text_img = self.text_renderer.render_text(
                    text=bar_text,
                    font_size=12,
                    color=(255, 255, 255, 255),
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 255),
                )
                canvas.alpha_composite(
                    bar_text_img,
                    (
                        bar_x + (bar_w - bar_text_img.width) // 2,
                        bar_y + (bar_h - bar_text_img.height) // 2,
                    ),
                )

                y += row_h + row_gap

            cur_y = body_top + body_h + 16
            for img in footer_imgs:
                canvas.alpha_composite(img, ((image_width - img.width) // 2, cur_y))
                cur_y += img.height + 4

            sep_y = cur_y + 6
            draw.line([(0, sep_y), (image_width, sep_y)], fill=(30, 30, 40, 220), width=2)
            nick_y = sep_y + 10
            canvas.alpha_composite(nick_img, ((image_width - nick_img.width) // 2, nick_y))
            
            canvas.alpha_composite(skip_img, ((image_width - skip_img.width) // 2, nick_y + nick_img.height + 8))

            if notice:
                headline = str(notice.get("headline") or "")
                subline = str(notice.get("subline") or "")

                headline_img = self.text_renderer.render_text(
                    text=headline,
                    font_size=54,
                    color=(255, 255, 255, 215),
                    stroke_width=4,
                    stroke_color=(0, 0, 0, 255),
                    shadow=True,
                    shadow_color=(0, 0, 0, 200),
                    shadow_offset=(3, 3),
                ) if headline else None

                subline_img = self.text_renderer.render_text(
                    text=subline,
                    font_size=38,
                    color=(255, 255, 255, 215),
                    stroke_width=3,
                    stroke_color=(0, 0, 0, 255),
                    shadow=True,
                    shadow_color=(0, 0, 0, 200),
                    shadow_offset=(3, 3),
                ) if subline else None

                block_h = 0
                if headline_img:
                    block_h += headline_img.height
                if subline_img:
                    block_h += (12 if block_h else 0) + subline_img.height

                cur_y = (canvas.height - block_h) // 2
                if headline_img:
                    canvas.alpha_composite(headline_img, ((image_width - headline_img.width) // 2, cur_y))
                    cur_y += headline_img.height + 12
                if subline_img:
                    canvas.alpha_composite(subline_img, ((image_width - subline_img.width) // 2, cur_y))

            os.makedirs(output_folder, exist_ok=True)
            output_path = os.path.join(output_folder, f"monthly_{username}_{_get_unique_id()}.png")
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
                image_path = self._generate_monthly_status_image(
                    status=status,
                    username=sender,
                    background_path=background_path,
                    output_folder=self.results_folder,
                    notice=notice,
                )
                if image_path:
                    file_queue.put(image_path)
                    return

        self.send_message_image(sender, file_queue, message, "Monthly Quest", cache, user_id)

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        if error:
            self._respond(sender, file_queue, "You must be registered before using monthly quests.", cache, user_id)
            return ""

        if args:
            action = args[0].lower()
            
            if action in {"claim", "c"}:
                success, payload = monthly_manager.claim_reward(cache, user_id)
                status = monthly_manager.get_status(cache, user_id)
                message = self._build_status_message(status)
                notice = None
                if success:
                    message = f"Claimed monthly reward: +{payload} coins.\n\n{message}"
                    notice = {"headline": "REWARD CLAIMED", "subline": f"+{payload} COINS"}
                elif payload:
                    message = f"{payload}\n\n{message}"
                self._respond(sender, file_queue, message, cache, user_id, status=status, notice=notice)
                return ""
            
            elif action in {"skip", "reroll", "s"}:
                if len(args) < 2:
                    self._respond(sender, file_queue, "Usage: /monthly skip <number> or /monthly skip <game>", cache, user_id)
                    return ""
                
                quest_to_skip = args[1].lower()
                success, message = monthly_manager.skip_quest(cache, user_id, quest_to_skip)
                status = monthly_manager.get_status(cache, user_id)
                full_message = f"{message}\n\n{self._build_status_message(status)}"
                notice = None
                if success:
                    notice = {"headline": "", "subline": "Quest replaced"}
                self._respond(sender, file_queue, full_message, cache, user_id, status=status, notice=notice)
                return ""

        status = monthly_manager.get_status(cache, user_id)
        auto_claimed = False
        auto_claim_amount = None
        if status and status.get("can_claim"):
            success, payload = monthly_manager.claim_reward(cache, user_id)
            if success:
                auto_claimed = True
                auto_claim_amount = payload

        if auto_claimed:
            status = monthly_manager.get_status(cache, user_id)

        message = self._build_status_message(status)
        notice = None
        if auto_claimed and auto_claim_amount is not None:
            message = f"Auto-claimed monthly reward: +{auto_claim_amount} coins.\n\n{message}"
            notice = {"headline": "REWARD CLAIMED", "subline": f"+{auto_claim_amount} COINS"}

        self._respond(sender, file_queue, message, cache, user_id, status=status, notice=notice)
        return ""


def register():
    plugin = MonthlyPlugin()
    return {
        "name": "monthly",
        "aliases": ["/monthly", "/mq", "/month"],
        "description": (
            "Track monthly quests for every casino game. Each month you get 15 random quests. "
            "Reach each game's monthly target to claim a 2500 coin reward. "
            "Use /monthly skip <number> or /monthly skip <game> to reroll a quest."
        ),
        "execute": plugin.execute_game,
    }