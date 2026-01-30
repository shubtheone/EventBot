import discord
from discord.ext import commands
import aiohttp
from bs4 import BeautifulSoup
import config

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="top10", description="List top 10 CTFtime events for the team")
    async def top10(self, ctx):
        await ctx.defer()
        
        team_id = config.CTFTIME_TEAM_ID
        url = f'https://ctftime.org/team/{team_id}'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        await ctx.send(f"Failed to fetch data from CTFtime (Status: {response.status})")
                        return
                    html = await response.text()
            
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find('table', class_='table-striped')

            if not table:
                await ctx.send("Could not find events table on CTFtime page.")
                return

            data = []
            rows = table.find_all('tr')
            
            # Skip header row
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) >= 5: # Ensure enough columns
                    try:
                        place = cols[1].text.strip()
                        event_name = cols[2].text.strip()
                        # event_link = cols[2].find('a')['href'] if cols[2].find('a') else None
                        
                        # Handle potential non-numeric weight/points 
                        # User script: ctf_points = float(cols[3].text.strip()) -> This is usually "CTF points"
                        # User script: rating_points = float(cols[4].text.strip().replace("*", "")) -> This is "Rating points"
                        
                        rating_str = cols[4].text.strip().replace("*", "")
                        if not rating_str:
                            rating_points = 0.0
                        else:
                            rating_points = float(rating_str)

                        data.append({
                            'place': place,
                            'event_name': event_name,
                            'rating_points': rating_points
                        })
                    except ValueError:
                        continue # Skip rows with bad data

            # Sort by rating points descending
            data.sort(key=lambda x: x['rating_points'], reverse=True)
            
            top_10 = data[:10]
            total_rating = sum(item['rating_points'] for item in top_10)

            # Build Embed
            embed = discord.Embed(
                title=f"🏆 Top 10 CTFtime Events (Team ID: {team_id})",
                url=url,
                color=0xFFD700 # Gold
            )

            # Create a monospace table for the description
            table_lines = []
            table_lines.append(f"{'#':<3} | {'Event Name':<25} | {'Rating':<6}")
            table_lines.append("-" * 40)
            
            for i, entry in enumerate(top_10, 1):
                name = entry['event_name'][:25] # Truncate for display
                rating = f"{entry['rating_points']:.2f}"
                place = entry['place']
                # table_lines.append(f"{place:>3} | {name:<25} | {rating:>6}")
                # Actually, let's use the Rank in the top 10 list as standard, but user script shows 'place' (their rank in the CTF).
                # User script output: place | event | rating
                table_lines.append(f"{entry['place']:>3} | {name:<25} | {rating:>6}")

            embed.description = "```\n" + "\n".join(table_lines) + "\n```"
            embed.set_footer(text=f"Total Rating (Top 10): {total_rating:.3f}")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"An error occurred while fetching stats: {str(e)}")

async def setup(bot):
    await bot.add_cog(Stats(bot))
