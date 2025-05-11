import os
import random
import discord
from discord.ext import commands
from pyowm import OWM
from playwright.async_api import async_playwright

from config import (
	DISCORD_TOKEN, OWM_TOKEN, WEATHER_PERSON, BULLIED_USER,
	ASSETS_TEXT_PATH, DATA_PATH
)
from utils import (
	load_list_from_file, load_swears, load_pickle, save_pickle
)
from common.logger import get_logger

logger = get_logger(__name__)

# Load static data
logger.info("Loading static data...")
city_list = load_list_from_file(os.path.join(ASSETS_TEXT_PATH, 'cities.txt'))
bully_words = load_list_from_file(os.path.join(ASSETS_TEXT_PATH, 'bully_words.txt'))
edbot_responses_list = load_list_from_file(os.path.join(ASSETS_TEXT_PATH, 'edbot_responses.txt'))
swears = load_swears(os.path.join(ASSETS_TEXT_PATH, 'swears.txt'))
swear_counts_file = os.path.join(DATA_PATH, 'swear_counts.pkl')
swear_counts = load_pickle(swear_counts_file)

swear_responses = {
	'not_bad': ["pottymouth", "that's not nice"],
	'bad': ["you're starting to hurt my feelings", "i don't know why you keep doing that"],
	'really_bad': ["okay now i'm going to cry", "that's not nice at all :(", "why do you hate me"]
}

# Weather setup
logger.info("Setting up weather manager...")
owm = OWM(OWM_TOKEN)
mgr = owm.weather_manager()

# Discord client setup
logger.info("Setting up Discord client...")
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Speaker tracking
speaker_loop = [0]
current_speaker = ['']

def count_swears(message_content, swears):
	logger.debug("Counting swears in message...")
	words = message_content.lower().split()
	counts = {'not_bad': 0, 'bad': 0, 'really_bad': 0}
	for word in words:
		for severity, swear_list in swears.items():
			if word in swear_list:
				counts[severity] += 1
	logger.debug(f"Swear counts: {counts}")
	return counts

def get_random_response(severity):
	logger.debug(f"Getting random response for severity: {severity}")
	return random.choice(swear_responses[severity]) if severity in swear_responses else ""

@client.event
async def on_ready():
	logger.info(f'{client.user.name} has connected to Discord!')

