import asyncio
import json
import os
from datetime import datetime, timezone

import discord
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from common.logger import get_logger
from config import AZURE_AI_ENDPOINT, AZURE_AI_AGENT_NAME, ALLOWED_CHANNEL_IDS, DISCORD_TOKEN, SCRIPT_DIR

logger = get_logger("edbot_ai")

HISTORY_DIR = os.path.join(SCRIPT_DIR, "history")
MAX_API_MESSAGES = 60  # 30 pairs

# Parse allowed channel IDs into a set
allowed_channels = set()
for ch_id in ALLOWED_CHANNEL_IDS.split(","):
    ch_id = ch_id.strip()
    if ch_id.isdigit():
        allowed_channels.add(int(ch_id))

# Per-channel locks to prevent concurrent processing
channel_locks: dict[int, asyncio.Lock] = {}

# Azure clients (initialized in on_ready)
openai_client = None
agent = None

# Discord client setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def get_channel_lock(channel_id: int) -> asyncio.Lock:
    if channel_id not in channel_locks:
        channel_locks[channel_id] = asyncio.Lock()
    return channel_locks[channel_id]


def get_history_path(channel_id: int) -> str:
    return os.path.join(HISTORY_DIR, f"channel_{channel_id}.json")


def load_history(channel_id: int) -> list[dict]:
    path = get_history_path(channel_id)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Failed to load history for channel %s: %s", channel_id, e)
        return []


def save_history(channel_id: int, history: list[dict]) -> None:
    os.makedirs(HISTORY_DIR, exist_ok=True)
    path = get_history_path(channel_id)
    try:
        with open(path, "w") as f:
            json.dump(history, f, indent=2)
    except IOError as e:
        logger.error("Failed to save history for channel %s: %s", channel_id, e)


@client.event
async def on_ready():
    global openai_client, agent

    logger.info("Logged in as %s (ID: %s)", client.user, client.user.id)
    logger.info("Allowed channels: %s", allowed_channels)

    try:
        project_client = AIProjectClient(
            endpoint=AZURE_AI_ENDPOINT,
            credential=DefaultAzureCredential(),
        )
        agent = project_client.agents.get(agent_name=AZURE_AI_AGENT_NAME)
        openai_client = project_client.get_openai_client()
        logger.info("Azure AI client initialized (agent: %s)", agent.name)
    except Exception as e:
        logger.error("Failed to initialize Azure AI client: %s", e)


@client.event
async def on_message(message: discord.Message):
    # Ignore bots and own messages
    if message.author.bot or message.author == client.user:
        return

    # Channel filtering
    if message.channel.id not in allowed_channels:
        return

    # Handle !clear command
    if message.content.strip() == "!clear":
        await handle_clear(message)
        return

    # Check if Azure client is ready
    if openai_client is None or agent is None:
        logger.warning("Azure AI client not initialized, ignoring message in channel %s", message.channel.id)
        return

    lock = get_channel_lock(message.channel.id)

    # If channel is locked, react with thumbs down and skip
    if lock.locked():
        logger.info("Channel %s is locked, adding reaction to message from %s", message.channel.id, message.author.display_name)
        try:
            await message.add_reaction("\U0001f44e")
        except discord.HTTPException:
            pass
        return

    async with lock:
        await process_message(message)


async def handle_clear(message: discord.Message):
    channel_id = message.channel.id
    try:
        await asyncio.to_thread(save_history, channel_id, [])
        logger.info("History cleared for channel %s by %s", channel_id, message.author.display_name)
    except Exception as e:
        logger.error("Failed to clear history for channel %s: %s", channel_id, e)

    try:
        await message.channel.send("memory wiped. i have no idea who any of you are.")
    except discord.HTTPException as e:
        logger.error("Failed to send clear confirmation in channel %s: %s", channel_id, e)


async def process_message(message: discord.Message):
    channel_id = message.channel.id
    author_name = message.author.display_name

    logger.info("Processing message in channel %s from %s", channel_id, author_name)

    try:
        # Load history
        history = await asyncio.to_thread(load_history, channel_id)

        # Append user message
        user_entry = {
            "role": "user",
            "content": f"{author_name}: {message.content}",
            "author": author_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        history.append(user_entry)

        # Prepare API payload (last 60 entries, role+content only)
        api_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in history[-MAX_API_MESSAGES:]
        ]

        # Call Azure AI with typing indicator
        async with message.channel.typing():
            response = await asyncio.to_thread(
                openai_client.responses.create,
                input=api_history,
                extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
            )

        reply = response.output_text

        # Send reply in chunks respecting Discord's 2000 char limit
        chunks = []
        remaining = reply
        while len(remaining) > 2000:
            split_at = remaining.rfind(" ", 0, 2000)
            if split_at == -1:
                split_at = 2000
            chunks.append(remaining[:split_at])
            remaining = remaining[split_at:].lstrip(" ")
        chunks.append(remaining)

        for chunk in chunks:
            await message.channel.send(chunk)

        # Append assistant response to history and save
        assistant_entry = {
            "role": "assistant",
            "content": reply,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        history.append(assistant_entry)
        await asyncio.to_thread(save_history, channel_id, history)

        logger.info("Response sent in channel %s", channel_id)

    except Exception as e:
        logger.error("Error processing message in channel %s: %s", channel_id, e)
        try:
            await message.channel.send("something broke on my end, try again")
        except discord.HTTPException:
            pass


if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
