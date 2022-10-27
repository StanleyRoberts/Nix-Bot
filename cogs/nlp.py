import discord
import transformers
from discord.ext import commands
from transformers import BloomForCausalLM
from transformers import BloomTokenizerFast
from transformers import AutoTokenizer, AutoModel
import torch
import re


class NLP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.tokenizer = AutoTokenizer.from_pretrained("bigscience/bloom")

        self.model = AutoModel.from_pretrained("bigscience/bloom")

        self.result_length = 50
        self.inputs = tokenizer(prompt, return_tensors="pt")

    @commands.Cog.listener("on_message")
    async def NLP(msg):
        """
        Prints out an AI generated response to the message if it mentions Nix

        Args:
            msg (discord.Message): Message that triggered event
        """
        if (bot.user.mentioned_in(msg)):

            clean_prompt = re.sub(" @", " ",
                                  re.sub("@" + bot.user.name, "", msg.clean_content))

            prompt = "The following is a conversation with a phoenix named Nix. The phoenix is helpful, creative, " +\
                "clever, and very friendly.\n\nHuman: Hello, who are you?\nNix: I am a phoenix made of fire. " +\
                "How can I help you today?\nHuman: " + clean_prompt + "\nNix: "

            response = self.tokenizer.decode(self.model.generate(self.inputs["input_ids"],
                                                                 max_length=self.result_length,
                                                                 do_sample=True,
                                                                 top_k=50,
                                                                 top_p=0.9
                                                                 )[0])

            await msg.reply(response.strip('\n'))


def setup(bot):
    bot.add_cog(NLP(bot))
