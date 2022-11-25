import discord
from discord.ext import commands
import random
from discord.ui import Button, View


def allCards():                                      # Sets all available cards
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


def dropDeck():
    shuffleCards(deck)
    currentCard = deck[1]


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


def playerTurn():             # ahh yes
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

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.green)
    async def button_callback(self, button, interaction,):
        playerHand()
        player1Hand = playerHand()
        player2Hand = playerHand()
        player3Hand = playerHand()
        await interaction.response.send_message("Your cards:\n" +
                                                self.player1.mention + ": " + str(player1Hand) + "\n" +
                                                self.player2.mention + ": " + str(player2Hand) + "\n" +
                                                self.player3.mention + ": " + str(player3Hand))
        random.shuffle(deck)
        currentCard = deck[1]
        # fix next time 'send_message' -> API
        await interaction.send_message('Current card is: ' + currentCard)


def setup(bot):
    bot.add_cog(NixUno(bot))
