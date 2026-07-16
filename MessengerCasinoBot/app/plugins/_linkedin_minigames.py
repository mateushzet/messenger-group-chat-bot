import os
import time
from dataclasses import dataclass
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ImageDraw, ImageFont


DAILY_COMPLETION_REWARD = 30

CANVAS_WIDTH = 720
CANVAS_HEIGHT = 820
TEXT_DARK = (22, 27, 37)
TEXT_LIGHT = (245, 248, 252)
MUTED = (169, 178, 194)
PANEL = (31, 38, 52)

QUEENS_REGION_COLORS = {
    "A": (231, 117, 116),
    "B": (245, 189, 92),
    "C": (113, 198, 151),
    "D": (103, 169, 229),
    "E": (183, 139, 229),
}


@dataclass(frozen=True)
class ValidationResult:
    solved: bool
    errors: List[str]


@dataclass(frozen=True)
class RewardResult:
    awarded: bool
    reward: int
    balance: int
    already_claimed: bool = False


@dataclass(frozen=True)
class QueensPuzzle:
    puzzle_id: str
    size: int
    regions: Tuple[str, ...]
    solution: Tuple[int, ...]

    @property
    def cell_count(self) -> int:
        return self.size * self.size

    def position(self, tile: int) -> Tuple[int, int]:
        index = tile - 1
        return index // self.size, index % self.size

    def validate_placements(self, placements: Iterable[int]) -> ValidationResult:
        tiles = tuple(placements)
        errors: List[str] = []

        if len(tiles) != self.size:
            errors.append(f"Place exactly {self.size} queens.")

        if any(tile < 1 or tile > self.cell_count for tile in tiles):
            errors.append(f"Tiles must be between 1 and {self.cell_count}.")

        if len(set(tiles)) != len(tiles):
            errors.append("Each tile can only be used once.")

        valid_tiles = [tile for tile in tiles if 1 <= tile <= self.cell_count]
        rows = [self.position(tile)[0] for tile in valid_tiles]
        cols = [self.position(tile)[1] for tile in valid_tiles]
        regions = [self.regions[tile - 1] for tile in valid_tiles]

        if len(rows) != self.size or len(set(rows)) != self.size:
            errors.append("Each row must contain exactly one queen.")

        if len(cols) != self.size or len(set(cols)) != self.size:
            errors.append("Each column must contain exactly one queen.")

        if len(regions) != self.size or len(set(regions)) != self.size:
            errors.append("Each region must contain exactly one queen.")

        for idx, first in enumerate(valid_tiles):
            first_row, first_col = self.position(first)
            for second in valid_tiles[idx + 1:]:
                second_row, second_col = self.position(second)
                if abs(first_row - second_row) <= 1 and abs(first_col - second_col) <= 1:
                    errors.append("Queens cannot touch, including diagonally.")
                    return ValidationResult(False, errors)

        return ValidationResult(not errors, errors)

    def format_board(self, placements: Iterable[int]) -> str:
        selected = set(placements)
        lines = []

        for row in range(self.size):
            cells = []
            for col in range(self.size):
                tile = row * self.size + col + 1
                region = self.regions[tile - 1]
                marker = "Q" if tile in selected else region
                cells.append(f"{tile:02d}{marker}")
            lines.append(" ".join(cells))

        return "\n".join(lines)


