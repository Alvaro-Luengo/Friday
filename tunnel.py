import subprocess
import threading
import re
import os
import sys
import time
from pathlib import Path
from config import (
    BASE_DIR,
    LOG_FILE,
    URL_FILE,
    CLOUDFLARE_TUNNEL_TOKEN,
    NGROK_AUTHTOKEN,
    NGROK_DOMAIN,
    FIXED_REMOTE_URL,
    TUNNEL_PROVIDER
)

CLOUDFLARED_BIN = BASE_DIR / "cloudflared.exe"
NGROK_BIN = BASE_DIR / "ngrok.exe"

class RemoteTunnel:
    def __init__(self, port: int = 5000):
        self.port = port
        self.process = None
        self.public_url = None
        self.is_fixed = False
        self.provider_name = "desconocido"
        self._stop_event = threading.Event()

    def start(self, timeout: int = 25) -> str:
        """Inicia el túnel según la configuración activa (Link fijo Cloudflare/Ngrok o Temporal)."""
        # 1. Modo Personalizado (Custom URL / IP Fija / Port Forwarding existente)
        if TUNNEL_PROVIDER == "custom" and FIXED_REMOTE_URL:
            self.public_url = FIXED_REMOTE_URL
            self.is_fixed = True
            self.provider_name = "Personalizado (Link Fijo)"
            self._save_url(self.public_url)
            return self.public_url

        # 2. Modo Cloudflare Zero Trust (Túnel con Token Permanente)
        if CLOUDFLARE_TUNNEL_TOKEN and (TUNNEL_PROVIDER in ("auto", "cloudflare")):
            return self._start_cloudflare_named_tunnel(timeout=timeout)

        # 3. Modo Ngrok (con Dominio Estático Gratuito o estándar)
        if NGROK_AUTHTOKEN and (TUNNEL_PROVIDER in ("auto", "ngrok")):
            return self._start_ngrok_tunnel(timeout=timeout)

        # 4. Modo Quick Tunnel Temporal de Cloudflare (Fallback cuando no hay tokens configurados)
        return self._start_cloudflare_quick_tunnel(timeout=timeout)

    def _start_cloudflare_named_tunnel(self, timeout: int = 25) -> str:
        """Inicia Cloudflare Tunnel persistente usando Token (Zero Trust)."""
        if not CLOUDFLARED_BIN.exists():
            print("[-] No se encontró cloudflared.exe en", CLOUDFLARED_BIN)
            return ""

        self.provider_name = "Cloudflare Named Tunnel (Link Fijo)"
        self.is_fixed = True

        cmd = [
            str(CLOUDFLARED_BIN),
            "tunnel",
            "run",
            "--token", CLOUDFLARE_TUNNEL_TOKEN
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        ready_event = threading.Event()

        def reader():
            # Patrones de conexión exitosa de cloudflared
            success_patterns = [
                re.compile(r'registered connIndex', re.IGNORECASE),
                re.compile(r'Registered tunnel connection', re.IGNORECASE),
                re.compile(r'Connection .* registered', re.IGNORECASE),
                re.compile(r'Starting tunnel tunnelID=', re.IGNORECASE)
            ]
            for line in self.process.stderr:
                if self._stop_event.is_set():
                    break
                for pat in success_patterns:
                    if pat.search(line):
                        ready_event.set()
                        break

        t = threading.Thread(target=reader, daemon=True)
        t.start()

        # Si el usuario configuró FIXED_REMOTE_URL (ej: https://jarvis.midominio.com), usamos esa
        self.public_url = FIXED_REMOTE_URL if FIXED_REMOTE_URL else "https://(túnel cloudflare activo)"
        self._save_url(self.public_url)

        if ready_event.wait(timeout=timeout):
            return self.public_url

        # Si expiró el timeout pero el proceso sigue vivo, asumimos que sigue conectando
        if self.process.poll() is None:
            return self.public_url

        print("[-] Error: El túnel Cloudflare con token finalizó inesperadamente.")
        return ""

    def _start_ngrok_tunnel(self, timeout: int = 25) -> str:
        """Inicia Ngrok usando dominio estático o dinámico."""
        if not NGROK_BIN.exists():
            print("[-] No se encontró ngrok.exe en", NGROK_BIN)
            return ""

        self.provider_name = "Ngrok"
        cmd = [
            str(NGROK_BIN),
            "http",
            str(self.port),
            "--authtoken", NGROK_AUTHTOKEN,
            "--log", "stdout",
            "--log-format", "json"
        ]

        # Si hay un dominio estático configurado
        target_domain = NGROK_DOMAIN or FIXED_REMOTE_URL
        if target_domain:
            self.is_fixed = True
            self.provider_name = "Ngrok Dominio Estático (Link Fijo)"
            domain_clean = target_domain.strip()
            if not domain_clean.startswith("http://") and not domain_clean.startswith("https://"):
                domain_clean = f"https://{domain_clean}"
            cmd.extend(["--url", domain_clean])
        else:
            self.is_fixed = False

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        ready_event = threading.Event()
        url_regex = re.compile(r'("url":\s*"|url=)(https://[^\s",]+)')

        def reader():
            for line in self.process.stdout:
                if self._stop_event.is_set():
                    break
                match = url_regex.search(line)
                if match and not self.public_url:
                    self.public_url = match.group(2)
                    self._save_url(self.public_url)
                    ready_event.set()
                elif "err=" in line and "authentication failed" in line:
                    print(f"[-] Error de autenticación en Ngrok: {line.strip()}")

        t = threading.Thread(target=reader, daemon=True)
        t.start()

        if ready_event.wait(timeout=timeout):
            return self.public_url

        # Fallback a target_domain si se especificó y el proceso no ha muerto
        if target_domain and self.process.poll() is None:
            self.public_url = target_domain
            self._save_url(self.public_url)
            return self.public_url

        return ""

    def _start_cloudflare_quick_tunnel(self, timeout: int = 25) -> str:
        """Inicia túnel temporal trycloudflare.com (genera URL aleatoria)."""
        if not CLOUDFLARED_BIN.exists():
            print("[-] No se encontró cloudflared.exe para túnel remoto.")
            return ""

        self.provider_name = "Cloudflare Quick Tunnel (Temporal)"
        self.is_fixed = False

        cmd = [
            str(CLOUDFLARED_BIN),
            "tunnel",
            "--url", f"http://127.0.0.1:{self.port}",
            "--no-autoupdate"
        ]

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        url_found_event = threading.Event()

        def reader():
            url_regex = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')
            for line in self.process.stderr:
                if self._stop_event.is_set():
                    break
                match = url_regex.search(line)
                if match and not self.public_url:
                    self.public_url = match.group(0)
                    self._save_url(self.public_url)
                    url_found_event.set()

        t = threading.Thread(target=reader, daemon=True)
        t.start()

        if url_found_event.wait(timeout=timeout):
            return self.public_url
        return ""

    def _save_url(self, url: str):
        try:
            with open(URL_FILE, "w", encoding="utf-8") as f:
                f.write(url)
        except Exception:
            pass

    def stop(self):
        """Detiene el túnel."""
        self._stop_event.set()
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

        try:
            if URL_FILE.exists():
                URL_FILE.unlink()
        except Exception:
            pass

# Compatibilidad con código previo que importa CloudflareTunnel
CloudflareTunnel = RemoteTunnel

if __name__ == "__main__":
    tunnel = RemoteTunnel(5000)
    print("Iniciando túnel de prueba...")
    url = tunnel.start()
    if url:
        print(f"\n[+] TÚNEL ACTIVO ({tunnel.provider_name}): {url}")
        print(f"    ¿Es link fijo?: {'SÍ (Permanente)' if tunnel.is_fixed else 'NO (Temporal)'}")
        print("Manteniendo 10 segundos...")
        time.sleep(10)
    tunnel.stop()
    print("Túnel cerrado.")
