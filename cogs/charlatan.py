from discord.ext import commands
from discord.partial_emoji import PartialEmoji
from functions.style import Emotes
import discord
from functions.style import Colours
import random
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

RULE_EXPLANATION = """ ```__Charlatan Rules__
Every player is given the same list of words with the same word marked, except the *Charlatan* who gets an unmarked list of words.

Each player takens it in turn to say a word related to the marked word (the *Charlatan* must try and guess a relevant word).

A small amount of discussion time is permitted to try and identify the *Charlatan*.

After discussion the players must vote on who they think is a *Charlatan*:
- if they fail to eliminate the *Charlatan* they lose and the *Charlatan* scores 2pts.
- if they eliminate the *Charlatan*, the *Charlatan* gets to guess the marked word. If they are correct the *Charlatan* gets 1pt and the other players get zero
- if they eliminate the *Charlatan* and the *Chalartan* incorrectly guesses the marked word, the other players each get 1pt``` """


class Charlatan(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(name='charlatan', description="Play a game of Charlatan")
    async def start_game(self, ctx: discord.ApplicationContext):
        user = ctx.author
        view = CharlatanView(set([user]))
        await ctx.respond(embed=view.make_embed(), view=view)


class WordList(discord.ui.Modal):
    def __init__(self, title, users):
        super().__init__(title=title)
        self.add_item(discord.ui.InputText(label="Add 12 words for game here:",
                                           style=discord.InputTextStyle.long,
                                           placeholder=DEFAULT_WORDLIST))
        self.users = users

    async def callback(self, interaction):
        view = CharlatanView(set(self.users), self.children[0].value.split('\n'))
        await interaction.message.edit(embed=view.make_embed(), view=view)


class CharlatanView(discord.ui.View):
    def __init__(self, users, wordlist=DEFAULT_WORDLIST.split("\n")):
        super().__init__(timeout=300)
        self.users = users
        self.wordlist = wordlist

    def make_embed(self):
        desc = "Playing right now: \n{}".format("\n".join([user.mention for user in self.users]))
        return discord.Embed(title="Charlatan", description=desc,
                             colour=Colours.PRIMARY)

    @discord.ui.button(label="Word List", row=0, style=discord.ButtonStyle.secondary)
    async def wordlist_callback(self, _, interaction):
        await interaction.response.send_modal(WordList(title="Word List", users=self.users))

    @discord.ui.button(label="Join", row=0, style=discord.ButtonStyle.primary)
    async def join_callback(self, _, interaction: discord.Interaction) -> None:
        self.users.add(interaction.user)
        view = CharlatanView(self.users)
        await interaction.response.edit_message(embed=view.make_embed(), view=view)

    @discord.ui.button(label="Rules", row=1, style=discord.ButtonStyle.secondary)
    async def rules_callback(self, _, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(ephemeral=True, content=RULE_EXPLANATION)

    @discord.ui.button(label="Start Game", row=1, style=discord.ButtonStyle.primary)
    async def start_callback(self, _, interaction: discord.Interaction):
        await interaction.response.defer()
        wordlist = self.wordlist[:12]  # For the case of the wordlist having more than 12 words
        word = random.choice(wordlist)
        charlatan = random.choice(list(self.users))
        words = "\n".join([i if (i is not word) else "**" + i + "**" for i in wordlist])
        for user in list(self.users):
            await user.send(words) if not user == charlatan else await user.send("You are the charlatan: \n" + "\n".join(wordlist))


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Charlatan(bot))
