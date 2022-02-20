import os
from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
import subprocess
app = Flask(__name__)

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
	print("start")
	response = MessagingResponse()
	response.message("")
	number = request.form['From']
	body = request.form['Body']
	content = (str(number) + " " + str(body))
	with open('textmessage.txt', 'a') as file:
		file.write(content)
		file.close()
	print("Done")
	return str(response)
	

if __name__ == "__main__":
    app.run(host = '0.0.0.0')

'''
So this is a Flask web server that my Twilio is pointed to for whenever my Twilio number recieves a text message
When my Twilio number recieves a text, twilio will do either GET or POST request to this server with the contents of the message it recieved.
When that happens, this code will write that text to a running log file for TextMessagePost.py to pickup.
Then the script will return an empty response to Twilio to complete the web request.

The biggest "Issue" with this code is that instead of writing to a text file like it is now, it should ought to call another
discord python script instad.  The issue I ran into was with the async libraries not
closing gracefully.  Writing to a text file was my workaround.
'''
