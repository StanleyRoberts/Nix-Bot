from types import coroutine
import discord
from discord.ext import commands
import functions.database as db
import asyncio


class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()

    @commands.Cog.listener()
    async def on_message(self, msg):
        async with self.lock:
            if (msg.content.isdigit()):
                values = db.single_SQL("SELECT CountingChannelID, CurrentCount, LastCounterID, HighScoreCounting, "
                                       "FailRoleID FROM Guilds WHERE ID=%s", (msg.guild.id,))
                # Checks for the right channel
                if (msg.channel.id == values[0][0]):
                    # Checks if it is the correct number
                    if (int(msg.content) != values[0][1] + 1):
                        await self.fail(msg, "Wrong number", values[0][4])
                    # Checks if the same user wrote twice
                    elif (msg.author.id == values[0][2]):
                        await self.fail(msg, "Same user entered two numbers", values[0][4])
                    else:
                        await msg.add_reaction('<:NixBlep:1026494035994607717>')
                        db.single_SQL("UPDATE Guilds SET LastCounterID =%s, CurrentCount = CurrentCount+1, HighScoreCounting="
                                      "(CASE WHEN %s>HighScoreCounting THEN %s ELSE HighScoreCounting END) WHERE ID =%s",
                                      (msg.author.id, msg.content, msg.content, msg.guild.id))

    @commands.slash_command(name='set_fail_role', description="Sets the role the given to users who fail at counting")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_fail_role(self, ctx, role: discord.Role):
        db.single_SQL("UPDATE Guilds SET FailRoleID=%s WHERE ID=%s",
                      (role.id, ctx.guild_id))
        await ctx.respond("<:NixDrinking:1026494037043187713> The fail role is set to {0}".format(role.mention), ephemeral=True)

    @commands.slash_command(name='set_counting_channel', description="Sets the channel for the counting game")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_counting_channel(self, ctx, channel: discord.TextChannel):
        db.single_SQL(
            "UPDATE Guilds SET CountingChannelID=%s WHERE ID=%s", (channel.id, ctx.guild_id))
        await ctx.respond("<:NixDrinking:1026494037043187713> Counting channel set to {0}".format(channel.mention), ephemeral=True)

    @commands.slash_command(name='get_highscore', description="Shows you the highest count your server has reached")
    async def get_highscore(self, ctx):
        highscore = db.single_SQL(
            "SELECT HighScoreCounting FROM Guilds WHERE ID = %s", (ctx.guild.id,))
        await ctx.respond("Your server highscore is {0}! <:NixWhoa:1026494032999895161>".format(highscore[0][0]))

    @staticmethod
    async def clear_fail_role():
        gandR = db.single_SQL("SELECT ID, LoserRoleID FROM Guilds")
        for g in gandR:
            # For all users with the role
            for user in commands.get_guild(g[0]).get_role(g[1]).members:
                # Remove the role
                await user.remove_roles(commands.get_guild(g[0]).get_role(g[1]))

    @staticmethod
    async def fail(msg, err_txt, roleID):
        db.single_SQL(
            "UPDATE Guilds SET CurrentCount=0, LastCounterID=NULL WHERE ID=%s", (msg.guild.id,))
        await msg.add_reaction('<:NixCrying:1026494029002723398>')
        await msg.channel.send("Counting Failed <:NixCrying:1026494029002723398> "+err_txt)
        if roleID:
            try:
                await msg.author.add_roles(msg.guild.get_role(roleID))
            except discord.errors.Forbidden:
                await msg.channel.send("<:NixConfused:1026494027727638599> Whoops! I couldn't set the {0} role (I need 'Manage Roles' to do that)"
                                       ".\nI won't try again until you set a new fail role".format(msg.guild.get_role(roleID).mention))
                db.single_SQL(
                    "UPDATE Guilds SET FailRoleID=NULL WHERE ID=%s", (msg.guild.id,))


def setup(bot):
    bot.add_cog(Counting(bot))
