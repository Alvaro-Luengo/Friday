import pywhatkit
from audio import speak
import os #for future modifications#
from huggingface_hub import InferenceClient
import re


API_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")
client = InferenceClient(provider="hf-inference", api_key=API_TOKEN) if API_TOKEN else None


def process_command(command):
    
    if "search on google" in command or "google" in command:
        query = command
        for phrase in ["search on google", "search google for", "google"]:
            query= query.replace(phrase, "")
        query = query.strip()
        speak(f"Searching Google for: {query}")
        pywhatkit.search(query)

    elif "play" in command:
        song = command.replace("play", "").strip()
        speak(f"Playing {song} on YouTube.")
        pywhatkit.playonyt(song)

    elif "goodbye" in command or "exit" in command:
        speak("Goodbye, sir.")
        exit()

    elif "who am i" in command:
        speak("You are Álvaro Luengo, my creator")

    elif "thank you" in command:
        speak("you're welcome")

    else:
        commandresume = command + " summarize it the most you can so it only has around 5 lines" #so it makes faster the thinking
        speak("im working on that")
        completion = client.chat.completions.create(model="HuggingFaceTB/SmolLM3-3B",messages=[{"role": "user", "content": commandresume}])
        full_response = completion.choices[0].message["content"]
        clean_response = re.sub(r"<think>.*?</think>\s*", "", full_response, flags=re.DOTALL)
        speak(clean_response)
