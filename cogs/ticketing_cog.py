import discord
from discord.ext import commands
from discord import Embed, EmbedField
from helpers import firebase_helper, config_helper
from loguru import logger as log
import asyncio


class Ticketing(commands.Cog):
    def __init__(self, bot) -> None:
        super().__init__()
        self.bot = bot
        self.tasks: set[asyncio.Task] = set()

    async def createTickets(
        self, tester: discord.Member | discord.User, tester_doc: dict | None = None
    ) -> list[int]:
        """Creates appropriate channels (tickets) for the top person in each queue that the tester tests in, adding the tester and testee
        to the channel.

        Args:
            tester (discord.Member | discord.User): The User of the Tester who will be testing here
            tester_doc (dict | None, optional): If already fetehed, the document about the tester. Optional paramater - reduces an API call if you have the value already. Defaults to None.

        Returns:
            list[int]: A list of Channel IDs for each channel created. Returns an empty list if any errors occurred
        """
        # Get the kits the tester tests in
        tester_doc = tester_doc or firebase_helper.get_tester(tester.id)
        if tester_doc == None:
            return []

        channels = []

        # FOR EACH KIT
        for kit in tester_doc["kits"]:
            # If the tester already has an open ticket in this kit, skip
            if int(tester_doc["tickets"][kit]) == 0:
                continue
            # Get top 1 person in that queue
            top_person: int = firebase_helper.get_queue(kit)[0]
            user = self.bot.guild.get_member(top_person)

            # Create a ticket in the correct category
            category_id = config_helper.getCategories()[kit]
            category = self.bot.guild.get_channel(category_id)

            overwrites = {
                self.bot.guild.default_role: discord.PermissionOverwrite(view_channel=False),  # type: ignore
                user: discord.PermissionOverwrite(view_channel=True),
                tester: discord.PermissionOverwrite(view_channel=True),
            }

            ticket_channel = await ctx.guild.create_text_channel(  # type: ignore
                f"{user.name}-{kit.replace('_', '-')}",
                reason=None,
                category=category,
                topic=f"Testing ticket created for {user.display_name}",
                overwrites=overwrites,
            )

            channels.append(ticket_channel.id)

            #   Ping the user id and tester, with a react message
            # Message 1 / 2 - Test Information
            test_info = firebase_helper.get_test_info(user.id, kit)
            if test_info == None:
                return []
            embed = discord.Embed(
                title="Test Information",
                thumbnail=user.avatar.url,
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
                description=f"<@{user.id}>, you have 20 minutes to react with a 👍 to this message, or this ticket will be closed, and you will be moved to the end of the queue. If you react to this and are unable to get tested, you will be punished.",
                color=0xEE3535,
            )

            activity_msg: discord.Message = await ticket_channel.send(
                f"<@{user.id}>", embed=embed
            )
            await activity_msg.add_reaction("👍")

            # DM the User
            embed = discord.Embed(
                title="Your Tier Tester is Ready",
                description=f"Hi {user.display_name}, in the server PvP Practice and Tier Testing, you requested a tier test in {kit.replace('_', ' ').title()}.\nA tester is now ready to test you. Please check the server to get tested ASAP, or you'll be moved to the back of the queue!",
                thumbnail=self.bot.user.avatar.url,
                color=0x45DEDE,
            )

            await user.send(embed=embed)

            # DM the next person in first place
            try:
                next_top_person: int = firebase_helper.get_queue(kit)[0]
                next_user = self.bot.guild.get_member(top_person)
                # DM the User
                embed = discord.Embed(
                    title="Get ready for your Tier Test!",
                    description=f"Hi {user.display_name}, in the server PvP Practice and Tier Testing, you requested a tier test in {kit.replace('_', ' ').title()}.\nThis message is just to let you know that you are the next person to get tested in this kit. Get ready!",
                    thumbnail=self.bot.user.avatar.url,
                    color=0x45DEDE,
                )

                await next_user.send(embed=embed)
            except IndexError as e:
                log.info("Last person in this queue!")
            except Exception as e:
                log.warning(
                    f"Unknown exception, unable to DM next person in queue: {e}"
                )

            # Update the ticket doc and tester doc to a reference of the ticket doc
            firebase_helper.set_test(tester.id, kit, user.id)
            firebase_helper.set_test_channel_id(kit, user.id, ticket_channel.id)

            # If the user has not reacted to the message after 20 minutes, delete the ticket, create the ticket and blah blah blah
            task = asyncio.create_task(
                self.coro_listen_for_reaction(
                    user, tester, activity_msg, ticket_channel, kit
                )
            )
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)
        return channels

    async def coro_listen_for_reaction(
        self,
        check_user: discord.Member | discord.User,
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
            reaction, user = await self.bot.wait_for(
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
            await check_user.send(embed=embed)

            # Tester
            embed = discord.Embed(
                title="New Ticket",
                color=0x3355FF,
                description="A ticket that was opened for you to test was closed. A new one has been opened for you (if there are people in the queue)",
            )
            await tester.send(embed=embed)
            # Add them to the back of the queue
            firebase_helper.send_to_end_of_queue(kit, check_user.id)
            # Update firestore channel IDs
            firebase_helper.set_test(tester.id, kit, 0)
            firebase_helper.set_test_channel_id(kit, check_user.id, 0)

            # Automatically create new tickets for this tester
            await self.createTickets(tester)
        else:
            # Response found
            await ticket_channel.send(
                embed=discord.Embed(
                    title="Let the testing begin!",
                    description=f"{user.display_name} has proved that they are active, so now this test can continue!",
                    color=0x33FF33,
                )
            )


def setup(bot):  # this is called by Pycord to setup the cog
    bot.add_cog(Ticketing(bot))  # add the cog to the bot
