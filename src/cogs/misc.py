from discord.ext import commands
import discord
import requests
import typing
import re
from tls_client.exceptions import TLSClientExeption as TLSClientException  # type: ignore[import]
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
    async def nlp(self, msg: discord.Message) -> None:
        """
        Prints out an AI generated response to the message if it mentions Nix

        Args:
            msg (discord.Message): Message that triggered event
        """
        if self.bot.user is None:
            logger.error("bot.user is None (Bot is offline)")
            return
        if (self.bot.user.mentioned_in(msg) and msg.reference is None):
            logger.info("Generating AI response", member_id=msg.author.id,
                        channel_id=msg.channel.id)
            async with msg.channel.typing():
                clean_prompt = re.sub(
                    " @", " ", re.sub("@" + self.bot.user.name, "", msg.clean_content))
                client = PyCAI(CAI_TOKEN)
                chat = await client.chat.new_chat(CAI_NIX_ID)
                participants = chat['participants']
                nix_username = participants[1 if participants[0]
                                            ['is_human'] else 0]['user']['username']
                try:
                    data = await client.chat.send_message(
                        tgt=nix_username,
                        history_id=chat['external_id'],
                        text=clean_prompt,
                        wait=True
                    )
                    text = data['replies'][0]['text']
                except TLSClientException:
                    text = f"Uh-oh! I'm having trouble at the moment, please try again later {Emotes.CLOWN}"
                await msg.reply(text)
                return


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
