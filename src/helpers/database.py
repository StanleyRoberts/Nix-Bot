import psycopg2
from psycopg2.errors import UniqueViolation
import typing
import traceback

from helpers.env import DATABASE_URL
from helpers.logger import Logger

logger = Logger()


class KeyViolation(Exception):
    pass


def select_from_unsafe(table_name: str) -> typing.List[typing.Tuple[typing.Any, ...]]:
    """logs select from table. ONLY FOR TESTING

    Args:
        table_name (str): table to select from

    Returns:
        typing.Optional[typing.Any]: returned values
    """
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    cur.execute(f'SELECT * FROM public.{table_name}')
    val = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return val


def single_sql(
    query: str,
    values: tuple[typing.Any, ...] = (None,)
) -> list[tuple[typing.Any, ...]]:
    """
    Opens a connection, submits a single SQL query to the database then cleans up

    Args:
        query (string): SQL query to execute.
        values (tuple, optional):
            Values to provide to the SQL query (i.e. for %s). Defaults to None.

    Raises:
        KeyViolation: Raised when key constraint is violated

    Returns:
        (list): Values returned from sql query as a list of tuples.
    """
    try:
        con = psycopg2.connect(DATABASE_URL)
    except psycopg2.Error as err:
        logger.critical(f"Failed to connect to database: {err}")
    cur = con.cursor()
    err_mess = None
    try:
        cur.execute(query, values if values != (None,) else None)
    except UniqueViolation as e:
        raise KeyViolation("Key constraint violated") from e
    except psycopg2.Error as e:
        err_mess = f"SQL Error: {e.__class__.__name__}\n{traceback.format_exc()}"
        logger.error(err_mess)
    except psycopg2.Warning as e:
        err_mess = f"SQL Warning: {e.__class__.__name__}\n{traceback.format_exc()}"
        logger.warning(err_mess)

    if cur.description:
        val = cur.fetchall()

    else:
        err_mess = "Expected return values"
    con.commit()
    cur.close()
    con.close()
    if err_mess:
        raise RuntimeError(err_mess)
    return val


def single_void_SQL(query: str, values: tuple[typing.Any, ...] = (None,)) -> None:
    """
    Opens a connection, submits a single SQL query to the database then cleans up

    Args:
        query (string): SQL query to execute.
        values (tuple, optional):
            Values to provide to the SQL query (i.e. for %s). Defaults to None.

    Raises:
        KeyViolation: Raised when key constraint is violated
    """
    try:
        con = psycopg2.connect(DATABASE_URL)
    except psycopg2.Error as err:
        logger.critical(f"Failed to connect to database: {err}")
    cur = con.cursor()
    err_mess = None
    try:
        cur.execute(query, values if values != (None,) else None)
    except UniqueViolation as e:
        raise KeyViolation("Key constraint violated") from e
    except psycopg2.Error as e:
        err_mess = f"SQL Error: {e.__class__.__name__}\n{traceback.format_exc()}"
        logger.error(err_mess)
    except psycopg2.Warning as e:
        err_mess = f"SQL Warning: {e.__class__.__name__}\n{traceback.format_exc()}"
        logger.warning(err_mess)

    con.commit()
    cur.close()
    con.close()
    if err_mess:
        raise RuntimeError(err_mess)


def multi_void_sql(commands: list[tuple[str, tuple[typing.Any, ...]]]) -> None:
    """Executes multiple commands for the database that don't have a return

    Args:
        commands (list[tuple[str, tuple[typing.Any, ...]]]):
            List of tuples where each tuple contains a string and a tuple.
            The string of each tuple is the query and the inner tuple contains
            the substituted values for the query.

    Raises:
        KeyViolation: _description_
        RuntimeError: _description_
    """
    try:
        con = psycopg2.connect(DATABASE_URL)
    except psycopg2.Error as err:
        logger.critical(f"Failed to connect to database: {err}")
    cur = con.cursor()
    err_mess = None
    for (query, values) in commands:
        try:
            cur.execute(query, values)
        except UniqueViolation as e:
            raise KeyViolation("Key constraint violated") from e
        except psycopg2.Error as e:
            err_mess = f"SQL Error: {e.__class__.__name__}\n{traceback.format_exc()}"
            logger.error(err_mess)
        except psycopg2.Warning as e:
            err_mess = f"SQL Warning: {e.__class__.__name__}\n{traceback.format_exc()}"
            logger.warning(err_mess)

        if err_mess:
            raise RuntimeError(err_mess)
    con.commit()
    cur.close()
    con.close()


def populate() -> None:
    """
    Sets up test database, and adds testing server as an entry
    """
    logger.info("Populating test database")
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE Guilds(ID BIGINT, CountingChannelID BIGINT, BirthdayChannelID BIGINT, " +
        "FactChannelID BIGINT, CurrentCount INTEGER, LastCounterID BIGINT, " +
        "HighScoreCounting INTEGER, FailRoleID BIGINT, NicknameChangeAllowed BOOLEAN DEFAULT False, PRIMARY KEY(ID));"
    )

    cur.execute("CREATE TABLE Birthdays(GuildID BIGINT, UserID BIGINT, Birthdate TEXT, " +
                "FOREIGN KEY(GuildID) REFERENCES Guilds(ID), PRIMARY KEY(GuildID, UserID));")

    cur.execute("CREATE TABLE Subreddits(GuildID BIGINT, subreddit TEXT, " +
                "SubredditChannelID BIGINT, PRIMARY KEY(GuildID, subreddit));")

    cur.execute(
        "CREATE TABLE ReactMessages(GuildID BIGINT, MessageID BIGINT, RoleID BIGINT, Emoji TEXT, " +
        "FOREIGN KEY(GuildID) REFERENCES Guilds(ID), " +
        "PRIMARY KEY(GuildID, MessageID, RoleID, Emoji));"
    )

    cur.execute(
        "CREATE TABLE RoleChannel(GuildID BIGINT, RoleID BIGINT, ChannelID BIGINT, " +
        "ToAdd BOOLEAN, FOREIGN KEY(GuildID) REFERENCES Guilds(ID), " +
        "PRIMARY KEY(GuildID, ChannelID, RoleID));"
    )

    cur.execute(
        "CREATE TABLE MessageChain(GuildID BIGINT, WatchedChannelID BIGINT, " +
        "ResponseChannelID BIGINT, Message VARCHAR(2000), FOREIGN KEY(GuildID) " +
        "REFERENCES Guilds(ID), PRIMARY KEY(GuildID, WatchedChannelID));"
    )

    cur.execute(
        "CREATE TABLE ChainedUsers(GuildID BIGINT, UserID BIGINT, ChannelID BIGINT, " +
        "FOREIGN KEY(GuildID, ChannelID) REFERENCES MessageChain(GuildID, WatchedChannelID), " +
        "PRIMARY KEY(GuildID, UserID, ChannelID));")

    cur.execute(
        "INSERT INTO Guilds (ID, CountingChannelID, BirthdayChannelID, FactChannelID, " +
        "CurrentCount, LastCounterID, HighScoreCounting, FailRoleID) VALUES (821016940462080000, " +
        "NULL, NULL, NULL, 0, NULL, 0, NULL);")

    cur.execute(
        "INSERT INTO Guilds (ID, CountingChannelID, BirthdayChannelID, FactChannelID, " +
        "CurrentCount, LastCounterID, HighScoreCounting, FailRoleID) VALUES " +
        "(1026169937422729226, NULL, NULL, NULL, 0, NULL, 0, NULL);"
    )

    con.commit()
    cur.close()
    con.close()
