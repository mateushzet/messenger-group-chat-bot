import os
import time
from base_game_plugin import BaseGamePlugin
from logger import logger

class HelpPlugin(BaseGamePlugin):
    def __init__(self):
        super().__init__(
            game_name="help"
        )
    
    def get_plugins_from_global(self):
        try:
            from command_worker import PLUGINS
            return PLUGINS
        except ImportError:
            logger.error("[Help] Cannot import PLUGINS from command_worker")
            return {}
    
    def get_user_id_from_cache(self, cache, sender, avatar_url):
        try:
            from user_manager import UserManager
            user_manager = UserManager(cache)
            user_id, user = user_manager.find_user_by_name_avatar(sender, avatar_url)
            return user_id if user_id else sender
        except Exception as e:
            logger.error(f"[Help] Error getting user_id: {e}")
            return sender
    
    def execute_game(self, command_name, args, file_queue, cache=None, sender=None, avatar_url=None):
        self.cache = cache
        
        plugins = self.get_plugins_from_global()
        
        if not plugins:
            error_message = "No plugins loaded.\nTry again in a moment."
            user_id = self.get_user_id_from_cache(cache, sender, avatar_url)
            return self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message=error_message,
                title="Help System - Error",
                cache=cache,
                user_id=user_id
            )
        
        if len(args) == 0:
            unique_plugins = {}
            for command, plugin_info in plugins.items():
                if command.startswith('/'):
                    plugin_name = plugin_info['name']
                    if plugin_name not in unique_plugins:
                        unique_plugins[plugin_name] = plugin_info
            
            message_lines = []
            message_lines.append("Use: /help <command_name>")
            message_lines.append("")
            message_lines.append("Available commands:")
            
            for plugin_name in sorted(unique_plugins.keys()):
                message_lines.append(f"• {plugin_name}")
            
            message = "\n".join(message_lines)
            
            user_id = self.get_user_id_from_cache(cache, sender, avatar_url)
            
            return self.send_message_image(
                nickname=sender,
                file_queue=file_queue,
                message=message,
                title="Help System",
                cache=cache,
                user_id=user_id
            )
        
        else:
            plugin_key = args[0].lower()
            
            if not plugin_key.startswith('/'):
                plugin_key = f"/{plugin_key}"
            
            found_plugin = None
            found_key = None
            
            for command, plugin_info in plugins.items():
                if command.lower() == plugin_key:
                    found_plugin = plugin_info
                    found_key = command
                    break
            
            if not found_plugin:
                clean_plugin_key = plugin_key.lstrip('/')
                for command, plugin_info in plugins.items():
                    if command.startswith('/'):
                        if plugin_info['name'].lower() == clean_plugin_key:
                            found_plugin = plugin_info
                            found_key = command
                            break
            
            if found_plugin:
                plugin_name = found_plugin['name']
                description = found_plugin.get('description', 'No description available')
                
                message_lines = []
                message_lines.append(description)
                message_lines.append("")
                
                if 'aliases' in found_plugin and found_plugin['aliases']:
                    filtered_aliases = [alias for alias in found_plugin['aliases'] if alias != found_key]
                    if filtered_aliases:
                        message_lines.append("Aliases:")
                        for alias in filtered_aliases:
                            message_lines.append(f"  {alias}")
                        message_lines.append("")
                
                message = "\n".join(message_lines)
                
                user_id = self.get_user_id_from_cache(cache, sender, avatar_url)
                
                return self.send_message_image(
                    nickname=sender,
                    file_queue=file_queue,
                    message=message,
                    title=f"Help: {found_key}",
                    cache=cache,
                    user_id=user_id
                )
            else:
                error_message = f"Plugin '{plugin_key}' not found.\n\nUse /help to see available commands."
                user_id = self.get_user_id_from_cache(cache, sender, avatar_url)
                return self.send_message_image(
                    nickname=sender,
                    file_queue=file_queue,
                    message=error_message,
                    title="Help - Not Found",
                    cache=cache,
                    user_id=user_id
                )

def register():
    plugin = HelpPlugin()
    logger.info("[Help] Help plugin registered")
    return {
        "name": "help",
        "description": "Get help for commands: /help or /help <command_name>",
        "aliases": ["/commands"],
        "execute": plugin.execute_game
    }