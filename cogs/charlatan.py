from discord.ext import commands
from discord.partial_emoji import PartialEmoji
from functions.style import Emotes
import discord
from functions.style import Colours
import random
import asyncio

'''
#TODO-List:
-prep: players, choose word (own list or given list)
-start: chose word, chose random chameleon(write in DMs), write word to players(in DMs)
-during the game: counter(voting for chameleon), voting(chameleon votes word), timer
-after: score of games(?), replay possible(start again without preparation)
'''

DEFAULT_WORDLIST = """Indiana Jones\nDr Who\nSpiderman\nDarth Vader\nSherlock Holmes\nGandalf
Superman\nBatman\nJames Bond\nDracula\nHomer Simpson\nFrankenstein
Robin Hood\nSuper Mario\nTarzan\nDumbledore"""

RULES = """__Charlatan Rules__
Every player is given the same list of words with the same word marked, \
except the *Charlatan* who gets an unmarked list of words.

Each player takens it in turn to say a word related to the marked word \
(the *Charlatan* must try and guess a relevant word).

A small amount of discussion time is permitted to try and identify the *Charlatan*.

After discussion the players must vote on who they think is a *Charlatan*:
> - if they fail to eliminate the *Charlatan* they lose and the *Charlatan* scores 2pts.
> - if they eliminate the *Charlatan*, the *Charlatan* gets to guess the marked word. \
If the *Charlatan* is correct they get 1pt and the other players get zero
> - if they eliminate the *Charlatan* and the *Chalartan* incorrectly guesses the marked word,
the other players each get 1pt"""


class CharlatanGame(discord.ui.View):
    """ View that manages the playing of the Charlatan game

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

    def add_button(self, i: int) -> None:
        """ Adds voting buttons to the view

        Args:
            i (int): Button label and unique ID
        """
        button = discord.ui.Button(label=str(i), custom_id=i)

        async def cast_vote(interaction: discord.Interaction):
            if self.players[interaction.user][0] is False:
                self.players[list(self.players)[int(button.custom_id)]][1] += 1
                self.players[interaction.user][0] = True
            # TODO write a message when someone clicks on a second user
        button.callback = cast_vote
        self.add_item(button)

    async def start_timer(self, time: int) -> None:
        """ Waits until time is up

        Args:
            time (int): amount of time to wait in seconds
        """
        seconds = time
        # The entire function can be made static/standalone
        while True:
            seconds -= 1
            if seconds == 0:
                break
            await asyncio.sleep(1)

    def count_votes(self) -> discord.User:
        """Returns the player with the highest number of votes

        Returns:
            discord.User: The user with the highest number of votes
        """
        # TODO handle ties
        return sorted(self.players.items(), key=lambda x: x[1][1])[::-1][0]


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
                                           placeholder=DEFAULT_WORDLIST[:97] + "..."))
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

    def __init__(self, users: dict[discord.User, int], wordlist: list[str] = DEFAULT_WORDLIST.split("\n")) -> None:
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
        return discord.Embed(title="Charlatan", description=desc,
                             colour=Colours.PRIMARY)

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
        await interaction.response.send_message(ephemeral=True, embed=discord.Embed(description=RULES))

    @ discord.ui.button(label="Start Game", row=1, style=discord.ButtonStyle.primary)
    async def start_callback(self, _, interaction: discord.Interaction) -> None:
        """Callback to start the game via the CharlatenGame view"""
        # TODO none of this should be here, this should all be moved into a new function in CharlatanGame
        wordlist = self.wordlist[:16]  # For the case of the wordlist having more than 12 words
        view = CharlatanGameView(wordlist, self.users, interaction)
        await interaction.channel.send(content="game starting...", view=view)
        await interaction.message.delete()
        view.start()


class CharlatanGameView(discord.ui.View):
    def __init__(self, wordlist, players, interaction):
        self.wordlist = wordlist
        self.players = players
        self.interaction = interaction

    async def start(self):
        self.interaction.channel.send(content="A game is ongoing")
        word = random.choice(self.wordlist)
        charlatan = random.choice(list(self.players.keys()))
        words = "\n".join([i if (i is not word) else "**" + i + "**" for i in self.wordlist]
                          )  # Writes the words as a list and marks the chosen one
        for key in self.players.keys():  # Sends the wordlist to everyone (altered for Charlatan)
            await key.send(words) if not key == charlatan else \
                await key.send("You are the charlatan: \n" + "\n".join(self.wordlist))
        view = CharlatanGame(self.players, self.interaction.channel)
        message = await self.interaction.channel.send(content="game starting...", view=view)
        message = await message.edit(content="Vote for a Charlatan:\n" + "\n".join(
            [str(list(self.players)[i].mention) + ": " + str(i) for i in range(0, len(self.players))]))
        await CharlatanGame.start_timer(10)
        correct_voting = self.check_voting_results()  # Checks if the vote was the Charlatan or not
        self.post_voting(correct_voting, charlatan, word)

    async def post_voting(self, correctVote, charlatan, word):
        if not correctVote:
            self.interaction.channel.send(
                content="You did not find the charlatan, it was {}".format(charlatan.mention))
            self.players[charlatan] += 2
        else:
            view = CharlatanChoice(chosenword=word, wordlist=self.wordlist)
            await CharlatanGame.start_timer(20)
            if view.correctGuess():
                self.players[charlatan] += 1
            else:
                for player in self.players.keys():
                    self.players[player] += 1 if player is not charlatan else None

    async def check_voting_results(self, view: CharlatanGame, charlatan) -> bool:
        voted_player = view.count_votes()
        if voted_player is charlatan:
            return True
        else:
            return False


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
                                   custom_id=i)

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
