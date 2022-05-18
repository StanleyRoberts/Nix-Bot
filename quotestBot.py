import discord
import requests
import json
import datetime

TOKEN = 'OTc0NzY1NDI1Mjk4NjQ5MDk4.GGVRVj.r6Pzitvw3K0aTYKZTVR6s8mQwI-EvWq_t2GKiM'

client = discord.Client()


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
        match user_message.lower():
            case '!quote':
                await msg.channel.send(give_quote().text)
                
            case '!activechange':
                if msg.author == client.get_user(482591737538281472) or msg.author == client.get_user(107523639410180096):
                    guild = client.get_guild(msg.guild.id)
                    mlist = memberlist(msg)
                    for m in mlist:
                        for i in guild.text_channels:
                            messages = await i.history(limit=None, before=None, after=last_monday()).flatten()
                            for j in messages:
                                if j.author == guild.get_member(m[0]):
                                    m[1] +=  1
                        mem = guild.get_member(m[0])
                        active = new_role = role = discord.utils.get(mem.guild.roles, name='active')
                        Active = new_role = role = discord.utils.get(mem.guild.roles, name='Active')
                        print(mem.roles)
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
                                await mem.add_roles(active)   
        return
if __name__ == "__main__":     
    client.run(TOKEN)