#!/usr/bin/env python3
"""AI Treasure Hunt — 1080x1920 story short. Renders one mp4 per scene, concats, adds music."""
import math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
GF = "/usr/share/fonts/truetype/google-fonts/"
def F(name, size):
    p = {"anton": GF + "ofl/anton/Anton-Regular.ttf", "pop": GF + "Poppins-Bold.ttf", "lora": GF + "Lora-Italic-Variable.ttf"}[name]
    return ImageFont.truetype(p, size)
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
_ecache = {}
def emoji(ch, size):
    k = (ch, size)
    if k not in _ecache:
        im = Image.new("RGBA", (160, 160)); ImageDraw.Draw(im).text((80, 80), ch, font=ImageFont.truetype(EMOJI_FONT, 109), embedded_color=True, anchor="mm")
        _ecache[k] = im.resize((size, size), Image.LANCZOS)
    return _ecache[k]

rng = random.Random(7)
def clamp(x): return max(0.0, min(1.0, x))
def ease(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease_back(x):
    x = clamp(x); c = 1.7; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def vgrad(top, bot, w=W, h=H):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top)[None, None, :] * (1 - t) + np.array(bot)[None, None, :] * t
    return Image.fromarray(np.repeat(a, w, 1).astype(np.uint8), "RGB").convert("RGBA")

def glow(size, color, power=2.2):
    yy, xx = np.mgrid[0:size, 0:size]; r = np.hypot(xx - size / 2, yy - size / 2) / (size / 2)
    a = np.clip(1 - r, 0, 1) ** power
    arr = np.zeros((size, size, 4), np.uint8); arr[..., :3] = color; arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")

def paste(base, im, cx, cy, s=1.0, alpha=1.0, rot=0):
    if s <= 0.01 or alpha <= 0.01: return
    if s != 1.0: im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    if rot: im = im.rotate(rot, Image.BILINEAR, expand=True)
    if alpha < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def kenburns(img, t, z0=1.0, z1=1.12, dx=0, dy=0):
    z = z0 + (z1 - z0) * t
    cw, ch = W / z, H / z
    cx = img.width / 2 + dx * t; cy = img.height / 2 + dy * t
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return img.resize((W, H), Image.BILINEAR, box=box)

# ---------- text helpers ----------
def wrap(text, fnt, maxw):
    d = ImageDraw.Draw(Image.new("L", (1, 1))); out = []
    for para in text.split("\n"):
        line = ""
        for w in para.split():
            tst = (line + " " + w).strip()
            if d.textlength(tst, font=fnt) <= maxw: line = tst
            else: out.append(line); line = w
        out.append(line)
    return out

CAP_F = F("pop", 60)
def caption(base, text, t, start=0.3, cps=28, y=1450):
    """typewriter caption in a dark rounded box"""
    n = int(max(0, t - start) * cps)
    if n <= 0: return
    lines = wrap(text, CAP_F, 900)
    lh = 84; bh = lh * len(lines) + 60
    a = clamp((t - start) / 0.25)
    box = Image.new("RGBA", (W - 80, bh)); ImageDraw.Draw(box).rounded_rectangle((0, 0, W - 81, bh - 1), 36, fill=(10, 6, 20, int(170 * a)), outline=(255, 205, 90, int(200 * a)), width=4)
    base.alpha_composite(box, (40, y))
    d = ImageDraw.Draw(base); shown = 0
    for i, l in enumerate(lines):
        part = l[:max(0, n - shown)]; shown += len(l) + 1
        if part:
            d.text((W / 2 - d.textlength(l, font=CAP_F) / 2, y + 30 + i * lh), part, font=CAP_F, fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))

