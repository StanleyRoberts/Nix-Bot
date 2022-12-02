import discord
from discord.ext import commands
from functions.style import Colours
import typing


class Help(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.slash_command(name='all_commands', description="Displays the help page for NixBot")
    async def display_help(self, ctx: discord.ApplicationContext) -> None:
        desc = "Note: depending on your server settings and role permissions," +\
            " some of these commands may be hidden or disabled\n\n" +\
            "".join(["\n***" + cog + "***\n" + "".join(sorted([command.mention + " : " + command.description + "\n"
                                                               for command in self.bot.cogs[cog].walk_commands()]))
                     for cog in self.bot.cogs])  # Holy hell
        embed = discord.Embed(title="Help Page", description=desc,
                              colour=Colours.PRIMARY)
        await ctx.respond(embed=embed)

    @commands.slash_command(name='help', description="Testing for a better help function")
    async def helper_embed(self, ctx: discord.ApplicationContext) -> None:
        view = Buttons(self.bot.cogs)
        await ctx.interaction.response.send_message(embed=view.build_embed(), view=view)


class Buttons(discord.ui.View):
    def __init__(self, cogs: typing.Mapping[str, discord.Cog]) -> None:
        super().__init__()
        self.index = 0
        self.pages = ["Front"] + [cogs[cog] for cog in cogs]

    def build_embed(self):
        self.index = self.index % len(self.pages)
        page = self.pages[self.index]

        compass = "|".join([" {0} ".format(page.qualified_name) if page != self.pages[self.index]
                            else "** {0} **".format(page.qualified_name) for page in self.pages[1:]]) + "\n"
        if page == "Front":
            desc = compass + "\nNote: depending on your server settings and role permissions, " +\
                "some of these commands may be hidden or disabled"
        else:
            desc = compass + "".join("\n***" + page.qualified_name + "***:\n" + ""
                                     .join(sorted([command.mention + " : " + command.description + "\n"
                                                   for command in page.walk_commands()])))

        return discord.Embed(title="Help Page", description=desc,
                             colour=Colours.PRIMARY)

    @discord.ui.button(label="<-", style=discord.ButtonStyle.primary)
    async def backward_callback(self, _, interaction: discord.Interaction) -> None:
        self.index -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="->", style=discord.ButtonStyle.primary)
    async def forward_callback(self, _, interaction: discord.Interaction) -> None:
        self.index += 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Help(bot))
