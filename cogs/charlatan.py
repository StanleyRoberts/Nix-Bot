from discord.ext import commands
from discord.partial_emoji import PartialEmoji
from functions.style import Emotes, Colours
import discord
import random
import functions.charlatan_helpers as helper
'''
#TODO-List:
-prep: players, choose word (own list or given list)
-start: chose word, chose random chameleon(write in DMs), write word to players(in DMs)
-during the game: counter(voting for chameleon), voting(chameleon votes word), timer
-after: score of games(?), replay possible(start again without preparation)
'''


class PlayerVoting(discord.ui.View):
    """ View that manages the voting of who the Charlatan is

    Args:
        players (dict[discord.User, int]): A mapping of players to their score
        channel (discord.TextChannel): The channel the game is to take place in
    """

    def __init__(self, players: dict[discord.User, int], channel: discord.TextChannel) -> None:
        # {player: [has_voted, times_voted_for]}
        self.players = {player: [False, 0] for player in players}
        self.channel = channel
        super().__init__(timeout=None)
        for i in range(0, len(self.players)):
            self.add_button(i)

    async def vote(self) -> discord.User:
        """Waits and then returns the most voted player

        Returns:
            discord.User: The most voted player
        """
        return sorted(self.players.items(), key=lambda x: x[1][1])[::-1][0][0]  # TODO handle ties

    def add_button(self, i: int) -> None:
        """ Adds voting buttons to the view

        Args:
            i (int): Button label and unique ID
        """
        button = discord.ui.Button(label=str(i + 1), custom_id=str(i))

        async def cast_vote(interaction: discord.Interaction):
            if self.players[interaction.user][0] is False:
                voted_player = list(self.players)[int(button.custom_id)]  # indexes into the dictionary
                self.players[voted_player][1] += 1
                self.players[interaction.user][0] = True
                await interaction.response.send_message(ephemeral=True, content="You voted for {}".format(voted_player.display_name))
            # TODO write a message when someone clicks on a second user
        button.callback = cast_vote
        self.add_item(button)


class WordSelection(discord.ui.Modal):
    """ Modal to choose a custom wordlist


    Args:
            title (str): Modal title
            users (dict[discord.User, int]): A dictionary mapping the current players to their score
    """

    def __init__(self, title: str, users: dict[discord.User, int]) -> None:
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
        view = CharlatanLobby(self.users, self.children[0].value.split('\n'))
        await interaction.message.edit(embed=view.make_embed(), view=view)


class CharlatanLobby(discord.ui.View):
    """ Pre-game lobby for the CharlatanGame

    Args:
        users (dict[discord.User, int]): Mapping of users to their score
        wordlist (list[str], optional): List of words to use for the game. Defaults to a wordlist of fantasy characters
    """

    def __init__(self, users: dict[discord.User, int],
                 wordlist: list[str] = helper.DEFAULT_WORDLIST.split("\n")) -> None:
        super().__init__(timeout=300)
        self.users = users
        self.wordlist = wordlist

    def make_embed(self) -> discord.Embed:
        """Constructs an embed showing the current players in the lobby

        Returns:
            discord.Embed: The constructed embed
        """
        desc = "Playing now:\n " + "\n".join(str(key.mention) + " : " + str(
            self.users[key]) for key in self.users.keys())
        self.embed = discord.Embed(title="Charlatan", description=desc,
                                   colour=Colours.PRIMARY)
        return self.embed

    @ discord.ui.button(label="Word List", row=0, style=discord.ButtonStyle.secondary)
    async def wordlist_callback(self, _, interaction: discord.Interaction) -> None:
        """Callback to send the WordSelection modal view"""
        await interaction.response.send_modal(WordSelection(title="Word List", users=self.users))

    @ discord.ui.button(label="Join", row=0, style=discord.ButtonStyle.primary)
    async def join_callback(self, _, interaction: discord.Interaction) -> None:
        """Callback to join the lobby"""
        self.users.update({interaction.user: 0})
        view = CharlatanLobby(self.users)
        await interaction.response.edit_message(embed=view.make_embed(), view=view)

    @ discord.ui.button(label="Rules", row=1, style=discord.ButtonStyle.secondary)
    async def rules_callback(self, _, interaction: discord.Interaction) -> None:
        """Callback to display the rules"""
        await interaction.response.send_message(ephemeral=True, embed=discord.Embed(description=helper.RULES))

    @ discord.ui.button(label="Confirm Lobby", row=1, style=discord.ButtonStyle.primary)
    async def start_callback(self, _, interaction: discord.Interaction) -> None:
        """Callback to start the game via the CharlatenGame view"""
        wordlist = self.wordlist[:16]  # For the case of the wordlist having more than 16 words
        view = CharlatanGame(wordlist, self.users)
        await interaction.response.send_message(view=view)
        await interaction.message.delete()


