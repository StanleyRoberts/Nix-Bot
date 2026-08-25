import discord
from typing import TYPE_CHECKING, Callable, Coroutine, Any
import datetime as dt

from helpers.logger import Logger
import helpers.citation as helper
from helpers.style import Emotes
if TYPE_CHECKING:
    from .interface import CitationGame

logger = Logger()


class PlayerVoting(discord.ui.View):
    """ View that manages the voting of who the nonliar is

    Args:
        game_state (CitationGame): The current state of the game
        after_vote (Callable[[Player], Coroutine[Any, Any, None]]):
                                    callback function used after vote is handed in
    """

    def __init__(
        self,
        game_state: "CitationGame",
        after_vote: Callable[[], Coroutine[None, None, None]]
    ) -> None:
        logger.debug("New PlayerVoting view created")
        super().__init__(timeout=None)
        self.game_state = game_state
        self.after_vote = after_vote
        for i in range(0, len(self.game_state.players)):
            self.add_button(i)

    def add_button(self, i: int) -> None:
        """ Adds voting buttons to the view

        Args:
            i (int): Button label and unique ID
        """
        button = discord.ui.Button(
            label=str(i + 1),
            custom_id=str(i)
        )  # type: ignore[var-annotated]

        async def cast_vote(interaction: discord.Interaction) -> None:
            user = interaction.user
            if user is None or button.custom_id is None:
                logger.warning("Invalid button press")
                return
            content, valid = self.game_state.cast_vote(user, int(button.custom_id))
            await interaction.response.send_message(ephemeral=True, content=content)
            if not valid:
                logger.debug("Non valid interaction in cast_vote")
            else:
                await self.after_vote()

        button.callback = cast_vote  # type: ignore[method-assign]
        self.add_item(button)


class CitationLobby(discord.ui.View):
    """ Pre-game lobby for the "CitationGame"

    Args:
        game_state (CitationGame): The current state of the game
    """

    def __init__(self, game_state: "CitationGame") -> None:
        logger.debug("New CitationLobby view created")
        super().__init__(timeout=300)
        self.game_state = game_state

    @discord.ui.button(label="Join", row=0, style=discord.ButtonStyle.primary)
    async def join_callback(
        self,
        _: discord.ui.Button[discord.ui.View],
        interaction: discord.Interaction
    ) -> None:
        if interaction.user is None:
            logger.warning("Invalid Join interaction")
            return
        if self.game_state.find_player(interaction.user.id) is None:
            logger.debug("New player joined game", member_id=interaction.user.id)
            self.game_state.add_player(interaction.user)
            await interaction.response.edit_message(
                            embed=self.game_state.make_lobby_embed(title=helper.CITATIONTITLE),
                            view=self
            )
        else:
            logger.info("User double login into " + helper.CITATIONTITLE + " lobby detected",
                        member_id=interaction.user.id, channel_id=interaction.channel.id
                        if interaction.channel else 0)
            await interaction.response.send_message(
                content=f"You have already joined the game {Emotes.NOEMOTION}",
                ephemeral=True
            )

    @discord.ui.button(label="Rules", row=1, style=discord.ButtonStyle.secondary)
    async def rules_callback(
        self,
        _: discord.ui.Button[discord.ui.View],
        interaction: discord.Interaction
    ) -> None:
        await interaction.response.send_message(
            ephemeral=True,
            embed=discord.Embed(description=helper.CITATIONRULES)
        )

    @discord.ui.button(label="Confirm Lobby", row=2, style=discord.ButtonStyle.primary)
    async def start_callback(
        self,
        _: discord.ui.Button[discord.ui.View],
        interaction: discord.Interaction
    ) -> None:
        await interaction.response.edit_message(view=CitationView(self.game_state))

    @discord.ui.button(label="Leave", row=0, style=discord.ButtonStyle.secondary)
    async def leave_callback(
        self,
        _: discord.ui.Button[discord.ui.View],
        interaction: discord.Interaction
    ) -> None:
        if interaction.user:
            self.game_state.remove_player(interaction.user)
        if len(self.game_state.players) == 0:
            await self.on_timeout()
        else:
            await interaction.response.edit_message(view=self)


