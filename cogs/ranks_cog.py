import discord
from discord.ext import commands
from regex import F
from sympy import false
from helpers import firebase_helper
from helpers import config_helper

# If you're looking for the implementation of /ranks, you're looking in the wrong place!
# Look at the info cog.


class Ranks(commands.Cog):
    def __init__(self, bot):
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

    # Create the command group
    rank_group = discord.SlashCommandGroup(
        "rank", "All commands related two assigning or viewing ranks."
    )

    @rank_group.command(
        description="[Tier Tester Only command] - Award a tier to a player"
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
        "kit",
        str,
        choices=["Neth Pot", "Sword", "Axe", "Crystal", "Dia Pot", "UHC", "SMP"],
    )
    @discord.option("region", str, choices=["NA", "EU", "AS", "AU", "AF"])
    async def give(
        self,
        ctx,
        rank: str,
        kit: str,
        region: str,
        user: discord.Member,
        score: str,
        bypass: bool = False,
    ):
        await ctx.defer(ephemeral=True)
        allowed: bool = await self._handle_allowed_to_give_rank(
            ctx, user, rank, kit, bypass
        )
        if not allowed:
            return  # response has already been handled

        # Get the previous ranks of the player
        prev_ranks = firebase_helper.get_ranks(
            ctx.guild_id, user.id, user.avatar.url, user.name  # type: ignore
        )
        formatted_kit = kit.replace(" ", "_").lower().strip()
        prev_rank = ""
        try:
            prev_rank = self.INT_MAP[prev_ranks[formatted_kit]]
        except:
            prev_rank = "None"

        # Update the database for this new rank
        firebase_helper.set_rank(
            ctx.guild_id, user.id, kit, self.RANK_MAP[rank], user.avatar.url, user.name  # type: ignore
        )

        # Get the NEW ranks of the player
        ranks = firebase_helper.get_ranks(ctx.guild_id, user.id, user.avatar.url, user.name)  # type: ignore

        #   THIS PART GIVES USER THE APPROPRIATE DISCORD ROLE - THE HIGHEST RANK THEY HAVE ACHIEVED ACROSS ALL KITS

        # Crude way to get max rank the user has in every kit
        max_rank = -1
        for k, v in ranks.items():
            if int(v) > max_rank:
                max_rank = v

        # Remove all tier testing related roles the user already has (eg. LT5)
        all_tier_ids = config_helper.get_all_rank_role_ids()
        for i in all_tier_ids:
            role = ctx.guild.get_role(i)
            if role in user.roles:
                await user.remove_roles(role)

        # Give the user the highest rank they have earned
        max_rank_str = self.INT_MAP[
            max_rank
        ]  # Convert the rank from an int back to a string
        max_rank_id = config_helper.get_rank_role_id(max_rank_str)
        max_rank_role = ctx.guild.get_role(max_rank_id)
        await user.add_roles(max_rank_role, reason="Updated user's tier testing roles.")

        #   THIS PART SENDS THE RESULT IN AN EMBED TO THE RESULTS CHANNEL

        channel_id = (
            config_helper.get_results_channel_id()
        )  # TODO: Handle case when this is not set by user!
        channel = ctx.guild.get_channel(channel_id)

        # Construct an embed
        embed = discord.Embed(
            title=f"{user.name} is now {rank} in {kit}!",
            colour=max_rank_role.color,
            thumbnail=user.avatar.url,  # type: ignore
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

        # Finally respond back to the original tester.
        embed = discord.Embed(
            color=discord.Color.from_rgb(75, 255, 75),
            title="Success",
            description=f"You have successfully granted {user.name} the {rank} tier in {kit}.",
        )
        await ctx.respond(embed=embed, ephemeral=True)

    @rank_group.command(
        description="[TESTER ONLY!] Remove history and tier for a user in the specified kit.",
    )
    @discord.option("user", discord.Member)
    @discord.option(
        "kit",
        str,
        choices=["Neth Pot", "Sword", "Axe", "Crystal", "UHC", "SMP", "Dia Pot"],
    )
    async def remove(self, ctx, user: discord.Member, kit: str):
        # This takes a while to respond, so let's tell discord to be patient
        await ctx.defer()

        if not self._has_role(ctx, "admin", ctx.author):
            embed = discord.Embed(
                color=discord.Color.from_rgb(255, 75, 75),
                title="Insufficient Permissions",
                description="You must be a member of staff to use this command.",
            )
            await ctx.respond(embed=embed, ephemeral=True)
            return
        # Now only Admins

        # Remove the rank
        firebase_helper.remove_rank(ctx.guild_id, user.id, kit, user.avatar.url, user.name)  # type: ignore

        # Get the NEW ranks of the player
        ranks = firebase_helper.get_ranks(ctx.guild_id, user.id, user.avatar.url, user.name)  # type: ignore

        #   THIS PART GIVES USER THE APPROPRIATE DISCORD ROLE - THE HIGHEST RANK THEY HAVE ACHIEVED ACROSS ALL KITS

        # Crude way to get max rank the user has in every kit
        max_rank = -1
        for k, v in ranks.items():
            if int(v) > max_rank:
                max_rank = v
        # Remove all tier testing related roles the user already has (eg. LT5)
        all_tier_ids = config_helper.get_all_rank_role_ids()
        for i in all_tier_ids:
            role = ctx.guild.get_role(i)
            if role in user.roles:
                await user.remove_roles(role)
        if max_rank > 0:
            # Give the user the highest rank they have earned
            max_rank_str = self.INT_MAP[
                max_rank
            ]  # Convert the rank from an int back to a string
            max_rank_id = config_helper.get_rank_role_id(max_rank_str)
            max_rank_role = ctx.guild.get_role(max_rank_id)
            await user.add_roles(
                max_rank_role, reason="Updated user's tier testing roles."
            )

        # Give response to testers
        embed = discord.Embed(
            title=f"Removed {user.display_name}'s tier and history",
            colour=0x33FF33,
            thumbnail=user.avatar.url,  # type: ignore
            description=f"Removed ALL History, and ranks for {user.display_name} in {kit}",
            footer=discord.EmbedFooter("PvP Practice Bot", self.bot.user.avatar.url),  # type: ignore
        )

        await ctx.respond(embed=embed)

    async def _handle_allowed_to_give_rank(self, ctx, user, rank, kit, bypass) -> bool:
        """
        Function to handle the first part of /giverank, which is making sure the user is allowed to give the role.
        Written as a seperate function to make code cleaner, and to reduce length of the giverank function.
        """
        # Only let admins bypass, if not an admin and bypass, then don't do anything
        if bypass:
            if not self._has_role(ctx, "admin", ctx.author):
                embed = discord.Embed(
                    color=discord.Color.from_rgb(255, 75, 75),
                    title="Insufficient Permissions To Use option Bypass",
                    description="Bypass argument removes all restrictions from giving a role. Only staff members can set this to true.",
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return False
        else:
            # We're not bypassing so check the following before doing anything
            # 1. Is this person a tester
            # 2. Is the tested person actually allowed to be re-tested
            # 3. Is the tester allowed to give this high of a tier
            if not self._has_role(ctx, "tester", ctx.author):
                embed = discord.Embed(
                    color=discord.Color.from_rgb(255, 75, 75),
                    title="Insufficient Permissions",
                    description="You must be a Tier Tester to use this command.",
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return False
            # Now only Tier testers

            # Check if it has been less than MIN_TEST_WAIT_TIME days
            days_since_last_test = firebase_helper.get_last_tested(
                ctx.guild_id, user.id, kit, user.avatar.url, user.name  # type: ignore
            )
            if days_since_last_test < config_helper.get_test_cooldown():
                embed = discord.Embed(
                    color=discord.Color.from_rgb(255, 75, 75),
                    title="Unable to re-test this quick!",
                    description=f"A player can test once every {config_helper.get_test_cooldown()} days in a kit, but it has been only {days_since_last_test} day(s) since {user.name} was tested in {kit}.",
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return False

            # Check if the tester is allowed to give this rank
            testers_ranks = firebase_helper.get_ranks(
                ctx.guild_id,
                ctx.author.id,
                ctx.author.avatar.url,
                ctx.author.display_name,
            )
            formatted_kit = kit.lower().strip().replace(" ", "_")
            if testers_ranks[formatted_kit] < self.RANK_MAP[rank]:
                embed = discord.Embed(
                    color=discord.Color.from_rgb(255, 75, 75),
                    title="You are not allowed to award this rank.",
                    description=f"You are only allowed to award a player a maximum of the same rank as you in this kit. You cannot grant them a rank higher than you.\n Contact a <@&1252507321968365568> for help.",
                )
                await ctx.respond(embed=embed, ephemeral=True)
                return False
        return True

    def _has_role(
        self, ctx: discord.ApplicationContext, roleName: str, user: discord.Member
    ) -> bool:
        """
        Returns bool whether discord user has the role, specified with param roleName.
        args:
            -roleName: string representation of each relevant role for this bot. Check config.json if you are unsure what this includes.
            -user: discord user to check for these roles
        """

        role_id = config_helper.get_rank_role_id(roleName)
        print(f"Role ID Found for {roleName}: {role_id}")
        role = ctx.guild.get_role(role_id)  # type: ignore
        print(
            f"Found role? {role != None}. \t Name: {role.name if role != None else 'Unknown'}"
        )
        print(f"User to check for role: {user.display_name}")
        if role == None:
            return False
        return role in user.roles


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Ranks(bot))  # add the cog to the bot
