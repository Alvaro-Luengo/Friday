import os
import sys
import re
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
URL_FILE = BASE_DIR / "current_url.txt"

def load_env_dict():
    env_dict = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env_dict[k.strip()] = v.strip()
    return env_dict

def update_env_keys(updates: dict):
    lines = []
    existing_keys = set()
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k, _ = stripped.split("=", 1)
            k = k.strip()
            if k in updates:
                new_lines.append(f"{k}={updates[k]}")
                existing_keys.add(k)
                continue
        new_lines.append(line)

    # Añadir claves que no existían previamente
    for k, v in updates.items():
        if k not in existing_keys:
            new_lines.append(f"{k}={v}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"[OK] Archivo .env actualizado correctamente.")

def test_ngrok(token: str, domain: str):
    print("\n[*] Probando conexión de Ngrok...")
    ngrok_bin = BASE_DIR / "ngrok.exe"
    if not ngrok_bin.exists():
        print("[-] No se encontró ngrok.exe en", ngrok_bin)
        return False

    clean_domain = domain.strip()
    if not clean_domain.startswith("http://") and not clean_domain.startswith("https://"):
        clean_domain = f"https://{clean_domain}"

    cmd = [
        str(ngrok_bin),
        "http", "5000",
        "--authtoken", token.strip(),
        "--url", clean_domain,
        "--log", "stdout",
        "--log-format", "json"
    ]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
        time.sleep(3)
        poll = proc.poll()
        if poll is not None:
            stdout, _ = proc.communicate()
            print("[-] Error iniciando prueba de Ngrok. Salida:")
            for line in stdout.splitlines()[-5:]:
                print("   ", line)
            return False
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
        print("[+] ¡Prueba de Ngrok exitosa!")
        return True
    except Exception as e:
        print(f"[-] Error en prueba: {e}")
        return False

def test_cloudflare(token: str):
    print("\n[*] Probando token de Cloudflare...")
    cf_bin = BASE_DIR / "cloudflared.exe"
    if not cf_bin.exists():
        print("[-] No se encontró cloudflared.exe en", cf_bin)
        return False

    cmd = [str(cf_bin), "tunnel", "run", "--token", token.strip()]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        time.sleep(4)
        if proc.poll() is not None:
            _, stderr = proc.communicate()
            print("[-] Error probando token de Cloudflare:")
            for line in stderr.splitlines()[-4:]:
                print("   ", line)
            return False
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
        print("[+] ¡Prueba de Cloudflare exitosa!")
        return True
    except Exception as e:
        print(f"[-] Error en prueba: {e}")
        return False

def restart_friday_service():
    print("\n[*] Reiniciando Friday para activar el nuevo enlace...")
    stop_script = BASE_DIR / "stop_friday.py"
    if stop_script.exists():
        subprocess.run([sys.executable, str(stop_script)])

    time.sleep(2)
    start_vbs = BASE_DIR / "start_hidden.vbs"
    if start_vbs.exists():
        os.system(f'wscript "{start_vbs}"')
        print("[+] Friday iniciado en segundo plano.")
    else:
        print("[i] Inicia Friday manualmente ejecutando start_visible.bat")

    print("[*] Esperando a que el enlace se registre en el sistema...")
    for _ in range(12):
        time.sleep(1)
        if URL_FILE.exists():
            url = URL_FILE.read_text(encoding="utf-8").strip()
            if url and not url.startswith("https://(túnel"):
                print("\n" + "="*65)
                print("🎉 ¡ENLACE FIJO ACTIVO Y LISTO PARA TU MÓVIL! 🎉")
                print(f"👉 {url}")
                print("="*65)
                print("Puedes abrir este enlace en tu POCO X8 Pro Max e instalarlo.")
                print("¡Este enlace NUNCA volverá a cambiar al reiniciar el PC!")
                print("="*65 + "\n")
                return

    print("[i] El servicio está arrancando. Puedes comprobar el enlace con: python friday_status.py")

def main():
    print("=" * 65)
    print("       CONFIGURADOR DE ENLACE FIJO PERMANENTE PARA JARVIS/FRIDAY")
    print("=" * 65)
    print("Actualmente los enlaces temporales (trycloudflare.com) cambian cada")
    print("vez que reinicias el PC. Este asistente te permite configurar un")
    print("LINK FIJO que nunca cambiará.\n")

    print("Selecciona tu opción preferida:")
    print("  [1] NGROK (Recomendado si NO tienes dominio propio):")
    print("      * 100% Gratuito y permanente para siempre.")
    print("      * Ngrok te regala 1 dominio estático (ej: tu-nombre.ngrok-free.app).")
    print("      * NO tienes que pagar nada ni comprar ningún dominio.")
    print()
    print("  [2] CLOUDFLARE ZERO TRUST (Recomendado si YA TIENES dominio propio):")
    print("      * Requiere un dominio propio configurado en Cloudflare.")
    print("      * Utiliza tu propio subdominio (ej: jarvis.midominio.com).")
    print("      * Cero pantallas intermedias, conexión ultra directa.")
    print()
    print("  [3] URL PERSONALIZADA / DDNS PROPIO (DuckDNS / IP fija con puertos):")
    print("      * Si ya tienes tu router configurado con DDNS o IP fija.")
    print()
    print("  [4] RESTAURAR A LINK TEMPORAL (trycloudflare por defecto)")
    print("  [0] Salir sin hacer cambios")
    print("=" * 65)

    choice = input("\nElige una opción (1-4, 0): ").strip()

    if choice == "1":
        print("\n" + "-"*60)
        print("CONFIGURACIÓN DE NGROK (DOMINIO ESTÁTICO GRATUITO)")
        print("-"*60)
        print("1. Inicia sesión o regístrate gratis en: https://dashboard.ngrok.com")
        print("2. En el menú de la izquierda, entra en 'Cloud Edge' -> 'Domains'.")
        print("   Pulsa 'Create Domain' (te dará uno gratis tipo 'xxx.ngrok-free.app').")
        print("3. En el menú izquierdo, entra en 'Getting Started' -> 'Your Authtoken'.")
        print("-"*60)

        domain = input("\nPega tu dominio estático de Ngrok (ej: mi-jarvis.ngrok-free.app): ").strip()
        token = input("Pega tu Authtoken de Ngrok: ").strip()

        if not domain or not token:
            print("[-] Dominio o token vacíos. Operación cancelada.")
            return

        if test_ngrok(token, domain):
            clean_domain = domain if domain.startswith("http") else f"https://{domain}"
            updates = {
                "TUNNEL_PROVIDER": "ngrok",
                "NGROK_AUTHTOKEN": token,
                "NGROK_DOMAIN": clean_domain,
                "FIXED_REMOTE_URL": clean_domain
            }
            update_env_keys(updates)
            apply_now = input("\n¿Deseas reiniciar Friday ahora para activar este enlace fijo? (s/n): ").strip().lower()
            if apply_now in ("s", "si", "y", "yes"):
                restart_friday_service()

    elif choice == "2":
        print("\n" + "-"*60)
        print("CONFIGURACIÓN DE CLOUDFLARE ZERO TRUST TUNNEL")
        print("-"*60)
        print("1. Entra en https://one.dash.cloudflare.com -> Networks -> Tunnels.")
        print("2. Pulsa 'Add a tunnel' -> Selecciona 'Cloudflared' -> Nómbralo 'Friday'.")
        print("3. Copia el TOKEN largo que aparece en el comando de instalación.")
        print("4. En la pestaña 'Public Hostnames', añade tu subdominio (ej: jarvis.midominio.com)")
        print("   apuntando a: Type=HTTP, URL=localhost:5000")
        print("-"*60)

        token = input("\nPega el Token del túnel de Cloudflare: ").strip()
        fixed_url = input("Pega la URL completa de tu subdominio (ej: https://jarvis.midominio.com): ").strip()

        if not token:
            print("[-] Token vacío. Operación cancelada.")
            return

        if not fixed_url.startswith("http://") and not fixed_url.startswith("https://"):
            fixed_url = f"https://{fixed_url}"

        if test_cloudflare(token):
            updates = {
                "TUNNEL_PROVIDER": "cloudflare",
                "CLOUDFLARE_TUNNEL_TOKEN": token,
                "FIXED_REMOTE_URL": fixed_url
            }
            update_env_keys(updates)
            apply_now = input("\n¿Deseas reiniciar Friday ahora para activar este enlace fijo? (s/n): ").strip().lower()
            if apply_now in ("s", "si", "y", "yes"):
                restart_friday_service()

    elif choice == "3":
        print("\n" + "-"*60)
        print("CONFIGURACIÓN DE URL PERSONALIZADA")
        print("-"*60)
        custom_url = input("Introduce tu URL fija (ej: https://mi-jarvis.duckdns.org:5000): ").strip()
        if not custom_url:
            print("[-] URL vacía. Operación cancelada.")
            return
        if not custom_url.startswith("http://") and not custom_url.startswith("https://"):
            custom_url = f"https://{custom_url}"
        updates = {
            "TUNNEL_PROVIDER": "custom",
            "FIXED_REMOTE_URL": custom_url
        }
        update_env_keys(updates)
        apply_now = input("\n¿Deseas reiniciar Friday ahora? (s/n): ").strip().lower()
        if apply_now in ("s", "si", "y", "yes"):
            restart_friday_service()

    elif choice == "4":
        print("\n[*] Restaurando a Quick Tunnel temporal...")
        updates = {
            "TUNNEL_PROVIDER": "auto",
            "CLOUDFLARE_TUNNEL_TOKEN": "",
            "NGROK_AUTHTOKEN": "",
            "NGROK_DOMAIN": "",
            "FIXED_REMOTE_URL": ""
        }
        update_env_keys(updates)
        apply_now = input("\n¿Deseas reiniciar Friday ahora? (s/n): ").strip().lower()
        if apply_now in ("s", "si", "y", "yes"):
            restart_friday_service()

    else:
        print("\nOperación finalizada sin cambios.")

if __name__ == "__main__":
    main()
