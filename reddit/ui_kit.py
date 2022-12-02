import discord
from discord.partial_emoji import PartialEmoji
from functions.style import Emotes
from reddit.interface import RedditInterface


class ChangeSubModal(discord.ui.Modal):
    """
    Modal text box to change subreddit for reddit PostViewer

    Args:
        title (str): the modal title
        time (str): the time period for reddit posts
    """

    def __init__(self, title, time):
        super().__init__(title=title)
        self.add_item(discord.ui.InputText(label="Subreddit"))
        self.time = time

    async def callback(self, interaction):
        await interaction.response.defer()
        newsub = self.children[0].value
        post = await RedditInterface.get_post(newsub, self.time)
        await interaction.message.edit(content=post.text, files=post.img, attachments=[],
                                       view=PostViewer(newsub, self.time))


class PostViewer(discord.ui.View):
    """
    Manages the PostViewer context, which interactively displays reddit posts

    Args:
        sub (str): the subreddit to show posts from
        time (str): the time period to show posts from
    """

    def __init__(self, sub, time):
        super().__init__(timeout=300)
        self.sub = sub
        self.time = time

    @discord.ui.button(label="New Post", style=discord.ButtonStyle.primary,
                       emoji=PartialEmoji.from_str(Emotes.BLEP))
    async def refresh_callback(self, _, interaction: discord.Interaction):
        await interaction.response.defer()
        post = await RedditInterface.get_post(self.sub, self.time)
        await interaction.message.edit(content=post.text, files=post.img, attachments=[],
                                       view=PostViewer(self.sub, self.time))

    @discord.ui.button(label="Change Subreddit", style=discord.ButtonStyle.secondary,
                       emoji=PartialEmoji.from_str(Emotes.HUG))
    async def change_sub_callback(self, _, interaction):
        await interaction.response.send_modal(ChangeSubModal(title="Change Subreddit",
                                                             time=self.time))
