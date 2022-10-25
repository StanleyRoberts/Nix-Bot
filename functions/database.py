import psycopg2

from Nix import DATABASE_URL


class KeyViolation(Exception):
    pass


def single_SQL(query, values=None):
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
    con = psycopg2.connect(DATABASE_URL)
    cur = con.cursor()
    try:
        cur.execute(query, values)
    except psycopg2.errors.UniqueViolation:  # something is in the SQL twice
        raise KeyViolation("Key constraint violated")
    val = None
    if cur.description:
        val = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return val


def populate():
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
