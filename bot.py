import os
from typing import Any, Dict

from discord import Embed
from discord.ext import commands
from dotenv import load_dotenv
from requests import Session

load_dotenv()

hyperion_base_url = f"{os.getenv('HYPERION_ENDPOINT')}/api/v1"

hyperion_session = Session()
hyperion_session.headers.update(
    {
        "Authorization": f"Bearer {os.getenv('HYPERION_INTEGRATION_TOKEN')}",
    }
)


bot = commands.Bot(command_prefix="hyp!", description="Hyperion Test Bot")


def generate_debug_embed(resp: Dict[str, Any]) -> Embed:
    embed = Embed()
    embed.colour = (0xFF << 16) + (0x00 << 8) + (0xFF)

    for key, value in resp.items():
        key: str
        embed.add_field(name=key.replace("_", " ").capitalize(), value=str(value))

    return embed


@bot.command()
async def integration(ctx: commands.Context):
    integration_details = hyperion_session.get(f"{hyperion_base_url}/integration")
    integration_details.raise_for_status()
    integration_data = integration_details.json()

    await ctx.reply(embed=generate_debug_embed(integration_data))


@bot.command()
async def integration_connection(ctx: commands.Context):
    integration_connection_details = hyperion_session.get(
        f"{hyperion_base_url}/integration/connection"
    )
    integration_connection_details.raise_for_status()
    integration_data = integration_connection_details.json()

    await ctx.reply(embed=generate_debug_embed(integration_data))


@bot.command()
async def currency(ctx: commands.Context):
    currency_details = hyperion_session.get(f"{hyperion_base_url}/integration/currency")
    currency_details.raise_for_status()
    currency_data = currency_details.json()

    await ctx.reply(embed=generate_debug_embed(currency_data))


bot.run(os.getenv("DISCORD_TOKEN"))
