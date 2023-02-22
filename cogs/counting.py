import discord
import asyncio
from discord.ext import commands

import helpers.database as db
from helpers.style import Emotes


class Counting(commands.Cog):
    def __init__(self, bot: discord.ApplicationContext) -> None:
        self.bot = bot
        self.lock = asyncio.Lock()

    @commands.Cog.listener("on_message")
    async def count(self, msg):
        """
        Triggered on all messages, used to check for counting game

        Args:
            msg (discord.Message): Message that triggered function
        """
        async with self.lock:
            if (msg.content.isdigit()):
                values = db.single_SQL("SELECT CountingChannelID, CurrentCount, LastCounterID, HighScoreCounting, "
                                       "FailRoleID FROM Guilds WHERE ID=%s", (msg.guild.id,))
                if (msg.channel.id == values[0][0]):
                    if (int(msg.content) != values[0][1] + 1):
                        await self.fail(msg, "Wrong number", values[0][4])
                    elif (msg.author.id == values[0][2]):
                        await self.fail(msg, "Same user entered two numbers", values[0][4])
                    else:
                        await msg.add_reaction(Emotes.BLEP)
                        db.single_SQL("UPDATE Guilds SET LastCounterID =%s, CurrentCount = CurrentCount+1, " +
                                      "HighScoreCounting=(CASE WHEN %s>HighScoreCounting THEN %s ELSE " +
                                      "HighScoreCounting END) WHERE ID =%s",
                                      (msg.author.id, msg.content, msg.content, msg.guild.id))

    @commands.slash_command(name='set_fail_role', description="Sets the role the given to users who fail at counting")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_fail_role(self, ctx: discord.ApplicationContext, role: discord.Role) -> None:
        db.single_SQL("UPDATE Guilds SET FailRoleID=%s WHERE ID=%s",
                      (role.id, ctx.guild_id))
        await ctx.respond("The fail role is set to {0} {1}"
                          .format(role.mention, Emotes.DRINKING), ephemeral=True)

    @commands.slash_command(name='set_counting_channel', description="Sets the channel for the counting game")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_counting_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel) -> None:
        db.single_SQL("UPDATE Guilds SET CountingChannelID=%s WHERE ID=%s", (channel.id, ctx.guild_id))
        await ctx.respond("Counting channel set to {0} {1}"
                          .format(channel.mention, Emotes.DRINKING), ephemeral=True)

    @commands.slash_command(name='get_highscore', description="Shows you the highest count your server has reached")
    async def get_highscore(self, ctx: discord.ApplicationContext) -> None:
        highscore = db.single_SQL("SELECT HighScoreCounting FROM Guilds WHERE ID = %s", (ctx.guild.id,))
        await ctx.respond("Your server highscore is {0}! {1}".format(highscore[0][0], Emotes.WHOA))

    @staticmethod
    async def clear_fail_role() -> None:
        """
        Clears fail roles from all users on all servers
        """
        guilds_and_roles = db.single_SQL("SELECT ID, LoserRoleID FROM Guilds")
        for pair in guilds_and_roles:
            # For all users with the role
            for user in commands.get_guild(pair[0]).get_role(pair[1]).members:
                # Remove the role
                await user.remove_roles(commands.get_guild(pair[0]).get_role(pair[1]))

    @staticmethod
    async def fail(msg: discord.Message, err_txt: str, roleID: int) -> None:
        """
        Handles a generic counting failure

        Args:
            msg (discord.Message): Message that failed
            err_txt (string): Failure message to print to channel
            roleID (int): ID of role to assign to user that failed
        """
        db.single_SQL("UPDATE Guilds SET CurrentCount=0, LastCounterID=NULL WHERE ID=%s", (msg.guild.id,))
        await msg.add_reaction(Emotes.CRYING)
        await msg.channel.send("Counting Failed {0} {1}".format(Emotes.CRYING, err_txt))
        if roleID:
            try:
                await msg.author.add_roles(msg.guild.get_role(roleID))
            except discord.errors.Forbidden:
                await msg.channel.send("Whoops! I couldn't set the " +
                                       "{0} role {1} (I need 'Manage Roles' to do that)"
                                       ".\nI won't try again until you set a new fail role"
                                       .format(msg.guild.get_role(roleID).mention, Emotes.CONFUSED))
                db.single_SQL("UPDATE Guilds SET FailRoleID=NULL WHERE ID=%s", (msg.guild.id,))


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Counting(bot))
