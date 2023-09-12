from dotenv import load_dotenv
import os
from helpers.logger import Logger
if __debug__:
    load_dotenv()

logger = Logger()

TOKEN = os.getenv('TOKEN')  # Discord Token
CLIENT_ID = os.getenv('CLIENT_ID')  # PRAW/Reddit API client ID
SECRET_KEY = os.getenv('SECRET_KEY')  # PRAW/Reddit API secret key
USER_AGENT = os.getenv('USER_AGENT')  # PRAW/Reddit API user agent
NINJA_API_KEY = os.getenv('NINJA_API_KEY')  # X-API-Key for API-Ninjas
DATABASE_URL = os.getenv('DATABASE_URL')  # PostgreSQL db
CAI_CHAR_TOKEN = os.getenv('CAI_CHAR_TOKEN')  # Character AI client token
CAI_NIX_ID = os.getenv('CAI_NIX_ID')  # Character AI character ID of Nix bot

if __debug__:
    import testing.postgresql as tp  # type: ignore[import]
    postgres = tp.Postgresql()
    DATABASE_URL = postgres.url()


def shutdown_db() -> None:
    if __debug__:
        postgres.stop()


if TOKEN is None:
    logger.error("TOKEN environment variable missing")
if CLIENT_ID is None:
    logger.error("CLIENT_ID environment variable missing")
if SECRET_KEY is None:
    logger.error("SECRET_KEY environment variable missing")
if USER_AGENT is None:
    logger.error("USER_AGENT environment variable missing")
if NINJA_API_KEY is None:
    logger.error("NINJA_API_KEY environment variable missing")
if DATABASE_URL is None:
    logger.error("DATABASE_URL environment variable missing")
if CAI_CHAR_TOKEN is None:
    logger.error("CAI_CHAR_TOKEN environment variable missing")
if CAI_NIX_ID is None:
    logger.error("CAI_NIX_ID environment variable missing")