@client.event
async def on_message(message):
	logger.debug(f"Received message: {message.content} from {message.author}")
	if message.author == client.user:
		logger.debug("Message is from the bot itself, ignoring.")
		return

	# Bully logic
	if str(message.author) == BULLIED_USER:
		logger.debug(f"Checking bully logic for user: {message.author}")
		if random.randrange(1, 20) == 2:
			response = random.choice(bully_words)
			logger.info(f"Sending bully response: {response}")
			await message.channel.send(response)

	# Speaker spam detection
	if message.author == current_speaker[0]:
		speaker_loop[0] += 1
	else:
		current_speaker[0] = message.author
		speaker_loop[0] = 1
	if speaker_loop[0] >= 10:
		logger.info(f"Speaker spam detected for user: {message.author}")
		speaker_loop[0] = 0
		await message.channel.send(f"Hey {message.author.mention} can you like quiet down?")

	# Weather command
	if any(city.lower() in message.content.lower() for city in city_list):
		logger.debug("Weather command detected.")
		try:
			message_content = message.content.lower()
			words_in_message = set(message_content.split())
			city_set = {city.lower() for city in city_list}
			matched_cities = words_in_message.intersection(city_set)
			if matched_cities:
				city = matched_cities.pop()
				logger.info(f"Fetching weather for city: {city}")
				observation = mgr.weather_at_place(city + ", US")
				w = observation.weather
				temp = w.temperature('fahrenheit')['temp']
				status = w.detailed_status.lower()
				response = f"Hey {WEATHER_PERSON}! Here is the weather in {city.capitalize()}: {status}, with a temperature of {temp}°F."
				logger.info(f"Sending weather response: {response}")
				await message.channel.send(response)
		except Exception as e:
			logger.error(f"Weather error: {str(e)}")
			await message.channel.send("I pooped.")

	# "Who would win" command
	if 'who would win' in message.content.lower():
		logger.debug("Who would win command detected.")
		try:
			content_lower = message.content.lower()
			words = content_lower.split()
			if "or" not in words:
				raise ValueError("No 'or' found in message.")
			or_index = words.index("or")
			left_start = max(0, words.index("win") + 1) if "win" in words else 0
			fighter_left = ' '.join(words[left_start:or_index])
			fighter_right = ' '.join(words[or_index + 1:])
			if not fighter_left or not fighter_right:
				raise ValueError("Fighter names cannot be parsed correctly.")
			winner = random.choice([fighter_left, fighter_right])
			logger.info(f"Who would win result: {winner}")
			await message.channel.send(f"{winner} would win.")
		except Exception as e:
			logger.error(f"Who would win error: {str(e)}")
			await message.channel.send("You triggered my 'who would win' command but the parameters were invalid.")

	# Fortnite Store screenshot
	if 'FORTNITE STORE PLS' in message.content.upper():
		logger.debug("Fortnite store command detected.")
		await message.channel.send("One sec")
		try:
			async with async_playwright() as p:
				browser = await p.chromium.launch()
				context = await browser.new_context(
					user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
					viewport={'width': 1920, 'height': 1080},
					device_scale_factor=1,
					color_scheme='light',
					locale='en-US'
				)
				page = await context.new_page()
				await page.goto('https://fnbr.co/shop')
				os.makedirs(DATA_PATH, exist_ok=True)
				screenshot_path = os.path.join(DATA_PATH, 'fortnite.png')
				await page.screenshot(path=screenshot_path, full_page=True)
				await browser.close()
				logger.info(f"Fortnite store screenshot saved to: {screenshot_path}")
				await message.channel.send(file=discord.File(screenshot_path))
		except Exception as e:
			logger.error(f"Fortnite store error: {str(e)}")

	# Fun and meme responses
	triggers = [
		('uwu', lambda: f"{message.author.mention} stop that. "),
		('guess whos back', lambda: "back again"),
		('pog', lambda: "<:retrenched:885980310754459730>" if random.randrange(1, 5) == 2 else None),
		('todd', lambda: "im just a shitty toddbot"),
		('@everyone', lambda: f"You have commited a grave sin {message.author.mention}"),
		('@here', lambda: f"You're on thin fucking ice {message.author.mention}"),
		("how's the weather", lambda: "IT'S RAINING SIDEWAYS"),
		("do you have an umbrella", lambda: "HAD ONE"),
		("where is it", lambda: "INSIDE OUT - TWO MILES AWAY"),
		("anything we can do for you", lambda: "BRING ME SOME SOUP"),
		("what kind", lambda: "CHUNKY"),
		("shut up", lambda: "I'M SO FUCKING SCARED RIGHT NOW, YOU SHUT UP"),
		("look at him and tell me there's a god", lambda: "He made me in his own image."),
		("pokemon", lambda: "Pokemon GO to the polls"),
		("xd", lambda: "https://tenor.com/view/drinking-bleach-mug-clean-yourself-cleaning-gif-10137452"),
		("edbot", lambda: random.choice(edbot_responses_list)),
	]
	for trigger, response_func in triggers:
		if trigger in message.content.lower():
			logger.debug(f"Trigger detected: {trigger}")
			response = response_func()
			if response:
				logger.info(f"Sending trigger response: {response}")
				await message.channel.send(response)
			if trigger == "fly me to the moon":
				logger.info("Sending additional responses for 'fly me to the moon'")
				await message.channel.send("let me kick it's fucking ass")
				await message.channel.send("let me show it what i learned")
				await message.channel.send("in my moon jujitsu class")
			break

	# Swear tracking
	swear_count_message = count_swears(message.content, swears)
	total_swears = sum(swear_count_message.values())
	if total_swears > 0:
		logger.debug(f"Swear tracking: {swear_count_message}")
		user_id = str(message.author.id)
		swear_counts[user_id] = swear_counts.get(user_id, 0) + total_swears
		save_pickle(swear_counts_file, swear_counts)
		logger.info(f"Updated swear counts for user {user_id}: {swear_counts[user_id]}")
		# Random chance to respond to swears
		if swear_count_message['really_bad'] > 0 and random.random() < 0.5:
			response = get_random_response('really_bad')
			logger.info(f"Sending really_bad swear response: {response}")
			await message.channel.send(response)
		elif swear_count_message['bad'] > 0 and random.random() < 0.3:
			response = get_random_response('bad')
			logger.info(f"Sending bad swear response: {response}")
			await message.channel.send(response)
		elif swear_count_message['not_bad'] > 0 and random.random() < 0.1:
			response = get_random_response('not_bad')
			logger.info(f"Sending not_bad swear response: {response}")
			await message.channel.send(response)

if __name__ == "__main__":
	logger.info("Starting bot...")
	client.run(DISCORD_TOKEN)
