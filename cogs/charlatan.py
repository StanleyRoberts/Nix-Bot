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


class WordList(discord.ui.Modal):
    def __init__(self, title):
        super().__init__(title=title)
        self.add_item(discord.ui.InputText(label="Add words for game here:",
                                           style=discord.InputTextStyle.long,
                      placeholder="London\nParis\nBerlin\nStockholm\nNew York\nCanberra"))

    async def callback(self, interaction):
        word_list = self.children[0].value.split('\n')
        await interaction.message.edit(content=word_list)


class CharlatanView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Word List", style=discord.ButtonStyle.secondary)
    async def callback(self, _, interaction):
        await interaction.response.send_modal(WordList(title="Word List"))

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.primary)
    async def callback(self, _, interaction):
        await interaction.response()


class Charlatan(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(name='charlatan', description="Play a game of Charlatan")
    async def start_game(self, ctx: discord.ApplicationContext):
        user = ctx.author.mention
        await ctx.respond(embed=CharlatanView.make_embed([user]), view=CharlatanView([user]))


class CharlatanView(discord.ui.View):

    def __init__(self, users):
        super().__init__(timeout=300)
        self.users = users

    @staticmethod
    def make_embed(users):
        desc = "Playing right now: \n{}".format("\n".join(users))
        return discord.Embed(title="Charlatan", description=desc,
                             colour=Colours.PRIMARY)

    @discord.ui.button(label="join", style=discord.ButtonStyle.primary)
    async def join_button(self, _, interaction: discord.Interaction) -> None:
        self.users.append(interaction.user.mention)
        await interaction.response.edit_message(embed=self.make_embed(self.users), view=CharlatanView(self.users))

    @discord.ui.button(label="rules", style=discord.ButtonStyle.primary)
    async def rules(self, _, interaction: discord.Interaction) -> None:
        return


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Charlatan(bot))
