import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents)

async def load():
    for file in os.listdir('./commands'):
        if file.endswith('.py'):
            await bot.load_extension(f'commands.{file[:-3]}') 

@bot.event
async def on_ready():
    bot.remove_command('help')
    await load()
    print("Mustard ready")


bot.run(TOKEN)

