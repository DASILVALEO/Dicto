"""Genera screenshots de muestra del overlay de Dicto en distintos estados."""
from PIL import Image, ImageDraw, ImageFont
import os
import math

OUT = r"C:\Users\USUARIO\Desktop\app\consultas\voz-a-texto\docs"
os.makedirs(OUT, exist_ok=True)

BG = (245, 247, 250)
WINDOW = (255, 255, 255)
TEXT_DARK = (30, 30, 40)
TEXT_GRAY = (110, 115, 125)
ACCENT = (59, 130, 246)
GREEN = (34, 197, 94)
GREEN_LIGHT = (134, 239, 172)
RED = (239, 68, 68)
ORANGE = (251, 146, 60)
BORDER = (210, 215, 220)


def font(size, bold=False, mono=False):
    candidates = [
        (r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf", "normal"),
        (r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf", "normal"),
        (r"C:\Windows\Fonts\consolab.ttf" if bold and mono else (r"C:\Windows\Fonts\consola.ttf" if mono else None), "mono"),
    ]
    for path, _ in candidates:
        if path and os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def make_word_window(w, h, title="Microsoft Word - Propuesta comercial.docx"):
    """Crea una ventana tipo Word con contenido."""
    img = Image.new("RGB", (w, h), WINDOW)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 30], fill=(243, 243, 248))
    d.text((12, 8), title, fill=TEXT_DARK, font=font(12))
    d.text((w - 50, 8), "_  □  ×", fill=TEXT_GRAY, font=font(11))
    d.rectangle([0, 30, w, 56], fill=(248, 248, 252))
    d.line([0, 56, w, 56], fill=BORDER, width=1)
    # Ribbon icons (decorative)
    for x in [60, 100, 140, 180, 220, 260, 300, 340, 380, 420]:
        d.rectangle([x, 35, x + 22, 51], fill=(230, 235, 240))
    return img


def make_chrome_window(w, h, title="Gmail - Bandeja de entrada"):
    img = Image.new("RGB", (w, h), WINDOW)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 28], fill=(255, 255, 255))
    d.text((12, 7), title, fill=TEXT_DARK, font=font(11))
    d.text((w - 80, 7), "_  □  ×", fill=TEXT_GRAY, font=font(11))
    # Tabs
    d.rectangle([20, 32, 200, 56], fill=(245, 245, 245), outline=BORDER)
    d.text((30, 39), "Bandeja de entrada", fill=TEXT_DARK, font=font(10))
    return img


def make_excel_window(w, h, title="Excel - Presupuesto 2026.xlsx"):
    img = Image.new("RGB", (w, h), WINDOW)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 28], fill=(243, 243, 248))
    d.text((12, 6), title, fill=TEXT_DARK, font=font(11))
    # Column headers
    for col, x in enumerate(["A", "B", "C", "D", "E", "F", "G"]):
        d.rectangle([40 + col * 80, 30, 40 + col * 80 + 80, 50], fill=(220, 230, 240), outline=BORDER)
        d.text((48 + col * 80, 35), col_letter := x, fill=TEXT_DARK, font=font(10, bold=True))
    return img


def make_vscode_window(w, h, title="VS Code - main.py"):
    img = Image.new("RGB", (w, h), (30, 30, 30))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 30], fill=(43, 43, 43))
    d.text((12, 7), title, fill=(220, 220, 220), font=font(11))
    # Activity bar
    d.rectangle([0, 30, 40, h], fill=(33, 33, 33))
    return img


def draw_desktop_bg(w, h):
    """Fondo de escritorio azul oscuro (Windows 10 default)."""
    img = Image.new("RGB", (w, h), (32, 32, 40))
    d = ImageDraw.Draw(img)
    # Logo de Windows 10 centrado
    cx, cy = w // 2, h // 2
    # 4 cuadrados tipo Windows 10
    s = 50
    gap = 10
    for row in range(2):
        for col in range(2):
            x = cx - s - gap // 2 + col * (s + gap)
            y = cy - s - gap // 2 + row * (s + gap)
            d.rectangle([x, y, x + s, y + s], fill=(120, 150, 180))
    return img


