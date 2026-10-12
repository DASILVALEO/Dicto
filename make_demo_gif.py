"""Crea un demo GIF animado de Dicto mostrando el flujo completo."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 900, 540
OUT_DIR = r"C:\Users\USUARIO\Desktop\app\consultas\voz-a-texto\docs"
os.makedirs(OUT_DIR, exist_ok=True)

# Colores
BG = (245, 247, 250)
WORD_BG = (255, 255, 255)
WORD_BORDER = (200, 200, 210)
TEXT_DARK = (40, 40, 50)
TEXT_GRAY = (120, 120, 130)
ACCENT = (59, 130, 246)  # azul Dicto
GREEN = (34, 197, 94)
RED = (239, 68, 68)
ORANGE = (251, 146, 60)


def make_window(width, height, title="Word - Mi documento"):
    """Crea una ventana tipo Word con toolbar."""
    img = Image.new("RGB", (width, height), WORD_BG)
    d = ImageDraw.Draw(img)
    # Title bar
    d.rectangle([0, 0, width, 32], fill=(240, 240, 245))
    d.text((12, 8), title, fill=TEXT_DARK, font=font_title(14))
    d.text((width - 60, 8), "_ □ ×", fill=TEXT_GRAY, font=font_title(12))
    # Toolbar
    d.rectangle([0, 32, width, 64], fill=(248, 248, 252))
    d.line([0, 64, width, 64], fill=WORD_BORDER, width=1)
    # Body line guides
    for y in range(80, height - 20, 28):
        d.line([80, y, width - 40, y], fill=(245, 245, 250), width=1)
    return img


def font_title(size):
    paths = [r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()


def font_mono(size):
    paths = [r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\cour.ttf"]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()


def font_bold(size):
    paths = [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()


def draw_overlay(img, x, y, state="recording", elapsed_s=0, level_bars=None):
    """Dibuja el overlay transparente sobre la imagen."""
    if level_bars is None:
        level_bars = [0.3] * 20
    d = ImageDraw.Draw(img)
    if state == "recording":
        color = GREEN
        text = f"Grabando...  {elapsed_s}s"
    elif state == "processing":
        color = ORANGE
        text = f"Transcribiendo...  {elapsed_s}s"
    elif state == "done":
        color = GREEN
        text = f"OK"
    else:
        return img

    w, h = 280, 50
    # Timer
    d.text((x + 14, y + 17), f"{elapsed_s}s", fill=color, font=font_bold(16))
    # VU bars
    bx0 = x + 56
    by1 = y + 42
    n = len(level_bars)
    bar_w = (w - 70) / n
    for i, lv in enumerate(level_bars):
        bx = bx0 + i * bar_w
        bh = max(2, int(lv * 22))
        by = by1 - bh
        c = (134, 239, 172) if lv > 0.5 else color
        d.rectangle([bx, by, bx + bar_w - 1, by1], fill=c)
    return img


# === Frame 1: Setup (Word abierto, cursor) ===
frames = []
f = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(f)
# Word window in background
word = make_window(800, 450)
f.paste(word, (50, 50))
# Cursor
d.text((150, 180), "Esta es una reunión muy importante porque tenemos que discutir", fill=TEXT_DARK, font=font_mono(14))
d.text((150, 215), "el nuevo proyecto del cliente. La fecha de entrega es el 15 de marzo", fill=TEXT_DARK, font=font_mono(14))
d.text((150, 250), "y necesitamos coordinar con todos los miembros del equipo para", fill=TEXT_DARK, font=font_mono(14))
d.text((150, 285), "entregar un producto de calidad. También debemos considerar el", fill=TEXT_DARK, font=font_mono(14))
d.text((150, 320), "presupuesto y los recursos disponibles. Es fundamental mantener", fill=TEXT_DARK, font=font_mono(14))
# Cursor blinking line
d.rectangle([152, 348, 154, 365], fill=TEXT_DARK)
d.text((150, 345), "_", fill=TEXT_DARK, font=font_mono(14))
# Title instruction
d.text((20, 510), "1. Usuario en Word, cursor listo para escribir", fill=TEXT_GRAY, font=font_title(13))
frames.append(f)

# === Frame 2: Pulsa Alt Gr, aparece overlay ===
f = frames[0].copy()
d = ImageDraw.Draw(f)
# Indicador de tecla pulsada
d.text((20, 510), "2. Pulsa Alt Gr (Alt derecha) — overlay aparece", fill=TEXT_GRAY, font=font_title(13))
# Overlay in top center
level_bars = [0.1] * 20
f = draw_overlay(f, 310, 70, state="recording", elapsed_s=0, level_bars=level_bars)
frames.append(f)

# === Frame 3-5: Grabando con barras moviendose (3 frames) ===
for i, sec in enumerate([1, 2, 3]):
    f = frames[1].copy()
    d = ImageDraw.Draw(f)
    d.text((20, 510), f"3. Hablando... ({sec}s) - VU meter en vivo", fill=TEXT_GRAY, font=font_title(13))
    # Bars variables
    import math, random
    random.seed(sec)
    bars = []
    for j in range(20):
        base = 0.4 + 0.5 * math.sin(sec + j * 0.3)
        bars.append(max(0.1, min(1.0, base + random.uniform(-0.2, 0.2))))
    f = draw_overlay(f, 310, 70, state="recording", elapsed_s=sec, level_bars=bars)
    frames.append(f)

# === Frame 6: Pulsa Alt Gr otra vez, transcribiendo ===
f = frames[4].copy()
d = ImageDraw.Draw(f)
d.text((20, 510), "4. Pulsa Alt Gr otra vez - transcribiendo...", fill=TEXT_GRAY, font=font_title(13))
f = draw_overlay(f, 310, 70, state="processing", elapsed_s=4, level_bars=[0.3]*20)
frames.append(f)

# === Frame 7: Transcripción aparece en Word ===
f = frames[5].copy()
d = ImageDraw.Draw(f)
# Texto nuevo en Word (typed)
new_lines = [
    "el nuevo proyecto del cliente. La fecha de entrega es el 15 de marzo",
    "y necesitamos coordinar con todos los miembros del equipo para",
    "entregar un producto de calidad. Tambien debemos considerar el",
    "presupuesto y los recursos disponibles. Es fundamental mantener",
    "_comunicación fluida durante todo el proceso de desarrollo.",
]
# Highlight the new line
d.rectangle([148, 343, 150, 365], fill=ACCENT)
d.text((150, 345), "comunicacion fluida durante todo el proceso de desarrollo,", fill=ACCENT, font=font_mono(14))
# Quitar la "_" que estaba antes
d.rectangle([148, 343, 156, 367], fill=WORD_BG)
d.text((150, 345), "comunicacion fluida durante todo el proceso de desarrollo,", fill=ACCENT, font=font_mono(14))
# Overlay OK
d.text((20, 510), "5. Texto transcrito y pegado donde estaba el cursor", fill=ACCENT, font=font_bold(13))
f = draw_overlay(f, 310, 70, state="done", elapsed_s=4)
frames.append(f)

# === Frame 8: Final state ===
f = frames[6].copy()
d = ImageDraw.Draw(f)
d.text((20, 510), "6. Listo. Sigue dictando o cierra Word.", fill=ACCENT, font=font_bold(13))
frames.append(f)

# Guardar GIF
out_path = os.path.join(OUT_DIR, "demo.gif")
durations = [1500, 800, 600, 600, 600, 1200, 1500, 2000]
frames[0].save(out_path, format="GIF", save_all=True, append_images=frames[1:],
               duration=durations, loop=0, optimize=True)
print(f"GIF guardado: {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")
