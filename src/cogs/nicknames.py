from discord.ext import commands
import discord

from helpers.logger import Logger
import helpers.database as db
from helpers.style import Emotes

logger = Logger()


class Nicknames(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @discord.slash_command(name='allow_other_nickname_changes',
                           description="allows users to use Nix to change other peoples nicknames")
    @discord.commands.default_permissions(manage_guild=True)
    async def allow_nickname_changes(
        self,
        ctx: discord.ApplicationContext,
        allow_nickname_changes: bool,
    ) -> None:
        db.single_void_SQL("UPDATE Guilds SET NicknameChangeAllowed={%s} WHERE GuildID=%s",
                           (allow_nickname_changes, ctx.guild.id))
        ctx.respond("Members can now {}change each other's nicknames", ""
                    if allow_nickname_changes else "not ", ephemeral=True)

    @commands.slash_command(
        name='nickname',
        description="change a users nickname"
    )
    @discord.commands.option("user", type=discord.User, required=False)
    async def change_nickname(self, ctx: discord.ApplicationContext, nickname: str,
                              user: discord.User | None) -> None:
        logger.debug("TODO {}", db.single_sql(
            "SELECT NicknameChangeAllowed FROM Guilds WHERE GuildID=%s", (ctx.guild.id,)))
        if db.single_sql(
                "SELECT NicknameChangeAllowed FROM Guilds WHERE GuildID=%s", (ctx.guild.id,)):
            logger.debug("Guild does not allow nickname changes")
            await ctx.respond(
                f"Sorry, this server doesn't allow changing nicknames {Emotes.CRYING}",
                ephemeral=True
            )
            return
        if not user:
            user = ctx.user
        if not isinstance(user, discord.Member):
            logger.debug("User {subject} is not a guild member")
            return

        channel = ctx.channel
        if not isinstance(channel, discord.abc.GuildChannel):
            logger.debug("Channel {channel.id} is not guild channel")
            return
        # guard to prevent users without change_nickname perms from changing their own nickname through Nix
        if user == ctx.user and channel.permissions_for(ctx.user).change_nickname:
            logger.debug(
                "Guild does not allow user to change their own nickname")
            await ctx.respond(
                f"Sorry, you dont have permissions to change your own nickname {Emotes.WORRIED}",
                ephemeral=True
            )
            return

        await user.edit(nick=nickname)
        await ctx.respond(
            f"{user.mention}'s nickname has been changed to {nickname}! {Emotes.TEEHEE}",
            ephemeral=True
        )


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Nicknames(bot))
