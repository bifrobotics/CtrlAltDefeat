import discord
from dotenv import load_dotenv
import os

load_dotenv()


class SingletonBot(discord.Bot):
    _instance = None

    @staticmethod
    def getInstance():
        if SingletonBot._instance is None:
            SingletonBot._instance = SingletonBot(command_prefix="/", intents=discord.Intents.all())
        return SingletonBot._instance


bot = SingletonBot.getInstance()
