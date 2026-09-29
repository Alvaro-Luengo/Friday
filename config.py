import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Nombre del Asistente
ASSISTANT_NAME = os.getenv("ASSISTANT_NAME", "Friday")

# Configuración de APIs
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")

# Modelo preferido de Google Gemini
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

# Idioma de Friday: 'es' para Español, 'en' para Inglés
FRIDAY_LANGUAGE = os.getenv("FRIDAY_LANGUAGE", os.getenv("JARVIS_LANGUAGE", "es")).strip().lower()
JARVIS_LANGUAGE = FRIDAY_LANGUAGE

# Teléfono por defecto de mamá
MOM_PHONE = os.getenv("MOM_PHONE", "")

# Ruta de Antigravity CLI (agy) y permisos automáticos
AGY_PATH = os.getenv("AGY_PATH", r"C:\Users\alvar\AppData\Local\agy\bin\agy.exe")
AGY_SKIP_PERMISSIONS = os.getenv("AGY_SKIP_PERMISSIONS", "true").strip().lower() in ("true", "1", "yes")

# Servidor Móvil Web
MOBILE_SERVER_HOST = os.getenv("MOBILE_SERVER_HOST", "0.0.0.0")
MOBILE_SERVER_PORT = int(os.getenv("MOBILE_SERVER_PORT", "5000"))

# Acceso Remoto Fuera de Casa (Túnel HTTPS seguro)
ENABLE_REMOTE_TUNNEL = os.getenv("ENABLE_REMOTE_TUNNEL", "true").strip().lower() in ("true", "1", "yes")
TUNNEL_PROVIDER = os.getenv("TUNNEL_PROVIDER", "auto").strip().lower() # 'auto', 'cloudflare', 'ngrok', 'custom'

# Opción 1: Cloudflare Tunnel con Token (Link fijo permanente si tienes cuenta Cloudflare y dominio)
CLOUDFLARE_TUNNEL_TOKEN = os.getenv("CLOUDFLARE_TUNNEL_TOKEN", "").strip()

# Opción 2: Ngrok con Dominio Estático Gratuito (Link fijo 100% gratis para siempre sin comprar dominio)
NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "").strip()
NGROK_DOMAIN = os.getenv("NGROK_DOMAIN", "").strip()

# Enlace Fijo Personalizado o Dominio Asignado
FIXED_REMOTE_URL = os.getenv("FIXED_REMOTE_URL", os.getenv("CLOUDFLARE_TUNNEL_URL", "")).strip()

FRIDAY_PIN = os.getenv("FRIDAY_PIN", os.getenv("JARVIS_PIN", "1234")).strip()
JARVIS_PIN = FRIDAY_PIN

# Motor de Voz ('edge-tts' neural humana o 'pyttsx3' offline)
VOICE_ENGINE = os.getenv("VOICE_ENGINE", "edge-tts").strip().lower()
NEURAL_VOICE = os.getenv("NEURAL_VOICE", "es-ES-ElviraNeural").strip()
VOICE_RATE = os.getenv("VOICE_RATE", "+15%").strip()

# Micrófono Preferido en PC ('fifine', 'nvidia', 'ugreen', etc.)
PREFERRED_MICROPHONE = os.getenv("PREFERRED_MICROPHONE", "fifine").strip()

# Configuración Telegram Bot (Opcional)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID", "").strip()

# Archivos de registro
LOG_FILE = BASE_DIR / "friday.log"
URL_FILE = BASE_DIR / "current_url.txt"
