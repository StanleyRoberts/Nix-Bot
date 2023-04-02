import psycopg2

from helpers.env import DATABASE_URL
from helpers.logger import Logger

logger = Logger()


class KeyViolation(Exception):
    pass


def single_SQL(query: str, values: tuple[str, ...] = None) -> list[tuple[any, ...]]:
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
    try:
        cur.execute(query, values)
    except psycopg2.errors.UniqueViolation:
        logger.error("SQL Key contraint violated")
        raise KeyViolation("Key constraint violated")
    except psycopg2.Error as e:
        logger.error(f"SQL Error: {e.__class__.__name__}")
    except psycopg2.Warning as e:
        logger.warning(f"SQL Warning: {e.__class__.__name__}")
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
    con.commit()
    cur.close()
    con.close()
