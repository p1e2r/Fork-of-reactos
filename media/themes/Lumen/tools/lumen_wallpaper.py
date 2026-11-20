#!/usr/bin/env python3
"""Original 'Lumen' wallpaper: luminous translucent ribbons sweeping across a soft
blue backdrop. Drawn from scratch with layered gradients (no third-party artwork).

Usage: python3 lumen_wallpaper.py <out.bmp> <width> <height>
"""
import math, sys
import numpy as np
from PIL import Image, ImageFilter

W, H = int(sys.argv[2]), int(sys.argv[3])
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
u, v = x / W, y / H

# backdrop: pale sky blue at the top right, deeper blue at the bottom left
t = np.clip(0.6 * (1 - u) * 0.6 + 0.7 * v, 0, 1)[..., None]
top = np.array([196, 222, 246], np.float32)
bottom = np.array([24, 78, 168], np.float32)
img = top * (1 - t) + bottom * t

def band(center_fn, width, c_edge, c_core, alpha):
    """A translucent ribbon whose spine follows center_fn(u); brighter at its folded edge."""
    global img
    cy = center_fn(u)
    d = (v - cy) / width
    body = np.exp(-(d ** 2) * 1.6)
    edge = np.exp(-((d + 0.85) ** 2) * 12.0)      # bright rim along the upper edge
    shade = np.clip(0.5 + 0.5 * d, 0, 1)[..., None]  # darker towards the lower side
    col = np.array(c_core, np.float32) * (1 - shade) + np.array(c_edge, np.float32) * shade
    a = (alpha * body)[..., None]
    img = img * (1 - a) + col * a
    rim = (0.55 * edge)[..., None]
    img = img * (1 - rim) + np.array([250, 252, 255], np.float32) * rim

band(lambda s: 0.80 - 0.42 * np.sin(math.pi * (s * 0.95 + 0.05)) + 0.10 * s, 0.11, (18, 70, 170), (90, 160, 245), 0.85)
band(lambda s: 0.88 - 0.36 * np.sin(math.pi * (s * 0.90 + 0.12)) + 0.06 * s, 0.085, (30, 96, 200), (120, 190, 255), 0.80)
band(lambda s: 0.96 - 0.30 * np.sin(math.pi * (s * 0.85 + 0.20)), 0.065, (40, 110, 214), (160, 212, 255), 0.75)

# center glow
r = np.sqrt(((u - 0.55) * 1.6) ** 2 + (v - 0.55) ** 2)
glow = np.clip(1 - r / 0.55, 0, 1)[..., None] ** 2 * 0.25
img = img * (1 - glow) + np.array([255, 255, 255], np.float32) * glow

im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB').filter(ImageFilter.GaussianBlur(1.5))
im.save(sys.argv[1])
print('wrote', sys.argv[1], im.size)