@dataclass(frozen=True)
class TangoPuzzle:
    puzzle_id: str
    size: int
    givens: Dict[int, str]
    solution: Dict[int, str]
    same_links: Tuple[Tuple[int, int], ...]
    different_links: Tuple[Tuple[int, int], ...]

    @property
    def cell_count(self) -> int:
        return self.size * self.size

    def row_tiles(self, row: int) -> List[int]:
        start = row * self.size + 1
        return list(range(start, start + self.size))

    def column_tiles(self, col: int) -> List[int]:
        return [row * self.size + col + 1 for row in range(self.size)]

    def validate_assignments(self, assignments: Dict[int, str]) -> ValidationResult:
        errors: List[str] = []
        normalized = {
            int(tile): str(value).upper()
            for tile, value in assignments.items()
            if str(value).upper() in ("S", "M")
        }

        if len(normalized) != len(assignments):
            errors.append("Cells must be S or M.")

        for tile, value in self.givens.items():
            if normalized.get(tile) != value:
                errors.append("Prefilled cells cannot be changed.")
                break

        if len(normalized) != self.cell_count:
            errors.append("All cells must be filled.")

        rows_balanced = True
        cols_balanced = True
        rows_without_runs = True
        cols_without_runs = True

        for row in range(self.size):
            values = [normalized.get(tile) for tile in self.row_tiles(row)]
            if values.count("S") != self.size // 2 or values.count("M") != self.size // 2:
                rows_balanced = False
            if _has_three_in_a_row(values):
                rows_without_runs = False

        for col in range(self.size):
            values = [normalized.get(tile) for tile in self.column_tiles(col)]
            if values.count("S") != self.size // 2 or values.count("M") != self.size // 2:
                cols_balanced = False
            if _has_three_in_a_row(values):
                cols_without_runs = False

        if not rows_balanced:
            errors.append("Rows must contain equal suns and moons.")
        if not cols_balanced:
            errors.append("Columns must contain equal suns and moons.")
        if not rows_without_runs:
            errors.append("Rows cannot contain three matching symbols in a row.")
        if not cols_without_runs:
            errors.append("Columns cannot contain three matching symbols in a row.")

        links_valid = True
        for first, second in self.same_links:
            if normalized.get(first) != normalized.get(second):
                links_valid = False
                break

        for first, second in self.different_links:
            if normalized.get(first) == normalized.get(second):
                links_valid = False
                break

        if not links_valid:
            errors.append("Linked cells must match their same/different clues.")

        return ValidationResult(not errors, errors)

    def format_board(self, assignments: Dict[int, str]) -> str:
        lines = []

        for row in range(self.size):
            cells = []
            for col in range(self.size):
                tile = row * self.size + col + 1
                value = assignments.get(tile, ".")
                fixed = "*" if tile in self.givens else ""
                cells.append(f"{tile:02d}{value}{fixed}")
            lines.append(" ".join(cells))

        return "\n".join(lines)

    def format_links(self) -> str:
        same = ", ".join(f"{a:02d}={b:02d}" for a, b in self.same_links) or "none"
        different = ", ".join(f"{a:02d}x{b:02d}" for a, b in self.different_links) or "none"
        return f"Same: {same}\nDifferent: {different}"


