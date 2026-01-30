import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
CTFTIME_TEAM_ID = os.getenv('CTFTIME_TEAM_ID', '370140')
