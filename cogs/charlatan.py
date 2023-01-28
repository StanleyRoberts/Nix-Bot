from discord.ext import commands
from discord.partial_emoji import PartialEmoji
from functions.style import Emotes
import discord

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

    @ commands.slash_command(name='charlatan', description="Play a game of Charlatan")
    async def start_game(self, ctx):
        await ctx.interaction.response.send_message(view=CharlatanView())


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Charlatan(bot))
