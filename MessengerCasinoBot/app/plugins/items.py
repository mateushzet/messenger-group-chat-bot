import os
import colorsys
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw
from datetime import datetime
from base_game_plugin import BaseGamePlugin
from logger import logger


PAGES: Dict[int, List[int]] = {
    1: [5, 10, 15, 20, 25],
    2: [30, 35, 40, 45, 50],
    3: [55, 60, 65, 70, 75],
    4: [80, 85, 90, 95, 100],
    5: [110, 120, 130, 140, 150],
}

TOTAL_PAGES = len(PAGES)

ROW_CATEGORIES: List[str] = [
    "icon_bet",
    "icon_balance",
    "exp_bar",
]

CATEGORY_LABELS: Dict[str, str] = {
    "icon_bet": "Bet Icons",
    "icon_balance": "Balance Icons",
    "exp_bar": "Level Bars",
}

PRICES: Dict[int, int] = {
    5: 500, 10: 650, 15: 800, 20: 950, 25: 1100,
    30: 1250, 35: 1400, 40: 1550, 45: 1700, 50: 2000,
    55: 2150, 60: 2300, 65: 2450, 70: 2600, 75: 2750,
    80: 2900, 85: 3050, 90: 3200, 95: 3400, 100: 4000,
    110: 4400, 120: 4800, 130: 5200, 140: 5600, 150: 6000,
}


ITEM_NAMES: Dict[Tuple[str, int], str] = {
    # --- icon_bet ---
    ("icon_bet", 5): "Coin",
    ("icon_bet", 10): "Diamond",
    ("icon_bet", 15): "Ruby",
    ("icon_bet", 20): "Emerald",
    ("icon_bet", 25): "Rainbow Gem",
    ("icon_bet", 30): "Silver Eagle",
    ("icon_bet", 35): "Golden Lion",
    ("icon_bet", 40): "Platinum Dragon",
    ("icon_bet", 45): "Obsidian Phoenix",
    ("icon_bet", 50): "Royal Crown",
    ("icon_bet", 55): "Fortune Cauldron",
    ("icon_bet", 60): "Horn of Plenty",
    ("icon_bet", 65): "Pirate Treasure",
    ("icon_bet", 70): "Casino Star",
    ("icon_bet", 75): "Crystal Ball",
    ("icon_bet", 80): "Velvet Ace",
    ("icon_bet", 85): "Diamond Poker",
    ("icon_bet", 90): "Royal Roulette",
    ("icon_bet", 95): "Golden Jackpot",
    ("icon_bet", 100): "Legendary Treasure",
    ("icon_bet", 110): "Mythic Grail",
    ("icon_bet", 120): "Cosmic Diamond",
    ("icon_bet", 130): "Divine Artifact",
    ("icon_bet", 140): "Eternal Phoenix",
    ("icon_bet", 150): "Rainbow Dragon",

    # --- icon_balance ---
    ("icon_balance", 5): "Pouch",
    ("icon_balance", 10): "Silver Bar",
    ("icon_balance", 15): "Golden Vault",
    ("icon_balance", 20): "Purse",
    ("icon_balance", 25): "Green Sack",
    ("icon_balance", 30): "Merchant Chest",
    ("icon_balance", 35): "Banker's Bag",
    ("icon_balance", 40): "Royal Treasury",
    ("icon_balance", 45): "Wallet",
    ("icon_balance", 50): "Dragon's Sack",
    ("icon_balance", 55): "Cyber Wallet",
    ("icon_balance", 60): "Pirate Chest",
    ("icon_balance", 65): "Chest of Gods",
    ("icon_balance", 70): "Wizard's Pocket",
    ("icon_balance", 75): "Alchemist's Pouch",
    ("icon_balance", 80): "Credit Card",
    ("icon_balance", 85): "Diamond Chest",
    ("icon_balance", 90): "Royal Bank",
    ("icon_balance", 95): "Bitcoin",
    ("icon_balance", 100): "Legendary Vault",
    ("icon_balance", 110): "Poker Chips",
    ("icon_balance", 120): "Crystals",
    ("icon_balance", 130): "Divine Daimonds",
    ("icon_balance", 140): "Infinite treasures",
    ("icon_balance", 150): "Mimic",

    # --- exp_bar ---
    ("exp_bar", 5): "Green Bar",
    ("exp_bar", 10): "Red Bar",
    ("exp_bar", 15): "Golden Bar",
    ("exp_bar", 20): "Crystal Bar",
    ("exp_bar", 25): "Pink Bar",
    ("exp_bar", 30): "Emerald Star Bar",
    ("exp_bar", 35): "Ruby Star Bar",
    ("exp_bar", 40): "Sapphire Star Bar",
    ("exp_bar", 45): "Amethyst Storm Bar",
    ("exp_bar", 50): "Platinum Storm Bar",
    ("exp_bar", 55): "Amber Pulse Bar",
    ("exp_bar", 60): "Coral Pulse Bar",
    ("exp_bar", 65): "Turquoise Bar",
    ("exp_bar", 70): "Purple Bar",
    ("exp_bar", 75): "Obsidian Bar",
    ("exp_bar", 80): "Royal Gradient Bar",
    ("exp_bar", 85): "Mystic Gradient Bar",
    ("exp_bar", 90): "Legendary Gradient Bar",
    ("exp_bar", 95): "Cosmic Rainbow Bar",
    ("exp_bar", 100): "Divine Prism Bar",
    ("exp_bar", 110): "Mythic Flame Bar",
    ("exp_bar", 120): "Eternal Flame Bar",
    ("exp_bar", 130): "Starlight Flame Bar",
    ("exp_bar", 140): "Dragon Flame Bar",
    ("exp_bar", 150): "Rainbow Flame Bar",
}



