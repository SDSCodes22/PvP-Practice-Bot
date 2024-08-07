import discord
from discord import ApplicationContext, Embed, EmbedField
from discord.ext import commands
from views.tester_activity_view import SetActivityView
from helpers import embed_helper

# @sdsiscool on discord


class EmbedSender(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    embed_group = discord.SlashCommandGroup(
        "embed", description="Commands relating to embed fields"
    )

    @embed_group.command(
        description="Send an Embed from the defined Embed List (Check source code)"
    )
    @commands.has_permissions(administrator=True)
    async def send(self, ctx: ApplicationContext, embed: discord.Option(str, autocomplete=discord.utils.basic_autocomplete(embed_helper.get_embed_names))) -> None:  # type: ignore
        for i in embed_helper.LIST:
            if i["name"] != embed:
                continue
            # This is the embed we want to send
            await ctx.channel.send(content=i["content"], embed=i["embed"], view=i["view"]())  # type: ignore
            await ctx.respond("Successfully sent embed to this channel", ephemeral=True)


def setup(bot):
    bot.add_cog(EmbedSender(bot))
