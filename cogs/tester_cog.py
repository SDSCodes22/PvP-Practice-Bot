# It may be confusing, but this cog will handle more of the tester interaction and monitoring
from pydoc import describe
from discord.ext import commands
import discord
from helpers import config_helper, firebase_helper


class TesterManagement(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot

    tester_command_group = discord.SlashCommandGroup(
        name="tester", description="Commands regarding managing tier testers."
    )

    @tester_command_group.command(
        description="Add a tester to the database, who is able to tier test."
    )
    async def add(
        self,
        ctx,
        user: discord.Member,
        tests_sword: bool,
        tests_axe: bool,
        tests_dia_pot: bool,
        tests_neth_pot: bool,
        tests_crystal: bool,
        tests_uhc: bool,
        tests_smp: bool,
    ) -> None:
        # Add the tester
        tester_added = firebase_helper.add_tester(
            user,
            [
                tests_sword,
                tests_axe,
                tests_dia_pot,
                tests_neth_pot,
                tests_crystal,
                tests_uhc,
                tests_smp,
            ],
        )

        if tester_added:
            embed = discord.Embed(
                title="Added Tester",
                description=f"{user.display_name} has been added as a tier tester, ready to test!",
                color=0x33FF33,
            )
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title="Tester not Added",
                description=f"Unable to add {user.display_name}. They are already a tester!",
                color=0xFF3333,
            )
            await ctx.respond(embed=embed)

    @tester_command_group.command(
        description="Get some info about a particular tier tester"
    )
    async def info(self, ctx, tester: discord.Member):
        info = firebase_helper.get_tester(tester.id)

        if info == None:
            embed = discord.Embed(
                title="Tester not found",
                description=f"{tester.display_name} was not found on the database. Check for a typo, or ask an admin to run /tester add.",
                color=0xFF3333,
            )
            await ctx.respond(embed=embed)
            return

        # Create info
        formatted_kits = ", ".join(
            [
                i.replace("_", " ").title().replace("Smp", "SMP").replace("Uhc", "UHC")
                for i in info["kits"]
            ]
        )

        embed = discord.Embed(
            title=f"About {tester.display_name}",
            description=f"Basic info about {tester.display_name}.",
            color=0x4499FF,
            fields=[
                discord.EmbedField("Tests:", formatted_kits),
                discord.EmbedField("Active Tests:", info["activeTests"]),
                discord.EmbedField("No. 'Testing Sessions':", info["amountActive"]),
                discord.EmbedField(
                    "Able to test right now?:", "Yes" if info["isActive"] else "No"
                ),
            ],
            thumbnail=tester.avatar.url,  # type: ignore
        )

        await ctx.respond(embed=embed)


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(TesterManagement(bot))  # add the cog to the bot
