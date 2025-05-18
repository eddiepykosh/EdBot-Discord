import os
import random
import discord 
from discord.ext import commands, tasks 
import time
import asyncpraw # Reddit Async Library
from dotenv import load_dotenv # env stuff
import asyncio # For Async commands bc discord needs them
from boto3 import Session # for TTS
from botocore.exceptions import BotoCoreError, ClientError # More TTS
from contextlib import closing # Even More TTS
import wolframalpha
import yt_dlp
import pickle
import functools
import aiohttp
import asyncio
from datetime import datetime

from config import (
    DISCORD_TOKEN, AWS_ID, AWS_SECRET, API_BASE_URL, mathID, DATA_PATH, ASSETS_AUDIO_PATH, ASSETS_TEXT_PATH
)
from utils import load_pickle, save_pickle
from common.logger import get_logger

logger = get_logger(__name__)

# Find where script is running
#script_dir = os.path.dirname(__file__)

# Rock Paper Scissor Stuff
score_file = os.path.join(DATA_PATH, 'scores.pkl')
# Function to load scores from file
async def load_scores():
    if os.path.exists(score_file):
        try:
            with open(score_file, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading scores: {e}")
            return {}
    else:
        return {}
async def save_scores(scores):
    try:
        with open(score_file, 'wb') as f:
            pickle.dump(scores, f)
    except Exception as e:
        logger.error(f"Error saving scores: {e}")

all_scores = asyncio.run(load_scores())

# Function to load swear counts from a file
def load_swear_counts(filename):
    if os.path.exists(filename):
        with open(filename, 'rb') as file:
            return pickle.load(file)
    return {}



# Logic for Youtube Downloader

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
    'default_search': 'ytsearch',
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
        self.url = data.get('webpage_url')

    @classmethod
    async def from_url(cls, search, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=not stream))
        
        if 'entries' in data:
            # take first item from the results
            data = data['entries'][0]

        # Ensure the /data directory exists
        if not os.path.exists('data'):
            os.makedirs('data')

        filename = data['title'] if stream else ytdl.prepare_filename(data)
        
        # Adjust filename path to include data/ prefix explicitly, ensuring compatibility
        if not filename.startswith('data/'):
            filename = os.path.join('data', os.path.basename(filename))

        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# Begin universal functions
# Sends a message in the channel where called and then joins to play some audio
async def audioPlayer(ctx, audioFile, textToSend):
	
	if ctx.voice_client is None:
		if ctx.author.voice:
			logger.debug("Need to get in")
			audio_source = discord.FFmpegPCMAudio(audioFile)
			logger.debug("afterFF")
			voice_channel = ctx.author.voice.channel
			channel = None
			if voice_channel != None:
				channel = voice_channel.name
				vc = await voice_channel.connect()
			logger.debug("I connected")
			if not vc.is_playing():
				logger.debug("trying1")
				vc.play(audio_source, after=None)
				vc.pause() # This and the async sleep is needed or else the audio will be way faster then it should
				await asyncio.sleep(2)
				vc.resume()
				await ctx.send(textToSend)
			else:
				print("something is wrong")
	else:
		logger.debug("Already here")
		if ctx.voice_client.is_playing():
			await ctx.send("I'm busy")
		else:
			audio_source = discord.FFmpegPCMAudio(audioFile)	
			server = ctx.message.guild
			vc = server.voice_client
			if not vc.is_playing():
				logger.debug("trying1")
				vc.play(audio_source, after=None)
				vc.pause() # This and the async sleep is needed or else the audio will be way faster then it should
				await asyncio.sleep(2)
				vc.resume()
				await ctx.send(textToSend)
	return 

