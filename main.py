# main.py
import os

from bot_singleton import bot


class CtrlAltDefeat:
    token = str(os.getenv("TOKEN"))

    def __init__(self):
        # Bind the on_ready method to the bot instance
        bot.on_ready = self.on_ready.__get__(bot)
        self.load_cogs()
        bot.run(self.token)

    async def on_ready(self):
        print(f"{bot.user} is ready and online")

    def load_cogs(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                bot.load_extension(f"cogs.{filename[:-3]}")


bot_instance = CtrlAltDefeat()
