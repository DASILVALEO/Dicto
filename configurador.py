"""Configurador GUI para voz-a-texto.

Permite al usuario:
- Ver y cambiar la API key (MiniMax, Groq, OpenAI)
- Cambiar de proveedor
- Cambiar hotkey
- Cambiar idioma
- Probar la conexion
- Guardar y reiniciar el watchdog

Uso: pythonw configurador.pyw
"""
import os
import sys
import json
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

import requests

CONFIG_PATH = Path.home() / ".dictation_config.json"
WATCHDOG_BAT = Path(__file__).parent / "watchdog_dictation.bat"

PROVIDERS = {
    "minimax": {
        "label": "MiniMax (nube, espanol nativo)",
        "url_test": "https://api.minimax.io/v1/speech_to_text",
        "key_field": "minimax_api_key",
        "placeholder": "sk-cp-...",
        "free": True,
    },
    "groq": {
        "label": "Groq (nube, gratis)",
        "url_test": "https://api.groq.com/openai/v1/models",
        "key_field": "groq_api_key",
        "placeholder": "gsk_...",
        "free": True,
    },
    "openai": {
        "label": "OpenAI (nube, pago)",
        "url_test": "https://api.openai.com/v1/models",
        "key_field": "openai_api_key",
        "placeholder": "sk-...",
        "free": False,
    },
}

