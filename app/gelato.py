import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
    
load_dotenv()
TOKEN = os.getenv("TOKEN","")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)


async def load():
    logger.info("Loading commands")
    for file in os.listdir('./commands'):
        if file.endswith('.py') and "__init__" not in file:
            await bot.load_extension(f'commands.{file[:-3]}')


@bot.event
async def on_ready():
    bot.remove_command('help')
    await load()
    logger.info("Gelato ready")


if __name__ == "__main__":
    bot.run(TOKEN)