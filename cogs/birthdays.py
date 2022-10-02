import discord
from discord.ext import commands
from functions.helpers import single_SQL


class Birthdays(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='set_birthday_channel', description="Sets the channel for the birthday messages")
    @discord.commands.default_permissions(manage_guild=True)
    async def set_counting_channel(self, ctx, channel: discord.TextChannel):
        single_SQL("UPDATE Guilds SET BirthdayChannelID={0} WHERE ID={1}".format(channel.id, ctx.guild_id))
        await ctx.respond("Birthday channel set to {0}".format(channel))

    @commands.slash_command(name='birthday', description="Set your birthday")
    async def set_birthday(self, ctx,
                           day: discord.Option(int, "Enter day of the month (as integer)", min_value=0, max_value=31, required=True),
                           month: discord.Option(str, "Enter month of the year", required=True,
                                                 choices=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])):
        single_SQL("INSERT OR REPLACE INTO Birthdays (GuildID, UserID, Birthdate) VALUES ({0}, {1}, \'{2}\')".format(ctx.guild.id, ctx.author.id, month+str(day)))
        await ctx.respond(ctx.author.mention+" your birthday is set to {0} {1}".format(day, month))

def setup(bot):
    bot.add_cog(Birthdays(bot))