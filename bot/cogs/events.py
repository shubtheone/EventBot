import discord
from discord.ext import commands, tasks
from scrapers.manager import ScraperManager
from bot.utils import create_event_embed, create_events_summary_embed
import json
import os

SUBSCRIPTIONS_FILE = "data/subscriptions.json"
KNOWN_EVENTS_FILE = "data/known_events.json"

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scraper_manager = ScraperManager()
        self.subscriptions = self._load_json(SUBSCRIPTIONS_FILE, {})
        self.known_events = set(self._load_json(KNOWN_EVENTS_FILE, []))
        
        # Start the background task
        self.check_new_events.start()

    def cog_unload(self):
        self.check_new_events.cancel()

    def _load_json(self, filename, default):
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except:
                return default
        return default

    def _save_json(self, filename, data):
        # Create directory if it doesn't exist (just in case)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(data, f)

    @commands.hybrid_command(name="events", description="List upcoming CTFs")
    async def events(self, ctx, limit: int = 0):
        await ctx.defer()
        self._send_events(ctx, limit, type_filter='CTF')

    @commands.hybrid_command(name="hackathons", description="List upcoming Hackathons (Unstop, etc.)")
    async def hackathons(self, ctx, limit: int = 0):
        await ctx.defer()
        self._send_events(ctx, limit, type_filter='Hackathon')

    async def _send_events(self, ctx, limit, type_filter):
        try:
            events = self.scraper_manager.get_all_events(type_filter=type_filter)
            
            if not events:
                await ctx.send(f"No upcoming {type_filter} events found.")
                return

            if limit > 0:
                subset = events[:limit]
                for event in subset:
                    embed = create_event_embed(event)
                    await ctx.send(embed=embed)
            else:
                embed = create_events_summary_embed(events)
                await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.hybrid_command(name="watch", description="Set this channel to receive new CTF notifications")
    @commands.has_permissions(administrator=True)
    async def watch(self, ctx):
        """
        Sets the current channel as the notification channel for this server.
        """
        guild_id = str(ctx.guild.id)
        channel_id = ctx.channel.id
        
        self.subscriptions[guild_id] = channel_id
        self._save_json(SUBSCRIPTIONS_FILE, self.subscriptions)
        
        await ctx.send(f"✅ checks enabled! I will post new events to {ctx.channel.mention}.")

    @tasks.loop(minutes=60)
    async def check_new_events(self):
        # Avoid running immediately on startup before bot is ready
        if not self.bot.is_ready():
            return

        print("Checking for new events...")
        try:
            current_events = self.scraper_manager.get_all_events()
            new_events = []
            
            for event in current_events:
                # Use URL as a unique identifier
                event_id = event.get('url')
                if not event_id:
                    continue
                
                if event_id not in self.known_events:
                    new_events.append(event)
                    self.known_events.add(event_id)
            
            if new_events:
                print(f"Found {len(new_events)} new events!")
                # Save updated known events
                self._save_json(KNOWN_EVENTS_FILE, list(self.known_events))
                
                # Notify all subscribed channels
                for guild_id, channel_id in self.subscriptions.items():
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        for event in new_events:
                            embed = create_event_embed(event)
                            await channel.send("🚨 **New Event Detected!**", embed=embed)
                    else:
                        print(f"Could not find channel {channel_id} for guild {guild_id}")
            else:
                print("No new events found.")
                
        except Exception as e:
            print(f"Error in background task: {e}")

    @check_new_events.before_loop
    async def before_check_new_events(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Events(bot))
