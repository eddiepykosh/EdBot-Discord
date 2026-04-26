# EdBot-Discord

EdBot 4.0 - the Discord bot that probably should not have made it this far, but absolutely did.

## What It Is

EdBot is a multi-process Discord bot for a private server setup. It is split into three runnable services:

- `edbot_command.py`: command handler for `./` commands, audio playback, TTS, Reddit, WolframAlpha, quotes, and small games.
- `edbot_listener.py`: passive chat listener for keyword responses, swear counting, weather lookups, and the Fortnite store screenshot.
- `edbot_ai.py`: AI chat bot for configured Discord channels using an OpenAI-compatible Responses API backend.

Version 4.0 is focused on local Docker Compose usage, persistent runtime state, safer startup validation, and JSON-based bot state instead of pickle for long-term storage.

## Features

- Command-based Discord interactions with the `./` prefix.
- Voice channel audio playback through FFmpeg and `discord.py[voice]`.
- YouTube audio download/playback through `yt_dlp`.
- AWS Polly TTS command.
- OpenWeatherMap weather responses.
- Reddit and WolframAlpha integrations.
- Keyword-triggered listener responses.
- Swear counting stored as JSON state.
- AI chat with per-channel history files.
- Optional Tavily MCP search support for the AI provider.
- Local Docker Compose deployment with separate command, listener, and AI containers.

## Quick Start

The recommended setup is local Docker Compose.

1. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

2. Fill in `.env` with the tokens and IDs for the services you want to run.

3. Build and start the containers:

   ```bash
   docker compose up -d --build
   ```

4. Watch logs:

   ```bash
   docker compose logs -f
   ```

5. Stop the bot:

   ```bash
   docker compose down
   ```

## Docker Compose Layout

The included `docker-compose.yml` builds the image locally and starts three services:

- `command`
- `listener`
- `edbot-ai`

Runtime folders are mounted from the repo:

- `./data:/app/data`
- `./logs:/app/logs`
- `./history:/app/history` for AI memory

For Docker, set this in `.env` if you want the AI history path to explicitly match the mounted volume:

```env
HISTORY_PATH=/app/history
```

If `HISTORY_PATH` is left blank, the app defaults to a repo-local `history` directory.

## Environment Variables

All services require:

```env
DISCORD_TOKEN=
```

The command bot requires `DISCORD_TOKEN` and will warn if optional command integrations are missing:

```env
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
WRA_MATH_KEY=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=
STREAMING_CHANNEL=
PARROT_CHANNEL=
FORTNITE_PEOPLE=
VALORANT_PEOPLE=
```

The listener requires:

```env
OWM_TOKEN=
WEATHER_PERSON=
BULLIED_USER=
```

The AI bot requires:

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1
ALLOWED_CHANNEL_IDS=
```

Optional AI settings:

```env
OPENAI_BASE_URL=
OPENAI_MAX_OUTPUT_TOKENS=4096
TAVILY_API_KEY=
TAVILY_MCP_SERVER_URL=
TAVILY_MCP_DEFAULT_PARAMETERS=
HISTORY_PATH=/app/history
```

`ALLOWED_CHANNEL_IDS` should be a comma-separated list of numeric Discord channel IDs.

## Runtime State

EdBot writes runtime state to mounted folders so containers can be rebuilt without losing memory or counters.

Important files:

- `data/scores.json`: rock-paper-scissors scores.
- `data/swear_counts.json`: listener swear counts.
- `data/last_tts.mp3`: latest generated TTS audio.
- `data/fortnite.png`: latest Fortnite store screenshot.
- `history/channel_<id>.json`: AI chat history per allowed channel.
- `logs/*.log`: process logs.

Old `scores.pkl` and `swear_counts.pkl` files are migrated to JSON if present.

## Running Without Docker

Docker is preferred, but direct Python execution still works.

1. Install system dependencies:

   ```bash
   sudo apt install libffi-dev libnacl-dev python3-dev ffmpeg
   ```

2. Create a virtual environment and install Python dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   ```

3. Create and fill `.env`:

   ```bash
   cp .env.example .env
   ```

4. Run the process you want:

   ```bash
   python3 edbot_command.py
   python3 edbot_listener.py
   python3 edbot_ai.py
   ```

## Common Commands

- `./play <search or URL>`: download and play YouTube audio.
- `./pause`, `./resume`, `./stop`, `./join`, `./fuckoff`: voice controls.
- `./tts <text>`: generate AWS Polly TTS and play it.
- `./reddit <subreddit>`: post a hot Reddit link.
- `./domath <query>`: ask WolframAlpha.
- `./quote`, `./hypeman`, `./rps`, `./rpsscore`, `./swear_count`: assorted server nonsense.

The AI bot listens only in channels listed in `ALLOWED_CHANNEL_IDS`. Send `!clear` in an allowed channel to clear that channel's AI history.

## Troubleshooting

- Make sure Discord Message Content Intent is enabled for the bot in the Discord Developer Portal.
- If audio fails, confirm FFmpeg is installed in the container or host environment.
- If voice support fails locally, confirm `discord.py[voice]` and native voice dependencies are installed.
- If the listener crashes at startup, check `OWM_TOKEN`, `WEATHER_PERSON`, and `BULLIED_USER`.
- If the AI bot ignores messages, check `ALLOWED_CHANNEL_IDS` and confirm the IDs are numeric.
- If the Fortnite screenshot fails, rebuild the Docker image so Playwright and Chromium are installed.

## Development Notes

- There is no `main.py`; each bot process is started independently.
- GitHub Actions publishing has been removed in favor of local Compose builds.
- `.env`, logs, history, generated media, and JSON runtime state are ignored by Git.
- Suggested future work is tracked in `ai_docs/suggested_improvements.md`.

## History

### EdBot 4.0

- Local Docker Compose is the primary deployment path.
- Added startup configuration validation.
- Added atomic writes for runtime JSON and binary outputs.
- Moved long-term bot state from pickle to JSON.
- Added configurable AI history storage with `HISTORY_PATH`.
- Kept the command, listener, and AI bot processes separate.

### EdBot 3.0

- Added the OpenAI-compatible AI chat process.
- Continued the split command/listener architecture.
- Expanded Docker-based deployment.

### EdBot 2.0

- Introduced separate command and listener scripts.
- Consolidated the original weather and command bot experiments.

### EdBot 1.0

- Began as a weather bot and slowly learned too many tricks.

## Todo

- sentience
