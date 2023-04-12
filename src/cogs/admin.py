import discord
from discord.ext import commands

from helpers.logger import Logger
import helpers.database as db
from helpers.style import Emotes, string_to_emoji

logger = Logger()


class Admin(commands.Cog):

    @commands.slash_command(
        name="send_react_message",
        description="sends a message to the given channel. " +
        "reacting with the given emoji will assign the given role")
    @discord.commands.default_permissions(manage_guild=True)
    async def greeting_role(self, ctx: discord.ApplicationContext,
                            text: str,
                            channel: discord.TextChannel,
                            emoji: discord.Option(str, required=False),
                            role: discord.Option(discord.Role, required=False)):

        if emoji:
            try:
                part_emoji = string_to_emoji(emoji)
            except ValueError:
                await ctx.respond(f"Whoops! {Emotes.WTF} That emoji is not a valid discord emoji", ephemeral=True)
                return

        message = await channel.send(text)
        if not emoji:
            return

        await message.add_reaction(emoji=part_emoji)
        if role:
            # TODO this requires live database update
            db.single_SQL("INSERT INTO ReactMessages VALUES (%s, %s, %s, %s)",
                          (ctx.guild_id, message.id, role.id, emoji.id))
        await ctx.respond(f"Message Sent! {Emotes.HEART}", ephemeral=True)

    @discord.slash_command(name="clear_role_setting",
                           description="resets all role assigning behaviour" +
                           "note this will not clear existing roles, or delete Nix messages")
    @discord.commands.default_permissions(manage_guild=True)
    async def delete_react_entry(self, ctx: discord.ApplicationContext):
        logger.info("Dropping react entries", guild_id=ctx.guild_id)
        db.single_SQL("DELETE FROM ReactMessages WHERE GuildID=%s", (ctx.guild_id,))
        db.single_SQL("DELETE FROM RoleMessages WHERE GuildID=%s", (ctx.guild_id,))

    @discord.slash_command(name='set_role_channel',
                           description="sets role channel, anyone who sends a message in " +
                           "the channel will be assigned the given role")
    async def role_channel(self, ctx: discord.ApplicationContext,
                           channel: discord.TextChannel,
                           role: discord.Role):
        # TODO this requires live db update
        db.single_SQL("INSERT INTO RoleMessages VALUES %s %s %s", (ctx.guild_id, role.id, channel.id))

    @commands.Cog.listener('on_message')
    async def assign_role(self, msg: discord.Message):
        vals = db.single_SQL("SELECT RoleID FROM RoleChannel WHERE ChannelID=%s", (msg.channel.id,))
        for val in vals:
            msg.author.add_roles(msg.guild.get_role(val[0]))

    @commands.Cog.listener('on_raw_reaction_add')
    async def assign_roles(self, event: discord.RawReactionActionEvent):
        vals = db.single_SQL("SELECT EmojiID, RoleID FROM ReactMessages WHERE MessageID=%s", (event.message_id,))
        for val in vals:
            if val[0] == event.emoji.id:
                event.member.add_roles(event.member.guild.get_role(vals[1]))


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Admin(bot))
