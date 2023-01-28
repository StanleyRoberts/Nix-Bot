from discord.ext import commands
from discord.partial_emoji import PartialEmoji
from functions.style import Emotes
import discord
from functions.style import Colours

'''
#TODO-List:
-prep: players, choose word (own list or given list)
-start: chose word, chose random chameleon(write in DMs), write word to players(in DMs)
-during the game: counter(voting for chameleon), voting(chameleon votes word), timer
-after: score of games(?), replay possible(start again without preparation)
'''

DEFAULT_WORDLIST = "Indiana Jones\nDr Who\nSpiderman\nDarth Vader\nSherlock Holmes\nGandalf"
"\nSuperman\nBatman\nJames Bond\nDracula\nHomer Simpson\nFrankenstein"
"\nRobin Hood\nSuper Mario\nTarzan\nDumbledore"


class Charlatan(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(name='charlatan', description="Play a game of Charlatan")
    async def start_game(self, ctx: discord.ApplicationContext):
        user = ctx.author.mention
        view = CharlatanView(set([user]))
        await ctx.respond(embed=view.make_embed(), view=view)


class WordList(discord.ui.Modal):
    def __init__(self, title, users):
        super().__init__(title=title)
        self.add_item(discord.ui.InputText(label="Add words for game here:",
                                           style=discord.InputTextStyle.long,
                                           placeholder=DEFAULT_WORDLIST))
        self.users = users

    async def callback(self, interaction):
        view = CharlatanView(set(self.users), self.children[0].value.split('\n'))
        await interaction.message.edit(embed=view.make_embed(), view=view)


class CharlatanView(discord.ui.View):
    def __init__(self, users, wordlist=DEFAULT_WORDLIST):
        super().__init__(timeout=300)
        self.users = users
        self.wordlist = wordlist

    def make_embed(self):
        desc = "Playing right now: \n{}".format("\n".join(self.users))
        return discord.Embed(title="Charlatan", description=desc,
                             colour=Colours.PRIMARY)

    @discord.ui.button(label="Word List", row=0, style=discord.ButtonStyle.secondary)
    async def wordlist_callback(self, _, interaction):
        await interaction.response.send_modal(WordList(title="Word List", users=self.users))

    @discord.ui.button(label="Join", row=0, style=discord.ButtonStyle.primary)
    async def join_callback(self, _, interaction: discord.Interaction) -> None:
        self.users.add(interaction.user.mention)
        view = CharlatanView(self.users)
        await interaction.response.edit_message(embed=view.make_embed(), view=view)

    @discord.ui.button(label="Rules", row=1, style=discord.ButtonStyle.secondary)
    async def rules_callback(self, _, interaction: discord.Interaction) -> None:
        return

    @discord.ui.button(label="Start Game", row=1, style=discord.ButtonStyle.primary)
    async def start_callback(self, _, interaction):
        return


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Charlatan(bot))
