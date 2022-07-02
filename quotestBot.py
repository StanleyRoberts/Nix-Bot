import discord
import requests
import json
import datetime
from ctypes import sizeof
import praw
import random
import prawcore


TOKEN = 'OTc0NzY1NDI1Mjk4NjQ5MDk4.GGVRVj.r6Pzitvw3K0aTYKZTVR6s8mQwI-EvWq_t2GKiM'

CLIENT_ID = 'atOZU5hA9clYKG-oTZKNsA'
SECRET_KEY = 'bchDQT8bPriqN03okgKNSgppYWGq2Q'
USER_AGENT = 'atOZU5hA9clYKG-oTZKNsA'

prefix = '!'

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

async def getmeme(subr, time):
    subreddit = reddit_read_only.subreddit(subr)
    memes = subreddit.top(time)
    mem = []
    for post in memes:
        mem.append(post)
    meme = mem[random.randint(0, len(mem)-1)]
    if not meme.is_self:
        link = meme.url
    else:
        link = meme.selftext
    return (meme.title, link)

def last_monday():
    today = datetime.datetime.today()
    monday = today - datetime.timedelta(days=today.weekday())
    return monday

def memberlist(msg):
    guild = client.get_guild(msg.guild.id)
    mlist = []
    for i in guild.members:
        member_id = i.id
        mlist.append([member_id, 0])
    return mlist

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

def give_quote():
    response = requests.get("https://inspirobot.me/api?generate=true")
    return response

@client.event
async def on_message(msg):
    username = str(msg.author).split('#')[0]
    user_message = str(msg.content)
    channel = str(msg.channel.name)
    print(f'{username}: {user_message} ({channel})')

    if msg.author == client.user:
        return

    if msg.channel.name == '🤖-bot-commands' or msg.channel.name == 'testing-of-the-bot🤖':
        message = user_message.lower().split()
        if message[0][0] == prefix:
            print("prefix here")
            match message[0][1:]:
                case 'quote':
                    await msg.channel.send(give_quote().text)   
                case 'annoystan':
                    await msg.channel.send('<@107523639410180096>')
                    
                case 'activechange':
                        guild = client.get_guild(msg.guild.id)
                        mlist = memberlist(msg)
                        for m in mlist:
                            for i in guild.text_channels:
                                messages = await i.history(limit=None, before=None, after=last_monday()).flatten()
                                for j in messages:
                                    if j.author == guild.get_member(m[0]):
                                        m[1] +=  1
                            mem = guild.get_member(m[0])
                            active = discord.utils.get(mem.guild.roles, name='active')
                            Active = discord.utils.get(mem.guild.roles, name='Active')
                            if m[1] < 11:
                                if Active in mem.roles:
                                    await mem.remove_roles(Active)
                                    await mem.add_roles(active)                       
                                elif active in mem.roles:
                                    await mem.remove_roles(active)
                            else:
                                if Active in mem.roles:
                                    continue
                                elif active in mem.roles:
                                    await mem.remove_roles(active) 
                                    await mem.add_roles(Active)
                                else:
                                    await mem.add_roles(Active)
                        await msg.channel.send("done")
                case 'meme':
                    subr = message[1]
                    words = len(message)
                    if words >= 3:
                        time = message[2]
                    else:
                        time = "all"
                    try:
                        fun = await getmeme(subr, time)
                    except prawcore.exceptions.Redirect:
                        await msg.channel.send("Subreddit\'"+subr+"\' not found")
                    except prawcore.exceptions.NotFound:
                        await msg.channel.send("Subreddit\'"+subr+"\' banned")
                    except prawcore.exceptions.Forbidden:
                        await msg.channel.send("Subreddit\'"+subr+"\' private")
                    await msg.channel.send("***"+fun[0]+"***\n"+fun[1])
        return
if __name__ == "__main__":     
    client.run(TOKEN)