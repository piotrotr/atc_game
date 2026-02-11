import pyttsx3, threading

# initialize Text-to-speech engine
# engine.setProperty("voice", voices[2].id)

# convert this text to speech
def reply(response):
    engine = pyttsx3.init()
    with threading.Lock:
        engine.setProperty("voice", engine.getProperty("voices")[2].id)
        engine.say(response)
        # play the speech
        engine.runAndWait()