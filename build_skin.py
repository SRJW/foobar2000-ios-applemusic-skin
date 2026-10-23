import os
import zipfile
from PIL import Image, ImageDraw, ImageFilter

OUT_DIR = "build"
os.makedirs(OUT_DIR, exist_ok=True)

# 1. Crear un lienzo maestro de Fondo Estilo Apple Music "Mesh Blur" (2250x4000)
# Lo creamos a 2250 de ancho para que cubra cualquier proporción sin bordes blancos
master_bg = Image.new("RGBA", (2250, 4000), (18, 14, 26, 255))
blur_layer = Image.new("RGBA", (2250, 4000), (0, 0, 0, 0))
draw_blur = ImageDraw.Draw(blur_layer)

# Manchas de color vibrantes estilo Apple Music (Rojizo, Coral, Violeta, Azul profundo)
draw_blur.ellipse([-200, 100, 1200, 1600], fill=(195, 45, 65, 200))
draw_blur.ellipse([700, 300, 2100, 1800], fill=(130, 40, 145, 190))
draw_blur.ellipse([100, 1200, 1600, 2700], fill=(215, 70, 95, 150))
draw_blur.ellipse([-100, 2200, 1500, 3800], fill=(45, 30, 85, 220))

# Aplicar desenfoque gaussiano masivo para efecto iOS Blur
blur_layer = blur_layer.filter(ImageFilter.GaussianBlur(radius=240))
master_bg = Image.alpha_composite(master_bg, blur_layer)

# Oscurecer ligeramente la parte inferior para contraste de controles
overlay_grad = Image.new("RGBA", (2250, 4000), (0, 0, 0, 0))
draw_grad = ImageDraw.Draw(overlay_grad)
for y in range(4000):
    alpha = int(40 + 150 * (y / 4000) ** 1.5)
    draw_grad.line([(0, y), (2250, y)], fill=(12, 10, 18, alpha))
master_bg = Image.alpha_composite(master_bg, overlay_grad)

# 2. Función para generar el fondo y la máscara redondeada exacta para cada ancho de pantalla
def generate_layout_assets(width, suffix):
    # Recortar el fondo centrado al ancho exacto del layout
    x_offset = (2250 - width) // 2
    bg_cropped = master_bg.crop((x_offset, 0, x_offset + width, 4000)).copy()
    
    art_size = int(width * 0.82)
    art_x = (width - art_size) // 2
    art_y = 440

    # Dibujar sombra suave detrás de donde irá la carátula
    shadow = Image.new("RGBA", (width, 4000), (0, 0, 0, 0))
    d_sh = ImageDraw.Draw(shadow)
    d_sh.rounded_rectangle(
        [art_x - 10, art_y + 25, art_x + art_size + 10, art_y + art_size + 45],
        radius=90, fill=(0, 0, 0, 140)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=45))
    bg_with_shadow = Image.alpha_composite(bg_cropped, shadow)

    # Dibujar píldora superior de iOS (indicador de arrastrar) y textos decorativos
    d_ui = ImageDraw.Draw(bg_with_shadow)
    cx = width // 2
    d_ui.rounded_rectangle([cx - 90, 110, cx + 90, 132], radius=11, fill=(255, 255, 255, 90))
    
    # Botón izquierdo decorativo (flecha abajo en círculo translúcido)
    d_ui.ellipse([art_x, 190, art_x + 130, 320], fill=(255, 255, 255, 35))
    d_ui.line([(art_x + 42, 242), (art_x + 65, 268), (art_x + 88, 242)], fill=(255, 255, 255, 230), width=10)

    # Guardar el fondo completo
    bg_with_shadow.save(f"{OUT_DIR}/bg_{suffix}.png")

    # Crear la máscara de esquinas redondeadas (roundcover) tomando los píxeles exactos del fondo
    # Así las 4 esquinas exteriores tapan los picos cuadrados del [albumart] y el centro es transparente
    cover_patch = bg_cropped.crop((art_x, art_y, art_x + art_size, art_y + art_size)).copy()
    alpha_mask = Image.new("L", (art_size, art_size), 255) # 255 = opaco (tapa las esquinas)
    d_mask = ImageDraw.Draw(alpha_mask)
    # Hueco central transparente con bordes muy redondeados estilo Apple Music (radio 85px)
    d_mask.rounded_rectangle([0, 0, art_size, art_size], radius=85, fill=0)
    # Borde sutil brillante de 2px alrededor de la carátula
    cover_patch.putalpha(alpha_mask)
    d_border = ImageDraw.Draw(cover_patch)
    d_border.rounded_rectangle([1, 1, art_size - 2, art_size - 2], radius=85, outline=(255, 255, 255, 45), width=3)
    cover_patch.save(f"{OUT_DIR}/roundcover_{suffix}.png")

    return art_x, art_y, art_size

