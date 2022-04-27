import discord
from discord.ext.commands import Bot

from commands.eunga_boy import EungaBoy
from commands.game_baseball import BaseballGame
from commands.game_gamble import GambleGame
from commands.music import Music
from commands.school import School
from commands.utils import Utils
from error_handler import ErrorHandler

TOKEN ='edit your token'
intents = discord.Intents.default()
intents.message_content = True

# 메시지 앞에 접두사(prefix)가 있으면 bot.command() 이벤트가 호출됩니다.
bot = Bot(command_prefix = '!', intents = intents)
