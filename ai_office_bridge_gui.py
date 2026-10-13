"""
AI Office Bridge - GUI principal (version final con catalogo y email)
"""
import os
import sys
import json
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path
from datetime import datetime
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))
from ocr_engine import extract_from_file
from comprobante_generator import (
    crear_comprobante_iva, crear_comprobante_islr,
    agregar_a_libro_compras, TEMPLATES_DIR
)
from catalogo_proveedores import catalogo
from email_sender import send_comprobante_email, is_email_configured, load_config as load_email_config

CONFIG_PATH = Path.home() / ".dictation_config.json"
DICCIONARIO_DIR = Path(__file__).parent

COLORES = {
    "ok": "#d4edda",
    "error": "#f8d7da",
    "advertencia": "#fff3cd",
    "readonly": "#e9ecef",
    "blanco": "white",
}

VALIDATORS = {
    "text": lambda v: (True, None) if v else (False, "Requerido"),
    "date": lambda v: (
        (True, None) if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", v) else
        (False, "Formato DD/MM/YYYY")
    ),
    "rif": lambda v: (
        (True, None) if re.match(r"^[JVE]-\d{8}-\d$", v) else
        (False, "Formato: J-12345678-9")
    ),
    "money": lambda v: (
        (True, None) if re.match(r"^\d{1,3}(,\d{3})*(\.\d{1,2})?$|^\d+(\.\d{1,2})?$", v) else
        (False, "Formato: 1234.56")
    ),
}


class FormField:
    def __init__(self, parent, label, tipo="text", valor="", placeholder="",
                 on_change=None, ancho=30, requerido=True):
        self.tipo = tipo
        self.validador = VALIDATORS.get(tipo, VALIDATORS["text"])
        self.requerido = requerido
        self.on_change = on_change
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(self.frame, text=label + ":", width=18).pack(side="left")
        self.var = tk.StringVar(value=valor)
        self.var.trace_add("write", lambda *_: self._validate())
        self.entry = ttk.Entry(self.frame, textvariable=self.var, width=ancho)
        self.entry.pack(side="left", fill="x", expand=True)
        self.status_label = ttk.Label(self.frame, text="", width=22, foreground="gray")
        self.status_label.pack(side="left", padx=5)

    def get(self):
        return self.var.get().strip()

    def set(self, v):
        self.var.set(str(v) if v is not None else "")
        self._validate()

    def _validate(self):
        v = self.get()
        if not v and not self.requerido:
            self.entry.config(background=COLORES["blanco"])
            self.status_label.config(text="(opcional)", foreground="gray")
            return True
        if not v and self.requerido:
            self.entry.config(background=COLORES["error"])
            self.status_label.config(text="(requerido)", foreground="red")
            return False
        ok, error = self.validador(v)
        if ok:
            self.entry.config(background=COLORES["ok"])
            self.status_label.config(text="OK", foreground="green")
        else:
            self.entry.config(background=COLORES["error"])
            self.status_label.config(text=error, foreground="red")
        if self.on_change:
            self.on_change(v, ok)
        return ok

    def validate(self):
        return self._validate()


