from enum import Enum
import datetime

TIME = datetime.time(hour=7)


class Colours(Enum):
    """
    Colour palette for Nix
    """
    PRIMARY = discord.Colour(15570741)
    ACCENT = discord.Colour(14300197)
    TEXT = discord.Colour(460551)


class Emotes(Enum):
    """
    Emotes for Nix. Emotes should appear at the end of messages or lines, not before or within.
    Try to use Emotes in all Nix messages and try to use all emotes equally.
    """
    DRINKING = "<:NixDrinking:1026494037043187713>"
    NOEMOTION = "<:NixNoEmotion:1026494031670300773>"
    EVIL = "<:NixEvil:1033423155034849340>"
    SUPRISE = "<:NixSuprise:1033423188937416704>"
    SNEAKY = "<:NixSneaky:1033423327320080485>"
    HUG = "<:NixHug:1033423234370125904>"
    BLEP = "<:NixBlep:1026494035994607717>"
    CONFUSED = "<:NixConfused:1026494027727638599>"
    CRYING = "<:NixCrying:1026494029002723398>"
    HEART = "<:NixHeart:1026494038825779331>"
    WTF = "<:NixWTF:1026494030407806986>"
    WHOA = "<:NixWhoa:1026494032999895161>"
    UWU = "<:NixUwU:1026494034371420250>"
