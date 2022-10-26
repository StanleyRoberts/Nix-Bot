import discord
import os
import openai
import requests
from discord.ext import commands
from dotenv import load_dotenv
import functions.database as db
from functions.style import Colours


HEROKU = os.getenv('HEROKU')
if not HEROKU:
    load_dotenv()

TOKEN = os.getenv('TOKEN')  # Discord Token
CLIENT_ID = os.getenv('CLIENT_ID')  # PRAW/Reddit API client ID
SECRET_KEY = os.getenv('SECRET_KEY')  # PRAW/Reddit API secret key
USER_AGENT = os.getenv('USER_AGENT')  # PRAW/Reddit API user agent
NINJA_API_KEY = os.getenv('NINJA_API_KEY')  # X-API-Key for API-Ninjas
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL db
AI_API_KEY = os.getenv('AI_API_KEY')  # OpenAI API key

if not HEROKU:
    import testing.postgresql
    postgres = testing.postgresql.Postgresql()
    DATABASE_URL = postgres.url()

intents = discord.Intents(messages=True, message_content=True,
                          guilds=True, members=True)
bot = commands.Bot(intents=intents, command_prefix='%s',
                   activity=discord.Game(name="/help"))


@bot.slash_command(name='quote',
                   description="Displays an AI-generated quote over an inspirational image")
async def send_quote(ctx):
    await ctx.respond(requests.get("https://inspirobot.me/api?generate=true").text)


@bot.slash_command(name='talk')
async def talk(ctx, prompt):

    await ctx.respond("You asked: " + prompt)
    openai.api_key = AI_API_KEY
    start_sequence = "\nNix:"
    restart_sequence = "\nHuman: "

    response = openai.Completion.create(
        model="text-davinci-002",
        prompt="The following is a conversation with a phoenix named Nix. The phoenix is helpful, creative, " +
        "clever, and very friendly.\n\nHuman: Hello, who are you?\nNix: I am a phoenix made of fire. " +
        "How can I help you today?\nHuman: " + prompt,
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
        stop=[" Human:", " Nix:"]
    )
    test = str(response.choices[0].text)
    print(test)
    await ctx.respond(test)


@bot.slash_command(name='help', description="Displays the help page for NixBot")
async def display_help(ctx):
    desc = "Note: depending on your server settings and role permissions," + \
           " some of these commands may be hidden or disabled\n\n***Generic***\n" \
           + "".join(sorted([command.mention + " : " + command.description + "\n"
                             for command in bot.walk_application_commands() if not command.cog])) \
           + "".join(["\n***" + cog + "***\n" + "".join(sorted([command.mention + " : " + command.description + "\n"
                                                                for command in bot.cogs[cog].walk_commands()]))
                      for cog in bot.cogs])  # Holy hell
    embed = discord.Embed(title="Help Page", description=desc,
                          colour=Colours.PRIMARY)
    await ctx.respond(embed=embed)


@bot.event
async def on_guild_join(guild):
    """
    Called on Nix joining guild to setup database entries

    Args:
        guild (discord.Guild): Guild that triggered the event
    """
    db.single_SQL("INSERT INTO Guilds (ID, CountingChannelID, BirthdayChannelID, " +
                  "FactChannelID, CurrentCount, LastCounterID, HighScoreCounting, FailRoleID)"
                  " VALUES (%s, NULL, NULL, NULL, 0, NULL, 0, NULL);", (guild.id,))


@bot.event
async def on_guild_remove(guild):
    """
    Called when Nix leaves (or is kicked from) a guild to delete database entries

    Args:
        guild (discord.Guild): Guild that triggered the event
    """
    db.single_SQL("DELETE FROM Guilds WHERE ID=%s", (guild.id,))
    db.single_SQL("DELETE FROM Birthdays WHERE GuildID=%s", (guild.id,))
    db.single_SQL("DELETE FROM Subreddits WHERE GuildID=%s", (guild.id,))


@bot.event
async def on_guild_channel_delete(channel):
    """
    Called when guild channel is deleted, to delete hanging database entries

    Args:
        channel (discord.Channel): Channel that triggered the event
    """
    db.single_SQL(
        "DELETE FROM Subreddits WHERE SubredditChannelID=%s", (channel.id,))


@bot.event
async def on_member_remove(member):
    """
    Called when member leaves guild, to delete database entries

    Args:
        member (discord.Member): Member that triggered the event
    """
    db.single_SQL("DELETE FROM Birthdays WHERE GuildID=%s AND UserID=%s",
                  (member.guild.id, member.id))


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

if __name__ == "__main__":
    if not HEROKU:
        db.populate()
    cogs = ['birthdays', 'facts', 'counting', 'reddit']
    for cog in cogs:
        bot.load_extension(f'cogs.{cog}')
    bot.run(TOKEN)
