from dotenv import load_dotenv
import os
from helpers.logger import Logger
if __debug__:
    load_dotenv()

logger = Logger()

registered = set()


def load_env(name: str) -> str:
    env = os.getenv('TOKEN')
    if not env:
        logger.error(f"{name} environment variable missing")
    if __debug__:
        global registered
        registered.add(name)
    return env


TOKEN = load_env('TOKEN')  # Discord Token
CLIENT_ID = load_env('CLIENT_ID')  # PRAW/Reddit API client ID
SECRET_KEY = load_env('SECRET_KEY')  # PRAW/Reddit API secret key
USER_AGENT = load_env('USER_AGENT')  # PRAW/Reddit API user agent
NINJA_API_KEY = load_env('NINJA_API_KEY')  # X-API-Key for API-Ninjas
DATABASE_URL = load_env('DATABASE_URL')  # PostgreSQL db
HF_API = load_env('HF_API')  # HuggingFace API key

if __debug__:
    import testing.postgresql as tp  # type: ignore[import]
    postgres = tp.Postgresql()
    DATABASE_URL = postgres.url()


def shutdown_db() -> None:
    if __debug__:
        postgres.stop()
