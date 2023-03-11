import discord
import asyncio
import string
import random
import os

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

global found_ID, game_ongoing, MSG, bots_turn, hangman
found_ID = False
game_ongoing = False
bots_turn = False
hangman = None
MSG = None


async def edit_previous_message(new_content: str):
    if MSG:
        await MSG.edit(content=new_content)


class PlayHangman:
    def __init__(self):
        self.letters = string.ascii_lowercase

    async def start_game(self, channel):
        ini_string = r"%hangman"
        await channel.send(ini_string)

    async def make_guess(self, channel):
        guess = random.choice(self.letters)
        self.letters = self.letters.replace(guess, "")
        await channel.send(guess)

    async def play_hangman(self, channel):
        global game_ongoing, found_ID, bots_turn
        if not game_ongoing and not bots_turn:
            await self.start_game(channel)
            game_ongoing = True

        while bots_turn and game_ongoing:
            await self.make_guess(channel)
            bots_turn = False

            
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    
@client.event
async def on_message(message):
    global found_ID, MSG, game_ongoing, bots_turn, hangman
    if message.author == client.user:
        if not found_ID:
            MSG = message
            found_ID = True
        return
    if message.content == '**help':
        msg = """```
        List of commands:
        **attack                 starts game of Puffin's Hangman
        **abort                  aborts current game
        ```"""
        await message.channel.send(msg)
    if message.content == '**attack':
        if game_ongoing:
            await message.channel.send("Game already in progress.")
            return
        await message.channel.send("Starting game!")
        hangman = PlayHangman()
        task = asyncio.create_task(hangman.play_hangman(message.channel))
        await task
    if message.content == "**abort":
        game_ongoing = False
        bots_turn = False
        await message.channel.send("aborting game")
    if "Please guess a letter." in message.content and game_ongoing:
        bots_turn = True
        task = asyncio.create_task(hangman.play_hangman(message.channel))
        await task
    if "Congrats! You Win!" in message.content:
        bots_turn = False
        game_ongoing = False
        await message.channel.send("You lost again?? :sob: :cry:")
    if "Better luck next time." in message.content:
        bots_turn = False
        game_ongoing = False
        await message.channel.send("Bested by a bot :upside_down: :sob:")

@client.event
async def on_message_edit(before, after):
    global found_ID, MSG, game_ongoing, bots_turn, hangman
    if "Please guess a letter." in after.content and game_ongoing:
        bots_turn = True
        task = asyncio.create_task(hangman.play_hangman(after.channel))
        await task

client.run(TOKEN)