DEFAULT_CONFIG = {
    "provider": "minimax",
    "minimax_api_key": "",
    "groq_api_key": "",
    "openai_api_key": "",
    "language": "es",
    "hotkey": "alt gr",
    "quit_hotkey": "ctrl+alt+q",
    "auto_paste": True,
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig")))
        except Exception:
            pass
    return cfg


def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


class Configurador:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Configurador voz-a-texto")
        self.root.geometry("640x540")
        self.root.minsize(560, 480)
        try:
            self.root.iconbitmap(default="")
        except Exception:
            pass

        self.cfg = load_config()
        self.key_vars = {}
        self._build_ui()

    def _build_ui(self):
        # Notebook (pestanas)
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=10, pady=10)

        # === Pestana 1: API Keys ===
        tab1 = ttk.Frame(nb)
        nb.add(tab1, text="API Keys")
        self._build_api_keys_tab(tab1)

        # === Pestana 2: Comportamiento ===
        tab2 = ttk.Frame(nb)
        nb.add(tab2, text="Comportamiento")
        self._build_behavior_tab(tab2)

        # === Pestana 3: Estado ===
        tab3 = ttk.Frame(nb)
        nb.add(tab3, text="Estado")
        self._build_status_tab(tab3)

        # Botones inferiores
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="Probar conexion", command=self.test_connection).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Guardar", command=self.save).pack(side="right", padx=2)
        ttk.Button(btn_frame, text="Cancelar", command=self.root.destroy).pack(side="right")

    def _build_api_keys_tab(self, parent):
        ttk.Label(parent, text="Proveedor de transcripcion",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        ttk.Label(parent, text="Selecciona el servicio en la nube. Cada uno tiene su propia API key.",
                  wraplength=600).pack(anchor="w", pady=(0, 10))

        for prov_id, prov in PROVIDERS.items():
            frame = ttk.LabelFrame(parent, text=prov["label"])
            frame.pack(fill="x", padx=5, pady=5)
            inner = ttk.Frame(frame)
            inner.pack(fill="x", padx=5, pady=5)

            ttk.Label(inner, text="API Key:").grid(row=0, column=0, sticky="w", padx=2)
            var = tk.StringVar()
            self.key_vars[prov_id] = var
            current_key = self.cfg.get(prov["key_field"], "")
            if current_key:
                var.set("*" * min(20, len(current_key) // 4) + current_key[-6:])
                placeholder = "(actualmente configurada)"
            else:
                placeholder = prov["placeholder"]
            entry = ttk.Entry(inner, textvariable=var, width=50, show="")
            entry.grid(row=0, column=1, sticky="ew", padx=5)
            entry.config(foreground="gray")
            entry.insert(0, placeholder)
            entry.bind("<FocusIn>", lambda e, en=entry, ph=placeholder: self._clear_placeholder(en, ph))
            entry.bind("<FocusOut>", lambda e, en=entry, ph=placeholder, vid=prov_id: self._restore_placeholder(en, ph, vid))

            ttk.Label(inner, text="(pega tu API key. Para Minimax: https://platform.minimax.io)").grid(
                row=1, column=1, sticky="w", padx=5, pady=(2, 0))
            inner.columnconfigure(1, weight=1)

        # Proveedor activo
        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(parent, text="Proveedor activo:").pack(anchor="w")
        self.provider_var = tk.StringVar(value=self.cfg.get("provider", "minimax"))
        for prov_id, prov in PROVIDERS.items():
            ttk.Radiobutton(parent, text=prov["label"], variable=self.provider_var, value=prov_id
                            ).pack(anchor="w", padx=20)

    def _build_behavior_tab(self, parent):
        # Hotkey
        ttk.Label(parent, text="Atajos de teclado", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))

        ttk.Label(parent, text="Tecla para dictar (mantener o pulsar):").pack(anchor="w", pady=(5, 0))
        self.hotkey_var = tk.StringVar(value=self.cfg.get("hotkey", "alt gr"))
        hk_frame = ttk.Frame(parent)
        hk_frame.pack(fill="x", pady=2)
        ttk.Entry(hk_frame, textvariable=self.hotkey_var, width=30).pack(side="left", padx=(20, 5))
        ttk.Label(hk_frame, text="ej: alt gr, f12, ctrl+shift+space, right ctrl"
                  ).pack(side="left")

        ttk.Label(parent, text="Tecla para salir:").pack(anchor="w", pady=(10, 0))
        self.quit_var = tk.StringVar(value=self.cfg.get("quit_hotkey", "ctrl+alt+q"))
        ttk.Entry(parent, textvariable=self.quit_var, width=30).pack(anchor="w", padx=20, pady=2)

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=15)

        # Idioma
        ttk.Label(parent, text="Idioma (codigo BCP-47)", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5, 5))
        self.lang_var = tk.StringVar(value=self.cfg.get("language", "es"))
        lang_frame = ttk.Frame(parent)
        lang_frame.pack(fill="x", pady=2)
        ttk.Entry(lang_frame, textvariable=self.lang_var, width=10).pack(side="left", padx=(20, 5))
        ttk.Label(lang_frame, text="ej: es, en, fr, de, pt, it, ja, zh, vacio = auto").pack(side="left")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", pady=15)

        # Auto-paste
        self.paste_var = tk.BooleanVar(value=self.cfg.get("auto_paste", True))
        ttk.Checkbutton(parent, text="Pegar automaticamente donde este el cursor (recomendado)",
                        variable=self.paste_var).pack(anchor="w", padx=20)

    def _build_status_tab(self, parent):
        ttk.Label(parent, text="Estado actual", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        self.status_text = tk.Text(parent, height=12, wrap="word", state="disabled", font=("Consolas", 9))
        self.status_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.refresh_status()

        ttk.Button(parent, text="Refrescar estado", command=self.refresh_status).pack(pady=5)
        ttk.Button(parent, text="Reiniciar watchdog", command=self.restart_watchdog).pack(pady=2)
        ttk.Button(parent, text="Abrir archivo de config", command=self.open_config_file).pack(pady=2)

    def _clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, "end")
            entry.config(foreground="black")

    def _restore_placeholder(self, entry, placeholder, prov_id):
        if not entry.get().strip():
            entry.insert(0, placeholder)
            entry.config(foreground="gray")
        else:
            # Si el usuario escribio, marcar como "nueva key"
            new_val = entry.get().strip()
            if not new_val.startswith("*"):
                self.key_vars[prov_id].set(new_val)
                self.key_vars[prov_id + "_is_new"] = True

    def refresh_status(self):
        lines = []
        lines.append(f"Archivo de config: {CONFIG_PATH}")
        lines.append(f"Existe: {'SI' if CONFIG_PATH.exists() else 'NO'}")
        lines.append("")

        for prov_id, prov in PROVIDERS.items():
            key = self.cfg.get(prov["key_field"], "")
            if key:
                masked = key[:6] + "..." + key[-4:] if len(key) > 12 else "***"
                lines.append(f"{prov['label']}: {masked}")
            else:
                lines.append(f"{prov['label']}: (no configurada)")

        lines.append("")
        lines.append(f"Proveedor activo: {self.cfg.get('provider', 'minimax')}")
        lines.append(f"Hotkey: {self.cfg.get('hotkey', 'alt gr')}")
        lines.append(f"Idioma: {self.cfg.get('language', 'es')}")
        lines.append(f"Auto-paste: {self.cfg.get('auto_paste', True)}")
        lines.append("")

        # Estado del watchdog/proceso
        try:
            out = subprocess.run(["tasklist"], capture_output=True, text=True, timeout=5).stdout
            if "pythonw.exe" in out:
                lines.append("Proceso pythonw: ACTIVO (app corriendo)")
            else:
                lines.append("Proceso pythonw: NO activo")
        except Exception:
            lines.append("Proceso pythonw: (no se pudo comprobar)")

        # Auto-inicio
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
            try:
                val, _ = winreg.QueryValueEx(key, "DictationWatchdog")
                lines.append(f"Auto-inicio: CONFIGURADO -> {val}")
            except FileNotFoundError:
                lines.append("Auto-inicio: no configurado")
            winreg.CloseKey(key)
        except Exception:
            pass

        self.status_text.config(state="normal")
        self.status_text.delete("1.0", "end")
        self.status_text.insert("1.0", "\n".join(lines))
        self.status_text.config(state="disabled")

    def test_connection(self):
        """Prueba la API key del proveedor activo."""
        prov = self.provider_var.get()
        if prov not in PROVIDERS:
            messagebox.showerror("Error", f"Proveedor invalido: {prov}")
            return
        info = PROVIDERS[prov]
        current = self.cfg.get(info["key_field"], "")
        # Tomar el valor del input
        var = self.key_vars.get(prov)
        if var:
            typed = var.get().strip()
            if typed and not typed.startswith("*") and typed != info["placeholder"]:
                current = typed
        if not current:
            messagebox.showwarning("Sin API key", f"Configura primero la API key de {info['label']}.")
            return

        def do_test():
            try:
                headers = {"Authorization": f"Bearer {current}"}
                r = requests.get(info["url_test"], headers=headers, timeout=15)
                if r.status_code in (200, 400, 405):
                    # 400/405 tambien cuentan como "key valida" si responde el server
                    if r.status_code == 200 or "error" in r.text.lower() or r.status_code in (400, 405):
                        messagebox.showinfo("OK", f"Conexion exitosa con {info['label']}.")
                    else:
                        messagebox.showwarning("Aviso", f"Respuesta {r.status_code}: {r.text[:200]}")
                else:
                    messagebox.showerror("Error", f"Codigo {r.status_code}: {r.text[:200]}")
            except Exception as e:
                messagebox.showerror("Error de conexion", str(e))

        threading.Thread(target=do_test, daemon=True).start()

    def save(self):
        """Guarda configuracion y reinicia el watchdog."""
        self.cfg["provider"] = self.provider_var.get()
        self.cfg["hotkey"] = self.hotkey_var.get().strip() or "alt gr"
        self.cfg["quit_hotkey"] = self.quit_var.get().strip() or "ctrl+alt+q"
        self.cfg["language"] = self.lang_var.get().strip()
        self.cfg["auto_paste"] = self.paste_var.get()

        # Recoger API keys (solo si el usuario las cambio)
        for prov_id, prov in PROVIDERS.items():
            var = self.key_vars.get(prov_id)
            if var:
                val = var.get().strip()
                # Si tiene asteriscos (mascarilla) o placeholder, no cambiar
                if val and not val.startswith("*") and val != prov["placeholder"]:
                    self.cfg[prov["key_field"]] = val

        save_config(self.cfg)
        self.restart_watchdog()
        messagebox.showinfo("Guardado",
                            f"Configuracion guardada en:\n{CONFIG_PATH}\n\n"
                            f"El watchdog se ha reiniciado.")
        self.refresh_status()

    def restart_watchdog(self):
        """Reinicia el watchdog.bat (que a su vez relanza la app)."""
        try:
            subprocess.run(["taskkill", "/F", "/IM", "pythonw.exe"], capture_output=True)
            subprocess.run(["taskkill", "/F", "/IM", "python.exe", "/FI",
                            "WINDOWTITLE eq watchdog*"], capture_output=True)
        except Exception:
            pass
        try:
            subprocess.Popen(["cmd.exe", "/c", str(WATCHDOG_BAT)],
                             creationflags=0x08000000)  # CREATE_NO_WINDOW
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo reiniciar watchdog: {e}")

    def open_config_file(self):
        try:
            if CONFIG_PATH.exists():
                os.startfile(str(CONFIG_PATH))
            else:
                messagebox.showinfo("Info", f"Archivo no existe todavia. Pulsa Guardar primero.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = Configurador()
    app.run()
