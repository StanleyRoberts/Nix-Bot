import discord
from discord.ext import commands, tasks
import datetime as dt
import asyncpraw as praw
import asyncprawcore as prawcore
import random
import functions.database as db
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
            await ctx.respond("This server is now subscribed to {0} <:NixHug:1033423234370125904>".format(sub))

        except prawcore.exceptions.AsyncPrawcoreException:  # Can´t find subreddit exception
            await ctx.respond("The subreddit {0} is not available <:NixEvil:1033423155034849340>".format(sub))

        except db.KeyViolation:
            await ctx.respond("This server is already subscribed to {0} <:NixSuprise:1033423188937416704>".format(sub))
        print(db.single_SQL("SELECT * FROM Subreddits"))

    @commands.slash_command(name='unsubscribe', description="Unsubscribe to daily posts from the given subreddit")
    @discord.commands.default_permissions(manage_guild=True)
    async def unsubscribe_from_sub(self, ctx, sub):
        db.single_SQL("DELETE FROM Subreddits WHERE GuildID=%s AND Subreddit=%s ",
                      (ctx.guild_id, sub))  # Delete the subscription out of the SQL
        await ctx.respond("This server is now unsubscribed from {0} <:NixSneaky:1033423327320080485>".format(sub))

    @tasks.loop(time=dt.time(hour=9))
    async def daily_post(self):
        subs = db.single_SQL(
            "SELECT GuildID, Subreddit, SubredditChannelID FROM Subreddits")
        for entry in subs:
            # Go through the SQL and post the requested post in the chosen channel
            await (await self.bot.fetch_channel(entry[2])).send("Daily post (" + entry[1] + ")\n" +
                                                                (await self.get_reddit_post(entry[1], "day")))

    async def get_reddit_post(self, subreddit, time):
        response = "<:NixWTF:1026494030407806986> Unknown error searching for subreddit" + subreddit
        try:
            subr = await self.reddit.subreddit(subreddit)
            subm = random.choice([post async for post in subr.top(time_filter=time, limit=100)])
            link = subm.selftext if subm.is_self else subm.url
            response = "***" + subm.title + "***\n" + link
        except prawcore.exceptions.Redirect:
            response = "<:NixWTF:1026494030407806986> Subreddit \'" + subreddit + " \' not found"
        except prawcore.exceptions.NotFound:
            response = "<:NixWTF:1026494030407806986> Subreddit \'" + subreddit + "\' banned"
        except prawcore.exceptions.Forbidden:
            response = "<:NixWTF:1026494030407806986> Subreddit \'" + subreddit + "\' private"
        return response


def setup(bot):
    bot.add_cog(Reddit(bot))
