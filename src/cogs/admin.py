import discord
from discord.ext import commands

from helpers.logger import Logger
import helpers.database as db

logger = Logger()


class Admin(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @commands.slash_command(
        name="send_react_message",
        description="sends the given message to the given channel. " +
        "users who react with the given emoji will be assigned the given role")
    @discord.commands.default_permissions(manage_guild=True)
    async def greeting_role(self, ctx: discord.ApplicationContext,
                            text: str,
                            channel: discord.TextChannel,
                            emoji: discord.Option(discord.Emoji, required=False),
                            role: discord.Option(discord.Role, required=False)):
        message = await channel.send(text)
        if not emoji:
            return
        message.add_reaction(emoji=emoji)
        if role:
            # TODO this requires live database update
            db.single_SQL("INSERT INTO ReactMessages VALUES %s %s %s", (ctx.guild_id, message.id, role.id))

    @ commands.Cog.listener('on_raw_reaction_add')
    async def assign_roles(self, event: discord.RawReactionActionEvent):
        vals = db.single_SQL("SELECT * FROM ReactMessages WHERE EmojiID=%s", (event.emoji.id,))
        for val in vals:
            if val[1] == event.message_id:
                if val[2]:
                    event.member.add_roles(self.bot.get_guild(event.guild_id).get_role(vals[2]))


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Admin(bot))
