import os
import random
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageSequence

from base_game_plugin import BaseGamePlugin
from logger import logger
from plugins.monthly import record_monthly_win


class FifaPackOpeningPlugin(BaseGamePlugin):

    PACK_SIZE = 5
    PACK_COST = 2000
    PACK_NAME = "all"

    def __init__(self):
        super().__init__(game_name="fifa")

    def _cards_root(self) -> Path:
        return Path(__file__).resolve().parent.parent / "assets" / "fifa" / "cards"

    def _results_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent / "results"

    def _coins_icon_path(self) -> Path:
        return Path(__file__).resolve().parent.parent / "assets" / "fifa" / "fifa_coins.png"

    def _list_cards(self) -> List[Path]:
        root = self._cards_root()
        if not root.exists() or not root.is_dir():
            return []
        return [p for p in root.rglob("*.png") if p.is_file()]

    def _pick_cards(self, count: int) -> List[Path]:
        cards = self._list_cards()
        if not cards:
            return []
        return random.choices(cards, k=max(1, int(count)))

    def _extract_price(self, card_path: Path) -> int:
        name = card_path.name
        marker = "_price_"
        idx = name.lower().rfind(marker)
        if idx < 0:
            return 0
        tail = name[idx + len(marker) :]
        num = ""
        for ch in tail:
            if ch.isdigit():
                num += ch
            else:
                break
        try:
            return int(num) if num else 0
        except Exception:
            return 0

    def _load_and_resize_cards(self, paths: List[Path], target_h: int = 180) -> List[Image.Image]:  # Zmniejszone z 360 na 180
        images: List[Image.Image] = []
        for p in paths:
            try:
                img = Image.open(p).convert("RGBA")
                if img.height != target_h:
                    scale = target_h / float(img.height)
                    target_w = max(1, int(round(img.width * scale)))
                    img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                images.append(img)
            except Exception:
                continue
        return images

    def _compose_grid(self, images: List[Image.Image], cols: int = 3, pad: int = 18, bg=(10, 12, 18, 255)) -> Optional[Image.Image]:
        if not images:
            return None
        cols = max(1, int(cols))
        rows = (len(images) + cols - 1) // cols

        cell_w = max(img.width for img in images)
        cell_h = max(img.height for img in images)

        width = pad + cols * cell_w + (cols - 1) * pad + pad
        height = pad + rows * cell_h + (rows - 1) * pad + pad
        canvas = Image.new("RGBA", (width, height), bg)

        for idx, img in enumerate(images):
            r = idx // cols
            c = idx % cols
            x0 = pad + c * (cell_w + pad) + (cell_w - img.width) // 2
            y0 = pad + r * (cell_h + pad) + (cell_h - img.height) // 2
            canvas.alpha_composite(img, (x0, y0))

        return canvas

    def _draw_card_placeholders(self, canvas: Image.Image, cols: int, rows: int, cell_w: int, cell_h: int, pad: int):
        slot = Image.new("RGBA", (cell_w, cell_h), (255, 255, 255, 0))
        try:
            from PIL import ImageDraw

            d = ImageDraw.Draw(slot)
            d.rounded_rectangle([0, 0, cell_w - 1, cell_h - 1], radius=18, outline=(220, 220, 230, 80), width=3, fill=(255, 255, 255, 20))
        except Exception:
            pass

        for r in range(rows):
            for c in range(cols):
                x0 = pad + c * (cell_w + pad)
                y0 = pad + r * (cell_h + pad)
                canvas.alpha_composite(slot, (x0, y0))

    def _load_coins_icon(self, target_h: int = 20) -> Optional[Image.Image]:  # Zmniejszone z 22 na 20
        p = self._coins_icon_path()
        if not p.exists():
            return None
        try:
            icon = Image.open(p).convert("RGBA")
            if icon.height != target_h:
                scale = target_h / float(icon.height)
                w = max(1, int(round(icon.width * scale)))
                icon = icon.resize((w, target_h), Image.Resampling.LANCZOS)
            return icon
        except Exception:
            return None

    def _draw_price_tag(
        self,
        img: Image.Image,
        pos: Tuple[int, int],
        price: int,
        coin_icon: Optional[Image.Image],
        pad: int = 5,  # Zmniejszone z 10 na 5
    ):
        x, y = pos
        if not self.text_renderer:
            return
        tag_h = 28
        tag_w = 100
        bg = Image.new("RGBA", (tag_w, tag_h), (0, 0, 0, 150))
        draw = ImageDraw.Draw(bg)
        try:
            draw.rounded_rectangle([0, 0, tag_w - 1, tag_h - 1], radius=8, outline=(255, 255, 255, 80), width=2)
        except Exception:
            pass

        cursor_x = 6
        if coin_icon:
            bg.alpha_composite(coin_icon, (cursor_x, (tag_h - coin_icon.height) // 2))
            cursor_x += coin_icon.width + 5

        text = str(int(price))
        text_img = self.text_renderer.render_text(text, 14, (255, 255, 255, 255))
        bg.alpha_composite(text_img, (cursor_x, (tag_h - text_img.height) // 2))

        img.alpha_composite(bg, (x + pad, y + pad))

    def _compose_pack_opening_animation(
        self,
        tier: str,
        cards: List[Image.Image],
        prices: List[int],
        pack_cost: int,
        reveal_frames: int = 6,
        start_hold: int = 3,
        end_hold: int = 6,
        pad: int = 10,
        bg=(0, 0, 0, 0),
    ) -> Optional[List[Image.Image]]:
        if not cards or len(cards) != len(prices):
            return None

        coin_icon = self._load_coins_icon(target_h=16)

        if len(cards) != 5:
            return None

        cell_w = max(img.width for img in cards)
        cell_h = max(img.height for img in cards)

        stack_gap = max(5, pad // 2)
        col_gap = max(5, pad // 2)
        margin = 40

        inner_w = pad + (cell_w * 3) + (col_gap * 2) + pad
        inner_h = pad + (cell_h * 2) + stack_gap + pad
        base_w = inner_w + margin * 2
        base_h = inner_h + margin * 2

        best_idx = max(range(len(prices)), key=lambda i: prices[i])
        best_card = cards[best_idx]

        other_indices = [i for i in range(5) if i != best_idx]
        left_top, left_bottom, right_top, right_bottom = other_indices[0], other_indices[1], other_indices[2], other_indices[3]

        left_x = margin + pad
        center_x = margin + pad + (cell_w + col_gap)
        right_x = margin + pad + 2 * (cell_w + col_gap)

        top_y = margin + pad
        bottom_y = margin + pad + cell_h + stack_gap
        center_y = margin + pad + ((inner_h - 2 * pad - cell_h) // 2)

        positions_by_index = {
            best_idx: (center_x, center_y),
            left_top: (left_x, top_y),
            left_bottom: (left_x, bottom_y),
            right_top: (right_x, top_y),
            right_bottom: (right_x, bottom_y),
        }
        positions: List[Tuple[int, int]] = [positions_by_index[i] for i in range(5)]

        def new_base() -> Image.Image:
            base = Image.new("RGBA", (base_w, base_h), bg)
            panel = Image.new("RGBA", (inner_w, inner_h), (0, 0, 0, 0))
            try:
                d = ImageDraw.Draw(panel)
                d.rounded_rectangle(
                    [0, 0, inner_w - 1, inner_h - 1],
                    radius=20,
                    outline=(255, 255, 255, 30),
                    width=2,
                    fill=(27, 36, 38, 235),
                )
            except Exception:
                panel = Image.new("RGBA", (inner_w, inner_h), (27, 36, 38, 235))

            base.alpha_composite(panel, (margin, margin))
            return base

        frames: List[Image.Image] = []

        strip_h = 40
        try:
            strip = best_card.crop(
                (
                    0,
                    max(0, best_card.height - strip_h + 5),
                    max(0, best_card.width - 20),
                    max(0, best_card.height - 10),
                )
            )
            max_w = int(round(base_w* 0.9))
            max_h = int(round(base_h * 0.7))
        except Exception:
            strip = None

        if strip:
            for step in range(1, 13):
                t = step / 12.0
                w = max(1, int(round(max_w * (0.1 + 0.9 * t))))
                h = max(1, int(round(max_h * (0.1 + 0.9 * t))))
                stretch_w = min(int(round(w * 1.12)), int(round(base_w * 0.8)))
                teaser = strip.resize((stretch_w, h), Image.Resampling.BICUBIC)
                f = new_base()
                x = (base_w - teaser.width) // 2
                y = (base_h - teaser.height) // 2
                plate = Image.new("RGBA", (teaser.width + 20, teaser.height + 20), (0, 0, 0, 110))
                f.alpha_composite(plate, (x - 10, y - 10))
                f.alpha_composite(teaser, (x, y))
                frames.append(f)

            final_w = min(int(round(max_w * 1.12)), int(round(base_w * 0.8)))
            teaser_full = strip.resize((final_w, max_h), Image.Resampling.BICUBIC)
            for _ in range(max(6, start_hold * 2)):
                f = new_base()
                x = (base_w - teaser_full.width) // 2
                y = (base_h - teaser_full.height) // 2
                plate = Image.new("RGBA", (teaser_full.width + 20, teaser_full.height + 20), (0, 0, 0, 110))
                f.alpha_composite(plate, (x - 10, y - 10))
                f.alpha_composite(teaser_full, (x, y))
                frames.append(f)
        else:
            base = new_base()
            for _ in range(start_hold):
                frames.append(base.copy())

        reveal_bg = new_base()
        reveal_center_x = base_w // 2
        reveal_center_y = base_h // 2
        for step in range(1, 7):
            t = step / 6.0
            scale = 1.18 - 0.18 * t
            alpha = int(round(255 * t))
            card = best_card.copy()
            w = max(1, int(round(card.width * scale)))
            h = max(1, int(round(card.height * scale)))
            card = card.resize((w, h), Image.Resampling.LANCZOS)
            a = card.split()[-1].point(lambda v, a=alpha: int(v * a / 255))
            card.putalpha(a)
            f = reveal_bg.copy()
            f.alpha_composite(card, (reveal_center_x - w // 2, reveal_center_y - h // 2))
            frames.append(f)
        for _ in range(6):
            f = new_base()
            f.alpha_composite(best_card, (reveal_center_x - best_card.width // 2, reveal_center_y - best_card.height // 2))
            frames.append(f)

        reveal_order = [best_idx, left_top, left_bottom, right_top, right_bottom]
        revealed_set = set()
        for idx in reveal_order:
            card = cards[idx]
            for step in range(1, reveal_frames + 1):
                f = new_base()
                for j in reveal_order:
                    if j in revealed_set:
                        f.alpha_composite(cards[j], positions_by_index[j])
                        self._draw_price_tag(f, positions_by_index[j], prices[j], coin_icon)

                alpha = int(round(255 * (step / float(reveal_frames))))
                y_offset = int(round((1.0 - (step / float(reveal_frames))) * 8))
                card_step = card.copy()
                a = card_step.split()[-1].point(lambda v, a=alpha: int(v * a / 255))
                card_step.putalpha(a)
                x, y = positions_by_index[idx]
                f.alpha_composite(card_step, (x, y + y_offset))
                frames.append(f)

            revealed_set.add(idx)
            for _ in range(2):
                f = new_base()
                for j in reveal_order:
                    if j in revealed_set:
                        f.alpha_composite(cards[j], positions_by_index[j])
                        self._draw_price_tag(f, positions_by_index[j], prices[j], coin_icon)
                frames.append(f)

        final = new_base()
        for i, card in enumerate(cards):
            final.alpha_composite(card, positions_by_index[i])
            self._draw_price_tag(final, positions_by_index[i], prices[i], coin_icon)
        for _ in range(end_hold):
            frames.append(final.copy())

        return frames

    def _save_pack_animation(self, pack_name: str, card_paths: List[Path], pack_cost: int) -> Optional[str]:
        images = self._load_and_resize_cards(card_paths, target_h=180)
        prices = [self._extract_price(p) for p in card_paths]
        frames = self._compose_pack_opening_animation(pack_name, images, prices, pack_cost=pack_cost)
        if not frames:
            return None

        out_dir = self._results_dir()
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"fifa_pack_{pack_name}_{random.randint(1000, 9999)}.webp"
        try:
            frames[0].save(
                out_path,
                format="WEBP",
                save_all=True,
                append_images=frames[1:],
                duration=100,
                loop=0,
                quality=85,
            )
            return str(out_path)
        except Exception:
            return None

    def _usage(self) -> str:
        return (
            "PACK OPENING\n\n"
            "Commands:\n"
            "• /fifa open\n\n"
            "Cost: 2000"
        )

    def execute_game(self, command_name: str, args: List[str], file_queue, cache=None, sender: str = None, avatar_url: str = None) -> str:
        self.cache = cache

        if not args:
            self.send_message_image(sender, file_queue, self._usage(), "FIFA - Pack Opening", cache, None)
            return ""

        sub = args[0].lower().strip()
        if sub in ("help", "h", "?"):
            self.send_message_image(sender, file_queue, self._usage(), "FIFA - Help", cache, None)
            return ""

        if sub not in ("open", "o"):
            self.send_message_image(sender, file_queue, self._usage(), "FIFA - Pack Opening", cache, None)
            return ""

        count = self.PACK_SIZE
        pack_cost = self.PACK_COST
        user_id, user, err = self.validate_user_and_balance(cache, sender, avatar_url, pack_cost)
        if err:
            self.send_message_image(sender, file_queue, f"Insufficient funds.\n\nCost: {pack_cost}", "FIFA - Pack Opening", cache, user_id)
            return ""

        balance_before = int(user.get("balance", 0))
        balance_after_bet = balance_before - pack_cost
        self.update_user_balance(user_id, balance_after_bet)
        user["balance"] = balance_after_bet

        picks = self._pick_cards(count)
        if not picks:
            self.send_message_image(sender, file_queue, "No card assets found.", "FIFA - Error", cache, None)
            return ""

        total_value = sum(self._extract_price(p) for p in picks)
        net = int(total_value - pack_cost)
        new_balance = balance_after_bet + int(total_value)
        self.update_user_balance(user_id, new_balance)
        user["balance"] = new_balance

        try:
            new_level, new_progress = self.cache.add_experience(user_id, net, sender, file_queue)
            user["level"] = new_level
            user["level_progress"] = new_progress
        except Exception as e:
            logger.warning(f"[Fifa] add_experience failed: {e}")

        if net > 0:
            record_monthly_win(self.cache, user_id, "fifa", net)

        out = self._save_pack_animation(self.PACK_NAME, picks, pack_cost=pack_cost)
        if not out or not os.path.exists(out):
            self.send_message_image(sender, file_queue, "Failed to generate pack image.", "FIFA - Error", cache, None)
            return ""

        user_info_before = self.create_user_info(sender, pack_cost, 0, balance_before, user)
        user_info_after = self.create_user_info(sender, pack_cost, net, new_balance, user)
        
        result_path, error = self.generate_animation(
            base_animation_path=out,
            user_id=user_id,
            user=user,
            user_info_before=user_info_before,
            user_info_after=user_info_after,
            animated=True,
            frame_duration=100,
            last_frame_multiplier=30,
            show_win_text=True,
            font_scale=0.7,
            avatar_size=50,
        )

        if result_path:
            file_queue.put(result_path)
            return ""

        logger.error(f"[FIFA] Overlay generation failed: {error}")
        file_queue.put(out)
        return ""


def register():
    plugin = FifaPackOpeningPlugin()
    return {
        "name": "fifa",
        "aliases": ["/pack", "/packs", "/fc"],
        "description": "Pack opening (replacement for FIFA game). Use: /fifa open. Cost: 2000",
        "execute": plugin.execute_game,
    }
