#!/usr/bin/env python3
"""Original Lumen icon set: flat shapes with soft gradients in a Windows 11-like
spirit. Every icon is drawn from scratch with simple geometry (no Microsoft artwork).

Run from the repository root:  python3 media/themes/Lumen/tools/lumen_icons.py
"""
import math, os, struct, io
from PIL import Image, ImageDraw, ImageFilter

S = 256           # master canvas
SIZES = (48, 32, 24, 16)


# ------------------------------------------------------------------ helpers
def canvas():
    return Image.new('RGBA', (S, S), (0, 0, 0, 0))


def grad(size, c1, c2, angle=90):
    """Linear gradient image (angle 90 = top->bottom)."""
    w, h = size
    g = Image.new('RGBA', (w, h))
    px = g.load()
    a = math.radians(angle)
    dx, dy = math.cos(a), math.sin(a)
    span = abs(dx) * w + abs(dy) * h or 1
    for y in range(h):
        for x in range(w):
            t = ((x * dx + y * dy) - min(0, dx * w) - min(0, dy * h)) / span
            t = max(0.0, min(1.0, t))
            px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)) + (255,)
    return g


def shape(img, draw_fn, c1, c2=None, angle=90):
    """Fill the area drawn by draw_fn(maskdraw) with a gradient (or flat color)."""
    mask = Image.new('L', (S, S), 0)
    draw_fn(ImageDraw.Draw(mask))
    fill = grad((S, S), c1, c2 or c1, angle)
    img.paste(fill, (0, 0), mask)


def rr(box, r):
    return lambda d: d.rounded_rectangle(box, radius=r, fill=255)


def poly(pts):
    return lambda d: d.polygon(pts, fill=255)


def ell(box):
    return lambda d: d.ellipse(box, fill=255)


