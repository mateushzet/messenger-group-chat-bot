import os
import random
from PIL import Image

from base_game_plugin import BaseGamePlugin
from logger import logger
from plugins.monthly import record_monthly_win
from plugins.weekly import record_weekly_win


class DragonTowerGame:

    MAX_LEVELS = 9

    DIFFICULTIES = {
        "easy": {
            "tiles": 4,
            "safe": 3,
            "multipliers": [
                1.31, 1.74, 2.32, 3.10, 4.13,
                5.51, 7.34, 9.79, 13.05
            ]
        },
        "medium": {
            "tiles": 3,
            "safe": 2,
            "multipliers": [
                1.47, 2.21, 3.31, 4.96, 7.44,
                11.16, 16.74, 25.11, 37.67
            ]
        },
        "hard": {
            "tiles": 2,
            "safe": 1,
            "multipliers": [
                1.96, 3.92, 7.84, 15.68, 31.36,
                62.72, 125.44, 250.44, 501.76
            ]
        },
        "expert": {
            "tiles": 3,
            "safe": 1,
            "multipliers": [
                2.94, 8.82, 26.46, 79.38, 238.14,
                714.42, 2143.26, 6429.78, 19289.34
            ]
        },
        "master": {
            "tiles": 4,
            "safe": 1,
            "multipliers": [
                3.92, 15.68, 62.72, 250.88, 1003.52,
                4014.08, 16056.32, 64225.28, 256901.12
            ]
        }
    }

    def __init__(self, bet, difficulty="easy"):

        self.bet = bet
        self.difficulty = difficulty.lower()

        config = DragonTowerGame.DIFFICULTIES[self.difficulty]

        self.tiles_per_level = config["tiles"]
        self.safe_per_level = config["safe"]
        self.multipliers = config["multipliers"]

        self.current_level = 0

        self.game_over = False
        self.won = False
        self.cashout = False

        self.tower = []

        self.revealed = {}

        self.losing_tiles = {}

        self.selected_tile = None
        self.last_result = None

        self._generate_tower()

    def _generate_tower(self):

        self.tower = []

        for _ in range(self.MAX_LEVELS):

            safe_positions = random.sample(
                range(self.tiles_per_level),
                self.safe_per_level
            )

            level = [
                tile_index in safe_positions
                for tile_index in range(self.tiles_per_level)
            ]

            self.tower.append(level)

    def reveal(self, tile):

        if self.game_over:
            return "game_over"

        if tile < 1 or tile > self.tiles_per_level:
            return "invalid"

        tile_index = tile - 1

        if tile_index in self.revealed.get(
            self.current_level,
            set()
        ):
            return "already_revealed"

        current_level = self.current_level

        if current_level not in self.revealed:
            self.revealed[current_level] = set()

        self.revealed[current_level].add(tile_index)

        self.selected_tile = tile

        is_safe = self.tower[current_level][tile_index]

        if not is_safe:

            self.game_over = True
            self.won = False
            self.last_result = "skull"

            self.losing_tiles[current_level] = tile_index

            self.revealed[current_level] = set(
                range(self.tiles_per_level)
            )

            return "skull"

        self.last_result = "egg"

        self.current_level += 1

        if self.current_level >= self.MAX_LEVELS:

            self.game_over = True
            self.won = True
            self.last_result = "auto_win"

            return "auto_win"

        return "egg"

    def get_current_multiplier(self):

        if self.current_level <= 0:
            return 1.0

        index = min(
            self.current_level - 1,
            len(self.multipliers) - 1
        )

        return self.multipliers[index]

    def get_next_multiplier(self):

        if self.current_level >= self.MAX_LEVELS:
            return self.multipliers[-1]

        return self.multipliers[self.current_level]

    def get_payout(self):

        multiplier = self.get_current_multiplier()

        return int(
            self.bet * multiplier
        )

    def get_profit(self):

        return self.get_payout() - self.bet


