import discord
from discord.ext import commands, tasks
import functions.database as db
from functions.style import Emotes, Colours, TIME
import reddit.ui_kit as ui
from reddit.interface import RedditInterface


class Reddit(commands.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        self.daily_post.start()

    @commands.slash_command(name='reddit', description="Displays a random top reddit post from the given subreddit")
    async def send_reddit_post(self, ctx: discord.ApplicationContext, subreddit: str,
                               time: discord.Option(str, default="day",
                                                    choices=["month", "hour", "week", "all", "day", "year"],
                                                    description="Time period to search for top posts")):
        reddit = RedditInterface(subreddit, time)
        post = await reddit.get_post()
        await ctx.interaction.response.send_message(content=post.text, files=post.img, view=ui.PostViewer(reddit))

    @commands.slash_command(name='subscribe', description="Subscribe to a subreddit to get daily posts from it")
    @discord.commands.default_permissions(manage_guild=True)
    async def subscribe_to_sub(self, ctx: discord.ApplicationContext, sub: str,
                               channel: discord.Option(discord.TextChannel, required=False)) -> None:
        if not channel:
            channel = ctx.channel

        if not await RedditInterface.valid_sub(sub):
            await ctx.respond("The subreddit {0} is not available {1}".format(sub, Emotes.EVIL))
        elif (sub.lower(),) in db.single_SQL("SELECT Subreddit FROM Subreddits WHERE GuildID=%s", (ctx.guild_id,)):
            await ctx.respond("This server is already subscribed to {0} {1}".format(sub.lower(), Emotes.SUPRISE))
        else:
            db.single_SQL("INSERT INTO Subreddits (GuildID, Subreddit, SubredditChannelID) VALUES (%s, %s, %s)",
                          (ctx.guild_id, sub, channel.id))
            await ctx.respond("This server is now subscribed to {0} {1}".format(sub, Emotes.HUG))

    @commands.slash_command(name='unsubscribe', description="Unsubscribe to daily posts from the given subreddit")
    @discord.commands.default_permissions(manage_guild=True)
    async def unsubscribe_from_sub(self, ctx: discord.ApplicationContext, sub: discord.Option(required=False)) -> None:
        if not sub:
            await self.get_subs(ctx)
            return
        if (sub.lower(),) not in db.single_SQL("SELECT Subreddit FROM Subreddits WHERE GuildID=%s", (ctx.guild_id,)):
            await ctx.respond("This server is not subscribed to r/{0} {1}".format(sub, Emotes.SUPRISE))
        else:
            db.single_SQL("DELETE FROM Subreddits WHERE GuildID=%s AND Subreddit=%s ", (ctx.guild_id, sub))
            await ctx.respond("This server is now unsubscribed from {0} {1}".format(sub, Emotes.SNEAKY))

    @commands.slash_command(name='subscriptions', description="Get a list of the subscriptions of the server")
    async def get_subs(self, ctx: discord.ApplicationContext) -> None:
        subscriptions = db.single_SQL("SELECT Subreddit FROM Subreddits WHERE GuildID=%s", (ctx.guild_id,))

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
        subs = db.single_SQL("SELECT GuildID, Subreddit, SubredditChannelID FROM Subreddits")
        for entry in subs:
            try:
                post = await RedditInterface.single_post(entry[1], "day")
                await (await self.bot.fetch_channel(entry[2])).send("__Daily post__\n" +
                                                                    post.text, files=post.img)
            except discord.errors.Forbidden:
                pass  # silently fail if no perms, TODO setup logging channel


def setup(bot: discord.Bot) -> None:
    bot.add_cog(Reddit(bot))
