import discord
import asyncio
import typing

from helpers.style import Emotes
from helpers.logger import Logger
from trivia.interface import GuessValue, MAX_POINTS

logger = Logger()


class TriviaView(discord.ui.View):
    """View for the trivia game
            Args:
                players (dict[str, int]): the current players ids, mapped to their score
                difficulty (str): The difficulty of the questions
                interface (TriviaGame): _description_
    """

    def __init__(self, state, callback, channel_id):
        super().__init__(timeout=300)
        self.lock = asyncio.Lock()
        self.state = state
        self.channel_id = channel_id
        temp = super().on_timeout

        async def timeout():
            callback(channel_id)
            await temp()
            self.stop()
        self.on_timeout = timeout  # TODO timeout needs to be tested

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.secondary,
                       emoji='⏩')
    async def skip_callback(self, _, interaction: discord.Interaction):
        if interaction.user is None:
            logger.error("skip_callback interaction has no user")
            return
        old_answer = await self.state.skip(str(interaction.user.id))
        channel_id = interaction.channel_id if interaction.channel_id else 0
        guild_id = interaction.guild_id if interaction.guild_id else 0
        if old_answer:
            await interaction.response.send_message(f"The answer was: {old_answer} {Emotes.SUNGLASSES}")
            if not isinstance(interaction.channel, discord.abc.Messageable):
                logger.error("Callback for trivia interaction is not in sendable channel",
                             channel_id=channel_id, guild_id=guild_id)
                return
            await interaction.channel.send(await self.state.get_new_question(), view=self)
            logger.debug("Question successfully skipped", channel_id=channel_id, guild_id=guild_id)
        else:
            logger.debug("Question skip failed", channel_id=channel_id, guild_id=guild_id)

    async def handle_guess(self, msg: discord.Message):
        """Checks if a guess is correct

        If the guess is a number it has to be exact, otherwise any (spellingwise) close guesses will count too
        """
        async with self.lock:
            if msg.channel.id == self.message.channel.id:
                guess = self.state.check_guess(msg.content, str(msg.author.id))
                if guess == GuessValue.INCORRECT:
                    await msg.add_reaction(Emotes.BRUH)
                else:
                    await msg.add_reaction(Emotes.WHOA)
                    await msg.reply(f"You got the answer! ({self.state.answer}) " +
                                    f"You are now at {self.state.players[str(msg.author.id)]} points {Emotes.HAPPY}")
                    if guess == GuessValue.CORRECT_AND_WON:
                        await msg.reply(f"Congratulations! {msg.author.mention} has won with " +
                                        f"{MAX_POINTS} points! {Emotes.TEEHEE}")
                        await self.on_timeout()
                    else:
                        await msg.channel.send(await self.get_question(), view=self)

    async def get_question(self) -> str | None:
        return await self.state.get_new_question()

    def get_current_question(self):
        return self.state.get_current_question()
