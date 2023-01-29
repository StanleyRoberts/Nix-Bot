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
Every player is given the same list of words with the same word marked, except the *Charlatan* who gets an unmarked list of words.

Each player takens it in turn to say a word related to the marked word (the *Charlatan* must try and guess a relevant word).

A small amount of discussion time is permitted to try and identify the *Charlatan*.

After discussion the players must vote on who they think is a *Charlatan*:
> - if they fail to eliminate the *Charlatan* they lose and the *Charlatan* scores 2pts.
> - if they eliminate the *Charlatan*, the *Charlatan* gets to guess the marked word. If the *Charlatan* is correct they get 1pt and the other players get zero
> - if they eliminate the *Charlatan* and the *Chalartan* incorrectly guesses the marked word,
the other players each get 1pt"""


class Charlatan(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(name='charlatan', description="Play a game of Charlatan")
    async def start_game(self, ctx: discord.ApplicationContext):
        user = ctx.author
        view = CharlatanLobby({user: 0})
        await ctx.respond(embed=view.make_embed(), view=view)


class CharlatanGame(discord.ui.View):
    def __init__(self, players, channel):
        # {player: [has_voted, times_voted_for]}
        self.players = {player: [False, 0] for player in players}
        self.channel = channel
        super().__init__(timeout=None)
        for i in range(0, len(self.players)):
            self.add_button(i)

    def add_button(self, i):
        button = discord.ui.Button(label=i)
        button.custom_id = str(i)

        async def cast_vote(interaction: discord.Interaction):
            if self.players[interaction.user][0] is False:
                self.players[list(self.players)[int(button.custom_id)]][1] += 1
                self.players[interaction.user][0] = True
        button.callback = cast_vote
        self.add_item(button)

    async def start_timer(self, message):
        seconds = 5
        message = await message.edit(content="Vote for a Charlatan:\n" + "\n".join(
            [str(list(self.players)[i].mention) + ": " + str(i) for i in range(0, len(self.players))]))
        while True:
            seconds -= 1
            if seconds == 0:
                print(self.players)
                break
            await asyncio.sleep(1)


class WordSelection(discord.ui.Modal):
    def __init__(self, title, users):
        super().__init__(title=title)
        self.add_item(discord.ui.InputText(label="Add 12 words for game here:",
                                           style=discord.InputTextStyle.long,
                                           placeholder=DEFAULT_WORDLIST[:97] + "..."))
        self.users = users

    async def callback(self, interaction):
        view = CharlatanLobby({self.users: 0}, self.children[0].value.split('\n'))
        await interaction.message.edit(embed=view.make_embed(), view=view)


class CharlatanLobby(discord.ui.View):
    def __init__(self, users, wordlist=DEFAULT_WORDLIST.split("\n")):
        super().__init__(timeout=300)
        self.users = users
        self.wordlist = wordlist

    def make_embed(self):
        print(self.users)
        desc = "Playing now:\n " + "\n".join(str(key.mention) + " : " + str(
            self.users[key]) for key in self.users.keys())
        return discord.Embed(title="Charlatan", description=desc,
                             colour=Colours.PRIMARY)

    @ discord.ui.button(label="Word List", row=0, style=discord.ButtonStyle.secondary)
    async def wordlist_callback(self, _, interaction):
        await interaction.response.send_modal(WordSelection(title="Word List", users=self.users))

    @ discord.ui.button(label="Join", row=0, style=discord.ButtonStyle.primary)
    async def join_callback(self, _, interaction: discord.Interaction) -> None:
        self.users.update({interaction.user: 0})
        view = CharlatanLobby(self.users)
        await interaction.response.edit_message(embed=view.make_embed(), view=view)

    @ discord.ui.button(label="Rules", row=1, style=discord.ButtonStyle.secondary)
    async def rules_callback(self, _, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(ephemeral=True, embed=discord.Embed(description=RULES))

    @ discord.ui.button(label="Start Game", row=1, style=discord.ButtonStyle.primary)
    async def start_callback(self, _, interaction: discord.Interaction):
        wordlist = self.wordlist[:12]  # For the case of the wordlist having more than 12 words
        word = random.choice(wordlist)
        charlatan = random.choice(list(self.users.keys()))
        words = "\n".join([i if (i is not word) else "**" + i + "**" for i in wordlist])
        for key in self.users.keys():
            await key.send(words) if not key == charlatan else \
                await key.send("You are the charlatan: \n" + "\n".join(wordlist))

        view = CharlatanGame(self.users, interaction.channel)
        message = await interaction.channel.send(content="game starting...", view=view)
        await view.start_timer(message)
        await interaction.message.delete()


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Charlatan(bot))
