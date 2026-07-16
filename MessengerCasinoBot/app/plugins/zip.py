from datetime import datetime

from base_game_plugin import BaseGamePlugin
from plugins._linkedin_minigames import (
    DAILY_COMPLETION_REWARD,
    award_daily_completion,
    ensure_daily_state,
    get_daily_zip_puzzle,
    parse_tile_numbers,
    save_daily_state,
)


class ZipPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(game_name="zip")

    def _compose_message(self, puzzle, path, status_text):
        board = puzzle.format_board()
        current_path = " -> ".join(f"{tile:02d}" for tile in path) if path else "empty"
        return (
            f"{status_text}\n\n"
            f"Board:\n{board}\n\n"
            f"Clues: {puzzle.format_clues()}\n"
            f"Current path: {current_path}\n\n"
            "Rules: draw one path through every tile, moving up/down/left/right, "
            "and visit clues in order.\n"
            "Commands: /zip <full path>, /zip add <tiles>, /zip clear\n"
            f"Reward: {DAILY_COMPLETION_REWARD} coins once per day."
        )

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        user_id, user, error = self.validate_user(cache, sender, avatar_url)

        if error:
            self.send_message_image(sender, file_queue, "Invalid user!", "Zip", cache, user_id)
            return ""

        puzzle = get_daily_zip_puzzle()
        state = ensure_daily_state(
            cache,
            user_id,
            "zip",
            puzzle.puzzle_id,
            {"path": []},
        )
        path = [int(tile) for tile in state.get("path", [])]
        status_text = f"Zip daily puzzle {puzzle.puzzle_id}"
        command_errors = []

        if not args or args[0] in ("help", "rules"):
            if state.get("completed_date") == datetime.now().date().isoformat():
                status_text = "Zip solved today. Reward already claimed."
            elif path:
                status_text = f"Path length: {len(path)}/{puzzle.cell_count}."
        elif args[0] in ("clear", "reset"):
            path = []
            state["path"] = path
            save_daily_state(cache, user_id, "zip", state)
            status_text = "Zip path cleared."
        else:
            if args[0] == "add":
                tiles, command_errors = parse_tile_numbers(args[1:], puzzle.cell_count)
                path = path + tiles
            else:
                tiles, command_errors = parse_tile_numbers(args, puzzle.cell_count)
                path = tiles

            if command_errors:
                status_text = "Invalid path:\n" + "\n".join(command_errors)
            else:
                state["path"] = path
                save_daily_state(cache, user_id, "zip", state)

                if len(path) == puzzle.cell_count:
                    result = puzzle.validate_path(path)
                    if result.solved:
                        reward = award_daily_completion(cache, user_id, "zip", puzzle.puzzle_id)
                        if reward.awarded:
                            status_text = (
                                f"Zip solved! +{reward.reward} coins.\n"
                                f"New balance: {reward.balance}"
                            )
                        else:
                            status_text = "Zip solved. Reward already claimed today."
                    else:
                        status_text = "Not solved yet:\n" + "\n".join(result.errors)
                else:
                    status_text = f"Path length: {len(path)}/{puzzle.cell_count}."

        message = self._compose_message(puzzle, path, status_text)
        self.send_message_image(sender, file_queue, message, "Zip", cache, user_id)
        return ""


def register():
    plugin = ZipPlugin()
    return {
        "name": "zip",
        "aliases": ["/zp"],
        "description": (
            "Daily Zip puzzle. Submit a numbered path through every tile.\n"
            "Commands: /zip <full path>, /zip add <tiles>, /zip clear\n"
            f"Reward: {DAILY_COMPLETION_REWARD} coins once per day."
        ),
        "execute": plugin.execute_game,
    }
