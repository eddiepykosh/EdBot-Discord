import os
from dotenv import load_dotenv

load_dotenv()
SCRIPT_DIR = os.path.dirname(__file__)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")
API_BASE_URL = os.getenv("API_BASE_URL")
OWM_TOKEN = os.getenv('OWM_TOKEN')
mathID = os.getenv('WRA_MATH_KEY')
WEATHER_PERSON = os.getenv('WEATHER_PERSON')
BULLIED_USER = os.getenv('BULLIED_USER')

AZURE_AI_ENDPOINT = os.getenv('AZURE_AI_ENDPOINT')
AZURE_AI_AGENT_NAME = os.getenv('AZURE_AI_AGENT_NAME')
ALLOWED_CHANNEL_IDS = os.getenv('ALLOWED_CHANNEL_IDS', '')

AI_PROVIDER = os.getenv('AI_PROVIDER', 'azure')  # 'azure' or 'claude'
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-6')

ASSETS_TEXT_PATH = os.path.join(SCRIPT_DIR, 'assets', 'text')
ASSETS_AUDIO_PATH = os.path.join(SCRIPT_DIR, 'assets', 'audio')
DATA_PATH = os.path.join(SCRIPT_DIR, 'data')
