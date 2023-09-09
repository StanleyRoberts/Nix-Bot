import discord
from discord.ext import commands, tasks

import helpers.database as db
from helpers.style import Emotes, Colours, TIME
import reddit.ui_kit as ui
from reddit.interface import RedditInterface
from helpers.logger import Logger

logger = Logger()


class Reddit(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        self.daily_post.start()

    @discord.commands.option("time", type=str, default="day", description="Time period to search for top posts",
                             choices=["month", "hour", "week", "all", "day", "year"])
    @commands.slash_command(name='reddit', description="Displays a random top reddit post from the given subreddit")
    async def send_reddit_post(self, ctx: discord.ApplicationContext, subreddit: str, time: str):
        logger.debug("Getting reddit post", member_id=ctx.user.id, channel_id=ctx.channel_id)
        reddit = RedditInterface(subreddit, time)
        post = await reddit.get_post()
        await ctx.interaction.response.send_message(content=post.text, files=post.img, view=ui.PostViewer(reddit))

    @discord.commands.option("channel", type=discord.TextChannel, required=False)
    @commands.slash_command(name='subscribe', description="Subscribe to a subreddit to get daily posts from it")
    @discord.commands.default_permissions(manage_guild=True)
    async def subscribe_to_sub(self, ctx: discord.ApplicationContext, sub: str, channel: discord.TextChannel) -> None:
        if not channel:
            channel = ctx.channel

        if not await RedditInterface.valid_sub(sub):
            logger.warning(f"Subreddit {sub} is not valid", guild_id=ctx.guild_id)
            await ctx.respond(f"The subreddit {sub} is not available {Emotes.EVIL}")
        elif (sub.lower(),) in db.single_SQL("SELECT Subreddit FROM Subreddits WHERE GuildID=%s", (ctx.guild_id,)):
            logger.warning(f"Subreddit {sub} was already subscribed to",
                           guild_id=ctx.guild_id, channel_id=channel.id)
            await ctx.respond(f"This server is already subscribed to {sub} {Emotes.SUPRISE}")
        else:
            logger.info(f"Subreddit {sub} got subscribed to", guild_id=ctx.guild_id, channel_id=channel.id)
            db.single_void_SQL("INSERT INTO Subreddits (GuildID, Subreddit, SubredditChannelID) VALUES (%s, %s, %s)",
                               (ctx.guild_id, sub.lower(), channel.id))
            await ctx.respond(f"This server is now subscribed to {sub} {Emotes.HUG}")

    @discord.commands.option("sub", type=str, required=False)
    @ commands.slash_command(name='unsubscribe', description="Unsubscribe to daily posts from the given subreddit")
    @ discord.commands.default_permissions(manage_guild=True)
    async def unsubscribe_from_sub(self, ctx: discord.ApplicationContext, sub: str) -> None:
        if not sub:
            await self.get_subs(ctx)
            return
        if (sub.lower(),) not in db.single_SQL("SELECT Subreddit FROM Subreddits WHERE GuildID=%s", (ctx.guild_id,)):
            logger.warning(f"Subreddit {sub} was never subscribed to", guild_id=ctx.guild_id)
            await ctx.respond(f"This server is not subscribed to r/{sub} {Emotes.SUPRISE}")
        else:
            logger.info(f"Subreddit {sub} was unsubscribed from",
                        guild_id=ctx.guild_id, channel_id=ctx.channel_id)
            db.single_void_SQL("DELETE FROM Subreddits WHERE GuildID=%s AND Subreddit=%s ", (ctx.guild_id, sub))
            await ctx.respond(f"This server is now unsubscribed from r/{sub} {Emotes.SNEAKY}")

    @commands.slash_command(name='subscriptions', description="Get a list of the subscriptions of the server")
    async def get_subs(self, ctx: discord.ApplicationContext) -> None:
        subscriptions = db.single_SQL("SELECT Subreddit FROM Subreddits WHERE GuildID=%s", (ctx.guild_id,))
        logger.info("The list of subscripted subreddits was requested",
                    guild_id=ctx.guild_id, channel_id=ctx.channel_id)
        desc = "You have not subscribed to any subreddits yet\nGet started with {0}!".format(
            self.bot.get_application_command("subscribe").mention)
        if subscriptions:
            desc = "\n".join(["> " + sub[0] for sub in subscriptions])
        embed = discord.Embed(
            title="Subscriptions",
            description=desc,
            colour=Colours.PRIMARY)
        await ctx.respond(embed=embed)

    @tasks.loop(time=TIME)
    async def daily_post(self) -> None:
        """
        Called daily to print random post from subbed sub to linked discord channel
        """
        logger.info("Starting daily reddit loop")
        subs = db.single_SQL("SELECT GuildID, Subreddit, SubredditChannelID FROM Subreddits")
        for entry in subs:
            logger.info(f"Attempting to send reddit daily post <subreddit: {entry[1]}>",
                        guild_id=entry[0], channel_id=entry[2])
            try:
                post = await RedditInterface.single_post(entry[1], "day")
                channel = await self.bot.fetch_channel(entry[2])
                if not isinstance(channel, discord.abc.Messageable):
                    logger.error("reddit daily post channel is not sendable")
                    continue
                await channel.send("__Daily post__\n" + post.text, files=post.img)
            except discord.errors.Forbidden:
                logger.info("Permission failure for daily reddit post <subreddit: {0}>".format(
                    entry[1]), guild_id=entry[0], channel_id=entry[2])
                pass  # silently fail if no perms, TODO setup logging channel


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Reddit(bot))