class DragonTowerPlugin(BaseGamePlugin):

    CACHE_KEY = "active_dragon_tower_games"

    def __init__(self):

        logger.info(
            "[DragonTower] Initializing Dragon Tower plugin"
        )

        super().__init__(
            game_name="dragon_tower"
        )

        self.active_games = {}

        self.elements_folder = self.get_asset_path(
            "dragon_tower",
            "board_elements"
        )

        self.avatar_size = 80
        self.font_scale = 0.9

        self.loaded_images = {}

        self.cache = None
        self.cache_loaded = False

    def _save_active_games_to_cache(self):

        if not self.cache:
            return

        try:

            games_data = {}

            for user_id, game in self.active_games.items():

                games_data[str(user_id)] = {
                    "bet": game.bet,
                    "difficulty": game.difficulty,

                    "tower": game.tower,

                    "current_level": game.current_level,
                    "game_over": game.game_over,
                    "won": game.won,
                    "cashout": game.cashout,

                    "revealed": {
                        str(level): list(tiles)
                        for level, tiles in game.revealed.items()
                    },

                    "losing_tiles": {
                        str(level): tile
                        for level, tile in game.losing_tiles.items()
                    },

                    "selected_tile": game.selected_tile,
                    "last_result": game.last_result
                }

            self.cache.set_setting(
                self.CACHE_KEY,
                games_data
            )

            logger.debug(
                f"[DragonTower] Saved "
                f"{len(games_data)} active games"
            )

        except Exception as exc:

            logger.error(
                f"[DragonTower] Failed to save games: {exc}"
            )

    def _load_active_games_from_cache(self):

        if not self.cache:
            return

        if self.cache_loaded:
            return

        self.cache_loaded = True

        try:

            games_data = self.cache.get_setting(
                self.CACHE_KEY
            )

            if not games_data:

                logger.debug(
                    "[DragonTower] No saved games in cache"
                )

                return

            if not isinstance(games_data, dict):

                logger.warning(
                    "[DragonTower] Invalid cached game data"
                )

                return

            restored_games = {}

            for user_id_str, data in games_data.items():

                try:

                    user_id = str(user_id_str)

                    if not isinstance(data, dict):
                        continue

                    bet = int(
                        data.get("bet", 0)
                    )

                    difficulty = str(
                        data.get(
                            "difficulty",
                            "easy"
                        )
                    ).lower()

                    if bet <= 0:
                        continue

                    if difficulty not in DragonTowerGame.DIFFICULTIES:
                        continue

                    tower = data.get("tower")

                    if not isinstance(tower, list):
                        continue

                    if len(tower) != DragonTowerGame.MAX_LEVELS:
                        continue

                    config = DragonTowerGame.DIFFICULTIES[
                        difficulty
                    ]

                    valid_tower = True

                    for level in tower:

                        if not isinstance(level, list):
                            valid_tower = False
                            break

                        if len(level) != config["tiles"]:
                            valid_tower = False
                            break

                    if not valid_tower:
                        continue

                    game = DragonTowerGame(
                        bet,
                        difficulty
                    )

                    game.tower = [
                        [
                            bool(value)
                            for value in level
                        ]
                        for level in tower
                    ]

                    game.current_level = int(
                        data.get(
                            "current_level",
                            0
                        )
                    )

                    game.game_over = bool(
                        data.get(
                            "game_over",
                            False
                        )
                    )

                    game.won = bool(
                        data.get(
                            "won",
                            False
                        )
                    )

                    game.cashout = bool(
                        data.get(
                            "cashout",
                            False
                        )
                    )

                    game.revealed = {}

                    revealed_data = data.get(
                        "revealed",
                        {}
                    )

                    if isinstance(
                        revealed_data,
                        dict
                    ):

                        for level_str, tiles in revealed_data.items():

                            try:

                                level = int(level_str)

                                if not isinstance(
                                    tiles,
                                    list
                                ):
                                    continue

                                game.revealed[level] = set(
                                    int(tile)
                                    for tile in tiles
                                )

                            except (
                                ValueError,
                                TypeError
                            ):

                                continue

                    game.losing_tiles = {}

                    losing_data = data.get(
                        "losing_tiles",
                        {}
                    )

                    if isinstance(
                        losing_data,
                        dict
                    ):

                        for level_str, tile in losing_data.items():

                            try:

                                game.losing_tiles[
                                    int(level_str)
                                ] = int(tile)

                            except (
                                ValueError,
                                TypeError
                            ):

                                continue

                    game.selected_tile = data.get(
                        "selected_tile"
                    )

                    if game.selected_tile is not None:

                        try:

                            game.selected_tile = int(
                                game.selected_tile
                            )

                        except (
                            ValueError,
                            TypeError
                        ):

                            game.selected_tile = None

                    game.last_result = data.get(
                        "last_result"
                    )

                    if game.game_over:
                        continue

                    restored_games[user_id] = game

                except Exception as exc:

                    logger.error(
                        f"[DragonTower] Failed to restore "
                        f"user {user_id_str}: {exc}"
                    )

            self.active_games = restored_games

            logger.info(
                f"[DragonTower] Restored "
                f"{len(self.active_games)} games from cache"
            )

            self._save_active_games_to_cache()

        except Exception as exc:

            logger.error(
                f"[DragonTower] Failed to load active games: {exc}"
            )

    def _load_images(self):

        if self.loaded_images:
            return

        asset_names = [
            "background",
            "tile_hidden",
            "tile_current",
            "tile_egg",
            "tile_skull",
            "tile_lose",
            "tile_win"
        ]

        for name in asset_names:

            path = os.path.join(
                self.elements_folder,
                f"{name}.png"
            )

            try:

                self.loaded_images[name] = Image.open(
                    path
                ).convert("RGBA")

                logger.info(
                    f"[DragonTower] Loaded asset: {path}"
                )

            except Exception as exc:

                self.loaded_images[name] = None

                logger.warning(
                    f"[DragonTower] Failed to load "
                    f"{path}: {exc}"
                )

        for difficulty in DragonTowerGame.DIFFICULTIES:

            path = os.path.join(
                self.elements_folder,
                f"dragon_{difficulty}.png"
            )

            try:

                self.loaded_images[
                    f"dragon_{difficulty}"
                ] = Image.open(
                    path
                ).convert("RGBA")

                logger.info(
                    f"[DragonTower] Loaded dragon "
                    f"{difficulty}: {path}"
                )

            except Exception as exc:

                self.loaded_images[
                    f"dragon_{difficulty}"
                ] = None

                logger.warning(
                    f"[DragonTower] Failed to load "
                    f"dragon {difficulty}: {exc}"
                )

    def _get_user_background(
        self,
        user_id,
        width,
        height
    ):

        if not self.cache:
            return None

        try:

            bg_path = self.cache.get_background_path(
                user_id
            )

            if not bg_path:
                return None

            if not os.path.exists(bg_path):
                return None

            background = Image.open(
                bg_path
            ).convert("RGBA")

            background = background.resize(
                (width, height),
                Image.Resampling.LANCZOS
            )

            return background

        except Exception as exc:

            logger.warning(
                f"[DragonTower] Failed to load user "
                f"background for {user_id}: {exc}"
            )

            return None

    def _render_text(
        self,
        image,
        text,
        x,
        y,
        font_size=14,
        color=(255, 255, 255),
        center=True
    ):

        if not self.text_renderer:
            return

        text_img = self.text_renderer.render_text(
            text=str(text),
            font_size=font_size,
            color=color
        )

        if center:

            x -= text_img.width // 2
            y -= text_img.height // 2

        image.paste(
            text_img,
            (int(x), int(y)),
            text_img
        )

    def _draw_tile(
        self,
        image,
        x,
        y,
        tile_type,
        width=120,
        height=70
    ):

        asset = self.loaded_images.get(
            tile_type
        )

        if not asset:
            return

        tile = asset.resize(
            (width, height),
            Image.Resampling.LANCZOS
        )

        image.paste(
            tile,
            (int(x), int(y)),
            tile
        )

    def get_game_state_image(
        self,
        game,
        output_path,
        result=None,
        user_id=None
    ):

        self._load_images()

        WIDTH = 600
        HEIGHT = 900

        user_background = self._get_user_background(
            user_id,
            WIDTH,
            HEIGHT
        )

        if user_background:

            image = user_background

        else:

            image = Image.new(
                "RGBA",
                (WIDTH, HEIGHT),
                (15, 15, 25, 255)
            )

        tower_layer = Image.new(
            "RGBA",
            (WIDTH, HEIGHT),
            (0, 0, 0, 0)
        )

        tower_background = self.loaded_images.get(
            "background"
        )

        if tower_background:

            tower_background = tower_background.resize(
                (WIDTH, HEIGHT),
                Image.Resampling.LANCZOS
            )

            tower_layer.alpha_composite(
                tower_background
            )

        difficulty_name = (
            game.difficulty.upper()
        )

        self._render_text(
            tower_layer,
            "DRAGON TOWER",
            WIDTH // 2,
            35,
            font_size=24,
            color=(255, 215, 80)
        )

        self._render_text(
            tower_layer,
            difficulty_name,
            WIDTH // 2,
            65,
            font_size=14,
            color=(220, 220, 230)
        )

        dragon = self.loaded_images.get(
            f"dragon_{game.difficulty}"
        )

        if dragon:

            dragon_size = 90

            dragon = dragon.resize(
                (dragon_size, dragon_size),
                Image.Resampling.LANCZOS
            )

            tower_layer.paste(
                dragon,
                (
                    WIDTH - dragon_size - 20,
                    15
                ),
                dragon
            )

        TILE_WIDTH = 120
        TILE_HEIGHT = 70

        GAP_X = 8
        GAP_Y = 5

        max_tiles = 4

        total_width = (
            max_tiles * TILE_WIDTH
            + (max_tiles - 1) * GAP_X
        )

        start_x = (
            WIDTH - total_width
        ) // 2

        tower_top = 115

        for level_index in range(
            game.MAX_LEVELS - 1,
            -1,
            -1
        ):

            row_index = (
                game.MAX_LEVELS
                - 1
                - level_index
            )

            y = tower_top + row_index * (
                TILE_HEIGHT + GAP_Y
            )

            self._render_text(
                tower_layer,
                str(level_index + 1),
                30,
                y + TILE_HEIGHT // 2,
                font_size=12,
                color=(180, 180, 190)
            )

            is_current_level = (
                level_index == game.current_level
                and not game.game_over
            )

            for tile_index in range(
                game.tiles_per_level
            ):

                x = (
                    start_x
                    + tile_index * (
                        TILE_WIDTH + GAP_X
                    )
                    + (
                        (max_tiles - game.tiles_per_level)
                        * (TILE_WIDTH + GAP_X)
                        // 2
                    )
                )

                tile_type = "tile_hidden"

                if (
                    is_current_level
                    and level_index not in game.revealed
                ):

                    tile_type = "tile_current"

                if level_index in game.revealed:

                    if tile_index in game.revealed[level_index]:

                        if game.tower[level_index][tile_index]:

                            tile_type = "tile_egg"

                        else:

                            if (
                                game.losing_tiles.get(
                                    level_index
                                ) == tile_index
                            ):

                                tile_type = "tile_lose"

                            else:

                                tile_type = "tile_skull"

                if game.game_over:

                    if (
                        level_index
                        in game.losing_tiles
                    ):

                        losing_tile = (
                            game.losing_tiles[
                                level_index
                            ]
                        )

                        if tile_index == losing_tile:

                            tile_type = "tile_lose"

                        elif (
                            not game.tower[
                                level_index
                            ][tile_index]
                        ):

                            tile_type = "tile_skull"

                        else:

                            tile_type = "tile_egg"

                    else:

                        if game.tower[
                            level_index
                        ][tile_index]:

                            tile_type = "tile_egg"

                        else:

                            tile_type = "tile_skull"

                    crown_level = None
                    crown_tile_index = None

                    if game.won:

                        crown_level = (
                            DragonTowerGame.MAX_LEVELS - 1
                        )

                        if game.selected_tile is not None:

                            crown_tile_index = (
                                game.selected_tile - 1
                            )

                    elif game.cashout:

                        crown_level = (
                            game.current_level - 1
                        )

                        if game.selected_tile is not None:

                            crown_tile_index = (
                                game.selected_tile - 1
                            )

                    if (
                        crown_level is not None
                        and crown_tile_index is not None
                        and level_index == crown_level
                        and tile_index == crown_tile_index
                        and game.tower[level_index][tile_index]
                    ):

                        tile_type = "tile_win"

                self._draw_tile(
                    tower_layer,
                    x,
                    y,
                    tile_type,
                    TILE_WIDTH,
                    TILE_HEIGHT
                )

                if (
                    tile_type == "tile_current"
                    or tile_type == "tile_hidden"
                ):

                    self._render_text(
                        tower_layer,
                        str(tile_index + 1),
                        x + TILE_WIDTH // 2,
                        y + TILE_HEIGHT // 2,
                        font_size=18,
                        color=(255, 255, 255)
                    )

        bar_y = 805

        current_mult = (
            game.get_current_multiplier()
        )

        self._render_text(
            tower_layer,
            f"LEVEL {game.current_level}/9",
            WIDTH // 2,
            bar_y,
            font_size=14,
            color=(210, 210, 220)
        )

        self._render_text(
            tower_layer,
            f"x{current_mult:.2f}",
            WIDTH // 2,
            bar_y + 30,
            font_size=22,
            color=(255, 210, 60)
        )

        image.alpha_composite(
            tower_layer
        )

        image.save(
            output_path,
            format="WEBP",
            quality=90,
            optimize=True
        )

    def _charge_bet(
        self,
        user_id,
        user,
        bet
    ):

        balance = int(
            user.get("balance", 0)
        )

        if bet <= 0:
            return False

        if balance < bet:
            return False

        new_balance = balance - bet

        self.update_user_balance(
            user_id,
            new_balance
        )

        user["balance"] = new_balance

        return True

    def _finish_game(
        self,
        user_id,
        user,
        sender,
        game,
        payout,
        file_queue
    ):

        if payout > 0:

            new_balance = (
                int(user.get("balance", 0))
                + payout
            )

            self.update_user_balance(
                user_id,
                new_balance
            )

            user["balance"] = new_balance

        else:

            new_balance = int(
                user.get("balance", 0)
            )

        net_win = payout - game.bet

        try:

            new_level, new_progress = (
                self.cache.add_experience(
                    user_id,
                    net_win,
                    sender,
                    file_queue
                )
            )

            user["level"] = new_level
            user["level_progress"] = new_progress

        except Exception as exc:

            logger.error(
                f"[DragonTower] "
                f"Could not add experience: {exc}"
            )

        if net_win > 0:

            record_weekly_win(
                self.cache,
                user_id,
                "dragon_tower",
                net_win
            )

            record_monthly_win(
                self.cache,
                user_id,
                "dragon_tower",
                net_win
            )

        return new_balance, net_win

    def _send_help(
        self,
        sender,
        file_queue,
        cache,
        user_id
    ):

        self.send_message_image(
            sender,
            file_queue,
            "Dragon Tower Commands:\n\n"
            "Start new game:\n"
            "/dragon start <bet> [difficulty] [tiles]\n"
            "Example: /dragon start 100 easy\n"
            "Example: /dragon start 100 easy 1,2,3\n"
            "Example: /dragon start 100 1,3,2,4\n\n"
            "Shortcut:\n"
            "/dragon <bet> [difficulty] [tiles]\n"
            "Example: /dragon 100\n"
            "Example: /dragon 100 hard\n"
            "Example: /dragon 100 hard 1,2\n\n"
            "Difficulty is optional - default: easy\n\n"
            "Difficulty:\n"
            "easy - 3/4 safe\n"
            "medium - 2/3 safe\n"
            "hard - 1/2 safe\n"
            "expert - 1/3 safe\n"
            "master - 1/4 safe\n\n"
            "Choose tile:\n"
            "/dragon <tile>\n"
            "Multiple tiles:\n"
            "/dragon 2,3,1\n\n"
            "Cashout:\n"
            "/dragon cashout",
            "Dragon Tower",
            cache,
            user_id
        )

    def _parse_tiles(self, command):

        parts = command.split(",")

        tiles = []

        for part in parts:

            part = part.strip()

            if not part:
                continue

            try:

                tile = int(part)

            except ValueError:

                return None

            tiles.append(tile)

        if not tiles:
            return None

        return tiles

    def _process_reveal(
        self,
        user_id,
        user,
        sender,
        game,
        tiles,
        file_queue
    ):
        """
        Przetwarza listę kafelków dla aktywnej gry.
        Zwraca True jeśli gra się zakończyła (skull/auto_win),
        False jeśli gra nadal trwa.
        """

        for tile in tiles:

            if game.game_over:
                break

            if (
                tile < 1
                or tile > game.tiles_per_level
            ):

                self.send_message_image(
                    sender,
                    file_queue,
                    f"Tile {tile} invalid. "
                    f"Choose 1-{game.tiles_per_level}.",
                    "Dragon Tower - Error",
                    self.cache,
                    user_id
                )

                return True

            result = game.reveal(
                tile
            )

            if result == "already_revealed":

                continue

            if result == "skull":

                self.active_games.pop(
                    user_id,
                    None
                )

                self._save_active_games_to_cache()

                new_balance, net_win = (
                    self._finish_game(
                        user_id,
                        user,
                        sender,
                        game,
                        0,
                        file_queue
                    )
                )

                img_path = os.path.join(
                    self.results_folder,
                    f"dragon_tower_{user_id}_lost.webp"
                )

                self.get_game_state_image(
                    game,
                    img_path,
                    "LOSE",
                    user_id=user_id
                )

                overlay_path, overlay_error = (
                    self.apply_user_overlay(
                        img_path,
                        user_id,
                        sender,
                        game.bet,
                        net_win,
                        new_balance,
                        user,
                        show_win_text=True,
                        font_scale=self.font_scale,
                        avatar_size=self.avatar_size,
                        win_text_height=200
                    )
                )

                if overlay_path:

                    file_queue.put(
                        overlay_path
                    )

                logger.info(
                    f"[DragonTower] Loss: "
                    f"user={sender}, "
                    f"bet={game.bet}, "
                    f"level={game.current_level}"
                )

                return True

            if result == "auto_win":

                payout = game.get_payout()

                self.active_games.pop(
                    user_id,
                    None
                )

                self._save_active_games_to_cache()

                new_balance, net_win = (
                    self._finish_game(
                        user_id,
                        user,
                        sender,
                        game,
                        payout,
                        file_queue
                    )
                )

                img_path = os.path.join(
                    self.results_folder,
                    f"dragon_tower_{user_id}_win.webp"
                )

                self.get_game_state_image(
                    game,
                    img_path,
                    "WIN",
                    user_id=user_id
                )

                overlay_path, overlay_error = (
                    self.apply_user_overlay(
                        img_path,
                        user_id,
                        sender,
                        game.bet,
                        net_win,
                        new_balance,
                        user,
                        show_win_text=True,
                        font_scale=self.font_scale,
                        avatar_size=self.avatar_size,
                        win_text_height=200
                    )
                )

                if overlay_path:

                    file_queue.put(
                        overlay_path
                    )

                return True

            if result == "egg":

                logger.debug(
                    f"[DragonTower] Safe tile: "
                    f"user={sender}, "
                    f"level={game.current_level}, "
                    f"tile={tile}, "
                    f"multiplier=x"
                    f"{game.get_current_multiplier():.2f}"
                )

                self._save_active_games_to_cache()

        return False

    def execute_game(
        self,
        command_name,
        args,
        file_queue,
        cache=None,
        sender=None,
        avatar_url=None
    ):

        self.cache = cache

        self._load_active_games_from_cache()

        user_id, user, error = self.validate_user(
            cache,
            sender,
            avatar_url
        )

        user_id = str(user_id)

        if error == "Invalid user":

            self.send_message_image(
                sender,
                file_queue,
                "Invalid user!",
                "Dragon Tower - Error",
                cache,
                user_id
            )

            return ""

        if error:

            self.send_message_image(
                sender,
                file_queue,
                error,
                "Dragon Tower - Error",
                cache,
                user_id
            )

            return ""

        if not args:

            self._send_help(
                sender,
                file_queue,
                cache,
                user_id
            )

            return ""

        cmd = args[0].lower()

        if user_id not in self.active_games:

            try:

                shortcut_bet = int(
                    args[0]
                )

                if shortcut_bet > 0:

                    shortcut_difficulty = "easy"
                    shortcut_tiles = None

                    if len(args) >= 2:

                        second = args[1].lower()

                        if second in DragonTowerGame.DIFFICULTIES or second in {
                            "e", "m", "h", "x", "ma"
                        }:

                            shortcut_difficulty = second

                            if len(args) >= 3:

                                shortcut_tiles = args[2]

                        else:

                            shortcut_tiles = args[1]

                    new_args = [
                        "start",
                        str(shortcut_bet),
                        shortcut_difficulty
                    ]

                    if shortcut_tiles is not None:

                        new_args.append(shortcut_tiles)

                    args = new_args
                    cmd = "start"

            except (
                ValueError,
                TypeError
            ):

                pass

        if cmd in {
            "help",
            "?"
        }:

            self._send_help(
                sender,
                file_queue,
                cache,
                user_id
            )

            return ""

        if cmd in {
            "start",
            "bet",
            "b",
            "s"
        }:

            if len(args) < 2:

                self.send_message_image(
                    sender,
                    file_queue,
                    "Usage:\n"
                    "/dragon start <bet> [difficulty] [tiles]\n\n"
                    "Shortcut:\n"
                    "/dragon <bet> [difficulty] [tiles]\n\n"
                    "Examples:\n"
                    "/dragon start 100 easy\n"
                    "/dragon start 100 easy 1,2,3\n"
                    "/dragon start 100 1,3,2,4\n"
                    "/dragon 100\n"
                    "/dragon 100 hard 1,2",
                    "Dragon Tower - Start",
                    cache,
                    user_id
                )

                return ""

            try:

                bet = int(
                    args[1]
                )

            except ValueError:

                self.send_message_image(
                    sender,
                    file_queue,
                    "Invalid bet amount.",
                    "Dragon Tower - Error",
                    cache,
                    user_id
                )

                return ""

            aliases = {
                "e": "easy",
                "m": "medium",
                "h": "hard",
                "x": "expert",
                "ma": "master"
            }

            difficulty = "easy"
            tiles_arg = None

            if len(args) >= 3:

                second = args[2].lower()

                if second in DragonTowerGame.DIFFICULTIES or second in aliases:

                    difficulty = aliases.get(
                        second,
                        second
                    )

                    if len(args) >= 4:

                        tiles_arg = args[3]

                else:

                    tiles_arg = args[2]

            if difficulty not in (
                DragonTowerGame.DIFFICULTIES
            ):

                self.send_message_image(
                    sender,
                    file_queue,
                    "Invalid difficulty.\n\n"
                    "Available:\n"
                    "easy, medium, hard, expert, master",
                    "Dragon Tower - Error",
                    cache,
                    user_id
                )

                return ""

            if bet <= 0:

                self.send_message_image(
                    sender,
                    file_queue,
                    "Bet must be greater than zero.",
                    "Dragon Tower - Error",
                    cache,
                    user_id
                )

                return ""

            if user_id in self.active_games:

                self.send_message_image(
                    sender,
                    file_queue,
                    "You already have an active Dragon Tower game!\n\n"
                    "Use /dragon cashout.",
                    "Dragon Tower - Active Game",
                    cache,
                    user_id
                )

                return ""

            balance = int(
                user.get("balance", 0)
            )

            if balance < bet:

                self.send_message_image(
                    sender,
                    file_queue,
                    f"Insufficient funds!\n\n"
                    f"Bet: ${bet}\n"
                    f"Balance: ${balance}",
                    "Dragon Tower - Error",
                    cache,
                    user_id
                )

                return ""

            if not self._charge_bet(
                user_id,
                user,
                bet
            ):

                return ""

            game = DragonTowerGame(
                bet,
                difficulty
            )

            self.active_games[user_id] = game

            self._save_active_games_to_cache()

            if tiles_arg:

                tiles = self._parse_tiles(
                    tiles_arg
                )

                if tiles is None:

                    self.send_message_image(
                        sender,
                        file_queue,
                        "Invalid tile format.\n\n"
                        "Examples:\n"
                        "/dragon start 100 1,2,3\n"
                        "/dragon start 100 easy 1,2,3",
                        "Dragon Tower - Error",
                        cache,
                        user_id
                    )

                    return ""

                game_finished = self._process_reveal(
                    user_id,
                    user,
                    sender,
                    game,
                    tiles,
                    file_queue
                )

                if game_finished:

                    return ""

                img_path = os.path.join(
                    self.results_folder,
                    f"dragon_tower_{user_id}_move.webp"
                )

                self.get_game_state_image(
                    game,
                    img_path,
                    user_id=user_id
                )

                current_payout = (
                    game.get_payout()
                )

                current_profit = (
                    current_payout - game.bet
                )

                overlay_path, overlay_error = (
                    self.apply_user_overlay(
                        img_path,
                        user_id,
                        sender,
                        game.bet,
                        current_profit,
                        user["balance"],
                        user,
                        show_win_text=False,
                        font_scale=self.font_scale,
                        avatar_size=self.avatar_size,
                        win_text_height=200
                    )
                )

                if overlay_path:

                    file_queue.put(
                        overlay_path
                    )

                return ""

            img_path = os.path.join(
                self.results_folder,
                f"dragon_tower_{user_id}.webp"
            )

            self.get_game_state_image(
                game,
                img_path,
                user_id=user_id
            )

            overlay_path, overlay_error = (
                self.apply_user_overlay(
                    img_path,
                    user_id,
                    sender,
                    bet,
                    0,
                    user["balance"],
                    user,
                    show_win_text=False,
                    font_scale=self.font_scale,
                    avatar_size=self.avatar_size,
                    win_text_height=200
                )
            )

            if overlay_path:

                file_queue.put(
                    overlay_path
                )

            return ""

        if cmd in {
            "cashout",
            "c",
            "stand"
        }:

            game = self.active_games.get(
                user_id
            )

            if not game:

                self.send_message_image(
                    sender,
                    file_queue,
                    "No active Dragon Tower game.",
                    "Dragon Tower - Error",
                    cache,
                    user_id
                )

                return ""

            if game.current_level <= 0:

                self.send_message_image(
                    sender,
                    file_queue,
                    "You must reveal at least one safe tile before cashing out.",
                    "Dragon Tower - Error",
                    cache,
                    user_id
                )

                return ""

            payout = game.get_payout()

            game.cashout = True
            game.game_over = True

            self.active_games.pop(
                user_id,
                None
            )

            self._save_active_games_to_cache()

            new_balance, net_win = (
                self._finish_game(
                    user_id,
                    user,
                    sender,
                    game,
                    payout,
                    file_queue
                )
            )

            img_path = os.path.join(
                self.results_folder,
                f"dragon_tower_{user_id}_cashout.webp"
            )

            self.get_game_state_image(
                game,
                img_path,
                "WIN",
                user_id=user_id
            )

            overlay_path, overlay_error = (
                self.apply_user_overlay(
                    img_path,
                    user_id,
                    sender,
                    game.bet,
                    net_win,
                    new_balance,
                    user,
                    show_win_text=True,
                    font_scale=self.font_scale,
                    avatar_size=self.avatar_size,
                    win_text_height=200
                )
            )

            if overlay_path:

                file_queue.put(
                    overlay_path
                )

            logger.info(
                f"[DragonTower] Cashout: "
                f"user={sender}, "
                f"bet={game.bet}, "
                f"level={game.current_level}, "
                f"multiplier=x"
                f"{game.get_current_multiplier():.2f}, "
                f"payout={payout}, "
                f"net={net_win}"
            )

            return ""

        game = self.active_games.get(
            user_id
        )

        if not game:

            self.send_message_image(
                sender,
                file_queue,
                "No active Dragon Tower game.\n\n"
                "Start with:\n"
                "/dragon start <bet> [difficulty] [tiles]\n\n"
                "Or:\n"
                "/dragon <bet> [difficulty] [tiles]",
                "Dragon Tower - Error",
                cache,
                user_id
            )

            return ""

        tiles = self._parse_tiles(
            cmd
        )

        if tiles is None:

            self.send_message_image(
                sender,
                file_queue,
                "Invalid tile format.\n\n"
                "Examples:\n"
                "/dragon 2\n"
                "/dragon 2,3,1",
                "Dragon Tower - Error",
                cache,
                user_id
            )

            return ""

        game_finished = self._process_reveal(
            user_id,
            user,
            sender,
            game,
            tiles,
            file_queue
        )

        if game_finished:

            return ""

        img_path = os.path.join(
            self.results_folder,
            f"dragon_tower_{user_id}_move.webp"
        )

        self.get_game_state_image(
            game,
            img_path,
            user_id=user_id
        )

        current_multiplier = (
            game.get_current_multiplier()
        )

        current_payout = (
            game.get_payout()
        )

        current_profit = (
            current_payout - game.bet
        )

        overlay_path, overlay_error = (
            self.apply_user_overlay(
                img_path,
                user_id,
                sender,
                game.bet,
                current_profit,
                user["balance"],
                user,
                show_win_text=False,
                font_scale=self.font_scale,
                avatar_size=self.avatar_size,
                win_text_height=200
            )
        )

        if overlay_path:

            file_queue.put(
                overlay_path
            )

        return ""


def register():

    logger.info(
        "[DragonTower] Registering Dragon Tower plugin"
    )

    plugin = DragonTowerPlugin()

    return {
        "name": "dragon_tower",
        "aliases": [
            "/dragon",
            "/dragontower",
            "/dt"
        ],
        "description": (
            "Dragon Tower - Climb the tower "
            "and avoid the skulls.\n\n"
            "**Commands:**\n"
            "- /dragon start <bet> [difficulty] [tiles]\n"
            "- /dragon <bet> [difficulty] [tiles]\n"
            "- /dragon <tile>\n"
            "- /dragon <tile>,<tile>,<tile>\n"
            "- /dragon cashout\n\n"
            "**Difficulty:** "
            "easy, medium, hard, expert, master\n"
            "**Default difficulty:** easy"
        ),
        "execute": plugin.execute_game
    }