class FormularioFactura(tk.Toplevel):
    """Formulario validado para nueva factura con catalogo integrado."""
    def __init__(self, parent, on_submit=None, datos_extraidos=None,
                 aplicar_iva=True):
        super().__init__(parent)
        self.title("Nueva Factura - Validada")
        self.geometry("800x800")
        self.on_submit = on_submit
        self.datos = datos_extraidos or {}
        self.aplicar_iva_default = aplicar_iva

        self._build_ui()
        if self.datos:
            self._poblar_datos()
        self._update_proveedor_list()

    def _build_ui(self):
        banner = ttk.Frame(self, relief="sunken")
        banner.pack(fill="x", padx=10, pady=5)
        if self.datos.get("confianza_extraccion"):
            c = self.datos["confianza_extraccion"]
            color = "green" if c >= 70 else ("orange" if c >= 40 else "red")
            ttk.Label(banner, text=f"OCR con {c}% confianza. Verifica antes de guardar.",
                      foreground=color).pack(padx=5, pady=3)

        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        scrollbar.pack(side="right", fill="y")

        # Seccion 1: Identificacion
        sec1 = ttk.LabelFrame(scroll_frame, text="Identificacion de la Factura")
        sec1.pack(fill="x", padx=5, pady=5)
        self.f_numero = FormField(sec1, "N Factura", "text", placeholder="F-2026-001")
        self.f_fecha_emision = FormField(sec1, "Fecha Emision", "date", placeholder="DD/MM/YYYY")
        self.f_fecha_recepcion = FormField(sec1, "Fecha Recepcion", "date", placeholder="DD/MM/YYYY")
        self.f_numero_control = FormField(sec1, "N Control", "text", requerido=False)

        # Seccion 2: Proveedor (CON CATALOGO)
        sec2 = ttk.LabelFrame(scroll_frame, text="Proveedor (autocompletar desde catalogo)")
        sec2.pack(fill="x", padx=5, pady=5)
        # Combobox para nombre con autocompletar
        nombre_frame = ttk.Frame(sec2)
        nombre_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(nombre_frame, text="Nombre:", width=18).pack(side="left")
        self.f_proveedor = ttk.Combobox(nombre_frame, width=50)
        self.f_proveedor.pack(side="left", fill="x", expand=True)
        self.f_proveedor.bind("<<ComboboxSelected>>", self._on_proveedor_selected)
        self.f_proveedor.bind("<KeyRelease>", self._on_proveedor_typed)
        # Entry para RIF
        self.f_rif = FormField(sec2, "RIF", "rif", placeholder="J-12345678-9")
        # Entry para direccion y email
        self.f_direccion = FormField(sec2, "Direccion", "text", requerido=False)
        self.f_telefono = FormField(sec2, "Telefono", "text", requerido=False)
        self.f_email = FormField(sec2, "Email", "text", requerido=False)
        # Info de match
        self.match_label = ttk.Label(sec2, text="", foreground="green", font=("", 9, "italic"))
        self.match_label.pack(anchor="w", padx=20)

        # Seccion 3: Montos
        sec3 = ttk.LabelFrame(scroll_frame, text="Montos (en Bolivares)")
        sec3.pack(fill="x", padx=5, pady=5)
        self.f_subtotal = FormField(sec3, "Subtotal", "money", on_change=self._on_subtotal_change)
        self.f_iva = FormField(sec3, "IVA 16%", "money")
        self.f_total = FormField(sec3, "Total", "money", on_change=self._on_total_change)

        # Seccion 4: Retencion
        sec4 = ttk.LabelFrame(scroll_frame, text="Retencion (segun SENIAT)")
        sec4.pack(fill="x", padx=5, pady=5)
        self.f_aplica_iva = tk.BooleanVar(value=self.aplicar_iva_default)
        ttk.Checkbutton(sec4, text="Aplica retencion IVA 75%",
                        variable=self.f_aplica_iva,
                        command=self._recalc_retencion).pack(anchor="w")
        self.f_aplica_islr = tk.BooleanVar(value=False)
        ttk.Checkbutton(sec4, text="Aplica retencion ISLR",
                        variable=self.f_aplica_islr,
                        command=self._recalc_retencion).pack(anchor="w")
        islr_frame = ttk.Frame(sec4)
        islr_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(islr_frame, text="Alicuota ISLR %:", width=18).pack(side="left")
        self.f_alicuota_islr = ttk.Combobox(islr_frame, values=["0", "2", "3", "5", "10", "12", "100"],
                                              width=8, state="readonly")
        self.f_alicuota_islr.set("2")
        self.f_alicuota_islr.pack(side="left", padx=5)
        self.f_alicuota_islr.bind("<<ComboboxSelected>>", lambda e: self._recalc_retencion())

        self.f_monto_retencion = FormField(sec4, "Monto Total Retenido", "money", requerido=False)
        self.f_total_neto = FormField(sec4, "Total a Pagar (Neto)", "money", requerido=False)

        # Resumen
        self.resumen = ttk.Label(scroll_frame, text="", foreground="gray")
        self.resumen.pack(fill="x", padx=10, pady=5)

        # Botones
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Validar",
                   command=self._validar_todo).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Guardar + Comprobante + Email",
                   command=self._on_submit).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Cancelar",
                   command=self.destroy).pack(side="right", padx=2)

        self.campos_requeridos = [
            self.f_numero, self.f_fecha_emision, self.f_proveedor,
            self.f_rif, self.f_subtotal, self.f_iva, self.f_total
        ]

    def _update_proveedor_list(self):
        """Carga la lista de proveedores en el combobox."""
        nombres = catalogo.get_nombres()
        self.f_proveedor["values"] = nombres

    def _on_proveedor_typed(self, event):
        """Autocompletar mientras el usuario escribe."""
        query = self.f_proveedor.get()
        if len(query) < 2:
            return
        sugerencias = catalogo.buscar_por_nombre(query)
        if sugerencias:
            nombres = [p["nombre"] for p in sugerencias]
            self.f_proveedor["values"] = nombres
            # No modificar el texto actual
            try:
                self.f_proveedor.event_generate("<Down>")
            except Exception:
                pass

    def _on_proveedor_selected(self, event):
        """Cuando el usuario selecciona un proveedor del dropdown."""
        nombre = self.f_proveedor.get()
        if not nombre:
            return
        prov = catalogo.get_por_nombre_exacto(nombre)
        if prov:
            self.f_rif.set(prov["rif"])
            if prov.get("direccion"):
                self.f_direccion.set(prov["direccion"])
            if prov.get("telefono"):
                self.f_telefono.set(prov["telefono"])
            if prov.get("email"):
                self.f_email.set(prov["email"])
            self.match_label.config(text=f"Proveedor del catalogo: {prov['rif']}")

    def _poblar_datos(self):
        mapeo = {
            "numero_factura": "f_numero",
            "fecha_emision": "f_fecha_emision",
            "fecha_recepcion": "f_fecha_recepcion",
            "numero_control": "f_numero_control",
            "proveedor": "f_proveedor",
            "rif_proveedor": "f_rif",
            "direccion_proveedor": "f_direccion",
            "telefono_proveedor": "f_telefono",
            "email_proveedor": "f_email",
            "subtotal": "f_subtotal",
            "iva": "f_iva",
            "total": "f_total",
        }
        # Intentar matchear con catalogo si tenemos RIF o nombre
        rif = self.datos.get("rif_proveedor", "")
        nombre = self.datos.get("nombre_proveedor", "")
        prov_match = catalogo.sugerir_match(nombre, rif)
        if prov_match:
            self.datos["nombre_proveedor"] = prov_match["nombre"]  # Usar el nombre canonico
            self.datos["rif_proveedor"] = prov_match["rif"]
            if prov_match.get("email") and not self.datos.get("email_proveedor"):
                self.datos["email_proveedor"] = prov_match["email"]
            if prov_match.get("direccion") and not self.datos.get("direccion_proveedor"):
                self.datos["direccion_proveedor"] = prov_match["direccion"]
            if prov_match.get("telefono") and not self.datos.get("telefono_proveedor"):
                self.datos["telefono_proveedor"] = prov_match["telefono"]
        for key_dato, attr_campo in mapeo.items():
            if self.datos.get(key_dato):
                field = getattr(self, attr_campo)
                if hasattr(field, "set"):
                    field.set(self.datos[key_dato])
                else:
                    # Es un Combobox
                    field.set(self.datos[key_dato])
        if self.datos.get("aplica_retencion_iva") is False:
            self.f_aplica_iva.set(False)
        if self.datos.get("aplica_retencion_islr"):
            self.f_aplica_islr.set(True)
            if self.datos.get("porcentaje_islr_retenido"):
                self.f_alicuota_islr.set(str(int(self.datos["porcentaje_islr_retenido"])))
        self._recalc_retencion()

    def _on_subtotal_change(self, valor, ok):
        if ok and valor:
            try:
                sub = float(valor.replace(",", ""))
                iva = sub * 0.16
                self.f_iva.set(f"{iva:.2f}")
                self.f_total.set(f"{sub + iva:.2f}")
            except (ValueError, AttributeError):
                pass

    def _on_total_change(self, valor, ok):
        if ok and valor:
            try:
                tot = float(valor.replace(",", ""))
                sub = tot / 1.16
                iva = tot - sub
                self.f_subtotal.set(f"{sub:.2f}")
                self.f_iva.set(f"{iva:.2f}")
            except (ValueError, AttributeError):
                pass

    def _recalc_retencion(self):
        try:
            iva = float(self.f_iva.get().replace(",", "")) if self.f_iva.get() else 0
        except ValueError:
            iva = 0
        try:
            base = float(self.f_subtotal.get().replace(",", "")) if self.f_subtotal.get() else 0
        except ValueError:
            base = 0
        try:
            total = float(self.f_total.get().replace(",", "")) if self.f_total.get() else 0
        except ValueError:
            total = 0

        retencion = 0
        if self.f_aplica_iva.get():
            retencion += iva * 0.75
        if self.f_aplica_islr.get():
            try:
                alicuota = float(self.f_alicuota_islr.get())
                retencion += base * (alicuota / 100)
            except (ValueError, TypeError):
                pass
        self.f_monto_retencion.set(f"{retencion:.2f}" if retencion else "")
        neto = total - retencion
        self.f_total_neto.set(f"{neto:.2f}" if neto else "")

    def _validar_todo(self):
        errores = []
        # Validar campos normales
        for campo in self.campos_requeridos:
            if hasattr(campo, "validate"):
                if not campo.validate():
                    errores.append("Campo invalido")
        # Validaciones cruzadas
        try:
            sub = float(self.f_subtotal.get().replace(",", ""))
            iva = float(self.f_iva.get().replace(",", ""))
            tot = float(self.f_total.get().replace(",", ""))
            if abs(sub + iva - tot) > 0.01:
                errores.append(f"Sub+IVA ({sub+iva:.2f}) != Total ({tot:.2f})")
            if abs(sub * 0.16 - iva) > 0.01:
                errores.append(f"IVA ({iva:.2f}) != 16% Sub ({sub*0.16:.2f})")
        except (ValueError, AttributeError):
            pass

        if errores:
            self.resumen.config(text=f"{len(errores)} error(es): {'; '.join(errores[:3])}",
                                foreground="red")
            return False
        self.resumen.config(text="Todos los campos validos. Listo para guardar.",
                            foreground="green")
        return True

    def _on_submit(self):
        if not self._validar_todo():
            messagebox.showerror("Errores", "Hay errores. Corrigelos antes de guardar.")
            return
        if not messagebox.askyesno("Confirmar",
                                    "Guardar y generar comprobante de retencion?"):
            return
        # Recolectar datos del form
        # Para el Combobox de proveedor, el valor es el nombre
        datos = {
            "numero_factura": self.f_numero.get(),
            "fecha_emision": self.f_fecha_emision.get(),
            "fecha_recepcion": self.f_fecha_recepcion.get() or self.f_fecha_emision.get(),
            "numero_control": self.f_numero_control.get(),
            "nombre_proveedor": self.f_proveedor.get(),
            "rif_proveedor": self.f_rif.get(),
            "direccion_proveedor": self.f_direccion.get(),
            "telefono_proveedor": self.f_telefono.get(),
            "email_proveedor": self.f_email.get(),
            "subtotal": self.f_subtotal.get().replace(",", ""),
            "iva": self.f_iva.get().replace(",", ""),
            "total": self.f_total.get().replace(",", ""),
            "aplica_retencion_iva": self.f_aplica_iva.get(),
            "aplica_retencion_islr": self.f_aplica_islr.get(),
            "porcentaje_iva_retenido": 75 if self.f_aplica_iva.get() else 0,
            "porcentaje_islr_retenido": float(self.f_alicuota_islr.get()) if self.f_aplica_islr.get() else 0,
            "monto_retencion": self.f_monto_retencion.get().replace(",", ""),
            "monto_retencion_islr": str(float(self.f_subtotal.get().replace(",", "")) * float(self.f_alicuota_islr.get()) / 100) if (self.f_aplica_islr.get() and self.f_subtotal.get()) else "0",
            "total_neto": self.f_total_neto.get().replace(",", ""),
        }
        if self.on_submit:
            self.on_submit(datos)
        self.destroy()


