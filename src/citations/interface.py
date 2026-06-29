import random
import requests
import discord
import json

from typing import Tuple
from helpers.style import Colours
from helpers.logger import Logger
import helpers.charlatan as helper

logger = Logger()

THINKING_TIME = 15


class Player:
    """Represents a player in the game
    """

    def __init__(self, user: discord.User | discord.Member, score: int) -> None:
        self.user = user
        self.score = score
        self.is_liar = True
        self.is_guesser = False


class CitationGame:
    """ Manages the state of the Charlatan game

    This includes the players, score, selected charlatan and selected word
    """
    def __init__(
            self,
            player: discord.User | discord.Member
    ) -> None:
        self.article = ""
        self.players = [Player(player, 0)]
        self.reset_game()

    def _choose_guesser(self) -> None:
        """ Chooses a guessing player for the game
        Needs to be done after choosing the impostor.
        """
        valid = [player for player in self.players if player.is_liar]
        guesser = random.choice(valid)
        guesser.is_guesser = True
        logger.debug(f"Random Guesser was selected: {guesser.user.id}")

    def _choose_liars(self) -> None:
        nonliar = random.choice(self.players)
        nonliar.is_liar = False
        logger.debug(f"Random not lying player was selected: {nonliar.user.id}")

    def get_word_choices(self) -> list[str]:
        choices = []
        line_indeces = [random.randint(0, 999838) for _ in range(10)]
        line_indeces.sort()
        with open('titles.txt', 'r') as titles:
            counter = 0
            for title in titles:
                if counter == line_indeces[0]:
                    choices.append(title)
                    line_indeces.pop(0)
                    if len(line_indeces) == 0:
                        return choices
                counter += 1
        logger.error(f"Didn't get 10 choices, missed : {line_indeces}")
        return choices

    def _get_link(self) -> str:
        article_url = "https://en.wikipedia.org/wiki/"
        return article_url + self.article.replace(' ', '_')

    def reset_game(self) -> None:
        """ Reset charlatan game. (maintains scores)
        Chooses new guesser, impostor and secret wor
        """
        for p in self.players:
            p.is_guesser = False
            p.is_liar = True

    def add_player(self, new_player: discord.User | discord.Member) -> None:
        """Add new player to game"""
        self.players.append(Player(new_player, 0))

    def remove_player(self, player: discord.User | discord.Member) -> None:
        """Remove player from game if they exist"""
        self.players = [p for p in self.players if p.user.id != player.id]

    async def send_dms(self) -> None:
        """Send dms to players and impostor displaying wordlist
        """
        nonliar = self.get_non_liar()
        desc = self._get_link()
        title = "You get to tell the truth."
        await nonliar.user.send(
            embed=discord.Embed(title=title, description=desc, colour=Colours.PRIMARY)
        )

    async def score_players(self, voted_player: Player) -> bool:
        """Handles round result for normal players

        Args:
            voted_player (discord.User | discord.Member): Player voted for by the guesser

        Returns:
            bool: Whether the voted player was the charlatan
        """
        if voted_player is None:
            logger.warning("Attempted to find player not in lobby")
            return False
        if voted_player.is_liar:
            logger.debug("Guesser didn't find nonliar")
            voted_player.score += 1
            return False
        else:
            logger.debug("Correctly guessed nonliar")
            self.get_non_liar().score += 1
            self.get_guesser().score += 1
            return True

    def cast_vote(
        self,
        user: discord.User | discord.Member,
        player_idx: int
    ) -> Tuple[str, bool, Player | None]:
        """Handles player voting for nonliar

        Args:
            user (discord.User | discord.Member): Player that cast vote
            player_idx (int): Index of player they voted for

        Returns:
            str: Message to respond with
            bool: whether the vote was valid
            discord.User | discord.Member: player they voted for
        """
        player = self.find_player(user)
        if player is None:
            return "You aren't in this game! Wait for the next round to join...", False, None
        if not player.is_guesser:
            return "You are not allowed to vote this round. As you are not guessing.", False, None
        voted_for = self.players[player_idx]
        return f"You voted for {voted_for.user.display_name}", True, voted_for

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

    def get_non_liar(self) -> Player:
        """Get not lying player of this round

        Returns:
            Player: nonliar
        """
        for player in self.players:
            if not player.is_liar:
                return player
        logger.error("Attempted to get nonliar but no non liar set")
        return self.players[0]

    def get_guesser(self) -> Player:
        """Get guesser of this round
        Returns:
            Player: Guesser
        """
        for player in self.players:
            if player.is_guesser:
                return player
        logger.error("Attempted to get guesser but no guesser set")
        return self.players[0]

    def reset_scores(self) -> None:
        """Reset the scores for all players in the game
        """
        self.players = [Player(player.user, 0) for player in self.players]
