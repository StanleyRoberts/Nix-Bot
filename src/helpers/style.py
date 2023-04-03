import datetime
import discord


TIME = datetime.time(hour=7)


class Colours():
    """
    Colour palette for Nix
    """
    PRIMARY = discord.Colour(15570741)
    ACCENT = discord.Colour(14300197)
    TEXT = discord.Colour(460551)


class Emotes():
    """
    Emotes for Nix. Emotes should appear at the end of messages or lines, not before or within.
    Try to use Emotes in all Nix messages and try to use all emotes equally.
    """
    BLEP = "<:NixBlep:1026494035994607717>"  # counting success
    BRUH = "<:NixBruh:1091877305028202506>"  # none
    CLOWN = "<:NixClown:1091877301890846811>"  # ai failure
    CONFUSED = "<:NixConfused:1026494027727638599>"  # counting role fail, reddit posts exhausted
    CRYING = "<:NixCrying:1026494029002723398>"  # couting failed reaction, counting failed message
    DRINKING = "<:NixDrinking:1026494037043187713>"  # set fail role, set bday/counting/fact channel
    EVIL = "<:NixEvil:1033423155034849340>"  # subreddit not available for /subscribe
    HAPPY = "<:NixHappy:1091877310875046009>"  # none
    HEART = "<:NixHeart:1026494038825779331>"  # bday message
    HUG = "<:NixHug:1033423234370125904>"  # reddit /subscribe success, reddit browser change subreddit button
    NOEMOTION = "<:NixNoEmotion:1026494031670300773>"  # stopped daily facts message
    SNEAKY = "<:NixSneaky:1033423327320080485>"  # unsubbed from sub message
    STARE = "<:NixStare:1091877310052962344>"  # none
    SUNGLASSES = "<:NixSunglasses:1091877306793988166>"  # none
    SUPRISE = "<:NixSuprise:1033423188937416704>"  # already subbed in /subscribe, not subscribed in /unsubscribe
    TEEHEE = "<:NixTeeHee:1091877308756930590>"  # none
    UWU = "<:NixUwU:1026494034371420250>"  # birthday set message
    WHOA = "<:NixWhoa:1026494032999895161>"  # highscore message
    WTF = "<:NixWTF:1026494030407806986>"  # set sub failure for reddit browser
    YUM = "<:NixYum:1091877303740551288>"  # reddit browser new post button
