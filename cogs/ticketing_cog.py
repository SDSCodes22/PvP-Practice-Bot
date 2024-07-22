from helpers import firebase_helper, config_helper
import discord
from discord.ext import commands
import time


class Ticketing(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot

    ticket_group = discord.SlashCommandGroup(
        name="ticket",
        description="Administrator commands /ticket create or /ticket delete",
    )

    test_group = discord.SlashCommandGroup(
        name="test", description="Contains commands related to testing"
    )

    @ticket_group.command(
        description="Admin Command, Create a 'Ticket' in a given category."
    )
    async def create(
        self,
        ctx,
        tester: discord.Member,
        user: discord.Member,
        category: discord.CategoryChannel,
        id: int,
    ):
        """Administrator command to create a new ticket with a tester and a user

        Args:
            ctx (ApplicationContext): Context, given by the command
            tester (discord.Member): The member who will be testing
            user (discord.Member): The person who requested this test
        """
        await self._create_ticket(ctx, tester, user, category, id)
        await ctx.respond("Created!")

    @test_group.command(
        description="Use this command to request a tier test! You will be added to the queue in the requested kit."
    )
    @discord.option(
        "kit",
        str,
        choices=["Sword", "Axe", "Neth Pot", "Dia Pot", "SMP", "UHC", "Crystal"],
    )
    @discord.option("region", str, choices=["EU", "NA", "AS", "AF"])
    @discord.option("officially_tested", str, choices=["Yes", "No"])
    @discord.option("cracked", str, choices=["Yes", "No"])
    async def request(
        self, ctx, kit: str, region: str, officially_tested: str, cracked: str
    ):
        yn_map = {"Yes": True, "No": False}
        official_tested = yn_map[officially_tested]
        isCracked = yn_map[cracked]

        # Check if the player is allowed to be tested again (Last date is > cooldown)
        cooldown = config_helper.get_test_cooldown()
        last_tested = firebase_helper.get_last_tested(
            ctx.guild.id, ctx.author.id, kit, ctx.author.avatar.url, ctx.author.name
        )

        if last_tested < cooldown:
            embed = discord.Embed(
                title="Testing too quickly!",
                color=0xFF3333,
                description=f"You were tested in {kit} {last_tested} day(s) ago. You must wait {cooldown - last_tested} day(s) before getting tested again!",
                footer=discord.EmbedFooter(
                    "PvP Practice Bot", self.bot.user.avatar.url
                ),
            )
            await ctx.respond(embed=embed, ephemeral=True)

        # Create the ticket
        ticket_created = firebase_helper.create_ticket(
            ctx.author, isCracked, kit, region, official_tested
        )

        if ticket_created:
            embed = discord.Embed(
                title="Test Request Created!",
                color=0x22FF22,
                description=f"You have been added to the {kit} queue. Please review the details below",
                fields=[
                    discord.EmbedField("Kit:", kit),
                    discord.EmbedField("Region:", region),
                    discord.EmbedField("Officially Tested?", officially_tested),
                    discord.EmbedField("Cracked?", cracked),
                ],
            )
            await ctx.respond(embed=embed)
        else:
            embed = discord.Embed(
                title="Failed to create Test Request!",
                color=0xFF2222,
                description="It appears that you have already created a test request in this kit. Please remain patient!",
            )
            await ctx.respond(embed=embed, ephemeral=True)

    @test_group.command(description="Check up on any tests that you have requested")
    @discord.option(
        "kit",
        str,
        choices=["Sword", "Axe", "Neth Pot", "Dia Pot", "SMP", "UHC", "Crystal"],
    )
    async def info(self, ctx, kit: str):
        test_info = firebase_helper.get_test_info(ctx.author.id, kit)
        if test_info == None:
            embed = discord.Embed(
                title="Ticket not Found",
                description="It appears that you have not created a ticket for this kit! Use `/ticket request` to request a tier test!",
                color=0xFF3333,
            )
            await ctx.respond(embed=embed)
            return

        hours_since_test = int((time.time() - test_info["time_requested"]) // 3600)
        queue_position = firebase_helper.get_queue_position(ctx.author.id, kit)
        embed = discord.Embed(
            title=f"{ctx.author.display_name}'s {test_info['kit']} Test",
            color=0x3366FF,
            fields=[
                discord.EmbedField("Kit:", kit),
                discord.EmbedField("Hours Waiting:", str(hours_since_test)),
                discord.EmbedField(
                    "Cracked?", "Yes" if test_info["isCracked"] else "No"
                ),
                discord.EmbedField(
                    "Officially Tested?",
                    "Yes" if test_info["tested_official"] else "No",
                ),
                discord.EmbedField("Region:", test_info["region"]),
                discord.EmbedField("Position in Queue:", str(queue_position)),
            ],
        )

        await ctx.respond(embed=embed)

    async def _create_ticket(
        self,
        ctx: discord.ApplicationContext,
        tester: discord.Member,
        user: discord.Member,
        category: discord.CategoryChannel,
        id: int,
    ):

        #       Setup Permissions / Roles
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),  # type: ignore
            user: discord.PermissionOverwrite(view_channel=True),
            tester: discord.PermissionOverwrite(view_channel=True),
        }

        await ctx.guild.create_text_channel(  # type: ignore
            f"{user.name}-{id}",
            reason=None,
            category=category,
            position=id,
            topic=f"Testing ticket created for {user.display_name}",
            overwrites=overwrites,  # type: ignore IDGAF
        )


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Ticketing(bot))  # add the cog to the bot
