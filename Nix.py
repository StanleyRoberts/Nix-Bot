import discord
import requests
import json, random, os
import asyncpraw as praw, prawcore
from dotenv import load_dotenv
import sqlite3

### CONSTANTS ###

load_dotenv()

TOKEN = os.getenv('TOKEN') # Discord Token
API_KEY = os.getenv('API_KEY') # X-API-Key for API-Ninjas
CLIENT_ID = os.getenv('CLIENT_ID') # PRAW/Reddit API client ID
SECRET_KEY = os.getenv('SECRET_KEY') # PRAW/Reddit API secret key
USER_AGENT = os.getenv('USER_AGENT') #PRAW/Reddit API user agent

intents = discord.Intents(messages=True, guilds=True, members=True)
bot = discord.Bot(intents=intents, command_prefix='?') # Change to Bot rather than Client

reddit = praw.Reddit(client_id = CLIENT_ID,         
                     client_secret = SECRET_KEY, 
                     user_agent= USER_AGENT,) 

### Command Functions ###

@bot.slash_command(name='reddit')
async def send_reddit_post(ctx, subreddit,
                           time: discord.Option(str, default="day",
                                                choices=["month", "hour", "week", "all", "day", "year"])):
    try:
        subr = await reddit.subreddit(subreddit)
        posts = [post async for post in subr.top(time_filter=time, limit=100)]
    except prawcore.exceptions.Redirect:
        return "Subreddit \'"+subr+" \' not found"
    except prawcore.exceptions.NotFound:
        return "Subreddit \'"+subr+"\' banned"
    except prawcore.exceptions.Forbidden:
        return "Subreddit \'"+subr+"\' private"

    subm = random.choice(posts)
    link = subm.selftext if subm.is_self else subm.url

    await ctx.respond("***"+subm.title+"***\n"+link)

@bot.slash_command(name='fact')
async def send_fact(ctx):
    api_url = 'https://api.api-ninjas.com/v1/facts?limit={}'.format(1)
    response = requests.get(api_url, headers={'X-Api-Key': API_KEY})
    message = "Error: "+str(response.status_code)+"\n"+response.text
    if response.status_code == requests.codes.ok:
        cjson = json.loads(response.text)
        message = cjson[0]["fact"]
    await ctx.respond(message)

@bot.slash_command(name='quote')
async def send_quote(ctx):
    response = requests.get("https://inspirobot.me/api?generate=true")
    await ctx.respond(response.text)


### Client Event Handlers ###

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

if __name__ == "__main__":     
    bot.run(TOKEN)