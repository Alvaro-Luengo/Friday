import os
import re
import datetime
import json
import urllib.request
import urllib.parse
import subprocess
import webbrowser
import pywhatkit
import psutil
import google.generativeai as genai

from audio import speak
from call import makecall
from antigravity_bridge import ask_antigravity
from config import (
    GOOGLE_API_KEY,
    GEMINI_MODEL,
    FRIDAY_LANGUAGE,
    MOM_PHONE,
    ASSISTANT_NAME
)

# Configuración de Google Gemini API
if GOOGLE_API_KEY:
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"[Aviso] No se pudo configurar Gemini API: {e}")

from token_tracker import record_tokens, get_token_summary

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

WMO_WEATHER_CODES = {
    0: "cielo completamente despejado",
    1: "cielo mayormente despejado",
    2: "parcialmente nublado",
    3: "cielo nuboso",
    45: "niebla",
    48: "niebla con escarcha",
    51: "llovizna ligera",
    53: "llovizna moderada",
    55: "llovizna densa",
    61: "lluvia ligera",
    63: "lluvia moderada",
    65: "lluvia intensa",
    71: "nevada ligera",
    73: "nevada moderada",
    75: "nevada intensa",
    80: "chubascos dispersos",
    81: "chubascos moderados",
    82: "chubascos violentos",
    95: "tormenta eléctrica",
    96: "tormenta con granizo ligero",
    99: "tormenta con granizo fuerte"
}

def get_current_datetime_info(query: str = "") -> str:
    """Devuelve la fecha o la hora actual en español con precisión absoluta."""
    now = datetime.datetime.now()
    dia_sem = DIAS_SEMANA[now.weekday()]
    mes = MESES[now.month - 1]
    hora_str = now.strftime("%H:%M")

    # Si pregunta específicamente sólo por la hora
    if any(w in query for w in ["qué hora", "que hora", "la hora", "hora es", "tienes hora"]):
        return f"Son las {hora_str} en Madrid."

    # Si pregunta por el día o la fecha
    return f"Hoy es {dia_sem}, {now.day} de {mes} de {now.year}, y son las {hora_str}."

def get_madrid_weather(query: str = "") -> str:
    """Consulta el tiempo meteorológico en tiempo real para Madrid (hoy, mañana o resto de la semana)."""
    url = "https://api.open-meteo.com/v1/forecast?latitude=40.4168&longitude=-3.7038&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max&timezone=Europe%2FMadrid"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'FridayAssistant/2.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            current = data.get("current", {})
            daily = data.get("daily", {})
            now = datetime.datetime.now()
            today_idx = now.weekday()
            q = query.lower()

            # Caso 1: Mañana
            if "mañana" in q:
                if daily and len(daily.get("time", [])) > 1:
                    code_m = daily["weather_code"][1]
                    desc_m = WMO_WEATHER_CODES.get(code_m, "cielo variable")
                    max_m = round(daily["temperature_2m_max"][1])
                    min_m = round(daily["temperature_2m_min"][1])
                    prob_m = daily["precipitation_probability_max"][1]
                    dia_m = DIAS_SEMANA[(today_idx + 1) % 7]
                    rain_info = f"con un {prob_m}% de probabilidad de lluvia" if prob_m > 0 else "sin previsión de lluvias"
                    return f"Mañana {dia_m} en Madrid se espera {desc_m}, con una máxima de {max_m} grados, mínima de {min_m} grados y {rain_info}."

            # Caso 2: Resto de la semana / Esta semana / Próximos días / Fin de semana
            if any(k in q for k in ["semana", "fin de semana", "resto de la semana", "próximos días", "proximos dias", "días siguientes", "dias siguientes"]):
                if daily and len(daily.get("time", [])) >= 5:
                    parts = []
                    for i in range(1, min(6, len(daily["time"]))):
                        d_name = DIAS_SEMANA[(today_idx + i) % 7]
                        d_desc = WMO_WEATHER_CODES.get(daily["weather_code"][i], "cielo variable")
                        d_max = round(daily["temperature_2m_max"][i])
                        d_min = round(daily["temperature_2m_min"][i])
                        parts.append(f"{d_name.capitalize()}: {d_desc}, máxima de {d_max} y mínima de {d_min} grados")
                    summary_text = ". ".join(parts)
                    return f"El pronóstico para los próximos días en Madrid es: {summary_text}."

            # Caso 3: Tiempo actual / Hoy
            temp = round(current.get("temperature_2m", 20))
            sens = round(current.get("apparent_temperature", temp))
            code = current.get("weather_code", 0)
            desc = WMO_WEATHER_CODES.get(code, "cielo variable")
            wind = round(current.get("wind_speed_10m", 0))
            rain = current.get("precipitation", 0)

            today_max = round(daily.get("temperature_2m_max", [temp])[0]) if daily else temp
            today_min = round(daily.get("temperature_2m_min", [temp])[0]) if daily else temp

            rain_str = " No llueve actualmente." if rain == 0 else f" Se registra una precipitación de {rain} milímetros."
            return f"En Madrid tenemos actualmente {temp} grados con {desc}, sensación térmica de {sens} grados y viento a {wind} kilómetros por hora.{rain_str} Para hoy la máxima es de {today_max} y la mínima de {today_min} grados."
    except Exception:
        return "No pude conectar con el servicio meteorológico de Madrid en este momento."

