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
#More Discord stuff (not even sure if this is needed tbh)
from discord.ext import commands
#Env stuff
from dotenv import load_dotenv
import asyncio
from pyppeteer import launch

load_dotenv()

# Find where script is running
script_dir = os.path.dirname(__file__)

#initalize Lists
speakerLoop = [0]
currentSpeaker = ['tom nook'] #I needed a inital name so I used Tom Nook :)
cityList = ['pittsburgh', 'waco', 'harrisburg', 'indiana', 'donora'] #Inital set of cities for WeatherBot to check each incoming message for

#This part gets more cites from a txt file.
#I was lazy and didn't want to manually add these to a list variable so it does this instead.
city_file_path = os.path.join(script_dir, 'assets', 'text', 'cities.txt')
try:
	with open(city_file_path, 'r') as file:
        # Read the file
		city_file_content = file.read()
		cityList += city_file_content.split("\n")
		file.close()
except FileNotFoundError:
    print(f"The file {city_file_path} was not found.")


for i in range(len(cityList)):
    cityList[i] = cityList[i].lower()
print(cityList)

#Gets the Weather Lady
weatherPerson = os.getenv('WEATHER_PERSON')

#WeatherBot has some anger issues.  You can set a user for him to bully in the .env file
bully = os.getenv('BULLIED_USER')
bullyWords = ['fuck you', 'tiny mouth', 'tuba', 'fuck blood bowl', 'I shall forward this to your grad school', 'lol comm banned', 'you are giving me a panic attack', 'dylan PLEASE', "I'm BEGGING", "Watch out for the guy on the hill.. be sure to KOS.", "Eddie has a higher KD than you"] #Mean words for WeatherBot to say to a targeted user

#get tokens from .env file
TOKEN = os.getenv('DISCORD_TOKEN')
owm = OWM(os.getenv('OWM_TOKEN'))
mgr = owm.weather_manager()

#Init Discord Client variable
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

#This lets you know WeatherBot/EdBot has connected and is ready to meme
@client.event
async def on_ready():
	print(f'{client.user.name} has connected to Discord!')

#Where all the magic happens
#Anytime a message comes in to any discord EdBot/WeatherBot is in, this clock block is triggered
@client.event
async def on_message(message):
	#print("Someone Talked")
	#decides to be a jerk to the targeted user in env file
	if str(message.author) == bully: #First we gotta make sure it is the targeted user speaking
		chanceToBully = random.randrange(1, 50) #This probably isn't the best way to do RNG
		if chanceToBully == 2:
			response = random.choice(bullyWords)
			await message.channel.send(response)
			
	#Stops from talking to himself
	if message.author == client.user:
		return
	
	#Checks if someone is being annoying	
	if message.author == currentSpeaker[0]:
		speakerLoop[0] += 1
	else: 
		currentSpeaker[0] = message.author
		speakerLoop[0] = 1
	if speakerLoop[0] >= 10:
		speakerLoop[0] = 0
		response = "Hey " + message.author.mention + " can you SHUT THE FUCK UP"
		await message.channel.send(response)			
		

	#If ANY part of someones message contains a city in cityList, then we proceed 
	if any(cities.lower() in message.content.lower() for cities in cityList):
		try: 
			#This is a try block because sometimes some will say a word that accidentitly cpntains a city word.
			#For example "experienced" contains the city "Erie" and because of that, the code block will crash bc of the spaghetti code below 
			print('running city command')
			print(message.author)
			messageList = message.content.lower()
			messageList = messageList.split(" ")
			cityListset = set(cityList) #No idea
			locations = [i for i, item in enumerate(messageList) if item in cityListset] #LMAO on the logic.  This looks for what city the user said in their message.
			observation = mgr.weather_at_place(messageList[locations[0]] + ", US")
			w = observation.weather
			w.temperature('fahrenheit')['temp'] #AMERICA
			response = "Hey "+ weatherPerson + "! Here is the weather in " + messageList[locations[0]].capitalize() + ": " + w.detailed_status.lower() #proper string formating is for nerds
			await message.channel.send(response)
		except: #Indicates the city command failed
			await message.channel.send("lol")

	if 'uwu' in message.content.lower(): #uwu is cringe
		print(message.author)
		response = message.author.mention + " stop that. "
		await message.channel.send(response)
		
	if 'guess whos back' in message.content.lower():
		print(message.author)
		response = "back again"
		await message.channel.send(response)
		
	if 'pog' in message.content.lower(): 
		print(message.author)
		chancetoPog = random.randrange(1, 5)  #This probably isn't the best way to do RNG
		if chancetoPog == 2:
			response = "<:retrenched:885980310754459730>"
			await message.channel.send(response)
	
	if 'austin' in message.content.lower():
		print(message.author)
		response = "<@690012125430546562>"
		await message.channel.send(response)
	
	if 'todd' in message.content.lower(): #EdBot gets meta
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
			messageList = message.content.lower()
			messageList = messageList.split(" ")
			orLocation = messageList.index("or")
			fighterOptions = [(messageList[orLocation + 1]), (messageList[orLocation - 1])] #There is a bug here where the option to the left of the "Or" must be a single word and cannot be multiple words
			response = random.choice(fighterOptions) + " would win." #IDK if I just had bad RNG but this will occassionaly favor the first selection
			await message.channel.send(response)
		except:
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
		
client.run(TOKEN) #Kicks off the script



