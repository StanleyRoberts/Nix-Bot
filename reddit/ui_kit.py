import discord
from discord.partial_emoji import PartialEmoji
from functions.style import Emotes


class PostViewer(discord.ui.View):
    """
    Manages the PostViewer context, which interactively displays reddit posts

    Args:
        sub (str): the subreddit to show posts from
        time (str): the time period to show posts from
    """

    def __init__(self, reddit):
        super().__init__(timeout=300)
        self.reddit = reddit

    @discord.ui.button(label="New Post", style=discord.ButtonStyle.primary,
                       emoji=PartialEmoji.from_str(Emotes.BLEP))
    async def refresh_callback(self, _, interaction: discord.Interaction):
        await interaction.response.defer()
        post = await self.reddit.get_post()
        await interaction.message.edit(content=post.text, files=post.img, attachments=[],
                                       view=self)

    @discord.ui.button(label="Change Subreddit", style=discord.ButtonStyle.secondary,
                       emoji=PartialEmoji.from_str(Emotes.HUG))
    async def change_sub_callback(self, _, interaction):
        await interaction.response.send_modal(ChangeSubModal(title="Change Subreddit",
                                                             caller=self))


class ChangeSubModal(discord.ui.Modal):
    """
    Modal text box to change subreddit for reddit PostViewer

    Args:
        title (str): the modal title
        time (str): the time period for reddit posts
    """

    def __init__(self, title: str, caller: PostViewer) -> None:
        super().__init__(title=title)
        self.add_item(discord.ui.InputText(label="Subreddit"))
        self.caller = caller

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        newsub = self.children[0].value
        await self.caller.reddit.set_subreddit(newsub)
        post = await self.caller.reddit.get_post()
        await interaction.message.edit(content=post.text, files=post.img, attachments=[],
                                       view=self.caller)
