import datetime
import discord
from discord.partial_emoji import PartialEmoji

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
    BLEP = "<:NixBlep:1026494035994607717>"
    CONFUSED = "<:NixConfused:1026494027727638599>"
    CRYING = "<:NixCrying:1026494029002723398>"
    DRINKING = "<:NixDrinking:1026494037043187713>"
    EVIL = "<:NixEvil:1033423155034849340>"
    HEART = "<:NixHeart:1026494038825779331>"
    HUG = "<:NixHug:1033423234370125904>"
    NOEMOTION = "<:NixNoEmotion:1026494031670300773>"
    SUPRISE = "<:NixSuprise:1033423188937416704>"
    SNEAKY = "<:NixSneaky:1033423327320080485>"
    UWU = "<:NixUwU:1026494034371420250>"
    WTF = "<:NixWTF:1026494030407806986>"
    WHOA = "<:NixWhoa:1026494032999895161>"


async def string_to_emoji(emoji):
    return PartialEmoji.from_str(emoji)
