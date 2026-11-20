#!/usr/bin/env python3
"""Generate the Windows 11-style bitmaps of the Lumen theme (Light variant).

Every image here is drawn from scratch with simple shapes; nothing is copied from
Microsoft. Run:  python3 lumen_bitmaps.py <path to lumen.msstyles/bitmaps/Light>
"""
import os, struct, sys
from PIL import Image, ImageDraw

OUT = sys.argv[1]
SS = 4  # supersampling factor for smooth rounded shapes

# Palette (plain RGB values in the spirit of the Windows 11 light look)
MICA = (243, 243, 243)       # caption / taskbar / dialog surface
BORDER = (160, 160, 160)     # active window border
BORDER_IN = (200, 200, 200)  # inactive window border
ACCENT = (0, 95, 184)
ACCENT_HOT = (25, 110, 191)
ACCENT_PRESS = (49, 131, 202)
INK = (26, 26, 26)
INK_DIM = (140, 140, 140)
CLOSE_RED = (196, 43, 28)
CLOSE_RED_PRESS = (200, 64, 49)
MAGENTA = (255, 0, 255)


def save32(im, name):
    """32bpp BI_RGB bottom-up BMP with straight alpha (uxtheme premultiplies on load)."""
    im = im.convert('RGBA')
    w, h = im.size
    px = im.load()
    rows = []
    for y in range(h - 1, -1, -1):
        r = bytearray()
        for x in range(w):
            R, G, B, A = px[x, y]
            r += bytes((B, G, R, A))
        rows.append(bytes(r))
    data = b''.join(rows)
    hdr = struct.pack('<2sIHHI', b'BM', 54 + len(data), 0, 0, 54)
    hdr += struct.pack('<IiiHHIIiiII', 40, w, h, 1, 32, 0, len(data), 3780, 3780, 0, 0)
    open(os.path.join(OUT, name), 'wb').write(hdr + data)


def save24(im, name):
    im.convert('RGB').save(os.path.join(OUT, name), 'BMP')


def canvas(w, h, fill=(0, 0, 0, 0)):
    im = Image.new('RGBA', (w * SS, h * SS), fill)
    return im, ImageDraw.Draw(im)


