from discord.ext import commands
import requests


class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='quote',
                            description="Displays an AI-generated quote over an inspirational image")
    async def send_quote(self, ctx):
        await ctx.respond(requests.get("https://inspirobot.me/api?generate=true").text)


def setup(bot):
    bot.add_cog(Misc(bot))
