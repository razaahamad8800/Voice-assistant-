import pyttsx3
import speech_recognition as sr
import datetime
import wikipedia
import webbrowser
import os
import pyjokes
import pyautogui
import time
import requests
from PyDictionary import PyDictionary
import schedule
import threading

# Initialize voice engine and dictionary
engine = pyttsx3.init()
dictionary = PyDictionary()
engine.setProperty('rate', 160)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id if len(voices) > 1 else voices[0].id)

# File paths
notes_file = "notes.txt"
reminder_file = "reminders.txt"
greeted = False

# Speak text aloud
def speak(text):
    print(f"Assistant: {text}")
    engine.say(text)
    engine.runAndWait()

# Time-based greeting
def wish_user():
    global greeted
    if greeted:
        return
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good Morning!"
    elif hour < 18:
        greeting = "Good Afternoon!"
    else:
        greeting = "Good Evening!"
    speak(greeting)
    speak("Nice to see you! How can I help today?")
    greeted = True

# Take microphone input
def take_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        try:
            audio = r.listen(source, timeout=5)
            query = r.recognize_google(audio, language='en-in')
            print(f"You said: {query}")
            return query.lower()
        except sr.UnknownValueError:
            speak("Sorry, I didn't get that.")
        except sr.WaitTimeoutError:
            speak("I didn't hear anything. Try again.")
    return "none"

# Weather using Open-Meteo (free, no key needed)
def get_weather(city="Delhi"):
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_data = requests.get(geo_url).json()
        lat = geo_data['results'][0]['latitude']
        lon = geo_data['results'][0]['longitude']
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current_weather=true"
        )
        weather = requests.get(weather_url).json()
        temp = weather["current_weather"]["temperature"]
        wind = weather["current_weather"]["windspeed"]
        speak(f"The current temperature in {city} is {temp}°C with wind speed {wind} km/h.")
    except:
        speak("Unable to get weather data.")

# Search query via DuckDuckGo → Wikipedia → Google fallback
def search_duckduckgo(query):
    url = f"https://api.duckduckgo.com/?q={query}&format=json"
    try:
        res = requests.get(url).json()
        answer = res.get("AbstractText") or res.get("Answer") or ""
        if answer:
            speak(answer)
        else:
            raise ValueError("No direct answer from DuckDuckGo")
    except:
        try:
            summary = wikipedia.summary(query, sentences=2)
            speak(summary)
        except:
            speak("I couldn't find an answer. Let me search it online.")
            webbrowser.open(f"https://www.google.com/search?q={query}")

# App launcher (UPDATED — YOUTUBE ADDED)
def open_app(app_name):
    if "chrome" in app_name:
        os.system("start chrome")
    elif "notepad" in app_name:
        os.system("start notepad")
    elif "calculator" in app_name:
        os.system("start calc")
    elif "youtube" in app_name:   # <-- ADDED THIS LINE
        webbrowser.open("https://www.youtube.com")
    else:
        speak("App not recognized.")

# Time announcer
def tell_time():
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"The time is {current_time}")

# Notes and reminders
def take_note(content):
    with open(notes_file, "a") as f:
        f.write(f"{datetime.datetime.now()}: {content}\n")
    speak("Note saved.")

def read_notes():
    if os.path.exists(notes_file):
        with open(notes_file, "r") as f:
            speak(f.read())
    else:
        speak("No notes found.")

def add_reminder(content):
    with open(reminder_file, "a") as f:
        f.write(f"{datetime.datetime.now()}: {content}\n")
    speak("Reminder saved.")

def read_reminders():
    if os.path.exists(reminder_file):
        with open(reminder_file, "r") as f:
            speak(f.read())
    else:
        speak("No reminders found.")

# Dictionary word meaning
def define_word(word):
    meaning = dictionary.meaning(word)
    if meaning:
        for key, value in meaning.items():
            speak(f"As a {key}, {word} means: {value[0]}")
    else:
        speak("I couldn't find the meaning.")

# Chitchat responses
def handle_intents(query):
    responses = {
        "good morning": "Good morning! Hope you're feeling refreshed.",
        "good afternoon": "Good afternoon! Ready to be productive?",
        "good evening": "Good evening! Hope you had a great day.",
        "thank you": "You're welcome!",
        "who created you": "I was created by Raza Ahamad using Python.",
        "do you love me": "I'm code, but I like your vibe!",
        "hello": "Hello! How can I assist you?",
        "hi": "Hi there!",
        "how are you": "All systems are go!",
        "what's up": "Just waiting for your command.",
        "your name": "I'm your voice assistant.",
        "bye": "Goodbye! Talk soon.",
        "stop": "Okay, I'm going silent."
    }
    for key in responses:
        if key in query:
            speak(responses[key])
            if key == "stop":
                return "stop"
            if key == "bye":
                return "exit"
            return "continue"
    return None

# Smart Reminder Scheduler
def schedule_reminder(message, time_str):
    def job():
        speak(f"Reminder: {message}")
    schedule.every().day.at(time_str).do(job)
    speak(f"Reminder scheduled at {time_str}.")

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Main loop
def main():
    wish_user()
    threading.Thread(target=run_scheduler, daemon=True).start()
    while True:
        query = take_command()
        if query == "none":
            continue

        intent = handle_intents(query)
        if intent == "exit":
            break
        elif intent == "stop" or intent == "continue":
            continue  # Prevent further processing if already handled

        elif "open" in query:
            open_app(query)
        elif "note" in query and "take" in query:
            speak("What should I note down?")
            content = take_command()
            if content != "none":
                take_note(content)
        elif "read note" in query:
            read_notes()
        elif "remind" in query and "add" in query:
            speak("What should I remind you about?")
            content = take_command()
            if content != "none":
                speak("At what time? Please say in HH:MM format.")
                time_str = take_command()
                schedule_reminder(content, time_str)
        elif "read reminder" in query:
            read_reminders()
        elif "time" in query:
            tell_time()
        elif "joke" in query:
            speak(pyjokes.get_joke())
        elif "weather" in query:
            get_weather()
        elif "meaning of" in query:
            word = query.replace("meaning of", "").strip()
            define_word(word)
        elif "search" in query and "youtube" in query:
            speak("Searching on YouTube...")
            search_term = query.replace("search", "").replace("on youtube", "").strip()
            webbrowser.open(f"https://www.youtube.com/results?search_query={search_term}")
        else:
            search_duckduckgo(query)

if __name__ == "__main__":
    main()
