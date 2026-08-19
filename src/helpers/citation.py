import asyncio


async def start_timer(time: int) -> None:
    """ Waits until time is up

    Args:
        time (int): amount of time to wait in seconds
    """
    await asyncio.sleep(time)

THINK_TIME = 15

VOTE_TIME = 60

CHOICE_VOTE_TIME = 15

CITATIONTITLE = "Missing Citation"

CITATIONRULES = """__Missing Citation Rules__
Every player is given the title of a wikipedia article, \
except one player who gets the link to it.

One player is the guesser of the round. They want to find out who knows the actual article. \

The guesser asks questions about the article.
The players that don't get the article have to make up the contents of the article.
The other player correctly describes it. \


After discussion the guesser has to guess who they think has the actual article:
> - if they guess incorrectly, the player they guessed gets a point.
> - if they guess correctly, both the guesser and the player telling the truth get one point."""
