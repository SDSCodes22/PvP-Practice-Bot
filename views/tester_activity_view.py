import discord
from discord.ui.item import Item
from helpers import firebase_helper, config_helper
from cogs import ticketing_cog
from discord import EmbedField
from loguru import logger as log
import asyncio


class SetActivityView(discord.ui.View):
    def __init__(
        self,
        *items: Item,
        timeout: float | None = 180,
        disable_on_timeout: bool = False,
    ):
        super().__init__(*items, timeout=timeout, disable_on_timeout=disable_on_timeout)
        self.tasks: set[asyncio.Task] = set()

    @discord.ui.button(
        label="I'm Online", style=discord.ButtonStyle.primary, emoji="✅"
    )
    async def active_callback(self, button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, invisible=False)
        log.debug("Active button callback!")
        # Check if a tester is active already
        tester_info = firebase_helper.get_tester(interaction.user.id)  # type: ignore incorrect null
        if tester_info == None:
            embed = discord.Embed(title="You're not a tester?!?", color=0xFF3333)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        if tester_info["isActive"]:
            embed = discord.Embed(title="You're already active!", color=0x33FF33)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        log.debug("Is a tester which is not active.")
        # Give the tester the active role
        active_role_id = config_helper.get_rank_role_id("online")
        active_role = interaction.guild.get_role(active_role_id)  # type: ignore it is NOT None

        inactive_role_id = config_helper.get_rank_role_id("offline")
        inactive_role = interaction.guild.get_role(inactive_role_id)  # type: ignore
        if active_role != None:
            await interaction.user.add_roles(active_role, reason="online")  # type: ignore
        if inactive_role != None:
            await interaction.user.remove_roles(inactive_role, reason="online")  # type: ignore

        log.debug("Gave roles...")
        # Create tickets for the tester
        tickets: list[int] = await self.createTickets(
            interaction, interaction.user, tester_info
        )

        log.debug("Tickets created!")

        # Update tester doc
        firebase_helper.set_tester_active(interaction.user.id)  # type: ignore
        embed = discord.Embed(
            title="You are now active.",
            description="Check your channels, tickets should have automatically been made and assigned to you.",
            color=0x33FF33,
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        log.debug("Doc updated!")

    @discord.ui.button(
        label="I'm Offline", style=discord.ButtonStyle.secondary, emoji="👋"
    )
    async def inactive_callback(self, button, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, invisible=False)
        # Check that the tester is active already and that it is a a tester
        tester_info = firebase_helper.get_tester(interaction.user.id)  # type: ignore incorrect null
        if tester_info == None:
            embed = discord.Embed(title="You're not a tester?!?", color=0xFF3333)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        if not tester_info["isActive"]:
            embed = discord.Embed(title="You're already offline!", color=0x33FF33)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Give the tester the offline role, and remove the online role, if they have it
        active_role_id = config_helper.get_rank_role_id("online")
        active_role = interaction.guild.get_role(active_role_id)  # type: ignore it is NOT None

        inactive_role_id = config_helper.get_rank_role_id("offline")
        inactive_role = interaction.guild.get_role(inactive_role_id)  # type: ignore
        if active_role != None:
            await interaction.user.remove_roles(active_role, reason="offline")  # type: ignore
        if inactive_role != None:
            await interaction.user.add_roles(inactive_role, reason="offline")  # type: ignore

        # For each ticket:
        for k, v in tester_info["tickets"].items():
            log.debug(f"In loop of tickets: \t k: {k}, v: {v}")
            if str(v) == "0":
                continue
            log.debug(f"Has ticket for: \t k: {k}, v: {v}")
            #   Delete all channels that are open still
            doc = firebase_helper.get_test_info(v, k)
            if doc == None:
                continue
            channel_id = doc["channel_id"]
            channel = interaction.guild.get_channel(int(channel_id))  # type: ignore
            if channel != None:
                await channel.delete(reason="Tester became offline")

            #   DM Users whos tickets were closed
            nice_kit = k.replace("_", " ").title().strip()
            embed = discord.Embed(
                title="Ticket Closed",
                color=0xFF5555,
                description=f"The ticket that was created for your tier test in {nice_kit} was unfortunately closed because your tester went offline. Don't fret, you're still 1st in the queue, and will get tested soon! Sorry for the inconvenience.",
            )
            user = interaction.guild.get_member(v)  # type: ignore
            if user != None:
                await user.send(embed=embed)
            #   Update ticket document and tester document
            firebase_helper.set_test_channel_id(k, v, 0)
            firebase_helper.set_test(interaction.user.id, k, 0)  # type: ignore
        # Set tester's isActive to false
        firebase_helper.set_tester_inactive(interaction.user.id)  # type: ignore

        await interaction.followup.send("You're now inactive", ephemeral=True)

    async def createTickets(
        self,
        interaction: discord.Interaction,
        tester: discord.Member | discord.User | None,
        tester_doc: dict | None = None,
    ) -> list[int]:
        """Creates appropriate channels (tickets) for the top person in each queue that the tester tests in, adding the tester and testee
        to the channel.

        Args:
            tester (discord.Member | discord.User): The User of the Tester who will be testing here
            tester_doc (dict | None, optional): If already fetehed, the document about the tester. Optional paramater - reduces an API call if you have the value already. Defaults to None.

        Returns:
            list[int]: A list of Channel IDs for each channel created. Returns an empty list if any errors occurred
        """
        if tester == None:
            return []
        # Get the kits the tester tests in
        tester_doc = tester_doc or firebase_helper.get_tester(tester.id)
        if tester_doc == None:
            return []

        channels = []
        log.debug(f"Kits: {tester_doc['kits']}")
        # FOR EACH KIT
        for kit in tester_doc["kits"]:
            # If the tester already has an open ticket in this kit, skip
            if int(tester_doc["tickets"][kit]) != 0:
                continue
            # Get top 1 person in that queue
            try:
                top_person: int = firebase_helper.get_queue(kit)[0]
            except IndexError:
                # There are no people in this queue
                continue
            user = interaction.guild.get_member(top_person)  # type: ignore
            log.debug(
                f"User is None: {'Yes' if user == None else 'No'}\nuser name: {user.display_name}"  # type: ignore NOT NONE
            )
            # Create a ticket in the correct category
            category_id = config_helper.getCategories()[kit]
            category = interaction.guild.get_channel(category_id)  # type: ignore

            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),  # type: ignore
                user: discord.PermissionOverwrite(view_channel=True),
                tester: discord.PermissionOverwrite(view_channel=True),
            }

            ticket_channel = await interaction.guild.create_text_channel(  # type: ignore
                f"{user.name}-{kit.replace('_', '-')}",  # type: ignore
                reason=None,
                category=category,  # type: ignore
                topic=f"Testing ticket created for {user.display_name}",  # type: ignore
                overwrites=overwrites,  # type: ignore
            )
            log.debug(f"Ticket channel ID: {ticket_channel.id}")
            channels.append(ticket_channel.id)

            #   Ping the user id and tester, with a react message
            # Message 1 / 2 - Test Information
            test_info = firebase_helper.get_test_info(user.id, kit)  # type: ignore
            if test_info == None:
                return []
            embed = discord.Embed(
                title="Test Information",
                thumbnail=user.avatar.url,  # type: ignore
                color=0x44BDFF,
                fields=[
                    EmbedField("Kit:", test_info["kit"].replace("_", " ").title()),
                    EmbedField("Cracked:", "Yes" if test_info["isCracked"] else "No"),
                    EmbedField("Region:", test_info["region"]),
                    EmbedField(
                        "Officially Tested:",
                        "Yes" if test_info["tested_official"] else "No",
                    ),
                ],
            )

            await ticket_channel.send(f"<@{tester.id}>", embed=embed)

            # Message 2 / 2  - Activity Check
            embed = discord.Embed(
                title="Activity Check",
                description=f"<@{user.id}>, you have 20 minutes to react with a 👍 to this message, or this ticket will be closed, and you will be moved to the end of the queue. If you react to this and are unable to get tested, you will be punished.",  # type: ignore
                color=0xEE3535,
            )

            activity_msg: discord.Message = await ticket_channel.send(
                f"<@{user.id}>", embed=embed  # type: ignore
            )
            await activity_msg.add_reaction("👍")

            # DM the User
            embed = discord.Embed(
                title="Your Tier Tester is Ready",
                description=f"Hi {user.display_name}, in the server PvP Practice and Tier Testing, you requested a tier test in {kit.replace('_', ' ').title()}.\nA tester is now ready to test you. Please check the server to get tested ASAP, or you'll be moved to the back of the queue!",  # type: ignore
                thumbnail=interaction.user.avatar.url,  # type: ignore
                color=0x45DEDE,
            )

            await user.send(embed=embed)  # type: ignore
            # DM the next person in first place
            try:
                next_top_person: int = firebase_helper.get_queue(kit)[1]
                next_user = interaction.guild.get_member(top_person)  # type: ignore
                # DM the User
                embed = discord.Embed(
                    title="Get ready for your Tier Test!",
                    description=f"Hi {user.display_name}, in the server PvP Practice and Tier Testing, you requested a tier test in {kit.replace('_', ' ').title()}.\nThis message is just to let you know that you are the next person to get tested in this kit. Get ready!",  # type: ignore
                    color=0x45DEDE,
                )

                await next_user.send(embed=embed)  # type: ignore
            except IndexError as e:
                log.info("Last person in this queue!")
            except Exception as e:
                log.warning(
                    f"Unknown exception, unable to DM next person in queue: {e}"
                )

            # Update the ticket doc and tester doc to a reference of the ticket doc
            firebase_helper.set_test(tester.id, kit, user.id)  # type: ignore
            firebase_helper.set_test_channel_id(kit, user.id, ticket_channel.id)  # type: ignore

            # If the user has not reacted to the message after 20 minutes, delete the ticket, create the ticket and blah blah blah
            task = asyncio.create_task(
                self.coro_listen_for_reaction(
                    interaction, user, tester, activity_msg, ticket_channel, kit
                )
            )
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)
        return channels

    async def coro_listen_for_reaction(
        self,
        interaction: discord.Interaction,
        check_user: discord.Member | None,
        tester: discord.Member | discord.User,
        message: discord.Message,
        ticket_channel: discord.TextChannel,
        kit: str,
    ):
        def check(reaction, user):
            return (
                user == check_user
                and str(reaction.emoji) == "👍"
                and reaction.message == message
            )

        try:
            reaction, user = await interaction.client.wait_for(
                "reaction_add", timeout=1200.0, check=check
            )
        except asyncio.TimeoutError:
            # 20 Minutes has passed with no response
            # Delete the text channel
            await ticket_channel.delete(
                reason="Testee did not respond. Closing ticket."
            )

            #       DM the user & tester
            # User
            embed = discord.Embed(
                title="Ticket Closed due to Inactivity",
                color=0xFF3333,
                description=f"A Tier Testing ticket was opened for your {kit} request, because you were next in the queue. Due to you being inactive, the ticket has automatically been closed and you have been moved to the end of the queue.",
            )
            await check_user.send(embed=embed)  # type: ignore

            # Tester
            embed = discord.Embed(
                title="New Ticket",
                color=0x3355FF,
                description="A ticket that was opened for you to test was closed. A new one has been opened for you (if there are people in the queue)",
            )
            await tester.send(embed=embed)
            # Add them to the back of the queue
            firebase_helper.send_to_end_of_queue(kit, check_user.id)  # type: ignore
            # Update firestore channel IDs
            firebase_helper.set_test(tester.id, kit, 0)
            firebase_helper.set_test_channel_id(kit, check_user.id, 0)  # type: ignore

            # Automatically create new tickets for this tester
            await self.createTickets(interaction, tester)
        else:
            # Response found
            await ticket_channel.send(
                embed=discord.Embed(
                    title="Let the testing begin!",
                    description=f"{user.display_name} has proved that they are active, so now this test can continue!",
                    color=0x33FF33,
                )
            )
