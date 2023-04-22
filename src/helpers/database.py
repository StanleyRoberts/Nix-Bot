import psycopg2
from psycopg2.errors import UniqueViolation
from psycopg2 import sql
import typing
import traceback

from helpers.env import DATABASE_URL
from helpers.logger import Logger

logger = Logger()


class KeyViolation(Exception):
    pass


def select_from_unsafe(table_name: str) -> typing.Optional[typing.Any]:
    """selects from table. ONLY FOR TESTING

    Args:
        table_name (str): table to select from

    Returns:
        typing.Optional[typing.Any]: returned values
    """
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    cur.execute('SELECT * FROM public.{}'.format(table_name))
    val = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    logger.debug(val)


def single_SQL(query: str, values: tuple[typing.Any, ...] = (None,)) -> typing.Optional[typing.Any]:
    """
    Opens a connection, submits a single SQL query to the database then cleans up

    Args:
        query (string): SQL query to execute
        values (tuple, optional): Values to provide to the SQL query (i.e. for %s). Defaults to None.

    Raises:
        KeyViolation: Raised when key constraint is violated

    Returns:
        (list): Values returned from sql query as a list of tuples.
    """
    try:
        con = psycopg2.connect(DATABASE_URL)
    except psycopg2.Error:
        logger.critical("Failed to connect to database")
    cur = con.cursor()
    err_mess = None
    try:
        cur.execute(query, values if values != (None,) else None)
    except UniqueViolation:
        logger.error("SQL Key contraint violated")
        raise KeyViolation("Key constraint violated")
    except psycopg2.Error as e:
        err_mess = f"SQL Error: {e.__class__.__name__}\n{traceback.format_exc()}"
        logger.error(err_mess)
    except psycopg2.Warning as e:
        err_mess = f"SQL Warning: {e.__class__.__name__}\n{traceback.format_exc()}"
        logger.warning(err_mess)

    if err_mess:
        raise RuntimeError(err_mess)
    val = None
    if cur.description:
        val = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return val


def populate() -> None:
    """
    Sets up test database, and adds testing server as an entry
    """
    logger.info("Populating test database")
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    cur.execute("CREATE TABLE Guilds(ID BIGINT, CountingChannelID BIGINT, BirthdayChannelID BIGINT, " +
                "FactChannelID BIGINT, CurrentCount INTEGER, LastCounterID BIGINT, HighScoreCounting INTEGER, " +
                "FailRoleID BIGINT, PRIMARY KEY(ID));")

    cur.execute("CREATE TABLE Birthdays(GuildID BIGINT, UserID BIGINT, Birthdate TEXT, " +
                "FOREIGN KEY(GuildID) REFERENCES Guilds(ID), PRIMARY KEY(GuildID, UserID));")

    cur.execute("INSERT INTO Guilds (ID, CountingChannelID, BirthdayChannelID, FactChannelID, " +
                "CurrentCount, LastCounterID, HighScoreCounting, FailRoleID) VALUES (821016940462080000, " +
                "NULL, NULL, NULL, 0, NULL, 0, NULL);")

    cur.execute("CREATE TABLE Subreddits(GuildID BIGINT, subreddit TEXT, " +
                "SubredditChannelID BIGINT, PRIMARY KEY(GuildID, subreddit));")
    # TODO GuildID should be a foreign key (needs to be adjusted in live db too)

    cur.execute("CREATE TABLE ReactMessages(GuildID BIGINT, MessageID BIGINT, RoleID BIGINT, Emoji TEXT, " +
                "FOREIGN KEY(GuildID) REFERENCES Guilds(ID), PRIMARY KEY(GuildID, MessageID, RoleID, Emoji));")

    cur.execute("CREATE TABLE RoleChannel(GuildID BIGINT, RoleID BIGINT, ChannelID BIGINT, " +
                "FOREIGN KEY(GuildID) REFERENCES Guilds(ID), PRIMARY KEY(GuildID, ChannelID, RoleID));")

    cur.execute("CREATE TABLE MessageChain(GuildID BIGINT, ChannelID BIGINT, Message VARCHAR(2000), " +
                "FOREIGN KEY(GuildID) REFERENCES Guilds(ID), PRIMARY KEY(GuildID, ChannelID));")

    cur.execute("CREATE TABLE ChainedUsers(GuildID BIGINT, UserID BIGINT," +
                "FOREIGN KEY(GuildID) REFERENCES Guilds(ID), PRIMARY KEY(GuildID, UserID));")

    con.commit()
    cur.close()
    con.close()
