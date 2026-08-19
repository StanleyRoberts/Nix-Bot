import discord
from typing import TYPE_CHECKING, Callable, Coroutine, Any
import datetime as dt

from helpers.logger import Logger
import helpers.citation as helper
from helpers.style import Emotes, Colours
from citations.interface import Player
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
        after_vote: Callable[[], Coroutine[Any, Any, None]]
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
        if self.game_state.find_player(interaction.user) is None:
            logger.debug("New player joined game", member_id=interaction.user.id)
            self.game_state.add_player(interaction.user)
            await interaction.response.edit_message(
                            embed=self.game_state.make_embed(title=helper.CITATIONTITLE),
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
        await interaction.response.edit_message(view=self)


class CitationView(discord.ui.View):
    """View that represent the main flow of the Missing Citation game"""

    def __init__(self, game_state: "CitationGame"):
        logger.debug("Created new " + helper.CITATIONTITLE + " view")
        super().__init__(timeout=300)
        self.game_state = game_state
        self.in_voting_phase = False

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.primary)
    async def start_game(
        self,
        _: discord.ui.Button[discord.ui.View],
        interaction: discord.Interaction
    ) -> None:
        await interaction.response.defer()
        self.clear_items()
        self.message = await (await interaction.original_response()).edit(
            embed=discord.Embed(
                description="Game is ongoing",
                title=helper.CITATIONTITLE,
                colour=Colours.PRIMARY
            ),
            view=self
        )
        self.game_state.reset_game()
        self.game_state._choose_liars()
        await self.article_choice()
        self.message = await (await interaction.original_response()).edit(
            embed=discord.Embed(
                description="First stage: Think of an article that could have that title.\n"
                + "Article is: " + self.game_state.article,
                title=helper.CITATIONTITLE,
                colour=Colours.PRIMARY
            ),
            view=self
        )
        await self.game_state.send_dms()
        await self.vote()

    async def vote(self) -> None:
        """Begins voting for the nonliar

        Args:
            channel (discord.TextChannel): Channel to vote using

        """
        async def callback_voting() -> None:
            if not self.in_voting_phase:
                self.in_voting_phase = True
                logger.debug("voting phase started")
                time = discord.utils.format_dt(
                    dt.datetime.now() + dt.timedelta(minutes=1), style="T")
                await self.message.edit(
                    view=view,
                    embed=discord.Embed(
                        description="Article is: " + self.game_state.article + "\n"
                                    + "Voting phase until: " + time + "\n"
                                    + "Vote for person telling the truth:\n" + "\n".join(
                                        [self.game_state.players[button_id].user.mention + ": " +
                                            str(button_id + 1) for button_id in
                                            range(0, len(self.game_state.players))]
                                    ),
                        title=helper.CITATIONTITLE,
                        colour=Colours.PRIMARY
                    )
                )
                await helper.start_timer(helper.VOTE_TIME)
                await self.score_player()
                await helper.start_timer(helper.VOTE_RESULT_TIME)
                await self.leaderboard()

        logger.debug("Begin player thinking timer")
        await helper.start_timer(helper.THINK_TIME)
        logger.debug("Begin talking stage")
        view = PlayerVoting(self.game_state, callback_voting)
        await self.message.edit(
            view=view,
            embed=discord.Embed(
                description="Article is: " + self.game_state.article + "\n"
                            + "To begin vote phase " + "\n"
                            + "vote for person telling the truth:\n" + "\n".join(
                                [self.game_state.players[button_id].user.mention + ": " +
                                    str(button_id + 1) for button_id in
                                    range(0, len(self.game_state.players))]
                            ),
                title=helper.CITATIONTITLE,
                colour=Colours.PRIMARY
            )
        )
        view.message = self.message
        self.clear_items()

    async def article_choice(self) -> None:
        """Handles nonliar choosing an article

        Sends a voting dm to the nonliar.
        Called at start of game.
        """

        logger.debug("Beginning article voting")
        article_list = self.game_state.get_word_choices()
        guess = CitationChoice(article_list, self)
        await self.game_state.get_non_liar().user.send(view=guess)
        await helper.start_timer(helper.CHOICE_VOTE_TIME)

        if not guess.choice_made:
            self.game_state.article = article_list[0] if len(article_list) > 0 else "Error"

    async def score_player(self) -> None:
        """Score results and updated view based on votes
        """
        description = self.game_state.score_players()
        await self.message.edit(
            embed=discord.Embed(
                description=description,
                title=helper.CITATIONTITLE,
                colour=Colours.PRIMARY),
            view=self
        )

    async def leaderboard(self) -> None:
        """Adds Play Again and Back to Lobby buttons to the interaction message
        """
        self.clear_items()

        play_again_button = discord.ui.Button(
            label="Play Again",
            style=discord.ButtonStyle.primary
        )  # type: ignore[var-annotated]

        async def play_again(interaction: discord.Interaction) -> None:
            await interaction.response.edit_message(view=self)
        play_again_button.callback = play_again  # type: ignore[method-assign]
        self.add_item(play_again_button)

        lobby_button = discord.ui.Button(
            label="Back to Lobby",
            style=discord.ButtonStyle.secondary
        )  # type: ignore[var-annotated]

        async def back_to_lobby(interaction: discord.Interaction) -> None:
            play_again_button.disabled = True
            self.game_state.reset_scores()
            await interaction.response.edit_message(view=CitationLobby(self.game_state))
        lobby_button.callback = back_to_lobby  # type: ignore[method-assign]
        self.add_item(lobby_button)

        await self.message.edit(view=self, embed=self.game_state.make_embed("Leaderboard"))


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
                response = f"Article chosen. Read the article's summary" \
                    + f" and close it before the questions begin. {Emotes.HUG}"
                self.children = [button]
                button.disabled = True
                await self.message.edit(content=response, view=self)
        button.callback = word_guess  # type: ignore[method-assign]
        self.add_item(button)
