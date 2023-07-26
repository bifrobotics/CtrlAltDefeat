import datetime

import discord
import os
from dotenv import load_dotenv

load_dotenv()
bot = discord.Bot()

token = str(os.getenv("TOKEN"))

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online")

# get all files in the cogs folder
for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}") # load the cog

bot.run(token) # run the bot with the token