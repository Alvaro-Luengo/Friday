import subprocess
import sys
import psutil

def stop_friday():
    print("[*] Buscando y deteniendo procesos de Friday...")
    stopped_count = 0

    # Detener python/pythonw que ejecuten main.py o mobile_server.py
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline') or []
            cmd_str = " ".join(cmdline).lower()
            if "main.py" in cmd_str or "mobile_server.py" in cmd_str:
                print(f" -> Deteniendo proceso Friday (PID: {proc.info['pid']})")
                proc.terminate()
                stopped_count += 1
            elif proc.info.get('name', '').lower() in ("cloudflared.exe", "ngrok.exe"):
                proc_name = proc.info.get('name')
                print(f" -> Deteniendo túnel {proc_name} (PID: {proc.info['pid']})")
                proc.terminate()
                stopped_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if stopped_count > 0:
        print(f"[OK] {stopped_count} procesos de Friday detenidos correctamente.")
    else:
        print("[i] No se encontraron procesos activos de Friday.")

if __name__ == "__main__":
    stop_friday()