def get_madrid_weather_data() -> dict:
    """Devuelve los datos estructurados meteorológicos de Madrid para la app móvil."""
    url = "https://api.open-meteo.com/v1/forecast?latitude=40.4168&longitude=-3.7038&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max&timezone=Europe%2FMadrid"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'FridayAssistant/2.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            current = data.get("current", {})
            daily = data.get("daily", {})
            now = datetime.datetime.now()
            today_idx = now.weekday()

            temp = round(current.get("temperature_2m", 20))
            sens = round(current.get("apparent_temperature", temp))
            code = current.get("weather_code", 0)
            desc = WMO_WEATHER_CODES.get(code, "cielo variable")
            wind = round(current.get("wind_speed_10m", 0))
            humidity = round(current.get("relative_humidity_2m", 50))
            rain = current.get("precipitation", 0)

            forecast = []
            if daily and "time" in daily:
                for i in range(len(daily["time"])):
                    d_code = daily["weather_code"][i]
                    d_desc = WMO_WEATHER_CODES.get(d_code, "variable")
                    d_name = DIAS_SEMANA[(today_idx + i) % 7]
                    forecast.append({
                        "date": daily["time"][i],
                        "day_name": "Hoy" if i == 0 else ("Mañana" if i == 1 else d_name.capitalize()),
                        "code": d_code,
                        "description": d_desc,
                        "temp_max": round(daily["temperature_2m_max"][i]),
                        "temp_min": round(daily["temperature_2m_min"][i]),
                        "rain_prob": daily.get("precipitation_probability_max", [0])[i],
                        "rain_sum": daily.get("precipitation_sum", [0])[i]
                    })

            return {
                "city": "Madrid",
                "current": {
                    "temperature": temp,
                    "apparent_temperature": sens,
                    "weather_code": code,
                    "description": desc,
                    "wind_speed": wind,
                    "humidity": humidity,
                    "rain": rain
                },
                "forecast": forecast
            }
    except Exception as e:
        return {"error": str(e), "city": "Madrid"}

