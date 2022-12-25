import requests
import json
import re
from discord.ext import commands

from Nix import HF_API


class NLP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def NLP(self, msg: str):
        """
        Prints out an AI generated response to the message if it mentions Nix

        Args:
            msg (discord.Message): Message that triggered event
        """
        if (self.bot.user.mentioned_in(msg) and msg.reference is None):
            clean_prompt = re.sub(" @", " ",
                                  re.sub("@" + self.bot.user.name, "", msg.clean_content))

            url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
            headers = {"Authorization": f"Bearer {HF_API}"}

            prompt = {"past_user_inputs": ["What is your name?", "Who are you?"],
                      "generated_responses": ["My name is Nix", "I am Nix, a phoenix made of flames"],
                      "text": clean_prompt}

            data = json.dumps({"inputs": prompt, "parameters": {
                              "return_full_text": False, "temperature": 0.8,
                              "use_cache": False}})
            response = requests.request("POST", url, headers=headers, data=data)

            text = json.loads(response.content.decode('utf-8'))
            await msg.reply(text['generated_text'])


def setup(bot):
    bot.add_cog(NLP(bot))
