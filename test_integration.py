import requests
import time
import subprocess
import sys
import json

# Asegurar utf-8
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def test_friday_full_integration():
    print("Iniciando servidor de Friday para pruebas de integración...")
    # Ejecutar sin túnel remoto durante tests locales
    env = dict(sys.modules['os'].environ)
    env["ENABLE_REMOTE_TUNNEL"] = "false"
    
    proc = subprocess.Popen([sys.executable, "mobile_server.py"], cwd=r"D:\Friday", env=env)
    time.sleep(2.5)

    headers = {"X-Friday-PIN": "1234", "X-Jarvis-PIN": "1234"}

    try:
        # 1. Probar PIN erróneo
        r_bad_pin = requests.post("http://localhost:5000/api/verify_pin", json={"pin": "9999"}, timeout=5)
        print("Test 1 (PIN erróneo):", r_bad_pin.status_code, "(esperado 401)")
        assert r_bad_pin.status_code == 401

        # 2. Probar PIN correcto
        r_good_pin = requests.post("http://localhost:5000/api/verify_pin", json={"pin": "1234"}, timeout=5)
        print("Test 2 (PIN correcto):", r_good_pin.status_code, "(esperado 200)")
        assert r_good_pin.status_code == 200

        # 3. Probar Estado del PC con métricas
        r_status = requests.get("http://localhost:5000/api/status", headers=headers, timeout=5)
        print("Test 3 (Estado PC y métricas):", r_status.status_code, r_status.json().get("metrics", {}).get("status"))
        assert r_status.status_code == 200
        assert r_status.json()["metrics"]["status"] == "online"

        # 4. Probar Descarga de APK nativo de Friday
        r_apk = requests.get("http://localhost:5000/download/friday.apk", timeout=5, stream=True)
        print("Test 4 (Descarga Friday.apk):", r_apk.status_code, f"Tamaño: {len(r_apk.content)} bytes")
        assert r_apk.status_code == 200
        assert len(r_apk.content) > 1000000 # Mayor a 1 MB

        # 5. Probar Meteorología 7 días
        r_weather = requests.get("http://localhost:5000/api/weather", headers=headers, timeout=10)
        print("Test 5 (Meteorología Madrid y 7 días):", r_weather.status_code, "Ciudad:", r_weather.json().get("city"), "Días previsión:", len(r_weather.json().get("forecast", [])))
        assert r_weather.status_code == 200
        assert len(r_weather.json().get("forecast", [])) >= 5

        # 6. Probar Historial de Auditoría de AGY
        r_history = requests.get("http://localhost:5000/api/agy/history", headers=headers, timeout=5)
        print("Test 6 (Historial AGY):", r_history.status_code, "Registros:", r_history.json().get("total"))
        assert r_history.status_code == 200

        # 7. Probar Streaming de Antigravity (AGY) con skip permissions
        print("Test 7 (Streaming AGY)...")
        r_stream = requests.post(
            "http://localhost:5000/api/agy/stream",
            headers=headers,
            json={"prompt": "Di 'Test AGY completado' en 3 palabras", "skip_permissions": True},
            stream=True,
            timeout=25
        )
        assert r_stream.status_code == 200
        received_chunks = 0
        for line in r_stream.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                if decoded.startswith("data:"):
                    received_chunks += 1
        print(f"Test 7 (Streaming AGY completado, {received_chunks} eventos recibidos)")
        assert received_chunks > 0

        print("\n" + "="*60)
        print("  [OK] TODAS LAS PRUEBAS DE INTEGRACION PASARON CON EXITO.")
        print("="*60 + "\n")

    finally:
        proc.terminate()
        proc.wait()
        print("Servidor de pruebas detenido.")

if __name__ == "__main__":
    test_friday_full_integration()