def get_gemini_response(prompt: str) -> str:
    """Obtiene respuesta resumida e inteligente de Google Gemini y registra tokens."""
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        now = datetime.datetime.now()
        dia_sem = DIAS_SEMANA[now.weekday()]
        mes = MESES[now.month - 1]
        temporal_context = f"Fecha y hora actual real: {dia_sem} {now.day} de {mes} de {now.year}, {now.strftime('%H:%M')} (Madrid, España)."

        sys_instruction = (
            f"Contexto temporal estricto: {temporal_context}\n\n"
            f"{prompt}\n\n"
            f"Instrucción obligatoria: Eres {ASSISTANT_NAME}, la asistente personal de Álvaro Luengo. "
            "Responde de forma concisa, educada, eficiente y natural en un máximo de 3 oraciones breves "
            f"en idioma {'español' if FRIDAY_LANGUAGE == 'es' else 'inglés'}."
        )
        response = model.generate_content(sys_instruction)
        try:
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                record_tokens(
                    response.usage_metadata.prompt_token_count,
                    response.usage_metadata.candidates_token_count,
                    model=GEMINI_MODEL
                )
        except Exception:
            pass
        return response.text.strip()
    except Exception as e:
        if "429" in str(e) or "ResourceExhausted" in str(e):
            return "Has alcanzado el límite de peticiones gratuitas por minuto. Espera unos segundos, no se te cobrará nada."
        try:
            fallback_model = genai.GenerativeModel('gemini-2.5-flash-lite')
            res = fallback_model.generate_content(prompt)
            return res.text.strip()
        except Exception:
            return f"Hubo un error con la API de IA: {str(e)}"

def get_system_status() -> str:
    """Obtiene métricas de rendimiento del PC."""
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage('C:').percent
    battery = psutil.sensors_battery()
    bat_str = f", batería al {battery.percent}%" if battery else ""
    
    if FRIDAY_LANGUAGE == "es":
        return f"Todo en orden, señor Álvaro. CPU al {cpu}%, memoria RAM al {ram}% y almacenamiento principal al {disk}%{bat_str}."
    else:
        return f"All systems operational, sir. CPU at {cpu}%, RAM memory at {ram}%, and disk at {disk}%{bat_str}."

def get_system_status_data() -> dict:
    """Obtiene métricas estructuradas del sistema para la app móvil."""
    cpu = psutil.cpu_percent(interval=0.2)
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage('C:')
    battery = psutil.sensors_battery()
    
    return {
        "status": "online",
        "cpu_percent": cpu,
        "ram_percent": vm.percent,
        "ram_used_gb": round(vm.used / (1024**3), 2),
        "ram_total_gb": round(vm.total / (1024**3), 2),
        "disk_percent": disk.percent,
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "disk_total_gb": round(disk.total / (1024**3), 2),
        "battery_percent": battery.percent if battery else None,
        "power_plugged": battery.power_plugged if battery else True,
        "agy_available": True
    }