# Reads whatever garbage I put in a text file to the discord where the command was called
async def copyPasta(ctx, txtFile):
	# Using 'with' statement to handle file operations
	try:
		with open(txtFile, 'r') as copypastafile:
			# Reading all lines at once
			lines = copypastafile.readlines()
			copypastafile.close()
		# Sending all lines as a single message
		# Joining lines and ensuring the message does not exceed Discord's character limit
		content = ''.join(lines)
		if len(content) <= 2000:
			await ctx.send(content)
		else:
			# If the message is too long, send it in chunks
			for start in range(0, len(content), 2000):
				await ctx.send(content[start:start + 2000])

	except FileNotFoundError:
		await ctx.send("Oops! The file was not found.")
	except IOError:
		await ctx.send("An error occurred while reading the file.")
	except discord.HTTPException as e:
		await ctx.send(f"An error occurred when sending the message: {str(e)}")

# Pings the people listed in the .env that it's time to game	
async def callingAllGamers(ctx, envData, whatToSay):
	gamers = os.getenv(envData)
	await ctx.send(gamers)
	await ctx.send(whatToSay)
	return
    
from discord.ext import commands

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='./', intents=intents)

@bot.event
async def on_ready():
    logger.info('im here') # Giving EdBot Depression

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.startswith('./'):
        guild_name = message.guild.name if message.guild else "Direct Message"
        logger.info(f"Command received: {message.content} from {message.author} in {message.channel} (Server: {guild_name})")
    await bot.process_commands(message)

# Begin list of commands

# You can force EdBot out of your VC
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

# Use AWS Poly for TTS
@bot.command(name='tts', help='lol funny voice')
async def tts(ctx, *, whatTotts):
    text = str(whatTotts)
    logger.info("TTS: " + text)
    session = Session(aws_access_key_id=AWS_ID, aws_secret_access_key=AWS_SECRET)
    polly = session.client('polly', region_name='us-east-2')
    try:
        response = polly.synthesize_speech(Text=text, OutputFormat='mp3', VoiceId='Brian')

        if 'AudioStream' in response:

            with closing(response['AudioStream']) as stream:
                output = 'last_tts.mp3'
                try:
                    with open(output, 'wb') as file:
                        file.write(stream.read())
                        logger.info("Made TTS")

                except IOError as error:
                    logger.error(error)
                    await ctx.send("IOError: " + str(error))
                    return error
    except ClientError as error:
        logger.error(error)
        await ctx.send("ClientError: " + str(error))
        return error
    except BotoCoreError as error:
        logger.error(error)
        await ctx.send("BotoCoreError: " + str(error))
        return error
    await audioPlayer(ctx, 'last_tts.mp3', "TTS Created")

# Will never actually ban someone. Just a social experiment 
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
	
# Using WolfRamAlpha API to do complex stuff
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

# Ripped the logic of this straight out of Stack Overflow
@bot.command(name='reddit', help='Pull a hot post from the sub of your choice')
async def redditRandom(ctx, *, redditSub):
    try:
        # Initialize Reddit client inside async context
        async with asyncpraw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT'),
        ) as reddit:
            try:
                async with asyncio.timeout(10):  # Lowercase timeout
                    sub = await reddit.subreddit(redditSub)
                    
                posts = []
                async for submission in sub.hot(limit=20):
                    posts.append(submission)
                
                if not posts:
                    await ctx.send(f"No posts found in r/{redditSub}")
                    return
                
                await ctx.send(random.choice(posts).url)
                
            except asyncio.TimeoutError:
                await ctx.send("Reddit request timed out. Try again later")
                
    except asyncpraw.exceptions.PRAWException as e:
        await ctx.send(f"Reddit error: {str(e)}")
    except Exception as e:
        await ctx.send(f"Command failed: {str(e)}")


# Cooldown Warning
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send('This command is on cooldown, you can use it in ' + str(round(error.retry_after, 2)) + ' seconds' )

