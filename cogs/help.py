import discord
from discord.ext import commands
from functions.style import Colours
from discord.ui import Button, View


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='testing', description="just testing")
    async def button(self, ctx):
        await ctx.respond("Look at this button", view=MyView())

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


class MyView(discord.ui.View):
    @discord.ui.button(label="Click me!", style=discord.ButtonStyle.primary)
    async def button_callback(self, button, interaction):
        await interaction.response.send_message("You clicked the button!")


def setup(bot):
    bot.add_cog(Help(bot))
