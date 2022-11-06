import discord
import random
from discord.ext import commands, tasks
import asyncpraw as praw
import asyncprawcore as prawcore
import functions.database as db
from functions.style import Emotes, Colours, TIME
from Nix import CLIENT_ID, SECRET_KEY, USER_AGENT


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reddit = praw.Reddit(client_id=CLIENT_ID,
                                  client_secret=SECRET_KEY,
                                  user_agent=USER_AGENT,)
        self.daily_post.start()

    @commands.slash_command(name='reddit', description="Displays a random top reddit post from the given subreddit")
    async def send_reddit_post(self, ctx, subreddit,
                               time: discord.Option(str, default="day",
                                                    choices=[
                                                        "month", "hour", "week", "all", "day", "year"],
                                                    description="Time period to search for top posts")):
        await ctx.respond(await self.get_reddit_post(subreddit, time))

    @commands.slash_command(name='subscribe', description="Subscribe to a subreddit to get daily posts from it")
    @discord.commands.default_permissions(manage_guild=True)
    async def subscribe_to_sub(self, ctx, sub, channel: discord.Option(discord.TextChannel, required=False)):
        if not channel:
            channel = ctx.channel
        try:
            # Needed to check if subreddit exists
            [post async for post in (await self.reddit.subreddit(sub)).top(time_filter="day", limit=1)][0]
            db.single_SQL("INSERT INTO Subreddits (GuildID, Subreddit, SubredditChannelID) VALUES (%s, %s, %s)",
                          (ctx.guild_id, sub, channel.id))  # Add subscription to SQL
            await ctx.respond("This server is now subscribed to {0} {1}".format(sub, Emotes.HUG))

        except prawcore.exceptions.AsyncPrawcoreException:  # Can´t find subreddit exception
            await ctx.respond("The subreddit {0} is not available {1}}".format(sub, Emotes.EVIL))

        except db.KeyViolation:
            await ctx.respond("This server is already subscribed to {0} {1}".format(sub, Emotes.SUPRISE))

    @commands.slash_command(name='unsubscribe', description="Unsubscribe to daily posts from the given subreddit")
    @discord.commands.default_permissions(manage_guild=True)
    async def unsubscribe_from_sub(self, ctx, sub: discord.Option(required=False)):
        if not sub:
            await self.getSubs(ctx)
            return
        if sub not in db.single_SQL("SELECT Subreddit FROM Subreddits WHERE GuildID=%s", (ctx.guild_id,)):
            await ctx.respond("This server is not subscribed to r/{0} {1}".format(sub, Emotes.SUPRISE))
        else:
            db.single_SQL("DELETE FROM Subreddits WHERE GuildID=%s AND Subreddit=%s ",
                          (ctx.guild_id, sub))  # Delete the subscription out of the SQL
            await ctx.respond("This server is now unsubscribed from {0} {1}".format(sub, Emotes.SNEAKY))

    @commands.slash_command(name='subscriptions', description="Get a list of the subscriptions of the server")
    async def get_subs(self, ctx):
        subscriptions = db.single_SQL(
            "SELECT Subreddit FROM Subreddits WHERE GuildID=%s", (ctx.guild_id,))

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
    async def daily_post(self):
        """
        Called daily to print random post from subbed sub to linked discord channel
        """
        subs = db.single_SQL(
            "SELECT GuildID, Subreddit, SubredditChannelID FROM Subreddits")
        for entry in subs:
            # Go through the SQL and post the requested post in the chosen channel
            await (await self.bot.fetch_channel(entry[2])).send("Daily post (" + entry[1] + ")\n" +
                                                                (await self.get_reddit_post(entry[1], "day")))

    @staticmethod
    async def get_reddit_post(self, subreddit, time):
        """
        Gets a random post (out of top 100) from a subreddit

        Args:
            subreddit (string): subreddit name to pull from
            time (string): time period to query (day, month, all, etc)

        Returns:
            string: reddit post, consisting of title and body in markdown format
        """
        response = "Unknown error searching for subreddit {0} {1}".format(
            Emotes.WTF, subreddit)
        try:
            subr = await self.reddit.subreddit(subreddit)
            subm = random.choice([post async for post in subr.top(time_filter=time, limit=100)])
            link = subm.selftext if subm.is_self else subm.url
            response = "***" + subm.title + "***\n" + link
        except prawcore.exceptions.Redirect:
            response = "{0} Subreddit \'".format(
                Emotes.WTF) + subreddit + " \' not found"
        except prawcore.exceptions.NotFound:
            response = "{0} Subreddit \'".format(
                Emotes.WTF) + subreddit + "\' banned"
        except prawcore.exceptions.Forbidden:
            response = "{0} Subreddit \'".format(
                Emotes.WTF) + subreddit + "\' private"
        return response


def setup(bot):
    bot.add_cog(Reddit(bot))
