import discord
from discord.ext import commands, tasks
from scrapers.manager import ScraperManager
from bot.utils import create_event_embed, create_events_summary_embed
import json
import os
from datetime import datetime, timezone
import dateutil.parser

SUBSCRIPTIONS_FILE = "data/subscriptions.json"
KNOWN_EVENTS_FILE = "data/known_events.json"
ACTIVE_EVENTS_FILE = "data/active_events.json"

class EventView(discord.ui.View):
    def __init__(self, bot, event_data, event_cog):
        super().__init__(timeout=None)
        self.bot = bot
        self.event_data = event_data
        self.event_cog = event_cog

    @discord.ui.button(label="Create Channel", style=discord.ButtonStyle.green, emoji="➕")
    async def create_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        guild_id = str(interaction.guild_id)
        event_url = self.event_data.get('url')
        
        if self.event_cog.get_channel_id(guild_id, event_url):
            await interaction.followup.send("A channel for this event already exists!", ephemeral=True)
            return

        # Sanitize channel name
        title = self.event_data.get('title', 'event')
        sanitized_title = "".join(c if c.isalnum() else "-" for c in title).lower()
        channel_name = f"ctf-{sanitized_title}"[:30].strip("-")
        
        # Create Channel
        try:
            category = interaction.channel.category
            channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                topic=f"Discussion for {title} - {event_url}"
            )
            
            # Post Event Info
            embed = create_event_embed(self.event_data)
            await channel.send(f"Welcome to the war room for **{title}**! @here", embed=embed)
            
            # Register active event
            self.event_cog.add_active_event(guild_id, event_url, channel.id, self.event_data)
            
            await interaction.followup.send(f"✅ Created channel {channel.mention}!", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"Failed to create channel: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Delete Channel", style=discord.ButtonStyle.red, emoji="➖")
    async def delete_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        guild_id = str(interaction.guild_id)
        event_url = self.event_data.get('url') # URL acts as ID
        
        channel_id = self.event_cog.get_channel_id(guild_id, event_url)
        
        if not channel_id:
            await interaction.followup.send("No tracked channel found for this event.", ephemeral=True)
            return
            
        channel = interaction.guild.get_channel(channel_id)
        
        if channel:
            try:
                await channel.delete(reason="User requested event channel deletion")
                self.event_cog.remove_active_event(guild_id, event_url)
                await interaction.followup.send("Channel deleted.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"Failed to delete channel: {e}", ephemeral=True)
        else:
            # Channel already gone, just clean up DB
            self.event_cog.remove_active_event(guild_id, event_url)
            await interaction.followup.send("Channel record cleaned up (channel was missing).", ephemeral=True)

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scraper_manager = ScraperManager()
        self.subscriptions = self._load_json(SUBSCRIPTIONS_FILE, {})
        self.known_events = set(self._load_json(KNOWN_EVENTS_FILE, []))
        self.active_events = self._load_json(ACTIVE_EVENTS_FILE, {}) # Structure: {guild_id: {event_url: {data}}}
        
        # Start background tasks
        self.check_new_events.start()
        self.check_event_starts.start()

    def cog_unload(self):
        self.check_new_events.cancel()
        self.check_event_starts.cancel()

    def _load_json(self, filename, default):
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except:
                return default
        return default

    def _save_json(self, filename, data):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(data, f, default=str)

    # --- Active Event Management ---
    def get_channel_id(self, guild_id, event_url):
        return self.active_events.get(str(guild_id), {}).get(event_url, {}).get('channel_id')

    def add_active_event(self, guild_id, event_url, channel_id, event_data):
        guild_id = str(guild_id)
        if guild_id not in self.active_events:
            self.active_events[guild_id] = {}
        
        self.active_events[guild_id][event_url] = {
            "channel_id": channel_id,
            "title": event_data.get('title'),
            "start_date": event_data.get('start_date'),
            "notified_start": False
        }
        self._save_json(ACTIVE_EVENTS_FILE, self.active_events)

    def remove_active_event(self, guild_id, event_url):
        guild_id = str(guild_id)
        if guild_id in self.active_events and event_url in self.active_events[guild_id]:
            del self.active_events[guild_id][event_url]
            self._save_json(ACTIVE_EVENTS_FILE, self.active_events)

    # --- Commands ---

    @commands.hybrid_command(name="events", description="List upcoming CTFs")
    async def events(self, ctx, limit: int = 5):
        await ctx.defer()
        await self._send_events(ctx, limit, type_filter='CTF')

    @commands.hybrid_command(name="hackathons", description="List upcoming Hackathons")
    async def hackathons(self, ctx, limit: int = 5):
        await ctx.defer()
        await self._send_events(ctx, limit, type_filter='Hackathon')

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
                    view = EventView(self.bot, event, self)
                    await ctx.send(embed=embed, view=view)
            else:
                embed = create_events_summary_embed(events)
                await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.hybrid_command(name="watch", description="Set this channel to receive new CTF notifications")
    @commands.has_permissions(administrator=True)
    async def watch(self, ctx):
        guild_id = str(ctx.guild.id)
        channel_id = ctx.channel.id
        
        self.subscriptions[guild_id] = channel_id
        self._save_json(SUBSCRIPTIONS_FILE, self.subscriptions)
        
        await ctx.send(f"✅ checks enabled! I will post new events to {ctx.channel.mention}.")

    # --- Tasks ---

    @tasks.loop(minutes=1)
    async def check_event_starts(self):
        if not self.bot.is_ready(): return
        
        now = datetime.now(timezone.utc)
        
        # Iterate over all guilds and events
        # Note: Iterate over copy to allow modification
        changes = False
        
        for guild_id, events_map in self.active_events.items():
            for event_url, info in events_map.items():
                if info.get('notified_start'):
                    continue
                
                try:
                    start_str = info.get('start_date')
                    if not start_str: continue
                    
                    # Parse start time
                    start_dt = dateutil.parser.isoparse(start_str)
                    
                    # If offset naive, assume UTC (though API usually returns iso with offset)
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=timezone.utc)
                        
                    if now >= start_dt:
                        # EVENT STARTED
                        channel_id = info.get('channel_id')
                        channel = self.bot.get_channel(channel_id)
                        
                        if channel:
                            await channel.send(f"@everyone 🚨 **CTF STARTED!** 🚨\nThe event **{info.get('title')}** has begun! Go go go!")
                        
                        info['notified_start'] = True
                        changes = True
                        
                except Exception as e:
                    print(f"Error checking start for {event_url}: {e}")
        
        if changes:
            self._save_json(ACTIVE_EVENTS_FILE, self.active_events)

    @tasks.loop(minutes=60)
    async def check_new_events(self):
        if not self.bot.is_ready(): return

        print("Checking for new events...")
        try:
            current_events = self.scraper_manager.get_all_events()
            new_events = []
            
            for event in current_events:
                # Use URL as a unique identifier
                event_id = event.get('url')
                if not event_id: continue
                
                if event_id not in self.known_events:
                    new_events.append(event)
                    self.known_events.add(event_id)
            
            if new_events:
                print(f"Found {len(new_events)} new events!")
                self._save_json(KNOWN_EVENTS_FILE, list(self.known_events))
                
                for guild_id, channel_id in self.subscriptions.items():
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        for event in new_events:
                            embed = create_event_embed(event)
                            view = EventView(self.bot, event, self)
                            await channel.send("🚨 **New Event Detected!**", embed=embed, view=view)
            else:
                print("No new events found.")
                
        except Exception as e:
            print(f"Error in background task: {e}")

    @check_new_events.before_loop
    async def before_check_new_events(self):
        await self.bot.wait_until_ready()
        
    @check_event_starts.before_loop
    async def before_check_event_starts(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Events(bot))
