import discord
from dotenv import load_dotenv, get_key
import os
import aiosqlite
from helper import *
import firebase_helper
from assets.drawer import *
import io

# Initialize variables and the bot
TOKEN = get_key(".env", "DISCORD_TOKEN")
guild_ids = [1230836040588071004]
intents = discord.Intents.default()
intents.members = True
bot = discord.Bot(intents=intents)

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
MIN_TEST_WAIT_TIME = 7


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
)
@discord.option(
    "kit", str, choices=["Neth Pot", "Sword", "Axe", "Crystal", "Dia Pot", "UHC", "SMP"]
)
@discord.option("region", str, choices=["NA", "EU", "AS", "AU", "AF"])
async def giverank(
    ctx,
    rank: str,
    kit: str,
    region: str,
    user: discord.Member,
    score: str,
    bypass: bool = False,
):
    # Only let admins bypass, if not an admin and bypass, then don't do anything
    if bypass:
        db = await initialize_tables()
        # Check if they have the tester rank
        admin_id = await get_rank_id(db, ctx.guild_id, "admin")
        admin_role = ctx.guild.get_role(admin_id)
        if not admin_role in ctx.author.roles:
            embed = discord.Embed(
                color=discord.Color.from_rgb(255, 75, 75),
                title="Insufficient Permissions To Use option Bypass",
                description="Bypass argument removes all restrictions from giving a role. Only staff members can set this to true.",
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
    else:
        # We're not bypassing so check the following before doing anything
        # 1. Is this person a tester
        # 2. Is the tested person actually allowed to be re-tested
        # 3. Is the tester allowed to give this high of a tier
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

        # Check if it has been less than MIN_TEST_WAIT_TIME days
        days_since_last_test = firebase_helper.get_last_tested(
            ctx.guild_id, user.id, kit, user.avatar.url, user.name
        )
        if days_since_last_test < MIN_TEST_WAIT_TIME:
            embed = discord.Embed(
                color=discord.Color.from_rgb(255, 75, 75),
                title="Unable to re-test this quick!",
                description=f"A player can test once every {MIN_TEST_WAIT_TIME} days in a kit, but it has been only {days_since_last_test} day(s) since {user.name} was tested in {kit}.",
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return

        # Check if the tester is allowed to give this rank
        testers_ranks = firebase_helper.get_ranks(
            ctx.guild_id, ctx.author.id, ctx.author.avatar.url, ctx.author.display_name
        )
        formatted_kit = kit.lower().strip().replace(" ", "_")
        if testers_ranks[formatted_kit] < RANK_MAP[rank]:
            embed = discord.Embed(
                color=discord.Color.from_rgb(255, 75, 75),
                title="You are not allowed to award this rank.",
                description=f"You are only allowed to award a player a maximum of the same rank as you in this kit. You cannot grant them a rank higher than you.\n Contact a <@&1252507321968365568> for help.",
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
    # Get the ranks of the player
    prev_ranks = firebase_helper.get_ranks(
        ctx.guild_id, user.id, user.avatar.url, user.name
    )
    formatted_kit = kit.replace(" ", "_").lower().strip()
    prev_rank = ""
    try:
        prev_rank = INT_MAP[prev_ranks[formatted_kit]]
    except:
        prev_rank = "None"
    # Update the database
    firebase_helper.set_rank(
        ctx.guild_id, user.id, kit, RANK_MAP[rank], user.avatar.url, user.name
    )

    # Get the ranks of the player
    ranks = firebase_helper.get_ranks(ctx.guild_id, user.id, user.avatar.url, user.name)

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

    channel_id = 1252421036260196352  # TODO: Store in the sqlite database instead for this guild ID
    channel = ctx.guild.get_channel(channel_id)

    # Construct an embed
    embed = discord.Embed(
        title=f"{user.name} is now {rank} in {kit}!",
        colour=rank_role.color,
        thumbnail=user.avatar.url,
        fields=[
            discord.EmbedField("Previous Rank: ", prev_rank),
            discord.EmbedField("Rank:", rank),
            discord.EmbedField("Kit:", kit),
            discord.EmbedField("Awarded By: ", ctx.author.name),
            discord.EmbedField("Region: ", region),
            discord.EmbedField("Score: ", score),
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
    guild_ids=guild_ids, description="Check this server's PvP Leaderboard."
)
async def leaderboard(ctx):
    await ctx.defer()
    # Get top 10
    top_10 = firebase_helper.get_leaderboard(ctx.guild_id)
    print(f"Raw top_10: {top_10}")
    members = [ctx.guild.get_member(int(i)) for i in top_10[0]]
    if None in members:
        members.remove(None)  # Removes members who aren't on the server
    kits = [INT_MAP[max(1, i)] for i in top_10[2]]

    # Create the leaderboard image
    image = await create_leaderboard(members, top_10[1], kits)

    # Create an send an embed
    with io.BytesIO() as image_binary:
        image.save(image_binary, "PNG")
        image_binary.seek(0)
        img_file = discord.File(fp=image_binary, filename="image.png")
        embed = discord.Embed(
            title="Server PvP Leaderboard",
            footer=discord.EmbedFooter(
                text="PvP Practice Bot", icon_url=bot.user.avatar.url
            ),
            color=discord.Colour.from_rgb(50, 127, 168),
            description="See the **Top 10** Overall best PvPers below:",
            image="attachment://image.png",
        )
        await ctx.respond(embed=embed, file=img_file)


@bot.slash_command(
    guild_ids=guild_ids,
    description="Check how long since a player was tested in a kit.",
)
@discord.option(
    "user",
    discord.Member,
)
@discord.option(
    "kit", str, choices=["Neth Pot", "Sword", "Axe", "Crystal", "UHC", "SMP", "Dia Pot"]
)
async def history(ctx, user: discord.Member, kit: str):
    days_since_last_test = firebase_helper.get_last_tested(
        ctx.guild_id, user.id, kit, user.avatar.url, user.name
    )
    embed = discord.Embed(
        title="Last Tested",
        description=f"{user.name} was last tested **{days_since_last_test} day(s) ago** in {kit}.",
        color=discord.Colour.from_rgb(75, 255, 75),
        thumbnail=user.avatar.url,
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


@bot.slash_command(guild_ids=guild_ids, description="Check the tiers of a user!")
@discord.option("user", discord.Member)
async def ranks(ctx, user: discord.Member):
    # In case getting the ranks takes a long time, tell discord to be patient
    # await ctx.defer()
    # Just get the ranks of the current guy my god
    ranks = firebase_helper.get_ranks(ctx.guild_id, user.id, user.avatar.url, user.name)

    # Construct the embed
    embed = discord.Embed(
        title=f"{user.display_name}'s ranks!",
        color=discord.Colour.from_rgb(49, 102, 63),
        thumbnail=user.avatar.url,
        fields=[
            discord.EmbedField(
                "<:neth_pot:1252741729543782441> Neth Pot:",
                INT_MAP[ranks["neth_pot"]] if ranks["neth_pot"] != 0 else "Not Tested",
            ),
            discord.EmbedField(
                "<:sword:1252741569216512113> Sword:",
                INT_MAP[ranks["sword"]] if ranks["sword"] != 0 else "Not Tested",
            ),
            discord.EmbedField(
                "<:axe:1252741528976363610> Axe:",
                INT_MAP[ranks["axe"]] if ranks["axe"] != 0 else "Not Tested",
            ),
            discord.EmbedField(
                "<:crystal:1252741632349179945> Crystal:",
                INT_MAP[ranks["crystal"]] if ranks["crystal"] != 0 else "Not Tested",
            ),
            discord.EmbedField(
                "<:dia_pot:1252741666612183122> Dia Pot:",
                INT_MAP[ranks["dia_pot"]] if ranks["dia_pot"] != 0 else "Not Tested",
            ),
            discord.EmbedField(
                "<:uhc:1252741833809854535> UHC:",
                INT_MAP[ranks["uhc"]] if ranks["uhc"] != 0 else "Not Tested",
            ),
            discord.EmbedField(
                "<:smp:1252741772384403528> SMP:",
                INT_MAP[ranks["smp"]] if ranks["smp"] != 0 else "Not Tested",
            ),
        ],
        footer=discord.EmbedFooter(
            text="PvP Practice Bot", icon_url=bot.user.avatar.url
        ),
    )
    await ctx.respond(embed=embed)


@bot.slash_command(
    guild_ids=guild_ids,
    description="Check the ELO of a player. (Or just go to the website)",
)
@discord.option("user", discord.Member)
async def elo(ctx, user: discord.Member):
    await ctx.defer()
    elo = firebase_helper.get_elo(ctx.guild_id, user.id, user.avatar.url, user.name)

    embed = discord.Embed(
        color=0x3477EB,
        thumbnail=user.avatar.url,
        title=f"ELO of {user.display_name}",
        fields=[discord.EmbedField("ELO:", str(elo))],
    )
    await ctx.respond(embed=embed)


@bot.slash_command(
    guild_ids=guild_ids,
    description="[TESTER ONLY!] Remove history and tier for a user in the specified kit.",
)
@discord.option("user", discord.Member)
@discord.option(
    "kit", str, choices=["Neth Pot", "Sword", "Axe", "Crystal", "UHC", "SMP", "Dia Pot"]
)
async def removerank(ctx, user: discord.Member, kit: str):
    # This takes a while to respond, so let's tell discord to be patient
    await ctx.defer(ephemeral=True)
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

    # Remove the rank
    firebase_helper.remove_rank(ctx.guild_id, user.id, kit, user.avatar.url, user.name)

    # Give response to testers
    embed = discord.Embed(
        title=f"Removed {user.display_name}'s tier and history",
        colour=0x33FF33,
        thumbnail=user.avatar.url,
        description=f"Removed ALL History, and ranks for {user.display_name} in {kit}",
        footer=discord.EmbedFooter("PvP Practice Bot", bot.user.avatar.url),
    )

    await ctx.respond(embed=embed, ephemeral=True)


bot.run(TOKEN)