# Play audio for Youtube
@bot.command(name='play', help='To play a song from YouTube')
async def play(ctx, *, search: str):
    try:
        async with ctx.typing():
            filename = await YTDLSource.from_url(search, loop=bot.loop)
            voice_channel = ctx.author.voice.channel
            if not ctx.voice_client:
                await voice_channel.connect()
            else:
                await ctx.voice_client.move_to(voice_channel)
            logger.info("Download completed")
            await ctx.send('**Now playing:** {}'.format(filename.title))
            ctx.voice_client.play(filename, after=lambda e: print('Player error: %s' % e) if e else None)
    except Exception as e:
        await ctx.send("Nah: " + str(e))

# Audio Controllers

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
        await ctx.send("The bot was not playing anything before this. Use play command")

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

# Misc Commands

@bot.command(name='meme', help='when someone sends an absolute MEME')
async def meme(ctx):
	await audioPlayer(ctx, os.path.join(ASSETS_AUDIO_PATH, 'notfunny.mp3'), "https://c.tenor.com/BM-QtYCZIloAAAAd/not-funny-didnt-laugh.gif")

@bot.command(name='walled', help='GET TILTED')
async def walled(ctx):
	await audioPlayer(ctx, os.path.join(ASSETS_AUDIO_PATH, 'notfunny.mp3'), "http://files.pykosh.com/files/gif/wall.gif")

@bot.command(name='PVS', help='GET HYPER')
async def walled(ctx):
	await audioPlayer(ctx, os.path.join(ASSETS_AUDIO_PATH, 'songs', 'PVS.mp3'), "I'm sorry")
	
@bot.command(name='bamba', help='GET SINGING')
async def walled(ctx):
    await audioPlayer(ctx, os.path.join(ASSETS_AUDIO_PATH, 'songs', 'LaBamba.mp3'), "I'm sorry")
      
@bot.command(name='kitteroast', help="GET ROASTED")
async def kitteroast(ctx):
	await audioPlayer(ctx, os.path.join(ASSETS_AUDIO_PATH, 'songs', 'kitte_roast.m4a'), "I'm NOT sorry")

@bot.command(name='ben', help='god help us all')
@commands.cooldown(1, 5, commands.BucketType.user)
async def ben(ctx):
	benVoice = random.choice(["ben/ben_laugh.mp3" , "ben/ben_yes.mp3", "ben/ben_no.mp3", "ben/ben_grunt.mp3"])
	await audioPlayer(ctx, os.path.join(ASSETS_AUDIO_PATH, benVoice), "calling ben")
	
@bot.command(name='bow', help='LETS GET IT')
@commands.cooldown(1, 5, commands.BucketType.user)
async def ben(ctx):
	await audioPlayer(ctx, os.path.join(ASSETS_AUDIO_PATH, 'songs', 'BOW.webm'), "on it")

# Pings the people listed in the .env that it's time to game		
@bot.command(name='fortnite', help='fortnite')
@commands.cooldown(1, 15, commands.BucketType.user) #Cooldown to prevent spam
async def fortnite(ctx):
	await callingAllGamers(ctx, 'FORTNITE_PEOPLE', "Fortnite time")
	
# Pings the people listed in the .env that it's time to game
@bot.command(name='valorant', help='valoreeee')
@commands.cooldown(1, 15, commands.BucketType.user) #Cooldown to prevent spam
async def valorant(ctx):
	await callingAllGamers(ctx, 'VALORANT_PEOPLE', "Valorant time")

@bot.command(name='kurt', help='my opinion on kurt thomspon')
async def kurt(ctx):
	await copyPasta(ctx, os.path.join(ASSETS_TEXT_PATH, 'copy_pastas', 'kurt.txt'))

@bot.command(name='tuning', help='my opinion on tuning')
async def tuning(ctx):
	await copyPasta(ctx, os.path.join(ASSETS_TEXT_PATH, 'copy_pastas', 'tune.txt'))
	
@bot.command(name='yamaha', help='my opinion on yamaha')
@commands.cooldown(1, 15, commands.BucketType.user) 
async def yamaha(ctx):
	await copyPasta(ctx, os.path.join(ASSETS_TEXT_PATH, 'copy_pastas', 'yamaha.txt'))

