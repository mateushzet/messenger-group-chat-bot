# Chat Bot Project Guide

This file is for AI chat bots and coding assistants working on this repository.
Read it before changing code so you understand the runtime shape, local state, and
plugin conventions.

## Project Summary

`MessengerGroupChatBot` is a Python Messenger group chat bot. It watches a
Messenger thread for slash commands, creates or updates player records, runs
casino-style mini-game plugins, and sends generated images or animations back to
the chat.

The user-facing product is a virtual casino with balances, rewards, rankings,
shops, and many games such as slots, blackjack, roulette, keno, mines, plinko,
crash, dice, and snakes.

## Important Paths

- `README.md` - high-level project description and screenshots.
- `MessengerCasinoBot/app/main.py` - process entry point.
- `MessengerCasinoBot/app/message_handler.py` - Messenger scraping and command
  detection.
- `MessengerCasinoBot/app/command_worker.py` - plugin loading and command
  dispatch.
- `MessengerCasinoBot/app/file_worker.py` - Messenger file upload/send loop.
- `MessengerCasinoBot/app/app_cache.py` - in-memory state plus JSON autosave.
- `MessengerCasinoBot/app/user_manager.py` - user creation, avatar download, and
  identity matching.
- `MessengerCasinoBot/app/base_game_plugin.py` - base helpers for most game and
  utility plugins.
- `MessengerCasinoBot/app/plugins/` - command plugins.
- `MessengerCasinoBot/app/assets/` - generated and source assets for images,
  animations, avatars, backgrounds, and game resources.
- `MessengerCasinoBot/app/config/config.example.ini` - example local config.

## Runtime Flow

1. `main.py` creates `AppCache`, a command queue, and a file queue.
2. `command_worker` starts in a daemon thread and imports every `.py` file in
   `app/plugins` that exposes `register()`.
3. `file_worker` starts in a daemon thread and logs into Messenger separately to
   upload queued images/files.
4. `message_handler.start_monitoring_messages()` logs into Messenger, scrapes
   recent message rows, ignores the bot's own messages, and queues new slash
   commands from other senders.
5. `command_worker.execute_command()` lowercases the whole incoming command text
   and sender name, creates/validates the user, then calls the matched plugin.
6. Plugins usually generate an image or animation under an assets/temp-style
   path and put that file path onto `file_queue`.
7. `file_worker` attaches the file in Messenger and sends it.
8. `AppCache` autosaves live state to `cache_backup.json` and daily backups.

Do not run the live bot unless explicitly asked. Running it can log into
Messenger and send messages or files to the configured group thread.

## Plugin Contract

Plugins are discovered dynamically by filename. A plugin module should define a
`register()` function returning a dictionary like this:

```python
def register():
    plugin = MyPlugin()
    return {
        "name": "mycommand",
        "aliases": ["/mycommand", "/mc"],
        "description": "Short help text shown by /help",
        "execute": plugin.execute_game,
    }
```

Most plugins subclass `BaseGamePlugin` and implement:

```python
def execute_game(self, command_name, args, file_queue, cache=None,
                 sender=None, avatar_url=None):
    self.cache = cache
    ...
```

Notes for future assistants:

- Command keys include the leading slash, for example `/balance`.
- Aliases should also include the leading slash.
- `command_worker` lowercases `message`, `sender`, command names, and args before
  plugins see them.
- Use `validate_user()` or `validate_user_and_balance()` from
  `BaseGamePlugin` when a command needs a known user or a sufficient balance.
- For image responses, prefer the shared helpers in `BaseGamePlugin` and queue
  the output path with `file_queue.put(path)`.
- Keep plugin descriptions clear because `/help` reads them dynamically.

## State, Config, And Secrets

Local runtime files are intentionally not committed:

- `MessengerCasinoBot/app/config/config.ini`
- `MessengerCasinoBot/app/config/cookies.json`
- `cache_backup.json`
- `backups/*`
- logs, generated `.png`, `.webp`, `.jpg`, `.json`, and font files

`config.example.ini` shows the expected sections:

- `[credentials] pin`
- `[messenger] threadid`
- `[gemini] api_key`
- optional `[gemini] models` for `/ask`

Never replace real config, cookies, cache backups, or generated user assets
unless the user explicitly asks. Treat them as local secrets and live state.

## Dependencies And Setup Notes

There is no package metadata or requirements file in the current repository.
Dependencies are inferred from imports and include at least:

- `playwright`
- `Pillow`
- `requests`
- `google-generativeai` for the `/ask` plugin

Playwright browser binaries may also be required locally. Because no lockfile is
present, avoid adding dependency-management files unless the user asks for setup
work.

## Safe Verification

Prefer checks that do not contact Messenger:

```powershell
python -m py_compile MessengerCasinoBot\app\main.py
python -m py_compile MessengerCasinoBot\app\plugins\balance.py
```

For broader syntax checks after Python edits, compile the edited files or the
app directory. Do not start `main.py` as a casual verification step because it
opens browser automation against Messenger.

## Editing Guidance

- Keep changes scoped; this repo is plugin-heavy, so new command behavior should
  usually live in a plugin.
- Follow existing plain-module import style. Files in `app` import siblings like
  `from logger import logger`, not package-qualified imports.
- Be careful with threaded code and shared state. `AppCache` uses a lock for
  many mutations; use its methods instead of mutating nested state directly when
  possible.
- Generated assets can be expensive or ignored by `.gitignore`; check before
  assuming an image file is tracked.
- If you touch Messenger selectors, expect fragility. Selector changes should be
  conservative and backed by screenshots/logs if available.
- If you change a plugin's help text or command behavior, consider updating
  `MessengerCasinoBot/app/plugins/games_descriptions.txt` too.

