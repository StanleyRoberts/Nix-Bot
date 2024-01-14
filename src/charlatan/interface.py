import random
import discord

from helpers.style import Colours
from helpers.logger import Logger
import helpers.charlatan as helper

logger = Logger()

CHARLATAN_VOTE_TIME = 15
PLAYER_VOTE_TIME = 15
DISCUSSION_TIME = 30


class Player:
    """Represents a player in the game
    """

    def __init__(self, user: discord.User | discord.Member, score: int) -> None:
        self.user = user
        self.score = score
        self.votee = -1
        self.times_voted_for = 0
        self.is_charlatan = False


class CharlatanGame:
    """ Manages the state of the Charlatan game

    This includes the players, score, selected charlatan and selected word
    """

    def __init__(
            self,
            player: discord.User | discord.Member,
            wordlist: list[str] = random.choice(list(helper.WORDLISTS.values()))
    ) -> None:
        self.wordlist = wordlist
        self.secret_word = random.choice(self.wordlist)
        self.players = [Player(player, 0)]
        self.reset_game()

    def _choose_charlatan(self) -> None:
        for p in self.players:
            p.is_charlatan = False
        charlatan = self.players[random.randint(0, len(self.players) - 1)]
        charlatan.is_charlatan = True
        logger.debug(f"Random Charlatan was selected: {charlatan.user.id}")

    def _choose_word(self) -> None:
        self.secret_word = random.choice(self.wordlist)

    def reset_game(self) -> None:
        """ Reset charlatan game. (maintains scores)

        Chooses new charlatan and secret wor
        """
        self._choose_charlatan()
        self._choose_word()

    def add_player(self, new_player: discord.User | discord.Member) -> None:
        """Add new player to game"""
        self.players.append(Player(new_player, 0))

    def remove_player(self, player: discord.User | discord.Member) -> None:
        """Remove player from game if they exist"""
        self.players = [p for p in self.players if p.user.id != player.id]

    async def send_dms(self) -> None:
        """Send dms to players and charlatan displaying wordlist
        """
        info = "> This is the wordlist for this round:\n"
        secret_words = "\n".join(
            ["- " + i if (i is not self.secret_word)
             else "- **" + i + "** [SECRET WORD]"
             for i in self.wordlist]
        )
        all_words = "\n".join(["- " + i for i in self.wordlist])

        for player in self.players:
            desc = info + (all_words if player.is_charlatan else secret_words)
            title = "You are the Charlatan" if player.is_charlatan else "You are a normal player"
            await player.user.send(
                embed=discord.Embed(title=title, description=desc, colour=Colours.PRIMARY)
            )

    async def score_players(self, voted_player: discord.User | discord.Member) -> bool:
        """Handles voting result for normal players

        Args:
            voted_player (discord.User | discord.Member): The most voted player

        Returns:
            bool: Whether the voted player was the charlatan
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
        """Handles voting result for the charlatan

        Args:
            correct_guess (bool): Whether the charalatan successfully guessed the secret word
        """
        if correct_guess:
            logger.debug("Charlatan guessed correctly")
            self.get_charlatan().score += 1
        else:
            logger.debug("Charlatan guessed incorrectly")
            for player in self.players:
                player.score += 1 if not player.is_charlatan else 0

    async def vote(self) -> list[discord.User | discord.Member]:
        """Waits and then returns the most voted player

        Returns:
            list[discord.User | discord.Member]:
                List containing the player with most votes (multiple if tie)
        """
        await helper.start_timer(PLAYER_VOTE_TIME)
        sort = sorted(self.players, key=lambda x: x.times_voted_for)[::-1]
        return [x.user for x in sort if x.times_voted_for == sort[0].times_voted_for]

    def reset_votes(self) -> None:
        """Reset votes for each player
        """
        for p in self.players:
            p.times_voted_for = 0

    def cast_vote(self, user: discord.User | discord.Member, player_idx: int) -> str:
        """Handles player voting for charlatan

        Args:
            user (discord.User | discord.Member): Player that cast vote
            player_idx (int): Index of player they voted for

        Returns:
            str: Message to respond with
        """
        player = self.find_player(user)
        if player is None:
            return "You aren't in this game! Wait for the next round to join..."
        if not player.votee == -1:
            # Reset the previous vote
            self.players[player.votee].times_voted_for -= 1
            player.votee = -1
        player.votee = int(player_idx)
        self.players[player.votee].times_voted_for += 1
        return f"You voted for {self.players[player.votee].user.display_name}"

    def find_player(self, user: discord.User | discord.Member) -> Player | None:
        """Return player if they are in the game

        Args:
            user (discord.User | discord.Member): Player to find

        Returns:
            Player | None: Found player or None if player not in game
        """
        for player in self.players:
            if player.user == user:
                return player
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
        """Get charlatan for this game

        Returns:
            Player: Charlatan
        """
        for player in self.players:
            if player.is_charlatan:
                return player
        logger.error("Attempted to get charlatan but no charlatan set")
        return self.players[0]

    def reset_scores(self) -> None:
        """Reset the scores for all players in the game
        """
        self.players = [Player(player.user, 0) for player in self.players]
