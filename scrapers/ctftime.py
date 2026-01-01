import requests
from datetime import datetime
import time
from .base import BaseScraper
from typing import List, Dict

class CTFTimeScraper(BaseScraper):
    def __init__(self):
        self.api_url = "https://ctftime.org/api/v1/events/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_events(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """
        Fetch upcoming CTF events from CTFtime.
        """
        start_timestamp = int(time.time())
        end_timestamp = start_timestamp + (days * 24 * 60 * 60)
        
        params = {
            'limit': limit,
            'start': start_timestamp,
            'finish': end_timestamp,
        }

        try:
            response = requests.get(self.api_url, params=params, headers=self.headers)
            response.raise_for_status()
            events = response.json()
            return self._normalize(events)
        except Exception as e:
            print(f"Error fetching CTFtime events: {e}")
            return []

    def _normalize(self, events: List[Dict]) -> List[Dict]:
        normalized_events = []
        for event in events:
            # Check if public
            if event.get('public_votable') or event.get('onsite') == False:
                 pass # Most listed are public enough or we filter later
            
            # Extract prize info if available (CTFtime api doesn't give prize pool directly in list, 
            # might need to parse description or just leave generic)
            
            normalized_events.append({
                'source': 'CTFtime',
                'title': event.get('title'),
                'description': event.get('description', 'No description provided.'),
                'start_date': event.get('start'),
                'end_date': event.get('finish'),
                'url': event.get('url'),
                'ctftime_url': event.get('ctftime_url'),
                'type': event.get('format'),
                'logo_url': event.get('logo'),
                'organizers': [org['name'] for org in event.get('organizers', [])],
                'weight': event.get('weight'),
                'is_open': True # details can vary
            })
        return normalized_events
