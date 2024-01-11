import discord
import random

from helpers.style import Colours
from helpers.logger import Logger
import helpers.charlatan as helper

logger = Logger()

CHARLATAN_VOTE_TIME = 20
PLAYER_VOTE_TIME = 20


class Player:
    """Represents a player in the game

        Args:
            user (discord.User): The Discord user the playerclass represents
            score (int): The score the player has
            votee (int): Who this player voted for
            times_voted_for (int): Amount of players who voted for this player
            is_charlatan (bool):
    """

    def __init__(self, user: discord.User | discord.Member, score: int) -> None:
        self.user = user
        self.score = score
        self.votee = -1
        self.times_voted_for = 0
        self.is_charlatan = False


class CharlatanGame:
    def __init__(self, player: discord.User | discord.Member,
                 wordlist: list[str] = random.choice(helper.WORDLISTS).wordlist) -> None:
        self.wordlist = wordlist
        self.players = [Player(player, 0)]
        self.reset_game()

    def _choose_charlatan(self) -> None:
        charlatan = self.players[random.randint(0, len(self.players) - 1)]
        charlatan.is_charlatan = True
        logger.debug(f"Random Charlatan was selected Charlatan: {charlatan.user.id}")

    def _choose_word(self) -> None:
        self.word = random.choice(self.wordlist)

    def reset_game(self) -> None:
        self._choose_charlatan()
        self._choose_word()

    def add_player(self, new_player: discord.User | discord.Member) -> None:
        self.players.append(Player(new_player, 0))

    async def send_dms(self) -> None:
        """Send dms to players and charlatan displaying wordlist
        """
        info = "> This is the wordlist for this round:\n"
        words = "\n".join(["- " + i if (i is not self.word)
                          else "- **" + i + "** [SECRET WORD]" for i in self.wordlist])
        for player in self.players:  # Sends the wordlist to everyone (altered for Charlatan)
            desc = info + (words if not player.is_charlatan else "\n".join(self.wordlist))
            title = "You are a normal player" if not player.is_charlatan else "You are the Charlatan"
            await player.user.send(embed=discord.Embed(title=title, description=desc, colour=Colours.PRIMARY))

    async def score_players(self, voted_player: discord.User | discord.Member) -> bool:
        """Handles voting results for players

        Args:
            voted_player (discord.User): The most voted player
            channel (discord.TextChannel): Channel to send result message to
        """
        player = self.find_player(voted_player)
        if player is None:
            logger.warning("Attempted to find player not in lobby")
            return False
        if not player.is_charlatan:
            logger.debug("Players didn't find charlatan")
            self.get_charlatan().score += 2
            return False
        else:
            logger.debug("Correctly guessed charlatan")
            return True

    def charlatan_result(self, correct_guess: bool) -> None:
        if correct_guess:
            logger.debug("Charlatan guessed correctly")
            self.get_charlatan().score += 1
        else:
            logger.debug("Charlatan guessed incorrectly")
            for player in self.players:
                player.score += 1 if not player.is_charlatan else 0

    async def vote(self) -> discord.User | discord.Member:
        """Waits and then returns the most voted player

        Returns:
            discord.User: The most voted player
        """
        await helper.start_timer(PLAYER_VOTE_TIME)
        return sorted(self.players, key=lambda x: x.times_voted_for)[::-1][0].user  # TODO handle ties

    def cast_vote(self, user: discord.User | discord.Member, button_id: int) -> str:
        player = self.find_player(user)
        if player is None:
            return "You aren't in this game! Wait for the next round to join..."
        if not player.votee == -1:
            # TODO the voted player should probably be part of the callback,
            # rather than relying on hackily storing data in the id

            # Reset the previous vote
            self.players[player.votee].times_voted_for -= 1
            player.votee = -1
        player.votee = int(button_id)  # TODO this cant be a good idea
        self.players[player.votee].times_voted_for += 1
        return "You voted for {}".format(self.players[player.votee].user.display_name)

    def find_player(self, user: discord.User | discord.Member) -> Player | None:
        for player in self.players:
            if player.user == user:
                return player
        else:
            return None

    def make_embed(self, title: str) -> discord.Embed:
        """Constructs an embed showing the current players in the lobby

            Returns:
                discord.Embed: The constructed embed
            """
        desc = "Playing now:\n " + "\n".join(player.user.display_name + " : " + str(
            player.score) for player in self.players)
        return discord.Embed(title=title, description=desc, colour=Colours.PRIMARY)

    def get_charlatan(self) -> Player:
        for player in self.players:
            if player.is_charlatan:
                return player
        else:
            logger.error("Attempted to get charlatan but no charlatan set")
            return self.players[0]

    def remake_players_with_score(self) -> None:
        self.players = [Player(player.user, player.score) for player in self.players]

    def remake_players_without_score(self) -> None:
        self.players = [Player(player.user, 0) for player in self.players]
