import sys
import socket
import threading
import json
import os
from pathlib import Path

# Asegurar codificación utf-8 en Windows para evitar errores con caracteres especiales
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from flask import Flask, request, jsonify, render_template, Response, send_file
from flask_cors import CORS
from functools import wraps
from commands import (
    process_command,
    get_system_status,
    get_system_status_data,
    get_madrid_weather_data
)
from antigravity_bridge import (
    stream_antigravity,
    resolve_approval_request,
    get_agy_audit_history
)
from config import (
    MOBILE_SERVER_HOST,
    MOBILE_SERVER_PORT,
    JARVIS_PIN,
    ENABLE_REMOTE_TUNNEL,
    BASE_DIR
)
from tunnel import CloudflareTunnel

app = Flask(__name__, template_folder="templates")
CORS(app)

current_tunnel = None

def get_local_ip():
    """Detecta la IP local de la máquina en la red local."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip

def require_pin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not JARVIS_PIN:
            return f(*args, **kwargs)

        # Buscar PIN en headers, query params o JSON body
        pin = request.headers.get("X-Jarvis-PIN") or request.headers.get("X-Friday-PIN")
        if not pin:
            pin = request.args.get("pin")
        if not pin and request.is_json:
            data = request.get_json(silent=True) or {}
            pin = data.get("pin")

        if str(pin) != str(JARVIS_PIN):
            return jsonify({"error": "PIN de seguridad incorrecto o ausente"}), 401
            
        return f(*args, **kwargs)
    return decorated_function

def find_friday_apk_path():
    """Localiza el archivo APK compilado para su descarga directa."""
    candidates = [
        BASE_DIR / "Friday.apk",
        BASE_DIR / "android_app" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk",
        BASE_DIR / "android_app" / "app" / "build" / "outputs" / "apk" / "release" / "app-release.apk",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/verify_pin", methods=["POST"])
def api_verify_pin():
    data = request.get_json(force=True, silent=True) or {}
    pin = data.get("pin", "")
    if not JARVIS_PIN or str(pin) == str(JARVIS_PIN):
        return jsonify({"valid": True})
    return jsonify({"valid": False, "error": "PIN incorrecto"}), 401

@app.route("/api/command", methods=["POST"])
@require_pin
def api_command():
    data = request.get_json(force=True, silent=True) or {}
    command_text = data.get("command", "").strip()
    speak_pc = data.get("speak_pc", True)

    if not command_text:
        return jsonify({"error": "Comando vacío"}), 400

    try:
        response_text = process_command(command_text, speak_aloud=speak_pc)
        return jsonify({
            "command": command_text,
            "response": response_text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/status", methods=["GET"])
@require_pin
def api_status():
    status = get_system_status()
    metrics = get_system_status_data()
    return jsonify({"status": status, "metrics": metrics})

@app.route("/api/weather", methods=["GET"])
@require_pin
def api_weather():
    data = get_madrid_weather_data()
    return jsonify(data)

@app.route("/api/agy/stream", methods=["GET", "POST"])
@require_pin
def api_agy_stream():
    """
    Endpoint SSE (Server-Sent Events) para transmitir la ejecución
    en vivo de Antigravity (AGY) al teléfono móvil con auto-skip-permissions
    y avisos de confirmación en tiempo real.
    """
    if request.method == "POST":
        payload = request.get_json(force=True, silent=True) or {}
        prompt = payload.get("prompt", "").strip()
        skip_permissions = payload.get("skip_permissions", True)
        continue_session = payload.get("continue_session", False)
        approval_id = payload.get("approval_id")
    else:
        prompt = request.args.get("prompt", "").strip()
        skip_permissions = request.args.get("skip_permissions", "true").lower() in ("true", "1")
        continue_session = request.args.get("continue_session", "false").lower() in ("true", "1")
        approval_id = request.args.get("approval_id")

    if not prompt:
        return jsonify({"error": "El parámetro 'prompt' es requerido"}), 400

    def generate_sse():
        try:
            for event in stream_antigravity(
                prompt=prompt,
                skip_permissions=skip_permissions,
                continue_session=continue_session,
                pre_approved_id=approval_id
            ):
                payload_str = json.dumps(event, ensure_ascii=False)
                yield f"data: {payload_str}\n\n"
        except Exception as e:
            err = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(err, ensure_ascii=False)}\n\n"

    return Response(
        generate_sse(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive"
        }
    )

@app.route("/api/agy/approve", methods=["POST"])
@require_pin
def api_agy_approve():
    """Aprueba o cancela una operación potencialmente peligrosa desde el móvil."""
    data = request.get_json(force=True, silent=True) or {}
    req_id = data.get("approval_id", "").strip()
    approved = bool(data.get("approved", False))

    if not req_id:
        return jsonify({"error": "Falta el 'approval_id'"}), 400

    success = resolve_approval_request(req_id, approved)
    return jsonify({
        "success": success,
        "approval_id": req_id,
        "approved": approved,
        "message": "Aprobación procesada" if success else "Solicitud no encontrada o ya resuelta"
    })

@app.route("/api/agy/history", methods=["GET"])
@require_pin
def api_agy_history():
    """Devuelve el historial auditado de todas las peticiones a Antigravity."""
    limit = int(request.args.get("limit", 50))
    history = get_agy_audit_history(limit=limit)
    return jsonify({"history": history, "total": len(history)})

@app.route("/download/friday.apk", methods=["GET"])
@app.route("/download", methods=["GET"])
@app.route("/api/download_apk", methods=["GET"])
def download_apk():
    """Permite descargar el APK nativo de Friday directamente al móvil."""
    apk_file = find_friday_apk_path()
    if not apk_file or not apk_file.exists():
        return jsonify({
            "error": "El instalador APK aún no ha sido compilado en el servidor.",
            "instructions": "Compila el APK con el script build_apk.bat o revisa android_app."
        }), 404

    return send_file(
        str(apk_file),
        as_attachment=True,
        download_name="Friday.apk",
        mimetype="application/vnd.android.package-archive"
    )

def launch_tunnel_async(port: int):
    """Lanza el túnel seguro en segundo plano sin retrasar el inicio de Flask."""
    global current_tunnel
    current_tunnel = CloudflareTunnel(port)
    url = current_tunnel.start(timeout=25)
    if url:
        print("\n" + "*"*65)
        print("  [+] ENLACE REMOTO FUERA DE CASA ACTIVO (4G/5G):")
        print(f"  👉 {url}")
        if getattr(current_tunnel, 'is_fixed', False):
            print("  🔒 LINK FIJO PERMANENTE ACTIVO (Nunca cambia)")
        else:
            print("  ⚠️ AVISO: LINK TEMPORAL (Cambia si se reinicia)")
            print("     Para un link fijo permanente para siempre,")
            print("     ejecuta: python setup_fixed_link.py")
        print("  (Abre este enlace desde tu móvil POCO en cualquier lugar)")
        print("*"*65 + "\n")
    else:
        print("\n[-] No se pudo abrir el túnel para acceso remoto.")

def start_mobile_server(host=MOBILE_SERVER_HOST, port=MOBILE_SERVER_PORT, enable_tunnel=ENABLE_REMOTE_TUNNEL, debug=False):
    ip = get_local_ip()

    print("\n" + "="*65)
    print("         SERVIDOR MOVIL DE FRIDAY ACTIVO (AGY V2.0)")
    print("="*65)
    print(f"  * Enlace Local (PC):         http://localhost:{port}")
    print(f"  * Enlace Mismo Wi-Fi:        http://{ip}:{port}")
    if enable_tunnel:
        print("  * Enlace Fuera de Casa:      Conectando túnel seguro...")
        t = threading.Thread(target=launch_tunnel_async, args=(port,), daemon=True)
        t.start()
    else:
        print("  * Enlace Fuera de Casa:      Desactivado (ENABLE_REMOTE_TUNNEL=false)")
    print(f"  * Descarga Directa APK:      http://{ip}:{port}/download/friday.apk")
    print(f"  * PIN de Seguridad:          {JARVIS_PIN}")
    print("="*65 + "\n")

    try:
        app.run(host=host, port=port, debug=debug, use_reloader=False)
    finally:
        if current_tunnel:
            current_tunnel.stop()

if __name__ == "__main__":
    start_mobile_server()
