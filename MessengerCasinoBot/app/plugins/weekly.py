import random
from datetime import datetime, timedelta

from base_game_plugin import BaseGamePlugin


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

        return {
            "week_start": weekly.get("week_start"),
            "progress": variant_progress,
            "targets": targets,
            "labels": labels,
            "active_quests": active,
            "claimed": weekly.get("claimed", False),
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

    def _respond(self, sender, file_queue, message, cache, user_id):
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
            if success:
                payload_list = payload if isinstance(payload, (list, tuple)) else (payload,)
                if len(payload_list) >= 2:
                    old_choice, new_choice = payload_list[0], payload_list[1]
                else:
                    old_choice = payload_list[0] if payload_list else "unknown"
                    new_choice = "unknown"
                replaced_idx = payload_list[2] if len(payload_list) > 2 else None
                old_entry = weekly_manager.variant_data.get(old_choice, {})
                new_entry = weekly_manager.variant_data.get(new_choice, {})
                old_label = old_entry.get("label", old_choice)
                new_label = new_entry.get("label", new_choice)
                slot_text = f"Quest #{replaced_idx + 1}" if replaced_idx is not None else "Quest"
                self._respond(sender, file_queue,
                              f"{slot_text} skipped: {old_label} → {new_label}. Skip available again next week.",
                              cache, user_id)
            else:
                self._respond(sender, file_queue, payload, cache, user_id)
            return ""

        if args and args[0].lower() in {"claim", "c"}:
            success, payload = weekly_manager.claim_reward(cache, user_id)
            if success:
                self._respond(sender, file_queue, f"Weekly reward claimed! +{payload} coins added to your balance.", cache, user_id)
            else:
                self._respond(sender, file_queue, payload, cache, user_id)
            return ""

        status = weekly_manager.get_status(cache, user_id)
        message = self._build_status_message(status)
        self._respond(sender, file_queue, message, cache, user_id)
        return ""


def register():
    plugin = WeeklyPlugin()
    return {
        "name": "weekly",
        "aliases": ["/weekly", "/wq"],
        "description": (
            "Track weekly quests (3 active quests). Use `/weekly` to view status, `/weekly claim` to cash out, "
            "and `/weekly skip <slot>` (or `/weekly rotate <slot>`) once per week to swap one active quest (1-3) for another random one."
        ),
        "execute": plugin.execute_game
    }
