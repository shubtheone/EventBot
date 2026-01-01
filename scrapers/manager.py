from typing import List, Dict
from .ctftime import CTFTimeScraper
from .unstop import UnstopScraper

class ScraperManager:
    def __init__(self):
        self.scrapers = [
            CTFTimeScraper(),
            UnstopScraper()
        ]

    def get_all_events(self, type_filter: str = None) -> List[Dict]:
        all_events = []
        for scraper in self.scrapers:
            # We could optimize by only calling relevant scrapers
            # but for now fetching all is fine (<50 reqs)
            try:
                events = scraper.fetch_events()
                all_events.extend(events)
            except Exception as e:
                print(f"Scraper failed: {e}")
        
        # Filter if needed
        if type_filter:
            if type_filter == 'CTF':
                all_events = [e for e in all_events if e.get('source') == 'CTFtime']
            elif type_filter == 'Hackathon':
                all_events = [e for e in all_events if e.get('type') == 'Hackathon']
        
        # Sort by start date (handling None dates)
        all_events.sort(key=lambda x: x.get('start_date') or '9999-99-99')
        return all_events