def draw_overlay(img, x, y, w=300, h=50, state="recording", elapsed_s=0, level_bars=None):
    """Dibuja overlay transparente encima de img."""
    if level_bars is None:
        level_bars = [0.3] * 20
    d = ImageDraw.Draw(img)
    if state == "recording":
        color = GREEN
    elif state == "processing":
        color = ORANGE
    else:
        color = GREEN

    # Cronometro
    d.text((x + 14, y + 14), f"{elapsed_s}s", fill=color, font=font(18, bold=True))
    # VU bars
    bx0 = x + 58
    by1 = y + h - 8
    n = len(level_bars)
    bar_w = (w - 70) / n
    for i, lv in enumerate(level_bars):
        bx = bx0 + i * bar_w
        bh = max(2, int(lv * (h - 18)))
        by = by1 - bh
        c = GREEN_LIGHT if lv > 0.5 else color
        d.rectangle([bx, by, bx + bar_w - 1, by1], fill=c)
    return img


# ====== SCREENSHOT 1: Word + overlay Grabando ======
W, H = 1100, 700
img = draw_desktop_bg(W, H)
# Word window
word = make_word_window(800, 500)
img.paste(word, (100, 100))
# Texto del documento
d = ImageDraw.Draw(img)
doc_text = [
    "Esta es una reunion muy importante porque tenemos que discutir",
    "el nuevo proyecto del cliente. La fecha de entrega es el 15 de",
    "marzo y necesitamos coordinar con todos los miembros del equipo",
    "para entregar un producto de calidad. Tambien debemos considerar",
    "el presupuesto y los recursos disponibles. Es fundamental",
    "",
]
y = 90
for line in doc_text:
    d.text((130, y), line, fill=TEXT_DARK, font=font(15, mono=True))
    y += 25
# Cursor parpadeante
d.rectangle([130, y, 132, y + 22], fill=TEXT_DARK)
# Overlay en "Grabando" con VU bars animado
import random
random.seed(42)
bars = [0.4 + 0.5 * math.sin(i * 0.5) + random.uniform(-0.1, 0.1) for i in range(20)]
bars = [max(0.1, min(1.0, b)) for b in bars]
img = draw_overlay(img, 400, 30, state="recording", elapsed_s=2, level_bars=bars)
# Title
d.text((20, 660), "App destino: Microsoft Word - cursor listo, dictando", fill=(200, 200, 210), font=font(12))
img.save(os.path.join(OUT, "screenshot-1-grabando-word.png"))
print("OK 1: Grabando en Word")

# ====== SCREENSHOT 2: Word + overlay Transcribiendo ======
img = draw_desktop_bg(W, H)
word = make_word_window(800, 500)
img.paste(word, (100, 100))
d = ImageDraw.Draw(img)
for i, line in enumerate(doc_text):
    d.text((130, 90 + i * 25), line, fill=TEXT_DARK, font=font(15, mono=True))
# Cursor
d.rectangle([130, 90 + len(doc_text) * 25, 132, 90 + len(doc_text) * 25 + 22], fill=TEXT_DARK)
# Overlay procesando
img = draw_overlay(img, 400, 30, state="processing", elapsed_s=1, level_bars=[0.3]*20)
d.text((20, 660), "Audio enviado a MiniMax/IA - transcribiendo en la nube", fill=(200, 200, 210), font=font(12))
img.save(os.path.join(OUT, "screenshot-2-procesando.png"))
print("OK 2: Procesando")

# ====== SCREENSHOT 3: Word + OK + texto nuevo pegado ======
img = draw_desktop_bg(W, H)
word = make_word_window(800, 500)
img.paste(word, (100, 100))
d = ImageDraw.Draw(img)
# Texto previo
for i, line in enumerate(doc_text):
    d.text((130, 90 + i * 25), line, fill=TEXT_DARK, font=font(15, mono=True))
