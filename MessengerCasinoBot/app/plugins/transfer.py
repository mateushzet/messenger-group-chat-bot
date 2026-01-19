from base_game_plugin import BaseGamePlugin
from logger import logger

class TransferPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="transfer",
            results_folder=self.get_app_path("temp"),
        )

    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache

        if not cache or not sender or not avatar_url:
            logger.error(f"[Transfer] Internal error: insufficient data")
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Internal Error: Unsufficient data",
                title="TRANSFER ERROR",
                cache=cache,
                user_id=None
            )
            return None

        if len(args) < 2:
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Usage: /transfer <amount> <player_name>\n\nExample: /transfer 100 John",
                title="TRANSFER HELP",
                cache=cache,
                user_id=None
            )
            return None

        try:
            amount = int(args[0])
            if amount <= 0:
                raise ValueError
        except ValueError:
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message=(
                    "Invalid amount. Must be a positive number\n\n"
                    "Examples:\n"
                    "- /transfer 100 John\n"
                    "- /transfer 500 Jane Doe"
                ),
                title="TRANSFER ERROR",
                cache=cache,
                user_id=None
            )
            return None

        recipient_name_raw = " ".join(args[1:]).strip()
        recipient_input = recipient_name_raw[1:].strip() if recipient_name_raw.startswith("@") else recipient_name_raw

        if not recipient_input:
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Player name cannot be empty\n\nUsage: /transfer <amount> <player_name>",
                title="TRANSFER ERROR",
                cache=cache,
                user_id=None
            )
            return None

        sender_id, sender_data, error = self.validate_user(cache, sender, avatar_url)
        if error or not sender_data:
            logger.error(f"[Transfer] Sender not found: {sender}")
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Sender account not found",
                title="TRANSFER ERROR",
                cache=cache,
                user_id=None
            )
            return None

        sender_balance = sender_data.get("balance", 0)
        if sender_balance < amount:
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message=(
                    f"Insufficient funds\n\n"
                    f"Your balance: {sender_balance}\n"
                    f"Transfer amount: {amount}"
                ),
                title="TRANSFER ERROR",
                cache=cache,
                user_id=sender_id
            )
            return None

        recipients = []

        if recipient_input.isdigit():
            recipient_id = int(recipient_input)
            recipient_data = cache.users.get(recipient_id)

            if not recipient_data:
                self.send_message_image(
                    nickname=sender,
                    file_queue=file_queue,
                    message=f"Player with ID {recipient_id} not found",
                    title="TRANSFER ERROR",
                    cache=cache,
                    user_id=sender_id
                )
                return None

            recipients = [(recipient_id, recipient_data)]

        else:
            recipients = self._find_recipient_by_name_safe(recipient_input, cache)

            if not recipients:
                self.send_message_image(
                    nickname=sender,
                    file_queue=file_queue,
                    message=f"Player '{recipient_input}' not found",
                    title="TRANSFER ERROR",
                    cache=cache,
                    user_id=sender_id
                )
                return None

            if len(recipients) > 1:
                self.send_message_image(
                    nickname=sender,
                    file_queue=file_queue,
                    message=self._format_multiple_recipients_error(recipients, recipient_input),
                    title="TRANSFER - MULTIPLE USERS",
                    cache=cache,
                    user_id=sender_id
                )
                return None

        recipient_id, recipient_data = recipients[0]

        if sender_id == recipient_id:
            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message="Cannot transfer money to yourself",
                title="TRANSFER ERROR",
                cache=cache,
                user_id=sender_id
            )
            return None

        recipient_balance = recipient_data.get("balance", 0)

        try:
            if not cache.update_user(sender_id, balance=sender_balance - amount):
                raise RuntimeError("Failed to update sender balance")

            if not cache.update_user(recipient_id, balance=recipient_balance + amount):
                cache.update_user(sender_id, balance=sender_balance)
                raise RuntimeError("Failed to update recipient balance")

            recipient_display_name = recipient_data.get("name", recipient_input)

            logger.info(f"[Transfer] Transfer completed: sender_id - {sender_id} , recipient_id - {recipient_id}, amount - {amount}, sender new balance - {sender_balance - amount}, recipient new balance - {recipient_balance + amount}")

            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message=(
                    "SUCCESSFUL TRANSFER\n\n"
                    f"Amount: {amount}\n"
                    f"To: {recipient_display_name}\n"
                    f"Your new balance: {sender_balance - amount}\n"
                    f"Recipient's new balance: {recipient_balance + amount}"
                ),
                title="TRANSFER COMPLETED",
                cache=cache,
                user_id=sender_id
            )

        except Exception as e:
            logger.error("[Transfer] Transfer failed", exc_info=True)
            try:
                cache.update_user(sender_id, balance=sender_balance)
                cache.update_user(recipient_id, balance=recipient_balance)
            except Exception:
                pass

            self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message=f"Transfer failed: {str(e)}\n\nPlease try again later",
                title="TRANSFER ERROR",
                cache=cache,
                user_id=sender_id
            )

        return None    

    def _find_recipient_by_name_safe(self, name, cache):
        if not hasattr(cache, 'users') or not cache.users:
            logger.error("[Transfer] Cache has no users or users is empty")
            return []
        
        search_name = name
        if search_name.startswith('@'):
            search_name = search_name[1:].strip()
            
        exact_matches = []
        partial_matches = []
        name_lower = search_name.lower().strip()
        
        for user_id, user_data in cache.users.items():
            if not isinstance(user_data, dict):
                continue
                
            user_name = user_data.get('name', '')
            if not user_name:
                continue
                
            user_name_lower = user_name.lower()
            
            if user_name_lower == name_lower:
                exact_matches.append((user_id, user_data))
            elif user_name_lower.startswith(name_lower):
                partial_matches.append((user_id, user_data))
        
        return exact_matches + partial_matches
    
    def _format_multiple_recipients_error(self, recipients, searched_name):
        if not recipients:
            return ""

        error_msg = "MULTIPLE USERS FOUND\n\n"
        error_msg += f"More than one user matches '{searched_name}'.\n"
        error_msg += "Please use the USER ID instead of the name.\n\n"

        for i, (user_id, user_data) in enumerate(recipients[:5], 1):
            user_name = user_data.get("name", "Unknown")
            balance = user_data.get("balance", 0)

            error_msg += (
                f"{i}. Name: {user_name}\n"
                f"   User ID: {user_id}\n"
                f"   Balance: {balance}\n\n"
            )

        if len(recipients) > 5:
            error_msg += f"... and {len(recipients) - 5} more users.\n\n"

        error_msg += (
            "Example:\n"
            "/transfer <amount> <user_id>"
        )

        return error_msg

def register():
    plugin = TransferPlugin()
    return {
        "name": "transfer",
        "aliases": ["/t"],
        "description": (
            "TRANSFER MONEY BETWEEN PLAYERS\n\n"
            "Usage: /transfer <amount> <player_name>\n\n"
            "Examples:\n"
            "- /transfer 100 John\n"
            "- /transfer 500 Jane Doe\n"
            "- /transfer 100 @John  (ignores @ symbol)\n\n"
        ),
        "execute": plugin.execute_game
    }