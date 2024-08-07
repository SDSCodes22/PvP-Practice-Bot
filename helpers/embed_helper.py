from views.tester_activity_view import SetActivityView
from discord import Embed, EmbedField
import discord

LIST = [
    {
        "name": "set activity",
        "content": "",
        "embed": Embed(
            title="Set Activity Status",
            description="As part of our new testing system, use the 2 buttons below to get tickets to test.",
            color=0x3333FF,
        ),
        "view": SetActivityView,
    }
]


async def get_embed_names(ctx: discord.AutocompleteContext):
    output = []
    for i in LIST:
        output.append(i["name"])
    return output
