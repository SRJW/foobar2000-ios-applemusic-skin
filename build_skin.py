import os
import zipfile
from PIL import Image, ImageDraw, ImageFilter

OUT_DIR = "build"
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Crear fondo degradado estilo Apple Music (1800x4000)
bg = Image.new("RGBA", (1800, 4000), (28, 28, 30, 255))
draw_bg = ImageDraw.Draw(bg)
for y in range(4000):
    # Degradado suave de tono rojizo/vino oscuro arriba hacia gris carbón/negro abajo
    r = int(75 * (1 - y / 4000) + 18 * (y / 4000))
    g = int(25 * (1 - y / 4000) + 18 * (y / 4000))
    b = int(40 * (1 - y / 4000) + 22 * (y / 4000))
    draw_bg.line([(0, y), (1800, y)], fill=(r, g, b, 255))
bg.save(f"{OUT_DIR}/bg.png")

# 2. Crear máscara de esquinas redondeadas para el Album Art (roundcover.png)
# Recorta visualmente las esquinas cuadradas del [albumart]
mask = Image.new("L", (1540, 1540), 255)
draw_mask = ImageDraw.Draw(mask)
draw_mask.rounded_rectangle([20, 20, 1520, 1520], radius=80, fill=0)

cover_overlay = Image.new("RGBA", (1540, 1540), (58, 22, 34, 0))
cover_overlay.save(f"{OUT_DIR}/roundcover.png")

# 3. Función auxiliar para crear iconos de reproducción limpios en blanco
def create_icon(name, size, draw_fn, alpha=255):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_fn(draw, size, (255, 255, 255, alpha))
    img.save(f"{OUT_DIR}/{name}.png")

# Play & Pause
create_icon("playNew", 340, lambda d, s, c: d.polygon([(95, 60), (95, 280), (275, 170)], fill=c))
create_icon("playNew-h", 340, lambda d, s, c: d.polygon([(95, 60), (95, 280), (275, 170)], fill=(255,255,255,140)))
create_icon("pauseNew", 340, lambda d, s, c: (d.rounded_rectangle([90, 65, 145, 275], radius=15, fill=c), d.rounded_rectangle([195, 65, 250, 275], radius=15, fill=c)))
create_icon("pauseNew-h", 340, lambda d, s, c: (d.rounded_rectangle([90, 65, 145, 275], radius=15, fill=(255,255,255,140)), d.rounded_rectangle([195, 65, 250, 275], radius=15, fill=(255,255,255,140))))

# Next & Prev (Doble triángulo estilo Apple Music)
def draw_next(d, s, c):
    d.polygon([(40, 80), (40, 220), (155, 150)], fill=c)
    d.polygon([(155, 80), (155, 220), (270, 150)], fill=c)
def draw_prev(d, s, c):
    d.polygon([(260, 80), (260, 220), (145, 150)], fill=c)
    d.polygon([(145, 80), (145, 220), (30, 150)], fill=c)

create_icon("skipnextNew", 300, draw_next)
create_icon("skipnextNew-h", 300, lambda d, s, c: draw_next(d, s, (255,255,255,140)))
create_icon("skipprevNew", 300, draw_prev)
create_icon("skipprevNew-h", 300, lambda d, s, c: draw_prev(d, s, (255,255,255,140)))

# Botón Menú (Círculo traslúcido con 3 puntos de iOS)
def draw_menu(d, s, c):
    d.ellipse([5, 5, s-5, s-5], fill=(255, 255, 255, 40))
    for cx in [42, 70, 98]:
        d.ellipse([cx-7, 63, cx+7, 77], fill=c)
create_icon("menu", 140, draw_menu)
create_icon("menu-h", 140, lambda d, s, c: draw_menu(d, s, (255,255,255,140)))

# Shuffle y Repeat (Indicadores minimalistas)
for btn in ["shuffle", "shuffle-h", "shuffled", "shuffled-h", "repeat", "repeat-h", "repeated", "repeated-h"]:
    is_active = "ed" in btn
    col = (250, 45, 72, 255) if is_active else (255, 255, 255, 160)
    img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([40, 85, 160, 115], radius=15, fill=col)
    img.save(f"{OUT_DIR}/{btn}.png")

