import random
import discord

from helpers.style import Emotes, Colours
from helpers.logger import Logger
from citations.titles import Titles
from citation import CHOICE_AMOUNT

logger = Logger()


class Player:
    """Represents a player in the game
    """

    def __init__(self, user: discord.User | discord.Member) -> None:
        self.user = user
        self.is_liar: bool = True
        self.voted_for: Player | None = None
        self.votes: int = 0


class CitationGame:
    """ Manages the state of the Citations game

    This includes the players, selected nonliar and selected word
    """
    def __init__(
            self,
            initiator: discord.User | discord.Member
    ) -> None:
        self.article = ""
        self.players = [Player(initiator)]

    def _choose_liars(self) -> None:
        nonliar = random.choice(self.players)
        nonliar.is_liar = False
        logger.debug(f"Random not lying player was selected: {nonliar.user.id}")

    def get_article_choices(self) -> list[str]:
        """Returns a list of CHOICE_AMOUNT random article titles"""
        articles = [Titles["a_" + str(i)].value
                    for i in random.sample(range(0, 999838 + 1), CHOICE_AMOUNT)]
        if len(articles) != CHOICE_AMOUNT:
            logger.error(
                f"Logic Error: Didn't get {CHOICE_AMOUNT} choices, missed : "
                + f"{CHOICE_AMOUNT - len(articles)}")
        return articles

    def _get_link(self) -> str:
        article_url = "https://en.wikipedia.org/wiki/"
        return article_url + self.article.replace(' ', '_')

    def add_player(self, new_player: discord.User | discord.Member) -> None:
        """Add new player to game"""
        self.players.append(Player(new_player))

    def remove_player(self, player: discord.User | discord.Member) -> None:
        """Remove player from game if they exist"""
        self.players = [p for p in self.players if p.user.id != player.id]

    async def send_link(self) -> None:
        """Send dm to nonliar with wikipedia link
        """
        nonliar = self.get_non_liar()
        desc = f"Skim the article and close it before the questions begin {Emotes.HUG}" \
               + "\n" + self._get_link()
        title = "You get to tell the truth."
        await nonliar.user.send(
            embed=discord.Embed(title=title, description=desc, colour=Colours.PRIMARY))

    def round_result(self) -> str:
        """ Tallies up vote result and returns description of it.
        Final description shows (in order):
        - Whether non-liar was found and who they were
        - List of players who voted for the correct player
        - How many people voted each player to be the non-liar in descending order

        Returns:
            str: Description of embed showing the round's result
        """
        correct = []

        for player in self.players:
            if player.voted_for is None:
                continue
            if player is not player.voted_for and player.is_liar:
                player.voted_for.votes += 1
                if not player.voted_for.is_liar:
                    correct.append(player)

        most_voted = [p for p in self.players
                      if p.votes == max(self.players, key=lambda p: p.votes).votes]

        nonliar = self.get_non_liar()

        if nonliar not in most_voted:
            reply = "Players didn't find non-liar " + f"{Emotes.CRYING}\n" \
                    + f"it was {nonliar.user.mention}\n"
        else:
            reply = "The non-liar was found " + f"{Emotes.HAPPY}\n"
            if len(most_voted) > 1:
                reply += f"it was {nonliar.user.mention}\n"
        reply += "\n" + "Most voted: " + ", ".join([p.user.mention for p in most_voted]) \
                 + "\n" + "Correct guessers: " + ", ".join([p.user.mention for p in correct])
        return reply + "\n\nVote amount of players:\n " + "\n".join(
            player.user.mention + " : " +
            str(player.votes) for player in self.players)

    def cast_vote(self, user: discord.User | discord.Member, player_idx: int) -> tuple[str, bool]:
        """Handles player voting for nonliar

        Args:
            user (discord.User | discord.Member): Player that casts vote
            player_idx (int): Index of player they voted for

        Returns:
            str: Message to respond with
            bool: Whether vote was valid
        """
        player = self.find_player(user.id)
        if player is None:
            return "You aren't in this game! Wait for the next round to join...", False
        elif player_idx < 0 or player_idx >= len(self.players):
            return "Something went wrong during vote", False
        elif self.players[player_idx] is player:
            return "You are not allowed to vote for yourself", False
        player.voted_for = self.players[player_idx]
        return f"You voted for {self.players[player_idx].user.display_name}", True

    def find_player(self, id: int) -> Player | None:
        """Return player, if they are in the game

        Args:
            id (int): Discord id of player to find

        Returns:
            Player | None: Found player or None if player not in game
        """
        for player in self.players:
            if player.user.id == id:
                return player
        return None

    def make_lobby_embed(self, title: str) -> discord.Embed:
        """Constructs an embed showing the current players in the lobby

            Returns:
                discord.Embed: The constructed embed
            """
        desc = "Playing now:\n " + "\n".join(p.user.display_name for p in self.players)
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
