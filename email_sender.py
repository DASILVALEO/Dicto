"""
Email sender para comprobantes de retencion.
Usa SMTP (built-in) con soporte para adjuntos.
"""
import os
import json
import smtplib
import ssl
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List


CONFIG_PATH = Path.home() / ".dictation_email_config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
        except Exception:
            pass
    return {
        "smtp_server": "",
        "smtp_port": 587,
        "use_tls": True,
        "username": "",
        "password": "",
        "from_name": "Comprobante de Retencion",
        "default_cc": []
    }


def save_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def is_configured() -> bool:
    cfg = load_config()
    return all([cfg.get("smtp_server"), cfg.get("username"), cfg.get("password")])


def send_comprobante_email(comprobante_path: Path, datos: dict,
                          extra_attachments: List[Path] = None) -> tuple[bool, str]:
    """Envia el comprobante de retencion por email al proveedor.

    datos debe tener: email_proveedor, nombre_proveedor, numero_factura
    Retorna (ok, mensaje)
    """
    cfg = load_config()
    if not all([cfg.get("smtp_server"), cfg.get("username"), cfg.get("password")]):
        return False, "Email no configurado. Ve a Configuracion en la GUI."

    destinatario = datos.get("email_proveedor", "").strip()
    if not destinatario:
        return False, "El proveedor no tiene email. Agregalo en el catalogo."

    # Crear mensaje
    msg = MIMEMultipart()
    msg["From"] = f"{cfg['from_name']} <{cfg['username']}>"
    msg["To"] = destinatario
    msg["Subject"] = f"Comprobante de Retencion - {datos.get('nombre_proveedor', '')} - {datos.get('numero_factura', '')}"
    cc_list = cfg.get("default_cc", [])
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)

    # Cuerpo HTML
    monto = datos.get("monto_retencion", "0.00")
    total = datos.get("total", "0.00")
    neto = datos.get("total_neto", "0.00")
    body_html = f"""
<html>
<body>
<h2>Comprobante de Retencion</h2>
<p>Estimado(a) <b>{datos.get('nombre_proveedor', '')}</b>,</p>
<p>Adjunto encontrara el comprobante de retencion correspondiente a la factura
<b>{datos.get('numero_factura', '')}</b>.</p>

<table border="1" cellpadding="8" style="border-collapse: collapse;">
  <tr><th>Concepto</th><th>Monto (Bs.)</th></tr>
  <tr><td>Total Factura</td><td>{total}</td></tr>
  <tr><td>Monto Retenido</td><td>{monto}</td></tr>
  <tr><td>Total a Pagar (Neto)</td><td>{neto}</td></tr>
</table>

<p>Por favor confirmar la recepcion de este comprobante.</p>

<p>Saludos cordiales,<br>
{cfg['from_name']}</p>
</body>
</html>
"""
    msg.attach(MIMEText(body_html, "html"))

    # Adjuntar comprobante
    if comprobante_path.exists():
        with open(comprobante_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=comprobante_path.name)
        part["Content-Disposition"] = f'attachment; filename="{comprobante_path.name}"'
        msg.attach(part)

    # Adjuntos extra (ej. factura original)
    if extra_attachments:
        for att_path in extra_attachments:
            if att_path and att_path.exists():
                with open(att_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=att_path.name)
                    part["Content-Disposition"] = f'attachment; filename="{att_path.name}"'
                    msg.attach(part)

    # Enviar
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"], timeout=30) as server:
            if cfg.get("use_tls", True):
                server.starttls(context=context)
            server.login(cfg["username"], cfg["password"])
            recipients = [destinatario] + cc_list
            server.sendmail(cfg["username"], recipients, msg.as_string())
        return True, f"Email enviado a {destinatario}"
    except smtplib.SMTPAuthenticationError:
        return False, "Error de autenticacion SMTP. Verifica usuario y password."
    except smtplib.SMTPException as e:
        return False, f"Error SMTP: {e}"
    except Exception as e:
        return False, f"Error enviando email: {e}"


def send_test_email(to: str) -> tuple[bool, str]:
    """Envia email de prueba."""
    cfg = load_config()
    if not all([cfg.get("smtp_server"), cfg.get("username"), cfg.get("password")]):
        return False, "Email no configurado."

    msg = MIMEText("Este es un email de prueba desde AI Office Bridge. Si lo recibes, tu configuracion SMTP esta correcta.")
    msg["From"] = f"{cfg['from_name']} <{cfg['username']}>"
    msg["To"] = to
    msg["Subject"] = "Test - AI Office Bridge"

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(cfg["smtp_server"], cfg["smtp_port"], timeout=30) as server:
            if cfg.get("use_tls", True):
                server.starttls(context=context)
            server.login(cfg["username"], cfg["password"])
            server.sendmail(cfg["username"], [to], msg.as_string())
        return True, f"Email de prueba enviado a {to}"
    except Exception as e:
        return False, str(e)
