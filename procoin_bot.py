import discord
from discord import commands

bot = commands.Bot(command_prefix='&')
bot.load_extension('procoin_cog')

@bot.event
async def on_ready():
    print('Logged in')
    
# TODO implement discord error handling