import os
import subprocess
from pathlib import Path

def install_startup():
    startup_dir = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    shortcut_path = startup_dir / "Friday.lnk"
    vbs_path = Path(r"D:\Friday\start_hidden.vbs")

    ps_cmd = (
        f'$wsh = New-Object -ComObject WScript.Shell; '
        f'$s = $wsh.CreateShortcut("{shortcut_path}"); '
        f'$s.TargetPath = "wscript.exe"; '
        f'$s.Arguments = \'"{vbs_path}"\'; '
        f'$s.WorkingDirectory = "D:\\Friday"; '
        f'$s.Description = "Friday Background Assistant"; '
        f'$s.WindowStyle = 7; '
        f'$s.Save()'
    )

    res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
    if shortcut_path.exists():
        print(f"[OK] Acceso directo creado con éxito en: {shortcut_path}")
        print("Friday se iniciará de forma 100% invisible en cada arranque de Windows.")
        return True
    else:
        print("[!] Error al crear el acceso directo:", res.stderr)
        return False

if __name__ == "__main__":
    install_startup()
