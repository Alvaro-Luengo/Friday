import sys
import psutil
from pathlib import Path
from config import LOG_FILE, URL_FILE

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def show_status():
    print("=" * 60)
    print("             ESTADO DEL ASISTENTE FRIDAY")
    print("=" * 60)
    
    found = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = " ".join(proc.info.get('cmdline') or []).lower()
            if "main.py" in cmd:
                print(f"[+] Friday está ACTIVO en segundo plano (PID: {proc.info['pid']})")
                found = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if not found:
        print("[-] Friday NO está ejecutándose en este momento.")

    print()
    if URL_FILE.exists():
        url = URL_FILE.read_text(encoding="utf-8").strip()
        is_temp = "trycloudflare.com" in url
        tipo = "⚠️ TEMPORAL (cambia al reiniciar)" if is_temp else "🔒 FIJO PERMANENTE"
        print(f"[+] Enlace Remoto HTTPS Actual ({tipo}):\n    👉 {url}")
        if is_temp:
            print("    [!] Para configurar un Link Fijo permanente, ejecuta setup_fixed_link.py")
    else:
        print("[-] No hay túnel remoto activo actualmente.")

    print("\n--- Últimas líneas de registro (friday.log) ---")
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text(encoding="utf-8").strip().splitlines()
        for l in lines[-6:]:
            print("  ", l)
    else:
        print("  (Sin registros aún)")

    print("=" * 60)

if __name__ == "__main__":
    show_status()
