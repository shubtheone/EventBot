import requests
import json

def debug_unstop():
    url = "https://unstop.com/api/public/opportunity/search-result?opportunity=hackathons&per_page=5"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        r = requests.get(url, headers=headers)
        print(f"Status Code: {r.status_code}")
        
        try:
            data = r.json()
            print("\nTop level type:", type(data))
            
            if isinstance(data, dict):
                print("Keys:", data.keys())
                if 'data' in data:
                    print("\nData field type:", type(data['data']))
                    if isinstance(data['data'], dict):
                        print("Data keys:", data['data'].keys())
        except Exception as e:
            print("JSON parse failed:", e)
            print("Raw text snippet:", r.text[:200])

    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    debug_unstop()
