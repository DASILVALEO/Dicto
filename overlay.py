"""Overlay transparente tipo SayIt: solo VU meter verde + cronometro, sin fondo.

En Windows, se logra con wm_attributes('-transparentcolor', color) que hace
totalmente invisibles los pixeles de ese color. Dibujamos todo lo demas
(barras verdes, texto) sobre fondo 'magenta' que es el color transparente.
"""
import tkinter as tk
import threading
import queue
import time


# Color que Tkinter hara totalmente transparente (no sera visible)
TRANSPARENT_COLOR = "#ff00ff"  # magenta puro


class DictationOverlay:
    """Overlay con fondo transparente. Muestra:
        - Modo recording: cronometro 'Xs' + VU meter de barras verdes
        - Modo processing: 'Xs - transcribiendo...'
        - Modo done: 'OK' por 5 segundos
        - Modo ready/oculto: invisible
    """

    # Colores
    GREEN = "#22c55e"      # verde brillante
    GREEN_BRIGHT = "#86efac"  # verde claro (pico)
    YELLOW = "#fbbf24"     # amarillo
    WHITE = "#ffffff"
    GRAY = "#9ca3af"
    RED = "#ef4444"

    def __init__(self):
        self.queue: "queue.Queue" = queue.Queue()
        self.root: "tk.Tk | None" = None
        self.thread: "threading.Thread | None" = None
        self._state = "ready"
        self._text = ""
        self._level = 0.0
        self._level_history: list[float] = []
        self._running = False
        self._done_until: float = 0.0
        self._recording_start: float = 0.0  # para el cronometro
        self._processing_start: float = 0.0
        self._last_size: tuple = (220, 36)

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self._running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self):
        self._running = False
        try:
            if self.root:
                self.root.after(0, self.root.quit)
        except Exception:
            pass

    def set_state(self, state: str, text: str = ""):
        self.queue.put(("state", state, text))

    def set_level(self, level: float):
        self.queue.put(("level", max(0.0, min(1.0, level))))

    def _run(self):
        try:
            self.root = tk.Tk()
        except Exception as e:
            print(f"[OVERLAY] Tkinter fallo: {e}")
            return

        self.root.title("Dictation")
        # Sin bordes
        try:
            self.root.overrideredirect(True)
        except Exception:
            pass
        # Siempre encima
        try:
            self.root.attributes("-topmost", True)
        except Exception:
            pass
        # Color clave totalmente transparente
        try:
            self.root.attributes("-transparentcolor", TRANSPARENT_COLOR)
        except Exception as e:
            print(f"[OVERLAY] transparentcolor no soportado: {e}")
        # Tamano inicial
        w, h = 220, 36
        self.root.geometry(f"{w}x{h}+{500}+{50}")
        self.root.minsize(100, 30)

        # Arrastrable
        self._drag = {"x": 0, "y": 0, "active": False}
        self.root.bind("<Button-1>", self._on_drag_start)
        self.root.bind("<B1-Motion>", self._on_drag_motion)

        # Canvas con fondo del color transparente
        self.canvas = tk.Canvas(self.root, bg=TRANSPARENT_COLOR,
                                height=h, width=w, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.root.after(40, self._tick)
        try:
            self.root.mainloop()
        except Exception:
            pass

    def _on_drag_start(self, event):
        self._drag["x"] = event.x
        self._drag["y"] = event.y
        self._drag["active"] = True

    def _on_drag_motion(self, event):
        if not self._drag["active"]:
            return
        x = self.root.winfo_x() + (event.x - self._drag["x"])
        y = self.root.winfo_y() + (event.y - self._drag["y"])
        self.root.geometry(f"+{x}+{y}")

    def _tick(self):
        if not self._running:
            try:
                self.root.destroy()
            except Exception:
                pass
            return

        # Procesar mensajes
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == "state":
                    self._state = msg[1]
                    self._text = msg[2] if len(msg) > 2 else ""
                    if self._state == "recording" and self._recording_start == 0.0:
                        self._recording_start = time.time()
                    elif self._state == "processing" and self._processing_start == 0.0:
                        self._processing_start = time.time()
                    elif self._state in ("ready", "done"):
                        if self._state == "done":
                            self._done_until = time.time() + 5.0
                        if self._state == "ready":
                            self._recording_start = 0.0
                            self._processing_start = 0.0
                elif msg[0] == "level":
                    self._level = float(msg[1])
                    self._level_history.append(self._level)
                    if len(self._level_history) > 32:
                        self._level_history = self._level_history[-32:]
        except queue.Empty:
            pass

        # Auto-dismiss
        display_state = self._state
        display_text = self._text
        if self._state == "done" and time.time() > self._done_until:
            display_state = "ready"

        # Cronometro
        timer_text = ""
        if display_state == "recording" and self._recording_start > 0:
            elapsed = int(time.time() - self._recording_start)
            timer_text = f"{elapsed}s"
        elif display_state == "processing" and self._processing_start > 0:
            elapsed = int(time.time() - self._processing_start)
            timer_text = f"{elapsed}s"

        self._draw(display_state, display_text, timer_text)
        try:
            self.root.after(40, self._tick)
        except Exception:
            pass

    def _draw(self, state: str, text: str, timer_text: str):
        c = self.canvas
        c.delete("all")
        # Restaurar fondo transparente
        c.configure(bg=TRANSPARENT_COLOR)

        w = c.winfo_width()
        h = c.winfo_height()
        margin_x = 10
        margin_y = 8

        if state == "ready":
            # Invisible en ready
            return

        # Color principal segun estado
        if state == "recording":
            main_color = self.GREEN
        elif state == "processing":
            main_color = self.YELLOW
        elif state == "done":
            main_color = self.GREEN
        elif state == "error":
            main_color = self.RED
        else:
            return

        # Dibujar cronometro a la izquierda
        timer_x = margin_x + 4
        timer_y = h // 2
        if timer_text:
            c.create_text(timer_x, timer_y, text=timer_text, fill=main_color,
                          font=("Segoe UI", 11, "bold"), anchor="w")

        # VU meter (barras verticales) - a la derecha del cronometro
        meter_x0 = timer_x + 36 if timer_text else margin_x
        meter_x1 = w - margin_x
        meter_y0 = margin_y
        meter_y1 = h - margin_y

        if state == "recording" and self._level_history:
            # VU meter: barras mas grandes y responsivas (estilo test de micro de Windows)
            n = min(len(self._level_history), 24)
            samples = self._level_history[-n:]
            total_w = meter_x1 - meter_x0
            bar_gap = 2
            bar_w = (total_w - bar_gap * (n - 1)) / n
            max_bar_h = (meter_y1 - meter_y0)
            for i, lv in enumerate(samples):
                bx = meter_x0 + i * (bar_w + bar_gap)
                # Altura minima 3px, maxima proporcional al nivel (amplificado x3 para que se vea)
                bh = max(3, min(max_bar_h, lv * max_bar_h * 3.0))
                by = meter_y1 - bh
                # Color mas brillante en picos
                if lv > 0.3:
                    color = self.GREEN_BRIGHT
                else:
                    color = main_color
                c.create_rectangle(bx, by, bx + bar_w, meter_y1, fill=color, outline="")
        else:
            # En processing/done/error: barra estatica baja
            n = 24
            total_w = meter_x1 - meter_x0
            bar_gap = 2
            bar_w = (total_w - bar_gap * (n - 1)) / n
            for i in range(n):
                bx = meter_x0 + i * (bar_w + bar_gap)
                if state == "processing":
                    bh = 4 + (i % 4) * 2
                else:
                    bh = 3
                by = meter_y1 - bh
                c.create_rectangle(bx, by, bx + bar_w, meter_y1, fill=main_color, outline="")

        # Indicador de estado (punto) si no es recording
        if state != "recording" and not timer_text:
            cx, cy, r = 14, h // 2, 5
            c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=main_color, outline="")

        # Texto (en processing o done, mostrar mensaje corto)
        if state == "processing":
            txt = "..."
        elif state == "done" and text:
            txt = "OK" if len(text) > 30 else text
        else:
            txt = ""
        if txt and not timer_text:
            c.create_text(margin_x, h//2, text=txt, fill=main_color,
                          font=("Segoe UI", 10, "bold"), anchor="w")
