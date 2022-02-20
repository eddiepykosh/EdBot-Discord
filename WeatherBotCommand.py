#I'm sorry for all the imports
import os
import random
import discord #discord stuff
from discord.ext import commands #More Discord
import time
import ffmpeg #for playing audio files through commandline to discord
import asyncpraw #Reddit Async Library
from twilio.rest import Client #Call/Text Message API
from dotenv import load_dotenv #env stuff
import asyncio #For Async commands bc discord needs them
from boto3 import Session #for TTS
from botocore.exceptions import BotoCoreError, ClientError #More TTS
from contextlib import closing #Even More TTS
import sys 
import subprocess 
import json #For Contacts File

load_dotenv()

#Twilio Stuff
account_sid = os.getenv('TWILIO_ACCOUNT_ID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
TwilioPhoneNumber = os.getenv('TWILIO_PHONE_NUMBER')



TOKEN = os.getenv('DISCORD_TOKEN')

reddit = asyncpraw.Reddit(
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    user_agent=os.getenv('USER_AGENT'),
)


from discord.ext import commands

bot = commands.Bot(command_prefix='./')

@bot.event
async def on_ready():
	print('im here') #Giving EdBot Depression

#This part was meant to be a rudimentary exercise that ended up taking me 4 hours
#This should REALLY be it's own function but discord.py async stuff is hell to deal with
@bot.command(name='addcontact', help='add a contact')
async def contactadd(ctx, *,contactData):
	discordInput = contactData
	with open('contacts.json') as json_file:
		pythonDict = json.load(json_file)
		json_file.close()
	discordInputList = discordInput.split(" ")
	if len(discordInputList) == 3: #Checks if contact has a first and last name or just a first name and acts accordingly
		contactName = discordInputList.pop(0) + " " + discordInputList.pop(0)
	else:
		contactName = discordInputList.pop(0)
	contactPhone = discordInputList.pop(0)
	if len(contactPhone) == 10: #make sure number is valid bc I dont want people to call 911 on my bot
		newContact = {
			contactName.lower(): contactPhone
		}
		print(pythonDict)
		pythonDict.update(newContact)
		print(pythonDict)
		with open("contacts.json", "w") as f:
			json.dump(pythonDict, f)
			f.close()
		await ctx.send("Contact Added")
	else:
		await ctx.send("Invalid phone number idiot")

@bot.command(name='printcontacts', help='Print all known contact')
async def printcontacts(ctx):
	with open('contacts.json') as json_file:
		pythonDict = json.load(json_file)
		json_file.close()
	print(pythonDict)
	await ctx.send(str(pythonDict))

#Sends a gif in the channel where called and then joins to play some audio and then leave	
@bot.command(name='meme', help='when someone sends an absolute MEME')
async def meme(ctx):
	await ctx.send("https://c.tenor.com/BM-QtYCZIloAAAAd/not-funny-didnt-laugh.gif")
	audio_source = discord.FFmpegPCMAudio('notfunny.mp3')
	voice_channel = ctx.author.voice.channel
	channel = None
	if voice_channel != None:
		channel = voice_channel.name
		vc = await voice_channel.connect()
	if not vc.is_playing():
		vc.play(audio_source, after=None)
		vc.pause() #This and the async sleep is needed or else the audio will be way faster then it should
		await asyncio.sleep(2)
		vc.resume()
	while vc.is_playing():
		await asyncio.sleep(0.5)
	await vc.disconnect()

#Sends a gif in the channel where called and then joins to play some audio and then leave
@bot.command(name='walled', help='GET TILTED')
async def walled(ctx):
	await ctx.send("http://files.pykosh.com/files/gif/wall.gif")
	audio_source = discord.FFmpegPCMAudio('walled.mp3')
	voice_channel = ctx.author.voice.channel
	channel = None
	if voice_channel != None:
		channel = voice_channel.name
		vc = await voice_channel.connect()
	if not vc.is_playing():
		vc.play(audio_source, after=None)
		vc.pause() #This and the async sleep is needed or else the audio will be way faster then it should
		await asyncio.sleep(2)
		vc.resume()
	while vc.is_playing():
		await asyncio.sleep(0.5)
	await vc.disconnect()

#For if someone sends an annoyingly long TTS, you can force EdBot out of your VC
@bot.command(name='fuckoff', help='forces EdBot out of Voice')
async def leave(ctx):
	try:
		await ctx.voice_client.disconnect()
	except:
		await ctx.send("EdBot is not in voice")


@bot.command(name='streaming', help='eddie is streaming')
async def streamer(ctx):
	streamingChannel = int(os.getenv('STREAMING_CHANNEL'))
	channel = bot.get_channel(streamingChannel)
	await channel.send("My father is streaming at https://www.twitch.tv/edderdp")

@bot.command(name='parrot', help='ECHO ECho echo')
async def parrot(ctx, *,whatToParrot):
	parrotChannel = int(os.getenv('PARROT_CHANNEL'))
	channel = bot.get_channel(parrotChannel)
	await channel.send(whatToParrot)

#This should also be it's own fuction or another Python File, but once again dealing with async stuff is hell
#I didn't write the TTS code, that came from my friend for my TeamSpeak Bot
@bot.command(name='tts', help='lol funny voice')
async def tts(ctx, *,whatTotts):
	text = str(whatTotts)
	session = Session(profile_name='default')
	polly = session.client('polly', region_name='us-east-2')
	try:
		response = polly.synthesize_speech(Text=text, OutputFormat='mp3', VoiceId='Brian')

		if 'AudioStream' in response:
	
			with closing(response['AudioStream']) as stream:
				output = ('last_tts.mp3')
				try:
					with open(output, 'wb') as file:
						file.write(stream.read())
						print("Made TTS")
					
				except IOError as error:
					print(error)
					return error
	except ClientError as error:
		print(error)
		return error
	except BotoCoreError as error:
		print(error)
		return error
	audio_source = discord.FFmpegPCMAudio('last_tts.mp3')
	voice_channel = ctx.author.voice.channel
	channel = None
	if voice_channel != None:
		channel = voice_channel.name
		vc = await voice_channel.connect()
	if not vc.is_playing():
		vc.play(audio_source, after=None)
		vc.pause() #This and the async sleep is needed or else the audio will be way faster then it should
		await asyncio.sleep(2) 
		vc.resume()
	while vc.is_playing():
		await asyncio.sleep(0.5)
	await vc.disconnect()

#Will never actually ban someone. Just a social experiment 
@bot.command(name='ban', help='/ban @username')
async def ban(ctx, *,userName):
	await ctx.send("Okay, banning "  + userName + " in: ")
	time.sleep(1)
	await ctx.send("3")
	time.sleep(1)
	await ctx.send("2")
	time.sleep(1)
	await ctx.send("1")
	time.sleep(5)
	await ctx.send("HA. Bitch u thought")

#Ripped the logic of this straight out of Stack Overflow
@bot.command(name='reddit', help='Pull a hot post from the sub of your choice.   usage: ./reddit <inset sub here> ')
async def redditRandom(ctx, *,redditSub):
	try:
		posts = []
		sub = await reddit.subreddit(redditSub)
		hot = sub.hot(limit = 20)
		async for submission in hot:
			posts.append(submission)
		random_post = random.choice(posts)
		await ctx.send(random_post.url)
	except:
		await ctx.send("reddit command failed :(")

#Pings the people listed in the .env that it's time to game		
@bot.command(name='fortnite', help='fortnite')
@commands.cooldown(1, 15, commands.BucketType.user) #Cooldown to prevent spam
async def fortnite(ctx):
	fortniteGang = os.getenv('FORTNITE_PEOPLE')
	await ctx.send(fortniteGang)
	await ctx.send("Fortnite time")

#Pings the people listed in the .env that it's time to game
@bot.command(name='valorant', help='valoreeee')
@commands.cooldown(1, 15, commands.BucketType.user) #Cooldown to prevent spam
async def valorant(ctx):
	valorantGang = os.getenv('VALORANT_PEOPLE')
	await ctx.send(valorantGang)
	await ctx.send("Valorant time")

#Basically changes a .txt document from True to false or vice-versa
#DEFINITLY a better way to do this
@bot.command(name='togglewakeup', help='Turn on and off wakeup')
async def togglewakeup(ctx):
	botOwner = os.getenv('BOT_OWNER')
	if str(ctx.author) == botOwner : #Makes it so only I can use this command. DEFINITLY a better way to do this
		with open('togglewakeup.txt', 'r') as file:
			status = file.read().rstrip()
			file.close()
			print(status)
		if status == 'True':
			with open('togglewakeup.txt', 'w') as file:
				file.write('False')
				file.close()
			await ctx.send('Wake up is now OFF')
		else:
			with open('togglewakeup.txt', 'w') as file:
				file.write('True')
				file.close()
			await ctx.send('Wake up is now ON')
	else:
		await ctx.send('Sorry, but you are not Eddie')

#My pride and joy feature.  You can text someone from Discord
@bot.command(name='text', help='text someone')
@commands.cooldown(1, 15, commands.BucketType.user)
async def text(ctx, *,whatToText):
	stringList = whatToText.split(" ") #breaks everything after ./text into a list
	with open('contacts.json') as json_file: #Read in the contacts file
		pythonDict = json.load(json_file)
		json_file.close()
	smallWhattoText = whatToText.lower() #All contacts are in lowercase in the JSON.  This changes everything after ./text into lowercase
	discordNameList = smallWhattoText.split(" ") #Same thing as stringList
	try: #This checks if the first word after ./text is a phone number
		contactNumber = int(discordNameList[0]) #A phone number will always be an int 
		contactNumber = str(contactNumber) #Store found number
		stringList.pop(0) #kicks phone number out of the stringList that will be send to our target
	except: #This block triggers if the above try failed.  Now we will check if the first word after ./text is in our contacts JSON
		contactNumber = pythonDict.get(discordNameList[0]) #checks if a FIRST NAME only contact was found 
		if contactNumber is None: #We didn't find a FIRST NAME ONLY contact. Checking First AND Last name
			try:
				fullName = discordNameList[0] + " " + discordNameList[1]
				contactNumber = pythonDict.get(fullName)
				stringList.pop(0)
				stringList.pop(0)
			except:
				contactNumber = "INVALID" #For if the discordNameList is too short
			if contactNumber is None: #Couldn't find a valid phone number or a contact 
				contactNumber = "INVALID"
		else:
			stringList.pop(0) #Found a FIRST NAME ONLY contact
			
	#This whole section above should be it's own function
	
	try: #Checks the results of the above logic
		phoneNumber = int(contactNumber)
		phoneNumber = str(phoneNumber)
	except:
		await ctx.send("No contact found")
	if len(phoneNumber) == 10: #Makes sure number is valid (Don't want people texting 911)
		messageContent = " ".join(stringList)
		textAPI = Client(account_sid, auth_token)
		message = textAPI.messages \
						.create(
							 body="Message from EdBot: " + messageContent,
							 from_=TwilioPhoneNumber,
							 to='+1' + phoneNumber
						 )

		print(message.sid)
		await ctx.send("Message sent to " + phoneNumber)
	else:
		await ctx.send("invalid phone number")
	
@bot.command(name='call', help='call someone')
@commands.cooldown(1, 15, commands.BucketType.user)
async def call(ctx, *,whatToText):
	#Due to calls being alot more serious, user's must supply the phone number 
	#Also I'm lazy
	stringList = whatToText.split(" ")
	phoneNumber = stringList.pop(0)
	if len(phoneNumber) == 10:
		messageContent = " ".join(stringList)
		callAPI = Client(account_sid, auth_token)
		call = callAPI.calls.create(
							 url='http://files.pykosh.com/files/walled.mp3',
							 from_ =TwilioPhoneNumber,
							 to='+1' + phoneNumber,
							 method = 'GET'
						 )

		print(call.sid)
		await ctx.send("call sent.")
	else:
		await ctx.send("invalid phone number")
		
@bot.command(name='customcall', help='call someone by supplying your own mp3')
@commands.cooldown(1, 15, commands.BucketType.user)
async def customcall(ctx, *,whatToText):
	#Due to calls being alot more serious, user's must supply the phone number 
	#Also I'm lazy
	#There is no code here to check if link is a actual valid MP3.
	#If the MP3 is invalid the TWILIO API will play a "Call could not be completed" to target phone number
	stringList = whatToText.split(" ")
	phoneNumber = stringList.pop(0)
	mp3Link = stringList.pop(0)
	print(mp3Link)
	if len(phoneNumber) == 10: #Gotta make sure no one's doing anyone no-no's
		messageContent = " ".join(stringList)
		callAPI = Client(account_sid, auth_token)
		call = callAPI.calls.create(
							 url= mp3Link,
							 from_ =TwilioPhoneNumber,
							 to='+1' + phoneNumber,
							 method = 'GET' #Gotta use Get NOT POST bc most websites do not support POST for downloading stuff
						 )

		print(call.sid)
		await ctx.send("call sent.")
	else:
		await ctx.send("invalid phone number")

#These next 4 are pretty self explanitory, just a shitpost command
@bot.command(name='kurt', help='my opinion on kurt thomspon')
async def kurt(ctx):
	await ctx.send("I’m just gonna preface this by saying don’t read this, it’s long and I’m just ranting.")
	await ctx.send("Let me just say, Kurt Thompson is one of the most vile, egotistical trumpet players I have ever heard, and a total bigot.")
	await ctx.send("His playing is okay at best. He can get up there, but it sounds like shit. No consistency or good sound articulation, and he’s not good enough to have a style. The only thing he can do is play relatively high, otherwise he sounds like a goddamn 3rd grader.")
	await ctx.send("You wouldn’t be able to tell by his ego however, which is on a level I have never seen before. His ego passes that if any player I’ve ever seen and he appears to believe he is better than even Wayne Bergeron or Allen Vizzuti, saying that he leaves them all behind while playing his “quadruple g” (which is perhaps the most bullshit thing I’ve ever heard). And his ego makes him loud and annoying, and it makes young inexperienced folk listen to him.")
	await ctx.send("Which brings me to the worst part about him, his method. Because he can play high, that means young players thinks he’s amazing and will listen to what he says. And what he says is breeding the worst breed of trumpet players I have ever heard. I recently did a camp with some high school kids over the summer and judged their playing and attempted to help hem but they were some of the most unbearable children I’ve ever met. They repeated everything Kurt had ever said in his methods which is just total bs and makes no sense, and when I tried to get them on track to play decently they all asked how high I could play, and when I would not honor such a dumb question, they attempted to show me his method, that has made them all just terrible musicians. He markets to young kids that don’t know any better by flaunting his one ok talent, and it is giving them massive egos, a terrible view of the instrument, and none of them will let go.")
	await ctx.send("On top of that, he will do anything to sell his method. In a video description, he said that women aren’t as good at screaming trumpet and that the only thing to fix that was his course. That makes me sick. Calling women bad at trumpet and then trying to sell bullshit to make them better? That’s sexist and a shitty thing to do. He has called out other players by name and called them terrible and then tried to sell. He has squeaked a high note and tried to sell. He released perhaps the most egregious recording of MacArthur park and tried to sell because of that. I don’t know where I’m going with this, I got sidetracked, but this dude just fuckijg sucks.")
	await ctx.send("TLDR; fuck Kurt Thompson, a shitty player and an even shittier person.")

@bot.command(name='tuning', help='my opinion on tuning')
async def tuning(ctx):
	await ctx.send("I have heard of (factory tuned) tubas.  Does that mean they are tuned to a certain pitch or what?  Is there such a thing as a factory tuned tuba, does the term apply to other brass instruments?")
	await ctx.send("I have a very old tuba - my photo - made in the late 1800s in Grasliz Bohemia for the Carl Fuchs Music Company In Los Angeles, CA.  During tuning I seldom have to tinker with slides on my horn - all comments and questions are welcome.  By the way, many years ago while playing with the Palos Verdes Symphonic Band I was teased about my factory tuned Tuba.")
	await ctx.send("It embarrassed me, I reddened because I thought it was a criticism of my playing.  I’m still not sure what he meant but I’m going on my 56th year playing that same Tuba I purchased from Milt Marcus, a Tuba collector living in Long CA when I was 24.")
	
@bot.command(name='yamaha', help='my opinion on yamaha')
@commands.cooldown(1, 15, commands.BucketType.user) #Cooldown to prevent spam
async def yamaha(ctx):
	await ctx.send("As I've discussed with you elsewhere, I personally find every single Yamaha horn to be absolute garbage. Lifeless horns with no playability. They only play 'one way' and if you want to, or personally do, play differently, you will not get any better result. In fact it may, and likely will, play worse. I hate, hate, hate the sound of Yamaha low brass. It's so thin, lifeless, and boring. That's because Japanese musical culture values higher voices more than lower voices. That's why there's so much more of the fluff and junk from piccolos and flutes and all that mess in Japanese band literature.")

@bot.command(name='genz', help='my opinion on zoomers')
@commands.cooldown(1, 15, commands.BucketType.user) #Cooldown to prevent spam
async def genz(ctx):
	await ctx.send("Greetings fellow chatters of Trombone,")
	await ctx.send(' I write to you today in lieu of some, lets say…interesting fashion choices I’ve observed Gen Z make over the past couple of auditions I’ve taken. Just the other day I saw a young man show up to an audition in just a sweater and khakis. There wasn’t a single button in site! No buttons! Now if God has taught me one thing it is to never pass judgement on my fellow man. However, this time I couldn’t help but wonder “who does this little youknowwhat think he is??”')
	await ctx.send('The Gen Z media will have you believe that since the audition is “blind” you should “wear whatever you’re comfortable in.” I say shame on you. I cannot count how many lovely conversations I’ve had in musicians lounges waiting for the inevitable “the committee has decided to advance this candidate or that candidate”, that I simply wouldn’t have had had I not been wearing a button down and slacks! There’s a certain respect you earn with your attire in this business before you ever play a note. You never know who might have a gig ready for a handsome, put together trombonist. I mean, will this generation stop at nothing before they break down every barrier separating civil society from savagery?')
	await ctx.send('I’m wondering what the hive thinks about attire for blind auditions. Am I crazy or should you hold on to some dignity behind that screen?')
	await ctx.send('P.S. if someone could get me Steve Shires’ contact info I would really appreciate it. I’ve been working on a 3D printed valve with my nephew that I’d love to get his eyes on now that he’s making trombones again. Thanks.')
	
#Yells at user if they are on cooldown 
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send('This command is on cooldown, you can use it in ' + str(round(error.retry_after, 2)) + ' seconds' )
        
	
bot.run(TOKEN) #Kickoff EdBot





