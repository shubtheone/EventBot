import requests
from bs4 import BeautifulSoup
import json

def test_devpost():
    print("Testing Devpost...")
    url = "https://devpost.com/hackathons"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            tiles = soup.find_all('div', class_='hackathon-tile')
            print(f"Devpost: Found {len(tiles)} hackathons.")
            if len(tiles) > 0:
                print("Sample Devpost Title:", tiles[0].find('h3').text.strip())
        else:
            print(f"Devpost failed: {r.status_code}")
    except Exception as e:
        print(f"Devpost error: {e}")

def test_unstop():
    print("\nTesting Unstop...")
    # Trying their public API endpoint often used by frontend
    url = "https://unstop.com/api/public/opportunity/search-result?opportunity=hackathons&per_page=10"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            # print(str(data)[:200]) # Debug
            opportunities = data.get('data', {}).get('data', [])
            print(f"Unstop: Found {len(opportunities)} hackathons.")
            if opportunities:
                print("Sample Unstop Title:", opportunities[0].get('title'))
        else:
            print(f"Unstop failed: {r.status_code}")
    except Exception as e:
        print(f"Unstop error: {e}")

if __name__ == "__main__":
    test_devpost()
    test_unstop()
