import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv
from database import Servers, init_db, Session

logger = logging.getLogger(__name__)
    
load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

async def load():
    logger.info("Loading commands")
    for file in os.listdir('./commands'):
        if file.endswith('.py') and "__init__" not in file:
            await bot.load_extension(f'commands.{file[:-3]}')

    logger.info("Loading database")
    init_db() 
    for guild in bot.guilds:
        if not Session.get(Servers,str(guild.id)):
            Session.add(Servers(server_id=str(guild.id), server_name=guild.name))
    Session.commit()

@bot.event
async def on_ready():
    bot.remove_command('help')
    await load()
    logger.info("Mustard ready")


bot.run(TOKEN)