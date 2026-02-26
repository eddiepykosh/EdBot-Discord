import asyncio
import json
import os
import time
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
        logger.debug("No history file for channel %s, starting fresh", channel_id)
        return []
    try:
        with open(path, "r") as f:
            history = json.load(f)
        logger.debug("Loaded %d history entries for channel %s", len(history), channel_id)
        return history
    except (json.JSONDecodeError, IOError) as e:
        logger.error("Failed to load history for channel %s: %s", channel_id, e, exc_info=True)
        return []


def save_history(channel_id: int, history: list[dict]) -> None:
    os.makedirs(HISTORY_DIR, exist_ok=True)
    path = get_history_path(channel_id)
    try:
        with open(path, "w") as f:
            json.dump(history, f, indent=2)
        logger.debug("Saved %d history entries for channel %s", len(history), channel_id)
    except IOError as e:
        logger.error("Failed to save history for channel %s: %s", channel_id, e, exc_info=True)


@client.event
async def on_ready():
    global openai_client, agent

    logger.info("Logged in as %s (ID: %s)", client.user, client.user.id)
    logger.info("Allowed channels: %s", allowed_channels)
    logger.info("discord.py version: %s", discord.__version__)

    try:
        logger.info("Initializing Azure AI client (endpoint: %s, agent: %s)", AZURE_AI_ENDPOINT, AZURE_AI_AGENT_NAME)
        project_client = AIProjectClient(
            endpoint=AZURE_AI_ENDPOINT,
            credential=DefaultAzureCredential(),
        )
        agent = project_client.agents.get(agent_name=AZURE_AI_AGENT_NAME)
        openai_client = project_client.get_openai_client()
        logger.info("Azure AI client initialized (agent: %s, id: %s)", agent.name, agent.id)
    except Exception as e:
        logger.error("Failed to initialize Azure AI client: %s", e, exc_info=True)


@client.event
async def on_disconnect():
    logger.warning("Disconnected from Discord")


@client.event
async def on_resumed():
    logger.info("Reconnected and session resumed")


@client.event
async def on_error(event: str, *args, **kwargs):
    logger.error("Unhandled exception in event '%s'", event, exc_info=True)


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
        logger.info("Channel %s is locked, dropping message from %s (msg_id: %s)", message.channel.id, message.author.display_name, message.id)
        try:
            await message.add_reaction("\U0001f44e")
        except discord.HTTPException as e:
            logger.warning("Failed to add reaction to msg %s: %s", message.id, e)
        return

    async with lock:
        await process_message(message)


async def handle_clear(message: discord.Message):
    channel_id = message.channel.id
    try:
        await asyncio.to_thread(save_history, channel_id, [])
        logger.info("History cleared for channel %s by %s (user_id: %s)", channel_id, message.author.display_name, message.author.id)
    except Exception as e:
        logger.error("Failed to clear history for channel %s: %s", channel_id, e, exc_info=True)

    try:
        await message.channel.send("memory wiped. i have no idea who any of you are.")
    except discord.HTTPException as e:
        logger.error("Failed to send clear confirmation in channel %s: %s", channel_id, e, exc_info=True)


async def process_message(message: discord.Message):
    channel_id = message.channel.id
    author_name = message.author.display_name

    # Filter image attachments
    image_attachments = [
        a for a in message.attachments
        if a.content_type and a.content_type.startswith("image/")
    ]

    # Skip if nothing to process
    if not message.content.strip() and not image_attachments:
        logger.debug("Skipping message %s in channel %s (no text or images)", message.id, channel_id)
        return

    logger.info(
        "Processing message %s in channel %s from %s (text_len: %d, images: %d)",
        message.id, channel_id, author_name, len(message.content), len(image_attachments),
    )
    if image_attachments:
        for a in image_attachments:
            logger.debug("Image attachment: %s (type: %s, size: %d bytes)", a.filename, a.content_type, a.size)

    try:
        # Load history
        history = await asyncio.to_thread(load_history, channel_id)
        logger.debug("History for channel %s: %d entries, sending %d to API", channel_id, len(history), min(len(history) + 1, MAX_API_MESSAGES))

        # Build history text - image filenames stored as labels since CDN URLs expire
        history_text = f"{author_name}: {message.content}"
        if image_attachments:
            labels = " ".join(f"[image: {a.filename}]" for a in image_attachments)
            history_text = f"{history_text} {labels}".strip()

        # Append user message
        user_entry = {
            "role": "user",
            "content": history_text,
            "author": author_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        history.append(user_entry)

        # Prepare API payload (last 60 entries, role+content only)
        # Current message is multimodal if images are present
        api_messages = history[-MAX_API_MESSAGES:]
        api_history = []
        for i, msg in enumerate(api_messages):
            if i == len(api_messages) - 1 and image_attachments:
                content_parts = [{"type": "input_text", "text": msg["content"]}]
                for a in image_attachments:
                    content_parts.append({"type": "input_image", "image_url": a.url})
                api_history.append({"role": "user", "content": content_parts})
            else:
                api_history.append({"role": msg["role"], "content": msg["content"]})

        # Call Azure AI with typing indicator
        logger.debug("Sending request to Azure AI (agent: %s, payload_messages: %d)", agent.name, len(api_history))
        t_start = time.monotonic()
        async with message.channel.typing():
            response = await asyncio.to_thread(
                openai_client.responses.create,
                input=api_history,
                extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
            )
        elapsed = time.monotonic() - t_start
        logger.info("Azure AI responded in %.2fs (response_id: %s)", elapsed, getattr(response, "id", "n/a"))

        reply = response.output_text
        if not reply:
            logger.warning("Azure AI returned empty response for message %s in channel %s", message.id, channel_id)

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

        logger.debug("Sending reply in %d chunk(s) (total chars: %d)", len(chunks), len(reply))
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

        logger.info("Response sent for message %s in channel %s", message.id, channel_id)

    except Exception as e:
        logger.error("Error processing message %s in channel %s: %s", message.id, channel_id, e, exc_info=True)
        try:
            await message.channel.send(f"something broke on my end, try again\n```{type(e).__name__}: {e}```")
        except discord.HTTPException as send_err:
            logger.error("Failed to send error message to channel %s: %s", channel_id, send_err, exc_info=True)


if __name__ == "__main__":
    logger.info("Starting edbot_ai")
    try:
        client.run(DISCORD_TOKEN)
    except Exception as e:
        logger.critical("client.run() exited with an exception: %s", e, exc_info=True)
    finally:
        logger.info("edbot_ai shutting down")
