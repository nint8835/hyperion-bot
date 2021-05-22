from typing import Any, Dict

from discord import Embed
from discord.ext import commands

from .hyperion import hyperion_base_url, hyperion_session


def generate_debug_embed(resp: Dict[str, Any]) -> Embed:
    embed = Embed()
    embed.colour = (0xFF << 16) + (0x00 << 8) + (0xFF)

    for key, value in resp.items():
        key: str
        embed.add_field(name=key.replace("_", " ").capitalize(), value=str(value))

    return embed


class Debug(commands.Cog):
    """Various commands for debugging various things."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def integration(self, ctx: commands.Context):
        """Get details on the integration the bot is authenticated as."""
        integration_details = hyperion_session.get(f"{hyperion_base_url}/integration")
        integration_details.raise_for_status()
        integration_data = integration_details.json()

        await ctx.reply(embed=generate_debug_embed(integration_data))

    @commands.command()
    async def integration_connection(self, ctx: commands.Context):
        """Get details on the integration connection the bot is using."""
        integration_connection_details = hyperion_session.get(
            f"{hyperion_base_url}/integration/connection"
        )
        integration_connection_details.raise_for_status()
        integration_data = integration_connection_details.json()

        await ctx.reply(embed=generate_debug_embed(integration_data))

    @commands.command()
    async def currency(self, ctx: commands.Context):
        """Get details on the currency the bot is connected to."""
        currency_details = hyperion_session.get(
            f"{hyperion_base_url}/integration/currency"
        )
        currency_details.raise_for_status()
        currency_data = currency_details.json()

        await ctx.reply(embed=generate_debug_embed(currency_data))
