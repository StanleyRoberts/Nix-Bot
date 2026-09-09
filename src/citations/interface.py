import random
import discord

from helpers.style import Emotes, Colours
from helpers.logger import Logger
from citations.titles import Titles
from citations.citation import CHOICE_AMOUNT

logger = Logger()


class Player:
    """Represents a player in the game
    """

    def __init__(self, user: discord.User | discord.Member) -> None:
        self.user = user
        self.is_misinformant: bool = True
        self.voted_for: Player | None = None
        self.votes: int = 0


class CitationGame:
    """ Manages the state of the Citations game

    This includes the players, selected editor and selected word
    """
    def __init__(
            self,
            initiator: discord.User | discord.Member
    ) -> None:
        self.article = ""
        self.players = [Player(initiator)]

    def _choose_misinformant(self) -> None:
        editor = random.choice(self.players)
        editor.is_misinformant = False
        logger.debug(f"Random not lying player was selected: {editor.user.id}")

    def get_article_choices(self) -> list[str]:
        """Returns a list of CHOICE_AMOUNT random article titles"""
        articles = [Titles["a_" + str(i)].value
                    for i in random.sample(range(0, 999580 + 1), CHOICE_AMOUNT)]
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
        """Send dm to editor with wikipedia link
        """
        editor = self.get_editor()
        desc = f"Skim the article and close it before the questions begin {Emotes.HUG}" \
               + "\n" + self._get_link()
        title = "You get to tell the truth."
        await editor.user.send(
            embed=discord.Embed(title=title, description=desc, colour=Colours.PRIMARY))

    def round_result(self) -> str:
        """ Tallies up vote result and returns description of it.
        Final description shows (in order):
        - Whether editor was found and who they were
        - List of players who voted for the correct player
        - How many people voted each player to be the editor in descending order

        Returns:
            str: Description of embed showing the round's result
        """
        correct = []

        for player in self.players:
            if player.voted_for is None:
                continue
            if player is not player.voted_for and player.is_misinformant:
                player.voted_for.votes += 1
                if not player.voted_for.is_misinformant:
                    correct.append(player)

        most_voted = [p for p in self.players
                      if p.votes == max(self.players, key=lambda p: p.votes).votes]

        editor = self.get_editor()

        if editor not in most_voted:
            reply = "Players didn't find editor " + f"{Emotes.CRYING}\n" \
                    + f"it was {editor.user.mention}\n"
        else:
            reply = "The editor was found " + f"{Emotes.HAPPY}\n"
            if len(most_voted) > 1:
                reply += f"it was {editor.user.mention}\n"
        reply += "\n" + "Most voted: " + ", ".join([p.user.mention for p in most_voted]) \
                 + "\n" + "Correct guessers: " + ", ".join([p.user.mention for p in correct])
        return reply + "\n\nVote amount of players:\n " + "\n".join(
            player.user.mention + " : " +
            str(player.votes) for player in self.players)

    def cast_vote(self, user: discord.User | discord.Member, player_idx: int) -> tuple[str, bool]:
        """Handles player voting for editor

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

    def get_editor(self) -> Player:
        """Get not lying player of this round

        Returns:
            Player: editor
        """
        for player in self.players:
            if not player.is_misinformant:
                return player
        logger.error("Attempted to get editor, but none set")
        return self.players[0]
