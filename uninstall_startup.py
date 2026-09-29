import os
from pathlib import Path

def uninstall_startup():
    startup_dir = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    shortcut_path = startup_dir / "Friday.lnk"
    if shortcut_path.exists():
        shortcut_path.unlink()
        print("[OK] Inicio automático de Friday desactivado correctamente.")
    else:
        print("[i] No se encontró acceso directo de Friday en Startup.")

if __name__ == "__main__":
    uninstall_startup()
