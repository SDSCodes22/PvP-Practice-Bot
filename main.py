import discord
from dotenv import load_dotenv, get_key
import os
import aiosqlite

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


@bot.slash_command(
    guild_ids=guild_ids,
    description="[Admin only command] - Configure roles for this bot.",
)
async def configroles(
    ctx,
    admin_role: discord.Option(discord.Role),
    tier_tester_role: discord.Option(discord.Role),
    lt5_role: discord.Option(discord.Role),
    ht5_role: discord.Option(discord.Role),
    lt4_role: discord.Option(discord.Role),
    ht4_role: discord.Option(discord.Role),
    lt3_role: discord.Option(discord.Role),
    ht3_role: discord.Option(discord.Role),
    lt2_role: discord.Option(discord.Role),
    ht2_role: discord.Option(discord.Role),
    lt1_role: discord.Option(discord.Role),
    ht1_role: discord.Option(discord.Role),
):

    ids = [
        admin_role.id,
        tier_tester_role.id,
        lt5_role.id,
        ht5_role.id,
        lt4_role.id,
        ht4_role.id,
        lt3_role.id,
        ht3_role.id,
        lt2_role.id,
        ht2_role.id,
        lt1_role.id,
        ht1_role.id,
    ]
    db = await initialize_tables()
    await db.execute(
        f"""
    DELETE FROM roles_list WHERE Guild_ID = {ctx.guild_id};
    """
    )
    await db.execute(
        f"""
    INSERT INTO roles_list( Guild_ID, Admin_ID, Tester_ID, LT5_ID, HT5_ID, LT4_ID, HT4_ID, LT3_ID, HT3_ID, LT2_ID, HT2_ID, LT1_ID, HT1_ID)
    VALUES ({ctx.guild_id},{ids[0]}, {ids[1]},  {ids[2]}, {ids[3]}, {ids[4]}, {ids[5]}, {ids[6]}, {ids[7]}, {ids[8]}, {ids[9]}, {ids[10]}, {ids[11]})
    """
    )
    await db.commit()
    await ctx.respond("Success!", ephemeral=True)


async def initialize_tables():
    """
    Creates 2 tables in the directory database.db,
    0 - member_list:
        cols: GUILD_ID (int), PLAYER (str), RANK (int)
        rows: each row is a player
    1 - roles_list:
        cols: GUILD_ID (int), ADMIN_ID (int), TESTER_ID (int), LT5_ID (int), HT5_ID (int), LT4_ID (int), HT4_ID (int), LT3_ID (int), HT3_ID (int), LT2_ID (int), HT2_ID (int), LT1_ID (int), HT1_ID (int)
    """
    db_path = os.path.join(os.path.dirname(__file__), "database.db")
    db = await aiosqlite.connect(db_path)
    cursor = await db.execute(
        """
    CREATE TABLE IF NOT EXISTS member_list (
        Guild_ID int,
        Player varchar(255),
        Rank int
    );
    """
    )
    await db.execute(
        """
    CREATE TABLE IF NOT EXISTS roles_list (
        Guild_ID int,
        Admin_ID int,
        Tester_ID int,
        LT5_ID int,
        HT5_ID int,
        LT4_ID int,
        HT4_ID int,
        LT3_ID int,
        HT3_ID int,
        LT2_ID int,
        HT2_ID int,
        LT1_ID int,
        HT1_ID int
    );
    """
    )
    await db.commit()
    return db


bot.run(TOKEN)
