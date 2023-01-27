from discord.ext import commands
import discord

'''
#TODO-List:
-prep: players, choose word (own list or given list)
-start: chose word, chose random chameleon(write in DMs), write word to players(in DMs)
-during the game: counter(voting for chameleon), voting(chameleon votes word), timer
-after: score of games(?), replay possible(start again without preparation)
'''


class Charlatan(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(name='Charlatan', description="Play a game of Charlatan")
    def start_game(self, ctx):
        return


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Charlatan(bot))