# 3. Crear los marcadores de barra (Knobs) SIN que se deformen
# El contenedor tiene 140px de alto; haciendo el PNG de 140x140 con un círculo pequeño en el centro evitamos que foobar lo estire
knob = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
d_knob = ImageDraw.Draw(knob)
d_knob.ellipse([42, 42, 98, 98], fill=(255, 255, 255, 255))
knob.save(f"{OUT_DIR}/position-marker.png")
knob.save(f"{OUT_DIR}/volume-marker.png")

# Barras (Track normal y Track relleno) de 140px de alto con línea central fina de 16px
track = Image.new("RGBA", (1500, 140), (0, 0, 0, 0))
ImageDraw.Draw(track).rounded_rectangle([0, 62, 1500, 78], radius=8, fill=(255, 255, 255, 55))
track.save(f"{OUT_DIR}/seek-track.png")

track_h = Image.new("RGBA", (1500, 140), (0, 0, 0, 0))
ImageDraw.Draw(track_h).rounded_rectangle([0, 62, 1500, 78], radius=8, fill=(255, 255, 255, 235))
track_h.save(f"{OUT_DIR}/seek-track-highlighted.png")

# 4. Iconos de Reproducción (Play, Pause, Next, Prev, Menu)
def make_btn(name, size, draw_fn, alpha=255):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(im), size, (255, 255, 255, alpha))
    im.save(f"{OUT_DIR}/{name}.png")

# Play / Pause
make_btn("playNew", 320, lambda d, s, c: d.polygon([(95, 55), (95, 265), (265, 160)], fill=c))
make_btn("playNew-h", 320, lambda d, s, c: d.polygon([(95, 55), (95, 265), (265, 160)], fill=c), 140)
make_btn("pauseNew", 320, lambda d, s, c: (d.rounded_rectangle([85, 60, 138, 260], radius=16, fill=c), d.rounded_rectangle([182, 60, 235, 260], radius=16, fill=c)))
make_btn("pauseNew-h", 320, lambda d, s, c: (d.rounded_rectangle([85, 60, 138, 260], radius=16, fill=c), d.rounded_rectangle([182, 60, 235, 260], radius=16, fill=c)), 140)

# Next / Prev
def d_next(d, s, c):
    d.polygon([(35, 75), (35, 205), (145, 140)], fill=c)
    d.polygon([(145, 75), (145, 205), (255, 140)], fill=c)
def d_prev(d, s, c):
    d.polygon([(245, 75), (245, 205), (135, 140)], fill=c)
    d.polygon([(135, 75), (135, 205), (25, 140)], fill=c)

make_btn("skipnextNew", 280, d_next)
make_btn("skipnextNew-h", 280, d_next, 140)
make_btn("skipprevNew", 280, d_prev)
make_btn("skipprevNew-h", 280, d_prev, 140)

# Botón Menú (...)
def d_menu(d, s, c):
    d.ellipse([0, 0, s, s], fill=(255, 255, 255, 35))
    for cx in [38, 65, 92]:
        d.ellipse([cx - 6, 59, cx + 6, 71], fill=c)
make_btn("menu", 130, d_menu)
make_btn("menu-h", 130, d_menu, 140)

# Iconos reales para Shuffle (Flechas cruzadas) y Repeat (Bucle)
def d_shuffle(d, s, c, active=False):
    if active:
        d.rounded_rectangle([20, 20, s-20, s-20], radius=35, fill=(255, 255, 255, 45))
    d.line([(45, 130), (85, 130), (125, 70), (155, 70)], fill=c, width=10)
    d.line([(45, 70), (85, 70), (125, 130), (155, 130)], fill=c, width=10)
    d.polygon([(145, 52), (145, 88), (170, 70)], fill=c)
    d.polygon([(145, 112), (145, 148), (170, 130)], fill=c)

