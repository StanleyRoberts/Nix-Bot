import discord
import datetime as dt
from discord.ext import commands, tasks
import datetime as dt

import helpers.database as db
from helpers.style import Emotes, TIME
from helpers.logger import Logger

logger = Logger()


class Birthdays(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        self.daily_bday.start()

    @commands.slash_command(name='set_birthday_channel', description="Sets the channel for the birthday messages")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_counting_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel) -> None:
        db.single_SQL("UPDATE Guilds SET BirthdayChannelID=%s WHERE ID=%s", (channel.id, ctx.guild_id))
        await ctx.respond("Birthday channel set to {0} {1}".format(channel.mention, Emotes.DRINKING), ephemeral=True)
        logger.info("Counting channel set", guild_id=ctx.guild_id, channel_id=channel.id)

    @commands.slash_command(name='birthday', description="Set your birthday")
    async def set_birthday(self, ctx: discord.ApplicationContext,
                           day: discord.Option(int, "Enter day of the month (as integer)",
                                               min_value=0, max_value=31, required=True),
                           month: discord.Option(str, "Enter month of the year", required=True,
                                                 choices=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])) -> None:
        db.single_SQL("INSERT INTO Birthdays (GuildID, UserID, Birthdate) VALUES (%s, %s, %s) ON CONFLICT " +
                      "(GuildID, UserID) DO UPDATE SET Birthdate=%s",
                      (ctx.guild.id, ctx.author.id, month + str(day), month + str(day)))
        await ctx.respond(ctx.author.mention + " your birthday is set to {0} {1} {2}"
                          .format(day, month, Emotes.UWU))
        logger.info("Birthday set", member_id=ctx.author.id)

    @commands.slash_command(name='show_birthdays', description="Shows all tracked birthdays for the server")
    @discord.commands.default_permissions(manage_guild=True)
    async def show_birthdays(self, ctx: discord.ApplicationContext):
        vals = db.single_SQL("SELECT UserID, Birthdate from Birthdays WHERE GuildID=%s", (ctx.guild_id,))
        if vals:
            out_str = "\n".join([(await self.bot.fetch_user(user[0])).mention + " : " + user[1] for user in vals])
        else:
            out_str = "No users have entered their birthday yet! Get started with " + self.set_birthday.mention
        embed = discord.Embed(title="Birthday List", description=out_str)
        await ctx.respond(embed=embed)

    @tasks.loop(time=TIME)  # 1 behind curr time
    async def daily_bday(self) -> None:
        """
        Called daily to check for, and congratulate birthdays to birthday channel
        """
        logger.info("Starting daily birthday loop")
        today = dt.date.today().strftime("%b%e").replace(" ", "")
        val = db.single_SQL("SELECT BirthdayChannelID, string_agg(UserID::varchar, \' \') FROM Birthdays " +
                            "INNER JOIN Guilds ON Birthdays.GuildID=Guilds.ID WHERE Birthdays.Birthdate=%s " +
                            "GROUP BY ID;", (today,))
        for guild in val:
            users = " ".join([(await self.bot.fetch_user(int(user))).mention for user in guild[1].split(" ")])
            if guild[0]:
                logger.debug("Attempting to send birthday message", channel_id=guild[0])
                try:
                    await (await self.bot.fetch_channel(guild[0]))\
                        .send("Happy Birthday to: " + users +
                              "!\nHope you have a brilliant day {0}".format(Emotes.HEART))
                except discord.errors.Forbidden:
                    logger.warning("Failed to send birthday message", channel_id=guild[0])
                    # silently fail if no perms, TODO setup logging channel
                    pass


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Birthdays(bot))
