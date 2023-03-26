from discord.ext import commands
from huggingface_hub.inference_api import InferenceApi
import discord
import requests
import typing
import re
import json
import aiohttp

from helpers.style import Colours
from helpers.logger import Logger
from helpers.style import Emotes
from helpers.env import HF_API

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
    async def gen_response(self, msg: discord.Message):
        """
        Prints out an AI generated response to the message if it mentions Nix

        Args:
            msg (discord.Message): Message that triggered event
        """
        if self.bot.user.mentioned_in(msg) and msg.reference is None:
            logger.info("Generating AI response", member_id=msg.author.id, channel_id=msg.channel.id)
            clean_prompt = re.sub(" @", " ",
                                  re.sub("@" + self.bot.user.name, "", msg.clean_content))

            text = "Nix's Persona: Nix is a kind and friendly phoenix who lives in a volcano.\n<START>\n" +\
                "\nYou: " + clean_prompt + "\nNix: "

            logger.debug("Sending text: {0}".format(repr(text)))

            async with aiohttp.ClientSession() as session:
                # we force pygmalion into text-gen to allow us to set Nix personality
                url = "https://api-inference.huggingface.co/pipeline/text-generation/PygmalionAI/pygmalion-6b"
                input = {"inputs": text,
                         "parameters": {"return_full_text": False, "max_new_tokens": 50},
                         "options": {"use_cache": False, "wait_for_model": True}
                         }
                async with session.post(url, data=json.dumps(input)) as req:
                    if not req.ok:
                        logger.error("Error {0}: {1}".format(req.status, req.content))
                        await msg.reply("Sorry, I had trouble understanding. Please try again later {0}"
                                        .format(Emotes.CONFUSED))
                    else:
                        response = (await req.json())[0]['generated_text'].split("\n")[0]
                        response = re.sub("<USER>", msg.author.display_name, re.sub("<BOT>", "Nix", response))
                        logger.info("response: {0}".format(response))
                        await msg.reply(response)


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
