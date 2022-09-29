import discord
import requests
import json, random, os
import praw, prawcore
from discord.ext import commands
from dotenv import load_dotenv

### CONSTANTS ###

load_dotenv()

TOKEN = os.getenv('TOKEN') # Discord Token
API_KEY = os.getenv('API_KEY') # X-API-Key for API-Ninjas
CLIENT_ID = os.getenv('CLIENT_ID') # PRAW/Reddit API client ID
SECRET_KEY = os.getenv('SECRET_KEY') # PRAW/Reddit API secret key
USER_AGENT = os.getenv('USER_AGENT') #PRAW/Reddit API user agent
USERNAME = "WatchingRacoons" # reddit account username
PASSWORD = os.getenv('PASSWORD') # reddit account password

intents = discord.Intents(messages=True, guilds=True, members=True)
bot = commands.Bot(intents=intents, command_prefix='?') # Change to Bot rather than Client

reddit_read_only = praw.Reddit(client_id = CLIENT_ID,
                               client_secret = SECRET_KEY,
                               user_agent= USER_AGENT)

reddit_authorized = praw.Reddit(client_id = CLIENT_ID,         
                                client_secret = SECRET_KEY, 
                                user_agent= USER_AGENT,        
                                username=USERNAME,    
                                password=PASSWORD) 

### Customisable variables ###

prefix = '!'
allowed_channels = ['🤖-bot-commands', 'testing-of-the-bot🤖']

### Command Functions ###

def give_meme(message):
    subr = message[1]
    time = message[2] if len(message)>=3 else "all" # message[2] needs sanity check (hahahha same)
    try:
        subreddit = reddit_read_only.subreddit(subr)
        posts = subreddit.top(time)
        memes = [post for post in posts]
    except prawcore.exceptions.Redirect:
        return "Subreddit \'"+subr+" \' not found"
    except prawcore.exceptions.NotFound:
        return "Subreddit \'"+subr+"\' banned"
    except prawcore.exceptions.Forbidden:
        return "Subreddit \'"+subr+"\' private"

    meme = random.choice(memes) 

    if meme.is_self:
        link = meme.selftext
    else:
        link = meme.url
    return "***"+meme.title+"***\n"+link

def give_fact():
    api_url = 'https://api.api-ninjas.com/v1/facts?limit={}'.format(1)
    response = requests.get(api_url, headers={'X-Api-Key': API_KEY})
    if response.status_code == requests.codes.ok:
        cjson = json.loads(response.text)
        return cjson[0]["fact"]
    return "Error: "+response.status_code+"\n"+response.text

def give_quote():
    response = requests.get("https://inspirobot.me/api?generate=true")
    return response.text

def parse_command(message):
    match message[0][1:]:
        case 'quote': return give_quote()
        case 'annoystan': return '<@107523639410180096>'
        case 'meme': return give_meme(message)
        case 'fact': return give_fact()
        case _: return "Unknown command"

### Client Event Handlers ###

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

@bot.event
async def on_message(msg):
    username = str(msg.author).split('#')[0]
    user_message = str(msg.content)
    channel = str(msg.channel.name)
    print(f'{username}: {user_message} ({channel})')

    if msg.author == bot.user:
        return

    message = user_message.lower().split()
    if msg.channel.name in allowed_channels and message[0][0] == prefix:
        response = parse_command(message)
        await msg.channel.send(response)

if __name__ == "__main__":     
    bot.run(TOKEN)