import discord
from discord.ext import commands
from discord import Embed, EmbedField
from helpers import firebase_helper, config_helper
from loguru import logger as log
import asyncio


class Ticketing(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Ticketing(bot))  # add the cog to the bot