def process_command(command: str, speak_aloud: bool = True) -> str:
    """
    Procesa un comando de texto o voz y ejecuta la acción correspondiente.
    Devuelve la respuesta en texto.
    """
    cmd = command.strip().lower()
    if not cmd:
        return ""

    response_text = ""

    # 1. INTEGRACIÓN CON ANTIGRAVITY (AGY)
    if any(k in cmd for k in ["antigravity", "agy", "ask agy", "pregunta a agy", "código", "programa", "desarrolla", "soluciona"]):
        task = cmd
        for prefix in ["antigravity", "pregunta a agy", "pregúntale a agy", "ask agy", "agy"]:
            task = task.replace(prefix, "")
        task = task.strip()
        if not task:
            task = "explica qué herramientas tienes activas"

        msg = "Consultando con el agente Antigravity, por favor espera un momento..." if FRIDAY_LANGUAGE == "es" else "Querying Antigravity agent, please wait a moment..."
        if speak_aloud:
            speak(msg)

        agy_response = ask_antigravity(task)
        response_text = agy_response

    # 2. ESTADO DEL SISTEMA / ORDENADOR (CPU, RAM, DISCO, TEMPERATURA)
    elif (
        any(k in cmd for k in [
            "system status", "estado del sistema", "rendimiento", "cómo está el pc", "como esta el pc",
            "cómo está el ordenador", "como esta el ordenador", "estado del ordenador", "estado de la máquina",
            "estado del equipo", "estado pc", "estado ordenador", "cómo va el pc", "como va el pc",
            "cómo va el ordenador", "como va el ordenador", "recursos", "batería", "cpu", "memoria", "ram"
        ])
        or ("estado" in cmd and any(w in cmd for w in ["pc", "ordenador", "equipo", "máquina", "maquina", "sistema"]))
        or (("cómo está" in cmd or "como esta" in cmd or "cómo va" in cmd or "como va" in cmd) and any(w in cmd for w in ["pc", "ordenador", "equipo"]))
    ):
        response_text = get_system_status()

    # 2.1 CONSUMO DE TOKENS Y CONTROL DE COSTES
    elif any(k in cmd for k in ["tokens", "token", "cuántos tokens", "cuantos tokens", "gastar dinero", "cuesta dinero", "coste", "presupuesto"]):
        response_text = get_token_summary()

    # 2.2 FECHA Y HORA ACTUAL (MADRID)
    elif (
        any(k in cmd for k in [
            "qué día", "que dia", "qué fecha", "que fecha", "fecha de hoy", "día de hoy", "dia de hoy",
            "qué hora", "que hora", "la hora", "hora es", "tienes hora", "dime la hora", "en qué año", "en que año",
            "cuándo es", "cuando es"
        ])
        or cmd in ["día", "dia", "fecha", "hora", "hoy"]
    ):
        response_text = get_current_datetime_info(cmd)

    # 2.3 EL TIEMPO Y CLIMA EN TU ZONA (MADRID) - HOY, MAÑANA Y SEMANA
    elif any(k in cmd for k in [
        "tiempo", "el tiempo", "qué tiempo", "que tiempo", "clima", "el clima",
        "temperatura", "qué temperatura", "que temperatura", "va a llover", "lloverá", "llovera",
        "llueve", "pronóstico", "pronostico", "previsión", "prevision", "tiempo en madrid", "clima en madrid"
    ]):
        response_text = get_madrid_weather(cmd)

    # 3. BÚSQUEDA EN GOOGLE
    elif any(k in cmd for k in ["search on google", "search google for", "google", "busca en google", "buscar en google", "busca"]):
        query = cmd
        for phrase in ["search on google for", "search on google", "search google for", "google", "busca en google", "buscar en google", "busca"]:
            query = query.replace(phrase, "")
        query = query.strip()
        if query:
            msg = f"Buscando en Google: {query}" if FRIDAY_LANGUAGE == "es" else f"Searching Google for: {query}"
            if speak_aloud:
                speak(msg)
            pywhatkit.search(query)
            response_text = msg
        else:
            response_text = "¿Qué deseas que busque?" if FRIDAY_LANGUAGE == "es" else "What do you want me to search for?"

    # 4. REPRODUCIR MÚSICA EN SPOTIFY
    elif any(k in cmd for k in ["play", "pon", "ponga", "pongas", "reproduce", "reproducir", "toca", "spotify"]):
        song = cmd
        phrases_to_remove = sorted([
            "reproduce en spotify", "pon en spotify", "busca en spotify", "abrir spotify", "abre spotify", "en spotify",
            "reproduce la canción", "reproducir la canción", "pon la canción", "pon la música",
            "que ponga", "que pongas", "ponme", "ponte", "reproduce", "reproducir", "toca", "pon", "play", "spotify"
        ], key=len, reverse=True)
        for phrase in phrases_to_remove:
            song = re.sub(rf'\b{re.escape(phrase)}\b', '', song, flags=re.IGNORECASE)
        song = re.sub(r'\s+', ' ', song).strip()
        if song:
            msg = f"Reproduciendo {song} en Spotify." if FRIDAY_LANGUAGE == "es" else f"Playing {song} on Spotify."
            if speak_aloud:
                speak(msg)
            encoded = urllib.parse.quote(song)
            try:
                os.startfile(f"spotify:search:{encoded}")
            except Exception:
                try:
                    subprocess.Popen(["cmd.exe", "/c", "start", "", f"spotify:search:{encoded}"], shell=False)
                except Exception:
                    webbrowser.open(f"https://open.spotify.com/search/{encoded}")
            response_text = msg
        else:
            msg = "Abriendo Spotify." if FRIDAY_LANGUAGE == "es" else "Opening Spotify."
            if speak_aloud:
                speak(msg)
            try:
                os.startfile("spotify:")
            except Exception:
                subprocess.Popen(["cmd.exe", "/c", "start", "", "spotify:"], shell=False)
            response_text = msg

    # 5. SALIDA / APAGADO
    elif any(k in cmd for k in ["goodbye", "exit", "adiós", "salir", "apágate", "cerrar", "duérmete"]):
        response_text = "Hasta pronto, señor Álvaro. Quedo en suspensión." if FRIDAY_LANGUAGE == "es" else "Goodbye, sir. Going into standby."
        if speak_aloud:
            speak(response_text)
        exit(0)

    # 6. IDENTIDAD
    elif any(k in cmd for k in ["who am i", "quién soy", "quien soy"]):
        response_text = "Eres Álvaro Luengo, mi creador." if FRIDAY_LANGUAGE == "es" else "You are Álvaro Luengo, my creator."

    elif any(k in cmd for k in ["quién eres", "quien eres", "cómo te llamas", "como te llamas", "who are you"]):
        response_text = "Soy Friday, tu asistente personal creada por ti, Álvaro." if FRIDAY_LANGUAGE == "es" else "I am Friday, your personal assistant created by you, Álvaro."

    # 7. AGRADECIMIENTO
    elif any(k in cmd for k in ["thank you", "gracias", "muchas gracias"]):
        response_text = "De nada, siempre a tu servicio, Álvaro." if FRIDAY_LANGUAGE == "es" else "You're welcome, sir."

    # 8. MODO PODER (SPOTIFY ROCK POWER)
    elif any(k in cmd for k in ["power mode", "modo poder", "modo energía", "modo fiesta"]):
        msg = "Modo poder activado. Abriendo AC/DC en Spotify con todos los sistemas al máximo, señor." if FRIDAY_LANGUAGE == "es" else "Power mode activated. All systems optimal, sir."
        if speak_aloud:
            speak(msg)
        try:
            subprocess.Popen(["cmd.exe", "/c", "start", "", "spotify:search:ACDC%20Back%20in%20Black"], shell=False)
        except Exception:
            webbrowser.open("https://open.spotify.com/search/ACDC%20Back%20in%20Black")
        response_text = msg

    # 9. MENSAJE A MAMÁ
    elif any(k in cmd for k in ["message mom", "mensaje a mamá", "mensaje a mama", "escribe a mamá", "escribe a mama"]):
        pywhatkit.sendwhatmsg_instantly(MOM_PHONE, "Te quiero mucho")
        response_text = "Mensaje enviado a mamá." if FRIDAY_LANGUAGE == "es" else "Message sent to mom."

    # 10. LLAMADAS TELEFÓNICAS (ADB ANDROID)
    elif any(k in cmd for k in ["call", "make call to", "llama a", "marcar"]):
        number = cmd
        for p in ["make call to", "call", "llama a", "marcar al", "marcar"]:
            number = number.replace(p, "")
        number = number.strip()
        if not number:
            number = MOM_PHONE
        success = makecall(number)
        response_text = f"Marcando al {number} en tu móvil." if success else f"No se pudo completar la llamada al {number}."

    # 11. REPETICIÓN
    elif "again" in cmd or "repite" in cmd:
        response_text = command

    # 12. CONSULTA GENERAL DE IA (GOOGLE GEMINI)
    else:
        wait_msg = "Procesando..." if FRIDAY_LANGUAGE == "es" else "Processing..."
        if speak_aloud:
            speak(wait_msg)
        response_text = get_gemini_response(command)

    if speak_aloud and response_text:
        speak(response_text)

    return response_text

if __name__ == "__main__":
    print("Probando identidad de Friday...")
    print(process_command("quién eres", speak_aloud=False))