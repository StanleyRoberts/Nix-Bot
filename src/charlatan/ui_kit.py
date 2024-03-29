import random
import discord
from typing import TYPE_CHECKING

from helpers.logger import Logger
import helpers.charlatan as helper
from helpers.style import Emotes, Colours
from charlatan.interface import CHARLATAN_VOTE_TIME, DISCUSSION_TIME
if TYPE_CHECKING:
    from .interface import CharlatanGame


logger = Logger()


class PlayerVoting(discord.ui.View):
    """ View that manages the voting of who the Charlatan is

    Args:
        game_state (CharlatanGame): The current state of the game
    """

    def __init__(self, game_state: "CharlatanGame") -> None:
        logger.debug("New PlayerVoting view created")
        super().__init__(timeout=None)
        self.game_state = game_state
        for i in range(0, len(self.game_state.players)):
            self.add_button(i)

    async def vote(self) -> discord.User | discord.Member:
        """Returns the most voted player

        Returns:
            discord.User | discord.Member: The most voted player
        """
        most_voted = await self.game_state.vote()
        while len(most_voted) > 1:
            logger.info("Restarting loop")
            self.clear_items()
            for i, p in enumerate(self.game_state.players):
                if p.user in most_voted:
                    self.add_button(i)
            await self.message.edit(
                embed=discord.Embed(
                    title="Tied vote!",
                    description="Vote for a Charlatan:\n" + "\n".join(
                        [self.game_state.players[button_id].user.mention + ": " +
                            str(button_id + 1) for button_id, player in
                            enumerate(self.game_state.players)
                            if player.user in most_voted]
                    ),
                    colour=Colours.PRIMARY
                ),
                view=self
            )
            self.game_state.reset_votes()
            most_voted = await self.game_state.vote()
        return most_voted[0]

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
            content = self.game_state.cast_vote(user, int(button.custom_id))
            await interaction.response.send_message(ephemeral=True, content=content)

        button.callback = cast_vote  # type: ignore[method-assign]
        self.add_item(button)


class CharlatanLobby(discord.ui.View):
    """ Pre-game lobby for the "CharlatanGame"

    Args:
        game_state (CharlatanGame): The current state of the game
    """

    def __init__(self, game_state: "CharlatanGame") -> None:
        logger.debug("New CharlatanLobby view created")
        super().__init__(timeout=300)
        self.game_state = game_state

    @discord.ui.button(label="Join", row=0, style=discord.ButtonStyle.primary)
    async def join_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:
        if interaction.user is None:
            logger.warning("Invalid Join interaction")
            return
        if self.game_state.find_player(interaction.user) is None:
            logger.debug("New player joined game", member_id=interaction.user.id)
            self.game_state.add_player(interaction.user)
            await interaction.response.edit_message(embed=self.game_state.make_embed("Charlatan"),
                                                    view=self)
        else:
            logger.info("User double login into Charlatan lobby detected",
                        member_id=interaction.user.id, channel_id=interaction.channel.id
                        if interaction.channel else 0)
            await interaction.response.send_message(
                content=f"You have already joined the game {Emotes.NOEMOTION}",
                ephemeral=True
            )

    @discord.ui.button(label="Rules", row=1, style=discord.ButtonStyle.secondary)
    async def rules_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            ephemeral=True,
            embed=discord.Embed(description=helper.RULES)
        )

    @discord.ui.button(label="Word List", row=1, style=discord.ButtonStyle.secondary)
    async def wordlist_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(view=WordSelection(game_state=self.game_state),
                                                ephemeral=True)

    @discord.ui.button(label="Confirm Lobby", row=2, style=discord.ButtonStyle.primary)
    async def start_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:
        self.game_state.wordlist = self.game_state.wordlist[:16]
        await interaction.response.edit_message(view=CharlatanView(self.game_state))

    @discord.ui.button(label="Leave", row=0, style=discord.ButtonStyle.secondary)
    async def leave_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:
        if interaction.user:
            self.game_state.remove_player(interaction.user)
        await interaction.response.edit_message(view=self)


