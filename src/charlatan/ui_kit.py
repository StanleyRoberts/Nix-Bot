import random
import discord
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .interface import CharlatanGame
from helpers.logger import Logger
import helpers.charlatan as helper
from helpers.style import Emotes, Colours
logger = Logger()

CHARLATAN_VOTE_TIME = 20
PLAYER_VOTE_TIME = 20


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
        """Waits and then returns the most voted player

        Returns:
            discord.User | discord.Member: The most voted player
        """
        return await self.game_state.vote()  # TODO handle ties

    def add_button(self, i: int) -> None:
        """ Adds voting buttons to the view

        Args:
            i (int): Button label and unique ID
        """
        button = discord.ui.Button(label=str(i + 1), custom_id=str(i))  # type: ignore[var-annotated]

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

    @discord.ui.button(label="Word List", row=0, style=discord.ButtonStyle.secondary)
    async def wordlist_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(WordSelection(title="Word List", game_state=self.game_state))

    @discord.ui.button(label="Join", row=0, style=discord.ButtonStyle.primary)
    async def join_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:
        if interaction.user is None:
            logger.warning("Invalid Join interaction")
            return
        if self.game_state.find_player(interaction.user) is None:
            logger.debug("New player joined game", member_id=interaction.user.id)
            self.game_state.add_player(interaction.user)
            view = CharlatanLobby(self.game_state)
            await interaction.response.edit_message(embed=self.game_state.make_embed("Charlatan"),
                                                    view=view)
        else:
            logger.info("User double login into Charlatan lobby detected",
                        member_id=interaction.user.id, channel_id=interaction.channel.id if interaction.channel else 0)
            await interaction.response.send_message(content=f"You have already joined the game {Emotes.NOEMOTION}",
                                                    ephemeral=True)

    @discord.ui.button(label="Rules", row=1, style=discord.ButtonStyle.secondary)
    async def rules_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(ephemeral=True, embed=discord.Embed(description=helper.RULES))

    @discord.ui.button(label="Confirm Lobby", row=1, style=discord.ButtonStyle.primary)
    async def start_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:
        self.game_state.wordlist = self.game_state.wordlist[:16]
        await interaction.response.edit_message(view=CharlatanView(self.game_state))


class CharlatanView(discord.ui.View):
    def __init__(self, game_state: "CharlatanGame"):
        logger.debug("Created new CharlatanGame view")
        super().__init__(timeout=300)
        self.game_state = game_state

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.primary)
    async def start_game(self, _: discord.Button, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        self.clear_items()
        self.message = await (await interaction.original_response()).edit(
            embed=discord.Embed(description="Game is ongoing", title="Charlatan", colour=Colours.PRIMARY), view=self)
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
        await self.message.edit(view=view, embed=discord.Embed(description="Vote for a Charlatan:\n" + "\n".join(
            [self.game_state.players[button_id].user.mention + ": " + str(button_id + 1) for button_id in
                range(0, len(self.game_state.players))]), title="Charlatan", colour=Colours.PRIMARY))
        self.clear_items()
        return await view.vote()

    async def score_players(self, voted_player: discord.User | discord.Member) -> None:
        charlatan_found = await self.game_state.score_players(voted_player)
        if charlatan_found:
            await self.message.edit(
                embed=discord.Embed(description="The players have found the charlatan, it was {} {}"
                                    .format(self.game_state.get_charlatan().user.mention, Emotes.HUG),
                                    title="Charlatan", colour=Colours.PRIMARY), view=self)
            await self.charlatan_guess()
        else:
            await self.message.edit(
                embed=discord.Embed(description="The players did not find the charlatan, it was {} {}"
                                    .format(self.game_state.get_charlatan().user.mention, Emotes.CRYING),
                                    title="Charlatan", colour=Colours.PRIMARY), view=self)

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
        self.game_state.charlatan_result(correct_guess)
        if correct_guess:
            await self.message.edit(embed=discord.Embed(description="\nThe Charlatan guessed the correct word {}"
                                    .format(Emotes.WHOA), title="Charlatan", colour=Colours.PRIMARY), view=self)
        else:
            await self.message.edit(embed=discord.Embed(description="\nThe Charlatan did not guess the correct word {}"
                                    .format(Emotes.CONFUSED), title="Charlatan", colour=Colours.PRIMARY), view=self)

    async def leaderboard(self) -> None:
        """Adds Play Again and Back to Lobby buttons to the interaction message
        """
        self.clear_items()

        play_again_button = discord.ui.Button(label="Play Again",
                                              style=discord.ButtonStyle.primary)  # type: ignore[var-annotated]

        async def play_again(interaction: discord.Interaction) -> None:
            self.game_state.remake_players_with_score()
            view = CharlatanView(self.game_state)
            await interaction.response.edit_message(view=view)
        play_again_button.callback = play_again  # type: ignore[method-assign]
        self.add_item(play_again_button)

        lobby_button = discord.ui.Button(label="Back to Lobby",
                                         style=discord.ButtonStyle.secondary)  # type: ignore[var-annotated]

        async def back_to_lobby(interaction: discord.Interaction) -> None:
            play_again_button.disabled = True
            self.game_state.remake_players_without_score()
            self.game_state.wordlist = random.choice(helper.WORDLISTS).wordlist
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
        for i in range(len(self.parent.game_state.wordlist)):
            self.add_button(
                i, False if self.parent.game_state.wordlist[i] is not self.parent.game_state.word else True)

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
                    response = "You guessed the correct word good job. It was \"{}\" {}".format(
                        self.parent.game_state.word, Emotes.HUG)
                    await self.parent.charlatan_result(True)
                else:
                    logger.debug("CharlatanChoice, incorrect button callback triggered")
                    response = "You did not guess the correct word. It was \"{}\" {}".format(
                        self.parent.game_state.word, Emotes.CRYING)
                    await self.parent.charlatan_result(False)
                self.children = [button]
                button.disabled = True
                await self.message.edit(content=response, view=self)
        button.callback = word_guess  # type: ignore[method-assign]
        self.add_item(button)


class WordSelection(discord.ui.Modal):
    """ Modal to choose a custom wordlist

    Args:
        game_state (CharlatanGame): The current state of the game
    """

    def __init__(self, title: str, game_state: "CharlatanGame") -> None:
        logger.debug("New WordSelection modal created")
        super().__init__(title=title)
        self.add_item(discord.ui.InputText(label="Add 16 words for the game here:",
                                           style=discord.InputTextStyle.long,
                                           placeholder="".join(random.choice(helper.WORDLISTS).wordlist)[:97] + "..."))
        self.game_state = game_state

    async def callback(self, interaction: discord.Interaction) -> None:
        """ Changes interaction view to CharlatanLobby

        Edits the interaction message to use the CharlatanLobby view with the new wordlist

        Args:
            interaction (discord.Interaction): Interaction containing the message to change the view of
        """
        logger.debug("WordSelection complete, returning to lobby")
        new_wordlist = self.children[0].value
        if new_wordlist is None:
            return
        self.game_state.wordlist = new_wordlist.split('\n')
        view = CharlatanLobby(self.game_state)
        if interaction.message is None:
            logger.warning("Interaction message is none, could not return to lobby")
            return
        await interaction.message.edit(embed=self.game_state.make_embed("Charlatan"),
                                       view=view)
