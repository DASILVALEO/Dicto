"""
AI Office Bridge - GUI principal
================================

Interfaz grafica amigable para automatizar el trabajo administrativo
del abasto con panaderia.

Flujo principal:
1. Arrastras factura PDF/imagen
2. MiniMax Vision extrae datos
3. Form valida con tus ojos
4. Genera comprobante de retencion
5. Actualiza libro de compras
6. (Opcional) Envia por email
"""
import os
import sys
import json
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
from typing import Optional

# Modulos propios
sys.path.insert(0, str(Path(__file__).parent))
from ocr_engine import extract_from_file
from comprobante_generator import (
    crear_comprobante_iva, crear_comprobante_islr,
    agregar_a_libro_compras, TEMPLATES_DIR
)

# Configuracion
CONFIG_PATH = Path.home() / ".dictation_config.json"
DICCIONARIO_DIR = Path(__file__).parent

# Colores para validacion
COLORES = {
    "ok": "#d4edda",
    "error": "#f8d7da",
    "advertencia": "#fff3cd",
    "readonly": "#e9ecef",
    "blanco": "white",
}

# Tipos de campo y sus validadores
VALIDATORS = {
    "text": lambda v: (True, None) if v else (False, "Requerido"),
    "number": lambda v: (
        (True, None) if re.match(r"^-?\d+\.?\d*$", v.replace(",", "")) else
        (False, "Solo numeros")
    ),
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
    "percent": lambda v: (
        (True, None) if re.match(r"^\d+(\.\d+)?$", v) and 0 <= float(v) <= 100 else
        (False, "Numero entre 0 y 100")
    ),
}


class FormField:
    """Campo de formulario con validacion en tiempo real."""
    def __init__(self, parent, label, tipo="text", valor="", placeholder="",
                 on_change=None, ancho=30, requerido=True):
        self.tipo = tipo
        self.validador = VALIDATORS.get(tipo, VALIDATORS["text"])
        self.requerido = requerido
        self.on_change = on_change
        self._error_msg = None

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
            self._error_msg = None
        else:
            self.entry.config(background=COLORES["error"])
            self.status_label.config(text=error, foreground="red")
            self._error_msg = error
        if self.on_change:
            self.on_change(v, ok)
        return ok

    def validate(self):
        return self._validate()


