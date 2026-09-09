import asyncio
from enum import Enum
from helpers.style import Colours
import discord


async def start_timer(time: int) -> None:
    """ Waits until time is up

    Args:
        time (int): amount of time to wait in seconds
    """
    await asyncio.sleep(time)


async def edit_embed(
        message: discord.Message | discord.InteractionMessage,
        view: discord.ui.View,
        description: str) -> None:
    await message.edit(
        view=view,
        embed=discord.Embed(
            description=description,
            title=CITATIONTITLE,
            colour=Colours.PRIMARY
        )
    )


class Phases(Enum):
    TALKING = 1
    VOTING = 2
    ENDING = 3
    FINISHED = 4


CHOICE_AMOUNT = 10

THINK_TIME = 20

VOTE_TIME = 60

CHOICE_VOTE_TIME = 15

VOTE_RESULT_TIME = 10

CITATIONTITLE = "Missing Citation"

CITATIONRULES = """__Missing Citation Rules__
Every player is given the title of a wikipedia article, \
except one player, the "editor" who gets the link to it.

You then have 20 seconds to make up what the article could be about or read the content of it.
After that time the editor closes the article and the next phase begins.
Every player attempts to convince the others of their version of the article's content.

After this phase players start voting on who they think told the truth.
The person telling the truth can vote but their vote will not be counted.
Every player wants to receive as many votes for them as they can while also voting for the editor.
"""
