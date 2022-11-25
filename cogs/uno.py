import discord
from discord.ext import commands
import random
from discord.ui import Button, View


def allCards():  # Sets all available cards
    deck = []
    colors = ['green', 'red', 'yellow', 'blue']
    values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 'Draw 2', 'SKIP']
    # want to add specific cards like a "flame" card.. bc its Nix Uno
    wilds = ['WILD Draw 4', 'WILD']
    for c in colors:
        for v in values:
            cardVal = '{} {}'.format(c, v)
            deck.append(cardVal)
    deck += (wilds)
    return deck


deck = allCards()


def shuffleCards(deck):
    random.shuffle(deck)


shuffleCards(deck)


def playerTurn():  # needs to be looked at!!
    players = [player1, player2, player3]


def dropDeck():
    shuffleCards(deck)
    startCard = deck[1]
    currentCard = ""


dropDeck()


def playerHand():
    Hand = []
    handPosition = [1, 2, 3, 4, 5]
    for Card in handPosition:
        shuffleCards(deck)
        Hand.append(deck[1])
    posHand = 0
    for i in Hand:
        posHand += 1
        print(str(posHand) + ') ' + i)
    return Hand


playerHand()
player1Hand = playerHand()
player2Hand = playerHand()
player3Hand = playerHand()


def playerTurn():
    turns = [1, 2, 3]


class NixUno(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="nix_uno",
                            description="Starts a game of NixUno and slect players who should participate")
    async def start_game(self, ctx,
                         player1: discord.Option(discord.Member, required=False),
                         player2: discord.Option(discord.Member, required=False),
                         player3: discord.Option(discord.Member, required=False)):
        await ctx.respond(player1.mention + ' ' + player2.mention + ' ' + player3.mention +
                          ' are playing right now <:NixSip:1025434211986984971>')
        await self.followUp(ctx.channel_id, player1, player2, player3)

    async def followUp(self, channelID, player1, player2, player3):
        await (await self.bot.fetch_channel(channelID)).send('Press "Start Game" to play', view=MyView(player1,
                                                                                                       player2,
                                                                                                       player3))


class MyView(discord.ui.View):
    def __init__(self, player1, player2, player3):
        super().__init__()
        self.player1 = player1
        self.player2 = player2
        self.player3 = player3

        player1 = 1
        player2 = 2
        player3 = 3

    async def followUp(self, channelID, player1, player2, player3):
        await (await self.bot.fetch_channel(channelID)).send('Press "Start Game" to play', view=MyView())


class MyView(discord.ui.View):  # Create a class called MyView that subclasses discord.ui.View
    # Create a button with the label "😎 Click me!" with color Blurple
    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.green)
    async def button_callback(self, button, interaction, player1, player2, player3):
        random.shuffle(deck)
        startCard = deck[1]
        await interaction.response.send_message("It is " + player1.mention + "'s turn")
        await interaction.response.send_message('The current card is: ' + str(startCard))


def setup(bot):
    bot.add_cog(NixUno(bot))
