from enum import Enum
from datetime import datetime


class Priority(Enum):
    """Priority for logging message
    """
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class Logger(object):
    """Logger singleton for creating log messages

    Returns:
        Logger: returns reference to global singleton logger
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls.print_level = 0
            cls.debug_mode = True
            cls.command_bot = None
        return cls._instance

    def set_priority(self, priority: str):
        """Set logger to only display messages of te given priority and above

        Args:
            priority (str): chosen priority, acceptable values: 'debug', 'info', 'warning', 'error', 'critical'
        """
        self.print_level = 0
        self.info("Logging level set to {0}".format(priority))
        try:
            self.print_level = Priority[priority].value
        except KeyError:
            self.info("Invalid logging level, defaulting to all")

    def set_bot(self, discord_bot):
        """Set bot to resolve ID values for logging messages (e.g. guild, channel, member ID)

        Args:
            discord_bot (discord.Bot): bot object to use to resolve ID values
        """
        self.command_bot = discord_bot

    def debug(self, message: str, guild_id: int = None, member_id: int = None, channel_id: int = None):
        """Logs a DEBUG level message

        Args:
            message (str): Message to log
            guild_id (int, optional): guild ID to link to log. Defaults to None.
            member_id (int, optional): member ID to link to log. Defaults to None.
            channel_id (int, optional): channel ID to link to log. Defaults to None.
        """
        self._print_log(message, Priority.DEBUG, guild_id, member_id, channel_id)

    def info(self, message: str, guild_id: int = None, member_id: int = None, channel_id: int = None):
        """Logs a INFO level message

        Args:
            message (str): Message to log
            guild_id (int, optional): guild ID to link to log. Defaults to None.
            member_id (int, optional): member ID to link to log. Defaults to None.
            channel_id (int, optional): channel ID to link to log. Defaults to None.
        """
        self._print_log(message, Priority.INFO, guild_id, member_id, channel_id)

    def warning(self, message: str, guild_id: int = None, member_id: int = None, channel_id: int = None):
        """Logs a WARNING level message

        Args:
            message (str): Message to log
            guild_id (int, optional): guild ID to link to log. Defaults to None.
            member_id (int, optional): member ID to link to log. Defaults to None.
            channel_id (int, optional): channel ID to link to log. Defaults to None.
        """
        self._print_log(message, Priority.WARNING, guild_id, member_id, channel_id)

    def error(self, message: str, guild_id: int = None, member_id: int = None, channel_id: int = None):
        """Logs a ERROR level message

        Args:
            message (str): Message to log
            guild_id (int, optional): guild ID to link to log. Defaults to None.
            member_id (int, optional): member ID to link to log. Defaults to None.
            channel_id (int, optional): channel ID to link to log. Defaults to None.
        """
        self._print_log(message, Priority.ERROR, guild_id, member_id, channel_id)

    def critical(self, message: str, guild_id: int = None, member_id: int = None, channel_id: int = None):
        """Logs a CRITICAL level message

        Args:
            message (str): Message to log
            guild_id (int, optional): guild ID to link to log. Defaults to None.
            member_id (int, optional): member ID to link to log. Defaults to None.
            channel_id (int, optional): channel ID to link to log. Defaults to None.
        """
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
        log = "[" + priority.name + "]: " + str(message)
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
