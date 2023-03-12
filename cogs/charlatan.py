# TODO this needs a lot of review before merge
# Ive put some todo comments around things I
# think might be issues.

from discord.ext import commands
import discord
import random

from helpers.style import Emotes, Colours
import helpers.charlatan_helpers as helper
from helpers.logger import Logger


logger = Logger()

CHARLATAN_VOTE_TIME = 20
PLAYER_VOTE_TIME = 20


class PlayerVoting(discord.ui.View):
    """ View that manages the voting of who the Charlatan is

    Args:
        players (dict[discord.User, int]): A mapping of players to their score
        channel (discord.TextChannel): The channel the game is to take place in
    """

    def __init__(self, players: dict[discord.User, int], channel: discord.TextChannel) -> None:
        logger.debug("New PlayerVoting view created")
        # {player: [player_voted_for, times_voted_for]}
        self.players = {player: [-1, 0] for player in players}
        self.channel = channel
        super().__init__(timeout=None)
        for i in range(0, len(self.players)):
            self.add_button(i)

    async def vote(self) -> discord.User:
        """Waits and then returns the most voted player

        Returns:
            discord.User: The most voted player
        """
        await helper.start_timer(PLAYER_VOTE_TIME)
        return sorted(self.players.items(), key=lambda x: x[1][1])[::-1][0][0]  # TODO handle ties

    def add_button(self, i: int) -> None:
        """ Adds voting buttons to the view

        Args:
            i (int): Button label and unique ID
        """
        button = discord.ui.Button(label=str(i + 1), custom_id=str(i))

        async def cast_vote(interaction: discord.Interaction):
            if self.players[interaction.user][0] != -1:
                # TODO the voted player should probably be part of the callback,
                # rather than relying on hackily storing data in the id

                # Reset the previous vote
                self.players[list(self.players)[self.players[interaction.user][0]]][1] -= 1
                self.players[interaction.user][0] = -1
            voted_player = list(self.players)[int(button.custom_id)]  # indexes into the dictionary
            self.players[voted_player][1] += 1
            self.players[interaction.user][0] += int(button.custom_id)  # TODO this cant be a good idea
            await interaction.response.send_message(ephemeral=True, content="You voted for {}"
                                                    .format(voted_player.display_name))

        button.callback = cast_vote
        self.add_item(button)


class WordSelection(discord.ui.Modal):
    """ Modal to choose a custom wordlist

    Args:
        title (str): Modal title
        users (dict[discord.User, int]): A dictionary mapping the current players to their score
    """

    def __init__(self, title: str, users: dict[discord.User, int]) -> None:
        logger.debug("New WordSelection modal created")
        super().__init__(title=title)
        self.add_item(discord.ui.InputText(label="Add 16 words for the game here:",
                                           style=discord.InputTextStyle.long,
                                           placeholder=helper.DEFAULT_WORDLIST[:97] + "..."))
        self.users = users

    async def callback(self, interaction: discord.Interaction) -> None:
        """ Changes interaction view to CharlatanLobby

        Edits the interaction message to use the CharlatanLobby view with the new wordlist

        Args:
            interaction (discord.Interaction): Interaction containing the message to change the view of
        """
        logger.debug("WordSelection complete, returning to lobby")
        view = CharlatanLobby(self.users, self.children[0].value.split('\n'))
        await interaction.message.edit(embed=helper.make_embed(self.users, "Charlatan"), view=view)


