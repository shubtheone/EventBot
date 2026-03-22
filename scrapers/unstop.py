import requests
import re
from .base import BaseScraper
from typing import List, Dict

# Strong match: any of these in the TITLE means it's definitely relevant
TITLE_KEYWORDS = [
    "ctf",
    "capture the flag",
    "cybersecurity",
    "cyber security",
    "bug bounty",
    "pentest",
    "cyber clash",
    "cyber conquest",
    "cyber siege",
]

# Weak match: a hint word in the title AND a CTF-specific term in description.
# "hack" alone is excluded because it matches every generic hackathon.
TITLE_HINTS = ["security", "cyber", "infosec", "forensic"]
DETAIL_KEYWORDS = [
    "ctf",
    "capture the flag",
    "penetration testing",
    "jeopardy-style",
    "reverse engineering",
    "binary exploitation",
    "web exploitation",
    "cryptography challenge",
    "forensics challenge",
]


class UnstopScraper(BaseScraper):
    API_URL = "https://unstop.com/api/public/opportunity/search-result"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36",
    }

    def fetch_events(self) -> List[Dict]:
        """
        Fetch open competitions from Unstop and filter for CTF / cybersecurity
        events client-side (Unstop API has no server-side keyword search).
        """
        try:
            all_items = self._fetch_all_pages()
            filtered = self._filter_cybersecurity(all_items)
            return self._normalize(filtered)
        except Exception as e:
            print(f"Unstop scraper error: {e}")
            return []

    def _fetch_all_pages(self, max_pages: int = 20) -> List[Dict]:
        """Paginate through the Unstop competitions API."""
        all_items: List[Dict] = []
        for page in range(1, max_pages + 1):
            params = {
                "opportunity": "competitions",
                "oppstatus": "open",
                "per_page": 50,
                "page": page,
            }
            resp = requests.get(
                self.API_URL, params=params, headers=self.HEADERS, timeout=15
            )
            resp.raise_for_status()
            data = resp.json()

            items = data.get("data", {}).get("data", [])
            if not items:
                break
            all_items.extend(items)

            # Stop if we've reached the last page
            last_page = data.get("data", {}).get("last_page", 1)
            if page >= last_page:
                break

        return all_items

    def _filter_cybersecurity(self, items: List[Dict]) -> List[Dict]:
        """Keep only CTF / cybersecurity-related competitions."""
        matched = []
        for item in items:
            title = (item.get("title") or "").lower()
            details = (item.get("details") or "").lower()
            # Strip HTML tags from details for cleaner matching
            details = re.sub(r"<[^>]+>", " ", details)

            # Strong: keyword appears directly in title
            title_match = any(kw in title for kw in TITLE_KEYWORDS)

            # Weak: CTF-related term in description AND a hint word in title
            detail_match = any(kw in details for kw in DETAIL_KEYWORDS) and any(
                kw in title for kw in TITLE_HINTS
            )

            if title_match or detail_match:
                matched.append(item)

        return matched

    @staticmethod
    def _parse_prizes(prizes_list) -> str:
        """Build a human-readable prize string from the API prizes array."""
        if not prizes_list:
            return "Not specified"

        parts = []
        for p in prizes_list:
            cash = p.get("cash")
            name = p.get("name", "")
            if cash:
                parts.append(
                    f"\u20b9{cash:,.0f}"
                    if isinstance(cash, (int, float))
                    else str(cash)
                )
            elif name:
                parts.append(name)

        return " | ".join(parts) if parts else "Not specified"

    def _normalize(self, events: List[Dict]) -> List[Dict]:
        normalized = []
        for event in events:
            if not isinstance(event, dict):
                continue

            public_url = event.get("public_url") or event.get("seo_url", "")
            url = (
                f"https://unstop.com/{public_url}"
                if public_url
                else "https://unstop.com"
            )

            # Organisation info
            org = event.get("organisation") or {}
            org_name = org.get("name", "Unknown")

            # Registration fee
            is_paid = event.get("isPaid", False)
            fee = "Paid" if is_paid else "Free"

            # Region / location
            region = (event.get("region") or "").lower()
            onsite = region not in ("online", "")

            # Prizes
            prize_str = self._parse_prizes(event.get("prizes"))

            # Registration count
            reg_count = event.get("registerCount", 0)

            # Strip HTML from description
            raw_desc = event.get("details") or "No description."
            clean_desc = re.sub(r"<[^>]+>", "", raw_desc).strip()
            # Collapse whitespace
            clean_desc = re.sub(r"\s+", " ", clean_desc)

            end_date = event.get("end_date")
            start_date = (
                event.get("start_date") or end_date
            )  # Fallback so sorting works

            normalized.append(
                {
                    "source": "Unstop",
                    "title": event.get("title"),
                    "description": clean_desc,
                    "start_date": start_date,
                    "end_date": end_date,
                    "url": url,
                    "ctftime_url": None,
                    "type": "CTF / Cybersecurity",
                    "logo_url": event.get("logoUrl2") or event.get("logo_url"),
                    "organizers": [org_name],
                    "weight": 0,
                    "onsite": onsite,
                    # Unstop-specific fields
                    "prize": prize_str,
                    "fee": fee,
                    "registrations": reg_count,
                }
            )
        return normalized