@dataclass(frozen=True)
class ZipPuzzle:
    puzzle_id: str
    size: int
    clues: Dict[int, int]
    solution: Tuple[int, ...]
    walls: Tuple[Tuple[int, int], ...] = ()

    @property
    def cell_count(self) -> int:
        return self.size * self.size

    def position(self, tile: int) -> Tuple[int, int]:
        index = tile - 1
        return index // self.size, index % self.size

    def validate_path(self, path: Sequence[int]) -> ValidationResult:
        tiles = tuple(path)
        errors: List[str] = []

        if any(tile < 1 or tile > self.cell_count for tile in tiles):
            errors.append(f"Tiles must be between 1 and {self.cell_count}.")

        if len(tiles) != self.cell_count or len(set(tiles)) != self.cell_count:
            errors.append("Path must cover every tile exactly once.")

        if tiles and tiles[0] != self.clues[min(self.clues.keys())]:
            errors.append("Path must start at clue 1.")

        if tiles and tiles[-1] != self.clues[max(self.clues.keys())]:
            errors.append("Path must end at the final clue.")

        wall_pairs = {tuple(sorted(pair)) for pair in self.walls}
        adjacent = True
        for first, second in zip(tiles, tiles[1:]):
            if not (1 <= first <= self.cell_count and 1 <= second <= self.cell_count):
                adjacent = False
                continue
            first_row, first_col = self.position(first)
            second_row, second_col = self.position(second)
            if abs(first_row - second_row) + abs(first_col - second_col) != 1:
                adjacent = False
                continue
            if tuple(sorted((first, second))) in wall_pairs:
                adjacent = False

        if not adjacent:
            errors.append("Path steps must move to orthogonally adjacent tiles.")

        clue_positions = []
        for clue_number in sorted(self.clues):
            clue_tile = self.clues[clue_number]
            if clue_tile not in tiles:
                clue_positions.append(None)
            else:
                clue_positions.append(tiles.index(clue_tile))

        if (
            any(position is None for position in clue_positions)
            or clue_positions != sorted(clue_positions)
        ):
            errors.append("Path must visit numbered clues in order.")

        return ValidationResult(not errors, errors)

    def format_board(self) -> str:
        clue_lookup = {tile: clue for clue, tile in self.clues.items()}
        lines = []

        for row in range(self.size):
            cells = []
            for col in range(self.size):
                tile = row * self.size + col + 1
                clue = clue_lookup.get(tile)
                marker = str(clue) if clue else "."
                cells.append(f"{tile:02d}{marker}")
            lines.append(" ".join(cells))

        return "\n".join(lines)

    def format_clues(self) -> str:
        parts = [f"{clue}@{tile:02d}" for clue, tile in sorted(self.clues.items())]
        return " -> ".join(parts)


def _has_three_in_a_row(values: Sequence[Optional[str]]) -> bool:
    for index in range(0, len(values) - 2):
        window = values[index:index + 3]
        if window[0] and window[0] == window[1] == window[2]:
            return True
    return False


def _font(size: int, bold: bool = False):
    names = ("arialbd.ttf", "Arial Bold.ttf", "arial.ttf", "Arial.ttf") if bold else (
        "arial.ttf",
        "Arial.ttf",
    )

    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue

    return ImageFont.load_default()


def _text_size(draw: ImageDraw.ImageDraw, text: str, font) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_centered_text(draw: ImageDraw.ImageDraw, box, text: str, font, fill) -> None:
    width, height = _text_size(draw, text, font)
    x1, y1, x2, y2 = box
    x = x1 + ((x2 - x1) - width) / 2
    y = y1 + ((y2 - y1) - height) / 2
    draw.text((x, y), text, font=font, fill=fill)


def _draw_wrapped_text(draw: ImageDraw.ImageDraw, text: str, x: int, y: int,
                       max_width: int, font, fill, line_spacing: int = 6) -> int:
    line_height = _text_size(draw, "Ag", font)[1] + line_spacing

    for paragraph in text.split("\n"):
        if not paragraph.strip():
            y += line_height
            continue

        words = paragraph.split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if _text_size(draw, candidate, font)[0] <= max_width:
                line = candidate
                continue

            if line:
                draw.text((x, y), line, font=font, fill=fill)
                y += line_height
            line = word

        if line:
            draw.text((x, y), line, font=font, fill=fill)
            y += line_height

    return y


def _new_canvas(title: str, status_text: str, accent: Tuple[int, int, int],
                height: int = CANVAS_HEIGHT):
    img = Image.new("RGB", (CANVAS_WIDTH, height), (18, 23, 33))
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, CANVAS_WIDTH, 118], fill=accent)
    draw.rectangle([0, 96, CANVAS_WIDTH, 118], fill=(18, 23, 33))
    _draw_centered_text(
        draw,
        (40, 22, CANVAS_WIDTH - 40, 64),
        title,
        _font(34, bold=True),
        TEXT_DARK,
    )

    status_y = _draw_wrapped_text(
        draw,
        status_text,
        48,
        132,
        CANVAS_WIDTH - 96,
        _font(22, bold=True),
        TEXT_LIGHT,
        line_spacing=7,
    )

    return img, draw, max(205, status_y + 24)


