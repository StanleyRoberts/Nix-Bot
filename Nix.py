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

intents = discord.Intents(messages=True, message_content=True, guilds=True, members = True)
bot = discord.Bot(intents=intents, command_prefix='?')

reddit = praw.Reddit(client_id = CLIENT_ID,         
                     client_secret = SECRET_KEY, 
                     user_agent= USER_AGENT,) 


### Command Functions ###

@bot.slash_command(name='reddit', description="Displays a random top reddit post from the given subreddit")
async def send_reddit_post(ctx, subreddit,
                           time: discord.Option(str, default="day",
                                                choices=["month", "hour", "week", "all", "day", "year"],
                                                description="Time period to search for top posts")):
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

@bot.slash_command(name='fact', description="Displays a random fact")
async def send_fact(ctx):
    api_url = 'https://api.api-ninjas.com/v1/facts?limit={}'.format(1)
    response = requests.get(api_url, headers={'X-Api-Key': API_KEY})
    message = "Error: "+str(response.status_code)+"\n"+response.text
    if response.status_code == requests.codes.ok:
        cjson = json.loads(response.text)
        message = cjson[0]["fact"]
    await ctx.respond(message)

@bot.slash_command(name='quote', description="Displays an AI-generated quote on an inspirational image")
async def send_quote(ctx):
    response = requests.get("https://inspirobot.me/api?generate=true")
    await ctx.respond(response.text)

@bot.slash_command(name='set_counting_channel', description="Sets the channel for the counting game")
@discord.commands.default_permissions(manage_guild=True)
async def set_counting_channel(ctx, channel: discord.TextChannel):
    single_SQL("UPDATE Guilds SET CountingChannelID={0} WHERE ID={1}".format(channel.id, ctx.guild_id))
    await ctx.respond("Counting channel set to {0}".format(channel))

@bot.slash_command(name='get_highscore', description="Shows you the highest count your server has reached")
async def get_highscore(ctx):
    highscore = single_SQL("SELECT HighScoreCounting FROM Guilds WHERE ID = {0}".format(ctx.guild_id))
    await ctx.respond("Your highscore is {0}".format(highscore[0][0]))
    
@bot.slash_command(name='clearlosers', description="Testing to clear Loserrole")
@discord.commands.default_permissions(manage_guild=True)
async def clearrole(ctx):
    await clearLosers()
    print("done")

@bot.slash_command(name='set_loser_role', description="Set the role the person who failed at counting should get")
@discord.commands.default_permissions(manage_guild=True)
async def set_loserRole(ctx, role: discord.Role):
    single_SQL("UPDATE Guilds SET LoserRoleID={0} WHERE ID={1}".format(role.id, ctx.guild_id))
    await ctx.respond("The role for the loser is set to {0}".format(role.name))
    
@bot.event
async def on_message(msg):
    if(msg.content.isdigit()):
        values = single_SQL("SELECT CountingChannelID, CurrentCount, LastCounterID, HighScoreCounting, LoserRoleID FROM Guilds WHERE ID={0}".format(msg.guild.id))
        if(msg.channel.id == values[0][0]): #Checks for the right channel
            if(int(msg.content) == values[0][1] + 1): #Checks if it is the correct number
                if(msg.author.id != values[0][2]): #Checks if the same user wrote twice 
                    await msg.add_reaction('<:NixBlep:1025434663281492120>') #!!Change for the NixP-Emote before adding it to the server!!
                    single_SQL("UPDATE Guilds SET LastCounterID = {0}, CurrentCount = CurrentCount+1 WHERE ID = {1}".format(msg.author.id, msg.guild.id))
                    if(values[0][1] > values[0][3]):
                        single_SQL("UPDATE Guilds SET HighScoreCounting = {0} WHERE ID = {1}".format(values[0][1]+1, msg.guild.id))  
                        print(values[0][3])
                else: #The same user wrote two times in a row
                    single_SQL("UPDATE Guilds SET CurrentCount = 0, LastCounterID = 0 WHERE ID = {0}".format(msg.guild.id))
                    await msg.add_reaction('<:NixCrying:1025433818527715459>')
                    await msg.channel.send("Counting failed: same user entered two numbers in a row")
                    await msg.author.add_roles(msg.guild.get_role(values[0][4]))
            else: #Wrong number got typed in the chat
                single_SQL("UPDATE Guilds SET CurrentCount = 0, LastCounterID = 0 WHERE ID = {0}".format(msg.guild.id))
                await msg.add_reaction('<:NixCrying:1025433818527715459>')
                await msg.channel.send("Counting failed: Wrong number")
                await msg.author.add_roles(msg.guild.get_role(values[0][4]))
            
async def clearLosers():
    gandR = single_SQL("SELECT ID, LoserRoleID FROM Guilds")
    for g in gandR:
        for user in bot.get_guild(g[0]).get_role(g[1]).members: #For all users with the role
            await user.remove_roles(bot.get_guild(g[0]).get_role(g[1])) #Remove the role


### Helpers ###

def single_SQL(query):
    con = sqlite3.connect("server_data.db")
    cur = con.cursor()
    cur.execute(query)
    val = cur.fetchall()
    con.commit()
    cur.close()
    con.close()
    return val


### Client Event Handlers ###

@bot.event
async def on_guild_join(guild):
    single_SQL("INSERT INTO Channels VALUES ({0}, NULL, 0, 0, 0);".format(guild.id))

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

if __name__ == "__main__":     
    bot.run(TOKEN)