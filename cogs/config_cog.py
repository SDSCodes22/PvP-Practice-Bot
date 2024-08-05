import discord
from discord.ext import commands
from helpers import config_helper


class Config(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot

    # create a command group
    config_group = discord.SlashCommandGroup(
        name="config",
        description="This command allows you to condigure some options in the bot. Admin only.",
    )

    @config_group.command(
        description="Set up the roles for the bot, so that it can understand and do things for you."
    )
    @commands.has_permissions(administrator=True)
    async def roles(
        self,
        ctx,
        admin: discord.Role,
        tester: discord.Role,
        manager: discord.Role,
        lt5: discord.Role,
        ht5: discord.Role,
        lt4: discord.Role,
        ht4: discord.Role,
        lt3: discord.Role,
        ht3: discord.Role,
        lt2: discord.Role,
        ht2: discord.Role,
        lt1: discord.Role,
        ht1: discord.Role,
        online: discord.Role,
        offline: discord.Role,
    ):

        config_helper.configure_roles(
            admin.id,
            tester.id,
            manager.id,
            lt5.id,
            ht5.id,
            lt4.id,
            ht4.id,
            lt3.id,
            ht3.id,
            lt2.id,
            ht2.id,
            lt1.id,
            ht1.id,
            online.id,
            offline.id,
        )

        await ctx.respond("Updated roles for bot successfully!", ephemeral=True)

    @config_group.command(description="Set which channel will be used to post results")
    @commands.has_permissions(administrator=True)
    async def resultschannel(self, ctx, channel: discord.TextChannel):
        config_helper.set_results_channel_id(channel.id)
        await ctx.respond(f"Successfully set the text channel to <#{channel.id}>")

    @config_group.command(
        description="Set how long a person must wait between tests in a kit"
    )
    @commands.has_permissions(administrator=True)
    async def cooldown(self, ctx, days: int):
        config_helper.set_test_cooldown(days)
        await ctx.respond(f"Successfully set the test cooldown to {days} day(s)")

    @config_group.command(
        description="Set the different categories to create tickets under"
    )
    @commands.has_permissions(administrator=True)
    async def categories(
        self,
        ctx,
        sword: discord.CategoryChannel,
        axe: discord.CategoryChannel,
        dia_pot: discord.CategoryChannel,
        neth_pot: discord.CategoryChannel,
        crystal: discord.CategoryChannel,
        smp: discord.CategoryChannel,
        uhc: discord.CategoryChannel,
    ):
        config_helper.configureCategories(
            sword.id, axe.id, neth_pot.id, dia_pot.id, crystal.id, uhc.id, smp.id
        )
        await ctx.respond("Sucessfully set the categories for creating tickets")


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Config(bot))  # add the cog to the bot