class AIBridge(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Office Bridge - Suite Administrativa con IA")
        self.geometry("1200x750")
        self.minsize(1000, 600)

        self.config = self._load_config()
        self.archivo_actual = None
        self.datos_extraidos = None

        self._setup_style()
        self._build_ui()
        self._log(f"Proveedores en catalogo: {len(catalogo.proveedores)}", "info")
        self._log(f"Email configurado: {'SI' if is_email_configured() else 'NO'}", "info")

    def _load_config(self):
        if CONFIG_PATH.exists():
            try:
                return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
            except Exception:
                pass
        return {}

    def _setup_style(self):
        try:
            import ttkbootstrap
            self.style = ttkbootstrap.Style(theme="cosmo")
        except ImportError:
            self.style = ttk.Style()
            self.style.theme_use("clam")

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=5)
        ttk.Button(top, text="Abrir archivo",
                   command=self._abrir_archivo).pack(side="left", padx=2)
        ttk.Button(top, text="Cargar Factura (OCR)",
                   command=self._cargar_factura).pack(side="left", padx=2)
        ttk.Button(top, text="Nueva Factura",
                   command=self._nueva_factura).pack(side="left", padx=2)
        ttk.Button(top, text="Guardar en Libro",
                   command=self._guardar_en_libro).pack(side="left", padx=2)
        ttk.Button(top, text="Configuracion",
                   command=self._settings).pack(side="right")
        self.file_label = ttk.Label(self, text="Sin archivo", foreground="gray")
        self.file_label.pack(anchor="w", padx=15)

        main = ttk.PanedWindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=10, pady=5)
        left = ttk.Frame(main)
        main.add(left, weight=65)
        ttk.Label(left, text="Actividad",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=5)
        self.chat = tk.Text(left, wrap="word", height=25, state="disabled",
                            font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        scroll = ttk.Scrollbar(left, command=self.chat.yview)
        self.chat.configure(yscrollcommand=scroll.set)
        self.chat.pack(fill="both", expand=True, padx=5, pady=5)
        scroll.pack(side="right", fill="y")
        btn_frame = ttk.Frame(left)
        btn_frame.pack(fill="x", padx=5, pady=5)
        ttk.Button(btn_frame, text="Limpiar log",
                   command=self._clear_log).pack(side="left", padx=2)
        right = ttk.Frame(main)
        main.add(right, weight=35)
        ttk.Label(right, text="Vista Previa",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=5)
        self.preview = tk.Text(right, wrap="none", state="disabled",
                               font=("Consolas", 8), bg="#f5f5f5")
        pscroll_y = ttk.Scrollbar(right, command=self.preview.yview)
        pscroll_x = ttk.Scrollbar(right, command=self.preview.xview, orient="horizontal")
        self.preview.configure(yscrollcommand=pscroll_y.set,
                               xscrollcommand=pscroll_x.set)
        self.preview.pack(fill="both", expand=True, padx=5, pady=5)
        pscroll_y.pack(side="right", fill="y")
        pscroll_x.pack(side="bottom", fill="x")
        self.status = ttk.Label(self, text="Listo", relief="sunken", anchor="w")
        self.status.pack(fill="x", side="bottom")

    def _log(self, msg, tipo="info"):
        self.chat.config(state="normal")
        prefix = {"info": "[INFO] ", "ok": "[OK]   ", "error": "[ERR]  ",
                  "warn": "[WARN] ", "user": "[USER] ", "ai": "[AI]   "}.get(tipo, "  ")
        self.chat.insert("end", prefix + msg + "\n")
        self.chat.see("end")
        self.chat.config(state="disabled")

    def _clear_log(self):
        self.chat.config(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.config(state="disabled")

    def _set_status(self, msg):
        self.status.config(text=msg)
        self.update_idletasks()

    def _abrir_archivo(self):
        path = filedialog.askopenfilename(
            title="Abrir archivo Excel",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")])
        if not path:
            return
        self.archivo_actual = Path(path)
        self.file_label.config(text=f"Archivo: {self.archivo_actual.name}")
        self._log(f"Archivo abierto: {self.archivo_actual.name}", "ok")

    def _cargar_factura(self):
        path = filedialog.askopenfilename(
            title="Cargar factura (PDF o imagen)",
            filetypes=[("Imagen", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                       ("PDF", "*.pdf"), ("Todos", "*.*")])
        if not path:
            return
        self._log(f"Cargando: {Path(path).name}...", "info")
        self._set_status("Extrayendo con MiniMax Vision...")
        self.update_idletasks()
        try:
            datos = extract_from_file(Path(path))
        except Exception as e:
            self._log(f"Error: {e}", "error")
            messagebox.showerror("Error", str(e))
            return
        if "error" in datos:
            self._log(f"Error: {datos['error']}", "error")
            messagebox.showerror("Error", datos["error"])
            return
        self.datos_extraidos = datos
        self._log(f"OCR: {datos.get('confianza_extraccion', '?')}% confianza", "ok")
        self._log(f"  N Factura: {datos.get('numero_factura', 'N/A')}", "ai")
        self._log(f"  Proveedor: {datos.get('nombre_proveedor', 'N/A')}", "ai")
        # Verificar match con catalogo
        match = catalogo.sugerir_match(datos.get("nombre_proveedor", ""),
                                       datos.get("rif_proveedor", ""))
        if match:
            self._log(f"  Match en catalogo: {match['nombre']} ({match['rif']})", "ok")
        else:
            self._log("  Sin match en catalogo (proveedor nuevo?)", "warn")
        # Preview
        self.preview.config(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", json.dumps(datos, indent=2, ensure_ascii=False))
        self.preview.config(state="disabled")
        # Form
        aplicar_iva = datos.get('aplica_retencion_iva', True)
        FormularioFactura(self, on_submit=self._on_factura_guardada,
                          datos_extraidos=datos, aplicar_iva=aplicar_iva)
        self._log("Abriendo formulario pre-llenado...", "info")

    def _nueva_factura(self):
        if not self.archivo_actual:
            messagebox.showwarning("Sin archivo",
                                    "Primero abre un archivo Excel.")
            return
        FormularioFactura(self, on_submit=self._on_factura_guardada)
        self._log("Formulario de nueva factura abierto", "info")

    def _on_factura_guardada(self, datos):
        self._log(f"Factura validada: {datos['numero_factura']} - {datos['proveedor']}", "ok")
        self._log(f"  Total: Bs. {datos['total']} | Ret: Bs. {datos['monto_retencion']} | Neto: Bs. {datos['total_neto']}", "info")
        self.datos_extraidos = datos
        self._set_status(f"Listo para escribir al Excel: {datos['numero_factura']}")

    def _guardar_en_libro(self):
        if not self.datos_extraidos:
            messagebox.showwarning("Sin datos", "No hay factura cargada.")
            return
        if not self.archivo_actual:
            messagebox.showwarning("Sin archivo", "Abre un archivo Excel primero.")
            return

        datos = self.datos_extraidos
        output_dir = self.archivo_actual.parent / "generados"
        output_dir.mkdir(exist_ok=True)
        archivos_generados = []

        # 1. Agregar al libro
        self._log(f"Agregando al libro: {self.archivo_actual.name}", "info")
        if agregar_a_libro_compras(datos, self.archivo_actual):
            self._log("Factura agregada al libro", "ok")
        else:
            self._log("No se pudo agregar al libro", "warn")

        # 2. Generar comprobante IVA
        if datos.get('aplica_retencion_iva') or datos.get('monto_retencion'):
            self._log("Generando comprobante IVA...", "info")
            archivo_iva = crear_comprobante_iva(datos, output_dir)
            if archivo_iva:
                self._log(f"Comprobante IVA: {archivo_iva.name}", "ok")
                archivos_generados.append(archivo_iva)

        # 3. Generar comprobante ISLR
        if datos.get('aplica_retencion_islr'):
            self._log("Generando comprobante ISLR...", "info")
            archivo_islr = crear_comprobante_islr(datos, output_dir)
            if archivo_islr:
                self._log(f"Comprobante ISLR: {archivo_islr.name}", "ok")
                archivos_generados.append(archivo_islr)

        # 4. Enviar email
        if is_email_configured() and datos.get("email_proveedor"):
            self._log(f"Enviando email a {datos['email_proveedor']}...", "info")
            for archivo in archivos_generados:
                ok, msg = send_comprobante_email(archivo, datos)
                if ok:
                    self._log(f"Email enviado: {msg}", "ok")
                else:
                    self._log(f"Email fallo: {msg}", "warn")
        else:
            self._log("Email no enviado (no configurado o sin email del proveedor)", "warn")

        self._set_status(f"Procesado: {datos['numero_factura']}")
        msg = f"Factura procesada.\nArchivos generados en:\n{output_dir}"
        if archivos_generados:
            msg += f"\n\n{len(archivos_generados)} comprobante(s) creado(s)"
        messagebox.showinfo("Listo", msg)

    def _settings(self):
        SettingsDialog(self)

    def _show_preview(self):
        if not self.archivo_actual or not self.archivo_actual.exists():
            return
        try:
            import subprocess as sp
            result = sp.run(
                ["C:\\Program Files\\GridCraft\\gridcraft-cli.exe", "info",
                 str(self.archivo_actual)],
                capture_output=True, text=True, timeout=10
            )
            self.preview.config(state="normal")
            self.preview.delete("1.0", "end")
            self.preview.insert("1.0", result.stdout[:5000])
            self.preview.config(state="disabled")
        except Exception as e:
            self._log(f"Error: {e}", "error")


class SettingsDialog(tk.Toplevel):
    """Dialog de configuracion (email, etc)."""
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Configuracion")
        self.geometry("500x350")
        cfg = load_email_config()
        # Email
        em = ttk.LabelFrame(self, text="Email (SMTP)")
        em.pack(fill="x", padx=10, pady=10)
        ttk.Label(em, text="SMTP Server:").grid(row=0, column=0, sticky="w", padx=5)
        self.e_server = ttk.Entry(em, width=40)
        self.e_server.insert(0, cfg.get("smtp_server", ""))
        self.e_server.grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(em, text="Puerto:").grid(row=1, column=0, sticky="w", padx=5)
        self.e_port = ttk.Entry(em, width=10)
        self.e_port.insert(0, str(cfg.get("smtp_port", 587)))
        self.e_port.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(em, text="Usuario:").grid(row=2, column=0, sticky="w", padx=5)
        self.e_user = ttk.Entry(em, width=40)
        self.e_user.insert(0, cfg.get("username", ""))
        self.e_user.grid(row=2, column=1, padx=5, pady=2)
        ttk.Label(em, text="Password:").grid(row=3, column=0, sticky="w", padx=5)
        self.e_pass = ttk.Entry(em, width=40, show="*")
        self.e_pass.insert(0, cfg.get("password", ""))
        self.e_pass.grid(row=3, column=1, padx=5, pady=2)
        ttk.Label(em, text="CC (opcional):").grid(row=4, column=0, sticky="w", padx=5)
        self.e_cc = ttk.Entry(em, width=40)
        self.e_cc.insert(0, ", ".join(cfg.get("default_cc", [])))
        self.e_cc.grid(row=4, column=1, padx=5, pady=2)
        # Botones
        bf = ttk.Frame(self)
        bf.pack(fill="x", padx=10, pady=5)
        ttk.Button(bf, text="Guardar", command=self._save).pack(side="right", padx=2)
        ttk.Button(bf, text="Probar Email", command=self._test).pack(side="right", padx=2)

    def _save(self):
        from email_sender import save_config
        cfg = {
            "smtp_server": self.e_server.get(),
            "smtp_port": int(self.e_port.get() or 587),
            "use_tls": True,
            "username": self.e_user.get(),
            "password": self.e_pass.get(),
            "from_name": "Comprobante de Retencion",
            "default_cc": [x.strip() for x in self.e_cc.get().split(",") if x.strip()],
        }
        save_config(cfg)
        messagebox.showinfo("OK", "Configuracion guardada")
        self.destroy()

    def _test(self):
        from email_sender import send_test_email
        to = self.e_user.get()
        if not to:
            messagebox.showwarning("Atencion", "Ingresa un email destino")
            return
        ok, msg = send_test_email(to)
        if ok:
            messagebox.showinfo("OK", msg)
        else:
            messagebox.showerror("Error", msg)


def main():
    app = AIBridge()
    app.mainloop()


if __name__ == "__main__":
    main()
