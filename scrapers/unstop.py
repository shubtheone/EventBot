import requests
from .base import BaseScraper
from typing import List, Dict

class UnstopScraper(BaseScraper):
    def fetch_events(self) -> List[Dict]:
        """
        Fetch upcoming Hackathons from Unstop API.
        """
        api_url = "https://unstop.com/api/public/opportunity/search-result?opportunity=hackathons&per_page=20"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            print(f"DEBUG: Unstop response type: {type(data)}")
            # If it's a list, print first item keys to understand structure
            if isinstance(data, list) and len(data) > 0:
                 print(f"DEBUG: First item in list: {str(data[0])[:100]}")

            opportunities = []
            
            # Case 1: Standard Dict Response { data: { data: [] } }
            if isinstance(data, dict) and 'data' in data:
                inner = data['data']
                if isinstance(inner, dict) and 'data' in inner:
                    opportunities = inner['data']
                elif isinstance(inner, list):
                     opportunities = inner
            
            # Case 2: Direct List Response (possible protection/variation) [ ... ]
            elif isinstance(data, list):
                opportunities = data

            return self._normalize(opportunities)
        except Exception as e:
            print(f"Error fetching Unstop events: {e}")
            return []

    def _normalize(self, events: List[Dict]) -> List[Dict]:
        normalized = []
        for event in events:
            # Unstop API fields (guessing based on common fields, refined by test)
            # title, start_date, end_date, seo_url -> url
            
            slug = event.get('seo_url', '')
            url = f"https://unstop.com/{slug}" if slug else "https://unstop.com"
            
            # Dates in Unstop might be ISO or specific format. 
            # Often they have 'start_date' and 'end_date' fields.
            
            normalized.append({
                'source': 'Unstop',
                'title': event.get('title'),
                'description': event.get('filters', {}).get('about', 'No description.'), # specific to unstop structure? or just generic
                'start_date': event.get('start_date'),
                'end_date': event.get('end_date'),
                'url': url,
                'ctftime_url': None,
                'type': 'Hackathon', # Explicitly set as Hackathon
                'logo_url': event.get('logo_url'), # or 'logo'
                'organizers': [event.get('organisation', {}).get('name', 'Unknown')],
                'weight': 0,
                'onsite': event.get('region') != 'Online', # simplistic check
            })
        return normalized
