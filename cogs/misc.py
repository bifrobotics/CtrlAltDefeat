from datetime import datetime

import discord
from discord.ext import commands

class Misc(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="ping", description="Get the response time of the bot")
    async def ping(self, ctx):
        # Write a detailed embed message that includes the response time of the bot in ms
        embed = discord.Embed(title="Pong!", description=f"Response time: {round(self.bot.latency * 1000)}ms",
                              color=discord.Color.green(), timestamp=datetime.now())
        embed.set_footer(text=f"Requested by {ctx.user}", icon_url=ctx.user.avatar.url)
        await ctx.respond(embed=embed)


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Misc(bot)) # add the cog to the bot