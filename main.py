import sys
import os
import datetime
from pathlib import Path

# Asegurar codificación utf-8 en Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import threading
from voice import listen_for_wake_word, listen_for_command, detect_wake_word, active_mic_name
from audio import speak, play_ready_chime, play_processing_chime, play_activation_chime
from hud_overlay import hud_indicator
from antigravity_bridge import ask_antigravity, is_followup_question
from commands import process_command
from config import (
    FRIDAY_LANGUAGE,
    FRIDAY_PIN,
    ENABLE_REMOTE_TUNNEL,
    LOG_FILE,
    ASSISTANT_NAME,
    VOICE_ENGINE,
    NEURAL_VOICE
)
from mobile_server import start_mobile_server, get_local_ip, MOBILE_SERVER_PORT
from telegram_bot import start_telegram_bot_thread

def log_event(message: str):
    """Escribe eventos importantes en el log de Friday."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass

def print_banner():
    ip = get_local_ip()
    banner = f"""
=================================================================
      ⚡ {ASSISTANT_NAME.upper()} V2.0 - ASISTENTE PERSONAL & ANTIGRAVITY HUB ⚡
=================================================================
  * Identidad:         {ASSISTANT_NAME} (Activación: "Friday" o "Fraydey")
  * Idioma:            {'Español' if FRIDAY_LANGUAGE == 'es' else 'English'}
  * Micrófono Activo:  {active_mic_name}
  * Motor de Voz:      {VOICE_ENGINE} ({NEURAL_VOICE})
  * Enlace Wi-Fi Casa: http://{ip}:{MOBILE_SERVER_PORT}
  * Enlace Fuera Casa: {'Iniciando túnel seguro HTTPS...' if ENABLE_REMOTE_TUNNEL else 'Desactivado'}
  * PIN de Seguridad:  {FRIDAY_PIN}
  * Antigravity AGY:   Activo (di 'Friday pregunta a agy...')
=================================================================
"""
    print(banner)
    log_event(f"Friday iniciado. Mic: {active_mic_name} | Wi-Fi: http://{ip}:{MOBILE_SERVER_PORT}")

def is_agy_task(cmd: str) -> bool:
    cmd_lower = cmd.lower()
    return any(k in cmd_lower for k in ["antigravity", "agy", "ask agy", "pregunta a agy", "pregúntale a agy"])

def handle_agy_dialogue(initial_cmd: str):
    """Gestiona el diálogo por voz bidireccional continuo con Antigravity en la misma sesión."""
    task = initial_cmd
    for prefix in ["antigravity", "pregunta a agy", "pregúntale a agy", "ask agy", "agy"]:
        task = task.replace(prefix, "")
    task = task.strip()
    if not task:
        task = "Hola, ¿en qué me puedes ayudar?"

    msg = "Consultando con el agente Antigravity..." if FRIDAY_LANGUAGE == "es" else "Consulting Antigravity agent..."
    speak(msg)

    agy_res = ask_antigravity(task, continue_session=False)
    speak(agy_res)

    # Si AGY hace una pregunta o invita a dar más información, mantener la conversación abierta
    while is_followup_question(agy_res):
        print("\n[AGY requiere seguimiento]. Abriendo micrófono para Álvaro...")
        hud_indicator.show(duration=15.0)
        play_ready_chime()
        user_reply = listen_for_command(timeout=8, phrase_time_limit=15)
        hud_indicator.hide()

        if not user_reply:
            print("[No se detectó respuesta de seguimiento. Finalizando conversación con AGY.]")
            break

        play_processing_chime()
        print(f"[Respuesta de Álvaro a AGY]: {user_reply}")

        # Comprobar si desea cancelar o salir
        if any(w in user_reply.lower() for w in ["nada", "cancela", "cancelar", "adiós", "salir", "olvídalo", "déjalo", "gracias"]):
            speak("Entendido Álvaro, quedo a la espera." if FRIDAY_LANGUAGE == "es" else "Understood, standing by.")
            break

        agy_res = ask_antigravity(user_reply, continue_session=True)
        speak(agy_res)

def voice_loop():
    """Bucle principal de escucha por micrófono del PC."""
    while True:
        try:
            print(f"\n[Micrófono: {active_mic_name}] Esperando activación ('Friday' / 'Hey Friday')...")
            text = listen_for_wake_word()

            if not text:
                continue

            print(f"[Oído]: {text}")

            # Detección fonética de Friday
            detected, inline_command = detect_wake_word(text)

            if detected:
                log_event(f"Activación por voz detectada: '{text}'")

                # Primer pitido de confirmación instantáneo ("Ya puedes hablar")
                play_ready_chime()
                # Mostrar el HUD con el micrófono azul en la esquina superior izquierda
                hud_indicator.show(duration=15.0)

                # Si el usuario ya dictó la orden completa (ej: "Friday pon ColdPlay en Spotify")
                if inline_command:
                    play_processing_chime()  # Segundo pitido ("Procesando")
                    hud_indicator.hide()
                    print(f"[Comando directo]: {inline_command}")
                    if is_agy_task(inline_command):
                        handle_agy_dialogue(inline_command)
                    else:
                        process_command(inline_command, speak_aloud=True)
                else:
                    # El usuario sólo dijo "Friday" o "Hey Friday":
                    # NO hablamos ningún saludo, dejamos el micrófono abierto para escuchar su orden inmediatamente
                    print("[Esperando orden de Álvaro tras el pitido...]")
                    command = listen_for_command(timeout=8, phrase_time_limit=15)
                    hud_indicator.hide()

                    if command:
                        play_processing_chime()  # Segundo pitido ("Procesando")
                        print(f"[Comando recibido]: {command}")
                        if is_agy_task(command):
                            handle_agy_dialogue(command)
                        else:
                            process_command(command, speak_aloud=True)

        except KeyboardInterrupt:
            print(f"\n[!] Apagando {ASSISTANT_NAME}...")
            hud_indicator.hide()
            hud_indicator.stop()
            speak("Hasta pronto, señor Álvaro." if FRIDAY_LANGUAGE == "es" else "Goodbye, sir.")
            log_event("Friday apagado por el usuario.")
            sys.exit(0)
        except Exception as e:
            hud_indicator.hide()
            print(f"[Error en bucle de voz]: {e}")
            log_event(f"Error en bucle de voz: {e}")

def main():
    print_banner()

    # 0. Iniciar indicador visual HUD en pantalla
    hud_indicator.start()

    # 1. Servidor móvil web y túnel Cloudflare en segundo plano
    server_thread = threading.Thread(target=start_mobile_server, daemon=True)
    server_thread.start()

    # 2. Bot de Telegram opcional
    start_telegram_bot_thread()

    # 3. Bucle de voz por micrófono en el hilo principal
    voice_loop()

if __name__ == "__main__":
    main()