def gold_text(text, fnt, top=(255, 250, 210), bot=(255, 160, 20), stroke=9, glowc=(255, 190, 60)):
    lines = text.split("\n"); d = ImageDraw.Draw(Image.new("L", (1, 1)))
    ws = [d.textlength(l, font=fnt) for l in lines]; asc, desc = fnt.getmetrics(); lh = int((asc + desc) * 1.05)
    w, h = int(max(ws)) + 80, lh * len(lines) + 80
    m = Image.new("L", (w, h)); s = Image.new("L", (w, h)); dm, ds = ImageDraw.Draw(m), ImageDraw.Draw(s)
    for i, l in enumerate(lines):
        x = (w - ws[i]) / 2; yy = 40 + i * lh
        dm.text((x, yy), l, font=fnt, fill=255); ds.text((x, yy), l, font=fnt, fill=255, stroke_width=stroke, stroke_fill=255)
    out = Image.new("RGBA", (w, h))
    g = Image.new("RGBA", (w, h), glowc + (0,)); g.putalpha(s.filter(ImageFilter.GaussianBlur(18)).point(lambda v: min(255, v * 2)))
    out.alpha_composite(g)
    sh = Image.new("RGBA", (w, h), (40, 10, 0, 255)); sh.putalpha(s); out.alpha_composite(sh)
    fill = vgrad(top, bot, w, h); fill.putalpha(m); out.alpha_composite(fill)
    return out

# ---------- particles ----------
class Sparks:
    def __init__(s, n, area, color=(255, 220, 120), seed=1):
        r = random.Random(seed); x0, y0, x1, y1 = area
        s.p = [(r.uniform(x0, x1), r.uniform(y0, y1), r.uniform(0, 6.28), r.uniform(0.5, 1.6), r.uniform(4, 11)) for _ in range(n)]; s.c = color
    def draw(s, base, t, rise=40):
        d = ImageDraw.Draw(base)
        for x, y, ph, sp, sz in s.p:
            a = 0.5 + 0.5 * math.sin(t * 3 * sp + ph); yy = y - t * rise * sp
            r = sz * (0.5 + a * 0.7)
            d.ellipse((x - r, yy - r, x + r, yy + r), fill=s.c + (int(200 * a),))
            if a > 0.85: d.line((x - r * 3, yy, x + r * 3, yy), fill=s.c + (180,), width=2); d.line((x, yy - r * 3, x, yy + r * 3), fill=s.c + (180,), width=2)

def rays(size, n=16, color=(255, 210, 100)):
    im = Image.new("RGBA", (size, size)); d = ImageDraw.Draw(im); c = size / 2
    for k in range(n):
        a0 = k * 2 * math.pi / n; a1 = a0 + math.pi / n * 0.5
        d.polygon([(c, c), (c + c * 1.5 * math.cos(a0), c + c * 1.5 * math.sin(a0)), (c + c * 1.5 * math.cos(a1), c + c * 1.5 * math.sin(a1))], fill=color + (70,))
    m = glow(size, (255, 255, 255), 1.0).getchannel("A")
    im.putalpha(Image.fromarray((np.array(im.getchannel("A"), float) * np.array(m, float) / 255).astype(np.uint8)))
    return im.filter(ImageFilter.GaussianBlur(4))

