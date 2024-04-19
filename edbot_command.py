#I'm sorry for all the imports
import os
import random
import discord #discord stuff
from discord.ext import commands, tasks #More Discord
import time
import ffmpeg #for playing audio files through commandline to discord
import asyncpraw #Reddit Async Library
from dotenv import load_dotenv #env stuff
import asyncio #For Async commands bc discord needs them
from boto3 import Session #for TTS
from botocore.exceptions import BotoCoreError, ClientError #More TTS
from contextlib import closing #Even More TTS
import sys 
import subprocess 
import json #For Contacts File
import wolframalpha
import yt_dlp


load_dotenv()


mathID = os.getenv('WRA_MATH_KEY')
TOKEN = os.getenv('DISCORD_TOKEN')

reddit = asyncpraw.Reddit(
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    user_agent=os.getenv('USER_AGENT'),
)

yt_dlp.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
	'format': 'bestaudio/best',
	'outtmpl': 'data/%(title)s.%(ext)s',  # Saves files under the `data/` directory
	'restrictfilenames': True,
	'noplaylist': True,
	'nocheckcertificate': True,
	'ignoreerrors': False,
	'logtostderr': False,
	'quiet': True,
	'no_warnings': True,
	'default_search': 'auto',
	'source_address': '0.0.0.0'  # Bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
	def __init__(self, source, *, data, volume=0.5):
		super().__init__(source, volume)
		self.data = data
		self.title = data.get('title')
		self.url = ""

	@classmethod
	async def from_url(cls, url, *, loop=None, stream=False):
		loop = loop or asyncio.get_event_loop()
		data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
		
		if 'entries' in data:
			# take first item from a playlist
			data = data['entries'][0]

		# Ensure the /data directory exists
		if not os.path.exists('data'):
			os.makedirs('data')

		filename = data['title'] if stream else ytdl.prepare_filename(data)
		
		# Adjust filename path to include data/ prefix explicitly, ensuring compatibility
		if not filename.startswith('data/'):
			filename = os.path.join('data', os.path.basename(filename))

		return filename

#Sends a gif in the channel where called and then joins to play some audio and then leave
async def audioPlayer(ctx, audioFile, textToSend):
	
	if ctx.voice_client is None:
		if ctx.author.voice:
			print("Need to get in")
			audio_source = discord.FFmpegPCMAudio(audioFile)
			print("afterFF")
			voice_channel = ctx.author.voice.channel
			channel = None
			if voice_channel != None:
				channel = voice_channel.name
				vc = await voice_channel.connect()
			print("I connected")
			if not vc.is_playing():
				print("trying1")
				vc.play(audio_source, after=None)
				vc.pause() #This and the async sleep is needed or else the audio will be way faster then it should
				await asyncio.sleep(2)
				vc.resume()
				await ctx.send(textToSend)
			else:
				print("something is wrong")
	else:
		print("Already here")
		if ctx.voice_client.is_playing():
			await ctx.send("I'm busy")
		else:
			audio_source = discord.FFmpegPCMAudio(audioFile)	
			server = ctx.message.guild
			vc = server.voice_client
			if not vc.is_playing():
				print("trying1")
				vc.play(audio_source, after=None)
				vc.pause() #This and the async sleep is needed or else the audio will be way faster then it should
				await asyncio.sleep(2)
				vc.resume()
				await ctx.send(textToSend)
	return 

#Reads whatever garbage I put in a text file to the discord where the command was called
async def copyPasta(ctx, txtFile):
	copypastafile = open(txtFile, 'r')
	Lines = copypastafile.readlines()
	for line in Lines:
		await ctx.send(line)
	copypastafile.close()
	return

#Pings the people listed in the .env that it's time to game	
async def callingAllGamers(ctx, envData, whatToSay):
	gamers = os.getenv(envData)
	await ctx.send(gamers)
	await ctx.send(whatToSay)
	return
    
from discord.ext import commands

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='./',intents=intents)

@bot.event
async def on_ready():
	print('im here') #Giving EdBot Depression
	
@bot.command(name='meme', help='when someone sends an absolute MEME')
async def meme(ctx):
	await audioPlayer(ctx, 'notfunny.mp3', "https://c.tenor.com/BM-QtYCZIloAAAAd/not-funny-didnt-laugh.gif")

