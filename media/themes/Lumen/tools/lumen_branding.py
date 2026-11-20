#!/usr/bin/env python3
"""Original Lumen branding images (About boxes, logon, setup wizard, System
Properties): the start-button spark with a "Lumen" wordmark.

Run from the repository root:  python3 media/themes/Lumen/tools/lumen_branding.py [font.otf]"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from startglyph import glyph

FONT = sys.argv[1] if len(sys.argv) > 1 else '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
INK = (32, 36, 44)


def font(size):
    return ImageFont.truetype(FONT, size)


def save_like(im, path):
    """Save in the same pixel format as the file being replaced."""
    old = Image.open(path)
    if old.mode == 'P':
        im = im.convert('RGB').quantize(256)
    else:
        im = im.convert('RGB')
    im.save(path, 'BMP')


def flag(path, bg):
    im = Image.new('RGB', (48, 40), bg)
    g = glyph(36)
    im.paste(g, (6, 2), g)
    save_like(im, path)


def header(path):
    im = Image.new('RGB', (49, 49), (255, 255, 255))
    g = glyph(40)
    im.paste(g, (4, 4), g)
    save_like(im, path)


def watermark(path):
    w, h = 164, 400
    im = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / h
        d.line((0, y, w, y), fill=(int(14 + 20 * t), int(40 + 60 * t), int(90 + 110 * t)))
    g = glyph(96)
    glow = Image.new('RGBA', g.size, (120, 190, 255, 0))
    glow.putalpha(g.split()[3].filter(ImageFilter.GaussianBlur(8)))
    im.paste(glow, ((w - 96) // 2, 110), glow)
    im.paste(g, ((w - 96) // 2, 110), g)
    f = font(34)
    tw = d.textlength('Lumen', font=f)
    d.text(((w - tw) / 2, 222), 'Lumen', font=f, fill=(240, 246, 255))
    save_like(im, path)


def sysdm(path, mask_path):
    w, h = 320, 159
    logo = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    g = glyph(120)
    logo.alpha_composite(g, (8, 20))
    d = ImageDraw.Draw(logo)
    d.text((132, 46), 'Lumen', font=font(56), fill=INK + (255,))
    im = Image.new('RGB', (w, h), (255, 255, 255))
    im.paste(logo, (0, 0), logo)
    save_like(im, path)
    a = logo.split()[3]
    glow = a.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(3))
    mask = Image.composite(Image.new('L', (w, h), 255), glow, a)
    old = Image.open(mask_path)
    out = mask.convert('P') if old.mode == 'P' else mask
    out.save(mask_path, 'BMP')


flag('dll/win32/shell32/res/bitmaps/reactos_flag.bmp', (29, 29, 29))
flag('dll/win32/msgina/resources/reactos_flag.bmp', (29, 29, 29))
for base in ('dll/win32/syssetup/resources/', 'base/setup/reactos/res/'):
    header(base + 'header.bmp')
    watermark(base + 'watermark.bmp')
sysdm('dll/cpl/sysdm/resources/rosbitmap.bmp', 'dll/cpl/sysdm/resources/rosbitmap_mask.bmp')
print('branding images written')