# ---------- props ----------
def parchment(w, h, seed=3):
    r = np.random.default_rng(seed)
    base = np.array(vgrad((236, 212, 160), (205, 170, 110), w, h)).astype(float)
    noise = r.normal(0, 1, (h // 8, w // 8)); n = np.array(Image.fromarray(((noise + 3) * 40).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), float) / 255 - 0.5
    base[..., :3] += n[..., None] * 30
    yy, xx = np.mgrid[0:h, 0:w]; edge = np.minimum.reduce([xx, yy, w - xx, h - yy]) / 90
    burn = np.clip(1 - edge, 0, 1) ** 1.5
    base[..., :3] = base[..., :3] * (1 - burn[..., None] * 0.6) + np.array([90, 50, 20]) * burn[..., None] * 0.6
    img = Image.fromarray(base.clip(0, 255).astype(np.uint8), "RGBA")
    mask = Image.new("L", (w, h), 0); md = ImageDraw.Draw(mask)
    pts = []
    for i in range(40): pts.append((w * i / 40, r.uniform(0, 18)))
    for i in range(40): pts.append((w - r.uniform(0, 18), h * i / 40))
    for i in range(40): pts.append((w - w * i / 40, h - r.uniform(0, 18)))
    for i in range(40): pts.append((r.uniform(0, 18), h - h * i / 40))
    md.polygon(pts, fill=255); img.putalpha(mask)
    return img

MAP_W, MAP_H = 940, 1180
PATH = [(150, 1040), (260, 930), (220, 800), (360, 700), (520, 760), (640, 640), (560, 500), (690, 380), (800, 250)]
def map_layer():
    m = parchment(MAP_W, MAP_H); d = ImageDraw.Draw(m); ink = (70, 40, 15, 255)
    # river
    rv = [(0, 560 + 60 * math.sin(i / 6)) for i in range(0)]
    pts = [(x, 600 + 70 * math.sin(x / 120)) for x in range(0, MAP_W, 10)]
    d.line(pts, fill=(60, 110, 150, 220), width=22); d.line(pts, fill=(120, 170, 200, 200), width=8)
    # mountains
    for mx in (120, 230, 340):
        d.polygon([(mx - 70, 330), (mx, 200), (mx + 70, 330)], outline=ink, fill=(170, 130, 80, 255), width=5)
        d.line([(mx - 18, 235), (mx, 200), (mx + 18, 235)], fill=(250, 245, 230, 255), width=6)
    # palms
    for px, py in ((600, 860), (690, 900), (780, 850)):
        d.line([(px, py), (px + 10, py - 80)], fill=ink, width=8)
        for a in range(5):
            ang = math.pi * (1.1 + a * 0.2); d.line([(px + 10, py - 80), (px + 10 + 55 * math.cos(ang), py - 80 + 35 * math.sin(ang) + 15)], fill=(40, 90, 30, 255), width=8)
    # compass rose
    cx, cy = 790, 1030
    for k in range(8):
        a = k * math.pi / 4; L = 80 if k % 2 == 0 else 45
        d.polygon([(cx + L * math.cos(a), cy + L * math.sin(a)), (cx + 12 * math.cos(a + 1.57), cy + 12 * math.sin(a + 1.57)), (cx + 12 * math.cos(a - 1.57), cy + 12 * math.sin(a - 1.57))], fill=ink)
    d.text((cx, cy - 105), "N", font=F("lora", 44), fill=ink, anchor="mm")
    d.text((MAP_W / 2, 90), "Isle of Fortune", font=F("lora", 74), fill=ink, anchor="mm")
    return m

def draw_path(m, frac):
    d = ImageDraw.Draw(m); seg = []
    total = sum(math.dist(PATH[i], PATH[i + 1]) for i in range(len(PATH) - 1)); want = total * frac; acc = 0
    pts = [PATH[0]]
    for i in range(len(PATH) - 1):
        L = math.dist(PATH[i], PATH[i + 1])
        if acc + L >= want:
            f = (want - acc) / L; pts.append((PATH[i][0] + (PATH[i + 1][0] - PATH[i][0]) * f, PATH[i][1] + (PATH[i + 1][1] - PATH[i][1]) * f)); break
        pts.append(PATH[i + 1]); acc += L
    # dashed
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]; L = math.dist(pts[i], pts[i + 1]); k = 0
        while k < L:
            e = min(L, k + 22); d.line([(x0 + (x1 - x0) * k / L, y0 + (y1 - y0) * k / L), (x0 + (x1 - x0) * e / L, y0 + (y1 - y0) * e / L)], fill=(170, 20, 20, 255), width=9); k += 38
    return pts[-1]

def draw_x(m, cx, cy, s, a=1.0):
    d = ImageDraw.Draw(m); r = 42 * s; c = (200, 10, 10, int(255 * a))
    d.line([(cx - r, cy - r), (cx + r, cy + r)], fill=c, width=int(16 * s)); d.line([(cx - r, cy + r), (cx + r, cy - r)], fill=c, width=int(16 * s))

def ai_orb(t, size=360):
    im = Image.new("RGBA", (size * 2, size * 2)); c = size
    paste(im, glow(size * 2, (60, 180, 255), 1.8), c, c, 1.0, 0.9)
    d = ImageDraw.Draw(im); r = size * 0.42
    d.ellipse((c - r, c - r, c + r, c + r), fill=(20, 40, 90, 255), outline=(140, 230, 255, 255), width=8)
    for k in range(3):  # orbit rings
        a = t * (1.5 + k * 0.7) + k
        rr = r * (1.25 + 0.18 * k); d.arc((c - rr, c - rr * 0.45, c + rr, c + rr * 0.45), math.degrees(a), math.degrees(a) + 220, fill=(120, 220, 255, 200), width=5)
    # eyes
    blink = 0.15 if (t % 2.6) < 0.12 else 1.0
    for ex in (-r * 0.35, r * 0.35):
        d.rounded_rectangle((c + ex - 26, c - 40 * blink, c + ex + 26, c + 40 * blink), 20, fill=(190, 250, 255, 255))
    d.arc((c - 60, c + 20, c + 60, c + 95), 20, 160, fill=(190, 250, 255, 255), width=8)
    return im

def jungle_bg():
    bg = vgrad((12, 20, 60), (30, 70, 70)); d = ImageDraw.Draw(bg); r = random.Random(4)
    for _ in range(160):
        x, y = r.uniform(0, W), r.uniform(0, 900); s = r.uniform(1, 3.5); d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 255, 230, r.randint(120, 255)))
    paste(bg, glow(700, (220, 230, 255), 2.5), 780, 700, 1.0, 0.7)
    d.ellipse((700, 620, 860, 780), fill=(245, 245, 225, 255))
    return bg

