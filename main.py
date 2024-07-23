import discord

from dotenv import get_key
import os
import aiosqlite
from helpers.config_helper import *
import helpers.firebase_helper as firebase_helper
from assets.drawer import *
import io

# Initialize variables and the bot
TOKEN: str | None = get_key(
    ".env", "TEST_DISCORD_TOKEN"
)  #! Remove TEST_ for production
guild_ids: list[int] = [1230836040588071004]
intents: discord.Intents = discord.Intents.default()
intents.members = True
bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} successfully!")


cogs_list = [
    "config_cog",
    "info_cog",
    "ranks_cog",
    "stats_cog",
    "ticketing_cog",
    "tester_cog",
]

for cog in cogs_list:
    bot.load_extension(f"cogs.{cog}")

bot.run(TOKEN)
