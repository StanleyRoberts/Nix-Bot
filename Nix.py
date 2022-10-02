import discord
import os
from discord.ext import tasks, commands
import datetime as dt
from dotenv import load_dotenv
import functions.helpers as helper


### CONSTANTS ###

load_dotenv()

TOKEN = os.getenv('TOKEN') # Discord Token
CLIENT_ID = os.getenv('CLIENT_ID') # PRAW/Reddit API client ID
SECRET_KEY = os.getenv('SECRET_KEY') # PRAW/Reddit API secret key
USER_AGENT = os.getenv('USER_AGENT') #PRAW/Reddit API user agent
API_KEY = os.getenv('API_KEY') # X-API-Key for API-Ninjas

intents = discord.Intents(messages=True, message_content=True, guilds=True)
bot = commands.Bot(intents=intents, command_prefix='?', activity=discord.Game(name="/help"))


### Command Functions ###

@bot.slash_command(name='reddit', description="Displays a random top reddit post from the given subreddit")
async def send_reddit_post(ctx, subreddit,
                           time: discord.Option(str, default="day",
                                                choices=["month", "hour", "week", "all", "day", "year"],
                                                description="Time period to search for top posts")):
    await ctx.respond(helper.get_reddit_post(subreddit, time))

@bot.slash_command(name='quote', description="Displays an AI-generated quote over an inspirational image")
async def send_quote(ctx):
    await ctx.respond(helper.get_quote())

@bot.slash_command(name='set_counting_channel', description="Sets the channel for the counting game")
@discord.commands.default_permissions(manage_guild=True)
async def set_counting_channel(ctx, channel: discord.TextChannel):
    helper.single_SQL("UPDATE Guilds SET CountingChannelID={0} WHERE ID={1}".format(channel.id, ctx.guild_id))
    await ctx.respond("Counting channel set to {0}".format(channel))

@bot.slash_command(name='help', description="Displays the help page for NixBot")
async def display_help(ctx):
    embed = discord.Embed(title="Help Page",
                          description = "Note: depending on your server settings and role permissions,"\
                          " some of these commands may be hidden or disabled\n\n# Generic\n"
                          +"".join(sorted([command.mention+" : "+command.description+"\n"
                                           for command in bot.walk_application_commands() if not command.cog]))\
                          +"".join(["\n# "+cog+"\n"+"".join(sorted([command.mention+" : "+command.description+"\n"
                                      for command in bot.cogs[cog].walk_commands()])) for cog in bot.cogs]))
    await ctx.respond(embed=embed)


### Looping Tasks ###

@tasks.loop(time=dt.time(hour=9), count=1) #1 behind curr time
async def daily_check():
    guilds = helper.single_SQL("SELECT FactChannelID FROM Guilds")
    fact = helper.get_fact()
    for factID in guilds:
        if factID:
            await bot.get_channel(factID[0]).send(fact)
    
    today=dt.date.today().strftime("%b%e").replace(" ", "")
    val = helper.single_SQL("SELECT BirthdayChannelID, group_concat(UserID, ' ') as UserID FROM Birthdays INNER JOIN Guilds ON Birthdays.GuildID=Guilds.ID WHERE Birthdays.Birthdate=\'{0}\'GROUP BY ID;".format(today))
    for guild in val:
        users = " ".join([(await bot.fetch_user(int(user))).mention for user in guild[1].split(" ")])
        if guild[0]:
            await bot.get_channel(guild[0]).send("Happy Birthday to: "+users+"!\nHope you have a brilliant day <:NixFire:1025434443642589305>")


### Client Event Handlers ###

@bot.event
async def on_guild_join(guild):
    helper.single_SQL("INSERT INTO Guilds (ID, CountingChannelID, BirthdayChannelID, FactChannelID) VALUES ({0}, NULL, NULL, NULL);".format(guild.id))

@bot.event
async def on_guild_leave(guild):
    helper.single_SQL("DELETE FROM Guilds WHERE ID={0}; DELETE FROM Birthdays WHERE GuildID={0}".format(guild.id))

@bot.event
async def on_member_remove(member):
    helper.single_SQL("DELETE FROM Birthdays WHERE GuildID={0} AND UserID={1}".format(member.guild.id, member.id))

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

if __name__ == "__main__":
    cogs = ['birthdays', 'facts']
    for cog in cogs:
        bot.load_extension(f'cogs.{cog}')
    daily_check.start() 
    bot.run(TOKEN)