def _clamp(v: int) -> int:
    return max(0, min(255, int(v)))


def _make_icon_effect(category: str) -> Dict:
    icon_type = "bet" if category == "icon_bet" else "balance"
    return {
        "effect_type": "icon",
        "effect_data": {"icon_type": icon_type},
    }


_EXP_BAR_DEFS: Dict[int, Dict] = {
    # --- SOLID (2) ---
    5:   {"bar_type": "solid",           "color": (0, 200, 0, 255)},
    10:  {"bar_type": "solid",           "color": (220, 40, 40, 255)},

    # --- PULSE (2) ---
    15:  {"bar_type": "pulse",           "color": (255, 160, 30, 255)},
    20:  {"bar_type": "pulse",           "color": (255, 120, 120, 255)},

    # --- GLOW (3) ---
    25:  {"bar_type": "glow",            "color": (255, 215, 0, 255)},
    30:  {"bar_type": "glow",            "color": (100, 200, 255, 255)},
    35:  {"bar_type": "glow",            "color": (255, 100, 200, 255)},

    # --- STARS (3) ---
    40:  {"bar_type": "stars",           "color": (0, 100, 50, 255),    "star_color": (180, 255, 200, 255)},
    45:  {"bar_type": "stars",           "color": (100, 0, 30, 255),    "star_color": (255, 180, 200, 255)},
    50:  {"bar_type": "stars",           "color": (0, 30, 100, 255),    "star_color": (180, 200, 255, 255)},

    # --- LIGHTNING (2) ---
    55:  {"bar_type": "lightning",       "color": (80, 40, 140, 255),   "bolt_color": (220, 180, 255, 255)},
    60:  {"bar_type": "lightning",       "color": (180, 180, 200, 255), "bolt_color": (255, 255, 255, 255)},

    # --- STRIPES (3) ---
    65:  {"bar_type": "stripes",         "color": (0, 200, 200, 255),   "stripe_color": (0, 100, 100, 255)},
    70:  {"bar_type": "stripes",         "color": (140, 30, 160, 255),  "stripe_color": (80, 10, 100, 255)},
    75:  {"bar_type": "stripes",         "color": (190, 190, 200, 255), "stripe_color": (100, 100, 120, 255)},

    # --- GRADIENT (3) ---
    80:  {"bar_type": "gradient",        "from": (255, 215, 0, 255),   "to": (255, 100, 0, 255)},
    85:  {"bar_type": "gradient",        "from": (180, 100, 255, 255), "to": (80, 40, 160, 255)},
    90:  {"bar_type": "gradient",        "from": (255, 250, 200, 255), "to": (255, 180, 0, 255)},

    # --- RAINBOW (2) ---
    95:  {"bar_type": "rainbow",         "color": "rainbow"},
    100: {"bar_type": "rainbow_sparkle", "color": "rainbow",           "sparkle_color": (255, 255, 255, 255)},

    # --- FLAMES (5) - najwyzsze poziomy, rozne kolory ---
    110: {"bar_type": "flames",          "color": (255, 160, 0, 255),   "flame_color": (255, 240, 120, 255)},  # zlote
    120: {"bar_type": "flames",          "color": (200, 30, 0, 255),    "flame_color": (255, 180, 60, 255)},   # czerwone
    130: {"bar_type": "flames",          "color": (140, 40, 200, 255),  "flame_color": (220, 140, 255, 255)},  # fioletowe
    140: {"bar_type": "flames",          "color": (0, 100, 220, 255),   "flame_color": (140, 200, 255, 255)},  # niebieskie
    150: {"bar_type": "flames",          "color": (0, 140, 60, 255),    "flame_color": (140, 255, 180, 255)},  # zielone
}

def _make_exp_bar_effect(level: int) -> Dict:
    d = _EXP_BAR_DEFS.get(level, {"bar_type": "solid", "color": (255, 215, 0, 255)})
    effect_data = {
        "bar_type": d.get("bar_type", "solid"),
        "percent": 60,
    }
    for k, v in d.items():
        if k not in ("bar_type", "percent"):
            effect_data[k] = v
    effect_data["glow"] = d.get("bar_type") in ("glow", "rainbow_sparkle", "lightning", "flames")
    return {
        "effect_type": "exp_bar",
        "effect_data": effect_data,
    }


