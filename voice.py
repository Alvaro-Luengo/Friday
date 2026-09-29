import re
import speech_recognition as sr
from config import FRIDAY_LANGUAGE, PREFERRED_MICROPHONE

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.pause_threshold = 1.6  # Espera 1.6 segundos de silencio antes de cortar (no salta antes)
recognizer.non_speaking_duration = 0.5

# Variantes fonéticas para activar a Friday en español e inglés
WAKE_WORDS = [
    "friday",
    "fraydey",
    "frayday",
    "fraidey",
    "fraidei",
    "fraidi",
    "frayd",
    "viernes",
]

def get_recognition_language():
    return "es-ES" if FRIDAY_LANGUAGE == "es" else "en-US"

def get_microphone_device():
    """
    Selecciona el micrófono adecuado. Si PREFERRED_MICROPHONE está configurado
    (por ejemplo, 'fifine' o 'nvidia'), busca ese dispositivo específicamente.
    """
    names = sr.Microphone.list_microphone_names()
    target = PREFERRED_MICROPHONE.strip().lower() if PREFERRED_MICROPHONE else ""
    
    if target:
        for idx, name in enumerate(names):
            if target in name.lower():
                return sr.Microphone(device_index=idx), name

    # Por defecto, busca si existe fifine o nvidia antes de caer al predeterminado
    for idx, name in enumerate(names):
        if "fifine" in name.lower():
            return sr.Microphone(device_index=idx), name

    for idx, name in enumerate(names):
        if "nvidia broadcast" in name.lower():
            return sr.Microphone(device_index=idx), name

    # Dispositivo predeterminado del sistema operativo
    return sr.Microphone(), "Dispositivo Predeterminado de Windows"

# Inicializar y calibrar micrófono al arrancar
active_microphone, active_mic_name = get_microphone_device()
try:
    with active_microphone as mic:
        recognizer.adjust_for_ambient_noise(mic, duration=0.4)
except Exception:
    pass

GREETING_WORDS = {"hey", "oye", "hola", "ok", "eh", "ey", "buenos", "días", "buenas", "tardes", "noches"}

WAKE_PATTERNS = [
    r'\b(?:hey\s+|oye\s+|hola\s+|ok\s+|eh\s+|ey\s+|ay\s+)?(?:friday|fraydey|frayday|fraidey|fraidei|fraidi|frayd|fridi|freeday|free\s*day|viernes)\b',
    r'\b(?:air|ay|ey|hay|eh)\s*(?:fri|fry|frai|fray|fraidi|fridi)\b',
    r'\bair\s+fri\b',
    r'\bfri\s*day\b'
]

def detect_wake_word(text: str) -> tuple[bool, str]:
    """
    Detecta si el texto escuchado contiene cualquier variante de activación ('Friday', 'Hey Friday', 'Air Fri', etc.).
    Toma únicamente lo que viene DESPUÉS de la activación como comando.
    Devuelve (True, comando_restante) o (False, "").
    """
    if not text:
        return False, ""

    text_lower = text.lower().strip()

    for pattern in WAKE_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            after = text_lower[match.end():].strip()
            words = [w for w in after.split() if w not in GREETING_WORDS]
            clean_cmd = " ".join(words).strip()
            return True, clean_cmd

    return False, ""

def listen_for_wake_word() -> str:
    """Escucha continua del micrófono sin desconexiones para detectar 'Friday' o 'Hey Friday' al instante."""
    lang = get_recognition_language()
    recognizer.pause_threshold = 0.8
    recognizer.non_speaking_duration = 0.5
    with active_microphone as mic:
        try:
            # timeout=None mantiene el micrófono abierto sin reinicios periódicos
            audio = recognizer.listen(mic, timeout=None, phrase_time_limit=7)
            return recognizer.recognize_google(audio, language=lang).lower().strip()
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return ""
        except Exception:
            return ""

def listen_for_command(timeout: int = 8, phrase_time_limit: int = 15) -> str:
    """Escucha paciente para la orden de Álvaro (1.3s de margen sin cortes al respirar/pensar)."""
    lang = get_recognition_language()
    recognizer.pause_threshold = 1.3
    recognizer.non_speaking_duration = 0.5
    with active_microphone as mic:
        try:
            audio = recognizer.listen(mic, timeout=timeout, phrase_time_limit=phrase_time_limit)
            return recognizer.recognize_google(audio, language=lang).lower().strip()
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            return ""
        except Exception:
            return ""

def listen(timeout: int = 5, phrase_time_limit: int = 15) -> str:
    """Compatibilidad: delega en escucha de comandos."""
    return listen_for_command(timeout=timeout, phrase_time_limit=phrase_time_limit)