class CharlatanLobby(discord.ui.View):
    """ Pre-game lobby for the CharlatanGame

    Args:
        users (dict[discord.User, int]): Mapping of users to their score
        wordlist (list[str], optional): List of words to use for the game. Defaults to a wordlist of fantasy characters
    """

    def __init__(self, users: dict[discord.User, int],
                 wordlist: list[str] = helper.DEFAULT_WORDLIST.split("\n")) -> None:
        logger.debug("New CharlatanLobby view created")
        super().__init__(timeout=300)
        self.users = users
        self.wordlist = wordlist

    @ discord.ui.button(label="Word List", row=0, style=discord.ButtonStyle.secondary)
    async def wordlist_callback(self, _, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(WordSelection(title="Word List", users=self.users))

    @ discord.ui.button(label="Join", row=0, style=discord.ButtonStyle.primary)
    async def join_callback(self, _, interaction: discord.Interaction) -> None:
        logger.debug("New player joined game", member_id=interaction.user.id)
        self.users.update({interaction.user: 0})
        view = CharlatanLobby(self.users)
        await interaction.response.edit_message(embed=helper.make_embed(self.users, "Charlatan"), view=view)

    @ discord.ui.button(label="Rules", row=1, style=discord.ButtonStyle.secondary)
    async def rules_callback(self, _, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(ephemeral=True, embed=discord.Embed(description=helper.RULES))

    @ discord.ui.button(label="Confirm Lobby", row=1, style=discord.ButtonStyle.primary)
    async def start_callback(self, _, interaction: discord.Interaction) -> None:
        wordlist = self.wordlist[:16]
        await interaction.response.send_message(view=CharlatanGame(wordlist, self.users))
        await interaction.message.delete()


class CharlatanGame(discord.ui.View):
    def __init__(self, wordlist: list[str], players: dict[discord.User, int]):
        logger.debug("Created new CharlatanGame view")
        super().__init__(timeout=300)
        self.wordlist = wordlist
        self.players = players
        self.word = random.choice(self.wordlist)
        self.charlatan = random.choice(list(self.players.keys()))

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.primary)
    async def start_game(self, _, interaction: discord.Interaction):
        channel = interaction.channel
        interaction.response.defer()
        self.clear_items()
        await self.message.edit(
            embed=discord.Embed(description="Game is ongoing", title="Charlatan", colour=Colours.PRIMARY), view=self)
        await self.send_dms()
        await self.score_players(await self.vote(channel))
        await self.message.edit(embed=helper.make_embed(self.players, "Leaderboard"))
        await self.add_buttons()

    async def send_dms(self):
        """Send dms to players and charlatan displaying wordlist
        """
        info = "> This is the wordlist for this round:\n"
        words = "\n".join(["- " + i if (i is not self.word)
                          else "- **" + i + "** [SECRET WORD]" for i in self.wordlist])
        for key in self.players.keys():  # Sends the wordlist to everyone (altered for Charlatan)
            desc = info + (words if not key == self.charlatan else "\n".join(self.wordlist))
            title = "You are a normal player" if not key == self.charlatan else "You are the Charlatan"
            await key.send(embed=discord.Embed(title=title, description=desc, colour=Colours.PRIMARY))

    async def vote(self, channel: discord.TextChannel) -> discord.User:
        """Begins voting for the Charlatan

        Args:
            channel (discord.TextChannel): Channel to vote using

        Returns:
            discord.User: The most voted player
        """
        logger.debug("Begin player voting")
        view = PlayerVoting(self.players, channel)
        await self.message.edit(view=view, embed=discord.Embed(description="Vote for a Charlatan:\n" + "\n".join(
            [str(list(self.players)[i].mention) + ": " + str(i + 1) for i in range(0, len(self.players))]),
            title="Charlatan", colour=Colours.PRIMARY))
        self.clear_items()
        return await view.vote()

    async def score_players(self, voted_player: discord.User):
        """Handles voting results for players

        Args:
            voted_player (discord.User): The most voted player
            channel (discord.TextChannel): Channel to send result message to
        """
        if voted_player is not self.charlatan:
            logger.debug("Players incorrectly guessed charlatan")
            await self.message.edit(
                embed=discord.Embed(description="The players did not find the charlatan, it was {} {}"
                                    .format(self.charlatan.mention, Emotes.CRYING), title="Charlatan", colour=Colours.PRIMARY), view=self)
            self.players[self.charlatan] += 2
        else:
            logger.debug("Charlatan correctly guessed charlatan")
            await self.message.edit(
                embed=discord.Embed(description="The players have found the charlatan, it was {} {}"
                                    .format(self.charlatan.mention, Emotes.HUG), title="Charlatan", colour=Colours.PRIMARY), view=self)
            await self.charlatan_guess()

    async def charlatan_guess(self):
        """Handles scoring for the charlatan voting for the secret word.

        Sends a voting dm to the charlatan, and handles scoring and output messages for the result.
        Called if the Charlatan was discovered.

        Args:
            channel (discord.TextChannel): Channel to send result message to
        """
        logger.debug("Beginning charlatan voting")
        guess = CharlatanChoice(chosen_word=self.word, word_list=self.wordlist)
        await self.charlatan.send(view=guess)
        await helper.start_timer(CHARLATAN_VOTE_TIME)

        if guess.correctGuess:  # TODO no better way than accessing view property?
            logger.debug("Charlatan guessed correctly")
            await self.message.edit(embed=discord.Embed(description="\nThe Charlatan guessed the correct word {}"
                                    .format(Emotes.WHOA), title="Charlatan", colour=Colours.PRIMARY))
            self.players[self.charlatan] += 2
        else:
            logger.debug("Charlatan guessed incorrectly")
            await self.message.edit(embed=discord.Embed(description="\nThe Charlatan did not guess the correct word {}"
                                    .format(Emotes.CONFUSED), title="Charlatan", colour=Colours.PRIMARY))
            for key in self.players.keys():
                self.players[key] += 1 if key is not self.charlatan else 0

    async def add_buttons(self):
        """Adds Play Again and Back to Lobby buttons to the interaction message
        """
        self.clear_items()

        play_again_button = discord.ui.Button(label="Play Again", style=discord.ButtonStyle.primary)

        async def play_again(interaction: discord.Interaction):
            logger.debug("Play Again button selected")
            # TODO \/ send message, is edit more coherent (error in Startbutton messageedit)?
            view = CharlatanGame(wordlist=self.wordlist, players=self.players)
            view.message = await interaction.original_response()
            await interaction.response.edit_message(view=view)
            play_again_button.disabled = True  # TODO add lock
        play_again_button.callback = play_again
        self.add_item(play_again_button)
        logger.debug("Play Again button added to items")

        lobby_button = discord.ui.Button(label="Back to Lobby", style=discord.ButtonStyle.secondary)

        async def back_to_lobby(interaction: discord.Interaction):
            logger.debug("Return to Loby button selected")
            view = CharlatanLobby({interaction.user, 0})
            view.message = await interaction.original_response()  # TODO error(NotFound: Unknown Webhook 404)
            await interaction.response.edit_message(view=view)
            play_again_button.disabled = True  # TODO add lock
        lobby_button.callback = back_to_lobby
        self.add_item(lobby_button)
        logger.debug("Lobby button added to items")

        await self.message.edit(view=self)
        logger.debug("View was edited with Lobby and Play Again buttons")


class CharlatanChoice(discord.ui.View):
    """ A view that handles the Charlatan guessing the chosen word

    Args:
        chosen_word (str): The secret chosen word
        word_list (list[str]): The list of all words
    """

    def __init__(self, chosen_word: str, word_list: list[str]):
        logger.debug("Created new CharlatanChoice view")
        super().__init__(timeout=300)
        self.wordlist = word_list
        self.chosenword = chosen_word
        self.correctGuess = False
        for i in range(len(self.wordlist)):
            self.add_button(i, False if self.wordlist[i] is not self.chosenword else True)

    async def start_timer(self):
        """Start timer for charlatan to vote
        """
        await helper.start_timer(CHARLATAN_VOTE_TIME)

    def add_button(self, i: int, correct_button: bool) -> None:
        """Adds a button to the view

        Adds a button to the view representing a word in the wordlist, with a callback
        handling if the chosen word was the secret word.

        Args:
            i (int): The button ID, corresponding to its position in the wordlist
            correct_button (bool): Whether the word at postion 'i' is the secret word
        """
        button = discord.ui.Button(label=str(self.wordlist[i]),
                                   custom_id=str(i))

        async def word_guess(_):
            """Callback for the added button"""
            if correct_button:
                logger.debug("CharlatanChoice, correct button callback triggered")
                response = "You guessed the correct word good job. It was \"{}\" {}".format(
                    self.chosenword, Emotes.HUG)
                self.correctGuess = True
            else:
                logger.debug("CharlatanChoice, incorrect button callback triggered")
                response = "You did not guess the correct word. It was \"{}\" {}".format(
                    self.chosenword, Emotes.CRYING)
            self.children = [button]
            button.disabled = True
            await self.message.edit(content=response, view=self)
        button.callback = word_guess
        self.add_item(button)


class Charlatan(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(name='charlatan', description="Play a game of Charlatan")
    async def start_game(self, ctx: discord.ApplicationContext):
        logger.info("Starting Charlatan Game", guild_id=ctx.guild_id, channel_id=ctx.channel_id)
        await ctx.respond(embed=helper.make_embed({ctx.author: 0}, "Charlatan"),
                          view=CharlatanLobby({ctx.author: 0}))


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Charlatan(bot))
