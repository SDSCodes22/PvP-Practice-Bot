import discord
from dotenv import load_dotenv, get_key
import os
import aiosqlite
from helper import *
import firebase_helper

# Initialize variables and the bot
TOKEN = get_key(".env", "DISCORD_TOKEN")
guild_ids = [1230836040588071004]
bot = discord.Bot()

RANK_MAP = {
    "LT5": 1,
    "HT5": 2,
    "LT4": 3,
    "HT4": 4,
    "LT3": 5,
    "HT3": 6,
    "LT2": 7,
    "HT2": 8,
    "LT1": 9,
    "HT1": 10,
}

INT_MAP = {v: k for k, v in RANK_MAP.items()}

# Number of days before a player can test again
MIN_TEST_WAIT_TIME = 30


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
    description="[Tier Tester Only command] - Award a tier to a player",
)
@discord.option(
    "rank",
    str,
    choices=["LT5", "HT5", "LT4", "HT4", "LT3", "HT3", "LT2", "HT2", "LT1", "HT1"],
)
@discord.option(
    "user",
    discord.Member,
    choices=["LT5", "HT5", "LT4", "HT4", "LT3", "HT3", "LT2", "HT2", "LT1", "HT1"],
)
@discord.option("kit", str, choices=["Neth Pot", "Sword", "Axe", "Crystal"])
async def giverank(ctx, rank: str, kit: str, user: discord.Member, score: str):
    db = await initialize_tables()
    # Check if they have the tester rank
    tester_id = await get_rank_id(db, ctx.guild_id, "tester")
    tester_role = ctx.guild.get_role(tester_id)
    if not tester_role in ctx.author.roles:
        embed = discord.Embed(
            color=discord.Color.from_rgb(255, 75, 75),
            title="Insufficient Permissions",
            description="You must be a Tier Tester to use this command.",
        )
        await ctx.respond(embed=embed, ephemeral=True)
        return
    # Now only Tier testers
    # Update the database
    firebase_helper.set_rank(ctx.guild_id, user.id, kit, RANK_MAP[rank])

    # Get the ranks of the player
    ranks = firebase_helper.get_ranks(ctx.guild_id, user.id)

    # Crude way to get max rank
    max_rank = -1
    for k, v in ranks.items():
        if int(v) > max_rank:
            max_rank = v

    # Get the rank and award this to the player
    all_tier_ids = await get_all_tier_ids(db, ctx.guild_id)
    for i in all_tier_ids:
        role = ctx.guild.get_role(i)
        if role in user.roles:
            await user.remove_roles(role)

    print(f"INT MAP: {INT_MAP}")
    rank_str = INT_MAP[max_rank]
    rank_id = await get_rank_id(db, ctx.guild_id, rank_str.lower())
    # Award this rank
    rank_role = ctx.guild.get_role(rank_id)
    print(f"dbug, rank_role: {rank_role}")
    await user.add_roles(rank_role, reason="Updated user's tier testing roles.")

    channel_id = 1244288786247057489  # TODO: Store in the sqlite database instead for this guild ID
    channel = ctx.guild.get_channel(channel_id)

    # Construct an embed
    embed = discord.Embed(
        title=f"{user.name} is now {rank} in {kit}!",
        colour=rank_role.color,
        image=user.avatar.url,
        fields=[
            discord.EmbedField("Rank:", rank),
            discord.EmbedField("Kit:", kit),
            discord.EmbedField("Awarded By: ", ctx.author.name),
        ],
    )

    await channel.send(embed=embed)

    embed = discord.Embed(
        color=discord.Color.from_rgb(75, 255, 75),
        title="Success",
        description=f"You have successfully granted {user.name} the {rank} tier in {kit}.",
    )
    await ctx.respond(embed=embed, ephemeral=True)


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


bot.run(TOKEN)
