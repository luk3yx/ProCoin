#!/usr/bin/env python3

import discord # type: ignore
from discord.ext import commands # type: ignore
import os

bot = commands.Bot(command_prefix='&')
bot.load_extension('procoin_cog')

@bot.event
async def on_ready():
    print('Logged in')

# TODO implement discord error handling

# Store the token in token.txt, git should ignore it.
token_file = os.path.join(os.path.dirname(__file__), 'token.txt')
if __name__ == '__main__':
    with open(token_file, 'r') as f:
        token = f.read().strip()
    bot.run(token)
