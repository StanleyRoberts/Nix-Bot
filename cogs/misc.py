from discord.ext import commands
import discord
import requests
import typing
import json
import re

from functions.style import Colours
from Nix import HF_API


class Misc(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.slash_command(name='quote', description="Displays an AI-generated quote over an inspirational image")
    async def send_quote(self, ctx: discord.ApplicationContext) -> None:
        await ctx.respond(requests.get("https://inspirobot.me/api?generate=true").text)

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

    @commands.slash_command(name='help', description="Display the help page for Nix")
    async def helper_embed(self, ctx: discord.ApplicationContext) -> None:
        view = Help_Nav(self.bot.cogs)
        await ctx.interaction.response.send_message(embed=view.build_embed(), view=view)

    @commands.Cog.listener("on_message")
    async def NLP(self, msg: discord.Message):
        """
        Prints out an AI generated response to the message if it mentions Nix

        Args:
            msg (discord.Message): Message that triggered event
        """
        if (self.bot.user.mentioned_in(msg) and msg.reference is None):
            clean_prompt = re.sub(" @", " ",
                                  re.sub("@" + self.bot.user.name, "", msg.clean_content))

            url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
            headers = {"Authorization": f"Bearer {HF_API}"}

            prompt = {"past_user_inputs": ["What is your name?", "Who are you?", "Is Stan cool?"],
                      "generated_responses": ["My name is Nix", "I am Nix, a phoenix made of flames",
                                              "Yes, I think Stan is the best!"],
                      "text": clean_prompt}

            data = json.dumps({"inputs": prompt, "parameters": {
                              "return_full_text": False, "temperature": 0.8,
                              "use_cache": False}})
            response = requests.request("POST", url, headers=headers, data=data)

            text = json.loads(response.content.decode('utf-8'))
            await msg.reply(text['generated_text'])


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

    @discord.ui.button(label="<-", style=discord.ButtonStyle.primary)
    async def backward_callback(self, _, interaction: discord.Interaction) -> None:
        self.index -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="->", style=discord.ButtonStyle.primary)
    async def forward_callback(self, _, interaction: discord.Interaction) -> None:
        self.index += 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Misc(bot))
