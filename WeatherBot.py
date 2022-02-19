#The orginal version of EdBot.  Originally named "WeatherBot" 
#Does not use a command prefix and checks every message that comes in to see if it matches a keyword.  If it does, then EdBot does an action.  Similar to how ToddBot works.

import os
import random
import discord
#Weather Thing API
from pyowm import OWM
from pyowm.utils import config
from pyowm.utils import timestamps
#More Discord stuff (not even sure if this is needed tbh)
from discord.ext import commands
#Env stuff
from dotenv import load_dotenv

load_dotenv()


#initalize Lists
speakerLoop = [0]
currentSpeaker = ['tom nook'] #I needed a inital name so I used Tom Nook :)
cityList = ['pittsburgh', 'waco', 'harrisburg', 'indiana', 'donora'] #Inital set of cities for WeatherBot to check each incoming message for

#This part gets more cites from a txt file.
#I was lazy and didn't want to manually add these to a list variable so it does this instead.
txt_file = open("more cities.txt", "r")
file_content = txt_file.read()
cityList += file_content.split("\n")
txt_file.close()
for i in range(len(cityList)):
    cityList[i] = cityList[i].lower()
print(cityList)

#Gets the Weather Lady
weatherPerson = os.getenv('WEATHER_PERSON')

#WeatherBot has some anger issues.  You can set a user for him to bully in the .env file
bully = os.getenv('BULLIED_USER')
bullyWords = ['fuck you', 'tiny mouth', 'tuba'] #Mean words for WeatherBot to say to a targeted user

#get tokens from .env file
TOKEN = os.getenv('DISCORD_TOKEN')
owm = OWM(os.getenv('OWM_TOKEN'))
mgr = owm.weather_manager()

#Init Discord Client variable
client = discord.Client()

#This lets you know WeatherBot/EdBot has connected and is ready to meme
@client.event
async def on_ready():
	print(f'{client.user.name} has connected to Discord!')

#Where all the magic happens
#Anytime a message comes in to any discord EdBot/WeatherBot is in, this clock block is triggered
@client.event
async def on_message(message):
	#decides to be a jerk to the targeted user in env file
	if str(message.author) == bully: #First we gotta make sure it is the targeted user speaking
		chanceToBully = random.randrange(1, 25) #This probably isn't the best way to do RNG
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
	
client.run(TOKEN) #Kicks off the script



