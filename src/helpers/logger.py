from enum import Enum
from datetime import datetime
import inspect
import typing
import discord


class Priority(Enum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


TLogger = typing.TypeVar("TLogger", bound="Logger")


class Logger(object):
    _instance = None

    def __new__(cls: typing.Type[TLogger]) -> TLogger:
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls.print_level = 0
            cls.debug_mode = True
            cls.command_bot: discord.Bot | None = None
        return cls._instance

    def set_priority(self, priority: str) -> None:
        self.print_level = 0
        self.info(f"Logging level set to {priority}")
        self.print_level = Priority[priority].value

    def set_bot(self, discord_bot: discord.Bot) -> None:
        self.command_bot = discord_bot

    def debug(self, message: typing.Any, guild_id: int = 0, member_id: int = 0, channel_id: int = 0) -> None:
        try:
            call_class = inspect.stack()[1][0].f_locals["self"].__class__.__name__
        except KeyError:
            call_class = "No class"
        self._print_log(message, Priority.DEBUG, guild_id, member_id, channel_id, call_class)

    def info(self, message: typing.Any, guild_id: int = 0, member_id: int = 0, channel_id: int = 0) -> None:
        try:
            call_class = inspect.stack()[1][0].f_locals["self"].__class__.__name__
        except KeyError:
            call_class = "No class"
        self._print_log(message, Priority.INFO, guild_id, member_id, channel_id, call_class)

    def warning(self, message: typing.Any, guild_id: int = 0, member_id: int = 0, channel_id: int = 0) -> None:
        try:
            call_class = inspect.stack()[1][0].f_locals["self"].__class__.__name__
        except KeyError:
            call_class = "No class"
        self._print_log(message, Priority.WARNING, guild_id, member_id, channel_id, call_class)

    def error(self, message: typing.Any, guild_id: int = 0, member_id: int = 0, channel_id: int = 0) -> None:
        try:
            call_class = inspect.stack()[1][0].f_locals["self"].__class__.__name__
        except KeyError:
            call_class = "No class"
        self._print_log(message, Priority.ERROR, guild_id, member_id, channel_id, call_class)

    def critical(self, message: typing.Any, guild_id: int = 0, member_id: int = 0, channel_id: int = 0) -> None:
        try:
            call_class = inspect.stack()[1][0].f_locals["self"].__class__.__name__
        except KeyError:
            call_class = "No class"
        self._print_log(message, Priority.CRITICAL, guild_id, member_id, channel_id, call_class)

    def _print_log(self,
                   message: str,
                   priority: Priority,
                   guild_id: int,
                   member_id: int,
                   channel_id: int,
                   call_class: str
                   ) -> None:
        if priority.value < self.print_level:
            return
        log = "[" + priority.name + "] {" + call_class + "}: " + str(message)
        if Logger.debug_mode:
            time = datetime.now().strftime("%H:%M:%S") + " "
            log = time + log
        if self.command_bot is None:
            print(log + " { bot is not running yet }")
            return
        if guild_id:
            guild = self.command_bot.get_guild(guild_id)
            if guild:
                log += " (server: " + guild.name + ")"
            else:
                self.warning("Logger failed to deduce attribute (server) for the following message:")
        if member_id:
            user = self.command_bot.get_user(member_id)
            if user:
                log += " (user: " + user.name + ")"
            else:
                self.warning("Logger failed to deduce attribute (user) for the following message:")
        if channel_id:
            channel = self.command_bot.get_channel(channel_id)
            if channel and not isinstance(channel, discord.abc.PrivateChannel):
                log += " (channel: " + channel.name + ")"
            else:
                self.warning("Logger failed to deduce attribute (channel) for the following message:")
        print(log)