class CharlatanView(discord.ui.View):
    """View that represent the main flow of the charlatan game"""

    def __init__(self, game_state: "CharlatanGame"):
        logger.debug("Created new CharlatanGame view")
        super().__init__(timeout=300)
        self.game_state = game_state

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.primary)
    async def start_game(self, _: discord.Button, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        self.clear_items()
        self.message = await (await interaction.original_response()).edit(
            embed=discord.Embed(
                description="Game is ongoing",
                title="Charlatan",
                colour=Colours.PRIMARY
            ),
            view=self
        )
        self.game_state.reset_game()
        await self.game_state.send_dms()
        await self.score_players(await self.vote())
        await self.leaderboard()

    async def vote(self) -> discord.User | discord.Member:
        """Begins voting for the Charlatan

        Args:
            channel (discord.TextChannel): Channel to vote using

        Returns:
            discord.User | discord.Member: The most voted player
        """
        logger.debug("Begin player voting")
        view = PlayerVoting(self.game_state)
        await self.message.edit(
            view=view,
            embed=discord.Embed(
                description="Vote for a Charlatan:\n" + "\n".join(
                    [self.game_state.players[button_id].user.mention + ": " +
                        str(button_id + 1) for button_id in
                        range(0, len(self.game_state.players))]
                ),
                title="Charlatan",
                colour=Colours.PRIMARY
            )
        )
        view.message = self.message
        self.clear_items()
        await helper.start_timer(DISCUSSION_TIME)
        return await view.vote()

    async def score_players(self, voted_player: discord.User | discord.Member) -> None:
        """Update view based on voted player

        Args:
            voted_player (discord.User | discord.Member): Player that was voted as charlatan
        """
        charlatan_found = await self.game_state.score_players(voted_player)
        charlatan = self.game_state.get_charlatan().user.mention
        if charlatan_found:
            await self.message.edit(
                embed=discord.Embed(
                    description="The players have found the charlatan, " +
                    f"it was {charlatan} {Emotes.HUG}",
                    title="Charlatan",
                    colour=Colours.PRIMARY),
                view=self
            )
            await self.charlatan_guess()
        else:
            await self.message.edit(
                embed=discord.Embed(
                    description="The players did not find the charlatan, " +
                    f"it was {charlatan} {Emotes.CRYING}",
                    title="Charlatan",
                    colour=Colours.PRIMARY),
                view=self
            )

    async def charlatan_guess(self) -> None:
        """Handles scoring for the charlatan voting for the secret word.

        Sends a voting dm to the charlatan, and handles scoring and output messages for the result.
        Called if the Charlatan was discovered.
        """

        logger.debug("Beginning charlatan voting")
        guess = CharlatanChoice(self)
        await self.game_state.get_charlatan().user.send(view=guess)
        await helper.start_timer(CHARLATAN_VOTE_TIME)

        if not guess.guess_made:
            await self.charlatan_result(False)

    async def charlatan_result(self, correct_guess: bool) -> None:
        """Handles the charlatan guessing the secret word

        Args:
            correct_guess (bool): Whether the charlatan guessed the secret word correctly
        """
        self.game_state.charlatan_result(correct_guess)
        if correct_guess:
            await self.message.edit(
                embed=discord.Embed(
                    description=f"\nThe Charlatan guessed the correct word {Emotes.WHOA}",
                    title="Charlatan",
                    colour=Colours.PRIMARY),
                view=self
            )
        else:
            await self.message.edit(
                embed=discord.Embed(
                    description=f"\nThe Charlatan did not guess the correct word {Emotes.CONFUSED}",
                    title="Charlatan",
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
            self.game_state.wordlist = random.choice(list(helper.WORDLISTS.values()))
            await interaction.response.edit_message(view=CharlatanLobby(self.game_state))
        lobby_button.callback = back_to_lobby  # type: ignore[method-assign]
        self.add_item(lobby_button)

        await self.message.edit(view=self, embed=self.game_state.make_embed("Leaderboard"))


class CharlatanChoice(discord.ui.View):
    """ A view that handles the Charlatan guessing the chosen word

    Args:
        chosen_word (str): The secret chosen word
        word_list (list[str]): The list of all words
        origin ("CharlatanGame"): The Gameview which called this object
    """

    def __init__(self, parent: CharlatanView):
        logger.debug("Created new CharlatanChoice view")
        super().__init__(timeout=120)
        self.parent = parent
        self.guess_made = False
        for i, button_word in enumerate(self.parent.game_state.wordlist):
            self.add_button(
                i,
                False if button_word is not self.parent.game_state.secret_word else True
            )

    def add_button(self, i: int, correct_button: bool) -> None:
        """Adds a button to the view

        Adds a button to the view representing a word in the wordlist.
        Callback activates Charlatan_result with the correctness of the guess

        Args:
            i (int): The button ID, corresponding to its position in the wordlist
            correct_button (bool): Whether the word at postion 'i' is the secret word
        """
        button = discord.ui.Button(label=str(self.parent.game_state.wordlist[i]),
                                   custom_id=str(i))  # type: ignore[var-annotated]

        async def word_guess(interaction: discord.Interaction) -> None:
            """Callback for the added button"""
            if not self.guess_made:
                self.guess_made = True
                if correct_button:
                    logger.debug("CharlatanChoice, correct button callback triggered")
                    response = "You guessed the correct word good job. " + \
                        f"It was \"{self.parent.game_state.secret_word}\" {Emotes.HUG}"
                    await self.parent.charlatan_result(True)
                else:
                    logger.debug("CharlatanChoice, incorrect button callback triggered")
                    response = "You did not guess the correct word. " + \
                        f"It was \"{self.parent.game_state.secret_word}\" {Emotes.CRYING}"
                    await self.parent.charlatan_result(False)
                self.children = [button]
                button.disabled = True
                await self.message.edit(content=response, view=self)
        button.callback = word_guess  # type: ignore[method-assign]
        self.add_item(button)


class WordSelection(discord.ui.View):
    """ Modal to choose a custom wordlist

    Args:
        game_state (CharlatanGame): The current state of the game
    """

    def __init__(self, game_state: "CharlatanGame") -> None:
        logger.debug("New WordSelection modal created")
        super().__init__()
        self.game_state = game_state

    @staticmethod
    def random_selection() -> list[discord.SelectOption]:
        """Return a random selection of the possible wordlists

        Returns:
            list[discord.SelectOption]: List of options for each wordlist in the random subset
        """
        wordlists = [discord.SelectOption(label=x) for x in helper.WORDLISTS.keys()]
        random.shuffle(wordlists)
        return wordlists[:25]

    @discord.ui.select(
        placeholder="Choose a word list!",
        min_values=0,
        max_values=1,
        options=random_selection()
    )
    async def callback(self,
                       select: discord.ui.Select,  # type: ignore[type-arg]
                       interaction: discord.Interaction) -> None:
        """ Changes interaction view to CharlatanLobby

        Edits the interaction message to use the CharlatanLobby view with the new wordlist

        Args:
            interaction (discord.Interaction):
                Interaction containing the message to change the view of
        """
        logger.debug("WordSelection complete, returning to lobby")
        selected_list = select.values[0]
        if not isinstance(selected_list, str):
            logger.warning("Received a non-str type for selected list")
            return
        self.game_state.wordlist = helper.WORDLISTS[selected_list]
        await self.message.edit(f"Wordlist changed to {selected_list} {Emotes.TEEHEE}", view=None)
        await interaction.response.defer()
