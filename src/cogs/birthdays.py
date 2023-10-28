import discord
import datetime as dt
from discord.ext import commands, tasks

import helpers.database as db
from helpers.style import Emotes, Colours, TIME, RESET
from helpers.logger import Logger
logger = Logger()


class Birthdays(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        self.daily_bday.start()

    @commands.slash_command(name='set_birthday_channel', description="Sets the channel for the birthday messages")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_counting_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel) -> None:
        db.single_void_SQL("UPDATE Guilds SET BirthdayChannelID=%s WHERE ID=%s", (channel.id, ctx.guild_id))
        await ctx.respond(f"Birthday channel set to {channel.mention} {Emotes.DRINKING}", ephemeral=True)
        logger.info("Counting channel set", guild_id=ctx.guild_id, channel_id=channel.id)

    @discord.commands.option("day", type=int, description="Enter day of the month (as integer)", min_value=0,
                             max_value=31, required=True)
    @discord.commands.option("month", type=str, description="Enter month of the year",
                             choices=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], required=True)
    @commands.slash_command(name='birthday', description="Set your birthday")
    async def set_birthday(self, ctx: discord.ApplicationContext, day: int, month: str) -> None:
        db.single_void_SQL("INSERT INTO Birthdays (GuildID, UserID, Birthdate) VALUES (%s, %s, %s) ON CONFLICT " +
                           "(GuildID, UserID) DO UPDATE SET Birthdate=%s",
                           (ctx.guild.id, ctx.author.id, month + str(day), month + str(day)))
        await ctx.respond(f"{ctx.author.mention} your birthday is set to {day} {month} {Emotes.UWU}")
        logger.info("Birthday set", member_id=ctx.author.id)

    @ commands.slash_command(name='show_birthdays', description="Shows all tracked birthdays for the server")
    @ discord.commands.default_permissions(manage_guild=True)
    async def show_birthdays(self, ctx: discord.ApplicationContext) -> None:
        vals = db.single_SQL("SELECT UserID, Birthdate from Birthdays WHERE GuildID=%s", (ctx.guild_id,))
        if vals:
            out_str = "\n".join([(await self.bot.fetch_user(user[0])).mention + " : " + user[1] for user in vals])
        else:
            out_str = "No users have entered their birthday yet! Get started with " + self.set_birthday.mention
        embed = discord.Embed(title="Birthday List", description=out_str, color=Colours.PRIMARY)
        await ctx.respond(embed=embed)

    @tasks.loop(time=RESET)
    async def reset_fact(self) -> None:
        self.sent_today = False

    @ tasks.loop(time=TIME)
    async def daily_bday(self) -> None:
        """
        Called daily to check for, and congratulate birthdays to birthday channel
        """
        if self.sent_today:
            return
        self.sent_today = True
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
                    channel = await self.bot.fetch_channel(guild[0])
                    if (not isinstance(channel, discord.abc.Messageable) or
                            isinstance(channel, discord.abc.PrivateChannel)):
                        logger.error("Birthday channel set to Private Channel", channel_id=channel.id)
                        continue
                    (await channel
                        .send("Happy Birthday to: " + users +
                              f"!\nHope you have a brilliant day {Emotes.HEART}"))
                except discord.errors.Forbidden:
                    logger.info("Permission failure for sending birthday message", channel_id=guild[0])
                    # silently fail if no perms, TODO setup logging channel
                    pass


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Birthdays(bot))