@bot.command(name='genz', help='my opinion on zoomers')
@commands.cooldown(1, 15, commands.BucketType.user)
async def genz(ctx):
	await copyPasta(ctx, os.path.join(ASSETS_TEXT_PATH, 'copy_pastas', 'genz.txt'))
	
@bot.command(name='cctuba', help='my opinion on cctuba')
@commands.cooldown(1, 15, commands.BucketType.user)
async def cctuba(ctx):
	await copyPasta(ctx, os.path.join(ASSETS_TEXT_PATH, 'copy_pastas', 'cctuba.txt'))

@bot.command(name='rps')
async def rock_paper_scissors(ctx):
    username = str(ctx.author)
    
    # Initialize user scores if not present
    if username not in all_scores:
        all_scores[username] = {'userScore': 0, 'computerScore': 0, 'tieCounter': 0}

    userScore = all_scores[username]['userScore']
    computerScore = all_scores[username]['computerScore']
    tieCounter = all_scores[username]['tieCounter']
    
    # Game constants
    choices = ['rock', 'paper', 'scissors']
    tie = "It's a tie!"
    userWin = "You win!"
    computerWin = "Computer wins!"

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() in choices

    await ctx.send("Pick rock, paper, or scissors:")
    try:
        msg = await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        await ctx.send('You took too long to respond!')
        return

    userInput = msg.content.lower()
    computerGuess = random.choice(choices)

    await ctx.send(f"You chose: {userInput}")
    await ctx.send(f"The computer chose: {computerGuess}")

    # Determine the result
    if userInput == computerGuess:
        result = tie
        tieCounter += 1
    elif (userInput == 'rock' and computerGuess == 'scissors') or \
         (userInput == 'scissors' and computerGuess == 'paper') or \
         (userInput == 'paper' and computerGuess == 'rock'):
        result = userWin
        userScore += 1
    else:
        result = computerWin
        computerScore += 1

    await ctx.send(result)
    await ctx.send(f"Computer: {computerScore}, User: {userScore}, Ties: {tieCounter}")

    all_scores[username] = {'userScore': userScore, 'computerScore': computerScore, 'tieCounter': tieCounter}
    await save_scores(all_scores)
    await ask_to_play_again(ctx, bot)
    # Ask the user if they want to play again
# Function to check if the message is from the correct author and channel
async def check(msg, ctx):
    return msg.author == ctx.author and msg.channel == ctx.channel

async def ask_to_play_again(ctx, bot):
    await ctx.send("Do you want to play again? (yes/no)")

    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
        response = msg.content.lower()
        logger.debug(f"Received response: {response}")

        if response == 'yes':
            await rock_paper_scissors(ctx)  # Play again
        elif response == 'no':
            await ctx.send("Thanks for playing!")
        else:
            await ctx.send("Invalid response. Please respond with 'yes' or 'no'.")
    except asyncio.TimeoutError:
        await ctx.send('You took too long to respond. Exiting game.')

@bot.command(name='rpsscore', help='Rock Paper Scissors Score for you.')
async def score(ctx):
    username = str(ctx.author)
    if username in all_scores:
        userScore = all_scores[username]['userScore']
        computerScore = all_scores[username]['computerScore']
        tieCounter = all_scores[username]['tieCounter']
        await ctx.send(f"Your score - Wins: {userScore}, Losses: {computerScore}, Ties: {tieCounter}")
    else:
        await ctx.send("You don't have any scores yet. Play a game first!")

@bot.command(name='swear_count', help='how many times did you say a bad word?')
async def swear_count(ctx):
    swear_counts_file = os.path.join(DATA_PATH, 'swear_counts.pkl')
    swear_counts = load_swear_counts(swear_counts_file)
    user_id = str(ctx.author.id)
    total_swears = swear_counts.get(user_id, 0)
    await ctx.send(f"You have sworn a total of {total_swears} time(s).")



bot.run(DISCORD_TOKEN) # Kickoff EdBot





