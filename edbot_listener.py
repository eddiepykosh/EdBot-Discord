'''
The orginal version of EdBot.  Originally named "WeatherBot" 
Does not use a command prefix and checks every message that comes 
in to see if it matches a keyword.  If it does, 
then EdBot does an action.  Similar to how ToddBot works.
'''
import os
import random
import discord
# Weather Thing API
from pyowm import OWM
from pyowm.utils import config
from pyowm.utils import timestamps
# More Discord stuff (not even sure if this is needed tbh)
from discord.ext import commands
# .env stuff
from dotenv import load_dotenv
from playwright.async_api import async_playwright
import pickle

load_dotenv()

# Find where script is running
script_dir = os.path.dirname(__file__)

# initalize Lists
speaker_loop = [0]
current_speaker = ['tom nook']
city_list = ['norfolk']
bully_words = ['nah']
edbot_responses_list = ['whatever you say man']

# Gets the Weather Lady
weather_person = os.getenv('WEATHER_PERSON')
# This part gets cites from  cities.txt in assets/text.
city_file_path = os.path.join(script_dir, 'assets', 'text', 'cities.txt')
try:
	with open(city_file_path, 'r') as file:
        # Read the file
		city_file_content = file.read()
		city_list += city_file_content.split("\n")
		file.close()
except FileNotFoundError:
    print(f"The file {city_file_path} was not found.")


# for i in range(len(city_list)):
#     city_list[i] = city_list[i].lower()
# print(city_list)


# EdBot has some anger issues.  You can set a user for him to bully in the .env file
bullied_user = os.getenv('BULLIED_USER')
# This part gets cites from  bully_words.txt in assets/text.
bully_file_path = os.path.join(script_dir, 'assets', 'text', 'bully_words.txt')
try:
	with open(bully_file_path, 'r') as file:
        # Read the file
		bully_file_content = file.read()
		bully_words += bully_file_content.split("\n")
		file.close()
except FileNotFoundError:
    print(f"The file {bully_file_path} was not found.")

edbot_response_file_path = os.path.join(script_dir, 'assets', 'text', 'edbot_responses.txt')
try:
	with open(edbot_response_file_path, 'r') as file:
        # Read the file
		edbot_response_content = file.read()
		edbot_responses_list += edbot_response_content.split("\n")
		file.close()
except FileNotFoundError:
    print(f"The file {edbot_response_file_path} was not found.")

# Function to load swears from a file
def load_swears(filename):
    swears = {'not_bad': [], 'bad': [], 'really_bad': []}
    try:
        with open(filename, 'r') as file:
            for line in file:
                severity, swear = line.strip().split(',')
                if severity in swears:
                    swears[severity].append(swear)
    except FileNotFoundError:
        print(f"Error: The file '{filename}' was not found.")
    return swears

# Function to load swear counts from a file
def load_swear_counts(filename):
    if os.path.exists(filename):
        with open(filename, 'rb') as file:
            return pickle.load(file)
    return {}

def save_swear_counts(filename, swear_counts):
    with open(filename, 'wb') as file:
        pickle.dump(swear_counts, file)

swears = load_swears(os.path.join(script_dir, 'assets', 'text', 'swears.txt'))
swear_counts_file = os.path.join(script_dir, 'data', 'swear_counts.pkl')
swear_counts = load_swear_counts(swear_counts_file)

swear_responses = {
    'not_bad': ["pottymouth", "that's not nice"],
    'bad': ["you're starting to hurt my feelings", "i don't know why you keep doing that"],
    'really_bad': ["okay now i'm going to cry", "that's not nice at all :(", "why do you hate me"]
}

# Function to count swears in a message
def count_swears(message_content, swears):
    words_in_message = message_content.lower().split()
    swear_counts = {'not_bad': 0, 'bad': 0, 'really_bad': 0}

    for word in words_in_message:
        for severity, swear_list in swears.items():
            if word in swear_list:
                swear_counts[severity] += 1

    return swear_counts

# Function to get a random response based on severity
def get_random_response(severity):
    if severity in swear_responses:
        return random.choice(swear_responses[severity])
    return ""

# Get Discord and Weather Manager tokens from .env file
TOKEN = os.getenv('DISCORD_TOKEN')
owm = OWM(os.getenv('OWM_TOKEN'))
mgr = owm.weather_manager()