class CitationView(discord.ui.View):
    """View that represent the main flow of the Missing Citation game"""

    def __init__(self, game_state: "CitationGame"):
        logger.debug("Created new " + helper.CITATIONTITLE + " view")
        super().__init__(timeout=300)
        self.game_state = game_state
        self.phase: helper.Phases = helper.Phases.TALKING

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.primary)
    async def start_game(
        self,
        _: discord.ui.Button[discord.ui.View],
        interaction: discord.Interaction
    ) -> None:
        await interaction.response.defer()
        self.clear_items()
        self.message = await interaction.original_response()
        await helper.edit_embed(self.message, self, description="Game is ongoing")
        self.game_state._choose_liars()
        await self.article_choice()
        await helper.edit_embed(
            message=self.message,
            view=self,
            description="Unless you got a DM, make up an article about:\n"
                        + self.game_state.article,)
        await self.game_state.send_link()
        await self.vote()

    async def vote(self) -> None:
        """Begins voting for the nonliar

        Args:
            channel (discord.TextChannel): Channel to vote using
        """
        async def callback_voting() -> None:
            if self.phase == helper.Phases.TALKING:
                self.phase = helper.Phases.VOTING
                logger.debug("voting phase started")
                time = f"<t:{dt.datetime.now().timestamp().__ceil__() + helper.VOTE_TIME}:R>"
                await helper.edit_embed(
                    message=self.message,
                    view=view,
                    description="Article is: " + self.game_state.article + "\n"
                                + "Voting phase until: " + time + "\n"
                                + "Vote for person telling the truth:\n" + "\n".join(
                                    [self.game_state.players[button_id].user.mention + ": "
                                        + str(button_id + 1) for button_id in
                                        range(0, len(self.game_state.players))]) + "\n\n"
                                + "Non-liar can vote but it will not be counted.")
                await helper.start_timer(helper.VOTE_TIME)
                if self.phase == helper.Phases.VOTING:
                    self.phase = helper.Phases.ENDING
                    await self.score_player()
            if (all(p.voted_for is not None for p in self.game_state.players)
                    and self.phase == helper.Phases.VOTING):
                self.phase = helper.Phases.ENDING
                await self.score_player()

        logger.debug("Begin player thinking timer")
        await helper.start_timer(helper.THINK_TIME)
        logger.debug("Begin talking stage")
        view = PlayerVoting(self.game_state, callback_voting)
        await helper.edit_embed(
            message=self.message,
            view=view,
            description="Article is: " + self.game_state.article + "\n"
                        + "To begin vote phase " + "\n"
                        + "vote for person telling the truth:\n" + "\n".join(
                            [self.game_state.players[button_id].user.mention + ": " +
                                str(button_id + 1) for button_id in
                                range(0, len(self.game_state.players))]) + "\n\n"
                        + "Player not lying can vote but it will not be counted."
                        )
        view.message = self.message
        self.clear_items()

    async def article_choice(self) -> None:
        """Handles nonliar choosing an article

        Sends a voting dm to the nonliar.
        Called at start of game.
        """

        logger.debug("Beginning article voting")
        article_list = self.game_state.get_article_choices()
        guess = CitationChoice(article_list, self)
        await self.game_state.get_non_liar().user.send(view=guess)
        await helper.start_timer(helper.CHOICE_VOTE_TIME)

        if not guess.choice_made:
            self.game_state.article = article_list[0] if len(article_list) > 0 else "Error"
        self.game_state.article = self.game_state.article.replace('_', ' ')

    async def score_player(self) -> None:
        """Score results and updated view based on votes
        """
        description = self.game_state.score_players()
        await helper.edit_embed(self.message, self, description)


class CitationChoice(discord.ui.View):
    """ View for nonliar to select an article

    Args:
        article_list (list[str]): List of all articles/titles
        origin ("CitationGame"): Gameview which called this object
    """

    def __init__(self, article_list: list[str], parent: CitationView):
        logger.debug("Created new CitationChoice view")
        super().__init__(timeout=120)
        self.parent_view: CitationView = parent
        self.choice_made = False
        for i, button_word in enumerate(article_list):
            self.add_button(
                i,
                button_word
            )

    def add_button(self, i: int, article: str) -> None:
        """Adds a button to the view

        Adds a button to the view representing an article to choose

        Args:
            i (int): The button ID, corresponding to its position in the wordlist
            article (str): Title of the article being represented
        """
        button = discord.ui.Button(label=article.replace('_', ' '),
                                   custom_id=str(i))  # type: ignore[var-annotated]

        async def word_guess(interaction: discord.Interaction) -> None:
            """Callback for the added button"""
            if not self.choice_made:
                self.choice_made = True
                self.parent_view.game_state.article = article
                logger.debug("CitationChoice, choice made.")
                response = f"Article chosen {Emotes.HAPPY}"
                self.children = [button]
                button.disabled = True
                await self.message.edit(content=response, view=self)
        button.callback = word_guess  # type: ignore[method-assign]
        self.add_item(button)
