import discord
import asyncio
import random
import os
import time
import pandas as pd
import json

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

global found_ID, game_ongoing, MSG, bots_turn, hangman, word_length, prev_word, bad_letters, good_letters, prev_guess, num_missing
found_ID = False
game_ongoing = False
bots_turn = False
hangman = None
word_length = None
prev_word = ""
prev_guess = None
good_letters = set()
bad_letters = set()
MSG = None

async def edit_previous_message(new_content: str):
    if MSG:
        await MSG.edit(content=new_content)


class PlayHangman:
    def __init__(self):
        global word_length
        self.desperate_letter_dist = {
            "e": 24,
            "t": 18,
            "a": 16,
            "o": 15,
            "i": 14,
            "n": 14,
            "s": 12,
            "r": 12,
            "h": 12,
            "d": 9,
            "l": 8,
            "u": 6,
            "c": 6,
            "m": 5,
            "f": 5,
            "y": 4,
            "w": 4,
            "g": 4,
            "p": 4,
            "b": 3,
            "v": 2,
            "k": 2,
            "x": 1,
            "q": 1,
            "j": 1,
            "z": 1,
        }

        self.desperate_letters = ""
        for letter, freq in self.desperate_letter_dist.items():
            self.desperate_letters += letter*freq

        words_path = "./data/en_225k.csv"
        word_df = pd.read_csv(words_path)
        word_df = word_df[word_df.length == word_length]
        self.word_df = word_df
        self.selection_string = ""
        for word in word_df.word:
            self.selection_string += str(word)

    async def send_stats(self, channel, game_stat):
        with open("./data/data_tracking.json", "r") as f:
            curr_stats = json.load(f)
        curr_stats[game_stat] += 1
        with open("./data/data_tracking.json", "w") as f:
            json.dump(curr_stats, f)

        await channel.send(f"Bot currently holds: {curr_stats['wins']} wins and {curr_stats['losses']} losses")

    async def start_game(self, channel):
        ini_string = r"%hangman"
        await channel.send(ini_string)

    async def make_guess(self, channel):
        global prev_word, prev_guess, good_letters, bad_letters, num_missing
        guess = ""
        poss_words = self.word_df
        word_count = 0
        if prev_guess:
            print("smart")
            if good_letters:
                for p_char in good_letters:
                    poss_words = poss_words[[p_char in i for i in poss_words.word]]
            if bad_letters:
                for p_char in bad_letters:
                    poss_words = poss_words[[p_char not in i for i in poss_words.word]]

            all_guess = set()
            all_guess.update(good_letters)
            all_guess.update(bad_letters)

            poss_chars = ""
            list_words = poss_words.word.to_list()

            for word in list_words:
                test_word = word
                for letter in all_guess:
                    test_word = test_word.replace(letter, "")
                if len(test_word) == num_missing:
                    word_count += 1
                    poss_chars += test_word

            if poss_chars:
                guess = random.choice(poss_chars)
        if not guess:
            print("medium")
            if self.selection_string:
                guess = random.choice(self.selection_string)
        if not self.selection_string:
            print("dumb")
            guess = random.choice(self.desperate_letters)

        self.desperate_letters = self.desperate_letters.replace(guess, "")
        self.selection_string = self.selection_string.replace(guess, "")
        time.sleep(1)
        prev_guess = guess
        print(f"good letters: {good_letters}; bad_letters: {bad_letters}; num potential words: {word_count}")
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
    global found_ID, MSG, game_ongoing, bots_turn, hangman, word_length, prev_guess, prev_word, good_letters, bad_letters
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
        await message.channel.send(r"%get word length")
    if message.content == "**abort":
        game_ongoing = False
        bots_turn = False
        await message.channel.send("aborting game")
    if "Please guess a letter." in message.content and game_ongoing:
        bots_turn = True
        task = asyncio.create_task(hangman.play_hangman(message.channel))
        await task
    if "Congrats! You Win!" in message.content and game_ongoing:
        bots_turn = False
        game_ongoing = False
        await message.channel.send("You lost again?? :sob: :cry:")
        task = asyncio.create_task(hangman.send_stats(message.channel, "wins"))
        await task
        word_length = None
        prev_word = ""
        prev_guess = None
        good_letters = set()
        bad_letters = set()
    if "Better luck next time." in message.content and game_ongoing:
        bots_turn = False
        game_ongoing = False
        await message.channel.send("Bested by a bot :upside_down: :sob:")
        task = asyncio.create_task(hangman.send_stats(message.channel, "losses"))
        await task
        word_length = None
        prev_word = ""
        prev_guess = None
        good_letters = set()
        bad_letters = set()
    if "Word length set to" in message.content:
        word_length = int(message.content.replace("Word length set to ",""))
        hangman = PlayHangman()
        task = asyncio.create_task(hangman.play_hangman(message.channel))
        await task

@client.event
async def on_message_edit(before, after):
    global found_ID, MSG, game_ongoing, bots_turn, hangman, prev_word, bad_letters, good_letters, prev_guess, num_missing
    if "Current word" in after.content:
        curr_word = after.content.split("```")
        curr_word = [i for i in curr_word if 'Current word' in i]
        curr_word = curr_word[0].split("\n")[0].split(":")[-1]
        num_missing = len(curr_word)
        curr_word = curr_word.replace("_","")
        num_missing = num_missing - len(curr_word)
        curr_word = curr_word.replace(" ","")
        
        if curr_word != prev_word:
            good_letters = set(curr_word)
            if prev_guess:
                good_letters.add(prev_guess)
            prev_word = curr_word
        else: 
            if prev_guess:
                bad_letters.add(prev_guess)

    if "Please guess a letter." in after.content and game_ongoing:
        bots_turn = True
        task = asyncio.create_task(hangman.play_hangman(after.channel))
        await task
    

if __name__ == "__main__":
    client.run(TOKEN)