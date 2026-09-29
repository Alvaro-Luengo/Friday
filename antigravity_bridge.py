import subprocess
import os
import re
import json
import time
import uuid
import datetime
import threading
from typing import Generator, Dict, Any, Optional
from pathlib import Path
from config import AGY_PATH, AGY_SKIP_PERMISSIONS, BASE_DIR

AUDIT_LOG_FILE = BASE_DIR / "agy_audit.jsonl"

# Registro en memoria para aprobaciones interactivas pendientes
PENDING_APPROVALS: Dict[str, Dict[str, Any]] = {}
APPROVAL_LOCK = threading.Lock()

def clean_ansi(text: str) -> str:
    """Elimina secuencias de escape ANSI o colores de terminal."""
    if not text:
        return ""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def is_followup_question(text: str) -> bool:
    """
    Detecta si la respuesta de AGY requiere que el usuario continúe la conversación.
    """
    if not text:
        return False
    lower = text.lower().strip()
    if "?" in text or "¿" in text:
        return True

    followup_patterns = [
        "en qué te puedo ayudar",
        "en qué puedo ayudarte",
        "cómo te puedo ayudar",
        "coméntame",
        "cuéntame",
        "dime qué",
        "qué necesitas",
        "de qué se trata",
        "quieres que",
        "deseas que",
        "te gustaría",
        "indícame",
        "proporciona más",
        "necesito más información"
    ]
    return any(p in lower for p in followup_patterns)

def detect_dangerous_intent(text: str) -> Optional[str]:
    """
    Analiza si el texto o comando contiene instrucciones de borrado
    o modificación crítica que deban pedir confirmación al usuario móvil.
    """
    if not text:
        return None
    lower = text.lower()
    
    # Patrones de borrado de archivos o carpetas
    deletion_patterns = [
        (r'\b(borra|borrar|elimina|eliminar|suprime|suprimir|delete|remove|rmdir|rd|del)\b', "Eliminación de archivos o carpetas"),
        (r'\b(remove-item|drop|format|unlink|rm\s+-rf|rmdir\s+/s)\b', "Operación destructiva de comandos"),
        (r'\b(reset\s+--hard|clean\s+-fd)\b', "Reinicio forzado destructivo de Git"),
    ]
    for pattern, desc in deletion_patterns:
        if re.search(pattern, lower):
            return desc

    # Patrones de modificación de archivos críticos del núcleo de Friday
    critical_files = [".env", "config.py", "main.py", "mobile_server.py", "antigravity_bridge.py"]
    for cf in critical_files:
        if cf in lower and any(act in lower for act in ["modifica", "cambia", "sobrescribe", "reemplaza", "overwrite", "edit", "update"]):
            return f"Modificación de archivo crítico del sistema: {cf}"

    return None

def create_approval_request(action_desc: str, prompt: str) -> str:
    """Crea una solicitud de aprobación pendiente para que el móvil decida."""
    req_id = str(uuid.uuid4())[:8]
    event = threading.Event()
    with APPROVAL_LOCK:
        PENDING_APPROVALS[req_id] = {
            "req_id": req_id,
            "description": action_desc,
            "prompt": prompt,
            "status": "pending",
            "event": event,
            "created_at": datetime.datetime.now().isoformat()
        }
    return req_id

def resolve_approval_request(req_id: str, approved: bool) -> bool:
    """Resuelve una solicitud de aprobación desde la app móvil."""
    with APPROVAL_LOCK:
        req = PENDING_APPROVALS.get(req_id)
        if not req or req["status"] != "pending":
            return False
        req["status"] = "approved" if approved else "rejected"
        req["resolved_at"] = datetime.datetime.now().isoformat()
        req["event"].set()
        return True

def record_audit(entry: Dict[str, Any]):
    """Guarda un registro inmutable en el archivo de auditoría JSONL."""
    try:
        entry["timestamp"] = datetime.datetime.now().isoformat()
        line = json.dumps(entry, ensure_ascii=False) + "\n"
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception as e:
        print(f"[Aviso] No se pudo escribir en el log de auditoría: {e}")

def get_agy_audit_history(limit: int = 50) -> list:
    """Recupera el historial de operaciones de AGY ordenado de más reciente a más antiguo."""
    if not os.path.exists(AUDIT_LOG_FILE):
        return []
    records = []
    try:
        with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
                if len(records) >= limit:
                    break
            except Exception:
                continue
    except Exception as e:
        print(f"[Aviso] Error leyendo historial de AGY: {e}")
    return records

