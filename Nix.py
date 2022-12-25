import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

import functions.database as db
from functions.style import Colours

if __debug__:
    load_dotenv()

TOKEN = os.getenv('TOKEN')  # Discord Token
CLIENT_ID = os.getenv('CLIENT_ID')  # PRAW/Reddit API client ID
SECRET_KEY = os.getenv('SECRET_KEY')  # PRAW/Reddit API secret key
USER_AGENT = os.getenv('USER_AGENT')  # PRAW/Reddit API user agent
NINJA_API_KEY = os.getenv('NINJA_API_KEY')  # X-API-Key for API-Ninjas
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL db
HF_API = os.getenv('HF_API')  # HuggingFace API key


if __debug__:
    import testing.postgresql
    postgres = testing.postgresql.Postgresql()
    DATABASE_URL = postgres.url()

intents = discord.Intents(messages=True, message_content=True,
                          guilds=True, members=True)
bot = commands.Bot(intents=intents, command_prefix='%s',
                   activity=discord.Game(name="/help"))


@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    """
    Called on Nix joining guild to setup database entries

    Args:
        guild (discord.Guild): Guild that triggered the event
    """
    db.single_SQL("INSERT INTO Guilds (ID, CountingChannelID, BirthdayChannelID, " +
                  "FactChannelID, CurrentCount, LastCounterID, HighScoreCounting, FailRoleID)" +
                  " VALUES (%s, NULL, NULL, NULL, 0, NULL, 0, NULL);", (guild.id,))


@bot.event
async def on_guild_remove(guild: discord.Guild) -> None:
    """
    Called when Nix leaves (or is kicked from) a guild to delete database entries

    Args:
        guild (discord.Guild): Guild that triggered the event
    """
    db.single_SQL("DELETE FROM Guilds WHERE ID=%s", (guild.id,))
    db.single_SQL("DELETE FROM Birthdays WHERE GuildID=%s", (guild.id,))
    db.single_SQL("DELETE FROM Subreddits WHERE GuildID=%s", (guild.id,))


@bot.event
async def on_guild_channel_delete(channel: discord.TextChannel) -> None:
    """
    Called when guild channel is deleted, to delete hanging database entries

    Args:
        channel (discord.Channel): Channel that triggered the event
    """
    db.single_SQL(
        "DELETE FROM Subreddits WHERE SubredditChannelID=%s", (channel.id,))


@bot.event
async def on_member_remove(member: discord.Member) -> None:
    """
    Called when member leaves guild, to delete database entries

    Args:
        member (discord.Member): Member that triggered the event
    """
    db.single_SQL("DELETE FROM Birthdays WHERE GuildID=%s AND UserID=%s",
                  (member.guild.id, member.id))


@bot.event
async def on_ready() -> None:
    print('We have logged in as {0.user}'.format(bot))

if __name__ == "__main__":
    if __debug__:
        db.populate()
    cogs = ['birthdays', 'facts', 'counting', 'reddit', 'misc', 'nlp']
    for cog in cogs:
        bot.load_extension(f'cogs.{cog}')
    bot.run(TOKEN)
