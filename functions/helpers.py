import psycopg2, requests, json, random
import asyncpraw as praw, asyncprawcore as prawcore
from discord.ext import commands
import discord

from Nix import API_KEY, DATABASE_URL, HEROKU


def single_SQL(query, values=None):
    if HEROKU:
        con = psycopg2.connect(DATABASE_URL)
    else:
        con = psycopg2.connect(**DATABASE_URL)
    cur = con.cursor()
    cur.execute(query, values)
    val = None
    if cur.description:
        val = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return val

def populate():
    con = psycopg2.connect(**DATABASE_URL)   
    cur = con.cursor()
    cur.execute("CREATE TABLE Guilds(ID BIGINT, CountingChannelID BIGINT, BirthdayChannelID BIGINT, FactChannelID BIGINT, CurrentCount INTEGER, LastCounterID BIGINT, HighScoreCounting INTEGER, FailRoleID BIGINT, PRIMARY KEY(ID));")
    cur.execute("CREATE TABLE Birthdays(GuildID BIGINT, UserID BIGINT, Birthdate TEXT, FOREIGN KEY(GuildID) REFERENCES Guilds(ID), PRIMARY KEY(GuildID, UserID));")
    cur.execute("INSERT INTO Guilds (ID, CountingChannelID, BirthdayChannelID, FactChannelID, CurrentCount, LastCounterID, HighScoreCounting, FailRoleID) VALUES (821016940462080000, NULL, NULL, NULL, 0, NULL, 0, NULL);")
    cur.execute("CREATE TABLE subreddits(GuildID BIGINT, subreddit TEXT, SubredditChannelID BIGINT, PRIMARY KEY(GuildID, subreddit));")
    con.commit()
    cur.close()
    con.close()

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

async def clearLosers():
    gandR = single_SQL("SELECT ID, LoserRoleID FROM Guilds")
    for g in gandR:
        for user in commands.get_guild(g[0]).get_role(g[1]).members: #For all users with the role
            await user.remove_roles(commands.get_guild(g[0]).get_role(g[1])) #Remove the role

async def fail(msg, err_txt, roleID):
    single_SQL("UPDATE Guilds SET CurrentCount=0, LastCounterID=NULL WHERE ID=%s", (msg.guild.id,))
    await msg.add_reaction('<:NixCrying:1026494029002723398>')
    await msg.channel.send(err_txt)
    if roleID:
        try:
            await msg.author.add_roles(msg.guild.get_role(roleID))
        except discord.errors.Forbidden:
            await msg.channel.send("<:NixConfused:1026494027727638599> Whoops! I couldn't set the {0} role (I need 'Manage Roles' to do that).\nI won't try again until you set a new fail role".format(msg.guild.get_role(roleID).mention))
            single_SQL("UPDATE Guilds SET FailRoleID=NULL WHERE ID=%s", (msg.guild.id,))