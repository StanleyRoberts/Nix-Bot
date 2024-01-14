import discord
import asyncio
from discord.ext import commands

import helpers.database as db
from helpers.style import Emotes
from helpers.logger import Logger
from Nix import NIX_ID

logger = Logger()


class Counting(commands.Cog):
    def __init__(self) -> None:
        self.lock = asyncio.Lock()

    @commands.Cog.listener("on_message")
    async def count(self, msg: discord.Message) -> None:
        """
        Triggered on all messages, used to check for counting game

        Args:
            msg (discord.Message): Message that triggered function
        """
        if msg.author.id == NIX_ID:
            return
        if not msg.content.isdigit():
            return
        if msg.guild is None:
            return
        async with self.lock:
            values = db.single_sql(
                "SELECT CountingChannelID, CurrentCount, LastCounterID, "
                "FailRoleID FROM Guilds WHERE ID=%s",
                (msg.guild.id,)
            )
            (chnl_id, curr_ct, last_ctr_id, fail_id) = values[0]
            if msg.channel.id == chnl_id:
                logger.debug("Integer message detacted in counting channel")
                if int(msg.content) != curr_ct + 1:
                    logger.debug("Wrong number detected in counting channel")
                    await self.fail(msg, "Wrong number", fail_id)
                elif msg.author.id == last_ctr_id:
                    logger.debug("Double-user-input detected in counting channel")
                    await self.fail(msg, "Same user entered two numbers", fail_id)
                else:
                    await msg.add_reaction(Emotes.BLEP)
                    db.single_void_SQL(
                        "UPDATE Guilds SET LastCounterID =%s, CurrentCount = CurrentCount+1, " +
                        "HighScoreCounting=(CASE WHEN %s>HighScoreCounting THEN %s ELSE " +
                        "HighScoreCounting END) WHERE ID =%s",
                        (msg.author.id, msg.content, msg.content, msg.guild.id))

    @commands.slash_command(name='set_fail_role',
                            description="Sets the role the given to users who fail at counting")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_fail_role(self, ctx: discord.ApplicationContext, role: discord.Role) -> None:
        logger.info("fail_role set")
        db.single_void_SQL("UPDATE Guilds SET FailRoleID=%s WHERE ID=%s",
                           (role.id, ctx.guild_id))
        await ctx.respond(
            f"The fail role is set to {role.mention} {Emotes.DRINKING}", ephemeral=True
        )

    @commands.slash_command(name='set_counting_channel',
                            description="Sets the channel for the counting game")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_counting_channel(
        self,
        ctx: discord.ApplicationContext,
        channel: discord.TextChannel
    ) -> None:
        logger.info("counting_channel set")
        db.single_void_SQL("UPDATE Guilds SET CountingChannelID=%s WHERE ID=%s",
                           (channel.id, ctx.guild_id))
        await ctx.respond(
            f"Counting channel set to {channel.mention} {Emotes.DRINKING}", ephemeral=True
        )

    @commands.slash_command(name='get_highscore',
                            description="Shows you the highest count your server has reached")
    async def get_highscore(self, ctx: discord.ApplicationContext) -> None:
        highscore = db.single_sql(
            "SELECT HighScoreCounting FROM Guilds WHERE ID = %s", (ctx.guild.id,))
        await ctx.respond(f"Your server highscore is {highscore[0][0]}! {Emotes.WHOA}")

    @staticmethod
    async def fail(msg: discord.Message, err_txt: str, roleID: int) -> None:
        """
        Handles a generic counting failure

        Args:
            msg (discord.Message): Message that failed
            err_txt (string): Failure message to print to channel
            roleID (int): ID of role to assign to user that failed
        """
        if msg.guild is None or not isinstance(msg.author, discord.Member):
            return
        db.single_void_SQL(
            "UPDATE Guilds SET CurrentCount=0, LastCounterID=NULL WHERE ID=%s", (msg.guild.id,))
        await msg.add_reaction(Emotes.CRYING)
        await msg.channel.send(f"Counting Failed {Emotes.CRYING} {err_txt}")
        role = msg.guild.get_role(roleID)
        if role:
            try:
                await msg.author.add_roles(role, reason="failed the counting")
            except discord.errors.Forbidden:
                logger.warning("Missing permission to assign fail_role")
                await msg.channel.send("Whoops! I couldn't set the " +
                                       f"{role.mention} role {Emotes.CONFUSED} " +
                                       "(I need 'Manage Roles' to do that)" +
                                       "\nI won't try again until you set a new fail role")
                db.single_void_SQL("UPDATE Guilds SET FailRoleID=NULL WHERE ID=%s", (msg.guild.id,))
        else:
            logger.error("Couldnt get fail role for counting")


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Counting())
