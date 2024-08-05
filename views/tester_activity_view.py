import discord
from helpers import firebase_helper, config_helper


class SetActivityView(discord.ui.View):
    @discord.ui.button(
        label="I'm Active", style=discord.ButtonStyle.primary, emoji="✅"
    )
    async def active_callback(self, button, interaction: discord.Interaction):
        # Check if a tester is active already
        tester_info = firebase_helper.get_tester(interaction.user.id)  # type: ignore incorrect null
        if tester_info == None:
            embed = discord.Embed(title="You're not a tester?!?", color=0xFF3333)
            await interaction.response.send_message(embed=embed)
            return
        if tester_info["isActive"]:
            embed = discord.Embed(title="You're already active!", color=0x33FF33)
            await interaction.response.send_message(embed=embed)

        # Give the tester the active role
        active_role_id = config_helper.get_rank_role_id("online")
        active_role = interaction.guild.get_role(active_role_id)  # type: ignore it is NOT None

        pass
