import sqlite3, requests, json, random
import asyncpraw as praw, asyncprawcore as prawcore

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
    response = "Unknown error searching for subreddit"+subreddit
    try:
        subr = await reddit.subreddit(subreddit)
        subm = random.choice([post async for post in subr.top(time_filter=time, limit=100)])
        link = subm.selftext if subm.is_self else subm.url
        response = "***"+subm.title+"***\n"+link
    except prawcore.exceptions.Redirect:
        response = "Subreddit \'"+subreddit+" \' not found"
    except prawcore.exceptions.NotFound:
        response = "Subreddit \'"+subreddit+"\' banned"
    except prawcore.exceptions.Forbidden:
        response = "Subreddit \'"+subreddit+"\' private"
    return response