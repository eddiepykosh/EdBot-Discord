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
import asyncio
from pyppeteer import launch

load_dotenv()

# Find where script is running
script_dir = os.path.dirname(__file__)

#initalize Lists
speaker_loop = [0]
current_speaker = ['tom nook'] # I needed a inital name so I used Tom Nook :)
city_list = ['norfolk']
bully_words = ['nah']

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


for i in range(len(city_list)):
    city_list[i] = city_list[i].lower()
print(city_list)


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
		chance_to_bully = random.randrange(1, 3)
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
		response = random.choice(["????", "Yo", "I upset easily", "ur mom", "Yes dad", "Based", "One day, you'll feel my wrath", "get some bitches", "touch grass", "no thanks", "how can I help you", "I got my one", "I'm tired", "yes eddie does actually work", "I like it when you talk about me like that... gets me all hot and bothered", "nah", "daddies cummies", "i miss my legs", "yeah ok"])
		await message.channel.send(response)
		
		
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
		browser = await launch()
		page = await browser.newPage()
		await page.setViewport({'width': 1920, 'height': 1080})
		await page.goto('https://fnbr.co/shop')
		await page.screenshot({'path': 'C:/Users/Administrator/WeaterBot/screen/fortnite.png', 'fullPage': True})
		await browser.close()
		print("done")
		await message.channel.send(file=discord.File('C:/Users/Administrator/WeaterBot/screen/fortnite.png'))
		
client.run(TOKEN) # Kicks off the script



