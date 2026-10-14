"""
Motor de extraccion OCR usando MiniMax Vision.

Cuando hay internet: usa MiniMax Vision (alta precision).
Cuando no hay: usa pytesseract (OCR tradicional).
"""
import os
import sys
import json
import base64
import re
import requests
from pathlib import Path
from typing import Optional

API_KEY = os.environ.get("MINIMAX_API_KEY") or _load_key()
BASE_URL = "https://api.minimax.io/v1"
MODEL = "MiniMax-M3"

EXTRACTION_PROMPT = """Eres un asistente contable venezolano experto en facturas.

Analiza esta imagen de factura y extrae EXCLUSIVAMENTE un JSON con esta estructura.
NO incluyas explicaciones, solo el JSON.

{
  "numero_factura": "string",
  "fecha_emision": "DD/MM/YYYY",
  "fecha_recepcion": "DD/MM/YYYY",
  "nombre_proveedor": "string",
  "rif_proveedor": "J-12345678-9 o V-12345678-9 o E-12345678-9",
  "direccion_proveedor": "string",
  "telefono_proveedor": "string",
  "email_proveedor": "string (si esta visible)",
  "numero_control": "string (si esta visible)",
  "subtotal": numero_decimal,
  "iva": numero_decimal,
  "total": numero_decimal,
  "moneda": "Bs. o USD o EUR",
  "items": [
    {"cantidad": numero, "descripcion": "string", "precio_unitario": numero, "total": numero}
  ],
  "tipo_servicio": "bienes o servicios u honorarios u arrendamiento",
  "aplica_retencion_iva": true_o_false,
  "aplica_retencion_islr": true_o_false,
  "porcentaje_iva_retenido": numero (0, 75, 100),
  "porcentaje_islr_retenido": numero (0, 2, 3, 5, 10, 12, 100),
  "confianza_extraccion": numero_entre_0_y_100
}

Reglas:
- Si no puedes leer un campo, usa string vacio "" o null
- Fechas en formato DD/MM/YYYY
- Montos en numeros (sin puntos de miles, con punto decimal)
- El RIF venezolano tiene formato J-XXXXXXXX-X, V-XXXXXXXX, E-XXXXXXXX
- Si la factura es de BIENES, retencion IVA 75%
- Si es SERVICIOS, retencion IVA 75% o ISLR segun el caso
- Si son HONORARIOS PROFESIONALES, retencion ISLR 100% sobre base imponible
- Si es ARRENDAMIENTO, retencion ISLR 10% sobre la renta

Devuelve SOLO el JSON."""


def _load_key():
    """Carga API key de ~/.dictation_config.json"""
    cfg_path = Path.home() / ".dictation_config.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
            return cfg.get("minimax_api_key", "")
        except Exception:
            pass
    return ""


