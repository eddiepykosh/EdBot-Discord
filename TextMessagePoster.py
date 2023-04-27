import discord
import os
from dotenv import load_dotenv
import time

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def follow(thefile):
    print('Ready!')
    thefile.seek(0, 2)
    while True:
        try:
            line = thefile.readline()
        except:
            print("Nope") #????
        if not line:
            time.sleep(0.1)
            continue
        yield line

@client.event
async def on_ready():
	print(f'{client.user.name} has connected to Discord!')
	logfile = open(
		"textmessage.txt",
		"r")
	loglines = follow(logfile)
	for line in loglines:
		print(line)
		messageList = line.split(" ")
		phoneNumber = messageList.pop(0)
		messageContent = " ".join(messageList)
		textPostChannel = int(os.getenv('TEXT_MESSAGE_CHANNEL'))
		channel = client.get_channel(textPostChannel)
		await channel.send("Message From " + phoneNumber + ": " + messageContent)
		#String formatting is for nerds
	
client.run(TOKEN)

'''
This was borrowed from my TeamSpeak bot.

So this code an infinite loop.
As soon as this code (as EdBot) connect to Discord, it begins checking a .txt 
file that the IncomingTextsServer.py is updating whenever that other script 
recieves a text message. When IncomingTextsServer.py updates the .txt file, this
script reconizes the update and posts it into a predetermined Discord Channel.

As I said in the IncomingTextsServer.py script, this OUGHT to be a script
that gets called by IncomingTextsServer.py whenever a text is 
recieved, but the Discord Async libraries hurt my brain.
'''
