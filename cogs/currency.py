from datetime import datetime, timedelta
from typing import Dict

from discord import Embed
from discord.ext import commands

from .debug import generate_debug_embed
from .hyperion import (
    currency_details,
    hyperion_base_url,
    hyperion_session,
    resolve_account_id,
)

for name, id_ in [("Reoccuring Payout", "reoccuring-payout"), ("Gambling", "gamble")]:
    hyperion_session.post(
        f"{hyperion_base_url}/accounts",
        json={"id": id_, "display_name": name, "system_account": True},
    )


class Currency(commands.Cog):
    """Exposes basic Hyperion functionality via Discord."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.payouts: Dict[str, datetime] = {}

    @commands.command()
    async def openaccount(self, ctx: commands.Context):
        """Open a new account."""
        resp = hyperion_session.post(
            f"{hyperion_base_url}/accounts",
            json={
                "id": ctx.author.id,
                "starting_balance": 100,
                "display_name": ctx.author.name,
            },
        )

        if resp.status_code == 409:
            await ctx.reply(
                "You already have an account, so you cannot open a new one."
            )
            return

        await ctx.reply(
            f"Opened new account with starting balance of 100 {currency_details['plural_form']}."
        )

    @commands.command()
    async def payout(self, ctx: commands.Context):
        """Receive a reoccuring payout."""
        if (
            ctx.author.id in self.payouts
            and datetime.now() < self.payouts[ctx.author.id]
        ):
            await ctx.reply(
                "You've already received your scheduled payout - check back later!"
            )
            return

        transaction_create_resp = hyperion_session.post(
            f"{hyperion_base_url}/transactions",
            json={
                "source_account_id": "reoccuring-payout",
                "dest_account_id": ctx.author.id,
                "amount": 10,
            },
        )

        if transaction_create_resp.status_code == 404:
            await ctx.reply(
                "You don't have an account! Use `hyp!openaccount` to create one first."
            )
            return

        transaction_id = transaction_create_resp.json()["id"]

        exec_resp = hyperion_session.post(
            f"{hyperion_base_url}/transactions/{transaction_id}/execute"
        )
        exec_resp.raise_for_status()
        await ctx.reply(
            f"You've received a payout of 10 {currency_details['plural_form']}."
        )
        self.payouts[ctx.author.id] = datetime.now() + timedelta(days=1)

    @commands.command()
    async def ledger(self, ctx: commands.Context):
        """Get a list of all transactions for this currency."""
        transactions_resp = hyperion_session.get(f"{hyperion_base_url}/transactions")

        resp_lines = []

        for transaction in transactions_resp.json()[-10:]:
            source_account = resolve_account_id(transaction["source_account_id"])
            source_name = source_account["display_name"] or source_account["id"]
            dest_account = resolve_account_id(transaction["dest_account_id"])
            dest_name = dest_account["display_name"] or dest_account["id"]

            status_message = transaction["state"].capitalize()
            if transaction["state_reason"] is not None:
                status_message += f" ({transaction['state_reason']})"
            resp_lines.append(
                f"{source_name} -> {dest_name}: {transaction['amount']} {currency_details['shortcode']} - {status_message}"
            )

        resp = "\n".join(resp_lines)
        await ctx.reply(f"```\n{resp}\n```")
