import requests
import json
import re
from discord.ext import commands

from Nix import HF_API


class NLP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def NLP(self, msg):
        """
        Prints out an AI generated response to the message if it mentions Nix

        Args:
            msg (discord.Message): Message that triggered event
        """
        if (self.bot.user.mentioned_in(msg) and msg.reference is None):
            clean_prompt = re.sub(" @", " ",
                                  re.sub("@" + self.bot.user.name, "", msg.clean_content))

            url = "https://api-inference.huggingface.co/models/bigscience/bloom"
            headers = {"Authorization": f"Bearer {HF_API}"}

            prompt = "The following is a conversation with a phoenix named Nix. The phoenix is helpful, creative, " +\
                "clever, and very friendly.\n\nHuman: Hello, who are you?\nNix: I am a phoenix made of fire. " +\
                "How can I help you today?\nHuman: " + clean_prompt + "\nNix: "

            data = json.dumps({"inputs": prompt, "parameters": {
                              "return_full_text": False, "temperature": 0.9, "use_cache": False}})
            response = requests.request(
                "POST", url, headers=headers, data=data)

            text = json.loads(response.content.decode(
                'utf-8'))[0]['generated_text']
            print("\n\ngenerated text: " + text)

            # strip non-Nix messages
            trim = re.sub(
                "Nix:", "", text[len(prompt):].split('Human: ')[0])

            await msg.reply(trim if not any(ele in trim for ele in ['.', '!', '?', ')']) else "".join(
                (re.findall('.*?[.!?)]', trim))))  # strip dangling sentences


def setup(bot):
    bot.add_cog(NLP(bot))
