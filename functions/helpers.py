import sqlite3, requests, json, random
import asyncpraw as praw, asyncprawcore as prawcore
from discord.ext import commands
import discord

from Nix import API_KEY, CLIENT_ID, SECRET_KEY, USER_AGENT


def single_SQL(query, values):
    con = sqlite3.connect("server_data.db")
    cur = con.cursor()
    cur.execute(query, values)
    val = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return val

def get_fact():
    api_url = 'https://api.api-ninjas.com/v1/facts?limit={}'.format(1)
    response = requests.get(api_url, headers={'X-Api-Key': API_KEY})
    message = "Error: "+str(response.status_code)+"\n"+response.text
    if response.status_code == requests.codes.ok:
        cjson = json.loads(response.text)
        message = cjson[0]["fact"]
    return message

def get_quote():
    return requests.get("https://inspirobot.me/api?generate=true").text

async def get_reddit_post(subreddit, time):
    reddit = praw.Reddit(client_id = CLIENT_ID,         
                         client_secret = SECRET_KEY, 
                         user_agent= USER_AGENT,) 
    response = "<:NixWTF:930448654588850176> Unknown error searching for subreddit"+subreddit
    try:
        subr = await reddit.subreddit(subreddit)
        subm = random.choice([post async for post in subr.top(time_filter=time, limit=100)])
        link = subm.selftext if subm.is_self else subm.url
        response = "***"+subm.title+"***\n"+link
    except prawcore.exceptions.Redirect:
        response = "<:NixWTF:930448654588850176> Subreddit \'"+subreddit+" \' not found"
    except prawcore.exceptions.NotFound:
        response = "<:NixWTF:930448654588850176> Subreddit \'"+subreddit+"\' banned"
    except prawcore.exceptions.Forbidden:
        response = "<:NixWTF:930448654588850176> Subreddit \'"+subreddit+"\' private"
    return response

async def clearLosers():
    gandR = single_SQL("SELECT ID, LoserRoleID FROM Guilds")
    for g in gandR:
        for user in commands.get_guild(g[0]).get_role(g[1]).members: #For all users with the role
            await user.remove_roles(commands.get_guild(g[0]).get_role(g[1])) #Remove the role

async def fail(msg, err_txt, roleID):
    single_SQL("UPDATE Guilds SET CurrentCount=0, LastCounterID=NULL WHERE ID=?", (msg.guild.id,))
    await msg.add_reaction('<:NixCrying:930297358590304286>')
    await msg.channel.send(err_txt)
    if roleID:
        try:
            await msg.author.add_roles(msg.guild.get_role(roleID))
        except discord.errors.Forbidden:
            await msg.channel.send("<:NixConfused:929938576655925258> Whoops! I couldn't set the {0} role (I need 'Manage Roles' to do that).\nI won't try again until you set a new fail role".format(msg.guild.get_role(roleID).mention))
            single_SQL("UPDATE Guilds SET FailRoleID=NULL WHERE ID=?", (msg.guild.id,))