def jungle_layer(seed, color, ybase, dense):
    im = Image.new("RGBA", (W + 400, H)); d = ImageDraw.Draw(im); r = random.Random(seed)
    d.rectangle((0, ybase, W + 400, H), fill=color)
    x = -50
    while x < W + 450:
        h = r.uniform(250, 600) * dense; tx = x + r.uniform(-20, 20)
        d.line([(tx, ybase + 20), (tx + r.uniform(-40, 40), ybase - h)], fill=color, width=int(r.uniform(14, 26)))
        top = (tx, ybase - h)
        for a in range(7):
            ang = math.pi * (0.95 + a * 0.18); L = r.uniform(130, 220)
            mid = (top[0] + L * 0.5 * math.cos(ang), top[1] + L * 0.5 * math.sin(ang) - 30)
            end = (top[0] + L * math.cos(ang), top[1] + L * math.sin(ang) + 40)
            d.line([top, mid, end], fill=color, width=22, joint="curve")
        for _ in range(4):
            bx = x + r.uniform(-60, 120); br = r.uniform(70, 150); d.ellipse((bx - br, ybase - br * 0.7, bx + br, ybase + br * 0.7), fill=color)
        x += r.uniform(160, 300) / dense
    return im

def chest(open_f, t):
    im = Image.new("RGBA", (700, 700)); d = ImageDraw.Draw(im)
    wood, dark, gold = (120, 65, 25, 255), (70, 35, 12, 255), (240, 190, 60, 255)
    d.rounded_rectangle((110, 380, 590, 620), 20, fill=wood, outline=dark, width=8)
    for x in (110, 330, 550): d.rectangle((x, 380, x + 40, 620), fill=gold, outline=dark, width=4)
    d.rectangle((310, 400, 390, 480), fill=gold, outline=dark, width=5); d.ellipse((338, 425, 362, 449), fill=dark)
    # lid
    lid = Image.new("RGBA", (500, 220)); ld = ImageDraw.Draw(lid)
    ld.pieslice((0, 0, 500, 300), 180, 360, fill=wood, outline=dark, width=8); ld.rectangle((0, 140, 500, 210), fill=wood, outline=dark, width=8)
    for x in (0, 220, 440): ld.rectangle((x, 40 if x == 220 else 90, x + 40 + (20 if x == 440 else 0), 210), fill=gold)
    h = max(8, int(220 * math.cos(open_f * math.pi * 0.45)))
    lid2 = lid.resize((500, h), Image.BILINEAR)
    if open_f > 0:
        paste(im, glow(600, (255, 220, 100), 1.6), 350, 380, 1.0, open_f)
    im.alpha_composite(lid2, (100, 390 - h))
    return im

