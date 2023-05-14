import discord
from discord.ext import commands

from helpers.logger import Logger
import helpers.database as db
from helpers.style import Emotes
from helpers.emoji import Emoji

logger = Logger()


class Admin(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.slash_command(
        name="send_react_message",
        description="sends a message to the given channel. " +
        "reacting with the given emoji will assign the given role")
    @discord.commands.default_permissions(manage_guild=True)
    async def greeting_role(self, ctx: discord.ApplicationContext,
                            text: str,
                            channel: discord.Option(discord.TextChannel, required=False),
                            emoji: discord.Option(str, required=False),
                            role: discord.Option(discord.Role, required=False)):
        if not channel:
            channel = ctx.channel

        if emoji:
            logger.debug(f"emoji1={emoji}")
            try:
                emoji = Emoji(emoji)
            except ValueError:
                await ctx.respond(f"Whoops! {Emotes.WTF} That emoji is not a valid discord emoji", ephemeral=True)
                return

        text = text.replace("<<nl>>", "\n")
        try:
            message = await channel.send(text)
        except discord.errors.Forbidden:
            logger.info("Permission failure for chain_message", guild_id=ctx.guild_id, channel_id=channel.id)
            await ctx.respond(f"Whoops! {Emotes.WTF} I don't have permissions to write in {channel.mention}",
                              ephemeral=True)
            return
        if not emoji:
            await ctx.respond(f"Message Sent! {Emotes.HEART}", ephemeral=True)
            return

        await message.add_reaction(emoji=emoji.to_partial_emoji())
        logger.debug(f"role={role}")
        if role:
            logger.debug(f"Message ID on insert: {message.id}")
            db.single_SQL("INSERT INTO ReactMessages VALUES (%s, %s, %s, %s)",
                          (ctx.guild_id, message.id, role.id, emoji.as_text()))
        await ctx.respond(f"Message Sent! {Emotes.HEART}")

    @discord.slash_command(name="remove_single_role_assignment", description="Takes out all of Nix's role " +
                           "assigning behaviour for this role")
    async def remove_single_role(self, ctx: discord.ApplicationContext, role: discord.Option(discord.Role,
                                 description="The role to remove assignment for")):
        db.multi_void_SQL([
            ("DELETE FROM RoleChannel WHERE GuildID=%s AND RoleID=%s", (ctx.guild_id, role.id)),
            ("DELETE FROM ReactMessages WHERE GuildID=%s AND RoleID=%s", (ctx.guild_id, role.id))])
        await ctx.respond(f"All role assign behaviours have been cleared for {role.name}")

    @discord.slash_command(name="clear_role_setting",
                           description="resets all role assigning behaviour" +
                           "note this will not clear existing roles, or delete Nix messages")
    @discord.commands.default_permissions(manage_guild=True)
    async def delete_react_entry(self, ctx: discord.ApplicationContext):
        logger.info("Dropping react entries", guild_id=ctx.guild_id)
        db.multi_void_SQL([
            ("DELETE FROM ReactMessages WHERE GuildID=%s", (ctx.guild_id,)),
            ("DELETE FROM RoleChannel WHERE GuildID=%s", (ctx.guild_id,))])
        await ctx.respond("All role assign behaviours have been cleared")

    @discord.slash_command(name='set_role_channel',
                           description="sets role channel, anyone who sends a message in " +
                           "the channel will be assigned the given role")
    @discord.commands.default_permissions(manage_guild=True)
    async def role_channel(self, ctx: discord.ApplicationContext,
                           channel: discord.TextChannel,
                           role: discord.Role):
        db.single_SQL("INSERT INTO RoleChannel VALUES (%s, %s, %s, TRUE)",
                      (ctx.guild_id, role.id, channel.id))
        await ctx.respond(f"Role channel was set to {channel.mention}")

    @discord.slash_command(name='set_remove_role_channel',
                           description="sets role remove channel, anyone who sends a message " +
                           "will have the given role removed")
    @discord.commands.default_permissions(manage_guild=True)
    async def remove_role_channel(self, ctx: discord.ApplicationContext,
                                  channel: discord.TextChannel,
                                  role: discord.Role):
        db.single_SQL("INSERT INTO RoleChannel VALUES (%s, %s, %s, FALSE)",
                      (ctx.guild_id, role.id, channel.id))
        await ctx.respond(f"Role remove channel was set to {channel.mention}")

    @discord.commands.slash_command(
        name="set_chain_message",
        description="allows Nix to follow up with custom messages whenever a user send a message")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_chain_message(self, ctx: discord.ApplicationContext,
                                message: discord.Option(
                                    str,
                                    description="The message text that will be sent as a follow up. " +
                                                "Write <<user>> to ping the user"),
                                response_channel: discord.Option(
                                    discord.TextChannel,
                                    description="The channel where Nix sends its follow up"),
                                message_channel: discord.Option(
                                    discord.TextChannel,
                                    required=False,
                                    description="The channel Nix watches for new messages " +
                                    "If not provided then Nix follows up all messages")):
        channel_id = message_channel.id if message_channel is not None else -1
        try:
            db.single_SQL("INSERT INTO MessageChain VALUES (%s,%s,%s,%s)",
                          (ctx.guild_id, channel_id, response_channel.id, message))
            await ctx.respond(f"You set a chain_message for the channel {response_channel}")
        except db.KeyViolation:
            await ctx.respond(f"You already set this as a message for this channel {Emotes.CONFUSED}")

    @commands.slash_command(name="clear_chain_messages", description="Clears all chain message behaviours")
    @discord.commands.default_permissions(manage_guild=True)
    async def clear_chain_message(self, ctx: discord.ApplicationContext):
        db.multi_void_SQL([
            ("DELETE FROM ChainedUsers WHERE GuildID=%s", (ctx.guild_id,)),
            ("DELETE FROM MessageChain WHERE GuildID=%s", (ctx.guild_id,))])

    @commands.Cog.listener('on_message')
    async def chain_message(self, msg: discord.Message):
        if msg.author.id != self.bot.user.id:
            values = db.single_SQL("SELECT WatchedChannelID FROM MessageChain WHERE GuildID=%s",
                                   (msg.guild.id,))
            if values:
                check_vals = [val[0] for val in values]
                if msg.channel.id in check_vals or -1 in check_vals:
                    try:
                        db.single_SQL("INSERT INTO ChainedUsers VALUES (%s, %s, %s)",
                                      (msg.guild.id, msg.author.id, msg.channel.id
                                       if msg.channel.id in check_vals else -1))
                        await self.send_chained_message(msg.guild, msg.author)
                    except db.KeyViolation:
                        logger.info("User that is already chained has written in the channel again",
                                    member_id=msg.author.id, guild_id=msg.guild.id)

    @commands.Cog.listener('on_message')
    async def assign_role(self, msg: discord.Message):
        if msg.author.id != self.bot.user.id:
            vals = db.single_SQL("SELECT RoleID, ToAdd FROM RoleChannel WHERE ChannelID=%s", (msg.channel.id,))
            for (role_id, add_role) in vals:
                if add_role:
                    await msg.author.add_roles(msg.guild.get_role(role_id))
                else:
                    await msg.author.remove_roles(msg.guild.get_role(role_id))

    @commands.Cog.listener('on_raw_reaction_add')
    async def assign_react_role(self, event: discord.RawReactionActionEvent):
        if event.user_id == self.bot.user.id:
            return
        logger.debug(f"Message ID on reaction: {event.message_id}")
        vals = db.single_SQL(
            "SELECT Emoji, RoleID FROM ReactMessages WHERE MessageID=%s", (event.message_id,))
        logger.debug(f"SQL values: {vals}")
        for (emoji, role_id) in vals:
            if Emoji(emoji).to_partial_emoji() == event.emoji:
                logger.debug("adding role")
                await event.member.add_roles(event.member.guild.get_role(role_id))

    @commands.Cog.listener('on_raw_reaction_remove')
    async def unassign_react_role(self, event: discord.RawReactionActionEvent):
        vals = db.single_SQL(
            "SELECT Emoji, RoleID FROM ReactMessages WHERE MessageID=%s", (event.message_id,))
        for (emoji, role_id) in vals:
            if Emoji(emoji).to_partial_emoji() == event.emoji:
                logger.debug("removing role")
                guild = await self.bot.fetch_guild(event.guild_id)
                member = await guild.fetch_member(event.user_id)
                await member.remove_roles(guild.get_role(role_id))

    @staticmethod
    async def send_chained_message(guild: discord.Guild, user: discord.User):
        vals = db.single_SQL(
            "SELECT ResponseChannelID, Message FROM MessageChain WHERE GuildID=%s", (guild.id,))
        for (response_channel_id, message) in vals:
            msg = message.replace("<<user>>", user.mention)
            try:
                await guild.get_channel(response_channel_id).send(msg)
            except discord.errors.Forbidden:
                logger.info("Permission failure for chain_message",
                            guild_id=guild.id, channel_id=response_channel_id)
                pass


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Admin(bot))
