import discord
import os, requests
from discord.ext import commands
from dotenv import load_dotenv
import functions.database as db


### CONSTANTS ###

HEROKU = os.getenv('HEROKU')
if not HEROKU:
    load_dotenv()

TOKEN = os.getenv('TOKEN') # Discord Token
CLIENT_ID = os.getenv('CLIENT_ID') # PRAW/Reddit API client ID
SECRET_KEY = os.getenv('SECRET_KEY') # PRAW/Reddit API secret key
USER_AGENT = os.getenv('USER_AGENT') #PRAW/Reddit API user agent
API_KEY = os.getenv('API_KEY') # X-API-Key for API-Ninjas
DATABASE_URL = os.getenv('DATABASE_URL') # PostgreSQL db

if not HEROKU:
    import testing.postgresql
    postgres = testing.postgresql.Postgresql()
    DATABASE_URL = postgres.url()

intents = discord.Intents(messages=True, message_content=True, guilds=True, members = True)
bot = commands.Bot(intents=intents, command_prefix='%s', activity=discord.Game(name="/help"))


### Command Functions ###

@bot.slash_command(name='quote', description="Displays an AI-generated quote over an inspirational image")
async def send_quote(ctx):
    await ctx.respond(requests.get("https://inspirobot.me/api?generate=true").text)

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
    

### Client Event Handlers ###

@bot.event
async def on_guild_join(guild):
    db.single_SQL("INSERT INTO Guilds (ID, CountingChannelID, BirthdayChannelID, FactChannelID, CurrentCount, LastCounterID, HighScoreCounting, FailRoleID) VALUES (%s, NULL, NULL, NULL, 0, NULL, 0, NULL);", (guild.id,))

@bot.event
async def on_guild_remove(guild):
    db.single_SQL("DELETE FROM Guilds WHERE ID=%s", (guild.id,))
    db.single_SQL("DELETE FROM Birthdays WHERE GuildID=%s", (guild.id,))

@bot.event
async def on_member_remove(member):
    db.single_SQL("DELETE FROM Birthdays WHERE GuildID=%s AND UserID=%s", (member.guild.id, member.id))

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

if __name__ == "__main__":
    if not HEROKU: db.populate()
    cogs = ['birthdays', 'facts', 'counting', 'reddit']
    for cog in cogs:
        bot.load_extension(f'cogs.{cog}')
    bot.run(TOKEN)