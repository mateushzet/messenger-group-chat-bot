import os
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from PIL import Image, ImageDraw, ImageOps

from base_game_plugin import BaseGamePlugin
from utils import _get_unique_id
from logger import logger


DAILY_GAMES = [
    "blackjack",
    "case",
    "colors",
    "crash",
    "dice",
    "fifa",
    "hilo",
    "jackpot",
    "keno",
    "lotto",
    "mines",
    "piggy",
    "plinko",
    "poker",
    "roulette",
    "slots",
    "snakes",
    "tree",
]

DAILY_TARGET = 10000
DAILY_REWARD = 1000
DAY_SECONDS = 24 * 60 * 60
SETTING_KEY = "daily_quest"
OVERLAY_RESERVE = 130
NOTICE_RESERVE = 60


class DailyQuestManager:
    def __init__(self, games=None, target=DAILY_TARGET, reward=DAILY_REWARD):
        self.games = list(games or DAILY_GAMES)
        self.target = target
        self.reward = reward

    def _now(self) -> float:
        return time.time()

    def _pick_game(self, seed_value: Optional[float] = None) -> str:
        if not self.games:
            return ""
        rng = random.Random(seed_value)
        return rng.choice(self.games)

    def _new_state(self, now: float) -> Dict[str, Any]:
        seed_value = int(now)
        return {
            "game": self._pick_game(seed_value),
            "target": self.target,
            "started_at": now,
            "expires_at": now + DAY_SECONDS,
            "solved_at": None,
            "contributions": {},
            "paid_out": False,
            "payouts": None,
        }

    def _ensure_daily(self, cache) -> Dict[str, Any]:
        now = self._now()
        state = cache.settings.get(SETTING_KEY)

        if not state or not isinstance(state, dict):
            state = self._new_state(now)
            cache.settings[SETTING_KEY] = state
            logger.info(
                f"[DailyQuest] New day started: game={state['game']}, "
                f"expires_at={state['expires_at']}"
            )
            return state

        expires_at = state.get("expires_at") or 0
        if now >= expires_at:
            old_game = state.get("game")
            was_solved = state.get("solved_at") is not None
            was_paid = state.get("paid_out", False)
            state = self._new_state(now)
            cache.settings[SETTING_KEY] = state
            logger.info(
                f"[DailyQuest] Reset day (old game={old_game}, solved={was_solved}, "
                f"paid={was_paid}). New game={state['game']}, "
                f"expires_at={state['expires_at']}"
            )
            return state

        return state

    def record_win(self, cache, user_id, game_key, amount):
        if cache is None or amount is None:
            return
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return
        if amount <= 0:
            return

        game_key = (game_key or "").split("_", 1)[0]
        if not game_key:
            return

        state = self._ensure_daily(cache)

        if state.get("solved_at") is not None:
            return

        if state.get("game") != game_key:
            return

        uid = str(user_id)
        contributions = state.setdefault("contributions", {})
        contributions[uid] = contributions.get(uid, 0.0) + amount

        total = sum(contributions.values())
        if total >= state.get("target", self.target):
            now = self._now()
            state["solved_at"] = now
            state["expires_at"] = now + DAY_SECONDS
            logger.info(
                f"[DailyQuest] SOLVED game={state['game']} total={total} "
                f"contributors={len(contributions)}"
            )

        cache.settings[SETTING_KEY] = state

    def get_status(self, cache) -> Optional[Dict[str, Any]]:
        if cache is None:
            return None
        state = self._ensure_daily(cache)
        return self._build_status(state)

    def _build_status(self, state: Dict[str, Any]) -> Dict[str, Any]:
        contributions = dict(state.get("contributions", {}) or {})
        total = sum(contributions.values())
        target = state.get("target", self.target) or self.target
        solved = state.get("solved_at") is not None
        paid_out = bool(state.get("paid_out", False))

        percent = 0 if target <= 0 else int(max(0, min(100, (total / target) * 100)))

        sorted_contribs = sorted(
            contributions.items(), key=lambda kv: kv[1], reverse=True
        )

        return {
            "game": state.get("game"),
            "target": target,
            "total": total,
            "percent": percent,
            "contributions": contributions,
            "sorted_contributions": sorted_contribs,
            "solved": solved,
            "solved_at": state.get("solved_at"),
            "paid_out": paid_out,
            "payouts": state.get("payouts"),
            "expires_at": state.get("expires_at"),
            "reward": self.reward,
            "contributors_count": len(contributions),
            "can_claim": solved and not paid_out,
        }

    def claim(self, cache):
        if cache is None:
            return False, "Cache unavailable"

        state = self._ensure_daily(cache)

        if state.get("paid_out", False):
            return False, "Reward already paid out"

        if state.get("solved_at") is None:
            return False, "Goal not reached yet"

        contributions = state.get("contributions", {}) or {}
        total = sum(contributions.values())
        if total <= 0:
            return False, "No contributions"

        payouts = {}
        for uid, contrib in contributions.items():
            if contrib <= 0:
                continue
            share = int(self.reward * (contrib / total))
            if share > 0:
                payouts[uid] = share

        state["paid_out"] = True
        state["payouts"] = payouts
        cache.settings[SETTING_KEY] = state

        for uid, amount in payouts.items():
            try:
                cache.update_balance(uid, amount)
            except Exception as e:
                logger.error(
                    f"[DailyQuest] Payout failed for {uid}: {e}", exc_info=True
                )

        logger.info(
            f"[DailyQuest] Paid out game={state.get('game')} total={total} "
            f"recipients={len(payouts)} sum_paid={sum(payouts.values())}"
        )
        return True, payouts


