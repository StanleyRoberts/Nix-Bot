from enum import Enum
from datetime import datetime


class Priority(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class Logger(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls.print_level = 2
            cls.debug_mode = True
            cls.command_bot = None
        return cls._instance

    def set_priority(self, priority: str):
        self.print_level = Priority[priority].value

    def set_bot(self, discord_bot):
        self.command_bot = discord_bot

    def debug(self, message: str, guild_id: int = None, member_id: int = None, channel_id: int = None):
        self._print_log(message, Priority.DEBUG, guild_id, member_id, channel_id)

    def info(self, message: str, guild_id: int = None, member_id: int = None, channel_id: int = None):
        self._print_log(message, Priority.INFO, guild_id, member_id, channel_id)

    def warning(self, message: str, guild_id: int = None, member_id: int = None, channel_id: int = None):
        self._print_log(message, Priority.WARNING, guild_id, member_id, channel_id)

    def error(self, message: str, guild_id: int = None, member_id: int = None, channel_id: int = None):
        self._print_log(message, Priority.ERROR, guild_id, member_id, channel_id)

    def critical(self, message: str, guild_id: int = None, member_id: int = None, channel_id: int = None):
        self._print_log(message, Priority.CRITICAL, guild_id, member_id, channel_id)

    def _print_log(self,
                   message: str,
                   priority: Priority,
                   guild_id: int,
                   member_id: int,
                   channel_id: int
                   ):
        if priority.value < self.print_level:
            return
        log = "[" + priority.name + "]: " + message
        if Logger.debug_mode:
            time = datetime.now().strftime("%H:%M:%S") + " "
            log = time + log
        if guild_id:
            try:
                log += " (server: " + self.command_bot.get_guild(guild_id).name + ")"
            except AttributeError:
                self.warning("Logger failed to deduce attribute (server) for the following message:")
        if member_id:
            try:
                log += " (user: " + self.command_bot.get_user(member_id).name + ")"
            except AttributeError:
                self.warning("Logger failed to deduce attribute (user) for the following message:")
        if channel_id:
            try:
                log += " (channel: " + self.command_bot.get_channel(channel_id).name + ")"
            except AttributeError:
                self.warning("Logger failed to deduce attribute (channel) for the following message:")
        print(log)
