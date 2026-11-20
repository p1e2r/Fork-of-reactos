#!/usr/bin/env python3
"""Original abstract 'Lumen' wallpaper: a blue gradient with soft flowing light ribbons."""
import math, sys
import numpy as np
from PIL import Image, ImageFilter

W, H = int(sys.argv[2]), int(sys.argv[3])
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
u, v = x / W, y / H

# base diagonal gradient: deep navy (bottom-left) -> bright azure (top-right)
t = np.clip(0.55 * u + 0.45 * (1 - v), 0, 1)[..., None]
navy = np.array([8, 30, 74], np.float32)
azure = np.array([46, 128, 214], np.float32)
img = navy * (1 - t) + azure * t

# soft ribbons of light
def ribbon(phase, amp, freq, center, width, color, strength):
    global img
    cy = center + amp * np.sin(2 * math.pi * (freq * u + phase)) + 0.04 * np.sin(2 * math.pi * (3.1 * u + phase * 2))
    d = (v - cy) / width
    a = np.exp(-d * d)[..., None] * strength
    img = img * (1 - a) + np.array(color, np.float32) * a

ribbon(0.10, 0.10, 0.75, 0.62, 0.060, (140, 200, 255), 0.55)
ribbon(0.35, 0.12, 0.60, 0.70, 0.030, (220, 240, 255), 0.65)
ribbon(0.62, 0.08, 0.90, 0.55, 0.110, (90, 160, 240), 0.35)
ribbon(0.85, 0.06, 1.10, 0.78, 0.020, (255, 255, 255), 0.45)

# gentle vignette
r = np.sqrt((u - 0.55) ** 2 + (v - 0.5) ** 2)
img *= (1 - 0.35 * np.clip(r - 0.25, 0, 1))[..., None]

im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGB').filter(ImageFilter.GaussianBlur(1.2))
im.save(sys.argv[1])
print('wrote', sys.argv[1], im.size)
