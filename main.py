import discord
from dotenv import load_dotenv, get_key
import os

# Initialize variables and the bot
TOKEN = get_key(".env", "DISCORD_TOKEN")
guild_ids = [1230836040588071004]
bot = discord.Bot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} successfully!")


@bot.slash_command(
    guild_ids=guild_ids,
    description="Use this command to test if the bot is online and its latency",
)
async def ping(ctx):
    embed = discord.Embed(
        title="Pong!",
        description=f"The Bot's Latency is {round(bot.latency*1000, 1)}ms",
        colour=discord.Colour.from_rgb(45, 72, 128),
    )
    await ctx.respond(embed=embed)


bot.run(TOKEN)