# Texto NUEVO transcrito (resaltado)
new_line = "mantener comunicacion fluida durante todo el proceso."
d.text((130, 90 + 6 * 25), new_line, fill=ACCENT, font=font(15, mono=True))
# Cursor al final del texto
cursor_x = 130 + 480
cursor_y = 90 + 6 * 25
d.rectangle([cursor_x, cursor_y, cursor_x + 2, cursor_y + 22], fill=ACCENT)
# Overlay "OK"
img = draw_overlay(img, 400, 30, state="done", elapsed_s=3)
# Cambiar texto a "OK"
d = ImageDraw.Draw(img)
d.rectangle([400, 30, 700, 80], fill=(0, 0, 0, 0))  # limpiar
d.text((400 + 14, 30 + 14), "OK", fill=GREEN, font=font(18, bold=True))
# VU bars bajar
for i in range(20):
    bx = 400 + 58 + i * ((300 - 70) / 20)
    d.rectangle([bx, 30 + 32, bx + ((300-70)/20) - 1, 30 + 50], fill=GREEN)
# Texto contextual
d.text((20, 660), "Texto transcrito y pegado en el cursor - la app destino recibio el texto", fill=(200, 200, 210), font=font(12))
img.save(os.path.join(OUT, "screenshot-3-resultado.png"))
print("OK 3: Resultado")

# ====== SCREENSHOT 4: Multiples apps con overlay (showcase) ======
W2, H2 = 1200, 750
img = draw_desktop_bg(W2, H2)
# Chrome a la izquierda
chrome = make_chrome_window(550, 450)
img.paste(chrome, (30, 200))
d = ImageDraw.Draw(img)
# Contenido del email
d.text((50, 230), "Para: cliente@empresa.com", fill=TEXT_DARK, font=font(11, mono=True))
d.text((50, 250), "Asunto: Propuesta actualizada", fill=TEXT_DARK, font=font(11, mono=True, bold=True))
d.text((50, 275), "", fill=TEXT_DARK, font=font(11))
email_lines = [
    "Estimado cliente,",
    "",
    "Le adjunto la propuesta actualizada con los ajustes que",
    "conversamos ayer. Quedo atento a sus comentarios.",
    "",
    "Saludos cordiales,",
]
y2 = 295
for line in email_lines:
    d.text((50, y2), line, fill=TEXT_DARK, font=font(11, mono=True))
    y2 += 20
# Cursor parpadeante
d.rectangle([50, y2, 52, y2 + 16], fill=TEXT_DARK)

# Word en el centro-derecha
word = make_word_window(550, 350)
img.paste(word, (620, 200))
d = ImageDraw.Draw(img)
d.text((640, 230), "Documento Word (proceso en paralelo)", fill=TEXT_GRAY, font=font(11))

# Excel abajo
excel = make_excel_window(450, 200)
img.paste(excel, (30, 530))

# VS Code a la derecha
vscode = make_vscode_window(550, 200)
img.paste(vscode, (620, 530))

# Overlay "Grabando" flotando en el centro-arriba
bars = [0.6, 0.7, 0.8, 0.6, 0.5, 0.7, 0.9, 0.7, 0.5, 0.4,
        0.6, 0.8, 0.9, 0.8, 0.6, 0.5, 0.7, 0.8, 0.6, 0.5]
img = draw_overlay(img, 450, 30, state="recording", elapsed_s=3, level_bars=bars)
d = ImageDraw.Draw(img)
# Etiquetas en cada ventana
d.text((50, 470), "Gmail", fill=ACCENT, font=font(14, bold=True))
d.text((640, 470), "Word", fill=ACCENT, font=font(14, bold=True))
d.text((50, 720), "Excel", fill=ACCENT, font=font(14, bold=True))
d.text((640, 720), "VS Code", fill=ACCENT, font=font(14, bold=True))
# Mensaje
d.text((20, 15), "Dicto dicta en cualquier app - mueve el cursor, pulsa Alt Gr, habla", fill=(200, 200, 210), font=font(13))
img.save(os.path.join(OUT, "screenshot-4-multi-app.png"))
print("OK 4: Multi-app showcase")

# Print sizes
import os
for f in sorted(os.listdir(OUT)):
    if f.startswith("screenshot"):
        size = os.path.getsize(os.path.join(OUT, f)) / 1024
        print(f"  {f}: {size:.1f} KB")
