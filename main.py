import discord
from discord.ext.commands import Bot

TOKEN ='edit your token'
intents = discord.Intents.default()
intents.message_content = True
bot = Bot(command_prefix = '!', intents = intents)
