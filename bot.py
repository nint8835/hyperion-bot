import os
from typing import Any, Dict

from discord import Embed
from discord.ext import commands
from dotenv import load_dotenv
from requests import Session

from cogs.currency import Currency
from cogs.debug import Debug

load_dotenv()


bot = commands.Bot(command_prefix="hyp!", description="Hyperion Test Bot")


bot.add_cog(Debug(bot))
bot.add_cog(Currency(bot))

bot.run(os.getenv("DISCORD_TOKEN"))
