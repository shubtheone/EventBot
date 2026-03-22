import discord
from discord.ext import commands
import cloudscraper
from bs4 import BeautifulSoup
import asyncio
import config


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _fetch_ctftime_html(self, url):
        """Fetch CTFtime page using cloudscraper to bypass Cloudflare."""
        scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "desktop": True,
            }
        )
        response = scraper.get(url)
        response.raise_for_status()
        return response.text

    @commands.hybrid_command(
        name="top10",
        description="List top 10 CTFtime events. Use add: to simulate a pending score.",
    )
    async def top10(self, ctx, add: float = None):
        """Show top 10 rated CTFtime events for the current year.

        Parameters
        ----------
        add : float, optional
            Simulate a pending CTF score. If higher than the current #10,
            it replaces it and recalculates the total.
        """
        await ctx.defer()

        team_id = config.CTFTIME_TEAM_ID
        url = f"https://ctftime.org/team/{team_id}"

        try:
            # Run cloudscraper in a thread to avoid blocking the event loop
            html = await asyncio.to_thread(self._fetch_ctftime_html, url)

            soup = BeautifulSoup(html, "html.parser")

            # Find the current year's rating tab pane (the active one, e.g. id="rating_2026")
            # This skips the "Plan to participate" table which has no rating data.
            rating_pane = soup.find(
                "div",
                class_="tab-pane active",
                id=lambda x: x and x.startswith("rating_"),
            )

            if not rating_pane:
                await ctx.send(
                    "Could not find current year rating table on CTFtime page."
                )
                return

            year = rating_pane.get("id", "").replace("rating_", "")

            table = rating_pane.find("table", class_="table-striped")
            if not table:
                await ctx.send("Could not find events table on CTFtime page.")
                return

            data = []
            rows = table.find_all("tr")
            # Skip header row
            for row in rows[1:]:
                cols = row.find_all("td")
                if len(cols) >= 5:
                    try:
                        place = cols[1].text.strip()
                        event_name = cols[2].text.strip()

                        rating_str = cols[4].text.strip().replace("*", "")
                        if not rating_str:
                            rating_points = 0.0
                        else:
                            rating_points = float(rating_str)

                        data.append(
                            {
                                "place": place,
                                "event_name": event_name,
                                "rating_points": rating_points,
                            }
                        )
                    except ValueError:
                        continue

            if not data:
                await ctx.send("No event participation data found on CTFtime page.")
                return

            # Sort by rating points descending
            data.sort(key=lambda x: x["rating_points"], reverse=True)

            # If user provided an 'add' score, inject it and re-sort
            simulated = False
            if add is not None:
                data.append(
                    {
                        "place": "-",
                        "event_name": "** Pending CTF **",
                        "rating_points": add,
                    }
                )
                data.sort(key=lambda x: x["rating_points"], reverse=True)
                simulated = True

            top_10 = data[:10]
            total_rating = sum(item["rating_points"] for item in top_10)

            # Build Embed
            title = f"🏆 Top 10 CTFtime Events - {year} (Team ID: {team_id})"
            if simulated:
                title += " [Simulated]"

            embed = discord.Embed(
                title=title,
                url=url,
                color=0x00FF00 if simulated else 0xFFD700,
            )

            # Create a monospace table for the description
            table_lines = []
            table_lines.append(f"{'#':<3} | {'Event Name':<25} | {'Rating':<6}")
            table_lines.append("-" * 40)

            for i, entry in enumerate(top_10, 1):
                name = entry["event_name"][:25]
                rating = f"{entry['rating_points']:.2f}"
                marker = (
                    " <"
                    if simulated and entry["event_name"] == "** Pending CTF **"
                    else ""
                )
                table_lines.append(f"{i:<3} | {name:<25} | {rating:>6}{marker}")

            embed.description = "```\n" + "\n".join(table_lines) + "\n```"

            footer = f"Total Rating (Top 10): {total_rating:.3f}"
            if simulated:
                # Calculate difference from original top 10
                original_top10 = [
                    d for d in data if d["event_name"] != "** Pending CTF **"
                ][:10]
                original_total = sum(item["rating_points"] for item in original_top10)
                diff = total_rating - original_total
                if diff > 0:
                    footer += f"  (+{diff:.3f} from pending)"
                else:
                    footer += f"  (pending score too low to affect top 10)"
            embed.set_footer(text=footer)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"An error occurred while fetching stats: {str(e)}")


async def setup(bot):
    await bot.add_cog(Stats(bot))
