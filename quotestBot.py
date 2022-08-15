import discord
import requests
import json
import praw
import random
import prawcore

### CONSTANTS ###

TOKEN = 'OTc0NzY1NDI1Mjk4NjQ5MDk4.GGVRVj.r6Pzitvw3K0aTYKZTVR6s8mQwI-EvWq_t2GKiM'
API_KEY = 'PW28Q/V4PH0amKO/DbtbfQ==yR6f6tfRxigcL7uA'
CLIENT_ID = 'atOZU5hA9clYKG-oTZKNsA'
SECRET_KEY = 'bchDQT8bPriqN03okgKNSgppYWGq2Q'
USER_AGENT = 'atOZU5hA9clYKG-oTZKNsA'

intents = discord.Intents(messages=True, guilds=True, members=True)
client = discord.Client(intents=intents)

reddit_read_only = praw.Reddit(client_id = CLIENT_ID,
                               client_secret = SECRET_KEY,
                               user_agent= USER_AGENT)

reddit_authorized = praw.Reddit(client_id = CLIENT_ID,         
                                client_secret = SECRET_KEY, 
                                user_agent= USER_AGENT,        
                                username="WatchingRacoons",    
                                password="M3m3s4Disc") 

### Customisable variables ###

prefix = '!'
allowed_channels = ['🤖-bot-commands', 'testing-of-the-bot🤖']

### Command Functions ###

async def give_meme(message):
    subr = message[1]
    time = message[2] if len(message)>=3 else "all" # message[2] needs sanity check
    try:
        subreddit = await reddit_read_only.subreddit(subr)
        posts = subreddit.top(time)
        memes = [post for post in posts]
    except prawcore.exceptions.Redirect:
        return "Subreddit\'"+subr+"\' not found"
    except prawcore.exceptions.NotFound:
        return "Subreddit\'"+subr+"\' banned"
    except prawcore.exceptions.Forbidden:
        return "Subreddit\'"+subr+"\' private"

    meme = random.choice(memes) # this should work directly with 'posts' variable but i cant test it

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

async def parse_command(message):
    match message[0][1:]:
        case 'quote': return give_quote()
        case 'annoystan': return '<@107523639410180096>'
        case 'meme': return await give_meme()
        case 'fact': return give_fact()
        case _: return "Unknown command"

### Client Event Handlers ###

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(msg):
    username = str(msg.author).split('#')[0]
    user_message = str(msg.content)
    channel = str(msg.channel.name)
    print(f'{username}: {user_message} ({channel})')

    if msg.author == client.user:
        return

    message = user_message.lower().split()
    if msg.channel.name in allowed_channels and message[0][0] == prefix:
        response = parse_command(message)
        await msg.channel.send(response)

if __name__ == "__main__":     
    client.run(TOKEN)