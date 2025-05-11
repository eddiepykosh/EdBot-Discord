# EdBot-Discord

EdBot 3.0 - oh. dear. god.

---

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
  - [Using Docker](#using-docker)
  - [Without Docker](#without-docker)
- [Usage](#usage)
- [Disclaimer](#disclaimer)
- [Development History](#development-history)
  - [EdBot 2.0](#edbot-20)
  - [EdBot 1.0](#edbot-10)
- [Things to Know](#things-to-know)
- [Todo](#todo)

---

## Introduction

EdBot is a versatile Discord bot designed to "enhance" your server experience. Originally created as a weather bot, EdBot has evolved into a multi-functional tool with features ranging from audio playback to keyword-based actions.

---

## Features

- **Command-based interactions**: Execute commands with `./` to trigger various actions.
- **Keyword listener**: Responds to specific keywords with predefined actions.
- **Audio playback**: Plays MP3 files directly in your Discord server.
- **Weather updates**: Provides current weather information for a given city.
- ~~**Text-to-Speech (TTS)**: Converts text into speech using AWS Polly.~~

---

## Installation

### Using Docker

1. Create a new directory on your host machine.
2. Download the `docker-compose-from-dockerhub.yml` file from the `usage` folder and rename it to `docker-compose.yml`.
3. Download the sample `.env` file and place it in the same directory.
4. Update the `.env` file with the required information.
5. Make any necessary adjustments to the `docker-compose.yml` file.
6. Start the application:

   ```bash
   docker compose up -d
   ```

### Without Docker

1. Clone this repository:

   ```bash
   git clone https://github.com/your-username/EdBot-Discord.git
   cd EdBot-Discord
   ```

2. Set up a Python virtual environment and install dependencies:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Install additional system dependencies (if required):

   ```bash
   sudo apt install libffi-dev libnacl-dev python3-dev ffmpeg
   ```

4. Run the scripts:

   - Start the command handler:

     ```bash
     python edbot_command.py
     ```

   - Start the listener:

     ```bash
     python edbot_listener.py
     ```

5. (Optional) Automate the bot using the provided `.service` files for systemd.

---

## Usage

- **Commands**: Use `./` followed by a command to interact with EdBot.
- **Listener**: EdBot will automatically respond to specific keywords in chat.
- **Audio Features**: Ensure FFMPEG is installed and configured for audio playback.

---

## Disclaimer

EdBot 3.0 is a significant improvement over its predecessors, but some quirks may remain. Use the code responsibly and adapt it to your needs.

---

## Development History

### EdBot 2.0

- Introduced two primary scripts:
  - `edbot_command.py`: Handles commands like playing MP3s and sending messages.
  - `edbot_listener.py`: Listens for keywords and performs actions like weather updates.
- Cleaned up code with the help of ChatGPT.

### EdBot 1.0

- Consisted of four main scripts:
  - `WeatherBot.py`: The original bot, now renamed `edbot_listener.py`.
  - `WeatherBotCommand.py`: Now `edbot_command.py`, included TTS functionality.
  - `IncomingTextsServer.py` and `TextMessagePoster.py`: Removed due to potential abuse.
- Early experimentation with OpenAI APIs.

---

## Things to Know

- **No `main.py`**: Each script must be run individually.
- **Environment Variables**: Use the provided `.env` template.
- **Dependencies**:
  - Python 3.8+ and the packages listed in `requirements.txt`.
  - FFMPEG for audio features.
- ~~**TTS Setup**:~~
  - ~~Requires an AWS account.~~
  - ~~Create a `.aws` folder in your home directory with a credentials file.~~

---

## Todo

- Integrate EdBot into a Boston Dynamics Spot robot (requires $75,000 in funding).

---

Enjoy using EdBot 3.0! Contributions and feedback are welcome.
