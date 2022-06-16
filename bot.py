from datetime import datetime
from typing import Optional
from uuid import UUID

import discord
import requests
from discord import app_commands
from pydantic import BaseModel, BaseSettings


class Config(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    discord_token: str
    hyperion_endpoint: str
    hyperion_integration_token: str

    testing_guild_id: str = "497544520695808000"


class Currency(BaseModel):
    id: UUID
    name: str
    singular_form: str
    plural_form: str
    shortcode: str
    owner_id: str
    date_created: datetime
    date_modified: datetime


class Transaction(BaseModel):
    id: UUID
    amount: int
    state: str
    state_reason: Optional[str]
    description: Optional[str]
    source_currency_id: UUID
    source_account_id: str
    dest_currency_id: UUID
    dest_account_id: str
    integration_id: UUID
    date_created: datetime
    date_modified: datetime


class Account(BaseModel):
    id: str
    currency_id: UUID
    balance: int
    effective_balance: int
    date_created: datetime
    date_modified: datetime
    system_account: bool
    display_name: Optional[str]


config = Config()

guild = discord.Object(config.testing_guild_id)
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

hyperion_session = requests.session()
hyperion_session.headers.update(
    {
        "Authorization": f"Bearer {config.hyperion_integration_token}",
        "User-Agent": "Hyperion Bot",
    }
)

hyperion_session.post(
    f"{config.hyperion_endpoint}/api/v1/accounts",
    json={
        "id": "recurring-payout",
        "display_name": "Recurring Payout",
        "system_account": True,
    },
)

currency_details_resp = hyperion_session.get(
    f"{config.hyperion_endpoint}/api/v1/integration/currency"
)
currency = Currency(**currency_details_resp.json())


def get_last_payout_time(user_id: int) -> Optional[datetime]:
    transactions_resp = hyperion_session.get(
        f"{config.hyperion_endpoint}/api/v1/transactions",
    )

    transactions = [
        Transaction(**transaction) for transaction in transactions_resp.json()
    ]

    user_payouts = [
        transaction
        for transaction in transactions
        if transaction.source_account_id == "recurring-payout"
        and transaction.dest_account_id == str(user_id)
    ]

    if len(user_payouts) != 0:
        return user_payouts[-1].date_created

    return None


@tree.command(guild=guild)
async def openaccount(interaction: discord.Interaction):
    """Open a new Hyperion account."""
    resp = hyperion_session.post(
        f"{config.hyperion_endpoint}/api/v1/accounts",
        json={
            "id": interaction.user.id,
            "display_name": interaction.user.name,
            "system_account": False,
        },
    )

    if resp.status_code == 409:
        await interaction.response.send_message(
            "You already have an account.", ephemeral=True
        )
        return

    await interaction.response.send_message("Account opened.")


@tree.command(guild=guild)
async def daily(interaction: discord.Interaction):
    """Get your daily payout."""
    last_payout_time = get_last_payout_time(interaction.user.id)
    if (
        last_payout_time is not None
        and (datetime.utcnow() - last_payout_time).total_seconds() < 60 * 60 * 24
    ):
        await interaction.response.send_message(
            "You have already received your daily payout.", ephemeral=True
        )
        return

    transaction_resp = hyperion_session.post(
        f"{config.hyperion_endpoint}/api/v1/transactions",
        json={
            "source_account_id": "recurring-payout",
            "dest_account_id": interaction.user.id,
            "amount": 10,
            "description": "Daily payout",
        },
    )
    if transaction_resp.status_code != 200:
        await interaction.response.send_message(
            f"Error creating transaction.\n```\n{transaction_resp.json()['detail']}\n```",
        )
        return
    transaction = Transaction(**transaction_resp.json())

    execution_resp = hyperion_session.post(
        f"{config.hyperion_endpoint}/api/v1/transactions/{transaction.id}/execute",
    )
    if execution_resp.status_code != 200:
        await interaction.response.send_message(
            f"Error executing transaction.\n```\n{execution_resp.json()['detail']}\n```",
        )
        return

    await interaction.response.send_message(
        f"You have received a daily payout of 10 {currency.plural_form}."
    )


@tree.command(guild=guild)
async def balance(interaction: discord.Interaction, user: Optional[discord.User]):
    """Get balance of a user."""

    if user is None:
        user = interaction.user

    resp = hyperion_session.get(f"{config.hyperion_endpoint}/api/v1/accounts/{user.id}")
    if resp.status_code != 200:
        await interaction.response.send_message(
            f"Error getting account.\n```\n{resp.json()['detail']}\n```",
        )
        return

    prefix = "You have" if user == interaction.user else f"{user.name} has"

    account = Account(**resp.json())
    await interaction.response.send_message(
        f"{prefix} {account.balance} {currency.plural_form}."
    )


@tree.command(guild=guild)
async def send(
    interaction: discord.Interaction,
    user: discord.User,
    amount: int,
    description: Optional[str],
):
    """Send currency to another user."""
    resp = hyperion_session.post(
        f"{config.hyperion_endpoint}/api/v1/transactions",
        json={
            "source_account_id": interaction.user.id,
            "dest_account_id": user.id,
            "amount": amount,
            "description": description,
        },
    )
    if resp.status_code != 200:
        await interaction.response.send_message(
            f"Error creating transaction.\n```\n{resp.json()['detail']}\n```",
        )
        return

    transaction = Transaction(**resp.json())

    execution_resp = hyperion_session.post(
        f"{config.hyperion_endpoint}/api/v1/transactions/{transaction.id}/execute",
    )
    if execution_resp.status_code != 200:
        await interaction.response.send_message(
            f"Error executing transaction.\n```\n{execution_resp.json()['detail']}\n```",
        )
        return

    new_transaction = Transaction(**execution_resp.json())
    if new_transaction.state != "complete":
        await interaction.response.send_message(
            f"Transaction {new_transaction.state} - {new_transaction.state_reason}",
        )
        return

    await interaction.response.send_message(
        f"You have sent {amount} {currency.plural_form} to {user.name}."
    )


@client.event
async def on_ready():
    print("Bot ready, syncing commands")
    await tree.sync(guild=guild)


client.run(config.discord_token)
