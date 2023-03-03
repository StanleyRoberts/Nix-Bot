from discord.ext import commands
import discord
import requests
import typing
import json
import re

from src.helpers.style import Colours
from src.helpers.env import HF_API
from src.helpers.logger import Logger
from src.helpers.style import Emotes

logger = Logger()

USER_QS = ["Who are you?", "Is Stan cool?", "What is your favourite server?", "Where do you live?",
           "Unless I tell you what my name is, please call me \'fire friend\'"]
NIX_AS = ["I am Nix, a phoenix made of flames", "Yes, I think Stan is the best!",
          "I love the Watching Racoons server the most!",
          "I live in a volcano with my friends: DJ the Dragon and Sammy the Firebird.",
          "Sure thing, fire friend!"]


class Misc(commands.Cog):
    def __init__(self, bot) -> None:
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
            questions = USER_QS
            answers = NIX_AS

            inspect = msg
            is_answer = True
            while inspect.reference is not None:
                if is_answer:
                    answers.append(inspect.content)
                else:
                    questions.append(inspect.content)
                inspect = inspect

            if len(questions) != len(answers):
                logger.error("Questions and Answers array for NLP chained reply are not the same size")
                return

            logger.info("Generating AI response", member_id=msg.author.id, channel_id=msg.channel.id)
            clean_prompt = re.sub(" @", " ",
                                  re.sub("@" + self.bot.user.name, "", msg.clean_content))

            url = "https://api-inference.huggingface.co/models/PygmalionAI/pygmalion-6b"
            headers = {"Authorization": f"Bearer {HF_API}"}

            prompt = {"past_user_inputs": questions,
                      "generated_responses": answers,
                      "text": clean_prompt}

            data = json.dumps({"inputs": prompt,
                               "parameters": {"return_full_text": False},
                               "options": {"use_cache": False}
                               })
            response = requests.request("POST", url, headers=headers, data=data)
            if response.status_code != requests.codes.ok:
                logger.error("{0} AI request failed: {1}".format(response.status_code, response.content))
                await msg.reply("Uh-oh! I'm having trouble at the moment, please try again later {0}"
                                .format(Emotes.CONFUSED))
                return

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

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary, emoji='⬅️')
    async def backward_callback(self, _, interaction: discord.Interaction) -> None:
        self.index -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        logger.debug("Back button pressed", member_id=interaction.user.id)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, emoji='➡️')
    async def forward_callback(self, _, interaction: discord.Interaction) -> None:
        self.index += 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        logger.debug("Next button pressed", member_id=interaction.user.id)


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Misc(bot))