import json
import datetime
from pathlib import Path
from config import BASE_DIR

TOKEN_FILE = BASE_DIR / "token_usage.json"

def _load_data() -> dict:
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"history": {}, "total_tokens_all_time": 0}

def _save_data(data: dict):
    try:
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Aviso] No se pudo guardar token_usage.json: {e}")

def record_tokens(prompt_tokens: int, completion_tokens: int, model: str = "gemini-2.5-flash-lite"):
    """Registra el consumo exacto de tokens de una petición."""
    data = _load_data()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    total = prompt_tokens + completion_tokens
    
    if today not in data["history"]:
        data["history"][today] = {
            "requests": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "model": model
        }
        
    day_entry = data["history"][today]
    day_entry["requests"] += 1
    day_entry["prompt_tokens"] += prompt_tokens
    day_entry["completion_tokens"] += completion_tokens
    day_entry["total_tokens"] += total
    data["total_tokens_all_time"] += total

    _save_data(data)
    return total

def get_token_summary() -> str:
    """Devuelve un informe comprensible del consumo de tokens y coste."""
    data = _load_data()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    day_entry = data["history"].get(today, {
        "requests": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0
    })
    
    reqs = day_entry["requests"]
    day_tokens = day_entry["total_tokens"]
    all_time = data.get("total_tokens_all_time", 0)

    # Google AI Studio Free Tier para Gemini 2.5 Flash Lite / 2.0 Flash
    # Límite gratis: 15 peticiones por minuto, 1,500 peticiones al día
    limit_daily_requests = 1500
    remaining_requests = max(0, limit_daily_requests - reqs)

    report = (
        f"Consumo de hoy: {day_tokens} tokens en {reqs} consultas. "
        f"Te quedan {remaining_requests} peticiones gratuitas hoy. "
        "Coste: 0,00€. Estás en el plan 100% gratuito de Google AI Studio, no se cobrará nada."
    )
    return report

if __name__ == "__main__":
    print(get_token_summary())
