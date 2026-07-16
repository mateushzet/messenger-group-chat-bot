from datetime import datetime

from base_game_plugin import BaseGamePlugin
from plugins._linkedin_minigames import (
    DAILY_COMPLETION_REWARD,
    award_daily_completion,
    ensure_daily_state,
    get_daily_tango_puzzle,
    normalize_tango_assignments,
    parse_tango_symbol,
    save_daily_state,
)


class TangoPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="tango")

    def _compose_message(self, puzzle, assignments, status_text):
        board = puzzle.format_board(assignments)
        links = puzzle.format_links()
        return (
            f"{status_text}\n\n"
            f"Board:\n{board}\n\n"
            f"{links}\n\n"
            "S = sun, M = moon, * = fixed cell.\n"
            "Rules: each row and column has equal suns and moons, never three in a row.\n"
            "Commands: /tango <tile> <sun|moon>, /tango clear <tile>\n"
            f"Reward: {DAILY_COMPLETION_REWARD} coins once per day."
        )

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user(cache, sender, avatar_url)

        if error:
            self.send_message_image(sender, file_queue, "Invalid user!", "Tango", cache, user_id)
            return ""

        puzzle = get_daily_tango_puzzle()
        state = ensure_daily_state(
            cache,
            user_id,
            "tango",
            puzzle.puzzle_id,
            {"assignments": {}},
        )
        user_assignments = normalize_tango_assignments(state.get("assignments", {}))
        status_text = f"Tango daily puzzle {puzzle.puzzle_id}"
        command_errors = []

        if not args or args[0] in ("help", "rules"):
            if state.get("completed_date") == datetime.now().date().isoformat():
                status_text = "Tango solved today. Reward already claimed."
        elif args[0] in ("clear", "reset"):
            if len(args) == 1 or args[0] == "reset":
                user_assignments = {}
                status_text = "Tango board cleared."
            else:
                for raw_tile in args[1:]:
                    try:
                        tile = int(raw_tile)
                    except ValueError:
                        command_errors.append(f"'{raw_tile}' is not a tile number.")
                        continue
                    user_assignments.pop(tile, None)
                if not command_errors:
                    status_text = "Tango cell cleared."

            state["assignments"] = {str(tile): value for tile, value in user_assignments.items()}
            save_daily_state(cache, user_id, "tango", state)
        else:
            if len(args) % 2 != 0:
                command_errors.append("Use pairs: /tango <tile> <sun|moon>.")
            else:
                for index in range(0, len(args), 2):
                    raw_tile = args[index]
                    raw_symbol = args[index + 1]
                    try:
                        tile = int(raw_tile)
                    except ValueError:
                        command_errors.append(f"'{raw_tile}' is not a tile number.")
                        continue

                    symbol = parse_tango_symbol(raw_symbol)
                    if not symbol:
                        command_errors.append(f"'{raw_symbol}' must be sun or moon.")
                        continue
                    if tile < 1 or tile > puzzle.cell_count:
                        command_errors.append(f"Tile {tile} must be between 1 and {puzzle.cell_count}.")
                        continue
                    if tile in puzzle.givens:
                        command_errors.append(f"Tile {tile} is fixed and cannot be changed.")
                        continue

                    user_assignments[tile] = symbol

            if command_errors:
                status_text = "Invalid move:\n" + "\n".join(command_errors)
            else:
                state["assignments"] = {str(tile): value for tile, value in user_assignments.items()}
                save_daily_state(cache, user_id, "tango", state)

        assignments = {**puzzle.givens, **user_assignments}

        if not command_errors and args and args[0] not in ("help", "rules", "clear", "reset"):
            if len(assignments) == puzzle.cell_count:
                result = puzzle.validate_assignments(assignments)
                if result.solved:
                    reward = award_daily_completion(cache, user_id, "tango", puzzle.puzzle_id)
                    if reward.awarded:
                        status_text = (
                            f"Tango solved! +{reward.reward} coins.\n"
                            f"New balance: {reward.balance}"
                        )
                    else:
                        status_text = "Tango solved. Reward already claimed today."
                else:
                    status_text = "Not solved yet:\n" + "\n".join(result.errors)
            else:
                status_text = f"Filled {len(assignments)}/{puzzle.cell_count} cells."

        message = self._compose_message(puzzle, assignments, status_text)
        self.send_message_image(sender, file_queue, message, "Tango", cache, user_id)
        return ""


def register():
    plugin = TangoPlugin()
    return {
        "name": "tango",
        "aliases": ["/tg"],
        "description": (
            "Daily Tango puzzle. Fill numbered cells with sun or moon.\n"
            "Commands: /tango <tile> <sun|moon>, /tango clear <tile>\n"
            f"Reward: {DAILY_COMPLETION_REWARD} coins once per day."
        ),
        "execute": plugin.execute_game,
    }