# Init Discord Client variable
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Connected 
@client.event
async def on_ready():
	print(f'{client.user.name} has connected to Discord!')

'''
Where all the magic happens.

Anytime a message comes in to any 
Discord EdBot/WeatherBot is in, this block is triggered.
'''

@client.event
async def on_message(message):
	# A jerk function that says mean things to the targeted user.
	if str(message.author) == bullied_user:
		chance_to_bully = random.randrange(1, 20)
		print('dylans talking')
		if chance_to_bully == 2:
			response = random.choice(bully_words)
			await message.channel.send(response)
			
	# Stops from talking to himself.
	if message.author == client.user:
		return
	
	# Checks if someone is being annoying.	
	if message.author == current_speaker[0]:
		speaker_loop[0] += 1
	else: 
		current_speaker[0] = message.author
		speaker_loop[0] = 1
	if speaker_loop[0] >= 10:
		speaker_loop[0] = 0
		response = "Hey " + message.author.mention + " can you like quiet down?"
		await message.channel.send(response)			
		

	# If ANY part of someones message contains a city in city_list, then we proceed. 
	if any(cities.lower() in message.content.lower() for cities in city_list):
		try: 
        # Normalize the message content and split into words
			message_content = message.content.lower()
			words_in_message = set(message_content.split())

			# Create a set from city_list with lowercase for comparison
			city_listset = {city.lower() for city in city_list}

			# Find intersection of sets to get matching city names
			matched_cities = words_in_message.intersection(city_listset)
			
			if matched_cities:
				print('Running city command')
				print(message.author)
				
				# Handling multiple cities in one message; just taking the first matched city for simplicity
				first_matched_city = matched_cities.pop()
				
				# Fetch weather using the matched city
				observation = mgr.weather_at_place(first_matched_city + ", US")
				w = observation.weather
				temperature = w.temperature('fahrenheit')['temp']
				detailed_status = w.detailed_status.lower()

				response = f"Hey {weather_person}! Here is the weather in {first_matched_city.capitalize()}: {detailed_status}, with a temperature of {temperature}°F."
				await message.channel.send(response)

		except Exception as e:
			# Proper error logging
			print(f"An error occurred: {str(e)}")
			await message.channel.send("I pooped.")

	if 'who would win' in message.content.lower():
		try:
			content_lower = message.content.lower()
			# Find the position of "or" in the message
			words = content_lower.split()
			if "or" not in words:
				raise ValueError("No 'or' found in message.")

			or_index = words.index("or")
			
			# Extract fighters: Consider words before and after "or"
			# Join words from 'who would win' to 'or' (excluding both)
			left_start = max(0, words.index("win") + 1) if "win" in words else 0
			right_end = len(words) - 1
			
			# Take words from 'win' to 'or' for the left fighter and 'or' to the end for the right fighter
			fighter_left = ' '.join(words[left_start:or_index])
			fighter_right = ' '.join(words[or_index + 1:right_end + 1])
			
			# Validate fighters
			if not fighter_left or not fighter_right:
				raise ValueError("Fighter names cannot be parsed correctly.")

			# Choose a random fighter
			fighter_options = [fighter_left, fighter_right]
			winner = random.choice(fighter_options)
			response = f"{winner} would win."
			await message.channel.send(response)
		
		except Exception as e:
			print(f"Error: {str(e)}")
			await message.channel.send("You triggered my 'who would win' command but the parameters were invalid.")

	if 'FORTNITE STORE PLS' in message.content.upper():
		await message.channel.send("One sec")

		# Start Playwright and launch a browser
		async with async_playwright() as p:
			# Define a desktop user agent
			user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

			# Launch the browser and create a new context with the specified user agent
			browser = await p.chromium.launch()
			context = await browser.new_context(
				user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                device_scale_factor=1,
                color_scheme='light',
                locale='en-US'
			)
			
			# Open a new page within the context
			page = await context.new_page()

			# Navigate to the page
			await page.goto('https://fnbr.co/shop')

			# Define the path for the screenshot
			script_dir = os.path.dirname(os.path.abspath(__file__))  # Gets the directory of the current script
			data_dir = os.path.join(script_dir, 'data')
			os.makedirs(data_dir, exist_ok=True)  # Creates the data directory if it doesn't exist

			screenshot_path = os.path.join(data_dir, 'fortnite.png')
			await page.screenshot(path=screenshot_path, full_page=True)

			# Close the browser
			await browser.close()
			print("done")

			# Send the screenshot
			await message.channel.send(file=discord.File(screenshot_path))

	'''
	The rest of this is just generic comeback statements.
	'''

	if 'uwu' in message.content.lower():
		print(message.author)
		response = message.author.mention + " stop that. "
		await message.channel.send(response)
		
	if 'guess whos back' in message.content.lower():
		print(message.author)
		response = "back again"
		await message.channel.send(response)
		
	if 'pog' in message.content.lower(): 
		print(message.author)
		chancetoPog = random.randrange(1, 5)  # This probably isn't the best way to do RNG
		if chancetoPog == 2:
			response = "<:retrenched:885980310754459730>"
			await message.channel.send(response)
	
	if 'austin' in message.content.lower():
		print(message.author)
		response = "<@690012125430546562>"
		await message.channel.send(response)
	
	if 'todd' in message.content.lower(): # EdBot gets meta
		print(message.author)
		response = "im just a shitty toddbot"
		await message.channel.send(response)
	
	if '@everyone' in message.content.lower():
		print(message.author)
		response = "You have commited a grave sin " + message.author.mention
		await message.channel.send(response)
		
	if '@here' in message.content.lower():
		print(message.author)
		response = "You're on thin fucking ice " + message.author.mention
		await message.channel.send(response)
		
	if "how's the weather" in message.content.lower():
		print(message.author)
		response = "IT'S RAINING SIDEWAYS"
		await message.channel.send(response)

	if "do you have an umbrella" in message.content.lower():
		print(message.author)
		response = "HAD ONE"
		await message.channel.send(response)
		
	if "where is it" in message.content.lower():
		print(message.author)
		response = "INSIDE OUT - TWO MILES AWAY"
		await message.channel.send(response)

	if "anything we can do for you" in message.content.lower():
		print(message.author)
		response = "BRING ME SOME SOUP"
		await message.channel.send(response)

	if "what kind" in message.content.lower():
		print(message.author)
		response = "CHUNKY"
		await message.channel.send(response)
		
	if "shut up" in message.content.lower():
		print(message.author)
		response = "I'M SO FUCKING SCARED RIGHT NOW, YOU SHUT UP"
		await message.channel.send(response)
		
	if "look at him and tell me there's a god" in message.content.lower():
		print(message.author)
		response = "He made me in his own image."
		await message.channel.send(response)

	if "fly me to the moon" in message.content.lower():
		print(message.author)
		response1 = "let me kick it's fucking ass"
		response2 = "let me show it what i learned"
		response3 = "in my moon jujitsu class"
		await message.channel.send(response1)
		await message.channel.send(response2)
		await message.channel.send(response3)
	
	if "pokemon" in message.content.lower():
		print(message.author)
		response = "Pokemon GO to the polls"
		await message.channel.send(response)
		
	if "xd" in message.content.lower():
		print(message.author)
		response = "https://tenor.com/view/drinking-bleach-mug-clean-yourself-cleaning-gif-10137452"
		await message.channel.send(response)
		
	if "edbot" in message.content.lower():
		print(message.author)
		edbot_response = random.choice(edbot_responses_list)
		await message.channel.send(edbot_response)
	
	swear_count_message = count_swears(message.content, swears)
	total_swears = sum(swear_count_message.values())

	if total_swears > 0:
		user_id = str(message.author.id)
		if user_id not in swear_counts:
			swear_counts[user_id] = 0
		swear_counts[user_id] += total_swears
		save_swear_counts(swear_counts_file, swear_counts)

		#response = f"Your message had {total_swears} swear(s)."
		#await message.channel.send(response)

		# Random chance to send a response based on severity
		if swear_count_message['really_bad'] > 0 and random.random() < 0.5:  # 50% chance
			await message.channel.send(get_random_response('really_bad'))
		elif swear_count_message['bad'] > 0 and random.random() < 0.3:  # 30% chance
			await message.channel.send(get_random_response('bad'))
		elif swear_count_message['not_bad'] > 0 and random.random() < 0.1:  # 10% chance
			await message.channel.send(get_random_response('not_bad'))
		
client.run(TOKEN) # Kicks off the script