class FormularioFactura(tk.Toplevel):
    """Formulario validado para nueva factura."""
    def __init__(self, parent, on_submit=None, datos_extraidos=None,
                 aplicar_iva=True):
        super().__init__(parent)
        self.title("Nueva Factura - Validada")
        self.geometry("780x750")
        self.on_submit = on_submit
        self.datos = datos_extraidos or {}
        self.aplicar_iva_default = aplicar_iva

        self._build_ui()
        if self.datos:
            self._poblar_datos()

    def _build_ui(self):
        # Banner superior con info de carga
        banner = ttk.Frame(self, relief="sunken")
        banner.pack(fill="x", padx=10, pady=5)
        if self.datos.get("confianza_extraccion"):
            c = self.datos["confianza_extraccion"]
            color = "green" if c >= 70 else ("orange" if c >= 40 else "red")
            ttk.Label(banner, text=f"OCR con {c}% de confianza. Verifica los datos antes de guardar.",
                      foreground=color).pack(padx=5, pady=3)

        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        scrollbar.pack(side="right", fill="y")

        # === Seccion 1: Identificacion ===
        sec1 = ttk.LabelFrame(scroll_frame, text="Identificacion de la Factura")
        sec1.pack(fill="x", padx=5, pady=5)
        self.f_numero = FormField(sec1, "N Factura", "text",
                                   placeholder="F-2026-001")
        self.f_fecha_emision = FormField(sec1, "Fecha Emision", "date",
                                         placeholder="DD/MM/YYYY")
        self.f_fecha_recepcion = FormField(sec1, "Fecha Recepcion", "date",
                                            placeholder="DD/MM/YYYY")
        self.f_numero_control = FormField(sec1, "N Control", "text",
                                          requerido=False)

        # === Seccion 2: Proveedor ===
        sec2 = ttk.LabelFrame(scroll_frame, text="Proveedor")
        sec2.pack(fill="x", padx=5, pady=5)
        self.f_proveedor = FormField(sec2, "Nombre", "text",
                                     placeholder="Distribuidora XYZ")
        self.f_rif = FormField(sec2, "RIF", "rif", placeholder="J-12345678-9")
        self.f_direccion = FormField(sec2, "Direccion", "text", requerido=False)
        self.f_telefono = FormField(sec2, "Telefono", "text", requerido=False)
        self.f_email = FormField(sec2, "Email", "text", requerido=False)

        # === Seccion 3: Montos ===
        sec3 = ttk.LabelFrame(scroll_frame, text="Montos (en Bolivares)")
        sec3.pack(fill="x", padx=5, pady=5)
        self.f_subtotal = FormField(sec3, "Subtotal", "money",
                                    on_change=self._on_subtotal_change)
        self.f_iva = FormField(sec3, "IVA 16%", "money")
        self.f_total = FormField(sec3, "Total", "money",
                                 on_change=self._on_total_change)

        # === Seccion 4: Retencion ===
        sec4 = ttk.LabelFrame(scroll_frame, text="Retencion (segun reglas SENIAT)")
        sec4.pack(fill="x", padx=5, pady=5)
        self.f_aplica_iva = tk.BooleanVar(value=self.aplicar_iva_default)
        ttk.Checkbutton(sec4, text="Aplica retencion IVA 75%",
                        variable=self.f_aplica_iva,
                        command=self._recalc_retencion).pack(anchor="w")
        self.f_aplica_islr = tk.BooleanVar(value=False)
        ttk.Checkbutton(sec4, text="Aplica retencion ISLR",
                        variable=self.f_aplica_islr,
                        command=self._recalc_retencion).pack(anchor="w")
        # Frame para alicuota ISLR
        islr_frame = ttk.Frame(sec4)
        islr_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(islr_frame, text="Alicuota ISLR %:", width=18).pack(side="left")
        self.f_alicuota_islr = ttk.Combobox(islr_frame, values=["0", "2", "3", "5", "10", "12", "100"],
                                              width=8, state="readonly")
        self.f_alicuota_islr.set("2")
        self.f_alicuota_islr.pack(side="left", padx=5)
        self.f_alicuota_islr.bind("<<ComboboxSelected>>", lambda e: self._recalc_retencion())

        self.f_monto_retencion = FormField(sec4, "Monto Total Retenido", "money",
                                            requerido=False,
                                            on_change=lambda *_: None)
        self.f_total_neto = FormField(sec4, "Total a Pagar (Neto)", "money",
                                      requerido=False)

        # Resumen
        self.resumen = ttk.Label(scroll_frame, text="", foreground="gray")
        self.resumen.pack(fill="x", padx=10, pady=5)

        # Botones
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Validar Todo",
                   command=self._validar_todo).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Guardar y Generar Comprobante",
                   command=self._on_submit).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Cancelar",
                   command=self.destroy).pack(side="right", padx=2)

        self.campos_requeridos = [
            self.f_numero, self.f_fecha_emision, self.f_proveedor,
            self.f_rif, self.f_subtotal, self.f_iva, self.f_total
        ]

    def _poblar_datos(self):
        """Llena el form con datos extraidos."""
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
        for key_dato, attr_campo in mapeo.items():
            if self.datos.get(key_dato):
                getattr(self, attr_campo).set(self.datos[key_dato])
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
        """Calcula la retencion segun los checkboxes."""
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
            alicuota = float(self.f_alicuota_islr.get())
            retencion += base * (alicuota / 100)
        self.f_monto_retencion.set(f"{retencion:.2f}" if retencion else "")
        neto = total - retencion
        self.f_total_neto.set(f"{neto:.2f}" if neto else "")

    def _validar_todo(self):
        errores = []
        for campo in self.campos_requeridos:
            if not campo.validate():
                errores.append(f"Campo invalido o vacio")
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
            self.resumen.config(
                text=f"{len(errores)} error(es): {'; '.join(errores[:3])}",
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
                                    "Guardar esta factura y generar comprobante de retencion?"):
            return
        datos = {
            "numero_factura": self.f_numero.get(),
            "fecha_emision": self.f_fecha_emision.get(),
            "fecha_recepcion": self.f_fecha_recepcion.get() or self.f_fecha_emision.get(),
            "numero_control": self.f_numero_control.get(),
            "proveedor": self.f_proveedor.get(),
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
    """Ventana principal de AI Office Bridge."""
    def __init__(self):
        super().__init__()
        self.title("AI Office Bridge - Suite Administrativa con IA")
        self.geometry("1200x750")
        self.minsize(1000, 600)

        self.config = self._load_config()
        self.archivo_actual = None
        self.libro_compras_actual = None
        self.datos_extraidos = None

        self._setup_style()
        self._build_ui()

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
        # Topbar
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=5)
        ttk.Button(top, text="Abrir archivo",
                   command=self._abrir_archivo).pack(side="left", padx=2)
        ttk.Button(top, text="Cargar Factura (OCR)",
                   command=self._cargar_factura).pack(side="left", padx=2)
        ttk.Button(top, text="Nueva Factura Manual",
                   command=self._nueva_factura).pack(side="left", padx=2)
        ttk.Button(top, text="Guardar en Libro",
                   command=self._guardar_en_libro).pack(side="left", padx=2)
        ttk.Button(top, text="Configuracion",
                   command=self._settings).pack(side="right")

        self.file_label = ttk.Label(self, text="Sin archivo abierto", foreground="gray")
        self.file_label.pack(anchor="w", padx=15)

        # Main paned
        main = ttk.PanedWindow(self, orient="horizontal")
        main.pack(fill="both", expand=True, padx=10, pady=5)

        # Left: log
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
        ttk.Button(btn_frame, text="Probar Dicto",
                   command=self._probar_dicto).pack(side="left", padx=2)

        # Right: preview
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

        # Status
        self.status = ttk.Label(self, text="Listo. Carga una factura o abre un archivo Excel.",
                                relief="sunken", anchor="w")
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
            title="Abrir archivo Excel (libro de compras, comprobante, etc)",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")])
        if not path:
            return
        self.archivo_actual = Path(path)
        self.file_label.config(text=f"Archivo: {self.archivo_actual.name}")
        self._log(f"Archivo abierto: {self.archivo_actual.name}", "ok")
        self._show_preview()

    def _cargar_factura(self):
        """Carga factura (PDF o imagen) y extrae datos con OCR."""
        path = filedialog.askopenfilename(
            title="Cargar factura (PDF o imagen)",
            filetypes=[
                ("Imagen", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("PDF", "*.pdf"),
                ("Todos", "*.*")
            ])
        if not path:
            return
        self._log(f"Cargando factura: {Path(path).name}...", "info")
        self._set_status("Extrayendo datos con MiniMax Vision...")
        self.update_idletasks()

        # Extraer datos
        try:
            datos = extract_from_file(Path(path))
        except Exception as e:
            self._log(f"Error en extraccion: {e}", "error")
            messagebox.showerror("Error", f"No se pudo procesar: {e}")
            return

        if "error" in datos:
            self._log(f"Error: {datos['error']}", "error")
            messagebox.showerror("Error", datos["error"])
            return

        self.datos_extraidos = datos
        self._log(f"Datos extraidos con {datos.get('confianza_extraccion', '?')}% confianza", "ok")
        self._log(f"  N Factura: {datos.get('numero_factura', 'N/A')}", "ai")
        self._log(f"  Proveedor: {datos.get('nombre_proveedor', 'N/A')}", "ai")
        self._log(f"  RIF: {datos.get('rif_proveedor', 'N/A')}", "ai")
        self._log(f"  Total: {datos.get('total', 'N/A')}", "ai")

        # Mostrar preview de los datos extraidos
        self.preview.config(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", json.dumps(datos, indent=2, ensure_ascii=False))
        self.preview.config(state="disabled")

        # Abrir formulario pre-llenado
        aplicar_iva = datos.get('aplica_retencion_iva', True)
        form = FormularioFactura(self, on_submit=self._on_factura_guardada,
                                  datos_extraidos=datos, aplicar_iva=aplicar_iva)
        self._log("Abriendo formulario pre-llenado para tu revision...", "info")

    def _nueva_factura(self):
        if not self.archivo_actual:
            messagebox.showwarning("Sin archivo",
                                    "Primero abre un archivo Excel (libro de compras).")
            return
        form = FormularioFactura(self, on_submit=self._on_factura_guardada)
        self._log("Abriendo formulario de nueva factura...", "info")

    def _on_factura_guardada(self, datos):
        """Callback cuando el form guarda una factura."""
        self._log(f"Factura guardada: {datos['numero_factura']} - {datos['proveedor']}", "ok")
        self._log(f"  Total: Bs. {datos['total']}", "info")
        self._log(f"  Retencion: Bs. {datos['monto_retencion']}", "info")
        self._log(f"  Total a Pagar (Neto): Bs. {datos['total_neto']}", "info")

        # Guardar en archivo temporal
        self.datos_extraidos = datos
        self._set_status(f"Factura {datos['numero_factura']} validada. Click 'Guardar en Libro' para escribir al Excel.")

    def _guardar_en_libro(self):
        """Guarda la factura actual en el libro de compras + genera comprobante."""
        if not self.datos_extraidos:
            messagebox.showwarning("Sin datos",
                                    "No hay factura cargada. Carga una primero.")
            return
        if not self.archivo_actual:
            messagebox.showwarning("Sin archivo",
                                    "Abre un archivo Excel primero.")
            return

        datos = self.datos_extraidos
        output_dir = self.archivo_actual.parent / "generados"
        output_dir.mkdir(exist_ok=True)

        # 1. Agregar al libro de compras
        self._log(f"Agregando al libro de compras: {self.archivo_actual.name}...", "info")
        self._set_status("Escribiendo al libro de compras...")
        self.update_idletasks()
        ok = agregar_a_libro_compras(datos, self.archivo_actual)
        if ok:
            self._log("Factura agregada al libro de compras", "ok")
        else:
            self._log("No se pudo agregar al libro", "warn")

        # 2. Generar comprobante de retencion IVA si aplica
        if datos.get('aplica_retencion_iva') or datos.get('monto_retencion'):
            self._log("Generando comprobante de retencion IVA...", "info")
            self._set_status("Generando comprobante IVA...")
            self.update_idletasks()
            archivo_iva = crear_comprobante_iva(datos, output_dir)
            if archivo_iva:
                self._log(f"Comprobante IVA creado: {archivo_iva.name}", "ok")
                messagebox.showinfo("Exito",
                                    f"Comprobante creado en:\n{archivo_iva}")
            else:
                self._log("No se pudo crear comprobante IVA", "warn")

        # 3. Generar comprobante ISLR si aplica
        if datos.get('aplica_retencion_islr') or datos.get('porcentaje_islr_retenido'):
            self._log("Generando comprobante de retencion ISLR...", "info")
            self._set_status("Generando comprobante ISLR...")
            self.update_idletasks()
            archivo_islr = crear_comprobante_islr(datos, output_dir)
            if archivo_islr:
                self._log(f"Comprobante ISLR creado: {archivo_islr.name}", "ok")

        self._set_status(f"Procesado: {datos['numero_factura']} - {datos['proveedor']}")
        messagebox.showinfo("Listo",
                            f"Factura procesada. Comprobantes en:\n{output_dir}")

    def _show_preview(self):
        if not self.archivo_actual or not self.archivo_actual.exists():
            return
        try:
            result = subprocess.run(
                ["C:\\Program Files\\GridCraft\\gridcraft-cli.exe", "info",
                 str(self.archivo_actual)],
                capture_output=True, text=True, timeout=10
            )
            self.preview.config(state="normal")
            self.preview.delete("1.0", "end")
            self.preview.insert("1.0", result.stdout[:5000])
            self.preview.config(state="disabled")
        except Exception as e:
            self._log(f"Error leyendo archivo: {e}", "error")

    def _settings(self):
        has_key = bool(self.config.get("minimax_api_key"))
        messagebox.showinfo("Configuracion",
                            f"API key MiniMax: {'SI configurada' if has_key else 'NO configurada'}\n\n"
                            f"Ubicacion: {CONFIG_PATH}\n\n"
                            f"Templates: {TEMPLATES_DIR}")

    def _probar_dicto(self):
        self._log("Dicto sigue corriendo en background. Pulsa Alt Gr en cualquier app.", "info")
        self._log("Para usar Dicto aqui: click en un input, pulsa Alt Gr, habla, suelta.", "info")


def main():
    app = AIBridge()
    app.mainloop()


if __name__ == "__main__":
    main()
