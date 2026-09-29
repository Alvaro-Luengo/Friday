import re
import os
import sys
import time
import asyncio
import tempfile
from pathlib import Path

# Pygame para reproducción de audio de alta fidelidad sin bloqueos
import pygame
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()
except Exception:
    pass

import winsound
from enginestart import initiate_engine
from config import VOICE_ENGINE, NEURAL_VOICE, VOICE_RATE

def clean_for_speech(text: str) -> str:
    """Limpia markdown, código y símbolos no legibles para voz."""
    if not text:
        return ""
    text = re.sub(r'```[\s\S]*?```', 'bloque de código omitido', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'https?://\S+', 'enlace web', text)
    text = re.sub(r'[*_#~>]', '', text)
    # Pronunciación fonética natural en español para Friday ('Fráidey')
    text = re.sub(r'\b[Ff]riday\b', 'Fráidey', text)
    text = re.sub(r'\bFRIDAY\b', 'Fráidey', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def play_ready_chime():
    """Tono ascendente que indica: 'Friday te escucha, ya puedes hablar'."""
    try:
        winsound.Beep(1046, 65)  # Nota C6
        winsound.Beep(1568, 90)  # Nota G6
    except Exception:
        pass

def play_processing_chime():
    """Tono descendente de confirmación que indica: 'Petición capturada, procesando...'."""
    try:
        winsound.Beep(1318, 50)  # Nota E6
        winsound.Beep(988, 70)   # Nota B5
    except Exception:
        pass

def play_activation_chime():
    """Compatibilidad: reproduce tono de 'ya puedes hablar'."""
    play_ready_chime()

async def _synthesize_edge_tts(text: str, output_path: str):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice=NEURAL_VOICE, rate=VOICE_RATE)
    await communicate.save(output_path)

def speak_edge(text: str) -> bool:
    """Sintetiza y reproduce con la voz neuronal humana de Edge-TTS."""
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_file = f.name

        asyncio.run(_synthesize_edge_tts(text, temp_file))

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        pygame.mixer.music.load(temp_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
        
        pygame.mixer.music.unload()
        return True
    except Exception as e:
        print(f"[Aviso]: Falló voz neuronal ({e}). Usando respaldo local...")
        return False
    finally:
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass

def speak_local(text: str):
    """Respaldo offline con pyttsx3."""
    try:
        engine = initiate_engine()
        engine.setProperty("rate", 195)  # Velocidad más ágil
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"[Error en síntesis local: {e}]")

def speak(text: str):
    """Pronuncia el texto con la voz más natural y rápida posible."""
    if not text:
        return
    print(f"\n[Friday]: {text}")
    
    clean_text = clean_for_speech(text)
    if not clean_text:
        return

    if VOICE_ENGINE == "edge-tts":
        success = speak_edge(clean_text)
        if not success:
            speak_local(clean_text)
    else:
        speak_local(clean_text)

if __name__ == "__main__":
    print("Probando nueva voz de Friday...")
    play_activation_chime()
    speak("Hola Álvaro, mi voz ahora es rápida, fluida y totalmente humana.")
