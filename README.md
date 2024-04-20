# EdBot-Discord
EdBot 2.0 - GPT to the rescue

Origin:
---
EdBot was orginally a bot named WeatherBot that meant to annoy people on Discord by
telling them the current weather in a given city

Disclaimer:
---
EdBot 2.0 is now *less* of a coding malpratice. Some parts of it are still weird but ChatGPT helped clean up a ton of this.

Still though, copy and paste my code responsibly if you are gonna try and use parts of this thing.

What EdBot 2.0 is:
---
There are two primary scripts - edbot_command.py and edbotlistener.py.

* The Command script waits for someone to do a "./" command and then it acts accordingly.
  * It's primary functions are playing MP3's and dumping copy pastas with some added bonuses put in.
* The Listener scripts waits for keywords and does an action based on what it read.
  * Mostly just tells the weather and tells people to shut up.
  * Inspired by the Todd (Howard) Discord Bot.


What EdBot 1.0 was:
---
EdBot consists of 4 main parts:
* WeatherBot.py
  * This was the originating code and ToddBot part of EdBot. Now renamed EdBot-Listener 
* WeatherBotCommand.py
  * Now named EdBot-Command
  * This portion also include a Text-to-Speech portion (similar to what you hear on twitch streams)
* IncomingTextsServer.py and TextMessagePoster.py
  * This used to do some cool stuff with texting and calling via the Twilio but can be subject to abuse so I pulled all relevant function and going to make a new Repo for it.
* There was also 5th script to this that used OpenAI before ChatGPT was a thing.
  * It is no longer used because I could not really wrap my head around it
  * When I did manage to wrap my head around one part, the bot literally told me to go Alt-F4 myself
  * This was also before ChatGPT was a thing so the AI was really rowdy.

Things You Should Know if you try to use this:
---
* Good luck.
* There is no main.py - To use, you must call each of the scripts individually.
* I included a template .env file for the env variables.
* I also included the other files that the scripts reference in the assests folder.
* You'll need to install or have FFMPEG on your PATH to get the audio part to work.
  * Linux people use these:
    * apt install libffi-dev libnacl-dev python3-dev
    * apt install ffmpeg
* Project should run on anything Python past v3.8 . The requirements.txt should have what you need for Python dependencies.
* For TTS to work, you'll need a AWS account 
  * Also need to make a .aws folder in your /Users folder (For Windows at least).
  * Inside that you'll need a credentials file from AWS
  * Amazon probably has a guide on this 

Todo:
---
Find $75,000 and put EdBot inside a Boston Dynamics' robot dog Spot.
