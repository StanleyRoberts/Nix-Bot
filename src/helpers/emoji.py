import re
import emoji as emoji_lib

from discord.partial_emoji import PartialEmoji


class Emoji:
    def __init__(self, emoji: str):
        if re.compile(r"<?(?P<animated>a)?:?(?P<name>\w+):(?P<id>[0-9]{13,20})>?").match(emoji):
            self.string = emoji
            self.unicode = False
        elif emoji_lib.is_emoji(emoji):
            self.string = emoji_lib.demojize(emoji)
            self.unicode = True
        else:
            self.unicode = True
            converted = emoji_lib.emojize(emoji)
            if emoji_lib.is_emoji(converted):
                self.string = emoji
            else:
                raise ValueError(f"{emoji} is not a valid emoji")

    def as_text(self) -> str:
        return self.string

    def as_unicode(self) -> str:
        if self.unicode:
            return emoji_lib.emojize(self.string)
        else:
            raise ValueError(f"{self.string} is not a Unicode emoji")

    def to_partial_emoji(self) -> PartialEmoji:
        if self.unicode:
            return PartialEmoji.from_str(self.as_unicode())
        else:
            return PartialEmoji.from_str(self.string)


def string_to_partial_emoji(emoji: str) -> PartialEmoji:
    if emoji in emoji_lib.UNICODE_EMOJI['en'] or\
            re.compile(r"<?(?P<animated>a)?:?(?P<name>\w+):(?P<id>[0-9]{13,20})>?").match(emoji):
        return PartialEmoji.from_str(emoji)
    else:
        raise ValueError(f"{emoji} is not a valid emoji")
