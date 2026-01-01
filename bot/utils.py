import discord
from typing import Dict, List, Optional
from datetime import datetime

def format_date(iso_date: str) -> str:
    try:
        # Simple ISO parsing (assumes "2026-01-09T00:00:00+00:00" format)
        # We can use strptime or fromisoformat in Python 3.7+
        dt = datetime.fromisoformat(iso_date)
        return dt.strftime("%a, %d %b. %Y, %H:%M UTC")
    except Exception:
        return iso_date

def create_event_embed(event: Dict) -> discord.Embed:
    """
    Creates a detailed Discord Embed for a single event matching user request.
    """
    title = event.get('title', 'Unknown Event')
    url = event.get('url', '')
    description = event.get('description', 'No description.')
    
    # Truncate description for embed limits if necessary, better to keep it reasonable
    if len(description) > 300:
        description = description[:297] + "..."

    start_str = format_date(event.get('start_date', ''))
    end_str = format_date(event.get('end_date', ''))
    date_range = f"{start_str} — {end_str}"
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=0x2ecc71 # Emerald Green
    )
    
    # Date Range
    embed.add_field(name="Date", value=date_range, inline=False)
    
    # Type / Location
    onsite = event.get('onsite', False)
    location = "On-line" if not onsite else "On-site"
    embed.add_field(name="Location", value=location, inline=True)
    
    # Format
    fmt = event.get('type', 'Jeopardy')
    embed.add_field(name="Format", value=fmt, inline=True)
    
    # Links
    website = event.get('url', 'N/A')
    ctftime_link = event.get('ctftime_url', 'N/A')
    embed.add_field(name="Official URL", value=website, inline=False)
    embed.add_field(name="CTFtime URL", value=ctftime_link, inline=False)
    
    # Weight
    weight = event.get('weight', 0)
    embed.add_field(name="Rating Weight", value=str(weight), inline=True)
    
    # Organizers
    if event.get('organizers'):
        orgs = "\n".join(event['organizers'])
        embed.add_field(name="Event Organizers", value=orgs, inline=False)
        
    embed.set_footer(text=f"Source: {event.get('source', 'Unknown')}")
    
    if event.get('logo_url'):
        embed.set_thumbnail(url=event['logo_url'])
        
    return embed

def create_events_summary_embed(events: List[Dict]) -> discord.Embed:
    """
    Creates a summary list embed.
    """
    embed = discord.Embed(
        title=f"Upcoming CTF & Hackathons ({len(events)})",
        description="Here are the upcoming events:",
        color=0x3498db # Blue
    )
    
    for event in events[:10]: # Limit to 10 to avoid hitting limits
        start_display = event.get('start_date', '').split('T')[0]
        embed.add_field(
            name=f"{event['title']} ({start_display})",
            value=f"[Link]({event['url']}) - {event.get('type', 'Event')}",
            inline=False
        )
        
    if len(events) > 10:
        embed.set_footer(text=f"And {len(events) - 10} more events...")
        
    return embed
