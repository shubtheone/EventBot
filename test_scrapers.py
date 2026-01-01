from scrapers.manager import ScraperManager
import json

def main():
    manager = ScraperManager()
    print("Fetching events...")
    events = manager.get_all_events()
    print(f"Found {len(events)} events.")
    
    if events:
        print("\nTop 3 Upcoming Events:")
        for event in events[:3]:
            print(f"- {event['title']} ({event['start_date']})")
        
        # Save to a debug file
        with open('debug_events.json', 'w') as f:
            json.dump(events, f, indent=2)
            print("\nSaved all events to debug_events.json")
    else:
        print("No events found. Check network or API.")

if __name__ == "__main__":
    main()