class CharlatanGame(discord.ui.View):
    def __init__(self, wordlist: list[str], players: dict[discord.User, int]):
        super().__init__(timeout=300)
        self.wordlist = wordlist
        self.players = players
        self.word = random.choice(self.wordlist)
        self.charlatan = random.choice(list(self.players.keys()))

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.primary)
    async def start_game(self, _, interaction: discord.Interaction):
        self.interaction = interaction
        self.disable_all_items()
        await self.message.edit(view=self)
        await self.send_messages()
        await helper.start_timer(20)
        await self.post_voting(await self.voting())

    async def send_messages(self):
        words = "\n".join([i if (i is not self.word) else "**" + i + "**" for i in self.wordlist]
                          )  # Writes the words as a list and marks the chosen one
        for key in self.players.keys():  # Sends the wordlist to everyone (altered for Charlatan)
            desc = words if not key == self.charlatan else "\n".join(self.wordlist)
            title = "You are a normal player" if not key == self.charlatan else "You are the Charlatan"
            await key.send(embed=discord.Embed(title=title, description=desc, colour=Colours.PRIMARY))

    async def voting(self) -> discord.User:
        """Voting for the Charlatan

        Returns:
            discord.User: The most voted player
        """
        view = PlayerVoting(self.players, self.interaction.channel)
        message = await self.interaction.channel.send(content="game starting...", view=view)
        message = await message.edit(content="Vote for a Charlatan:\n" + "\n".join(
            [str(list(self.players)[i].mention) + ": " + str(i + 1) for i in range(0, len(self.players))]))
        await helper.start_timer(20)
        await message.delete()
        return await view.vote()

    async def post_voting(self, votedplayer: discord.User):
        """Handles voting results

        Args:
            correctVote (bool): If the players have voted the correct person
            votedplayer (discord.User): The most voted player
        """
        if votedplayer is not self.charlatan:
            await self.interaction.channel.send(
                content="The players did not find the charlatan, it was {} {}".format(self.charlatan.mention, Emotes.CRYING))
            self.players[self.charlatan] += 2
        else:
            view = CharlatanChoice(chosenword=self.word, wordlist=self.wordlist)
            await self.charlatan.send(view=view)
            await self.interaction.channel.send(content="The players have found the charlatan, it was {} {}".format(self.charlatan.mention, Emotes.HUG))
            await helper.start_timer(20)
            if view.correctGuess:
                await self.interaction.channel.send(content="The Charlatan guessed the correct word {}".format(Emotes.WHOA))
                self.players[self.charlatan] += 1
            else:
                await self.interaction.channel.send(content="The Charlatan did not guess the correct word {}".format(Emotes.CONFUSED))
                for key in self.players.keys():
                    self.players[key] += 1 if key is not self.charlatan else 0
        self.clear_items()
        desc = "\n".join(str(key.mention) + " : " + str(self.players[key]) for key in self.players.keys())
        embed = (discord.Embed(title="Leaderboard", description=desc, colour=Colours.PRIMARY))
        play_again_button = discord.ui.Button(label="Play again", style=discord.ButtonStyle.primary)
        play_again_button.callback = self.play_again
        lobby_button = discord.ui.Button(label="Back to the lobby", style=discord.ButtonStyle.secondary)
        lobby_button.callback = self.back_to_lobby
        self.add_item(play_again_button)
        self.add_item(lobby_button)
        await self.interaction.channel.send(embed=embed, view=self)

    async def play_again(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=CharlatanGame(wordlist=self.wordlist, players=self.players))

    async def back_to_lobby(self, interaction: discord.Interaction):
        await interaction.response.send_message(view=CharlatanLobby({}))


class CharlatanChoice(discord.ui.View):
    """ A view that handles the Charlatan guessing the chosen word

    Args:
        chosenword (str): The secret chosen word
        wordlist (list[str]): The list of all words
    """

    def __init__(self, chosenword: str, wordlist: list[str]):
        super().__init__(timeout=300)
        self.wordlist = wordlist
        self.chosenword = chosenword
        self.correctGuess = False
        for i in range(0, len(self.wordlist)):
            self.add_button(i, False if self.wordlist[i] is not self.chosenword else True)

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
                response = "You guessed the correct word good job. It was \"{}\" {}".format(
                    self.chosenword, Emotes.HUG)
                self.correctGuess = True
            else:
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
        user = ctx.author
        view = CharlatanLobby({user: 0})
        await ctx.respond(embed=view.make_embed(), view=view)


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Charlatan(bot))
