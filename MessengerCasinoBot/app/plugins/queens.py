from datetime import datetime

from base_game_plugin import BaseGamePlugin
from plugins._linkedin_minigames import (
    DAILY_COMPLETION_REWARD,
    award_daily_completion,
    ensure_daily_state,
    get_daily_queens_puzzle,
    parse_tile_numbers,
    save_daily_state,
)


class QueensPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="queens")

    def _compose_message(self, puzzle, placements, status_text):
        board = puzzle.format_board(placements)
        return (
            f"{status_text}\n\n"
            f"Board:\n{board}\n\n"
            "Cells show tile number + region letter. Q means selected queen.\n"
            "Rules: place one queen in each row, column, and region. Queens cannot touch.\n"
            "Commands: /queens <tile>, /queens set <tiles>, /queens clear\n"
            f"Reward: {DAILY_COMPLETION_REWARD} coins once per day."
        )

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user(cache, sender, avatar_url)

        if error:
            self.send_message_image(sender, file_queue, "Invalid user!", "Queens", cache, user_id)
            return ""

        puzzle = get_daily_queens_puzzle()
        state = ensure_daily_state(
            cache,
            user_id,
            "queens",
            puzzle.puzzle_id,
            {"placements": []},
        )
        placements = [int(tile) for tile in state.get("placements", [])]
        status_text = f"Queens daily puzzle {puzzle.puzzle_id}"
        command_errors = []

        if not args or args[0] in ("help", "rules"):
            if state.get("completed_date") == datetime.now().date().isoformat():
                status_text = "Queens solved today. Reward already claimed."
            elif placements:
                status_text = f"Selected {len(placements)}/{puzzle.size} queens."
        elif args[0] in ("clear", "reset"):
            placements = []
            state["placements"] = placements
            save_daily_state(cache, user_id, "queens", state)
            status_text = "Queens board cleared."
        else:
            if args[0] == "set":
                tiles, command_errors = parse_tile_numbers(args[1:], puzzle.cell_count)
                placements = tiles
            else:
                tiles, command_errors = parse_tile_numbers(args, puzzle.cell_count)
                if len(tiles) == puzzle.size:
                    placements = tiles
                else:
                    selected = set(placements)
                    for tile in tiles:
                        if tile in selected:
                            selected.remove(tile)
                        else:
                            selected.add(tile)
                    placements = sorted(selected)

            if command_errors:
                status_text = "Invalid move:\n" + "\n".join(command_errors)
            else:
                state["placements"] = placements
                save_daily_state(cache, user_id, "queens", state)

                result = puzzle.validate_placements(placements)
                if result.solved:
                    reward = award_daily_completion(cache, user_id, "queens", puzzle.puzzle_id)
                    if reward.awarded:
                        status_text = (
                            f"Queens solved! +{reward.reward} coins.\n"
                            f"New balance: {reward.balance}"
                        )
                    else:
                        status_text = "Queens solved. Reward already claimed today."
                elif len(placements) >= puzzle.size:
                    status_text = "Not solved yet:\n" + "\n".join(result.errors)
                else:
                    status_text = f"Selected {len(placements)}/{puzzle.size} queens."

        message = self._compose_message(puzzle, placements, status_text)
        self.send_message_image(sender, file_queue, message, "Queens", cache, user_id)
        return ""


def register():
    plugin = QueensPlugin()
    return {
        "name": "queens",
        "aliases": ["/queen", "/qn"],
        "description": (
            "Daily Queens puzzle. Use numbered tiles to place queens.\n"
            "Commands: /queens <tile>, /queens set <tiles>, /queens clear\n"
            f"Reward: {DAILY_COMPLETION_REWARD} coins once per day."
        ),
        "execute": plugin.execute_game,
    }
