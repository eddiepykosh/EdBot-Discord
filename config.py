import os
from dotenv import load_dotenv

load_dotenv()
SCRIPT_DIR = os.path.dirname(__file__)


def _get_int_env(name, default):
    value = os.getenv(name)
    if value in (None, ""):
        return default
    try:
        return int(value)
    except ValueError:
        return default

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
AWS_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")
API_BASE_URL = os.getenv("API_BASE_URL")
OWM_TOKEN = os.getenv('OWM_TOKEN')
mathID = os.getenv('WRA_MATH_KEY')
WEATHER_PERSON = os.getenv('WEATHER_PERSON')
BULLIED_USER = os.getenv('BULLIED_USER')

ALLOWED_CHANNEL_IDS = os.getenv('ALLOWED_CHANNEL_IDS', '')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4.1')
OPENAI_MAX_OUTPUT_TOKENS = _get_int_env('OPENAI_MAX_OUTPUT_TOKENS', 4096)

TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
TAVILY_MCP_SERVER_URL = os.getenv('TAVILY_MCP_SERVER_URL')
TAVILY_MCP_DEFAULT_PARAMETERS = os.getenv('TAVILY_MCP_DEFAULT_PARAMETERS')

ASSETS_TEXT_PATH = os.path.join(SCRIPT_DIR, 'assets', 'text')
ASSETS_AUDIO_PATH = os.path.join(SCRIPT_DIR, 'assets', 'audio')
DATA_PATH = os.path.join(SCRIPT_DIR, 'data')
HISTORY_PATH = os.getenv('HISTORY_PATH', os.path.join(SCRIPT_DIR, 'history'))


def get_missing_env(names):
    return [name for name in names if not os.getenv(name)]


def parse_channel_ids(raw_value):
    channel_ids = set()
    invalid_values = []
    for value in raw_value.split(","):
        value = value.strip()
        if not value:
            continue
        if value.isdigit():
            channel_ids.add(int(value))
        else:
            invalid_values.append(value)
    return channel_ids, invalid_values


def validate_required_env(names, logger, context):
    missing = get_missing_env(names)
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"{context} missing required environment variable(s): {joined}")

    logger.info("%s required environment validated: %s", context, ", ".join(names))


def warn_missing_optional_env(feature_env_map, logger):
    for feature, env_names in feature_env_map.items():
        missing = get_missing_env(env_names)
        if missing:
            logger.warning(
                "%s may be unavailable; missing optional environment variable(s): %s",
                feature,
                ", ".join(missing),
            )


def warn_invalid_int_env(names, logger):
    for name in names:
        value = os.getenv(name)
        if value in (None, ""):
            continue
        try:
            int(value)
        except ValueError:
            logger.warning(
                "%s must be an integer; using the configured default where applicable",
                name,
            )