def _draw_footer(draw: ImageDraw.ImageDraw, text: str) -> None:
    footer_top = CANVAS_HEIGHT - 100
    draw.rounded_rectangle(
        [42, footer_top, CANVAS_WIDTH - 42, CANVAS_HEIGHT - 34],
        radius=18,
        fill=PANEL,
        outline=(67, 78, 98),
        width=2,
    )
    _draw_wrapped_text(
        draw,
        text,
        66,
        footer_top + 17,
        CANVAS_WIDTH - 132,
        _font(17),
        MUTED,
        line_spacing=4,
    )


def render_queens_image(puzzle: QueensPuzzle, placements: Iterable[int],
                        status_text: str) -> Image.Image:
    img, draw, board_y = _new_canvas("QUEENS", status_text, (244, 206, 82))
    selected = set(placements)
    cell = 86
    gap = 8
    board_size = puzzle.size * cell + (puzzle.size - 1) * gap
    board_x = (CANVAS_WIDTH - board_size) // 2

    for row in range(puzzle.size):
        for col in range(puzzle.size):
            tile = row * puzzle.size + col + 1
            region = puzzle.regions[tile - 1]
            x = board_x + col * (cell + gap)
            y = board_y + row * (cell + gap)
            color = QUEENS_REGION_COLORS.get(region, (160, 165, 178))

            draw.rounded_rectangle(
                [x, y, x + cell, y + cell],
                radius=16,
                fill=color,
                outline=(15, 18, 25),
                width=3,
            )
            draw.text((x + 9, y + 7), f"{tile:02d}", font=_font(18, bold=True), fill=TEXT_DARK)
            draw.text((x + cell - 25, y + cell - 28), region, font=_font(20, bold=True), fill=TEXT_DARK)

            if tile in selected:
                draw.ellipse(
                    [x + 20, y + 20, x + cell - 20, y + cell - 20],
                    fill=(21, 26, 36),
                    outline=(255, 255, 255),
                    width=3,
                )
                _draw_centered_text(
                    draw,
                    (x + 20, y + 20, x + cell - 20, y + cell - 20),
                    "Q",
                    _font(34, bold=True),
                    TEXT_LIGHT,
                )

    _draw_footer(
        draw,
        "Komendy: /queens <pole>, /queens set <pola>, /queens clear. "
        "Nagroda: 30 coins raz dziennie.",
    )
    return img


