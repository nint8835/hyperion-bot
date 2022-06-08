import discord
import requests
from discord import app_commands
from pydantic import BaseSettings


class Config(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    discord_token: str
    hyperion_endpoint: str
    hyperion_integration_token: str

    testing_guild_id: str = "497544520695808000"


config = Config()
guild = discord.Object(config.testing_guild_id)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

session = requests.session()
session.headers.update(
    {
        "Authorization": f"Bearer {config.hyperion_integration_token}",
        "User-Agent": "Hyperion Bot",
    }
)

tree = app_commands.CommandTree(client)


@tree.command(guild=guild)
async def test(interaction: discord.Interaction):
    await interaction.response.send_message("Hello, world!")


@client.event
async def on_ready():
    print("Bot ready, syncing commands")
    await tree.sync(guild=guild)


client.run(config.discord_token)
