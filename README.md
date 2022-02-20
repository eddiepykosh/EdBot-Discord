# EdBot-Discord
EdBot - My Son

Hello and welcome to my Python spaghetti code named EdBot!

Origin:
---
EdBot was orginally a bot named WeatherBot that meant to annoy people on Discord by
telling them the current weather in a given city

Disclaimer:
---
EdBot has become a coding malpratice and an example of what not to do for coding in Python.
Copy and paste my code responsibly if you are gonna try and use parts of this thing

What EdBot is now:
---
EdBot consists of 4 main parts:
* WeatherBot.py
  * This is the originating code and ToddBot part of EdBot.  This code works with the 
Discord Python API to check all incoming messages EdBot can see and then he will respond appropriately.
    * There are no major programming atrocities in this part.
* WeatherBotCommand.py
  * This is the real meat part of EdBot and where we enter the rabbit hole.
  * Everything here command based (by default I use ./) 
  * This once again uses the Discord Python API to read and post things to Discord
  * It also uses the Reddit API (asyncpraw) to get posts from Reddit and the Twilio API to call people and send text messages
  * This portion also include a Text-to-Speech portion (similar to what you hear on twitch streams)
* IncomingTextsServer.py
  * This code does not directly interact with Discord.
  * This script takes all incoming text messages to my Twilio number and saves it to text file for TextMessagePoster.py to pickup
  * See the comments in the code for more info on this part
* TextMessagePoster.py
  * This code is an infinite loop (remember when I said coding malpratice?) that check for updates to the text file that IncomingTextsServer.py is updating
  * See the comments in the code for more info on this part
* The was also 5th script to this that used OpenAI
  * It is no longer used because I could not really wrap my head around it
  * When I did manage to wrap my head around one part, the bot literally told me to go Alt-F4 myself  

Things You Should Know if you try to use this:
---
* Good luck.
* To use, you must call each of the 4 scripts individually 
* I included a template .env file for the env variables
* I also included the other files that the scripts reference for your reference
* You'll need to install FFMPEG to get the audio part to work
  * AND you'll need to pip in the Discord audio library
    * pip install -U discord.py[voice]
* For TTS to work, you'll need a AWS account 
  * Also need to make a .aws folder in your /Users folder
  * Inside that you'll need a credentials file from AWS
  * Amazon probably has a guide on this 

Todo:
---
Find $75,000 and put EdBot inside a Boston Dynamics' robot dog Spot.
