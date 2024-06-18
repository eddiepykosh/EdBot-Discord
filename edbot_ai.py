import discord
import ollama
import logging
from discord.ext import commands
from dotenv import load_dotenv
import os
load_dotenv()

# Find where script is running
script_dir = os.path.dirname(__file__)

TOKEN = os.getenv('DISCORD_TOKEN')
MODEL_NAME = "llama3"

# logging.basicConfig(filename='log.txt', level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')

intents = discord.Intents.default()
intents.messages = True 

bot = commands.Bot(command_prefix='@Chat ', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user.name}')

@bot.event
async def on_message(message):
    username = str(message.author).split('#')[0]
    user_message = str(message.content)

    if message.author == bot.user:
        return

    if bot.user.mentioned_in(message):
        command = message.content.replace(f'<@!{bot.user.id}>', '').strip()

        response = ollama.generate(model=MODEL_NAME, prompt=f"You are EdBot, a helpful Discord AI.  Here is your prompt that a user has gave you: {user_message}")

        # await message.channel.send(response["response"])
        ai_reponse_path = os.path.join(script_dir, 'data', 'last_ai_response.txt')
        with open(ai_reponse_path, 'w') as file:
            file.write(response["response"])
            file.close()
        print("Done Writing")


        try:
            with open(ai_reponse_path, 'r') as ai_response_file:
                # Reading all lines at once
                lines = ai_response_file.readlines()
                ai_response_file.close()
            # Sending all lines as a single message
            # Joining lines and ensuring the message does not exceed Discord's character limit
            content = ''.join(lines)
            if len(content) <= 2000:
                await message.channel.send(content)
            else:
                # If the message is too long, send it in chunks
                for start in range(0, len(content), 2000):
                    await message.channel.send(content[start:start + 2000])
        except FileNotFoundError:
            await message.channel.send("Oops! The file was not found.")
        except IOError:
            await message.channel.send("An error occurred while reading the file.")
        except discord.HTTPException as e:
            await message.channel.send(f"An error occurred when sending the message: {str(e)}")


    await bot.process_commands(message)

bot.run(TOKEN)