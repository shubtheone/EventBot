import sys
import os

# Add parent directory to sys.path to allow importing config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import discord
from discord.ext import commands
import config
import asyncio

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
        # Load cogs
        for filename in os.listdir('./bot/cogs'):
            if filename.endswith('.py'):
                await self.load_extension(f'bot.cogs.{filename[:-3]}')
        
        # Sync slash commands
        await self.tree.sync()

bot = MyBot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

async def main():
    async with bot:
        await bot.start(config.TOKEN)

if __name__ == "__main__":
    if config.TOKEN:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            # Handle Ctrl+C
            pass
    else:
        print("Error: DISCORD_TOKEN not found in environment variables.")
