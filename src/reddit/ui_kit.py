import discord
from discord.partial_emoji import PartialEmoji

from helpers.style import Emotes
from helpers.logger import Logger

logger = Logger()


class PostViewer(discord.ui.View):
    """
    Manages the PostViewer context, which interactively displays reddit posts

    Args:
        reddit (asyncpraw.Reddit): Reddit instance
    """

    def __init__(self, reddit):
        super().__init__(timeout=300)
        self.reddit = reddit
        logger.info("Created PostViewer")

    @discord.ui.button(label="New Post", style=discord.ButtonStyle.primary,
                       emoji=PartialEmoji.from_str(Emotes.YUM))
    async def refresh_callback(self, _, interaction: discord.Interaction):
        await interaction.response.defer()
        post = await self.reddit.get_post()
        await interaction.message.edit(content=post.text, files=post.img, attachments=[],
                                       view=self)
        logger.debug("PostViewer - New post")

    @discord.ui.button(label="Change Subreddit", style=discord.ButtonStyle.secondary,
                       emoji=PartialEmoji.from_str(Emotes.HUG))
    async def change_sub_callback(self, _, interaction):
        await interaction.response.send_modal(ChangeSubModal(title="Change Subreddit",
                                                             caller=self))
        logger.debug("PostViewer - Change subreddit")


class ChangeSubModal(discord.ui.Modal):
    """
    Modal text box to change subreddit for reddit PostViewer

    Args:
        title (str): the modal title
        caller (PostViewer): the calling View
    """

    def __init__(self, title: str, caller: PostViewer) -> None:
        super().__init__(title=title)
        self.add_item(discord.ui.InputText(label="Subreddit"))
        self.caller = caller
        logger.debug("Created ChangeSubModal")

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        newsub = self.children[0].value
        await self.caller.reddit.set_subreddit(newsub)
        post = await self.caller.reddit.get_post()
        await interaction.message.edit(content=post.text, files=post.img, attachments=[],
                                       view=self.caller)
        logger.info("ChangeSubModal closed")