daily_manager = DailyQuestManager()


def record_daily_win(cache, user_id, game_key, amount):
    try:
        daily_manager.record_win(cache, user_id, game_key, amount)
    except Exception as e:
        logger.error(f"[DailyQuest] record_daily_win error: {e}", exc_info=True)


class DailyPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="dailyquest")
        self.reward_amount = daily_manager.reward
        self.target = daily_manager.target

    def _load_game_icon(self, game_key: str, size: int = 48) -> Image.Image:
        base_key = (game_key or "").split("_", 1)[0]
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
            font_size=max(14, int(size * 0.45)),
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

    def _load_avatar_circle(self, user_id, size: int) -> Optional[Image.Image]:
        try:
            path = None
            if hasattr(self, "cache") and self.cache and hasattr(self.cache, "get_avatar_path"):
                path = self.cache.get_avatar_path(user_id)
            if not path or not os.path.exists(path):
                return None
            img = Image.open(path).convert("RGBA")
            img = ImageOps.fit(
                img, (size, size), Image.Resampling.LANCZOS, centering=(0.5, 0.5)
            )
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)
            img.putalpha(mask)
            return img
        except Exception as e:
            logger.error(f"[DailyQuest] avatar load error for {user_id}: {e}")
            return None

    def _load_bg_segment(self, user_id, width: int, height: int) -> Optional[Image.Image]:
        if width <= 0 or height <= 0:
            return None
        try:
            path = None
            if hasattr(self, "cache") and self.cache and hasattr(self.cache, "get_background_path"):
                path = self.cache.get_background_path(user_id)
            if not path or not os.path.exists(path):
                return None
            img = Image.open(path).convert("RGBA")
            img = img.resize((width, height), Image.Resampling.LANCZOS)
            dark = Image.new("RGBA", (width, height), (0, 0, 0, 90))
            img = Image.alpha_composite(img, dark)
            return img
        except Exception as e:
            logger.error(f"[DailyQuest] bg segment error for {user_id}: {e}")
            return None

    def _format_remaining(self, expires_at) -> str:
        if not expires_at:
            return ""
        try:
            remaining = int(expires_at - time.time())
        except (TypeError, ValueError):
            return ""
        if remaining <= 0:
            return "resetting..."
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    def _get_username(self, user_id) -> str:
        try:
            if hasattr(self, "cache") and self.cache:
                u = self.cache.get_user(user_id)
                if u and u.get("name"):
                    return u["name"]
        except Exception:
            pass
        return f"User {user_id}"

    def _build_status_message(self, status: dict) -> str:
        if not status:
            return "Daily quest data unavailable."

        game = status.get("game") or "?"
        total = int(status.get("total", 0))
        target = int(status.get("target", self.target))
        percent = status.get("percent", 0)
        solved = status.get("solved", False)
        paid = status.get("paid_out", False)
        remaining = self._format_remaining(status.get("expires_at"))

        lines = [
            f"Daily Quest — {game.title()}",
            f"Goal: win {target} total (net).",
            f"Progress: {total}/{target} ({percent}%)",
            f"Contributors: {status.get('contributors_count', 0)}",
        ]

        if remaining:
            if solved:
                lines.append(f"Next quest in: {remaining}")
            else:
                lines.append(f"Time left: {remaining}")

        lines.append("")

        if paid:
            lines.append("Already paid out. Payouts:")
            payouts = status.get("payouts") or {}
            for uid, _amt in (status.get("sorted_contributions") or []):
                payout = int(payouts.get(str(uid), 0))
                if payout > 0:
                    lines.append(f"  {self._get_username(uid)}: +{payout}")
        elif solved:
            lines.append(
                f"Goal reached! Use /dailyquest to pay out +{self.reward_amount} coins "
                f"(split by contribution)."
            )
        else:
            lines.append(
                f"Win together on {game} to reach {target}. "
                f"Reward: {self.reward_amount} coins split proportionally."
            )

        return "\n".join(lines)

    def _generate_status_image(
        self,
        status: dict,
        username: str,
        background_path: str,
        output_folder: str,
        notice: Optional[dict] = None,
    ) -> Optional[str]:
        try:
            IMAGE_WIDTH = 680
            PADDING_X = 20
            HEADER_Y = 16
            ICON_SIZE = 48
            ICON_GAP = 10
            BAR_H = 54
            BAR_TOP_GAP = 20
            AVATAR_SIZE = BAR_H - 8
            MIN_SEGMENT_W = 3

            game_key_raw = status.get("game") or ""
            game = game_key_raw.title() if game_key_raw else "?"
            total = int(status.get("total", 0))
            target = int(status.get("target", self.target) or self.target)
            percent = status.get("percent", 0)
            paid = status.get("paid_out", False)
            solved = status.get("solved", False)
            remaining_txt = self._format_remaining(status.get("expires_at"))

            icon = self._load_game_icon(game_key_raw, size=ICON_SIZE)
            title_img = self.text_renderer.render_text(
                text=f"Daily Quest — {game}",
                font_size=28,
                color=(255, 255, 255, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
            )
            subtitle_img = self.text_renderer.render_text(
                text=f"Goal: {total}/{target}  ({percent}%)",
                font_size=18,
                color=(235, 235, 235, 255),
                stroke_width=1,
                stroke_color=(0, 0, 0, 255),
                shadow=True,
            )
            remaining_img = None
            if remaining_txt:
                label = "Next quest in" if solved else "Time left"
                remaining_img = self.text_renderer.render_text(
                    text=f"{label}: {remaining_txt}",
                    font_size=15,
                    color=(220, 220, 220, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255),
                    shadow=True,
                )

            header_total_w = ICON_SIZE + ICON_GAP + title_img.width
            header_x = (IMAGE_WIDTH - header_total_w) // 2
            icon_y = HEADER_Y + (title_img.height - ICON_SIZE) // 2
            title_x = header_x + ICON_SIZE + ICON_GAP

            subtitle_y = HEADER_Y + title_img.height + 8
            remaining_y = subtitle_y + subtitle_img.height + 4

            sorted_contribs = list(status.get("sorted_contributions", []) or [])
            total_contrib = sum(c for _, c in sorted_contribs) or 0

            bar_x = PADDING_X
            bar_w = IMAGE_WIDTH - PADDING_X * 2
            header_block_h = (
                subtitle_img.height
                + 8
                + (remaining_img.height + 4 if remaining_img else 0)
            )
            bar_y = HEADER_Y + title_img.height + header_block_h + BAR_TOP_GAP

            segments = []
            if total_contrib > 0:
                denom = max(target, 1)
                for uid, amount in sorted_contribs:
                    seg_w = int(bar_w * (amount / denom))
                    if seg_w < MIN_SEGMENT_W:
                        seg_w = MIN_SEGMENT_W
                    segments.append([uid, amount, seg_w, None])

                used = sum(s[2] for s in segments)

                if used > bar_w:
                    scale = bar_w / used
                    for seg in segments:
                        seg[2] = max(1, int(seg[2] * scale))
                    used = sum(s[2] for s in segments)

                if total_contrib >= target:
                    diff = bar_w - used
                    if segments and diff != 0:
                        segments[0][2] = max(MIN_SEGMENT_W, segments[0][2] + diff)
                        used = sum(s[2] for s in segments)
                        idx = 1
                        while used > bar_w and idx < len(segments):
                            over = used - bar_w
                            cut = min(over, segments[idx][2] - 1)
                            segments[idx][2] -= cut
                            used -= cut
                            idx += 1

                for seg in segments:
                    seg[3] = self._load_bg_segment(seg[0], seg[2], BAR_H)

            footer_lines = []
            if paid:
                footer_lines.append("Already paid out:")
                payouts = status.get("payouts") or {}
                for uid, _amt in sorted_contribs:
                    payout = int(payouts.get(str(uid), 0))
                    if payout > 0:
                        footer_lines.append(f"  {self._get_username(uid)}: +{payout}")
            elif solved:
                footer_lines.append("Goal reached — type /dq to pay out.")
            else:
                footer_lines.append(
                    f"Reward: {self.reward_amount} coins split by contribution."
                )

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
            footer_h = sum(i.height for i in footer_imgs) + max(0, len(footer_imgs) - 1) * 4

            bar_bottom = bar_y + BAR_H
            footer_y = bar_bottom + 20
            image_h = (
                footer_y
                + footer_h
                + 14
                + NOTICE_RESERVE
                + OVERLAY_RESERVE
                + 18
            )

            bg = Image.open(background_path).convert("RGB").resize(
                (IMAGE_WIDTH, image_h), Image.Resampling.LANCZOS
            )
            canvas = bg.convert("RGBA")
            draw = ImageDraw.Draw(canvas)

            canvas.alpha_composite(icon, (header_x, icon_y))
            canvas.alpha_composite(title_img, (title_x, HEADER_Y))
            canvas.alpha_composite(
                subtitle_img, ((IMAGE_WIDTH - subtitle_img.width) // 2, subtitle_y)
            )
            if remaining_img:
                canvas.alpha_composite(
                    remaining_img,
                    ((IMAGE_WIDTH - remaining_img.width) // 2, remaining_y),
                )

            draw.rounded_rectangle(
                [bar_x, bar_y, bar_x + bar_w, bar_y + BAR_H],
                radius=14,
                fill=(18, 18, 24, 235),
                outline=(40, 40, 50, 255),
                width=2,
            )

            cur_x = bar_x
            avatar_cache: Dict[str, Optional[Image.Image]] = {}
            for idx, (uid, amount, seg_w, bg_seg) in enumerate(segments):
                if seg_w <= 0:
                    continue
                if bg_seg is not None:
                    canvas.alpha_composite(bg_seg, (cur_x, bar_y))
                else:
                    draw.rectangle(
                        [cur_x, bar_y, cur_x + seg_w, bar_y + BAR_H],
                        fill=(60, 60, 80, 235),
                    )

                if idx > 0:
                    draw.line(
                        [(cur_x, bar_y + 4), (cur_x, bar_y + BAR_H - 4)],
                        fill=(0, 0, 0, 180),
                        width=2,
                    )

                av = avatar_cache.get(uid, "miss")
                if av == "miss":
                    av = self._load_avatar_circle(uid, AVATAR_SIZE)
                    avatar_cache[uid] = av
                if av is not None and seg_w >= AVATAR_SIZE + 8:
                    av_x = cur_x + seg_w - AVATAR_SIZE - 4
                    av_y = bar_y + (BAR_H - AVATAR_SIZE) // 2
                    if av_x >= cur_x + 2:
                        canvas.alpha_composite(av, (av_x, av_y))

                amount_img = self.text_renderer.render_text(
                    text=str(int(amount)),
                    font_size=15,
                    color=(255, 255, 255, 255),
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 255),
                    shadow=False,
                )
                text_x = cur_x + 6
                text_y = bar_y + (BAR_H - amount_img.height) // 2
                avail = seg_w - 12 - (
                    AVATAR_SIZE + 6 if (av is not None and seg_w >= AVATAR_SIZE + 8) else 0
                )
                if avail > 0 and amount_img.width <= avail:
                    canvas.alpha_composite(amount_img, (text_x, text_y))

                cur_x += seg_w

            if not segments:
                empty_img = self.text_renderer.render_text(
                    text="No contributions yet",
                    font_size=16,
                    color=(200, 200, 200, 255),
                    stroke_width=1,
                    stroke_color=(0, 0, 0, 255),
                )
                canvas.alpha_composite(
                    empty_img,
                    (
                        bar_x + (bar_w - empty_img.width) // 2,
                        bar_y + (BAR_H - empty_img.height) // 2,
                    ),
                )

            cur_y = footer_y
            for img in footer_imgs:
                canvas.alpha_composite(img, ((IMAGE_WIDTH - img.width) // 2, cur_y))
                cur_y += img.height + 4

            if notice:
                headline = str(notice.get("headline") or "")
                subline = str(notice.get("subline") or "")
                headline_img = self.text_renderer.render_text(
                    text=headline,
                    font_size=36,
                    color=(255, 255, 255, 215),
                    stroke_width=3,
                    stroke_color=(0, 0, 0, 255),
                    shadow=True,
                    shadow_color=(0, 0, 0, 200),
                    shadow_offset=(2, 2),
                ) if headline else None
                subline_img = self.text_renderer.render_text(
                    text=subline,
                    font_size=26,
                    color=(255, 255, 255, 215),
                    stroke_width=2,
                    stroke_color=(0, 0, 0, 255),
                    shadow=True,
                    shadow_color=(0, 0, 0, 200),
                    shadow_offset=(2, 2),
                ) if subline else None

                block_h = 0
                if headline_img:
                    block_h += headline_img.height
                if subline_img:
                    block_h += (8 if block_h else 0) + subline_img.height

                notice_bottom = image_h - OVERLAY_RESERVE - 10
                cy = notice_bottom - block_h
                if headline_img:
                    canvas.alpha_composite(
                        headline_img,
                        ((IMAGE_WIDTH - headline_img.width) // 2, cy),
                    )
                    cy += headline_img.height + 8
                if subline_img:
                    canvas.alpha_composite(
                        subline_img,
                        ((IMAGE_WIDTH - subline_img.width) // 2, cy),
                    )

            os.makedirs(output_folder, exist_ok=True)
            output_path = os.path.join(
                output_folder, f"dailyquest_base_{username}_{_get_unique_id()}.png"
            )
            canvas.convert("RGB").save(output_path, "PNG", quality=95)
            return output_path
        except Exception as e:
            logger.error(f"[DailyQuest] image generation error: {e}", exc_info=True)
            return None

    def _respond(self, sender, file_queue, message, cache, user_id,
                 user=None, status=None, notice=None):
        if status:
            background_path = None
            if cache and user_id and hasattr(cache, "get_background_path"):
                background_path = cache.get_background_path(user_id)
            if not background_path or not os.path.exists(background_path):
                background_path = self.get_asset_path("backgrounds", "default-bg.png")

            if background_path and os.path.exists(background_path):
                base_image_path = self._generate_status_image(
                    status=status,
                    username=sender,
                    background_path=background_path,
                    output_folder=self.results_folder,
                    notice=notice,
                )
                if base_image_path:
                    user_for_overlay = dict(user or {})
                    user_for_overlay["id"] = user_id

                    balance = user_for_overlay.get("balance", 0)
                    final_path, err = self.apply_user_overlay(
                        base_image_path=base_image_path,
                        user_id=user_id,
                        sender=sender,
                        total_bet=0,
                        win_amount=0,
                        balance=balance,
                        user=user_for_overlay,
                        show_win_text=False,
                        show_bet_amount=False,
                    )
                    if final_path:
                        file_queue.put(final_path)
                        return
                    logger.error(f"[DailyQuest] apply_user_overlay failed: {err}")

        self.send_message_image(sender, file_queue, message, "Daily Quest", cache, user_id)

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        if error:
            self.send_message_image(
                sender, file_queue,
                "You must be registered before using daily quests.",
                "Daily Quest", cache, user_id,
            )
            return ""

        status = daily_manager.get_status(cache)
        if not status:
            self.send_message_image(
                sender, file_queue,
                "Daily quest data unavailable.",
                "Daily Quest", cache, user_id,
            )
            return ""

        notice = None
        message_override = None

        if status.get("can_claim"):
            ok, payload = daily_manager.claim(cache)
            if ok:
                lines = ["Daily quest complete! Payouts:"]
                for uid, amount in sorted(payload.items(), key=lambda kv: kv[1], reverse=True):
                    lines.append(f"  {self._get_username(uid)}: +{amount}")
                message_override = "\n".join(lines)
                notice = {"headline": "REWARD PAID OUT", "subline": ""}
            else:
                message_override = f"Payout failed: {payload}"
            status = daily_manager.get_status(cache)

        elif status.get("paid_out"):
            notice = {"headline": "ALREADY PAID OUT", "subline": ""}
            message_override = "This daily quest has already been paid out."

        message = message_override or self._build_status_message(status)
        self._respond(
            sender, file_queue, message, cache, user_id,
            user=user, status=status, notice=notice,
        )
        return ""


def register():
    plugin = DailyPlugin()
    return {
        "name": "dailyquest",
        "aliases": ["/dailyquest", "/dq"],
        "description": (
            "Global daily co-op quest. Each day a random game is chosen. "
            "All players' net wins on that game sum toward a 10000 goal. "
            "When reached, the first /dq pays out 1000 coins split by contribution. "
            "24h window, unclaimed reward is lost."
        ),
        "execute": plugin.execute_game,
    }