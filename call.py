import re
from ppadb.client import Client as AdbClient

def sanitize_phone_number(number: str) -> str:
    """Valida y limpia el número de teléfono para evitar inyección en shell."""
    clean = re.sub(r'[\s\-()]', '', number.strip())
    # Debe ser una secuencia de dígitos opcionalmente empezando por '+'
    if re.fullmatch(r'^\+?[0-9]{3,15}$', clean):
        return clean
    return ""

def get_adb_client(host: str = "127.0.0.1", port: int = 5037):
    """Obtiene una conexión con el cliente ADB."""
    try:
        return AdbClient(host=host, port=port)
    except Exception as e:
        print(f"❌ Error al conectar con el servidor ADB: {e}")
        return None

def connect_wireless_device(ip_address: str, port: int = 5555):
    """Permite conectar el móvil por Wi-Fi mediante ADB sin cables."""
    client = get_adb_client()
    if not client:
        return False
    try:
        result = client.remote_connect(ip_address, port)
        print(f"📡 Conexión inalámbrica con {ip_address}:{port} -> {result}")
        return result
    except Exception as e:
        print(f"❌ Error al conectar inalámbricamente: {e}")
        return False

def makecall(numero_destino: str):
    """Inicia una llamada telefónica en el móvil Android conectado."""
    safe_number = sanitize_phone_number(numero_destino)
    if not safe_number:
        print(f"❌ Número de teléfono inválido o potencialmente inseguro: {numero_destino}")
        return False

    client = get_adb_client()
    if not client:
        return False

    try:
        devices = client.devices()
        if not devices:
            print("❌ No se detectó ningún dispositivo móvil. Conecta tu móvil por USB (o Wi-Fi) con depuración ADB activada.")
            return False

        device = devices[0]
        print(f"✅ Conectado a dispositivo: {device.serial}")
        print(f"📞 Marcando al {safe_number}...")
        
        # 'ACTION_CALL' inicia la llamada en Android
        device.shell(f"am start -a android.intent.action.CALL -d tel:{safe_number}")
        return True
    except Exception as e:
        print(f"❌ Error durante la llamada: {e}")
        return False

if __name__ == "__main__":
    test_num = "+34657188367"
    print(f"Probando llamada segura a {test_num}...")
    makecall(test_num)
