import sys
import time

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import speech_recognition as sr
from config import PREFERRED_MICROPHONE, FRIDAY_LANGUAGE

def run_mic_test():
    print("=" * 65)
    print("         PRUEBA Y DIAGNÓSTICO DE MICRÓFONO PARA FRIDAY")
    print("=" * 65)
    
    names = sr.Microphone.list_microphone_names()
    print("\n[+] Dispositivos de audio detectados en tu PC:")
    for idx, name in enumerate(names):
        if any(keyword in name.lower() for keyword in ["mic", "fifine", "nvidia", "ugreen", "realtek", "input", "poco"]):
            print(f"    [{idx}] {name}")

    # Buscar micrófono seleccionado
    selected_idx = None
    selected_name = "Dispositivo Predeterminado de Windows"
    
    if PREFERRED_MICROPHONE:
        for idx, name in enumerate(names):
            if PREFERRED_MICROPHONE.lower() in name.lower():
                selected_idx = idx
                selected_name = name
                break

    print(f"\n[+] Micrófono que Friday usará:")
    print(f"    👉 {selected_name} (Índice: {selected_idx if selected_idx is not None else 'Default'})")

    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True

    try:
        mic = sr.Microphone(device_index=selected_idx)
    except Exception as e:
        print(f"[!] Error abriendo micrófono: {e}")
        return

    print("\n[+] Calibrando ruido ambiental durante 1 segundo (guarda silencio)...")
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
    print(f"    Umbral de energía calibrado: {recognizer.energy_threshold:.1f}")

    print("\n🎤 DI ALGO AHORA (Por ejemplo: 'Hola Friday cómo estás')...")
    print("    Escuchando durante 5 segundos...")

    lang = "es-ES" if FRIDAY_LANGUAGE == "es" else "en-US"
    with mic as source:
        try:
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
            print("[+] Audio capturado. Procesando reconocimiento...")
            text = recognizer.recognize_google(audio, language=lang)
            print("\n" + "=" * 65)
            print(f"✅ ¡RECONOCIMIENTO EXITOSO!")
            print(f"👉 Has dicho: \"{text}\"")
            print("=" * 65)
            print("\nTu micrófono funciona perfectamente y Friday te escucha sin problemas.")
        except sr.WaitTimeoutError:
            print("\n[-] Tiempo de espera agotado: no se detectó voz.")
            print("    Asegúrate de que el micrófono no esté silenciado físicamente.")
        except sr.UnknownValueError:
            print("\n[-] Se detectó sonido pero no se pudieron distinguir palabras claras.")
        except Exception as e:
            print(f"\n[!] Error: {e}")

    print("\n" + "=" * 65)

if __name__ == "__main__":
    run_mic_test()
