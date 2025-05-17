import datetime
import discord
from dataclasses import dataclass

TIME = datetime.time(hour=7)
RESET = datetime.time(hour=8)


@dataclass
class Colours:
    """Colour palette for Nix
    """
    PRIMARY = discord.Colour(15570741)
    ACCENT = discord.Colour(14300197)
    TEXT = discord.Colour(460551)


@dataclass
class Emotes:
    """Emotes for Nix.

    Try to use Emotes in all Nix messages and try to use all emotes equally.
    'Equally' means in terms of expected Nix output, not number of code appearances
    """
    BLEP = "<:NixBlep:1026494035994607717>"
    BRUH = "<:NixBruh:1091877305028202506>"
    CLOWN = "<:NixClown:1091877301890846811>"
    CONFUSED = "<:NixConfused:1026494027727638599>"
    CRYING = "<:NixCrying:1026494029002723398>"
    DRINKING = "<:NixDrinking:1026494037043187713>"
    EVIL = "<:NixEvil:1033423155034849340>"
    HAPPY = "<:NixHappy:1091877310875046009>"
    HEART = "<:NixHeart:1026494038825779331>"
    HUG = "<:NixHug:1033423234370125904>"
    NOEMOTION = "<:NixNoEmotion:1026494031670300773>"
    SNEAKY = "<:NixSneaky:1033423327320080485>"
    STARE = "<:NixStare:1091877310052962344>"
    SUNGLASSES = "<:NixSunglasses:1091877306793988166>"
    SUPRISE = "<:NixSuprise:1033423188937416704>"
    TEEHEE = "<:NixTeeHee:1091877308756930590>"
    UWU = "<:NixUwU:1026494034371420250>"
    WHOA = "<:NixWhoa:1026494032999895161>"
    WTF = "<:NixWTF:1026494030407806986>"
    YUM = "<:NixYum:1091877303740551288>"
    GOON = "<:NixGoon:1357895953050501312>"