def shadow(img, strength=60, blur=6, offset=4):
    a = img.split()[3].point(lambda v: v * strength // 255)
    sh = Image.new('RGBA', img.size, (0, 0, 0, 0))
    sh.putalpha(a.filter(ImageFilter.GaussianBlur(blur)))
    out = Image.new('RGBA', img.size, (0, 0, 0, 0))
    out.paste(sh, (0, offset), sh)
    out.alpha_composite(img)
    return out


# ------------------------------------------------------------------ designs
def folder(open_=False, emblem=None):
    im = canvas()
    shape(im, lambda d: (d.rounded_rectangle((20, 52, 120, 96), 14, fill=255),
                         d.rounded_rectangle((20, 70, 236, 214), 16, fill=255)),
          (226, 160, 26), (204, 132, 10))
    if open_:
        shape(im, poly([(46, 104), (246, 104), (222, 214), (20, 214)]), (255, 214, 92), (246, 186, 48))
    else:
        shape(im, rr((20, 96, 236, 214), 16), (255, 211, 88), (247, 184, 44))
        shape(im, rr((20, 96, 236, 104), 4), (255, 228, 140))
    if emblem:
        emblem(im)
    return im


def emblem_doc(im):
    shape(im, rr((96, 120, 160, 196), 8), (255, 255, 255), (232, 238, 246))
    d = ImageDraw.Draw(im)
    for y in (140, 156, 172):
        d.rounded_rectangle((108, y, 148, y + 6), 3, fill=(60, 120, 200, 255))


def emblem_picture(im):
    shape(im, rr((86, 120, 170, 190), 8), (255, 255, 255))
    shape(im, poly([(94, 182), (122, 146), (140, 166), (150, 156), (162, 182)]), (40, 160, 90), (20, 120, 70))
    shape(im, ell((140, 128, 156, 144)), (255, 190, 40))


def emblem_music(im):
    d = ImageDraw.Draw(im)
    c = (120, 70, 200, 255)
    d.ellipse((96, 160, 124, 186), fill=c)
    d.ellipse((134, 150, 162, 176), fill=c)
    d.rectangle((116, 124, 124, 172), fill=c)
    d.rectangle((154, 114, 162, 162), fill=c)
    d.polygon([(116, 124), (162, 114), (162, 130), (116, 140)], fill=c)


def computer():
    im = canvas()
    shape(im, rr((16, 34, 240, 186), 18), (60, 64, 72), (36, 38, 44))
    shape(im, rr((28, 46, 228, 174), 10), (60, 150, 240), (20, 90, 200), 60)
    # soft wave on the screen
    shape(im, poly([(28, 140), (90, 118), (160, 136), (228, 112), (228, 174), (28, 174)]), (110, 190, 255), (40, 120, 220))
    shape(im, poly([(108, 186), (148, 186), (156, 214), (100, 214)]), (150, 156, 166), (110, 116, 126))
    shape(im, rr((70, 210, 186, 226), 8), (180, 186, 196), (130, 136, 146))
    return im


def drive(kind='hdd'):
    im = canvas()
    shape(im, rr((20, 92, 236, 196), 22), (210, 216, 226), (150, 158, 172))
    shape(im, rr((20, 92, 236, 112), 10), (236, 240, 246))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((44, 150, 160, 160), 5, fill=(110, 118, 132, 255))
    led = {'hdd': (40, 200, 110), 'removable': (60, 150, 240), 'net': (60, 150, 240), 'ram': (240, 160, 40)}[kind]
    d.ellipse((196, 146, 214, 164), fill=led + (255,))
    if kind == 'net':
        shape(im, rr((118, 196, 138, 230), 4), (110, 118, 132))
        shape(im, rr((70, 222, 186, 236), 6), (110, 118, 132))
    if kind == 'removable':
        shape(im, rr((96, 52, 160, 96), 8), (120, 128, 140), (90, 98, 110))
    return im


def cdrom():
    im = canvas()
    shape(im, ell((24, 24, 232, 232)), (236, 240, 248), (170, 180, 200), 45)
    # iridescent band
    shape(im, lambda d: (d.pieslice((24, 24, 232, 232), 200, 250, fill=255)), (150, 210, 255), (230, 170, 255), 0)
    shape(im, ell((96, 96, 160, 160)), (200, 206, 218))
    d = ImageDraw.Draw(im)
    d.ellipse((114, 114, 142, 142), fill=(0, 0, 0, 0))
    return im


def recycle(full=False):
    im = canvas()
    shape(im, poly([(48, 64), (208, 64), (190, 228), (66, 228)]), (200, 225, 245), (150, 190, 225))
    shape(im, rr((36, 46, 220, 70), 10), (220, 236, 250), (170, 200, 230))
    d = ImageDraw.Draw(im)
    for x0, x1 in ((96, 92), (128, 128), (160, 164)):
        d.line((x0, 86, x1, 210), fill=(110, 160, 210, 255), width=8)
    if full:
        shape(im, poly([(62, 50), (118, 18), (146, 54)]), (255, 255, 255), (220, 228, 238))
        shape(im, poly([(130, 48), (196, 26), (204, 54)]), (250, 220, 120), (230, 190, 70))
        shape(im, rr((36, 46, 220, 70), 10), (220, 236, 250), (170, 200, 230))
    return im


def globe():
    im = canvas()
    shape(im, ell((28, 28, 228, 228)), (80, 170, 255), (20, 100, 210), 60)
    d = ImageDraw.Draw(im)
    w = (255, 255, 255, 170)
    d.ellipse((28, 28, 228, 228), outline=w, width=6)
    d.ellipse((84, 28, 172, 228), outline=w, width=6)
    d.line((128, 28, 128, 228), fill=w, width=6)
    d.line((28, 128, 228, 128), fill=w, width=6)
    d.arc((40, 40, 216, 140), 200, 340, fill=w, width=6)
    d.arc((40, 116, 216, 216), 20, 160, fill=w, width=6)
    return im


def network():
    im = globe()
    small = computer().resize((140, 140), Image.LANCZOS)
    im.alpha_composite(small, (110, 110))
    return im


def control_panel():
    im = canvas()
    shape(im, rr((24, 24, 232, 232), 40), (70, 150, 245), (30, 95, 210), 60)
    d = ImageDraw.Draw(im)
    for i, (y, k) in enumerate(((80, 160), (128, 96), (176, 140))):
        d.rounded_rectangle((60, y - 6, 196, y + 6), 6, fill=(255, 255, 255, 140))
        d.ellipse((k - 18, y - 18, k + 18, y + 18), fill=(255, 255, 255, 255))
    return im


def desktop_icon():
    im = computer()
    return im


def page(lines=False, fold_color=(220, 226, 236), accent=None):
    im = canvas()
    shape(im, poly([(52, 20), (164, 20), (212, 68), (212, 236), (52, 236)]), (255, 255, 255), (236, 240, 246))
    shape(im, poly([(164, 20), (212, 68), (164, 68)]), fold_color)
    d = ImageDraw.Draw(im)
    d.line([(52, 20), (164, 20), (212, 68), (212, 236), (52, 236), (52, 20)], fill=(180, 188, 200, 255), width=4)
    if lines:
        for y in range(100, 220, 24):
            d.rounded_rectangle((76, y, 188, y + 8), 4, fill=(accent or (150, 160, 175)) + (255,))
    return im


def app_window():
    im = canvas()
    shape(im, rr((20, 36, 236, 220), 18), (250, 251, 253), (226, 232, 240))
    shape(im, rr((20, 36, 236, 80), 18), (60, 140, 235), (30, 100, 210))
    shape(im, rr((20, 62, 236, 80), 0), (30, 100, 210))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((40, 100, 120, 196), 8, fill=(200, 214, 232, 255))
    d.rounded_rectangle((136, 100, 216, 120), 6, fill=(200, 214, 232, 255))
    d.rounded_rectangle((136, 132, 216, 152), 6, fill=(200, 214, 232, 255))
    return im


def search_icon():
    im = canvas()
    d = ImageDraw.Draw(im)
    d.line((150, 150, 222, 222), fill=(80, 88, 100, 255), width=34)
    shape(im, ell((24, 24, 176, 176)), (90, 170, 255), (40, 110, 220), 60)
    shape(im, ell((48, 48, 152, 152)), (220, 238, 255), (170, 210, 250), 60)
    return im


# app icons --------------------------------------------------------------
def tile(c1, c2):
    im = canvas()
    shape(im, rr((20, 20, 236, 236), 44), c1, c2, 60)
    return im


def notepad():
    im = canvas()
    shape(im, rr((40, 28, 216, 232), 22), (255, 255, 255), (230, 236, 244))
    shape(im, rr((40, 28, 216, 72), 22), (60, 150, 240), (30, 110, 220))
    shape(im, rr((40, 52, 216, 72), 0), (30, 110, 220))
    d = ImageDraw.Draw(im)
    for y in (100, 132, 164, 196):
        d.rounded_rectangle((68, y, 188 if y != 196 else 140, y + 10), 5, fill=(150, 162, 180, 255))
    return im


def calculator():
    im = tile((70, 78, 92), (36, 40, 50))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((52, 48, 204, 96), 10, fill=(200, 226, 255, 255))
    for r in range(3):
        for c in range(3):
            x, y = 52 + c * 54, 112 + r * 40
            col = (255, 140, 60, 255) if (r, c) == (2, 2) else (210, 214, 222, 255)
            d.rounded_rectangle((x, y, x + 44, y + 30), 8, fill=col)
    return im


def terminal():
    im = tile((52, 56, 66), (18, 20, 26))
    d = ImageDraw.Draw(im)
    d.line([(64, 92), (110, 128), (64, 164)], fill=(255, 255, 255, 255), width=18, joint='curve')
    d.rounded_rectangle((124, 156, 192, 172), 8, fill=(255, 255, 255, 255))
    return im


def paint():
    im = canvas()
    shape(im, lambda d: d.ellipse((24, 40, 232, 220), fill=255), (250, 250, 252), (220, 224, 232))
    d = ImageDraw.Draw(im)
    d.ellipse((150, 140, 196, 186), fill=(0, 0, 0, 0))
    for (x, y), c in zip(((70, 90), (116, 66), (166, 82), (62, 144)),
                         ((235, 70, 70), (250, 190, 40), (60, 170, 90), (60, 130, 240))):
        d.ellipse((x - 20, y - 20, x + 20, y + 20), fill=c + (255,))
    return im


def taskmgr():
    im = tile((60, 170, 120), (20, 120, 80))
    d = ImageDraw.Draw(im)
    d.line([(48, 160), (92, 160), (112, 90), (140, 190), (162, 120), (176, 160), (208, 160)],
           fill=(255, 255, 255, 255), width=16, joint='curve')
    return im


def store():
    im = canvas()
    shape(im, rr((36, 76, 220, 228), 26), (70, 150, 245), (30, 95, 210), 60)
    d = ImageDraw.Draw(im)
    d.arc((84, 30, 172, 120), 180, 360, fill=(60, 130, 230, 255), width=14)
    for (x, y), c in zip(((104, 132), (152, 132), (104, 180), (152, 180)),
                         ((255, 255, 255), (230, 240, 255), (230, 240, 255), (255, 255, 255))):
        d.rounded_rectangle((x - 18, y - 18, x + 18, y + 18), 6, fill=c + (255,))
    return im


def wordpad():
    im = page(lines=True, accent=(60, 120, 220))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((28, 120, 124, 216), 16, fill=(30, 100, 210, 255))
    d.line([(52, 196), (76, 140), (100, 196)], fill=(255, 255, 255, 255), width=14, joint='curve')
    d.line([(62, 176), (90, 176)], fill=(255, 255, 255, 255), width=12)
    return im


def charmap():
    im = tile((250, 252, 255), (220, 228, 240))
    d = ImageDraw.Draw(im)
    for r in range(3):
        for c in range(3):
            x, y = 50 + c * 56, 50 + r * 56
            col = (30, 110, 220, 255) if (r, c) == (1, 1) else (190, 200, 216, 255)
            d.rounded_rectangle((x, y, x + 44, y + 44), 8, fill=col)
    return im


def media():
    im = tile((255, 140, 60), (230, 70, 50))
    shape(im, poly([(100, 72), (190, 128), (100, 184)]), (255, 255, 255))
    return im


# ------------------------------------------------------------------ ICO writer
def bmp_entry(img):
    """32bpp DIB (BGRA, bottom-up) plus an AND mask, as stored inside .ico files."""
    w, h = img.size
    px = img.load()
    xor = bytearray()
    for y in range(h - 1, -1, -1):
        for x in range(w):
            r, g, b, a = px[x, y]
            xor += bytes((b, g, r, a))
    row = ((w + 31) // 32) * 4
    andm = bytearray()
    for y in range(h - 1, -1, -1):
        bits = bytearray(row)
        for x in range(w):
            if px[x, y][3] == 0:
                bits[x // 8] |= 0x80 >> (x % 8)
        andm += bits
    hdr = struct.pack('<IiiHHIIiiII', 40, w, h * 2, 1, 32, 0, len(xor) + len(andm), 0, 0, 0, 0)
    return hdr + bytes(xor) + bytes(andm)


def render(master):
    master = shadow(master, 50, 5, 3)
    out = []
    for n in SIZES:
        im = master.resize((n, n), Image.LANCZOS)
        if n <= 24:
            im = im.filter(ImageFilter.UnsharpMask(radius=0.6, percent=60, threshold=0))
        out.append(im)
    return out


def write_ico(master, path):
    imgs = render(master)
    entries = [bmp_entry(i) for i in imgs]
    data = struct.pack('<HHH', 0, 1, len(entries))
    off = 6 + 16 * len(entries)
    for im, e in zip(imgs, entries):
        w = im.size[0]
        data += struct.pack('<BBBBHHII', w % 256, w % 256, 0, 0, 1, 32, len(e), off)
        off += len(e)
    data += b''.join(entries)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'wb').write(data)


SHELL = 'dll/win32/shell32/res/icons/'
TARGETS = {
    SHELL + '1.ico': lambda: page(),
    SHELL + '3.ico': app_window,
    SHELL + '4.ico': lambda: folder(),
    SHELL + '5.ico': lambda: folder(open_=True),
    SHELL + '8.ico': lambda: drive('removable'),
    SHELL + '9.ico': lambda: drive('hdd'),
    SHELL + '10.ico': lambda: drive('net'),
    SHELL + '12.ico': cdrom,
    SHELL + '13.ico': lambda: drive('ram'),
    SHELL + '14.ico': globe,
    SHELL + '15.ico': network,
    SHELL + '16.ico': computer,
    SHELL + '18.ico': network,
    SHELL + '20.ico': lambda: folder(),
    SHELL + '22.ico': control_panel,
    SHELL + '23.ico': search_icon,
    SHELL + '32.ico': lambda: recycle(False),
    SHELL + '33.ico': lambda: recycle(True),
    SHELL + '35.ico': desktop_icon,
    SHELL + '36.ico': control_panel,
    SHELL + '137.ico': control_panel,
    SHELL + '152.ico': lambda: page(lines=True),
    SHELL + '235.ico': lambda: folder(emblem=emblem_doc),
    SHELL + '236.ico': lambda: folder(emblem=emblem_picture),
    SHELL + '237.ico': lambda: folder(emblem=emblem_music),
    'base/shell/explorer/res/ico/101.ico': lambda: folder(),
    'base/applications/notepad/res/notepad.ico': notepad,
    'base/applications/calc/res/calc.ico': calculator,
    'base/shell/cmd/res/terminal.ico': terminal,
    'base/applications/mspaint/img/paint.ico': paint,
    'base/applications/taskmgr/res/taskmgr.ico': taskmgr,
    'base/applications/rapps/res/main.ico': store,
    'base/applications/wordpad/res/wordpad.ico': wordpad,
    'base/applications/charmap/res/charmap.ico': charmap,
    'base/applications/mplay32/resources/mplay32.ico': media,
}

if __name__ == '__main__':
    sheet = Image.new('RGBA', (8 * 72, ((len(TARGETS) + 7) // 8) * 72), (243, 243, 243, 255))
    for i, (path, fn) in enumerate(TARGETS.items()):
        master = fn()
        write_ico(master, path)
        sheet.alpha_composite(render(master)[0], ((i % 8) * 72 + 12, (i // 8) * 72 + 12))
    sheet.save('/tmp/lumen_icons_sheet.png')
    print('wrote', len(TARGETS), 'icons')
