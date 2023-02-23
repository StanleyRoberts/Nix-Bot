from dotenv import load_dotenv
import os

if __debug__:
    load_dotenv()

TOKEN = os.getenv('TOKEN')  # Discord Token
CLIENT_ID = os.getenv('CLIENT_ID')  # PRAW/Reddit API client ID
SECRET_KEY = os.getenv('SECRET_KEY')  # PRAW/Reddit API secret key
USER_AGENT = os.getenv('USER_AGENT')  # PRAW/Reddit API user agent
NINJA_API_KEY = os.getenv('NINJA_API_KEY')  # X-API-Key for API-Ninjas
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL db
HF_API = os.getenv('HF_API')  # HuggingFace API key


if __debug__:
    import testing.postgresql as tp
    postgres = tp.Postgresql()
    DATABASE_URL = postgres.url()


def shutdown_db():
    if __debug__:
        super(tp.Postgresql, postgres).terminate(signal.SIGINT if os.name != 'nt' else None)
