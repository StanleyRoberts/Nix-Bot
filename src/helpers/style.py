import datetime
import discord

TIME = datetime.time(hour=7)
RESET = datetime.time(hour=8)


class Colours():
    """Colour palette for Nix
    """
    PRIMARY = discord.Colour(15570741)
    ACCENT = discord.Colour(14300197)
    TEXT = discord.Colour(460551)


class Emotes():
    """Emotes for Nix.

    Try to use Emotes in all Nix messages and try to use all emotes equally.
    'Equally' means in terms of expected Nix output, not number of code appearances
    """
    BLEP = "<:NixBlep:1026494035994607717>"  # counting success
    BRUH = "<:NixBruh:1091877305028202506>"  # Trivia wrong answer
    CLOWN = "<:NixClown:1091877301890846811>"  # ai failure
    CONFUSED = "<:NixConfused:1026494027727638599>"  # counting role fail, reddit posts exhausted
    CRYING = "<:NixCrying:1026494029002723398>"  # couting failed reaction, counting failed message
    DRINKING = "<:NixDrinking:1026494037043187713>"  # set fail role, set bday/counting/fact channel
    EVIL = "<:NixEvil:1033423155034849340>"  # subreddit not available for /subscribe
    HAPPY = "<:NixHappy:1091877310875046009>"  # Trivia msg after correct guess
    HEART = "<:NixHeart:1026494038825779331>"  # bday message, send_react_message success
    HUG = "<:NixHug:1033423234370125904>"  # reddit /subscribe success, reddit browser change subreddit button
    NOEMOTION = "<:NixNoEmotion:1026494031670300773>"  # stopped daily facts message
    SNEAKY = "<:NixSneaky:1033423327320080485>"  # unsubbed from sub message, trivia question
    STARE = "<:NixStare:1091877310052962344>"  # existing trivia game
    SUNGLASSES = "<:NixSunglasses:1091877306793988166>"  # trivia answer after skip
    SUPRISE = "<:NixSuprise:1033423188937416704>"  # already subbed in /subscribe, not subscribed in /unsubscribe
    TEEHEE = "<:NixTeeHee:1091877308756930590>"  # Trivia show winner
    UWU = "<:NixUwU:1026494034371420250>"  # birthday set message, trivia start
    WHOA = "<:NixWhoa:1026494032999895161>"  # highscore message, Trivia correct guess
    WTF = "<:NixWTF:1026494030407806986>"  # set sub failure for reddit browser, invalid emoji in send_react_success
    YUM = "<:NixYum:1091877303740551288>"  # reddit browser new post button
