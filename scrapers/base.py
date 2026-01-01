from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScraper(ABC):
    @abstractmethod
    def fetch_events(self) -> List[Dict]:
        """
        Fetches events and returns a list of dictionaries.
        Each dictionary should have at least:
        - title
        - description
        - start_date (ISO format)
        - end_date (ISO format)
        - url
        - type (Jeopardy, Attack-Defense, Hackathon, etc.)
        - prize (optional)
        - organizers (optional)
        - logo_url (optional)
        """
        pass
