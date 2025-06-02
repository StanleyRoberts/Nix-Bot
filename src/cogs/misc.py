from discord.ext import commands
import discord
import requests
import typing
import re
from characterai import PyAsyncCAI as PyCAI  # type: ignore[import]

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
        view = Help_Nav(self.bot.cogs)
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

        if not self.bot.user.mentioned_in(msg):
            return

        logger.info("Generating AI response",
                    member_id=msg.author.id, channel_id=msg.channel.id)
        try:
            async with msg.channel.typing():
                await msg.reply(await Misc.ai_resp(
                    Misc.format_chain(
                        list(reversed(await Misc.get_history(msg))), self.bot.user.name
                    )
                ))
        except Exception as err:  # API for AI is unstable so we catch all here
            logger.error(f"AI error: {err}")
            await msg.reply(
                f"Uh-oh! I'm having trouble at the moment, please try again later {Emotes.CLOWN}"
            )

    @staticmethod
    async def get_history(
            msg: discord.Message,
            chain: list[str] = []) -> list[str]:
        """
        Get a messages reply-chain history

        Args:
            msg (discord.Message): Message to get reply-chain of

        Returns:
            string: List of each messages content in the reply-chain,
                chronologically with the first message being the newest
        """
        chain.append(msg.clean_content)
        if msg.reference is None or msg.reference.message_id is None:
            return chain
        else:
            return await Misc.get_history(
                await msg.channel.fetch_message(msg.reference.message_id), chain
            )

    @staticmethod
    def format_chain(msg_arr: list[str], bot_name: str) -> str:
        """
        Format a message chain for input into AI

        Args:
            msg_arr (list[str]): List of each messages content in the chain,
                in chronological order with the first item being the oldest message

        Returns:
            str: Formatted message for input into AI
        """
        logger.debug(f"chain: {msg_arr}")
        msg_arr = list(map(lambda x: re.sub(" @", " ", re.sub("@" + bot_name, "", x)),
                           msg_arr))
        if len(msg_arr) > 1:
            idents = ["[Nix]" if i % 2 else "[User]" for i in range(0, len(msg_arr))]
            history = "\n".join([i + ": " + j for (i, j) in zip(idents, msg_arr)])
            return f"""The following text is your message history with this user: `
{history}`

Please continue this conversation. The users newest message is: {msg_arr[len(msg_arr)-1]}"""
        else:
            return msg_arr[0]

    @staticmethod
    async def ai_resp(prompt: str) -> str:
        """
        Prints out an AI generated response to a message

        Args:
            prompt (str): Message text to reply to

        Returns:
            str: Response from the Nix AI
        """
        logger.debug(f"prompt: {prompt}")
        client = PyCAI(CAI_TOKEN)
        chat = await client.chat.new_chat(CAI_NIX_ID)
        participants = chat['participants']
        nix_username = participants[1 if participants[0]['is_human'] else 0]['user']['username']
        data = await client.chat.send_message(
            tgt=nix_username,
            history_id=chat['external_id'],
            text=prompt,
            wait=True
        )
        return typing.cast(str, data['replies'][0]['text'])


class Help_Nav(discord.ui.View):
    def __init__(self, cogs: typing.Mapping[str, discord.Cog]) -> None:
        super().__init__()
        self.index = 0
        self.pages = ["Front"] + [cogs[cog] for cog in cogs]

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