def down(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


def rrect(d, box, r, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = box
    d.rounded_rectangle((x0 * SS, y0 * SS, x1 * SS - 1, y1 * SS - 1), radius=r * SS,
                        fill=fill, outline=outline, width=width * SS)


def strip(states):
    """Stack equally sized RGBA state images vertically."""
    w, h = states[0].size
    out = Image.new('RGBA', (w, h * len(states)))
    for i, s in enumerate(states):
        out.paste(s, (0, i * h))
    return out


# ---------------------------------------------------------------- caption buttons
def caption_button(fills, w=46, h=32):
    states = []
    for f in fills:
        im = Image.new('RGBA', (w, h), MICA + (255,))
        if f is not None:
            ImageDraw.Draw(im).rectangle((0, 0, w - 1, h - 1), fill=f + (255,))
        states.append(im)
    return strip(states)


HOT = (229, 229, 229)
PRESS = (236, 236, 236)
save32(caption_button([None, HOT, PRESS, None, None, HOT, PRESS, None]), 'LIGHT_CAPTIONBUTTON.bmp')
save32(caption_button([None, CLOSE_RED, CLOSE_RED_PRESS, None, None, CLOSE_RED, CLOSE_RED_PRESS, None]),
       'LIGHT_CLOSEBUTTON.bmp')
save32(caption_button([None, CLOSE_RED, CLOSE_RED_PRESS, None, None, CLOSE_RED, CLOSE_RED_PRESS, None], 21, 21),
       'LIGHT_SMALLCLOSEBUTTON.bmp')


# ---------------------------------------------------------------- caption glyphs
def glyph(kind, n, color):
    im, d = canvas(n, n)
    lw = max(1, round(n / 13)) * SS
    m = n * SS * 0.12
    e = n * SS - m
    if kind == 'close':
        d.line((m, m, e, e), fill=color + (255,), width=lw)
        d.line((m, e, e, m), fill=color + (255,), width=lw)
    elif kind == 'max':
        d.rounded_rectangle((m, m, e, e), radius=n * SS * 0.12, outline=color + (255,), width=lw)
    elif kind == 'min':
        y = n * SS / 2
        d.line((m, y, e, y), fill=color + (255,), width=lw)
    elif kind == 'restore':
        o = n * SS * 0.22
        d.rounded_rectangle((m, m + o, e - o, e), radius=n * SS * 0.1, outline=color + (255,), width=lw)
        d.line((m + o, m, e, m), fill=color + (255,), width=lw)
        d.line((e, m, e, e - o), fill=color + (255,), width=lw)
    return down(im, n, n)


def glyph_strip(kind, n, close=False):
    hot = (255, 255, 255) if close else INK
    colors = [INK, hot, hot, INK_DIM, INK_DIM, hot, hot, (200, 200, 200)]
    return strip([glyph(kind, n, c) for c in colors])


for kind, base in (('close', 'CLOSEGLYPH'), ('max', 'MAXIMIZEGLYPH'),
                   ('min', 'MINIMIZEGLYPH'), ('restore', 'RESTOREGLYPH')):
    for size, suffix in ((6, '6'), (9, '9'), (13, ''), (19, '19'), (23, '23')):
        save32(glyph_strip(kind, size, kind == 'close'), 'LIGHT_%s%s.bmp' % (base, suffix))
save32(glyph_strip('close', 7, True), 'LIGHT_SMALLCLOSEGLYPH.bmp')


# ---------------------------------------------------------------- window frame
def frame_caption(w, h, top_border=True):
    states = []
    for b in (BORDER, BORDER_IN):
        im = Image.new('RGB', (w, h), MICA)
        d = ImageDraw.Draw(im)
        if top_border:
            d.line((0, 0, w - 1, 0), fill=b)
        d.line((0, 0, 0, h - 1), fill=b)
        d.line((w - 1, 0, w - 1, h - 1), fill=b)
        states.append(im)
    out = Image.new('RGB', (w, h * 2))
    out.paste(states[0], (0, 0)); out.paste(states[1], (0, h))
    return out


save24(frame_caption(66, 29), 'LIGHT_FRAMECAPTION.bmp')
save24(frame_caption(66, 29), 'LIGHT_FRAMECAPTIONMIN.bmp')
save24(frame_caption(66, 19), 'LIGHT_SMALLFRAMECAPTION.bmp')
mx = Image.new('RGB', (371, 44), MICA)
save24(mx, 'LIGHT_FRAMEMAXIMIZED.bmp')


def frame_side(w, h, edge):  # edge: 'left' | 'right' | 'bottom'
    out = Image.new('RGB', (w, h * 2), MICA)
    d = ImageDraw.Draw(out)
    for i, b in enumerate((BORDER, BORDER_IN)):
        y0 = i * h
        if edge == 'left':
            d.line((0, y0, 0, y0 + h - 1), fill=b)
        elif edge == 'right':
            d.line((w - 1, y0, w - 1, y0 + h - 1), fill=b)
        else:
            d.line((0, y0 + h - 1, w - 1, y0 + h - 1), fill=b)
            d.line((0, y0, 0, y0 + h - 1), fill=b)
            d.line((w - 1, y0, w - 1, y0 + h - 1), fill=b)
    return out


save24(frame_side(5, 31, 'left'), 'LIGHT_FRAMELEFT.bmp')
save24(frame_side(5, 31, 'right'), 'LIGHT_FRAMERIGHT.bmp')
save24(frame_side(49, 5, 'bottom'), 'LIGHT_FRAMEBOTTOM.bmp')


# ---------------------------------------------------------------- push button
def push_button():
    specs = [  # normal, hot, pressed, disabled, defaulted
        ((253, 253, 253), (208, 208, 208), (189, 189, 189)),
        ((246, 246, 246), (208, 208, 208), (189, 189, 189)),
        ((240, 240, 240), (215, 215, 215), (215, 215, 215)),
        ((245, 245, 245), (229, 229, 229), (229, 229, 229)),
        ((253, 253, 253), ACCENT, ACCENT),
    ]
    states = []
    for fill, border, bottom in specs:
        im, d = canvas(22, 23)
        rrect(d, (0, 0, 22, 23), 4, fill=bottom + (255,))
        rrect(d, (0, 0, 22, 22), 4, fill=border + (255,))
        rrect(d, (1, 1, 21, 21), 3, fill=fill + (255,))
        states.append(down(im, 22, 23))
    return strip(states)


save32(push_button(), 'LIGHT_BUTTON.bmp')


# ---------------------------------------------------------------- checkbox / radio
def checkbox(n):
    states = []
    un = [((250, 250, 250), (138, 138, 138)), ((240, 240, 240), (128, 128, 128)),
          ((232, 232, 232), (160, 160, 160)), ((247, 247, 247), (200, 200, 200))]
    on = [ACCENT, ACCENT_HOT, ACCENT_PRESS, (200, 200, 200)]
    for fill, border in un:
        im, d = canvas(n, n)
        rrect(d, (0, 0, n, n), max(2, n // 5), fill=border + (255,))
        rrect(d, (1, 1, n - 1, n - 1), max(1, n // 5 - 1), fill=fill + (255,))
        states.append(down(im, n, n))
    for mark in ('check', 'mixed'):
        for c in on:
            im, d = canvas(n, n)
            rrect(d, (0, 0, n, n), max(2, n // 5), fill=c + (255,))
            S = n * SS
            w = max(1, round(n / 10)) * SS
            if mark == 'check':
                d.line((S * .25, S * .52, S * .43, S * .70, S * .76, S * .32), fill=(255, 255, 255, 255),
                       width=w, joint='curve')
            else:
                d.line((S * .28, S * .5, S * .72, S * .5), fill=(255, 255, 255, 255), width=w)
            states.append(down(im, n, n))
    return strip(states)


def radio(n):
    states = []
    un = [((250, 250, 250), (138, 138, 138)), ((240, 240, 240), (128, 128, 128)),
          ((232, 232, 232), (160, 160, 160)), ((247, 247, 247), (200, 200, 200))]
    for fill, border in un:
        im, d = canvas(n, n)
        d.ellipse((0, 0, n * SS - 1, n * SS - 1), fill=border + (255,))
        d.ellipse((SS, SS, (n - 1) * SS - 1, (n - 1) * SS - 1), fill=fill + (255,))
        states.append(down(im, n, n))
    for c, dot in ((ACCENT, .28), (ACCENT_HOT, .32), (ACCENT_PRESS, .24), ((200, 200, 200), .28)):
        im, d = canvas(n, n)
        d.ellipse((0, 0, n * SS - 1, n * SS - 1), fill=c + (255,))
        r = n * SS * dot; cx = n * SS / 2
        d.ellipse((cx - r, cx - r, cx + r, cx + r), fill=(255, 255, 255, 255))
        states.append(down(im, n, n))
    return strip(states)


for n in (13, 16, 25):
    save32(checkbox(n), 'LIGHT_CHECKBOX%d.bmp' % n)
    save32(radio(n), 'LIGHT_RADIOBUTTON%d.bmp' % n)


# ---------------------------------------------------------------- progress
im, d = canvas(61, 14); rrect(d, (0, 4, 61, 10), 3, fill=(214, 214, 214, 255)); save32(down(im, 61, 14), 'LIGHT_PROGRESSTRACK.bmp')
im, d = canvas(13, 61); rrect(d, (4, 0, 9, 61), 3, fill=(214, 214, 214, 255)); save32(down(im, 13, 61), 'LIGHT_PROGRESSTRACKVERT.bmp')
im, d = canvas(49, 19); rrect(d, (0, 6, 49, 13), 3, fill=ACCENT + (255,)); save32(down(im, 49, 19), 'LIGHT_PROGRESSCHUNK.bmp')
im, d = canvas(19, 49); rrect(d, (6, 0, 13, 49), 3, fill=ACCENT + (255,)); save32(down(im, 19, 49), 'LIGHT_PROGRESSCHUNKVERT.bmp')


# ---------------------------------------------------------------- taskbar
def solid(w, h, top_line=None, left_line=None):
    im = Image.new('RGB', (w, h), MICA)
    d = ImageDraw.Draw(im)
    if top_line:
        d.line((0, 0, w - 1, 0), fill=top_line)
    if left_line:
        d.line((0, 0, 0, h - 1), fill=left_line)
    return im


TB_LINE = (222, 222, 222)
save24(solid(50, 30, top_line=TB_LINE), 'LIGHT_TASKBARBACKGROUNDBOTTOM.bmp')
save24(solid(50, 30), 'LIGHT_TASKBARBACKGROUNDTOP.bmp')
save24(solid(30, 50), 'LIGHT_TASKBARBACKGROUNDLEFT.bmp')
save24(solid(30, 50, left_line=TB_LINE), 'LIGHT_TASKBARBACKGROUNDRIGHT.bmp')
for name, size in (('BOTTOM', (15, 4)), ('TOP', (15, 4)), ('LEFT', (4, 15)), ('RIGHT', (4, 15))):
    save24(solid(*size), 'LIGHT_TASKBARSIZINGBAR%s.bmp' % name)
save24(solid(110, 28), 'LIGHT_TASKBARTRAY.bmp')
save24(solid(28, 110), 'LIGHT_TASKBARTRAYVERTICAL.bmp')
save24(solid(28, 10), 'LIGHT_TASKBANDBACKGROUND.bmp')


def task_button(w=26, h=28, vertical=False):
    # normal, hot, pressed, disabled, checked (active window), hot+checked
    specs = [(None, 'run'), ((0, 0, 0, 14), 'run'), ((0, 0, 0, 9), 'run'), (None, None),
             ((0, 0, 0, 12), 'active'), ((0, 0, 0, 20), 'active')]
    states = []
    for bg, pill in specs:
        im, d = canvas(w, h)
        if bg:
            rrect(d, (1, 1, w - 1, h - 1), 4, fill=bg)
        if pill:
            S = SS
            if vertical:
                ph = 8 if pill == 'active' else 3
                cy = h / 2
                d.rounded_rectangle((1 * S, (cy - ph / 2) * S, 4 * S, (cy + ph / 2) * S), radius=1.5 * S,
                                    fill=(ACCENT if pill == 'active' else (138, 138, 138)) + (255,))
            else:
                pw = 8 if pill == 'active' else 3
                cx = w / 2
                d.rounded_rectangle(((cx - pw / 2) * S, (h - 4) * S, (cx + pw / 2) * S, (h - 1) * S),
                                    radius=1.5 * S,
                                    fill=(ACCENT if pill == 'active' else (138, 138, 138)) + (255,))
        states.append(down(im, w, h))
    return strip(states)


save32(task_button(), 'LIGHT_TASKBANDBUTTON.bmp')
save32(task_button(), 'LIGHT_TASKBANDBUTTONNOEDGE.bmp')
save32(task_button(vertical=True), 'LIGHT_TASKBANDBUTTONVERTICAL.bmp')
save32(task_button(vertical=True), 'LIGHT_TASKBANDBUTTONNOEDGEVERTICAL.bmp')

# Start button background: transparent, soft rounded hover like the task buttons.
start = []
for bg in (None, (0, 0, 0, 14), (0, 0, 0, 9)):
    im, d = canvas(52, 30)
    if bg:
        rrect(d, (1, 1, 51, 29), 4, fill=bg)
    start.append(down(im, 52, 30))
save32(strip(start), 'LIGHT_STARTBUTTON.bmp')

print('Lumen bitmaps written to', OUT)
