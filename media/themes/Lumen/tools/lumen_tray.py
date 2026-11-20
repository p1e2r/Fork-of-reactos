#!/usr/bin/env python3
"""Original Lumen notification-area icons: thin dark monochrome glyphs in a
Windows 11-like spirit (volume, network, battery, safely remove hardware).

Run from the repository root:  python3 media/themes/Lumen/tools/lumen_tray.py
"""
import math, os, struct, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from lumen_icons import bmp_entry  # noqa: E402

SIZES = (32, 24, 20, 16)
K = 16                      # design grid is 16x16, drawn at K x
S = 16 * K
INK = (26, 26, 26, 255)
GREEN = (16, 124, 16, 255)
RED = (196, 43, 28, 255)
LW = int(1.25 * K)          # stroke width in design pixels


def P(*xy):
    return tuple(c * K for c in xy)


def new():
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def speaker(d):
    d.polygon([P(1.5, 6), P(4, 6), P(7.5, 2.5), P(7.5, 13.5), P(4, 10), P(1.5, 10)], outline=INK, width=LW)


def volume():
    im, d = new()
    speaker(d)
    d.arc((*P(6, 4.5), *P(11, 11.5)), -50, 50, fill=INK, width=LW)
    d.arc((*P(6, 2), *P(14.5, 14)), -50, 50, fill=INK, width=LW)
    return im


def volume_mute():
    im, d = new()
    speaker(d)
    d.line((*P(10, 5.5), *P(14.5, 10.5)), fill=INK, width=LW)
    d.line((*P(10, 10.5), *P(14.5, 5.5)), fill=INK, width=LW)
    return im


def network(badge=None):
    im, d = new()
    d.rounded_rectangle((*P(1, 2), *P(15, 11.5)), radius=1.5 * K, outline=INK, width=LW)
    d.line((*P(8, 11.5), *P(8, 14)), fill=INK, width=LW)
    d.line((*P(5, 14.2), *P(11, 14.2)), fill=INK, width=LW)
    if badge == 'off':
        d.line((*P(2, 1), *P(14, 13)), fill=INK, width=LW)
    elif badge == 'error':
        d.ellipse((*P(9, 8), *P(16, 15)), fill=RED)
        d.line((*P(11.2, 10.2), *P(13.8, 12.8)), fill=(255, 255, 255, 255), width=K)
        d.line((*P(11.2, 12.8), *P(13.8, 10.2)), fill=(255, 255, 255, 255), width=K)
    elif badge == 'setup':
        for i, x in enumerate((5, 8, 11)):
            d.ellipse((*P(x - 0.8, 6), *P(x + 0.8, 7.6)), fill=INK)
    return im


def battery(level=None, charging=False, error=False):
    im, d = new()
    d.rounded_rectangle((*P(0.8, 4.5), *P(13.5, 11.5)), radius=1.5 * K, outline=INK, width=LW)
    d.rounded_rectangle((*P(13.8, 6.5), *P(15.3, 9.5)), radius=0.6 * K, fill=INK)
    if level is not None:
        w = 10.4 * level / 5.0
        if w > 0:
            d.rectangle((*P(2.2, 5.9), *P(2.2 + w, 10.1)), fill=GREEN if charging else INK)
    if charging:
        d.polygon([P(8.5, 3), P(5, 8.6), P(7.6, 8.6), P(6.5, 13), P(10.5, 7), P(7.8, 7)], fill=INK,
                  outline=(255, 255, 255, 255))
    if error:
        d.line((*P(5, 6), *P(9.5, 10)), fill=RED, width=LW)
        d.line((*P(5, 10), *P(9.5, 6)), fill=RED, width=LW)
    return im


def ac_plug():
    im, d = new()
    d.line((*P(6, 1.5), *P(6, 5)), fill=INK, width=LW)
    d.line((*P(10, 1.5), *P(10, 5)), fill=INK, width=LW)
    d.rounded_rectangle((*P(3.5, 5), *P(12.5, 9.5)), radius=2 * K, outline=INK, width=LW)
    d.line((*P(8, 9.5), *P(8, 14.5)), fill=INK, width=LW)
    return im


def usb(error=False):
    im, d = new()
    d.rounded_rectangle((*P(4.5, 6), *P(11.5, 14.5)), radius=1.2 * K, outline=INK, width=LW)
    d.rectangle((*P(6, 1.5), *P(10, 6)), outline=INK, width=LW)
    d.line((*P(7.2, 3.2), *P(7.2, 4.2)), fill=INK, width=K)
    d.line((*P(8.8, 3.2), *P(8.8, 4.2)), fill=INK, width=K)
    if error:
        d.ellipse((*P(9, 9), *P(16, 16)), fill=RED)
        d.line((*P(12.5, 10.5), *P(12.5, 13)), fill=(255, 255, 255, 255), width=K)
    return im


def write(master, path):
    imgs = [master.resize((n, n), Image.LANCZOS) for n in SIZES]
    entries = [bmp_entry(i) for i in imgs]
    data = struct.pack('<HHH', 0, 1, len(entries))
    off = 6 + 16 * len(entries)
    for im, e in zip(imgs, entries):
        data += struct.pack('<BBBBHHII', im.size[0], im.size[1], 0, 0, 1, 32, len(e), off)
        off += len(e)
    open(path, 'wb').write(data + b''.join(entries))


ST = 'dll/shellext/stobject/resources/'
NET = 'dll/shellext/netshell/res/'
TARGETS = {
    ST + '3.ico': volume,
    ST + '4.ico': volume_mute,
    ST + '1.ico': lambda: battery(5),
    ST + '2.ico': usb,
    ST + 'hotplug/0.ico': lambda: usb(error=True),
    ST + 'hotplug/1.ico': usb,
    ST + 'battery/error.ico': lambda: battery(error=True),
    ST + 'battery/ac.ico': ac_plug,
    NET + 'netidle.ico': network,
    NET + 'nettrans.ico': network,
    NET + 'netrec.ico': network,
    NET + 'nettrrec.ico': network,
    NET + 'netoff.ico': lambda: network('off'),
    NET + 'neterror.ico': lambda: network('error'),
    NET + 'netsetup.ico': lambda: network('setup'),
}
for i in range(6):
    TARGETS[ST + 'battery/%d.ico' % i] = (lambda i=i: battery(i))
for i in range(5):
    TARGETS[ST + 'battery/charging%d.ico' % i] = (lambda i=i: battery(i + 1, charging=True))

if __name__ == '__main__':
    sheet = Image.new('RGBA', (len(TARGETS) * 40, 40), (243, 243, 243, 255))
    for i, (path, fn) in enumerate(TARGETS.items()):
        m = fn()
        write(m, path)
        sheet.alpha_composite(m.resize((32, 32), Image.LANCZOS), (i * 40 + 4, 4))
    sheet.save('/tmp/lumen_tray.png')
    print('wrote', len(TARGETS), 'tray icons')
