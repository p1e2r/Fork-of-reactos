#!/usr/bin/env python3
"""Original Lumen cursor set: smooth white shapes with a dark outline and a soft
shadow, in a Windows 11-like spirit. Drawn from scratch with simple geometry.

Run from the repository root:  python3 media/themes/Lumen/tools/lumen_cursors.py
"""
import math, os, struct
from PIL import Image, ImageDraw, ImageFilter

N = 32          # cursor size
K = 8           # supersampling
S = N * K
OUT = 'win32ss/user/user32/resources/'
WHITE, INK = (255, 255, 255, 255), (20, 20, 20, 255)
ACCENT = (0, 120, 212, 255)


def P(x, y):
    return (x * K, y * K)


def outlined(draw_fn, width=1.15):
    """Draw a shape white with a uniform dark outline around it.
    draw_fn(d, fill, grow) draws the shape; the outline comes from dilating it."""
    mask = Image.new('L', (S, S), 0)
    draw_fn(ImageDraw.Draw(mask), 255, 0)
    r = int(width * K)
    ring = mask.filter(ImageFilter.MaxFilter(2 * r + 1))
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    im.paste(Image.new('RGBA', (S, S), INK), (0, 0), ring)
    im.paste(Image.new('RGBA', (S, S), WHITE), (0, 0), mask)
    return im


def fatten(pts, grow):
    if not grow:
        return pts
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    out = []
    for x, y in pts:
        dx, dy = x - cx, y - cy
        l = math.hypot(dx, dy) or 1
        out.append((x + dx / l * grow * K, y + dy / l * grow * K))
    return out


ARROW = [(2, 2), (2, 23), (7.2, 18.6), (10.4, 25.6), (13.6, 24.2), (10.6, 17.4), (17.4, 17.2)]


def arrow(d, fill, grow, dx=0, dy=0):
    pts = [P(x + dx, y + dy) for x, y in ARROW]
    d.polygon(fatten(pts, grow * 1.15), fill=fill)


def c_normal():
    return outlined(arrow)


def c_help():
    im = outlined(arrow)
    d = ImageDraw.Draw(im)
    d.ellipse((*P(17, 15), *P(30, 28)), fill=ACCENT)
    w = 2 * K
    d.arc((*P(20.3, 17.3), *P(26.7, 23)), 200, 30, fill=WHITE, width=int(1.6 * K))
    d.line((*P(23.6, 22.6), *P(23.5, 24)), fill=WHITE, width=int(1.6 * K))
    d.ellipse((*P(22.6, 25), *P(24.6, 27)), fill=WHITE)
    return im


def ring(d, box, frac=0.75, start=-90, color=ACCENT, width=3.2):
    d.arc(box, start, start + 360 * frac, fill=color, width=int(width * K))


def c_wait():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((*P(4, 4), *P(28, 28)), fill=(255, 255, 255, 230))
    d.ellipse((*P(4, 4), *P(28, 28)), outline=INK, width=K)
    ring(d, (*P(7.5, 7.5), *P(24.5, 24.5)), 0.7)
    return im


def c_appstarting():
    im = outlined(arrow)
    d = ImageDraw.Draw(im)
    d.ellipse((*P(17, 16), *P(30, 29)), fill=(255, 255, 255, 235))
    d.ellipse((*P(17, 16), *P(30, 29)), outline=INK, width=K)
    ring(d, (*P(19, 18), *P(28, 27)), 0.7, width=2.2)
    return im


def c_hand():
    def hand(d, fill, grow):
        g = grow * K
        # pointing finger, other fingers, palm
        d.rounded_rectangle((P(8.5, 1.5)[0] - g, P(8.5, 1.5)[1] - g, P(12.5, 16)[0] + g, P(12.5, 16)[1] + g), 2 * K + g, fill=fill)
        for x in (12.5, 16, 19.5):
            d.rounded_rectangle((P(x, 10)[0] - g, P(x, 10)[1] - g, P(x + 3.6, 18)[0] + g, P(x + 3.6, 18)[1] + g), int(1.8 * K + g), fill=fill)
        d.polygon(fatten([P(4, 15.5), P(8.5, 13), P(23, 15), P(22.6, 23), P(19, 29), P(10.5, 29), P(6, 22)], grow), fill=fill)
    return outlined(hand)


def c_ibeam():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for col, w in ((WHITE, 3.4), (INK, 1.4)):
        d.line((*P(16, 7), *P(16, 25)), fill=col, width=int(w * K))
        d.line((*P(12.5, 6.5), *P(19.5, 6.5)), fill=col, width=int(w * K))
        d.line((*P(12.5, 25.5), *P(19.5, 25.5)), fill=col, width=int(w * K))
    return im


def c_cross():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for col, w in ((WHITE, 3.2), (INK, 1.2)):
        d.line((*P(16, 4), *P(16, 28)), fill=col, width=int(w * K))
        d.line((*P(4, 16), *P(28, 16)), fill=col, width=int(w * K))
    return im


def double_arrow(angle):
    """Two-headed arrow through the center, rotated by angle (degrees)."""
    def shape(d, fill, grow):
        pts = [(0, -12), (5.5, -6), (1.8, -6), (1.8, 6), (5.5, 6), (0, 12), (-5.5, 6), (-1.8, 6), (-1.8, -6), (-5.5, -6)]
        a = math.radians(angle)
        rot = [(16 + x * math.cos(a) - y * math.sin(a), 16 + x * math.sin(a) + y * math.cos(a)) for x, y in pts]
        d.polygon(fatten([P(x, y) for x, y in rot], grow), fill=fill)
    return outlined(shape)


