import sys
import os
import discord
from discord.ext import commands
import asyncio

# Add project root to sys.path
sys.path.append(os.getcwd())

async def test_load():
    print("Testing module imports...")
    try:
        from bot.cogs.events import Events
        from bot.utils import create_event_embed
        print("Imports successful.")
    except ImportError as e:
        print(f"Import failed: {e}")
        return

    print("Testing Cog loading...")
    bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
    
    try:
        await bot.add_cog(Events(bot))
        print("Events Cog loaded successfully.")
    except Exception as e:
        print(f"Failed to load Cog: {e}")

if __name__ == "__main__":
    asyncio.run(test_load())
