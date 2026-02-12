from discord.ext import commands
import discord
import requests
import typing
import re
from google import genai

from helpers.style import Colours, Emotes
from helpers.env import CAI_TOKEN, CAI_NIX_ID
from helpers.logger import Logger

logger = Logger()


class Misc(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.slash_command(
        name='quote',
        description="Displays an AI-generated quote over an inspirational image"
    )
    async def send_quote(self, ctx: discord.ApplicationContext) -> None:
        await ctx.respond(requests.get("https://inspirobot.me/api?generate=true", timeout=10).text)
        logger.info("Generating quote", member_id=ctx.author.id, channel_id=ctx.channel_id)

    @commands.slash_command(name='all_commands', description="Displays all of Nix's commands")
    async def display_help(self, ctx: discord.ApplicationContext) -> None:
        desc = ("Note: depending on your server settings and role permissions," +
                " some of these commands may be hidden or disabled\n\n" +
                "".join(
                    ["\n***" + cog + "***\n" + "".join(
                        sorted(
                            [command.mention + " : " +
                                command.description + "\n"
                                for command in self.bot.cogs[cog].walk_commands()
                                if isinstance(command, discord.SlashCommand)
                             ]
                        )
                    )
                        for cog in self.bot.cogs]
                ))
        embed = discord.Embed(title="Help Page", description=desc,
                              colour=Colours.PRIMARY)
        await ctx.respond(embed=embed)
        logger.info("Displaying long help", member_id=ctx.author.id, channel_id=ctx.channel_id)

    @commands.slash_command(name='help', description="Display the help page for Nix")
    async def helper_embed(self, ctx: discord.ApplicationContext) -> None:
        view = Help_Nav(self.bot.cogs, self.bot)
        await ctx.interaction.response.send_message(embed=view.build_embed(), view=view)
        logger.info("Displaying short help", member_id=ctx.author.id, channel_id=ctx.channel_id)

    @commands.Cog.listener("on_message")
    async def respond(self, msg: discord.Message) -> None:
        """
        Prints out an AI generated response to the message if it mentions Nix

        Args:
            msg (discord.Message): Message that triggered event
        """
        if self.bot.user is None:
            logger.error("Bot is offline")
            return

        if msg.guild is None:
            logger.error("Message not sent in server")
            return

        if not self.bot.user.mentioned_in(msg):
            return

        logger.info("Generating AI response",
                    member_id=msg.author.id, channel_id=msg.channel.id)

        nix_background = (
            f"You are Nix." +
            f"Nix is a phoenix made of flames, he is friendly, helpful, and kind." +
            f" He has many mythological friends and lives inside a volcano." +
            f" Nix is androgynous and has no gender." +
            f" Nix is a member of a Discord server called {msg.guild.name}" +
            f" which contains other humans and Nix." +
            f" Nix is talking to a server member called {msg.author.name}")

        async with msg.channel.typing():
            await msg.reply(await Misc.ai_resp(Misc.format_chain(
                list(reversed(await Misc.get_history(msg))), self.bot.user.name
            ), nix_background))

    @staticmethod
    async def get_history(
            msg: discord.Message,
            chain: list[tuple[str, str]] | None = None) -> list[tuple[str, str]]:
        """
        Get a messages reply-chain history

        Args:
            msg (discord.Message): Message to get reply-chain of

        Returns:
            string:List corresponding to each element in the message chain
                Tuple corresponds to (users_name, message content). Chronological order with
                first item being the newest message.
        """
        if chain is None:
            chain = []
        chain.append((msg.author.display_name, msg.clean_content))
        if msg.reference is None or msg.reference.message_id is None:
            return chain
        else:
            return await Misc.get_history(
                await msg.channel.fetch_message(msg.reference.message_id), chain
            )

    @staticmethod
    def format_chain(msg_arr: list[tuple[str, str]], bot_name: str) -> list[tuple[bool, str]]:
        """
        Format a message chain for input into AI

        Args:
            msg_arr (list[tuple[str, str]]): List corresponding to each element in the message chain
                Tuple corresponds to (users_name, message content). Chronological order with
                first item being the oldest message.

        Returns:
            list[tuple[bool, str]]: Formatted message for input into AI
        """
        msg_arr = list(map(lambda x: (x[0], re.sub(" @", " ", re.sub("@" + bot_name, "", x[1]))),
                           msg_arr))
        return [(message[0] == bot_name, message[1]) for message in msg_arr]

    @staticmethod
    async def ai_resp(messages: list[tuple[bool, str]], background: str) -> str:
        """
        Prints out an AI generated response to a message

        Args:
            messages (list[tuple(bool, str)]):
                List of past messages with flag set if the message was from the user.
                The first element in the list is the first message and
                the last message is the message to reply to.
            background (str): The background to use for Nix

        Returns:
            str: Response from the Nix AI
        """
        logger.debug(messages)
        response = None
        async with genai.Client().aio as client:
            try:
                response = (await client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=[
                        genai.types.Content(
                            role="model" if message[0] else "user",
                            parts=[genai.types.Part(text=message[1])]
                        )
                        for message in messages],
                    config=genai.types.GenerateContentConfig(
                        system_instruction=background
                    )
                )).text
            except Exception as err:
                logger.error(f"AI error: {err}")
            return (
                response or
                f"Uh-oh! I'm having trouble at the moment, please try again later {Emotes.CLOWN}"
            )


class Help_Nav(discord.ui.View):
    def __init__(self, cogs: typing.Mapping[str, discord.Cog], bot: discord.Bot) -> None:
        super().__init__()
        self.bot = bot
        self.index = 0
        self.pages = ["Front"] + [cogs[cog] for cog in cogs if cog != "Debug"]

    def build_embed(self) -> discord.Embed:
        self.index = self.index % len(self.pages)
        page = self.pages[self.index]

        compass = "|".join([f" {page.qualified_name} " if page != self.pages[self.index]
                            else f"** {page.qualified_name} **" for page in self.pages[1:]
                            if isinstance(page, discord.Cog)]) + "\n"
        if page == "Front":
            desc = compass + ("\nNote: depending on your server settings and role permissions, " +
                              "some of these commands may be hidden or disabled")
        else:
            if isinstance(page, str):
                raise ValueError(f"Unknown page encountered: {page}")
            desc = compass + ("\n***" + page.qualified_name + "***:\n" + ""
                              .join(sorted([command.mention + " : " + command.description + "\n"
                                            for command in page.walk_commands()
                                            if isinstance(command, discord.SlashCommand)])))
            if page.qualified_name == "Misc" and self.bot.user is not None:
                desc += f"{self.bot.user.mention} : Mentioning Nix in a message or replying" +\
                    " to Nix will cause Nix to respond!"

        return discord.Embed(title="Help Page", description=desc, colour=Colours.PRIMARY)

    @discord.ui.button(label="Back", style=discord.ButtonStyle.secondary, emoji='⬅️')
    async def backward_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:
        self.index -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        logger.debug("Back button pressed", member_id=interaction.user.id
                     if interaction.user is not None else 0)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, emoji='➡️')
    async def forward_callback(self, _: discord.Button, interaction: discord.Interaction) -> None:
        self.index += 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
        logger.debug("Next button pressed", member_id=interaction.user.id
                     if interaction.user is not None else 0)


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Misc(bot))