def c_sizeall():
    def shape(d, fill, grow):
        g = grow
        arm = [(0, -13), (5, -8), (1.6, -8), (1.6, -1.6), (8, -1.6), (8, -5), (13, 0), (8, 5), (8, 1.6),
               (1.6, 1.6), (1.6, 8), (5, 8), (0, 13), (-5, 8), (-1.6, 8), (-1.6, 1.6), (-8, 1.6), (-8, 5),
               (-13, 0), (-8, -5), (-8, -1.6), (-1.6, -1.6), (-1.6, -8), (-5, -8)]
        d.polygon(fatten([P(16 + x, 16 + y) for x, y in arm], g), fill=fill)
    return outlined(shape)


def c_up():
    def shape(d, fill, grow):
        pts = [(16, 3), (24, 12), (19, 12), (19, 28), (13, 28), (13, 12), (8, 12)]
        d.polygon(fatten([P(x, y) for x, y in pts], grow), fill=fill)
    return outlined(shape)


def c_no():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((*P(4, 4), *P(28, 28)), fill=WHITE)
    d.ellipse((*P(6, 6), *P(26, 26)), outline=(220, 50, 40, 255), width=int(3 * K))
    d.line((*P(9.5, 22.5), *P(22.5, 9.5)), fill=(220, 50, 40, 255), width=int(3 * K))
    d.ellipse((*P(4, 4), *P(28, 28)), outline=INK, width=K // 2)
    return im


def c_pen():
    def shape(d, fill, grow):
        pts = [(3, 29), (5, 22), (22, 5), (27, 10), (10, 27)]
        d.polygon(fatten([P(x, y) for x, y in pts], grow), fill=fill)
    im = outlined(shape)
    ImageDraw.Draw(im).polygon([P(3, 29), P(5, 23.5), P(8.5, 27)], fill=INK)
    return im


CURSORS = {  # file: (drawing, hotspot)
    'ocr_normal.cur': (c_normal, (2, 2)),
    'ocr_help.cur': (c_help, (2, 2)),
    'ocr_appstarting.cur': (c_appstarting, (2, 2)),
    'ocr_wait.cur': (c_wait, (16, 16)),
    'ocr_hand.cur': (c_hand, (10, 2)),
    'ocr_ibeam.cur': (c_ibeam, (16, 16)),
    'ocr_cross.cur': (c_cross, (16, 16)),
    'ocr_sizens.cur': (lambda: double_arrow(0), (16, 16)),
    'ocr_sizewe.cur': (lambda: double_arrow(90), (16, 16)),
    'ocr_sizenwse.cur': (lambda: double_arrow(-45), (16, 16)),
    'ocr_sizenesw.cur': (lambda: double_arrow(45), (16, 16)),
    'ocr_sizeall.cur': (c_sizeall, (16, 16)),
    'ocr_up.cur': (c_up, (16, 3)),
    'ocr_no.cur': (c_no, (16, 16)),
    'ocr_pen.cur': (c_pen, (3, 29)),
}


def finish(master):
    im = master.resize((N, N), Image.LANCZOS)
    # soft drop shadow
    a = im.split()[3].point(lambda v: v * 90 // 255).filter(ImageFilter.GaussianBlur(1.0))
    sh = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    sh.putalpha(a)
    out = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    out.paste(sh, (1, 1), sh)
    out.alpha_composite(im)
    return out


def dib(im, bpp):
    w, h = im.size
    px = im.load()
    row_and = ((w + 31) // 32) * 4
    andm = bytearray()
    for y in range(h - 1, -1, -1):
        bits = bytearray(row_and)
        for x in range(w):
            if px[x, y][3] < (128 if bpp == 1 else 1):
                bits[x // 8] |= 0x80 >> (x % 8)
        andm += bits
    if bpp == 32:
        xor = bytearray()
        for y in range(h - 1, -1, -1):
            for x in range(w):
                r, g, b, a = px[x, y]
                xor += bytes((b, g, r, a))
        hdr = struct.pack('<IiiHHIIiiII', 40, w, h * 2, 1, 32, 0, len(xor) + len(andm), 0, 0, 0, 0)
        return hdr + bytes(xor) + bytes(andm)
    xor = bytearray()
    for y in range(h - 1, -1, -1):
        bits = bytearray(row_and)
        for x in range(w):
            r, g, b, a = px[x, y]
            if a >= 128 and (r + g + b) > 384:
                bits[x // 8] |= 0x80 >> (x % 8)
        xor += bits
    hdr = struct.pack('<IiiHHIIiiII', 40, w, h * 2, 1, 1, 0, len(xor) + len(andm), 0, 0, 2, 0)
    pal = bytes((0, 0, 0, 0, 255, 255, 255, 0))
    return hdr + pal + bytes(xor) + bytes(andm)


def write_cur(im, hot, path):
    entries = [dib(im, 1), dib(im, 32)]
    data = struct.pack('<HHH', 0, 2, len(entries))
    off = 6 + 16 * len(entries)
    for e, colors in zip(entries, (2, 0)):
        data += struct.pack('<BBBBHHII', N, N, colors, 0, hot[0], hot[1], len(e), off)
        off += len(e)
    open(path, 'wb').write(data + b''.join(entries))


if __name__ == '__main__':
    sheet = Image.new('RGBA', (len(CURSORS) * 40, 80), (90, 140, 210, 255))
    for i, (name, (fn, hot)) in enumerate(CURSORS.items()):
        im = finish(fn())
        write_cur(im, hot, OUT + name)
        sheet.alpha_composite(im, (i * 40 + 4, 4))
        light = Image.new('RGBA', (40, 40), (243, 243, 243, 255))
        light.alpha_composite(im, (4, 4))
        sheet.paste(light, (i * 40, 40))
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save('/tmp/lumen_cursors.png')
    print('wrote', len(CURSORS), 'cursors')
