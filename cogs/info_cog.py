from attr import field
import discord
from discord.ext import commands
from helpers import firebase_helper


class Info(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot

    # Create a command group for info commands
    info_group = discord.SlashCommandGroup(
        name="info",
        description="Contains commands that will give you general information.",
    )

    @commands.slash_command(
        description="Use this command to test if the bot is online and its latency",
    )
    async def ping(self, ctx):
        embed = discord.Embed(
            title="Pong!",
            description=f"The Bot's Latency is {round(self.bot.latency*1000, 1)}ms",
            colour=discord.Colour.from_rgb(45, 72, 128),
        )
        await ctx.respond(embed=embed)

    @info_group.command(description="Get the link to the PvP Practice Rankings Website")
    async def website(self, ctx):
        embed = discord.Embed(
            title="Website Link",
            colour=0x3333FF,
            description="Find the website at: https://pvp-practice.web.app/",
            footer=discord.EmbedFooter(
                icon_url=self.bot.user.avatar.url, text="PvP Practice Bot"
            ),
        )
        await ctx.respond(embed=embed)

    @info_group.command(
        description="Get a list of some servers we recommend testing on."
    )
    async def servers(self, ctx):
        embed = discord.Embed(
            title="MC Testing Servers",
            colour=0x3333FF,
            description="If you're a tester and you aren't happy, DM @sdsiscool (I need help with this)",
            fields=[
                discord.EmbedField("EU:", "`skypractice.xyz`", True),
                discord.EmbedField("EU:", "`chickencraft.nl`", True),
            ],
        )
        await ctx.respond(embed=embed)

    @commands.slash_command(
        description="Check how long since a player was tested in a kit.",
    )
    @discord.option(
        "user",
        discord.Member,
    )
    @discord.option(
        "kit",
        str,
        choices=["Neth Pot", "Sword", "Axe", "Crystal", "UHC", "SMP", "Dia Pot"],
    )
    async def history(self, ctx, user: discord.Member, kit: str):
        days_since_last_test = firebase_helper.get_last_tested(
            ctx.guild_id, user.id, kit, user.avatar.url, user.name  # type: ignore
        )
        embed = discord.Embed(
            title="Last Tested",
            description=f"{user.name} was last tested **{days_since_last_test} day(s) ago** in {kit}.",
            color=discord.Colour.from_rgb(75, 255, 75),
            thumbnail=user.avatar.url,  # type: ignore
        )
        await ctx.respond(embed=embed)


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Info(bot))  # add the cog to the bot
