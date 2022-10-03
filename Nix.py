import discord
import os
from discord.ext import tasks, commands
import datetime as dt
from dotenv import load_dotenv
import functions.helpers as helper


### CONSTANTS ###

load_dotenv()

TOKEN = os.getenv('TOKEN') # Discord Token
CLIENT_ID = os.getenv('CLIENT_ID') # PRAW/Reddit API client ID
SECRET_KEY = os.getenv('SECRET_KEY') # PRAW/Reddit API secret key
USER_AGENT = os.getenv('USER_AGENT') #PRAW/Reddit API user agent
API_KEY = os.getenv('API_KEY') # X-API-Key for API-Ninjas

intents = discord.Intents(messages=True, message_content=True, guilds=True, members = True)
bot = commands.Bot(intents=intents, command_prefix='?', activity=discord.Game(name="/help"))


### Command Functions ###

@bot.slash_command(name='reddit', description="Displays a random top reddit post from the given subreddit")
async def send_reddit_post(ctx, subreddit,
                           time: discord.Option(str, default="day",
                                                choices=["month", "hour", "week", "all", "day", "year"],
                                                description="Time period to search for top posts")):
    await ctx.respond(helper.get_reddit_post(subreddit, time))

@bot.slash_command(name='quote', description="Displays an AI-generated quote over an inspirational image")
async def send_quote(ctx):
    await ctx.respond(helper.get_quote())

@bot.slash_command(name='set_counting_channel', description="Sets the channel for the counting game")
@discord.commands.default_permissions(manage_guild=True)
async def set_counting_channel(ctx, channel: discord.TextChannel):   
    helper.single_SQL("UPDATE Guilds SET CountingChannelID=? WHERE ID=?", (channel.id, ctx.guild_id))
    await ctx.respond("Counting channel set to {0}".format(channel))

@bot.slash_command(name='get_highscore', description="Shows you the highest count your server has reached")
async def get_highscore(ctx):
    highscore = helper.single_SQL("SELECT HighScoreCounting FROM Guilds WHERE ID = {0}".format(ctx.guild_id))
    await ctx.respond("Your highscore is {0}".format(highscore[0][0]))
    
@bot.slash_command(name='set_loser_role', description="Set the role the person who failed at counting should get")
@discord.commands.default_permissions(manage_guild=True)
async def set_loserRole(ctx, role: discord.Role):
    helper.single_SQL("UPDATE Guilds SET LoserRoleID={0} WHERE ID={1}".format(role.id, ctx.guild_id))
    await ctx.respond("The role for the loser is set to {0}".format(role.name))
    
@bot.event
async def on_message(msg):
    if(msg.content.isdigit()):
        values = helper.single_SQL("SELECT CountingChannelID, CurrentCount, LastCounterID, HighScoreCounting, LoserRoleID FROM Guilds WHERE ID={0}".format(msg.guild.id))
        if(msg.channel.id == values[0][0]): #Checks for the right channel
            if(int(msg.content) == values[0][1] + 1): #Checks if it is the correct number
                if(msg.author.id != values[0][2]): #Checks if the same user wrote twice 
                    await msg.add_reaction('<:NixBlep:1025434663281492120>') #!!Change for the NixP-Emote before adding it to the server!!
                    helper.single_SQL("UPDATE Guilds SET LastCounterID = {0}, CurrentCount = CurrentCount+1 WHERE ID = {1}".format(msg.author.id, msg.guild.id))
                    if(values[0][1] > values[0][3]):
                        helper.single_SQL("UPDATE Guilds SET HighScoreCounting = {0} WHERE ID = {1}".format(values[0][1]+1, msg.guild.id))  
                        print(values[0][3])
                else: #The same user wrote two times in a row
                    helper.API_KEYsingle_SQL("UPDATE Guilds SET CurrentCount = 0, LastCounterID = 0 WHERE ID = {0}".format(msg.guild.id))
                    await msg.add_reaction('<:NixCrying:1025433818527715459>')
                    await msg.channel.send("Counting failed: same user entered two numbers in a row")
                    await msg.author.add_roles(msg.guild.get_role(values[0][4]))
            else: #Wrong number got typed in the chat
                helper.single_SQL("UPDATE Guilds SET CurrentCount = 0, LastCounterID = 0 WHERE ID = {0}".format(msg.guild.id))
                await msg.add_reaction('<:NixCrying:1025433818527715459>')
                await msg.channel.send("Counting failed: Wrong number")
                await msg.author.add_roles(msg.guild.get_role(values[0][4]))
            
async def clearLosers():
    gandR = helper.single_SQL("SELECT ID, LoserRoleID FROM Guilds")
    for g in gandR:
        for user in bot.get_guild(g[0]).get_role(g[1]).members: #For all users with the role
            await user.remove_roles(bot.get_guild(g[0]).get_role(g[1])) #Remove the role

@bot.slash_command(name='help', description="Displays the help page for NixBot")
async def display_help(ctx):
    embed = discord.Embed(title="Help Page",
                          description = "Note: depending on your server settings and role permissions,"\
                          " some of these commands may be hidden or disabled\n\n# Generic\n"
                          +"".join(sorted([command.mention+" : "+command.description+"\n"
                                           for command in bot.walk_application_commands() if not command.cog]))\
                          +"".join(["\n# "+cog+"\n"+"".join(sorted([command.mention+" : "+command.description+"\n"
                                      for command in bot.cogs[cog].walk_commands()])) for cog in bot.cogs]))
    await ctx.respond(embed=embed)


### Looping Tasks ###

@tasks.loop(time=dt.time(hour=9)) #1 behind curr time
async def daily_check():
    guilds = helper.single_SQL("SELECT FactChannelID FROM Guilds")
    fact = helper.get_fact()
    for factID in guilds:
        if factID[0]:
            await (await bot.fetch_channel(factID[0])).send(fact)
    
    today=dt.date.today().strftime("%b%e").replace(" ", "")
    val = helper.single_SQL("SELECT BirthdayChannelID, group_concat(UserID, ' ') as UserID FROM Birthdays INNER JOIN"\
                            " Guilds ON Birthdays.GuildID=Guilds.ID WHERE Birthdays.Birthdate=\'?\'GROUP BY ID;", (today,))
    for guild in val:
        users = " ".join([(await bot.fetch_user(int(user))).mention for user in guild[1].split(" ")])
        if guild[0]:
            await (await bot.fetch_channel(guild[0])).send("Happy Birthday to: "+users+"!\nHope you have a brilliant day <:NixFire:1025434443642589305>")


### Client Event Handlers ###

@bot.event
async def on_guild_join(guild):
    helper.single_SQL("INSERT INTO Guilds (ID, CountingChannelID, BirthdayChannelID, FactChannelID, CurrentCount, LastCounterID, HighScoreCounting, LoserRoleID) VALUES (?, NULL, NULL, NULL, 0, NULL, 0, NULL);", (guild.id,))

@bot.event
async def on_guild_remove(guild):
    helper.single_SQL("DELETE FROM Guilds WHERE ID=?; DELETE FROM Birthdays WHERE GuildID=?", (guild.id, guild.id))

@bot.event
async def on_member_remove(member):
    helper.single_SQL("DELETE FROM Birthdays WHERE GuildID=? AND UserID=?", (member.guild.id, member.id))

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

if __name__ == "__main__":
    cogs = ['birthdays', 'facts']
    for cog in cogs:
        bot.load_extension(f'cogs.{cog}')
    daily_check.start() 
    bot.run(TOKEN)