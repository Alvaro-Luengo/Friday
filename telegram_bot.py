import os
import sys
import time
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_ALLOWED_USER_ID, FRIDAY_LANGUAGE
from commands import process_command

# Asegurar codificación utf-8 en Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

class JarvisTelegramBot:
    def __init__(self, token: str = TELEGRAM_BOT_TOKEN, allowed_user_id: str = TELEGRAM_ALLOWED_USER_ID):
        self.token = token
        self.allowed_user_id = str(allowed_user_id).strip()
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0

    def is_configured(self) -> bool:
        return bool(self.token)

    def send_message(self, chat_id: int, text: str):
        url = f"{self.base_url}/sendMessage"
        try:
            requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
        except Exception as e:
            print(f"[Telegram] Error enviando mensaje: {e}")

    def run_polling(self):
        if not self.is_configured():
            print("[Telegram] Bot no configurado. Añade TELEGRAM_BOT_TOKEN en .env si deseas usarlo.")
            return

        print("\n" + "="*60)
        print("[+] BOT DE TELEGRAM DE JARVIS INICIADO")
        print("    Puedes hablar con Jarvis directamente desde la app de Telegram")
        print("="*60 + "\n")

        while True:
            try:
                url = f"{self.base_url}/getUpdates"
                params = {"offset": self.offset, "timeout": 20}
                res = requests.get(url, params=params, timeout=25)

                if res.status_code != 200:
                    time.sleep(3)
                    continue

                data = res.json()
                for update in data.get("result", []):
                    self.offset = update["update_id"] + 1

                    message = update.get("message")
                    if not message:
                        continue

                    chat_id = message["chat"]["id"]
                    user_id = str(message.get("from", {}).get("id", ""))
                    username = message.get("from", {}).get("username", "Usuario")

                    # Si hay un usuario permitido configurado, verificarlo
                    if self.allowed_user_id and user_id != self.allowed_user_id:
                        print(f"[Telegram] Acceso bloqueado para usuario no autorizado: {user_id} (@{username})")
                        self.send_message(chat_id, "⛔ Acceso denegado. No eres el creador autorizado de este sistema.")
                        continue

                    # Si es el primer mensaje y no hay ID configurado, mostrarlo en consola para que Álvaro lo copie
                    if not self.allowed_user_id:
                        print(f"\n[Telegram] Mensaje recibido de User ID: {user_id} (@{username})")
                        print(f"👉 Copia 'TELEGRAM_ALLOWED_USER_ID={user_id}' en tu archivo .env para proteger tu bot.\n")

                    text = message.get("text", "")

                    if text.startswith("/start"):
                        greeting = (
                            "⚡ *JARVIS ONLINE*\n\n"
                            "Hola señor Álvaro. Su enlace seguro por Telegram está activo.\n"
                            "Envíeme cualquier comando o consulta para su PC o Antigravity."
                        )
                        self.send_message(chat_id, greeting)
                        continue

                    if text:
                        print(f"[Telegram recibido]: {text}")
                        # Procesar comando a través de Jarvis (sin hablar por los altavoces del PC para mayor privacidad)
                        response = process_command(text, speak_aloud=False)
                        self.send_message(chat_id, f"🤖 Jarvis:\n{response}")

            except requests.exceptions.RequestException:
                time.sleep(5)
            except Exception as e:
                print(f"[Telegram Error]: {e}")
                time.sleep(3)

def start_telegram_bot_thread():
    import threading
    bot = JarvisTelegramBot()
    if bot.is_configured():
        t = threading.Thread(target=bot.run_polling, daemon=True)
        t.start()
        return t
    return None

if __name__ == "__main__":
    bot = JarvisTelegramBot()
    bot.run_polling()
