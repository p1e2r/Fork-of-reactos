#!/usr/bin/env python3
"""Original Lumen boot logo: the start-button spark above a "Lumen" wordmark.
Quantized to the boot screen's existing 16-color palette (the copyright line and
progress bar drawn next to it use the same palette)."""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from startglyph import glyph

LOGO = 'ntoskrnl/inbv/resources/logo.bmp'
FONT = sys.argv[1] if len(sys.argv) > 1 else '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'

ref = Image.open(sys.argv[2] if len(sys.argv) > 2 else LOGO)
W, H = ref.size
palette = ref.getpalette()[:48]

im = Image.new('RGB', (W, H), (0, 0, 0))
g = glyph(132)
glow = Image.new('RGBA', g.size, (60, 150, 255, 0))
glow.putalpha(g.split()[3].filter(ImageFilter.GaussianBlur(10)).point(lambda v: v // 2))
im.paste(glow, ((W - 132) // 2, 14), glow)
im.paste(g, ((W - 132) // 2, 14), g)
d = ImageDraw.Draw(im)
font = ImageFont.truetype(FONT, 50)
tw = d.textlength('Lumen', font=font)
d.text(((W - tw) / 2, 160), 'Lumen', font=font, fill=(235, 242, 250))

pal_img = Image.new('P', (1, 1))
pal_img.putpalette(palette + [0] * (768 - 48))
out = im.quantize(palette=pal_img, dither=Image.Dither.NONE)
# 4 bits per pixel, like the original boot bitmaps
import struct
rowlen = ((W * 4 + 31) // 32) * 4
px = out.load()
rows = []
for y in range(H - 1, -1, -1):
    r = bytearray(rowlen)
    for x in range(W):
        v = px[x, y] & 15
        r[x // 2] |= v << 4 if x % 2 == 0 else v
    rows.append(bytes(r))
data = b''.join(rows)
pal = b''.join(bytes((palette[i * 3 + 2], palette[i * 3 + 1], palette[i * 3], 0)) for i in range(16))
off = 14 + 40 + len(pal)
hdr = struct.pack('<2sIHHI', b'BM', off + len(data), 0, 0, off)
hdr += struct.pack('<IiiHHIIiiII', 40, W, H, 1, 4, 0, len(data), 0, 0, 16, 16)
open(LOGO, 'wb').write(hdr + pal + data)
out.convert('RGB').resize((W * 2, H * 2)).save('/tmp/lumen_bootlogo.png')
print('wrote', LOGO)
