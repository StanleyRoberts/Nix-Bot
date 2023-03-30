import discord
import sys
from os import listdir
from discord.ext import commands

import helpers.database as db
from helpers.env import TOKEN, shutdown_db
from helpers.logger import Logger, Priority


intents = discord.Intents(messages=True, message_content=True,
                          guilds=True, members=True)
bot = commands.Bot(intents=intents, command_prefix='%s',
                   activity=discord.Game(name="/help"))


logger = Logger()
logger.set_bot(bot)


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
    db.single_SQL("DELETE FROM Subreddits WHERE SubredditChannelID=%s", (channel.id,))


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
    logger.info('Logged in', member_id=bot.user.id)


def main():
    if __debug__:
        db.populate()
        try:
            priority = Priority[sys.argv[1].upper()].name
            logger.set_priority(priority)
        except IndexError:
            logger.info("No logging level set, defaulting to all")
    else:
        logger.debug_mode = False
        logger.set_priority("WARNING")

    cogs = [cog[:-3] for cog in listdir('./src/cogs') if cog[-3:] == ".py" and cog != "__init__.py"]
    for cog in cogs:
        bot.load_extension(f'cogs.{cog}')

    try:
        bot.run(TOKEN)
    except KeyboardInterrupt:
        logger.warning("Keyboard interrupt: Failed to shutdown")
    finally:
        shutdown_db()
        logger.info("Bot succesfully shutdown")


if __name__ == "__main__":
    main()