@bot.command(name='walled', help='GET TILTED')
async def walled(ctx):
	await audioPlayer(ctx, 'walled.mp3', "http://files.pykosh.com/files/gif/wall.gif")

@bot.command(name='PVS', help='GET HYPER')
async def walled(ctx):
	await audioPlayer(ctx, 'PVS.mp3', "I'm sorry")
	
@bot.command(name='bamba', help='GET SINGING')
async def walled(ctx):
	await audioPlayer(ctx, 'LaBamba.mp3', "I'm sorry")

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

#This should also be it's own fuction or another Python File, but once again dealing with async stuff is hell.
# Edit - I just can't be bothered
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
	await audioPlayer(ctx, 'last_tts.mp3', "TTS Created")

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
	
#Using WolfRamAlpha API to do complex stuff
@bot.command(name='domath', help='does some math and other stuff')
async def domath(ctx, *,mathRequest):
	client = wolframalpha.Client(mathID)
	await ctx.send("hmmmm let me think")
	# Stores the response from
	# wolf ram alpha
	try:
		res = client.query(mathRequest)

		# Includes only text from the response
		answer = next(res.results).text
	except:
		answer = "Sorry but I don't know"

	await ctx.send(answer)

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
	await callingAllGamers(ctx, 'FORTNITE_PEOPLE', "Fortnite time")
	
#Pings the people listed in the .env that it's time to game
@bot.command(name='valorant', help='valoreeee')
@commands.cooldown(1, 15, commands.BucketType.user) #Cooldown to prevent spam
async def valorant(ctx):
	await callingAllGamers(ctx, 'VALORANT_PEOPLE', "Valorant time")

#These next 4 are pretty self explanitory, just a shitpost command
@bot.command(name='kurt', help='my opinion on kurt thomspon')
async def kurt(ctx):
	await copyPasta(ctx, "copy_pastas/kurt.txt")

@bot.command(name='tuning', help='my opinion on tuning')
async def tuning(ctx):
	print("being commanded")
	await copyPasta(ctx, "copy_pastas/tune.txt")
	
@bot.command(name='yamaha', help='my opinion on yamaha')
@commands.cooldown(1, 15, commands.BucketType.user) #Cooldown to prevent spam
async def yamaha(ctx):
	await copyPasta(ctx, "copy_pastas/yamaha.txt")

@bot.command(name='genz', help='my opinion on zoomers')
@commands.cooldown(1, 15, commands.BucketType.user) #Cooldown to prevent spam
async def genz(ctx):
	await copyPasta(ctx, "copy_pastas/genz.txt")
	
@bot.command(name='cctuba', help='my opinion on cctuba')
@commands.cooldown(1, 15, commands.BucketType.user) #Cooldown to prevent spam
async def cctuba(ctx):
	await copyPasta(ctx, "copy_pastas/cctuba.txt")
	
#Yells at user if they are on cooldown 
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send('This command is on cooldown, you can use it in ' + str(round(error.retry_after, 2)) + ' seconds' )
        

@bot.command(name='play', help='To play song')
async def play(ctx,url):
	try:
		async with ctx.typing():
			print("Attempting Download")
			await ctx.send("Downloading...")
			filename = await YTDLSource.from_url(url, loop=bot.loop)
			print("Download completed")
			await audioPlayer(ctx, filename, '**Now playing:** {}'.format(filename))
			# voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=filename)) 
	except Exception as e:
		await ctx.send("Something went wrong: " + e)

@bot.command(name='play_song', help='To play song')
async def play(ctx,url):
	await ctx.send("It's ./play now")

@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.pause()
    else:
        await ctx.send("The bot is not playing anything at the moment.")
    
@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("The bot was not playing anything before this. Use play_song command")

@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
    else:
        await ctx.send("The bot is not playing anything at the moment.")

@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()
	
@bot.command(name='ben', help='god help us all')
@commands.cooldown(1, 5, commands.BucketType.user)
async def ben(ctx):
	benVoice = random.choice(["ben/ben_laugh.mp3" , "ben/ben_yes.mp3", "ben/ben_no.mp3", "ben/ben_grunt.mp3"])
	await audioPlayer(ctx, benVoice, "calling ben")
	
@bot.command(name='bow', help='LETS GET IT')
@commands.cooldown(1, 5, commands.BucketType.user)
async def ben(ctx):
	await audioPlayer(ctx, "BOW.webm", "on it")

bot.run(TOKEN) #Kickoff EdBot