def encode_image(image_path: Path) -> str:
    """Convierte imagen a base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def compress_image(image_path: Path, max_size_mb: float = 2.0, max_dim: int = 1800) -> tuple[Path, bool]:
    """Comprime una imagen si es muy grande o pesada.

    Retorna (path_al_archivo_comprimido, fue_comprimido).
    Si no necesita compresion, retorna (path_original, False).
    """
    from PIL import Image
    file_size_mb = image_path.stat().st_size / (1024 * 1024)
    if file_size_mb <= max_size_mb:
        # Verificar tamano de pixeles
        try:
            with Image.open(image_path) as img:
                if max(img.size) <= max_dim:
                    return image_path, False
        except Exception:
            return image_path, False

    # Comprimir
    compressed_path = image_path.parent / f"{image_path.stem}_compressed.jpg"
    try:
        with Image.open(image_path) as img:
            # Convertir a RGB si es necesario
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            # Redimensionar si es muy grande
            if max(img.size) > max_dim:
                ratio = max_dim / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.LANCZOS)
            # Guardar como JPG comprimido
            quality = 85 if file_size_mb > 5 else 90
            img.save(compressed_path, "JPEG", quality=quality, optimize=True)
        new_size_mb = compressed_path.stat().st_size / (1024 * 1024)
        print(f"[OCR] Comprimida: {file_size_mb:.1f}MB -> {new_size_mb:.1f}MB")
        return compressed_path, True
    except Exception as e:
        print(f"[OCR] No se pudo comprimir: {e}")
        return image_path, False


def extract_with_minimax(image_path: Path) -> dict:
    """Extrae datos de factura usando MiniMax Vision con reintentos."""
    if not API_KEY:
        return {"error": "API key no configurada"}

    # Comprimir imagen si es muy grande (mas de 2MB)
    file_size_mb = image_path.stat().st_size / (1024 * 1024)
    print(f"[OCR] Imagen original: {file_size_mb:.2f}MB")
    if file_size_mb > 2:
        print("[OCR] Comprimiendo imagen...")
        image_path, was_compressed = compress_image(image_path, max_size_mb=2.0, max_dim=1800)

    img_b64 = encode_image(image_path)
    ext = image_path.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    data_url = f"data:{mime};base64,{img_b64}"
    b64_size_kb = len(img_b64) / 1024
    print(f"[OCR] Payload: {b64_size_kb:.0f}KB base64")
    print(f"[OCR] Enviando a MiniMax Vision...")

    # Reintentos con backoff
    max_retries = 3
    retry_delay = 5
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(
                f"{BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "user", "content": [
                            {"type": "text", "text": EXTRACTION_PROMPT},
                            {"type": "image_url", "image_url": {"url": data_url}}
                        ]}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                },
                timeout=60  # 60 segundos por intento
            )
            r.raise_for_status()
            content = r.json()["choices"][0]["message"]["content"].strip()
            # Limpiar thinking
            if "<think>" in content:
                end = content.find("</think>")
                if end != -1:
                    content = content[end + len("</think>"):].strip()
            # Extraer JSON
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                content = content[start:end]
            print(f"[OCR] Exito en intento {attempt}")
            return json.loads(content)
        except requests.Timeout:
            last_error = f"Timeout en intento {attempt}/{max_retries}"
            print(f"[OCR] {last_error}")
            if attempt < max_retries:
                import time as _t
                print(f"[OCR] Esperando {retry_delay}s antes de reintentar...")
                _t.sleep(retry_delay)
        except requests.ConnectionError as e:
            last_error = f"Sin conexion: {e}"
            print(f"[OCR] {last_error}")
            break  # No reintentar si no hay conexion
        except requests.HTTPError as e:
            last_error = f"Error HTTP {e.response.status_code}: {e.response.text[:200]}"
            print(f"[OCR] {last_error}")
            break
        except json.JSONDecodeError as e:
            return {"error": f"JSON invalido: {e}", "raw": content[:500] if 'content' in dir() else ''}
        except Exception as e:
            last_error = f"Error: {e}"
            print(f"[OCR] {last_error}")
            break
    return {"error": f"Fallaron {max_retries} intentos: {last_error}"}


def preprocess_image(image_path: Path) -> "Image.Image":
    """Preprocesa una imagen para mejorar la calidad del OCR.

    Solo hace resize si la imagen es muy pequena.
    En Sandy Bridge (CPU lento) evitamos operaciones pesadas.
    """
    try:
        import cv2
        from PIL import Image
    except ImportError:
        from PIL import Image
        return Image.open(image_path)

    img_cv = cv2.imread(str(image_path))
    if img_cv is None:
        return Image.open(image_path)

    # Solo resize si es muy pequena
    h, w = img_cv.shape[:2]
    if max(h, w) < 1500:
        scale = 1500 / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        img_cv = cv2.resize(img_cv, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    # Convertir a escala de grises (operacion simple y rapida)
    if len(img_cv.shape) == 3:
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_cv

    # Binarizacion Otsu (operacion simple, no pesada)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return Image.fromarray(binary)


def extract_with_tesseract(image_path: Path) -> dict:
    """OCR con tesseract (idioma espanol) + preprocesamiento."""
    import os

    # Configurar la ruta al ejecutable de tesseract
    tesseract_paths = [
        Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
        Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
        Path("C:/Users/USUARIO/AppData/Local/Programs/Tesseract-OCR/tesseract.exe"),
    ]
    tesseract_exe = None
    for p in tesseract_paths:
        if p.exists():
            tesseract_exe = str(p)
            break
    if not tesseract_exe:
        return {"error": "tesseract.exe no encontrado. Instala tesseract."}

    # Configurar TESSDATA_PREFIX
    if "TESSDATA_PREFIX" not in os.environ:
        candidates = [
            Path("C:/Users/USUARIO/.tessdata"),
            Path("C:/Program Files/Tesseract-OCR/tessdata"),
            Path("C:/Program Files (x86)/Tesseract-OCR/tessdata"),
        ]
        for c in candidates:
            if (c / "spa.traineddata").exists():
                os.environ["TESSDATA_PREFIX"] = str(c) + "/"
                break

    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return {"error": "pytesseract o Pillow no instalado"}

    pytesseract.pytesseract.tesseract_cmd = tesseract_exe

    # Preprocesar la imagen (mejora MUCHO la calidad del OCR)
    try:
        img_processed = preprocess_image(image_path)
    except Exception:
        from PIL import Image
        img_processed = Image.open(image_path)

    # Tesseract con parametros optimizados para facturas
    configs = [
        "--oem 3 --psm 6",  # LSTM engine, block of text
        "--oem 3 --psm 4",  # LSTM, single column
        "--oem 3 --psm 3",  # LSTM, fully automatic
    ]
    texto = ""
    for cfg in configs:
        try:
            t = pytesseract.image_to_string(img_processed, lang="spa", config=cfg)
            if len(t) > len(texto):
                texto = t
        except Exception:
            continue
    if not texto:
        try:
            texto = pytesseract.image_to_string(img_processed, lang="spa")
        except Exception as e:
            return {"error": f"Error tesseract: {e}"}
    return _parse_text_fallback(texto)


def _parse_text_fallback(texto: str) -> dict:
    """Parsea texto OCR con regex para extraer campos basicos."""
    datos = {
        "numero_factura": "",
        "fecha_emision": "",
        "fecha_recepcion": "",
        "nombre_proveedor": "",
        "rif_proveedor": "",
        "subtotal": 0.0,
        "iva": 0.0,
        "total": 0.0,
        "items": [],
        "confianza_extraccion": 30,  # Bajo porque es OCR
        "metodo_extraccion": "tesseract",
    }
    if not texto:
        return datos
    # RIF
    m = re.search(r"([JVE])-(\d{8})-(\d)", texto, re.IGNORECASE)
    if m:
        datos["rif_proveedor"] = f"{m.group(1).upper()}-{m.group(2)}-{m.group(3)}"
    # Fechas
    fechas = re.findall(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", texto)
    if fechas:
        datos["fecha_emision"] = fechas[0].replace("-", "/")
        if len(fechas) > 1:
            datos["fecha_recepcion"] = fechas[1].replace("-", "/")
    # Numero de factura (busca FACTURA, NRO, etc.)
    m = re.search(r"(?:factura|nro|n[uú]mero)[\s#:]*([A-Z0-9-]{4,20})",
                  texto, re.IGNORECASE)
    if m:
        datos["numero_factura"] = m.group(1).strip()
    # Subtotal, IVA, Total
    for campo, patron in [
        ("subtotal", r"subtotal[\s:]*\$?\s*([\d.,]+)"),
        ("iva", r"i\.?v\.?a\.?\s*[\d]*%?[\s:]*\$?\s*([\d.,]+)"),
        ("total", r"total[\s:]*\$?\s*([\d.,]+)"),
    ]:
        m = re.search(patron, texto, re.IGNORECASE)
        if m:
            try:
                val = m.group(1).replace(".", "").replace(",", ".")
                datos[campo] = float(val)
            except ValueError:
                pass
    return datos


def extract_from_file(file_path: Path) -> dict:
    """Extrae datos de un archivo. Usa MiniMax primero, fallback a tesseract."""
    if not file_path.exists():
        return {"error": "Archivo no existe", "metodo_extraccion": "ninguno"}
    # Detectar si es PDF
    if file_path.suffix.lower() == ".pdf":
        return _extract_from_pdf(file_path)
    # Intentar MiniMax primero
    if API_KEY:
        try:
            resultado = extract_with_minimax(file_path)
            if "error" not in resultado and resultado.get("numero_factura"):
                return resultado
            print(f"[OCR] MiniMax no dio datos validos: {resultado.get('error', '?')}")
        except Exception as e:
            print(f"[OCR] Excepcion en MiniMax: {e}")
    # Fallback a tesseract (siempre funciona si esta instalado)
    print("[OCR] Usando tesseract (OCR local)...")
    try:
        tesseract_result = extract_with_tesseract(file_path)
        tesseract_result["metodo_extraccion"] = "tesseract"
        tesseract_result["confianza_extraccion"] = 30
        tesseract_result["nota"] = "OCR local. Verifica los datos manualmente."
        return tesseract_result
    except Exception as e:
        return {"error": f"MiniMax y tesseract fallaron: {e}",
                "metodo_extraccion": "ninguno"}


def _extract_from_pdf(pdf_path: Path) -> dict:
    """Extrae texto de PDF primero, luego envia a MiniMax."""
    try:
        import pdfplumber
    except ImportError:
        return {"error": "pdfplumber no instalado"}
    texto = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            texto += page.extract_text() or ""
    if not texto.strip():
        return {"error": "PDF sin texto extraible, requiere OCR de imagen"}
    # Si hay texto, parsear con regex
    return _parse_text_fallback(texto)
