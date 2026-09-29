import pyttsx3
from config import FRIDAY_LANGUAGE

def initiate_engine(language: str = None):
    """
    Inicializa el motor pyttsx3 y selecciona la mejor voz
    femenina disponible para Friday según el idioma configurado ('es' o 'en').
    """
    if language is None:
        language = FRIDAY_LANGUAGE

    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    
    target_keyword = "spanish" if language == "es" else "english"
    
    selected_voice = None
    for voice in voices:
        v_name = voice.name.lower()
        if target_keyword in v_name:
            # Priorizar voces femeninas (Helena, Sabina, Zira) que encajan con Friday
            if any(fem in v_name for fem in ["helena", "sabina", "zira", "female"]):
                selected_voice = voice.id
                break
            selected_voice = voice.id

    if selected_voice:
        engine.setProperty("voice", selected_voice)
    elif voices:
        engine.setProperty("voice", voices[0].id)

    engine.setProperty("rate", 175)    # Velocidad de habla óptima
    engine.setProperty("volume", 1.0)   # Volumen máximo
    return engine
