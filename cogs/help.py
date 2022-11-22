import discord
from discord.ext import commands
from functions.style import Colours
from discord.ui import Button, View


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='testing', description="just testing")
    async def button(self, ctx):
        await ctx.respond("Look at this button", view=Buttons())

    @commands.slash_command(name='help', description="Displays the help page for NixBot")
    async def display_help(self, ctx):
        desc = "Note: depending on your server settings and role permissions," + \
            " some of these commands may be hidden or disabled\n\n" \
            + "".join(["\n***" + cog + "***\n" + "".join(sorted([command.mention + " : " + command.description + "\n"
                                                                for command in self.bot.cogs[cog].walk_commands()]))
                      for cog in self.bot.cogs])  # Holy hell
        embed = discord.Embed(title="Help Page", description=desc,
                              colour=Colours.PRIMARY)
        await ctx.respond(embed=embed)

    @commands.slash_command(name='testinghelp', description="Testing for a better help function")
    async def helper_embed(self, ctx):
        desc = "Note: depending on your server settings and role permissions," + \
            " some of these commands may be hidden or disabled\n\n" \
            + "".join(sorted([command.mention + " : " + command.description + "\n"
                             for command in self.bot.walk_application_commands() if not command.cog]))
        embeted = discord.Embed(title="Help Page", description=desc,
                                colour=Colours.PRIMARY)
        await ctx.interaction.response.send_message(embed=embeted, view=Buttons(self.bot.cogs))


class Buttons(discord.ui.View):
    def __init__(self, cogs):
        super().__init__()
        self.index = 0
        self.cogs = [cogs[cog] for cog in cogs]

    @discord.ui.button(label="Backwards", style=discord.ButtonStyle.primary)
    async def backward_Callback(self, _, interaction):
        if (self.index - 1 < 0):
            self.index = len(self.cogs)
        self.index -= 1
        cog = self.cogs[self.index]
        desc = await self.helpermessage_view(cog)
        embeted = discord.Embed(title="Help Page", description=desc,
                                colour=Colours.PRIMARY)
        await interaction.response.edit_message(embed=embeted)

    @discord.ui.button(label="Frontpage", style=discord.ButtonStyle.primary)
    async def home_callback(self, _, interaction):
        desc = "Note: depending on your server settings and role permissions," \
            + " some of these commands may be hidden or disabled"
        self.index = 0
        embeted = discord.Embed(title="Help Page", description=desc,
                                colour=Colours.PRIMARY)
        await interaction.response.edit_message(embed=embeted)

    @discord.ui.button(label="Forwards", style=discord.ButtonStyle.primary)
    async def forward_Callback(self, _, interaction):
        if (self.index + 1 == len(self.cogs)):
            self.index = -1
        self.index += 1
        cog = self.cogs[self.index]
        desc = await self.helpermessage_view(cog)
        embeted = discord.Embed(title="Help Page", description=desc,
                                colour=Colours.PRIMARY)
        await interaction.response.edit_message(embed=embeted)

    async def helpermessage_view(self, cog):
        text = "".join("\n***" + cog.qualified_name + "***:\n" + ""
                       .join(sorted([command.mention + " : " + command.description + "\n"
                                     for command in cog.walk_commands()])))
        return text


def setup(bot):
    bot.add_cog(Help(bot))
