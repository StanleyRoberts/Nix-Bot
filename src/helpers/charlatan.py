import asyncio
import json
from dataclasses import dataclass


async def start_timer(time: int) -> None:
    """ Waits until time is up

    Args:
        time (int): amount of time to wait in seconds
    """
    await asyncio.sleep(time)


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


@dataclass
class WordList:
    title: str
    wordlist: list[str]


# schema: list[dict{title: str, wordlist: list[str]}]
WORDLISTS: list[WordList] = []

with open("src/charlatan/wordlists.json", "r") as f:
    WORDLISTS = list(map(lambda x: WordList(x["title"], x["wordlist"]), json.loads(f.read())["wordlists"]))
