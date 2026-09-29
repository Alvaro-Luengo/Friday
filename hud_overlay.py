import sys
import os
import time
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_standalone_hud(duration: float = 8.0):
    """Ejecuta el HUD flotante de alta visibilidad en la esquina superior izquierda."""
    import tkinter as tk

    root = tk.Tk()
    root.overrideredirect(True)
    root.lift()
    root.attributes("-topmost", True)
    root.after_idle(root.attributes, "-topmost", True)

    width = 250
    height = 72
    pos_x = 30
    pos_y = 30

    root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
    root.configure(bg="#050e18")

    canvas = tk.Canvas(root, width=width, height=height, bg="#050e18", highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    pulse_state = [True]

    def draw_hud(glow=True):
        canvas.delete("all")
        border_col = "#00f0ff" if glow else "#0088cc"
        bg_card = "#071726"

        # Tarjeta HUD futurista con borde iluminado
        canvas.create_rectangle(
            2, 2, width-2, height-2,
            fill=bg_card, outline=border_col, width=2
        )

        # Círculo de fondo del micrófono
        mcx, mcy = 38, 36
        canvas.create_oval(mcx-22, mcy-22, mcx+22, mcy+22, fill="#0a253d", outline=border_col, width=2)

        # Micrófono Vectorial Azul/Cian Brillante (Independiente de emojis de Windows)
        mic_color = "#00f0ff" if glow else "#00c8f8"
        # Cuerpo / Cápsula del micro
        canvas.create_rectangle(mcx-5, mcy-10, mcx+5, mcy+3, fill=mic_color, outline="")
        canvas.create_oval(mcx-5, mcy-15, mcx+5, mcy-5, fill=mic_color, outline="")
        canvas.create_oval(mcx-5, mcy-2, mcx+5, mcy+8, fill=mic_color, outline="")
        # Horquilla / Arco de soporte
        canvas.create_arc(mcx-10, mcy-5, mcx+10, mcy+12, start=180, extent=180, style="arc", outline=mic_color, width=3)
        # Pie / Soporte vertical
        canvas.create_line(mcx, mcy+12, mcx, mcy+18, fill=mic_color, width=3)
        canvas.create_line(mcx-7, mcy+18, mcx+7, mcy+18, fill=mic_color, width=3)

        # Textos de estado
        canvas.create_text(74, 25, text="FRIDAY", anchor="w", font=("Segoe UI", 12, "bold"), fill="#00f0ff")
        status_color = "#8ee3f5" if glow else "#5c9fb0"
        canvas.create_text(74, 47, text="ESCUCHANDO...", anchor="w", font=("Segoe UI", 9, "bold"), fill=status_color)

    draw_hud(glow=True)

    def pulse():
        pulse_state[0] = not pulse_state[0]
        draw_hud(glow=pulse_state[0])
        root.lift()
        root.attributes("-topmost", True)
        root.after(350, pulse)

    root.after(350, pulse)
    root.after(int(duration * 1000), root.destroy)
    root.mainloop()

# Gestor de HUD para llamar desde main.py
class HudController:
    def __init__(self):
        self.proc = None

    def start(self):
        pass

    def show(self, duration: float = 7.0):
        """Lanza el HUD como proceso independiente para garantizar que aparezca."""
        self.hide()
        script = str(BASE_DIR / "hud_overlay.py")
        pythonw_path = str(Path(sys.executable).parent / "pythonw.exe")
        if not os.path.exists(pythonw_path):
            pythonw_path = "pythonw"

        try:
            self.proc = subprocess.Popen(
                [pythonw_path, script, "show", str(duration)],
                cwd=str(BASE_DIR),
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform.startswith("win") else 0
            )
        except Exception as e:
            print(f"[Aviso HUD]: {e}")

    def hide(self):
        """Cierra el HUD actual si está en pantalla."""
        if self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.proc = None

    def stop(self):
        self.hide()

hud_indicator = HudController()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        dur = float(sys.argv[2]) if len(sys.argv) > 2 else 5.0
        run_standalone_hud(dur)
    else:
        print("Probando HUD independiente durante 3 segundos...")
        hud_indicator.show(3.0)
        time.sleep(3.5)
        print("HUD finalizado.")
