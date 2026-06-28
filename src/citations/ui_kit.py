import discord
from typing import TYPE_CHECKING, Callable, Coroutine, Any

from helpers.logger import Logger
import helpers.citation as helper
from helpers.style import Emotes, Colours
from citations.interface import THINKING_TIME, Player
if TYPE_CHECKING:
    from .interface import CitationGame

CHOICE_VOTE_TIME = 15

logger = Logger()

class PlayerVoting(discord.ui.View):
    """ View that manages the voting of who the nonliar is

    Args:
        game_state (CitationGame): The current state of the game
        after_vote (Callable[[Player], Coroutine[Any, Any, None]]): callback function used after vote is handed in
    """

    def __init__(self, game_state: "CitationGame", after_vote: Callable[[Player], Coroutine[Any, Any, None]]) -> None:
        logger.debug("New PlayerVoting view created")
        super().__init__(timeout=None)
        self.game_state = game_state
        self.after_vote = after_vote
        for i in range(0, len(self.game_state.players)-1):
            self.add_button(i)

    def add_button(self, i: int) -> None:
        """ Adds voting buttons to the view

        Args:
            i (int): Button label and unique ID
        """
        if self.game_state.players[i].is_guesser:
            return

        button = discord.ui.Button(
            label=str(i + 1),
            custom_id=str(i)
        )  # type: ignore[var-annotated]

        async def cast_vote(interaction: discord.Interaction) -> None:
            user = interaction.user
            if user is None or button.custom_id is None:
                logger.warning("Invalid button press")
                return
            content, is_valid, guessed = self.game_state.cast_vote(user, int(button.custom_id))
            if is_valid and guessed is not None:
                await self.after_vote(guessed)
            logger.debug("Non valid interaction in cast_vote")
            await interaction.response.send_message(ephemeral=True, content=content)

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
    async def join_callback(self, _: discord.ui.Button[discord.ui.View], interaction: discord.Interaction) -> None:
        if interaction.user is None:
            logger.warning("Invalid Join interaction")
            return
        if self.game_state.find_player(interaction.user) is None:
            logger.debug("New player joined game", member_id=interaction.user.id)
            self.game_state.add_player(interaction.user)
            await interaction.response.edit_message(embed=self.game_state.make_embed(title=helper.CITATIONTITLE),
                                                    view=self)
        else:
            logger.info("User double login into " + helper.CITATIONTITLE + " lobby detected",
                        member_id=interaction.user.id, channel_id=interaction.channel.id
                        if interaction.channel else 0)
            await interaction.response.send_message(
                content=f"You have already joined the game {Emotes.NOEMOTION}",
                ephemeral=True
            )

    @discord.ui.button(label="Rules", row=1, style=discord.ButtonStyle.secondary)
    async def rules_callback(self, _: discord.ui.Button[discord.ui.View], interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            ephemeral=True,
            embed=discord.Embed(description=helper.CITATIONRULES)
        )

    @discord.ui.button(label="Confirm Lobby", row=2, style=discord.ButtonStyle.primary)
    async def start_callback(self, _: discord.ui.Button[discord.ui.View], interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(view=CitationView(self.game_state))

    @discord.ui.button(label="Leave", row=0, style=discord.ButtonStyle.secondary)
    async def leave_callback(self, _: discord.ui.Button[discord.ui.View], interaction: discord.Interaction) -> None:
        if interaction.user:
            self.game_state.remove_player(interaction.user)
        await interaction.response.edit_message(view=self)


class CitationView(discord.ui.View):
    """View that represent the main flow of the Missing Citation game"""

    def __init__(self, game_state: "CitationGame"):
        logger.debug("Created new " + helper.CITATIONTITLE + " view")
        super().__init__(timeout=300)
        self.game_state = game_state

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.primary)
    async def start_game(self, _: discord.ui.Button[discord.ui.View], interaction: discord.Interaction) -> None:
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
        self.game_state._choose_guesser()
        await self.article_choice()
        self.message = await (await interaction.original_response()).edit(
            embed=discord.Embed(
                description="Game is ongoing\n"\
                    + "Guesser is: " + self.game_state.get_guesser().user.mention +"\n" \
                    + "Article is: " + self.game_state.article,
                title=helper.CITATIONTITLE,
                colour=Colours.PRIMARY
            ),
            view=self
        )
        self.game_state
        await self.game_state.send_dms()
        await self.vote()

    async def vote(self) -> None:
        """Begins voting for the nonliar

        Args:
            channel (discord.TextChannel): Channel to vote using

        """
        async def callback_voting(player: Player) -> None:
            await self.score_player(player)
            await self.leaderboard()

        logger.debug("Begin player voting timer")
        await helper.start_timer(THINKING_TIME)
        logger.debug("Begin player voting")
        view = PlayerVoting(self.game_state, callback_voting)
        await self.message.edit(
            view=view,
            embed=discord.Embed(
                description="Vote for a nonliar:\n" + "\n".join(
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
        await helper.start_timer(CHOICE_VOTE_TIME)

        if not guess.choice_made:
            self.game_state.article = article_list[0] if len(article_list) > 0 else "Error"

    async def score_player(self, voted_player: Player) -> None:
        """Update view based on voted player

        Args:
            voted_player (discord.User | discord.Member): Player that was voted as nonliar
        """
        nonliar_found = await self.game_state.score_players(voted_player)
        nonliar = self.game_state.get_non_liar().user.mention
        if nonliar_found:
            await self.message.edit(
                embed=discord.Embed(
                    description="The guesser has found the truth speaker, " +
                    f"it was {nonliar} {Emotes.HUG}",
                    title=helper.CITATIONTITLE,
                    colour=Colours.PRIMARY),
                view=self
            )
        else:
            await self.message.edit(
                embed=discord.Embed(
                    description="The players did not find the truth speaker, " +
                    f"it was {nonliar} {Emotes.CRYING}",
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
    """ A view for the guesser to guess who is not lying

    Args:
        article_list (list[str]): The list of all words
        origin ("CitationGame"): The Gameview which called this object
    """

    def __init__(self, article_list: list[str], parent: CitationView):
        logger.debug("Created new CitationChoice view")
        super().__init__(timeout=120)
        self.parent: CitationView = parent
        self.choice_made = False
        for i, button_word in enumerate(article_list):
            self.add_button(
                i,
                button_word
            )

    def add_button(self, i: int, article: str) -> None:
        """Adds a button to the view

        Adds a button to the view representing an article to choose from
        Callback activates Charlatan_result with the correctness of the guess

        Args:
            i (int): The button ID, corresponding to its position in the wordlist
            correct_button (bool): Whether the word at postion 'i' is the secret word
        """
        button = discord.ui.Button(label=article,
                                   custom_id=str(i))  # type: ignore[var-annotated]

        async def word_guess(interaction : discord.Interaction) -> None:
            """Callback for the added button"""
            if not self.choice_made:
                self.choice_made = True
                self.parent.game_state.article = article
                logger.debug("CitationChoice, choice made.")
                response = f"Article chosen. Read the article's summary and close it before the questions begin. {Emotes.HUG}"
                self.children = [button]
                button.disabled = True
                await self.message.edit(content=response, view=self)
        button.callback = word_guess
        self.add_item(button)
