from discord.ext import commands
import discord
import requests
import typing
import re
import aiohttp

from helpers.style import Colours
from helpers.logger import Logger
from helpers.style import Emotes

logger = Logger()


class Misc(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.slash_command(name='quote', description="Displays an AI-generated quote over an inspirational image")
    async def send_quote(self, ctx: discord.ApplicationContext) -> None:
        await ctx.respond(requests.get("https://inspirobot.me/api?generate=true").text)
        logger.info("Generating quote", member_id=ctx.author.id, channel_id=ctx.channel_id)

    @commands.slash_command(name='all_commands', description="Displays all of Nix's commands")
    async def display_help(self, ctx: discord.ApplicationContext) -> None:
        desc = "Note: depending on your server settings and role permissions," +\
            " some of these commands may be hidden or disabled\n\n" +\
            "".join(["\n***" + cog + "***\n" + "".join(sorted([command.mention + " : " + command.description + "\n"
                                                               for command in self.bot.cogs[cog].walk_commands()]))
                     for cog in self.bot.cogs])  # Holy hell
        embed = discord.Embed(title="Help Page", description=desc,
                              colour=Colours.PRIMARY)
        await ctx.respond(embed=embed)
        logger.info("Displaying long help", member_id=ctx.author.id, channel_id=ctx.channel_id)

    @commands.slash_command(name='help', description="Display the help page for Nix")
    async def helper_embed(self, ctx: discord.ApplicationContext) -> None:
        view = Help_Nav(self.bot.cogs)
        await ctx.interaction.response.send_message(embed=view.build_embed(),
                                                    view=view)
        logger.info("Displaying short help", member_id=ctx.author.id, channel_id=ctx.channel_id)

    @commands.Cog.listener("on_message")
    async def NLP(self, msg: discord.Message):
        """
        Prints out an AI generated response to the message if it mentions Nix

        Args:
            msg (discord.Message): Message that triggered event
        """
        if self.bot.user.mentioned_in(msg):
            logger.info("Generating AI response", member_id=msg.author.id, channel_id=msg.channel.id)
            clean_prompt = re.sub(" @", " ",
                                  re.sub("@" + self.bot.user.name, "", msg.clean_content))

            history = []
            inspect = msg
            is_answer = False
            while inspect.reference is not None:
                inspect = self.bot.get_message(inspect.reference.message_id)
                if is_answer:
                    history.append({"role": "user", "content": re.sub(
                        " @", " ", re.sub("@" + self.bot.user.name, "", inspect.clean_content))})
                else:
                    history.append({"role": "assistant", "content": inspect.clean_content})
                is_answer = not is_answer
            history = [{"role": "system", "content": "You are Nix, a friendly and kind phoenix."}] + history[::-1]
            history.append({"role": "user", "content": clean_prompt})

            logger.debug("Generating response with following message history: " + str(history))

            async with aiohttp.ClientSession() as session:
                headers = {'Content-Type': "application/json"}
                json = {
                    "model": "gpt-3.5-turbo",
                    "messages": history
                }
                async with session.post("https://chatgpt-api.shn.hk/v1/", headers=headers, json=json) as response:
                    if not response.ok:
                        logger.error("{0}-{1} AI request failed: {2}".format(response.status,
                                     response.reason, response.content.read()))
                        await msg.reply("Uh-oh! I'm having trouble at the moment, please try again later {0}"
                                        .format(Emotes.CONFUSED))
                    else:
                        await msg.reply((await response.json())['choices'][0]['message']['content'])


class Help_Nav(discord.ui.View):
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

    @ discord.ui.button(label="Back", style=discord.ButtonStyle.secondary, emoji='⬅️')
    async def backward_callback(self, _, interaction: discord.Interaction) -> None:
        self.index -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        logger.debug("Back button pressed", member_id=interaction.user.id)

    @ discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, emoji='➡️')
    async def forward_callback(self, _, interaction: discord.Interaction) -> None:
        self.index += 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        logger.debug("Next button pressed", member_id=interaction.user.id)


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Misc(bot))
