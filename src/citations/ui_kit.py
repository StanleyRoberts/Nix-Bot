import discord
from typing import TYPE_CHECKING, Callable, Coroutine, Any
import datetime as dt
from asyncio import sleep

from helpers.logger import Logger
import citations.citation as helper
from helpers.style import Emotes
if TYPE_CHECKING:
    from .interface import CitationGame

logger = Logger()


class PlayerVoting(discord.ui.View):
    """ View for players to vote who editor is

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
            if valid:
                await self.after_vote()
            else:
                logger.debug("Non valid interaction in cast_vote")

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

    @discord.ui.button(label="Rules", row=0, style=discord.ButtonStyle.secondary)
    async def rules_callback(
        self,
        _: discord.ui.Button[discord.ui.View],
        interaction: discord.Interaction
    ) -> None:
        await interaction.response.send_message(
            ephemeral=True,
            embed=discord.Embed(description=helper.CITATIONRULES)
        )

    @discord.ui.button(label="Join", row=1, style=discord.ButtonStyle.primary)
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
                        if interaction.channel else None)
            await interaction.response.send_message(
                content=f"You have already joined the game {Emotes.NOEMOTION}",
                ephemeral=True
            )

    @discord.ui.button(label="Leave", row=1, style=discord.ButtonStyle.secondary)
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

    @discord.ui.button(label="Confirm Lobby", row=2, style=discord.ButtonStyle.primary)
    async def start_callback(
        self,
        _: discord.ui.Button[discord.ui.View],
        interaction: discord.Interaction
    ) -> None:
        await interaction.response.edit_message(view=CitationView(self.game_state))


class CitationView(discord.ui.View):
    """View that represents an in-progress Missing Citation game"""

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
        self.clear_items()
        await interaction.response.defer()
        self.message = await interaction.original_response()
        await helper.edit_embed(self.message, self, description="Game is ongoing")
        self.game_state._choose_editor()
        self.game_state.article = await self.article_choice()

        if self.game_state.article is None:
            await helper.edit_embed(
                message=self.message,
                view=self,
                description=f"An error has occured with the game {Emotes.CRYING}")
            return

        await helper.edit_embed(
            message=self.message,
            view=self,
            description="Unless you received a DM, make up an article about:\n"
                        + self.game_state.article)
        await self.game_state.send_article()
        logger.debug("Begin player thinking timer")
        await sleep(helper.THINK_TIME)
        logger.debug("Begin talking stage until first vote gets casted")
        await self.vote()

    async def vote(self) -> None:
        """Begins voting for the editor

        Args:
            channel (discord.TextChannel): Channel to vote using
        """
        async def callback_voting() -> None:
            if self.game_state.article is None:
                logger.warning("Voting callback called with article being None")
                return
            while self.phase is not helper.Phases.FINISHED:
                match self.phase:
                    case helper.Phases.TALKING:
                        self.phase = helper.Phases.VOTING
                        logger.debug("voting phase started")
                        time = dt.datetime.now().timestamp().__ceil__() + helper.VOTE_TIME
                        await helper.edit_embed(
                            message=self.message,
                            view=view,
                            description="Article is: " + self.game_state.article + "\n"
                                        + "Voting phase until: " + f"<t:{time}:R>" + "\n"
                                        + "Vote for person telling the truth:\n" + "\n".join(
                                            [self.game_state.players[button_id].user.mention + ": "
                                                + str(button_id + 1) for button_id in
                                                range(0, len(self.game_state.players))]) + "\n\n"
                                        + "editor can vote but it will not be counted.")
                        await sleep(helper.VOTE_TIME)
                        self.phase = helper.Phases.ENDING
                    case helper.Phases.VOTING:
                        if all(p.voted_for is not None for p in self.game_state.players):
                            self.phase = helper.Phases.ENDING
                    case helper.Phases.ENDING:
                        logger.debug("voting phase ended")
                        self.phase = helper.Phases.FINISHED
                        await self.finish_up_round()
                    case helper.Phases.FINISHED:
                        return

        if self.game_state.article is None:
            logger.warning("Voting called with article being None")
            return
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

    async def article_choice(self) -> str | None:
        """Handles editor choosing an article

        Sends a voting dm to the editor.
        Called at start of game.
        If no article is chosen by the time CHOICE_VOTE_TIME is up, uses first option as choice.

        Return: Article that was chosen; None in case of an error.
        """

        logger.debug("Beginning article voting")
        article_list = self.game_state.get_article_choices()
        guess = CitationChoice(article_list, self)
        await self.game_state.get_editor().user.send(view=guess)
        await sleep(helper.CHOICE_VOTE_TIME)

        if guess.choice is None:
            button = guess.children[0] if len(guess.children) > 0 else None
            if type(button) is discord.ui.Button and button.label is not None:
                button.disabled = True
                guess.children = [button]
                await guess.message.edit(view=guess)
                guess.choice = button.label
            else:
                logger.warning("Could not get an article for citation game")
                return None
        guess.choice = guess.choice.replace('_', ' ')
        return guess.choice

    async def finish_up_round(self) -> None:
        """Calculate round result and updated view based on it"""
        description = self.game_state.round_result()
        await helper.edit_embed(self.message, self, description)


class CitationChoice(discord.ui.View):
    """ View for editor to select an article

    Args:
        article_list (list[str]): Subset of articles/titles to choose from
        origin ("CitationGame"): Gameview which called this object
    """

    def __init__(self, article_list: list[str], parent: CitationView):
        logger.debug("Created new CitationChoice view")
        super().__init__(timeout=120)
        self.parent_view: CitationView = parent
        self.choice: str | None = None
        for i, button_word in enumerate(article_list):
            self.add_button(i, button_word)

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
            if self.choice is not None:
                return

            self.choice = article
            logger.debug("CitationChoice, choice made.")
            response = f"Article chosen {Emotes.HAPPY}"
            self.children = [button]
            button.disabled = True
            await self.message.edit(view=self)
            await interaction.respond(content=response)
        button.callback = word_guess  # type: ignore[method-assign]
        self.add_item(button)
