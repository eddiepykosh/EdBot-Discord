import asyncio
import os
import sys
import time
from datetime import datetime, timezone

import discord

from common.logger import get_logger
from config import (
    ALLOWED_CHANNEL_IDS,
    DISCORD_TOKEN,
    HISTORY_PATH,
    parse_channel_ids,
    validate_required_env,
    warn_invalid_int_env,
)
from utils import load_json_file, save_json_atomic
from providers import get_provider

logger = get_logger("edbot_ai")

HISTORY_DIR = HISTORY_PATH
MAX_API_MESSAGES = 60  # 30 pairs

allowed_channels, invalid_channel_ids = parse_channel_ids(ALLOWED_CHANNEL_IDS)

# Per-channel locks to prevent concurrent processing
channel_locks: dict[int, asyncio.Lock] = {}

# AI provider (initialized in on_ready)
provider = None

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
        history = load_json_file(path, [])
        logger.debug("Loaded %d history entries for channel %s", len(history), channel_id)
        return history
    except IOError as e:
        logger.error("Failed to load history for channel %s: %s", channel_id, e, exc_info=True)
        return []


def save_history(channel_id: int, history: list[dict]) -> None:
    os.makedirs(HISTORY_DIR, exist_ok=True)
    path = get_history_path(channel_id)
    try:
        save_json_atomic(path, history)
        logger.debug("Saved %d history entries for channel %s", len(history), channel_id)
    except IOError as e:
        logger.error("Failed to save history for channel %s: %s", channel_id, e, exc_info=True)


@client.event
async def on_ready():
    global provider

    logger.info("Logged in as %s (ID: %s)", client.user, client.user.id)
    logger.info("Allowed channels: %s", allowed_channels)
    logger.info("discord.py version: %s", discord.__version__)

    try:
        logger.info("Initializing AI provider: openai-compatible")
        provider = get_provider()
        provider.initialize()
        logger.info("AI provider initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize AI provider: %s", e, exc_info=True)


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

    # Check if AI provider is ready
    if provider is None or not provider.is_ready():
        logger.warning("AI provider not initialized, ignoring message in channel %s", message.channel.id)
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

        # Prepare API messages (last 60 entries, role+content only)
        api_messages = [{"role": msg["role"], "content": msg["content"]} for msg in history[-MAX_API_MESSAGES:]]

        # Call AI provider with typing indicator
        logger.debug("Sending request to AI provider (messages: %d)", len(api_messages))
        t_start = time.monotonic()
        async with message.channel.typing():
            reply, history_content = await asyncio.to_thread(
                provider.create_response, api_messages, image_attachments,
            )
        elapsed = time.monotonic() - t_start
        logger.info("AI provider responded in %.2fs", elapsed)

        if not reply:
            logger.warning("AI provider returned empty response for message %s in channel %s", message.id, channel_id)
            return

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
            "content": history_content,
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
        validate_required_env(
            ["DISCORD_TOKEN", "OPENAI_API_KEY", "OPENAI_MODEL", "ALLOWED_CHANNEL_IDS"],
            logger,
            "edbot_ai",
        )
        if invalid_channel_ids:
            raise RuntimeError(
                "edbot_ai ALLOWED_CHANNEL_IDS contains invalid value(s): "
                + ", ".join(invalid_channel_ids)
            )
        if not allowed_channels:
            raise RuntimeError("edbot_ai ALLOWED_CHANNEL_IDS must include at least one numeric channel ID")
        warn_invalid_int_env(["OPENAI_MAX_OUTPUT_TOKENS"], logger)
        client.run(DISCORD_TOKEN)
    except Exception as e:
        logger.critical("edbot_ai startup failed: %s", e, exc_info=True)
        sys.exit(1)
    finally:
        logger.info("edbot_ai shutting down")