# Barras de progreso y volumen (Tracks y Knobs)
track = Image.new("RGBA", (1500, 180), (0, 0, 0, 0))
ImageDraw.Draw(track).rounded_rectangle([0, 82, 1500, 98], radius=8, fill=(255, 255, 255, 60))
track.save(f"{OUT_DIR}/seek-track.png")

track_h = Image.new("RGBA", (1500, 180), (0, 0, 0, 0))
ImageDraw.Draw(track_h).rounded_rectangle([0, 82, 1500, 98], radius=8, fill=(255, 255, 255, 230))
track_h.save(f"{OUT_DIR}/seek-track-highlighted.png")

knob = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
ImageDraw.Draw(knob).ellipse([10, 10, 50, 50], fill=(255, 255, 255, 255))
knob.save(f"{OUT_DIR}/position-marker.png")
knob.save(f"{OUT_DIR}/volume-marker.png")

# Iconos requeridos por skindef
for ico in ["noart", "play", "pause", "iconadd2", "iconremove", "iconsliders", "iconspeaker", "iconlist", "iconfolder", "vol-min", "vol-max"]:
    im = Image.new("RGBA", (120, 120), (44, 44, 46, 255) if ico=="noart" else (0,0,0,0))
    im.save(f"{OUT_DIR}/{ico}.png")

# 4. Escribir archivos de configuración en UTF-16 LE (Con BOM ÿþ como en el archivo original)
skindef_content = """name: Apple Music (Dark)
author: Custom
version: 1.0
defaultart: noart.png
backgroundcol: 28,28,30
iconplay: play.png
iconpause: pause.png
iconadd: iconadd2.png
iconremove: iconremove.png
iconsliders: iconsliders.png
iconspeaker: iconspeaker.png
iconlist: iconlist.png
iconfolder: iconfolder.png

skin: 1800x4000 portrait-9-20-1800x4000.txt
skin: 2250x4000 portrait-9-20-1800x4000.txt
skin: 2500x4000 portrait-9-20-1800x4000.txt
skin: 2666x4000 portrait-9-20-1800x4000.txt
skin: 3000x4000 portrait-9-20-1800x4000.txt
"""

portrait_content = """[image]
bg.png
0,0,1800,4000

[button]
1520,220,140,140
menu
menu.png
menu-h.png
menu.png
menu-h.png

[albumart]
150,420,1500,1500
main

*if playing
[label]
150,2040,1500,130
left
[rgb-255-255-255][b][title][-b]

[label]
150,2175,1500,110
left
[rgb-235-235-245][artist]
*else
[label]
150,2040,1500,130
left
[rgb-255-255-255][b]Not Playing[-b]
*end

[position]
150,2360,1500,180
position-marker.png
seek-track.png
seek-track-highlighted.png

[label]
150,2530,600,80
left
[rgb-160-160-170][currentposition]

[label]
1050,2530,600,80
right
[rgb-160-160-170][length]

[button]
130,2820,200,200
shuffle
shuffle.png
shuffle-h.png
shuffled.png
shuffled-h.png

[button]
430,2770,300,300
skipback
skipprevNew.png
skipprevNew-h.png
skipprevNew.png
skipprevNew-h.png

[button]
750,2750,340,340
playnpause
playNew.png
playNew-h.png
pauseNew.png
pauseNew-h.png

[button]
1110,2770,300,300
skipnext
skipnextNew.png
skipnextNew-h.png
skipnextNew.png
skipnextNew-h.png

[button]
1470,2820,200,200
repeat
repeat.png
repeat-h.png
repeated.png
repeated-h.png

[volume]
220,3350,1360,180
volume-marker.png
seek-track.png
seek-track-highlighted.png

[label]
150,3680,1500,70
centered
[rgb-140-140-150]Lossless Audio • foobar2000
"""

with open(f"{OUT_DIR}/skindef.skindef", "w", encoding="utf-16") as f:
    f.write(skindef_content.replace("\n", "\r\n"))

with open(f"{OUT_DIR}/portrait-9-20-1800x4000.txt", "w", encoding="utf-16") as f:
    f.write(portrait_content.replace("\n", "\r\n"))

# 5. Empaquetar todo en AppleMusic.fbskin
with zipfile.ZipFile("AppleMusic.fbskin", "w", zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(OUT_DIR):
        for file in files:
            zf.write(os.path.join(root, file), arcname=file)

print("¡Skin compilado exitosamente como AppleMusic.fbskin!")