def d_repeat(d, s, c, active=False):
    if active:
        d.rounded_rectangle([20, 20, s-20, s-20], radius=35, fill=(255, 255, 255, 45))
    d.rounded_rectangle([45, 65, 155, 135], radius=25, outline=c, width=10)
    d.polygon([(135, 45), (135, 85), (165, 65)], fill=c)

make_btn("shuffle", 200, lambda d, s, c: d_shuffle(d, s, c, False), 150)
make_btn("shuffle-h", 200, lambda d, s, c: d_shuffle(d, s, c, False), 100)
make_btn("shuffled", 200, lambda d, s, c: d_shuffle(d, s, (255, 60, 90, 255), True))
make_btn("shuffled-h", 200, lambda d, s, c: d_shuffle(d, s, (255, 60, 90, 180), True))

make_btn("repeat", 200, lambda d, s, c: d_repeat(d, s, c, False), 150)
make_btn("repeat-h", 200, lambda d, s, c: d_repeat(d, s, c, False), 100)
make_btn("repeated", 200, lambda d, s, c: d_repeat(d, s, (255, 60, 90, 255), True))
make_btn("repeated-h", 200, lambda d, s, c: d_repeat(d, s, (255, 60, 90, 180), True))

# Iconos de Altavoz (Volumen Mín y Máx) y Barra inferior estilo Apple Music (Lyrics, AirPlay, Lista)
def d_vol_min(d, s, c):
    d.polygon([(20, 32), (38, 32), (58, 14), (58, 66), (38, 48), (20, 48)], fill=c)
def d_vol_max(d, s, c):
    d_vol_min(d, s, c)
    d.arc([48, 20, 74, 60], start=-60, end=60, fill=c, width=6)
    d.arc([56, 10, 90, 70], start=-60, end=60, fill=c, width=6)

make_btn("vol-min", 80, d_vol_min, 160)
make_btn("vol-max", 95, d_vol_max, 160)

# Iconos inferiores decorativos (Lyrics, AirPlay, Queue)
bottom_bar = Image.new("RGBA", (1200, 120), (0, 0, 0, 0))
db = ImageDraw.Draw(bottom_bar)
col_b = (255, 255, 255, 150)
# Burbuja de letras (izquierda)
db.rounded_rectangle([80, 15, 175, 95], radius=18, fill=col_b)
db.ellipse([105, 45, 120, 60], fill=(20, 15, 25, 255))
db.ellipse([135, 45, 150, 60], fill=(20, 15, 25, 255))
# AirPlay (centro)
db.arc([555, 15, 645, 95], start=135, end=45, fill=col_b, width=8)
db.arc([572, 32, 628, 82], start=135, end=45, fill=col_b, width=8)
db.polygon([(570, 105), (630, 105), (600, 68)], fill=col_b)
# Lista / Queue (derecha)
for ly in [28, 56, 84]:
    db.ellipse([1015, ly - 5, 1025, ly + 5], fill=col_b)
    db.line([(1040, ly), (1115, ly)], fill=col_b, width=8)
bottom_bar.save(f"{OUT_DIR}/bottom-icons.png")

# Iconos de sistema para el navegador de foobar
for ico in ["noart", "play", "pause", "iconadd2", "iconremove", "iconsliders", "iconspeaker", "iconlist", "iconfolder"]:
    im = Image.new("RGBA", (120, 120), (35, 30, 45, 255) if ico=="noart" else (0,0,0,0))
    im.save(f"{OUT_DIR}/{ico}.png")

# 5. Generar layouts dinámicos para TODAS las relaciones de aspecto (1800, 2000, 2250)
# Esto elimina para siempre la franja blanca de la derecha
layouts = [
    (1800, "9-20", "portrait-9-20-1800x4000.txt"),
    (2250, "9-16", "portrait-9-16-2250x4000.txt"),
    (2500, "10-16", "portrait-10-16-2500x4000.txt")
]

