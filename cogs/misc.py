from discord.ext import commands
import discord
import requests


class Misc(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(name='quote', description="Displays an AI-generated quote over an inspirational image")
    async def send_quote(self, ctx: discord.ApplicationContext) -> None:
        await ctx.respond(requests.get("https://inspirobot.me/api?generate=true").text)


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Misc(bot))
