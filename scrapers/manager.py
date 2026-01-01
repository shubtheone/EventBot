from typing import List, Dict
from .ctftime import CTFTimeScraper

class ScraperManager:
    def __init__(self):
        self.scrapers = [
            CTFTimeScraper()
        ]

    def get_all_events(self) -> List[Dict]:
        all_events = []
        for scraper in self.scrapers:
            events = scraper.fetch_events()
            all_events.extend(events)
        
        # Sort by start date
        all_events.sort(key=lambda x: x.get('start_date', ''))
        return all_events
