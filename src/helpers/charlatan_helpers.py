import asyncio
import discord
from helpers.style import Colours


def make_embed(users: dict[discord.User, int], title: str) -> discord.Embed:
    """Constructs an embed showing the current players in the lobby

        Returns:
            discord.Embed: The constructed embed
        """
    desc = "Playing now:\n " + "\n".join(str(key.mention) + " : " + str(
        users[key]) for key in users.keys())
    embed = discord.Embed(title=title, description=desc,
                          colour=Colours.PRIMARY)
    return embed


async def start_timer(time: int) -> None:
    """ Waits until time is up

    Args:
        time (int): amount of time to wait in seconds
    """
    seconds = time
    while True:
        seconds -= 1
        if seconds == 0:
            break
        await asyncio.sleep(1)


RULES = """__Charlatan Rules__
Every player is given the same list of words with the same word marked, \
except the *Charlatan* who gets an unmarked list of words.

Each player takens it in turn to say a word related to the marked word \
(the *Charlatan* must try and guess a relevant word).

A small amount of discussion time is permitted to try and identify the *Charlatan*.

After discussion the players must vote on who they think is a *Charlatan*:
> - if they fail to eliminate the *Charlatan* they lose and the *Charlatan* scores 2pts.
> - if they eliminate the *Charlatan*, the *Charlatan* gets to guess the marked word. \
If the *Charlatan* is correct they get 1pt and the other players get zero
> - if they eliminate the *Charlatan* and the *Chalartan* incorrectly guesses the marked word,
the other players each get 1pt"""

DEFAULT_WORDLIST = """Indiana Jones\nDr Who\nSpiderman\nDarth Vader\nSherlock Holmes\nGandalf
Superman\nBatman\nJames Bond\nDracula\nHomer Simpson\nFrankenstein
Robin Hood\nSuper Mario\nTarzan\nDumbledore"""