def _build_effect(category: str, level: int, item_id: int) -> Dict:
    if category in ("icon_bet", "icon_balance"):
        eff = _make_icon_effect(category)
        eff["icon_path"] = f"assets/items/item_{item_id}.png"
        return eff
    if category == "exp_bar":
        return _make_exp_bar_effect(level)
    return {"effect_type": "unknown", "effect_data": {}}


def _build_catalog() -> Dict[str, Dict]:
    catalog: Dict[str, Dict] = {}
    item_id = 1
    for page in range(1, TOTAL_PAGES + 1):
        levels = PAGES[page]
        for category in ROW_CATEGORIES:
            for level in levels:
                key = f"item_{item_id}"
                name = ITEM_NAMES.get((category, level), f"Item {item_id}")
                effect = _build_effect(category, level, item_id)
                entry = {
                    "id": item_id,
                    "name": name,
                    "category": category,
                    "price": PRICES.get(level, 500),
                    "required_level": level,
                    "description": f"{name} ({CATEGORY_LABELS.get(category, category)})",
                    "effect_type": effect["effect_type"],
                    "effect_data": effect["effect_data"],
                }
                if "icon_path" in effect:
                    entry["icon_path"] = effect["icon_path"]
                catalog[key] = entry
                item_id += 1
    return catalog



class ItemsPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="items")
        self.results_folder = self.get_asset_path("results")
        self.items_folder = self.get_asset_path("items")

        os.makedirs(self.results_folder, exist_ok=True)
        os.makedirs(self.items_folder, exist_ok=True)

        self.items_catalog: Dict[str, Dict] = _build_catalog()

        self._id_to_key: Dict[int, str] = {
            data["id"]: key for key, data in self.items_catalog.items()
        }

        self.categories = {
            "icon_bet": {"name": "Bet Icons", "icon": "\U0001F3B0"},
            "icon_balance": {"name": "Balance Icons", "icon": "\U0001F4B0"},
            "exp_bar": {"name": "Level Bars", "icon": "\U0001F4CA"},
        }

        self._cleanup_done = False


    def _cleanup_old_items(self) -> None:
        if self._cleanup_done:
            return
        self._cleanup_done = True

        if not self.cache or not hasattr(self.cache, "users"):
            return

        try:
            valid_keys = set(self.items_catalog.keys())
            user_ids = list(self.cache.users.keys())
            cleaned = 0
            for uid in user_ids:
                user = self.cache.get_user(uid)
                if not user:
                    continue
                old_items = user.get("items", {}) or {}
                old_equipped = user.get("equipped", {}) or {}

                new_items = {k: v for k, v in old_items.items() if k in valid_keys}
                new_equipped = {k: v for k, v in old_equipped.items() if k in valid_keys}

                if len(new_items) != len(old_items) or len(new_equipped) != len(old_equipped):
                    self.cache.update_user(uid, items=new_items, equipped=new_equipped)
                    cleaned += 1

            if cleaned:
                logger.info(f"[items] Cleaned old items for {cleaned} users")
        except Exception as e:
            logger.error(f"[items] Cleanup error: {e}", exc_info=True)


    def get_user_effects(self, user_id: str) -> Dict:
        if not self.cache:
            return {
                "icons": {},
                "colors": {},
                "frame": None,
                "exp_bar": None,
            }
        user = self.cache.get_user(user_id)
        if not user:
            return {
                "icons": {},
                "colors": {},
                "frame": None,
                "exp_bar": None,
            }

        equipped = user.get("equipped", {}) or {}
        effects = {
            "icons": {},
            "colors": {},
            "frame": None,
            "exp_bar": None,
        }

        effects["icons"]["bet"] = {
            "path": "assets/bet_icon.png",
            "item_id": None,
            "name": "Default",
        }
        effects["icons"]["balance"] = {
            "path": "assets/balance_icon.png",
            "item_id": None,
            "name": "Default",
        }

        for item_key in equipped:
            if item_key in self.items_catalog:
                item = self.items_catalog[item_key]
                effect_type = item.get("effect_type")
                effect_data = item.get("effect_data", {})

                if effect_type == "icon":
                    icon_type = effect_data.get("icon_type")
                    if icon_type:
                        # Nadpisuje domyslna ikone
                        effects["icons"][icon_type] = {
                            "path": item.get("icon_path", ""),
                            "item_id": item_key,
                            "name": item.get("name", ""),
                        }
                elif effect_type == "exp_bar":
                    effects["exp_bar"] = effect_data

        return effects


    def get_user_items(self, user_id: str) -> Dict:
        if not self.cache:
            return {}
        user = self.cache.get_user(user_id)
        if user and "items" in user:
            return user["items"]
        return {}

    def get_user_equipped(self, user_id: str) -> Dict:
        if not self.cache:
            return {}
        user = self.cache.get_user(user_id)
        if user and "equipped" in user:
            return user["equipped"]
        return {}

    def can_equip_item(self, user_id: str, item_key: str) -> Tuple[bool, str]:
        if item_key not in self.items_catalog:
            return False, "Item does not exist"
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User does not exist"
        item = self.items_catalog[item_key]
        required_level = item.get("required_level", 1)
        user_level = user.get("level", 1)
        if user_level < required_level:
            return False, f"Required level {required_level} (you have {user_level})"
        return True, "OK"

    def can_buy_item(self, user_id: str, item_key: str) -> Tuple[bool, str]:
        if item_key not in self.items_catalog:
            return False, "Item does not exist"
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User does not exist"
        item = self.items_catalog[item_key]
        required_level = item.get("required_level", 1)
        user_level = user.get("level", 1)
        if user_level < required_level:
            return False, f"Required level {required_level} to buy (you have {user_level})"
        return True, "OK"

    def add_item(self, user_id: str, item_key: str) -> Tuple[bool, str]:
        if item_key not in self.items_catalog:
            return False, "Item does not exist"
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User does not exist"

        items = user.get("items", {}) or {}
        if item_key in items:
            return False, "You already own this item"

        items[item_key] = {
            "acquired": datetime.now().isoformat(),
            "equipped": False,
        }
        self.cache.update_user(user_id, items=items)
        return True, f"Obtained: {self.items_catalog[item_key]['name']}!"

    def equip_item(self, user_id: str, item_key: str) -> Tuple[bool, str]:
        can_equip, msg = self.can_equip_item(user_id, item_key)
        if not can_equip:
            return False, msg

        if item_key not in self.items_catalog:
            return False, "Item does not exist"

        user = self.cache.get_user(user_id)
        if not user:
            return False, "User does not exist"

        items = user.get("items", {}) or {}
        if item_key not in items:
            return False, "You do not own this item"

        equipped = user.get("equipped", {}) or {}
        item_category = self.items_catalog[item_key]["category"]

        for eq_key in list(equipped.keys()):
            if eq_key in self.items_catalog:
                if self.items_catalog[eq_key]["category"] == item_category:
                    if eq_key != item_key:
                        del equipped[eq_key]
                        if eq_key in items:
                            items[eq_key]["equipped"] = False

        equipped[item_key] = True
        items[item_key]["equipped"] = True

        self.cache.update_user(user_id, equipped=equipped, items=items)
        return True, f"Equipped: {self.items_catalog[item_key]['name']}!"

    def unequip_item(self, user_id: str, item_key: str) -> Tuple[bool, str]:
        user = self.cache.get_user(user_id)
        if not user:
            return False, "User does not exist"

        equipped = user.get("equipped", {}) or {}
        if item_key not in equipped:
            return False, "This item is not equipped"

        del equipped[item_key]
        items = user.get("items", {}) or {}
        if item_key in items:
            items[item_key]["equipped"] = False

        self.cache.update_user(user_id, equipped=equipped, items=items)
        return True, f"Unequipped: {self.items_catalog[item_key]['name']}"

    def _resolve_item_by_id(self, raw: str) -> Optional[str]:
        try:
            item_id = int(raw)
        except (ValueError, TypeError):
            return None
        if item_id < 1 or item_id > len(self.items_catalog):
            return None
        return self._id_to_key.get(item_id)

    def get_items_for_page(self, page: int) -> List[Optional[str]]:
        if page not in PAGES:
            return []
        levels = PAGES[page]
        result: List[Optional[str]] = []
        for category in ROW_CATEGORIES:
            for level in levels:
                found = None
                for key, data in self.items_catalog.items():
                    if data["category"] == category and data["required_level"] == level:
                        found = key
                        break
                result.append(found)
        return result

    def _load_icon(self, icon_path: str, size: int) -> Optional[Image.Image]:
        try:
            full_path = self.get_app_path(icon_path) if icon_path else None
            if full_path and os.path.exists(full_path):
                img = Image.open(full_path).convert("RGBA")
                return img.resize((size, size), Image.LANCZOS)
        except Exception as e:
            logger.debug(f"[items] Could not load icon {icon_path}: {e}")
        return None

    def _draw_item_preview(self, base_img: Image.Image, x: int, y: int, size: int, item_data: Dict):
        draw = ImageDraw.Draw(base_img)
        effect_type = item_data.get("effect_type")
        effect_data = item_data.get("effect_data", {})

        draw.rounded_rectangle(
            [x, y, x + size, y + size],
            radius=6,
            fill=(30, 30, 40, 220),
            outline=(80, 80, 100, 255),
            width=1,
        )

        if effect_type == "icon":
            icon_path = item_data.get("icon_path", "")
            icon_img = self._load_icon(icon_path, size - 8)
            if icon_img:
                base_img.alpha_composite(icon_img, (x + 4, y + 4))
            else:
                # Fallback - text symbol
                icon_type = effect_data.get("icon_type", "bet")
                symbol = "B" if icon_type == "bet" else "$"
                if hasattr(self, "text_renderer"):
                    sym_img = self.text_renderer.render_text(
                        symbol, font_size=size // 2,
                        color=(255, 215, 0, 255),
                        stroke_width=2, stroke_color=(0, 0, 0, 255),
                    )
                    base_img.alpha_composite(
                        sym_img,
                        (x + (size - sym_img.width) // 2, y + (size - sym_img.height) // 2),
                    )

        elif effect_type == "exp_bar":
            bar_type = effect_data.get("bar_type", "solid")
            percent = effect_data.get("percent", 60)
            pad = 8
            bar_w = size - pad * 2
            bar_h = 14
            bar_x = x + pad
            bar_y = y + (size - bar_h) // 2 - 6

            draw.rectangle(
                [bar_x, bar_y, bar_x + bar_w, bar_y + bar_h],
                fill=(50, 50, 60, 255),
                outline=(120, 120, 140, 255),
                width=1,
            )

            fill_w = int(bar_w * percent / 100.0)
            color = effect_data.get("color")

            if bar_type in ("rainbow", "rainbow_sparkle") or color == "rainbow":
                for i in range(fill_w):
                    hue = (i / max(1, bar_w)) * 360
                    sat = 0.55 if bar_type == "rainbow_sparkle" else 1.0
                    r, g, b = colorsys.hsv_to_rgb(hue / 360.0, sat, 1.0)
                    c = (int(r * 255), int(g * 255), int(b * 255), 255)
                    draw.line([(bar_x + i, bar_y + 1), (bar_x + i, bar_y + bar_h - 1)], fill=c, width=1)
            elif bar_type == "gradient":
                c_from = effect_data.get("from", (255, 255, 255, 255))
                c_to = effect_data.get("to", (0, 0, 0, 255))
                for i in range(fill_w):
                    t = i / max(1, fill_w - 1)
                    c = tuple(int(c_from[j] * (1 - t) + c_to[j] * t) for j in range(4))
                    draw.line([(bar_x + i, bar_y + 1), (bar_x + i, bar_y + bar_h - 1)], fill=c, width=1)
            else:
                if isinstance(color, tuple):
                    c = color if len(color) == 4 else (*color, 255)
                else:
                    c = (255, 215, 0, 255)
                draw.rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h], fill=c)

            if hasattr(self, "text_renderer"):
                label = bar_type.upper().replace("_", " ")[:14]
                lbl_img = self.text_renderer.render_text(
                    label, font_size=11,
                    color=(255, 255, 255, 220),
                    stroke_width=1, stroke_color=(0, 0, 0, 255),
                )
                base_img.alpha_composite(
                    lbl_img,
                    (x + (size - lbl_img.width) // 2, y + size - lbl_img.height - 4),
                )

        else:
            if hasattr(self, "text_renderer"):
                txt = self.text_renderer.render_text(
                    "ITEM", font_size=14,
                    color=(200, 200, 200, 200),
                    stroke_width=1, stroke_color=(0, 0, 0, 255),
                )
                base_img.alpha_composite(
                    txt,
                    (x + (size - txt.width) // 2, y + (size - txt.height) // 2),
                )


    def create_shop_image(self, user_id: str, page: int = 1) -> Image.Image:
        user_items = self.get_user_items(user_id)
        equipped_items = self.get_user_equipped(user_id)
        user = self.cache.get_user(user_id)
        user_level = user.get("level", 1) if user else 1

        if page not in PAGES:
            page = 1

        levels = PAGES[page]
        page_item_keys = self.get_items_for_page(page)

        LABEL_WIDTH = 200
        ITEM_WIDTH = 230
        ITEM_HEIGHT = 245
        MARGIN = 12
        PADDING = 10
        PREVIEW_SIZE = 90
        HEADER_HEIGHT = 135
        COL_HEADER_HEIGHT = 42
        FOOTER_HEIGHT = 70

        cols = len(levels)
        rows = len(ROW_CATEGORIES)

        grid_width = LABEL_WIDTH + cols * ITEM_WIDTH + MARGIN * 2
        width = max(1400, grid_width + MARGIN * 2)
        height = HEADER_HEIGHT + COL_HEADER_HEIGHT + rows * (ITEM_HEIGHT + MARGIN) + FOOTER_HEIGHT

        img = Image.new("RGBA", (width, height), (20, 20, 30, 255))
        draw = ImageDraw.Draw(img)

        if hasattr(self, "text_renderer"):
            title = self.text_renderer.render_text(
                "ITEM SHOP",
                font_size=36,
                color=(255, 215, 0, 255),
                stroke_width=2,
                stroke_color=(0, 0, 0, 255),
            )
            img.alpha_composite(title, ((width - title.width) // 2, 12))

            lvl_text = f"Your level: {user_level}"
            lvl_img = self.text_renderer.render_text(
                lvl_text, font_size=18,
                color=(200, 255, 200, 255),
                stroke_width=1, stroke_color=(0, 0, 0, 255),
            )
            img.alpha_composite(lvl_img, ((width - lvl_img.width) // 2, 58))

            range_text = f"Levels: {levels[0]} - {levels[-1]}"
            page_text = f"Page {page}/{TOTAL_PAGES}  |  {range_text}  |  75 items"
            page_img = self.text_renderer.render_text(
                page_text, font_size=15,
                color=(200, 200, 200, 220),
                stroke_width=1, stroke_color=(0, 0, 0, 255),
            )
            img.alpha_composite(page_img, ((width - page_img.width) // 2, 86))

        col_y = HEADER_HEIGHT
        grid_x = MARGIN
        for i, lvl in enumerate(levels):
            col_x = grid_x + LABEL_WIDTH + i * ITEM_WIDTH
            if hasattr(self, "text_renderer"):
                hdr = self.text_renderer.render_text(
                    f"LVL {lvl}", font_size=18,
                    color=(255, 220, 120, 255),
                    stroke_width=1, stroke_color=(0, 0, 0, 255),
                )
                img.alpha_composite(
                    hdr,
                    (col_x + (ITEM_WIDTH - hdr.width) // 2, col_y + 10),
                )

        row_y = HEADER_HEIGHT + COL_HEADER_HEIGHT
        for r, category in enumerate(ROW_CATEGORIES):
            label = CATEGORY_LABELS.get(category, category)
            if hasattr(self, "text_renderer"):
                lbl_img = self.text_renderer.render_text(
                    label, font_size=18,
                    color=(180, 220, 255, 255),
                    stroke_width=1, stroke_color=(0, 0, 0, 255),
                )
                img.alpha_composite(
                    lbl_img,
                    (MARGIN + 4, row_y + (ITEM_HEIGHT - lbl_img.height) // 2),
                )

            for c, lvl in enumerate(levels):
                idx = r * cols + c
                item_key = page_item_keys[idx] if idx < len(page_item_keys) else None
                cell_x = MARGIN + LABEL_WIDTH + c * ITEM_WIDTH
                cell_y = row_y

                if item_key is None:
                    draw.rounded_rectangle(
                        [cell_x, cell_y, cell_x + ITEM_WIDTH - MARGIN, cell_y + ITEM_HEIGHT],
                        radius=8,
                        fill=(30, 30, 40, 200),
                        outline=(60, 60, 80, 255),
                        width=1,
                    )
                    continue

                item_data = self.items_catalog[item_key]
                item_id = item_data["id"]
                is_owned = item_key in user_items
                is_equipped = item_key in equipped_items
                required_level = item_data.get("required_level", 1)
                can_use = user_level >= required_level

                if is_equipped:
                    fill_color = (0, 70, 0, 230)
                    border_color = (0, 255, 0, 255)
                elif is_owned:
                    fill_color = (0, 40, 70, 230)
                    border_color = (0, 150, 255, 255)
                elif not can_use:
                    fill_color = (140, 30, 30, 230)
                    border_color = (255, 60, 60, 255)
                else:
                    fill_color = (40, 40, 50, 220)
                    border_color = (100, 100, 120, 255)

                draw.rounded_rectangle(
                    [cell_x, cell_y, cell_x + ITEM_WIDTH - MARGIN, cell_y + ITEM_HEIGHT],
                    radius=8,
                    fill=fill_color,
                    outline=border_color,
                    width=2,
                )

                preview_x = cell_x + (ITEM_WIDTH - MARGIN - PREVIEW_SIZE) // 2
                preview_y = cell_y + PADDING
                self._draw_item_preview(img, preview_x, preview_y, PREVIEW_SIZE, item_data)

                text_y = preview_y + PREVIEW_SIZE + 8
                name_color = (255, 255, 255, 255) if can_use else (150, 150, 150, 255)
                if hasattr(self, "text_renderer"):
                    name_img = self.text_renderer.render_text(
                        item_data["name"][:22], font_size=16,
                        color=name_color,
                        stroke_width=1, stroke_color=(0, 0, 0, 255),
                    )
                    img.alpha_composite(
                        name_img,
                        (cell_x + (ITEM_WIDTH - MARGIN - name_img.width) // 2, text_y),
                    )
                    text_y += name_img.height + 4

                price_color = (255, 200, 0, 255) if can_use else (150, 150, 150, 255)
                if hasattr(self, "text_renderer"):
                    price_img = self.text_renderer.render_text(
                        f"$ {item_data['price']}", font_size=15,
                        color=price_color,
                        stroke_width=1, stroke_color=(0, 0, 0, 255),
                    )
                    img.alpha_composite(
                        price_img,
                        (cell_x + (ITEM_WIDTH - MARGIN - price_img.width) // 2, text_y),
                    )
                    text_y += price_img.height + 4

                if is_equipped:
                    status_text, status_color = "EQUIPPED", (100, 255, 100, 255)
                elif is_owned:
                    status_text, status_color = "OWNED", (200, 200, 200, 255)
                elif not can_use:
                    status_text, status_color = "LOCKED", (255, 100, 100, 255)
                else:
                    status_text, status_color = "AVAILABLE", (100, 200, 255, 255)

                if hasattr(self, "text_renderer"):
                    status_img = self.text_renderer.render_text(
                        status_text, font_size=13,
                        color=status_color,
                        stroke_width=1, stroke_color=(0, 0, 0, 255),
                    )
                    img.alpha_composite(
                        status_img,
                        (cell_x + (ITEM_WIDTH - MARGIN - status_img.width) // 2, text_y),
                    )

                if hasattr(self, "text_renderer"):
                    num_img = self.text_renderer.render_text(
                        f"#{item_id}", font_size=26,
                        color=(255, 255, 255, 200),
                        stroke_width=1, stroke_color=(0, 0, 0, 255),
                    )
                    img.alpha_composite(
                        num_img,
                        (cell_x + PADDING,
                         cell_y + ITEM_HEIGHT - num_img.height - PADDING),
                    )

            row_y += ITEM_HEIGHT + MARGIN

        footer_y = height - FOOTER_HEIGHT + 15
        if hasattr(self, "text_renderer"):
            if page > 1:
                prev_img = self.text_renderer.render_text(
                    f"< /items {page - 1}", font_size=17,
                    color=(100, 200, 255, 255),
                    stroke_width=1, stroke_color=(0, 0, 0, 255),
                )
                img.alpha_composite(prev_img, (MARGIN, footer_y))

            if page < TOTAL_PAGES:
                next_img = self.text_renderer.render_text(
                    f"/items {page + 1} >", font_size=17,
                    color=(100, 200, 255, 255),
                    stroke_width=1, stroke_color=(0, 0, 0, 255),
                )
                img.alpha_composite(
                    next_img,
                    (width - next_img.width - MARGIN, footer_y),
                )

            instr_img = self.text_renderer.render_text(
                "/items buy <id>  |  /items equip <id>  |  /items list",
                font_size=15,
                color=(200, 200, 200, 180),
                stroke_width=1, stroke_color=(0, 0, 0, 255),
            )
            img.alpha_composite(
                instr_img,
                ((width - instr_img.width) // 2, footer_y),
            )

        return img

    def execute_game(self, command_name: str, args: List[str], file_queue,
                     cache=None, sender: Optional[str] = None,
                     avatar_url: Optional[str] = None) -> str:
        self.cache = cache
        self._cleanup_old_items()

        user_id, user, error = self.validate_user(cache, sender, avatar_url)
        if error:
            self.send_message_image(sender, file_queue, error, "Validation Error", cache, user_id)
            return ""

        if len(args) == 0:
            args = ["shop"]

        cmd = args[0].lower()

        if cmd.isdigit():
            page = int(cmd)
            if page < 1 or page > TOTAL_PAGES:
                self.send_message_image(
                    sender, file_queue,
                    f"Page must be 1-{TOTAL_PAGES}",
                    "Invalid Page", cache, user_id,
                )
                return ""
            return self._show_shop(user_id, sender, file_queue, cache, user, page)

        if cmd == "shop" or cmd == "s":
            page = 1
            if len(args) > 1:
                try:
                    page = int(args[1])
                except ValueError:
                    page = 1
            if page < 1 or page > TOTAL_PAGES:
                page = 1
            return self._show_shop(user_id, sender, file_queue, cache, user, page)

        if cmd == "buy" or cmd == "b":
            return self._cmd_buy(user_id, user, sender, file_queue, cache, args)

        if cmd == "equip" or cmd == "e":
            return self._cmd_equip(user_id, sender, file_queue, cache, args)

        if cmd == "unequip" or cmd == "u":
            return self._cmd_unequip(user_id, sender, file_queue, cache, args)

        if cmd == "list" or cmd == "my":
            return self._cmd_list(user_id, sender, file_queue, cache)

        return self._cmd_help(sender, file_queue, cache, user_id)


    def _show_shop(self, user_id, sender, file_queue, cache, user, page: int) -> str:
        shop_img = self.create_shop_image(user_id, page)
        img_path = os.path.join(
            self.results_folder,
            f"items_shop_{user_id}_page{page}.webp",
        )
        shop_img.save(img_path, format="WEBP", quality=85)

        overlay_path, error = self.apply_user_overlay(
            img_path, user_id, sender, 0, 0, user["balance"], user,
            show_win_text=False, show_bet_amount=False,
        )
        if overlay_path:
            file_queue.put(overlay_path)

        return (
            f"ITEM SHOP (Page {page}/{TOTAL_PAGES})\n"
            f"/items buy <id> - buy\n"
            f"/items equip <id> - equip\n"
            f"/items <page> - change page"
        )

    def _cmd_buy(self, user_id, user, sender, file_queue, cache, args) -> str:
        if len(args) < 2:
            self.send_message_image(
                sender, file_queue,
                "Usage: /items buy <id>\nCheck IDs in /items shop",
                "Invalid Usage", cache, user_id,
            )
            return ""

        item_key = self._resolve_item_by_id(args[1])
        if not item_key:
            self.send_message_image(
                sender, file_queue,
                f"Choose ID 1-{len(self.items_catalog)}",
                "Invalid ID", cache, user_id,
            )
            return ""

        item_data = self.items_catalog[item_key]
        price = item_data.get("price", 0)

        can_buy, msg = self.can_buy_item(user_id, item_key)
        if not can_buy:
            self.send_message_image(sender, file_queue, msg, "Level Too Low", cache, user_id)
            return ""

        user_items = self.get_user_items(user_id)
        if item_key in user_items:
            equip_success, equip_msg = self.equip_item(user_id, item_key)
            if equip_success:
                self.send_message_image(
                    sender, file_queue,
                    f"Already owned - equipped: {item_data['name']}",
                    "Already Owned", cache, user_id,
                )
            else:
                self.send_message_image(
                    sender, file_queue,
                    f"Already owned: {item_data['name']}\n({equip_msg})",
                    "Already Owned", cache, user_id,
                )
            return ""

        if user["balance"] < price:
            self.send_message_image(
                sender, file_queue,
                f"You need: {price} coins\nYou have: {user['balance']} coins",
                "Insufficient Funds", cache, user_id,
            )
            return ""

        success, message = self.add_item(user_id, item_key)
        if not success:
            self.send_message_image(sender, file_queue, message, "Purchase Failed", cache, user_id)
            return ""

        self.cache.update_balance(user_id, -price)
        user["balance"] -= price

        self.equip_item(user_id, item_key)

        self.send_message_image(sender, file_queue, message, "Purchase Success", cache, user_id)
        return ""

    def _cmd_equip(self, user_id, sender, file_queue, cache, args) -> str:
        if len(args) < 2:
            self.send_message_image(
                sender, file_queue,
                "Usage: /items equip <id>",
                "Invalid Usage", cache, user_id,
            )
            return ""

        item_key = self._resolve_item_by_id(args[1])
        if not item_key:
            self.send_message_image(
                sender, file_queue,
                f"Choose ID 1-{len(self.items_catalog)}",
                "Invalid ID", cache, user_id,
            )
            return ""

        success, message = self.equip_item(user_id, item_key)
        title = "Equip Success" if success else "Equip Failed"
        self.send_message_image(sender, file_queue, message, title, cache, user_id)
        return ""

    def _cmd_unequip(self, user_id, sender, file_queue, cache, args) -> str:
        if len(args) < 2:
            self.send_message_image(
                sender, file_queue,
                "Usage: /items unequip <id>",
                "Invalid Usage", cache, user_id,
            )
            return ""

        item_key = self._resolve_item_by_id(args[1])
        if not item_key:
            self.send_message_image(
                sender, file_queue,
                f"Choose ID 1-{len(self.items_catalog)}",
                "Invalid ID", cache, user_id,
            )
            return ""

        success, message = self.unequip_item(user_id, item_key)
        title = "Unequip Success" if success else "Unequip Failed"
        self.send_message_image(sender, file_queue, message, title, cache, user_id)
        return ""

    def _cmd_list(self, user_id, sender, file_queue, cache) -> str:
        user_items = self.get_user_items(user_id)
        equipped = self.get_user_equipped(user_id)

        if not user_items:
            self.send_message_image(
                sender, file_queue,
                "You don't own any items!\nVisit /items shop to buy some.",
                "No Items", cache, user_id,
            )
            return ""

        lines = ["Your items:"]
        for item_key, _ in user_items.items():
            if item_key in self.items_catalog:
                info = self.items_catalog[item_key]
                status = "EQUIPPED" if item_key in equipped else "Owned"
                lines.append(f"#{info['id']} {info['name']} - {status}")

        self.send_message_image(
            sender, file_queue,
            "\n".join(lines),
            "My Items", cache, user_id,
        )
        return ""

    def _cmd_help(self, sender, file_queue, cache, user_id) -> str:
        help_text = (
            "ITEM SYSTEM /items\n\n"
            "Commands:\n"
            "  /items - Shop (page 1)\n"
            "  /items <page> - Selected page (1-5)\n"
            "  /items shop <page> - Same as above\n"
            "  /items buy <id> - Buy item (ID 1-75)\n"
            "  /items equip <id> - Equip\n"
            "  /items unequip <id> - Unequip\n"
            "  /items list - Your items\n\n"
            "Pages and levels:\n"
            "  1: 5, 10, 15, 20, 25\n"
            "  2: 30, 35, 40, 45, 50\n"
            "  3: 55, 60, 65, 70, 75\n"
            "  4: 80, 85, 90, 95, 100\n"
            "  5: 110, 120, 130, 140, 150\n\n"
            "Categories (rows):\n"
            "  Bet Icons\n"
            "  Balance Icons\n"
            "  Level Bars"
        )
        self.send_message_image(sender, file_queue, help_text, "Items Help", cache, user_id)
        return ""


def register():
    plugin = ItemsPlugin()
    return {
        "name": "items",
        "aliases": ["/item", "/items", "/i"],
        "description": (
            "Item System\n\n"
            "Customize your interface with items!\n\n"
            "Commands:\n"
            "  /items - Shop (page 1)\n"
            "  /items <page> - Page 1-5\n"
            "  /items buy <id> - Buy (ID 1-75)\n"
            "  /items equip <id> - Equip\n"
            "  /items unequip <id> - Unequip\n"
            "  /items list - Your items\n\n"
            "Pages: 5/10/15/20/25 | 30/35/40/45/50 | 55/60/65/70/75 | "
            "80/85/90/95/100 | 110/120/130/140/150"
        ),
        "execute": plugin.execute_game,
    }