for w, tag, filename in layouts:
    # Usamos máximo 2250 para el crop
    eff_w = min(w, 2250)
    ax, ay, asize = generate_layout_assets(eff_w, tag)
    
    # Coordenadas centradas automáticamente según el ancho (w)
    menu_x = ax + asize - 130
    title_y = ay + asize + 110
    artist_y = title_y + 135
    seek_y = artist_y + 160
    time_y = seek_y + 135
    
    ctrl_y = time_y + 180
    cx = w // 2
    
    vol_y = ctrl_y + 460
    vol_w = asize - 220
    vol_x = (w - vol_w) // 2
    
    bot_x = (w - 1200) // 2

    txt = f"""[image]
bg_{tag}.png
0,0,{w},4000

[label]
0,205,{w},75
centered
[rgb-255-255-255][b]Reproduciendo[-b]

[label]
0,275,{w},65
centered
[rgb-180-175-190]de tu biblioteca

[button]
{menu_x},190,130,130
menu
menu.png
menu-h.png
menu.png
menu-h.png

[albumart]
{ax},{ay},{asize},{asize}
main

[image]
roundcover_{tag}.png
{ax},{ay},{asize},{asize}

*if playing
[label]
{ax},{title_y},{asize},120
left
[rgb-255-255-255][b][title][-b]

[label]
{ax},{artist_y},{asize},100
left
[rgb-235-185-200][artist]
*else
[label]
{ax},{title_y},{asize},120
left
[rgb-255-255-255][b]No reproduciendo[-b]
*end

[position]
{ax},{seek_y},{asize},140
position-marker.png
seek-track.png
seek-track-highlighted.png

[label]
{ax},{time_y},500,75
left
[rgb-190-185-200][currentposition]

[label]
{ax + asize - 500},{time_y},500,75
right
[rgb-190-185-200]-[remaining]

[button]
{ax},{ctrl_y + 60},200,200
shuffle
shuffle.png
shuffle-h.png
shuffled.png
shuffled-h.png

[button]
{cx - 460},{ctrl_y + 20},280,280
skipback
skipprevNew.png
skipprevNew-h.png
skipprevNew.png
skipprevNew-h.png

[button]
{cx - 160},{ctrl_y},320,320
playnpause
playNew.png
playNew-h.png
pauseNew.png
pauseNew-h.png

[button]
{cx + 180},{ctrl_y + 20},280,280
skipnext
skipnextNew.png
skipnextNew-h.png
skipnextNew.png
skipnextNew-h.png

[button]
{ax + asize - 200},{ctrl_y + 60},200,200
repeat
repeat.png
repeat-h.png
repeated.png
repeated-h.png

[image]
vol-min.png
{ax},{vol_y + 30},80,80

[volume]
{vol_x},{vol_y},{vol_w},140
volume-marker.png
seek-track.png
seek-track-highlighted.png

[image]
vol-max.png
{ax + asize - 95},{vol_y + 30},95,95

[image]
bottom-icons.png
{bot_x},3620,1200,120

[label]
0,3790,{w},65
centered
[rgb-170-165-180]Lossless Audio • foobar2000
"""
    with open(f"{OUT_DIR}/{filename}", "w", encoding="utf-16") as f:
        f.write(txt.replace("\n", "\r\n"))

# 6. Guardar skindef.skindef mapeando cada resolución a su lienzo real
skindef_content = """name: Apple Music (iOS Blur)
author: Custom
version: 2.0
defaultart: noart.png
backgroundcol: 18,14,26
iconplay: play.png
iconpause: pause.png
iconadd: iconadd2.png
iconremove: iconremove.png
iconsliders: iconsliders.png
iconspeaker: iconspeaker.png
iconlist: iconlist.png
iconfolder: iconfolder.png

skin: 1800x4000 portrait-9-20-1800x4000.txt
skin: 2250x4000 portrait-9-16-2250x4000.txt
skin: 2500x4000 portrait-10-16-2500x4000.txt
skin: 2666x4000 portrait-10-16-2500x4000.txt
skin: 3000x4000 portrait-10-16-2500x4000.txt
"""

with open(f"{OUT_DIR}/skindef.skindef", "w", encoding="utf-16") as f:
    f.write(skindef_content.replace("\n", "\r\n"))

# 7. Empaquetar en AppleMusic.fbskin
with zipfile.ZipFile("AppleMusic.fbskin", "w", zipfile.ZIP_DEFLATED) as zf:
    for root, _, files in os.walk(OUT_DIR):
        for file in files:
            zf.write(os.path.join(root, file), arcname=file)

print("¡AppleMusic.fbskin v2.0 generado con éxito!")