def render_tango_image(puzzle: TangoPuzzle, assignments: Dict[int, str],
                       status_text: str) -> Image.Image:
    img, draw, board_y = _new_canvas("TANGO", status_text, (112, 207, 173))
    cell = 100
    gap = 12
    board_size = puzzle.size * cell + (puzzle.size - 1) * gap
    board_x = (CANVAS_WIDTH - board_size) // 2
    centers: Dict[int, Tuple[int, int]] = {}

    for row in range(puzzle.size):
        for col in range(puzzle.size):
            tile = row * puzzle.size + col + 1
            x = board_x + col * (cell + gap)
            y = board_y + row * (cell + gap)
            centers[tile] = (x + cell // 2, y + cell // 2)
            value = assignments.get(tile)
            outline = (245, 248, 252) if tile in puzzle.givens else (72, 84, 106)

            draw.rounded_rectangle(
                [x, y, x + cell, y + cell],
                radius=18,
                fill=(42, 51, 68),
                outline=outline,
                width=3,
            )
            draw.text((x + 10, y + 8), f"{tile:02d}", font=_font(18, bold=True), fill=MUTED)

            if tile in puzzle.givens:
                draw.text((x + cell - 24, y + 8), "*", font=_font(22, bold=True), fill=TEXT_LIGHT)

            if value:
                if value == "S":
                    fill = (252, 203, 88)
                    text = "S"
                    text_fill = TEXT_DARK
                else:
                    fill = (83, 139, 231)
                    text = "M"
                    text_fill = TEXT_LIGHT

                draw.ellipse(
                    [x + 24, y + 24, x + cell - 24, y + cell - 24],
                    fill=fill,
                    outline=(255, 255, 255),
                    width=2,
                )
                _draw_centered_text(
                    draw,
                    (x + 24, y + 24, x + cell - 24, y + cell - 24),
                    text,
                    _font(30, bold=True),
                    text_fill,
                )

    for links, marker, fill in (
        (puzzle.same_links, "=", (252, 203, 88)),
        (puzzle.different_links, "x", (238, 112, 118)),
    ):
        for first, second in links:
            x1, y1 = centers[first]
            x2, y2 = centers[second]
            mx = (x1 + x2) // 2
            my = (y1 + y2) // 2
            draw.ellipse([mx - 17, my - 17, mx + 17, my + 17], fill=fill, outline=(18, 23, 33), width=3)
            _draw_centered_text(draw, (mx - 17, my - 17, mx + 17, my + 17), marker, _font(22, bold=True), TEXT_DARK)

    _draw_footer(
        draw,
        "Komendy: /tango <pole> sun|moon, /tango clear <pole>. "
        "S=Sun, M=Moon, *=pole stale. Nagroda: 30 coins raz dziennie.",
    )
    return img


def render_zip_image(puzzle: ZipPuzzle, path: Sequence[int],
                     status_text: str) -> Image.Image:
    img, draw, board_y = _new_canvas("ZIP", status_text, (124, 174, 244))
    cell = 100
    gap = 12
    board_size = puzzle.size * cell + (puzzle.size - 1) * gap
    board_x = (CANVAS_WIDTH - board_size) // 2
    centers: Dict[int, Tuple[int, int]] = {}
    clue_lookup = {tile: clue for clue, tile in puzzle.clues.items()}

    for row in range(puzzle.size):
        for col in range(puzzle.size):
            tile = row * puzzle.size + col + 1
            x = board_x + col * (cell + gap)
            y = board_y + row * (cell + gap)
            centers[tile] = (x + cell // 2, y + cell // 2)
            draw.rounded_rectangle(
                [x, y, x + cell, y + cell],
                radius=18,
                fill=(42, 51, 68),
                outline=(72, 84, 106),
                width=3,
            )
            draw.text((x + 10, y + 8), f"{tile:02d}", font=_font(18, bold=True), fill=MUTED)

    valid_path = [tile for tile in path if 1 <= tile <= puzzle.cell_count]
    if len(valid_path) > 1:
        points = [centers[tile] for tile in valid_path]
        draw.line(points, fill=(252, 203, 88), width=9)

    for step, tile in enumerate(valid_path, start=1):
        cx, cy = centers[tile]
        draw.ellipse([cx - 20, cy - 20, cx + 20, cy + 20], fill=(252, 203, 88), outline=(18, 23, 33), width=3)
        _draw_centered_text(draw, (cx - 20, cy - 20, cx + 20, cy + 20), str(step), _font(16, bold=True), TEXT_DARK)

    for tile, clue in clue_lookup.items():
        cx, cy = centers[tile]
        draw.ellipse([cx - 31, cy - 31, cx + 31, cy + 31], outline=(255, 255, 255), width=4)
        draw.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=(83, 139, 231))
        _draw_centered_text(draw, (cx - 24, cy - 24, cx + 24, cy + 24), str(clue), _font(26, bold=True), TEXT_LIGHT)

    _draw_footer(
        draw,
        "Komendy: /zip <pelna sciezka>, /zip add <pola>, /zip clear. "
        "Sciezka musi przejsc przez wszystkie pola i wskazowki po kolei.",
    )
    return img


def save_minigame_image(image: Image.Image, output_folder: str, prefix: str, user_id: str) -> str:
    os.makedirs(output_folder, exist_ok=True)
    safe_user_id = str(user_id).replace("\\", "_").replace("/", "_")
    filename = f"{prefix}_{safe_user_id}_{int(time.time() * 1000)}.png"
    output_path = os.path.join(output_folder, filename)
    image.save(output_path, "PNG")
    return output_path


def _today_key(today: Optional[date] = None) -> str:
    return (today or datetime.now().date()).isoformat()


def _select_daily(puzzles, today: Optional[date] = None):
    selected_day = today or datetime.now().date()
    return puzzles[selected_day.toordinal() % len(puzzles)]


def parse_tile_numbers(args: Sequence[str], max_tile: int) -> Tuple[List[int], List[str]]:
    tiles: List[int] = []
    errors: List[str] = []

    for arg in args:
        for part in str(arg).replace(",", " ").split():
            try:
                tile = int(part)
            except ValueError:
                errors.append(f"'{part}' is not a tile number.")
                continue

            if tile < 1 or tile > max_tile:
                errors.append(f"Tile {tile} must be between 1 and {max_tile}.")
            else:
                tiles.append(tile)

    return tiles, errors


def parse_tango_symbol(value: str) -> Optional[str]:
    normalized = str(value).strip().lower()
    if normalized in ("s", "sun", "1", "+"):
        return "S"
    if normalized in ("m", "moon", "0", "-"):
        return "M"
    return None


def normalize_tango_assignments(assignments: Optional[Dict]) -> Dict[int, str]:
    normalized: Dict[int, str] = {}
    if not assignments:
        return normalized

    for tile, value in assignments.items():
        symbol = parse_tango_symbol(str(value))
        if symbol:
            normalized[int(tile)] = symbol

    return normalized


def ensure_daily_state(cache, user_id: str, game_name: str, puzzle_id: str,
                       defaults: Dict, today: Optional[date] = None) -> Dict:
    date_key = _today_key(today)
    state = cache.get_game_state(user_id, game_name) if cache else None

    if not state or state.get("puzzle_date") != date_key or state.get("puzzle_id") != puzzle_id:
        state = {
            "puzzle_date": date_key,
            "puzzle_id": puzzle_id,
            "completed_date": None,
            **defaults,
        }
        cache.save_game_state(user_id, game_name, state)

    return state


def save_daily_state(cache, user_id: str, game_name: str, state: Dict) -> None:
    if cache:
        cache.save_game_state(user_id, game_name, state)


def award_daily_completion(cache, user_id: str, game_name: str, puzzle_id: str,
                           today: Optional[date] = None) -> RewardResult:
    date_key = _today_key(today)
    user = cache.get_user(user_id)
    balance = user.get("balance", 0) if user else 0
    state = cache.get_game_state(user_id, game_name) or {}

    if state.get("completed_date") == date_key:
        return RewardResult(False, 0, balance, already_claimed=True)

    balance = cache.update_balance(user_id, DAILY_COMPLETION_REWARD)
    state.update({
        "puzzle_date": date_key,
        "puzzle_id": puzzle_id,
        "completed_date": date_key,
        "reward": DAILY_COMPLETION_REWARD,
    })
    cache.save_game_state(user_id, game_name, state)

    return RewardResult(True, DAILY_COMPLETION_REWARD, balance)


QUEENS_PUZZLES: Tuple[QueensPuzzle, ...] = (
    QueensPuzzle(
        puzzle_id="queens-a",
        size=5,
        regions=(
            "A", "A", "B", "B", "B",
            "A", "A", "B", "B", "E",
            "C", "A", "D", "D", "E",
            "C", "C", "D", "D", "E",
            "C", "C", "D", "E", "E",
        ),
        solution=(2, 9, 11, 18, 25),
    ),
    QueensPuzzle(
        puzzle_id="queens-b",
        size=5,
        regions=(
            "A", "A", "A", "B", "B",
            "C", "A", "A", "B", "B",
            "C", "C", "D", "D", "B",
            "C", "C", "D", "D", "E",
            "E", "E", "E", "D", "E",
        ),
        solution=(3, 10, 12, 19, 21),
    ),
    QueensPuzzle(
        puzzle_id="queens-c",
        size=5,
        regions=(
            "A", "A", "A", "A", "A",
            "B", "B", "B", "C", "C",
            "D", "B", "B", "C", "C",
            "D", "D", "E", "E", "C",
            "D", "D", "E", "E", "E",
        ),
        solution=(4, 7, 15, 16, 23),
    ),
)


TANGO_PUZZLES: Tuple[TangoPuzzle, ...] = (
    TangoPuzzle(
        puzzle_id="tango-a",
        size=4,
        givens={1: "S", 4: "M", 6: "S", 11: "S", 13: "M", 16: "S"},
        solution={
            1: "S", 2: "S", 3: "M", 4: "M",
            5: "M", 6: "S", 7: "M", 8: "S",
            9: "S", 10: "M", 11: "S", 12: "M",
            13: "M", 14: "M", 15: "S", 16: "S",
        },
        same_links=((1, 2), (3, 4), (13, 14), (15, 16)),
        different_links=((2, 3), (5, 6), (9, 10), (11, 12)),
    ),
    TangoPuzzle(
        puzzle_id="tango-b",
        size=4,
        givens={1: "M", 4: "S", 6: "M", 11: "M", 13: "S", 16: "M"},
        solution={
            1: "M", 2: "M", 3: "S", 4: "S",
            5: "S", 6: "M", 7: "S", 8: "M",
            9: "M", 10: "S", 11: "M", 12: "S",
            13: "S", 14: "S", 15: "M", 16: "M",
        },
        same_links=((1, 2), (3, 4), (13, 14), (15, 16)),
        different_links=((2, 3), (5, 6), (9, 10), (11, 12)),
    ),
    TangoPuzzle(
        puzzle_id="tango-c",
        size=4,
        givens={1: "S", 4: "M", 6: "M", 11: "M", 13: "M", 16: "S"},
        solution={
            1: "S", 2: "M", 3: "S", 4: "M",
            5: "M", 6: "M", 7: "S", 8: "S",
            9: "S", 10: "S", 11: "M", 12: "M",
            13: "M", 14: "S", 15: "M", 16: "S",
        },
        same_links=((3, 7), (6, 5), (9, 10), (12, 11)),
        different_links=((1, 2), (4, 8), (13, 14), (15, 16)),
    ),
)


ZIP_PUZZLES: Tuple[ZipPuzzle, ...] = (
    ZipPuzzle(
        puzzle_id="zip-a",
        size=4,
        clues={1: 1, 2: 8, 3: 9, 4: 16, 5: 13},
        solution=(1, 2, 3, 4, 8, 7, 6, 5, 9, 10, 11, 12, 16, 15, 14, 13),
    ),
    ZipPuzzle(
        puzzle_id="zip-b",
        size=4,
        clues={1: 4, 2: 5, 3: 12, 4: 13, 5: 16},
        solution=(4, 3, 2, 1, 5, 6, 7, 8, 12, 11, 10, 9, 13, 14, 15, 16),
    ),
    ZipPuzzle(
        puzzle_id="zip-c",
        size=4,
        clues={1: 13, 2: 16, 3: 4, 4: 9, 5: 6},
        solution=(13, 14, 15, 16, 12, 8, 4, 3, 2, 1, 5, 9, 10, 11, 7, 6),
    ),
)


def get_daily_queens_puzzle(today: Optional[date] = None) -> QueensPuzzle:
    return _select_daily(QUEENS_PUZZLES, today)


def get_daily_tango_puzzle(today: Optional[date] = None) -> TangoPuzzle:
    return _select_daily(TANGO_PUZZLES, today)


def get_daily_zip_puzzle(today: Optional[date] = None) -> ZipPuzzle:
    return _select_daily(ZIP_PUZZLES, today)