def stream_antigravity(
    prompt: str,
    skip_permissions: bool = True,
    continue_session: bool = False,
    pre_approved_id: Optional[str] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Ejecuta AGY en modo streaming (stream-json) y emite eventos en tiempo real hacia el móvil.
    Detecta operaciones críticas (borrado o modificación clave) solicitando confirmación si no fue pre-aprobado.
    """
    executable = AGY_PATH
    if not os.path.exists(executable):
        executable = "agy"

    # Verificación de seguridad de primer nivel antes de ejecutar
    dangerous_desc = detect_dangerous_intent(prompt)
    if dangerous_desc and not pre_approved_id:
        req_id = create_approval_request(dangerous_desc, prompt)
        yield {
            "type": "approval_required",
            "approval_id": req_id,
            "description": dangerous_desc,
            "prompt": prompt,
            "message": f"⚠️ ATENCIÓN: La petición solicita '{dangerous_desc}'. Se requiere autorización expresa."
        }
        # Esperar hasta 45 segundos por la respuesta del móvil
        req = PENDING_APPROVALS.get(req_id)
        approved = False
        if req:
            req["event"].wait(timeout=45)
            approved = (req["status"] == "approved")

        if not approved:
            record_audit({
                "prompt": prompt,
                "status": "REJECTED_OR_TIMEOUT",
                "reason": dangerous_desc,
                "response": "Operación cancelada: No se obtuvo confirmación de seguridad desde el móvil."
            })
            yield {
                "type": "approval_rejected",
                "message": "Operación cancelada por seguridad: Se denegó el permiso o expiró el tiempo de espera."
            }
            return

    # Preparar comando AGY
    cmd = [executable]
    if skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    if continue_session:
        cmd.append("-c")
    cmd.extend(["-p", prompt, "--output-format", "stream-json"])

    yield {
        "type": "start",
        "prompt": prompt,
        "skip_permissions": skip_permissions,
        "continue_session": continue_session,
        "timestamp": datetime.datetime.now().isoformat()
    }

    audit_entry = {
        "prompt": prompt,
        "skip_permissions": skip_permissions,
        "continue_session": continue_session,
        "tools_called": [],
        "response": "",
        "status": "RUNNING"
    }

    full_response = []
    
    try:
        use_shell = not os.path.exists(executable)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=use_shell,
            cwd=str(BASE_DIR)
        )

        for line in process.stdout:
            line_str = line.strip()
            if not line_str:
                continue

            try:
                data = json.loads(line_str)
                event_type = data.get("event")

                if event_type == "init":
                    init_data = data.get("init", {})
                    conv_id = data.get("conversation_id", "")
                    audit_entry["conversation_id"] = conv_id
                    yield {
                        "type": "init",
                        "conversation_id": conv_id,
                        "cwd": init_data.get("cwd", "")
                    }

                elif event_type == "step_update":
                    step = data.get("step_update", {})
                    delta = step.get("text_delta")
                    if delta:
                        full_response.append(delta)
                        yield {
                            "type": "text_delta",
                            "delta": delta
                        }

                    # Detectar si una herramienta se está invocando
                    tool_call = step.get("tool_call") or step.get("tool")
                    if tool_call:
                        tool_info = {
                            "name": tool_call if isinstance(tool_call, str) else tool_call.get("name", "tool"),
                            "summary": step.get("summary", ""),
                            "action": step.get("action", "")
                        }
                        audit_entry["tools_called"].append(tool_info)
                        yield {
                            "type": "tool_call",
                            "tool": tool_info
                        }

                elif event_type == "result":
                    res = data.get("result", {})
                    res_text = res.get("response", "")
                    if res_text:
                        full_response = [res_text]
                    usage = res.get("usage", {})
                    audit_entry["status"] = res.get("status", "SUCCESS")
                    audit_entry["usage"] = usage
                    audit_entry["duration_seconds"] = res.get("duration_seconds", 0)
                    yield {
                        "type": "result",
                        "status": res.get("status", "SUCCESS"),
                        "response": clean_ansi(res_text),
                        "usage": usage,
                        "duration_seconds": res.get("duration_seconds", 0)
                    }

            except json.JSONDecodeError:
                # Salida no JSON (texto crudo de stdout)
                cleaned = clean_ansi(line_str)
                full_response.append(cleaned + "\n")
                yield {
                    "type": "text_delta",
                    "delta": cleaned + "\n"
                }

        process.wait()

        # Comprobar stderr
        stderr_output = process.stderr.read()
        if stderr_output and process.returncode != 0:
            err_clean = clean_ansi(stderr_output).strip()
            audit_entry["status"] = "ERROR"
            audit_entry["error"] = err_clean
            yield {
                "type": "error",
                "message": err_clean
            }
        else:
            audit_entry["status"] = "COMPLETED"

    except Exception as e:
        audit_entry["status"] = "EXCEPTION"
        audit_entry["error"] = str(e)
        yield {
            "type": "error",
            "message": f"Error ejecutando Antigravity: {str(e)}"
        }

    finally:
        final_text = clean_ansi("".join(full_response)).strip()
        audit_entry["response"] = final_text
        record_audit(audit_entry)
        yield {
            "type": "done",
            "final_response": final_text
        }

def ask_antigravity(prompt: str, continue_session: bool = False, timeout: int = 90) -> str:
    """
    Función de compatibilidad directa síncrona.
    Ejecuta AGY y devuelve la respuesta de texto completa.
    """
    last_response = ""
    for event in stream_antigravity(prompt, skip_permissions=AGY_SKIP_PERMISSIONS, continue_session=continue_session):
        if event.get("type") == "result":
            last_response = event.get("response", "")
        elif event.get("type") == "done" and not last_response:
            last_response = event.get("final_response", "")
        elif event.get("type") == "error":
            return f"Error de Antigravity: {event.get('message')}"
        elif event.get("type") == "approval_rejected":
            return f"Cancelado: {event.get('message')}"
            
    return last_response or "Antigravity procesó la solicitud con éxito."

if __name__ == "__main__":
    print("Probando streaming de Antigravity...")
    for ev in stream_antigravity("Di 'Conexión con Jarvis establecida correctamente' en una frase"):
        print(f"[{ev['type']}] {ev}")
