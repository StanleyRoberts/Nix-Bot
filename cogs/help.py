import discord
from discord.ext import commands
from functions.style import Colours
from discord.ui import Button, View


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='testing', description="just testing")
    async def button(self, ctx):
        await ctx.respond("Look at this button", view=BackwardButton())

    @commands.slash_command(name='help', description="Displays the help page for NixBot")
    async def display_help(self, ctx):
        desc = "Note: depending on your server settings and role permissions," + \
            " some of these commands may be hidden or disabled\n\n***Generic***\n" \
            + "".join(sorted([command.mention + " : " + command.description + "\n"
                             for command in self.bot.walk_application_commands() if not command.cog])) \
            + "".join(["\n***" + cog + "***\n" + "".join(sorted([command.mention + " : " + command.description + "\n"
                                                                for command in self.bot.cogs[cog].walk_commands()]))
                      for cog in self.bot.cogs])  # Holy hell
        embed = discord.Embed(title="Help Page", description=desc,
                              colour=Colours.PRIMARY)
        await ctx.respond(embed=embed)

    @commands.slash_command(name='testinghelp', description="Testing for a better help function")
    async def helper_embed(self, ctx):
        desc = "Note: depending on your server settings and role permissions," + \
            " some of these commands may be hidden or disabled\n\n***Generic***\n" \
            + "".join(sorted([command.mention + " : " + command.description + "\n"
                             for command in self.bot.walk_application_commands() if not command.cog]))
        embed = discord.Embed(title="Help Page", description=desc,
                              colour=Colours.PRIMARY)
        await ctx.respond(embed=embed)
        await (await self.bot.fetch_channel(ctx.channel.id)).send(view=BackwardButton())


class BackwardButton(discord.ui.View):
    @discord.ui.button(label="Backwards", style=discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        await interaction.embed.add_field(name="testing", value="Hello this is a testing text", inline=True)

    @discord.ui.button(label="Forwards", style=discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        await interaction.embed.add_field(name="testing", value="Hello this is a testing text", inline=True)


def setup(bot):
    bot.add_cog(Help(bot))
