import discord
import random

from helpers.style import Emotes, Colours
from helpers.logger import Logger
import helpers.charlatan_helpers as helper
from charlatan.ui_kit import CharlatanChoice

logger = Logger()

CHARLATAN_VOTE_TIME = 20
PLAYER_VOTE_TIME = 20


class CharlatanGame:
    def __init__(self, players: dict[discord.User, int],
                 wordlist: list[str] = helper.DEFAULT_WORDLIST.split("\n")) -> None:
        self.wordlist = wordlist
        self.players = players
        self.word = random.choice(self.wordlist)
        self.charlatan = random.choice(list(self.players.keys()))
        self.voting_players = {player: [-1, 0] for player in players}

    def add_player(self, new_player):
        self.players.update({new_player: 0})
        self.voting_players.update({new_player: [-1, 0]})

    async def send_dms(self):
        """Send dms to players and charlatan displaying wordlist
        """
        info = "> This is the wordlist for this round:\n"
        words = "\n".join(["- " + i if (i is not self.word)
                          else "- **" + i + "** [SECRET WORD]" for i in self.wordlist])
        for key in self.players.keys():  # Sends the wordlist to everyone (altered for Charlatan)
            desc = info + (words if not key == self.charlatan else "\n".join(self.wordlist))
            title = "You are a normal player" if not key == self.charlatan else "You are the Charlatan"
            await key.send(embed=discord.Embed(title=title, description=desc, colour=Colours.PRIMARY))

    async def score_players(self, voted_player: discord.User) -> bool:
        """Handles voting results for players

        Args:
            voted_player (discord.User): The most voted player
            channel (discord.TextChannel): Channel to send result message to
        """
        if voted_player is not self.charlatan:
            logger.debug("Players incorrectly guessed charlatan")
            self.players[self.charlatan] += 2
            return False
        else:
            logger.debug("Correctly guessed charlatan")
            return True

    def charlatan_result(self, correct_guess: bool):
        if correct_guess:
            logger.debug("Charlatan guessed correctly")
            self.players[self.charlatan] += 1
        else:
            logger.debug("Charlatan guessed incorrectly")
            for key in self.players.keys():
                self.players[key] += 1 if key is not self.charlatan else 0

    async def vote(self) -> discord.User:
        """Waits and then returns the most voted player

        Returns:
            discord.User: The most voted player
        """
        await helper.start_timer(PLAYER_VOTE_TIME)
        return sorted(self.voting_players.items(), key=lambda x: x[1][1])[::-1][0][0]  # TODO handle ties

    def cast_vote(self, user: discord.User, button_id: int) -> str:
        if self.voting_players[user][0] != -1:
            # TODO the voted player should probably be part of the callback,
            # rather than relying on hackily storing data in the id

            # Reset the previous vote
            # TODO doesnt work lmao
            self.voting_players[list(self.voting_players)[self.voting_players[user][0]]][1] -= 1
            self.voting_players[user][0] = -1
        voted_player = list(self.voting_players)[int(button_id)]  # indexes into the dictionary
        self.voting_players[voted_player][1] += 1
        self.voting_players[user][0] += int(button_id)  # TODO this cant be a good idea
        return "You voted for {}".format(voted_player.display_name)
