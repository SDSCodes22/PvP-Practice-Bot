import discord
from discord.ext import commands
from helpers import firebase_helper
from assets.drawer import *
import io


class Stats(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot
        self.RANK_MAP: dict[str, int] = {
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

        self.INT_MAP: dict[int, str] = {v: k for k, v in self.RANK_MAP.items()}

    @commands.slash_command(description="Check the tiers of a user!")
    @discord.option("user", discord.Member)
    async def ranks(self, ctx, user: discord.Member):
        # In case getting the ranks takes a long time, tell discord to be patient
        # await ctx.defer()
        # Just get the ranks of the current guy my god
        ranks: dict = firebase_helper.get_ranks(ctx.guild_id, user.id, user.avatar.url, user.name)  # type: ignore

        # Construct the embed
        embed = discord.Embed(
            title=f"{user.display_name}'s ranks!",
            color=discord.Colour.from_rgb(49, 102, 63),
            thumbnail=user.avatar.url,  # type: ignore
            fields=[
                discord.EmbedField(
                    "<:neth_pot:1252741729543782441> Neth Pot:",
                    (
                        self.INT_MAP[ranks["neth_pot"]]
                        if ranks["neth_pot"] != 0
                        else "Not Tested"
                    ),
                ),
                discord.EmbedField(
                    "<:sword:1252741569216512113> Sword:",
                    (
                        self.INT_MAP[ranks["sword"]]
                        if ranks["sword"] != 0
                        else "Not Tested"
                    ),
                ),
                discord.EmbedField(
                    "<:axe:1252741528976363610> Axe:",
                    self.INT_MAP[ranks["axe"]] if ranks["axe"] != 0 else "Not Tested",
                ),
                discord.EmbedField(
                    "<:crystal:1252741632349179945> Crystal:",
                    (
                        self.INT_MAP[ranks["crystal"]]
                        if ranks["crystal"] != 0
                        else "Not Tested"
                    ),
                ),
                discord.EmbedField(
                    "<:dia_pot:1252741666612183122> Dia Pot:",
                    (
                        self.INT_MAP[ranks["dia_pot"]]
                        if ranks["dia_pot"] != 0
                        else "Not Tested"
                    ),
                ),
                discord.EmbedField(
                    "<:uhc:1252741833809854535> UHC:",
                    self.INT_MAP[ranks["uhc"]] if ranks["uhc"] != 0 else "Not Tested",
                ),
                discord.EmbedField(
                    "<:smp:1252741772384403528> SMP:",
                    self.INT_MAP[ranks["smp"]] if ranks["smp"] != 0 else "Not Tested",
                ),
            ],
            footer=discord.EmbedFooter(
                text="PvP Practice Bot", icon_url=self.bot.user.avatar.url  # type: ignore
            ),
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(
        description="Check the ELO of a player. (Or just go to the website)",
    )
    @discord.option("user", discord.Member)
    async def elo(self, ctx, user: discord.Member):
        await ctx.defer()
        elo = firebase_helper.get_elo(ctx.guild_id, user.id, user.avatar.url, user.name)  # type: ignore

        embed = discord.Embed(
            color=0x3477EB,
            thumbnail=user.avatar.url,  # type: ignore
            title=f"ELO of {user.display_name}",
            fields=[discord.EmbedField("ELO:", str(elo))],
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(description="Check this server's PvP Leaderboard.")
    async def leaderboard(self, ctx):
        await ctx.defer()
        # Get top 10
        top_10 = firebase_helper.get_leaderboard(ctx.guild_id)
        print(f"Raw top_10: {top_10}")
        members = [ctx.guild.get_member(int(i)) for i in top_10[0]]  # type: ignore
        if None in members:
            members.remove(None)  # Removes members who aren't on the server
        kits = [self.INT_MAP[max(1, i)] for i in top_10[2]]  # type: ignore

        # Create the leaderboard image
        image = await create_leaderboard(members, top_10[1], kits)  # type: ignore

        # Create an send an embed
        with io.BytesIO() as image_binary:
            image.save(image_binary, "PNG")  # type: ignore
            image_binary.seek(0)
            img_file = discord.File(fp=image_binary, filename="image.png")
            embed = discord.Embed(
                title="Server PvP Leaderboard",
                footer=discord.EmbedFooter(
                    text="PvP Practice Bot", icon_url=self.bot.user.avatar.url  # type: ignore
                ),
                color=discord.Colour.from_rgb(50, 127, 168),
                description="See the **Top 10** Overall best PvPers below:",
                image="attachment://image.png",
            )
            await ctx.respond(embed=embed, file=img_file)


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Stats(bot))  # add the cog to the bot
