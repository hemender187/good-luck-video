#!/usr/bin/env python3
"""AI Treasure Hunt — 1080x1920 story short. Renders one mp4 per scene, concats, adds music."""
import math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
OUT = sys.argv[1] if len(sys.argv) > 1 else "story.mp4"
TMP = os.path.join(os.path.dirname(os.path.abspath(OUT)) or ".", ".story_tmp")
os.makedirs(TMP, exist_ok=True)
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

# ---------- scenes ----------
scenes = []
def scene(dur):
    def reg(fn): scenes.append((dur, fn)); return fn
    return reg

MAP = map_layer(); XPOS = PATH[-1]
MAP_BG = vgrad((40, 22, 10), (15, 8, 4))
RAYS = rays(1800)

@scene(4.5)
def s_hook(t, i):
    im = vgrad((25, 8, 40), (5, 0, 10)); paste(im, RAYS, W / 2, 820, 1.0, 0.8, rot=t * 12)
    paste(im, glow(900, (255, 180, 60), 2), W / 2, 820, 1.0, 0.8)
    m = MAP.copy(); draw_x(m, *XPOS, 1 + 0.15 * math.sin(t * 8))
    paste(im, m, W / 2, 900, 0.62 * (0.3 + 0.7 * ease_back(t / 0.8)), 1.0, rot=-6 + 4 * math.sin(t))
    tl = gold_text("THE AI\nTREASURE HUNT", F("anton", 150))
    paste(im, tl, W / 2, 330, ease_back((t - 0.4) / 0.5) * 0.95)
    sub = gold_text("a story about luck", F("lora", 70), (255, 255, 255), (230, 220, 255), 5, (180, 120, 255))
    paste(im, sub, W / 2, 1600, 1.0, clamp((t - 1.3) / 0.5))
    Sparks(40, (0, 0, W, H), seed=2).draw(im, t)
    return im

@scene(7.0)
def s_map(t, i):
    im = MAP_BG.copy(); m = MAP.copy()
    end = draw_path(m, ease((t - 1.0) / 4.5))
    paste(m, emoji("🔦", 70), end[0], end[1] - 10, 1.0, clamp((t - 1.0) / 0.3))
    draw_x(m, *XPOS, 1 + 0.12 * math.sin(t * 7))
    bg = Image.new("RGBA", (W, H)); bg.alpha_composite(im); paste(bg, m, W / 2, 720, 1.0)
    out = kenburns(bg, t / 7, 1.0, 1.08, 0, -60)
    caption(out, "Meera found an old map in her grandpa's trunk. One red X... but no one could read the clues.", t)
    return out

@scene(7.0)
def s_ai(t, i):
    im = MAP_BG.copy(); m = MAP.copy(); draw_path(m, 1.0); draw_x(m, *XPOS, 1.0)
    paste(im, m, W / 2, 760, 0.95)
    # scan line
    sy = 200 + (t * 420) % 1150; d = ImageDraw.Draw(im)
    band = Image.new("RGBA", (W, 60)); bd = ImageDraw.Draw(band)
    for k in range(60): bd.line([(0, k), (W, k)], fill=(80, 220, 255, int(120 * (1 - abs(k - 30) / 30))))
    im.alpha_composite(band, (0, int(sy) - 30))
    # grid
    for gx in range(80, W, 120): d.line([(gx, 180), (gx, 1360)], fill=(80, 200, 255, 40), width=2)
    # labels pop
    labels = [("River", 230, 560, 1.2), ("3 Palms", 690, 760, 2.4), ("Lucky Spot!", 800, 160, 3.6)]
    for txt, x, y, ts in labels:
        a = ease_back((t - ts) / 0.4)
        if a > 0:
            lb = Image.new("RGBA", (360, 90)); ld = ImageDraw.Draw(lb); ld.rounded_rectangle((0, 0, 359, 89), 30, fill=(10, 40, 80, 220), outline=(120, 230, 255, 255), width=4)
            ld.text((180, 45), txt, font=F("pop", 44), fill=(200, 250, 255), anchor="mm"); paste(im, lb, min(W - 190, max(190, x)), y, a)
    paste(im, ai_orb(t), 200 + 40 * math.sin(t * 1.3), 1180 + 25 * math.sin(t * 2.1), 0.55 * ease_back(t / 0.6))
    caption(im, "So she asked an AI. It scanned every line and whispered: \"Follow the river... past the three palms.\"", t, start=0.6)
    return im

JBG = jungle_bg(); J1 = jungle_layer(11, (20, 45, 50, 255), 1250, 0.8); J2 = jungle_layer(12, (10, 25, 28, 255), 1500, 1.0); J3 = jungle_layer(13, (3, 8, 10, 255), 1820, 0.35)
FIRE = Sparks(60, (0, 600, W, 1700), (150, 255, 200), seed=9)
@scene(7.0)
def s_jungle(t, i):
    im = JBG.copy()
    im.alpha_composite(J1.crop((int(40 * t), 0, int(40 * t) + W, H)))
    FIRE.draw(im, t, rise=15)
    im.alpha_composite(J2.crop((int(90 * t), 0, int(90 * t) + W, H)))
    # orb lighting the path + girl silhouette walking
    ox, oy = 640 + 30 * math.sin(t * 1.7), 1160 + 20 * math.sin(t * 2.3)
    paste(im, glow(900, (120, 210, 255), 2.2), ox, oy + 250, 1.0, 0.55)
    paste(im, ai_orb(t), ox, oy, 0.32)
    d = ImageDraw.Draw(im); gx, gy = 420, 1640; step = math.sin(t * 6)
    k = (5, 8, 12, 255)
    d.ellipse((gx - 34, gy - 300, gx + 34, gy - 232), fill=k)
    d.polygon([(gx - 45, gy - 230), (gx + 45, gy - 230), (gx + 70, gy - 80), (gx - 70, gy - 80)], fill=k)
    d.line([(gx - 20, gy - 85), (gx - 20 + 35 * step, gy)], fill=k, width=24); d.line([(gx + 20, gy - 85), (gx + 20 - 35 * step, gy)], fill=k, width=24)
    d.line([(gx + 40, gy - 210), (gx + 110, gy - 140 - 20 * step)], fill=k, width=18)
    paste(im, emoji("🗺️", 90), gx + 125, gy - 160 - 20 * step, 1.0, 0.95)
    im.alpha_composite(J3.crop((int(170 * t), 0, int(170 * t) + W, H)))
    caption(im, "Through the dark jungle, the little AI lit the way, one glowing step at a time.", t, y=230)
    return im

COINS = [(random.Random(k).uniform(-1, 1), random.Random(k + 99).uniform(0.6, 1.4), random.Random(k + 7).uniform(0, 6)) for k in range(36)]
@scene(7.0)
def s_chest(t, i):
    im = vgrad((25, 15, 10), (60, 35, 15)); d = ImageDraw.Draw(im)
    # cave mouth
    d.ellipse((-300, -200, W + 300, 1500), fill=(10, 6, 4, 255))
    d.ellipse((-100, 120, W + 100, 1700), fill=(35, 22, 14, 255))
    shake = 6 * math.sin(t * 40) * clamp((t - 2.0) / 0.3) * (1 - clamp((t - 2.8) / 0.3))
    of = ease((t - 2.8) / 0.8)
    if of > 0:
        paste(im, RAYS, W / 2, 1000, 1.0, of * 0.9, rot=t * 20)
    paste(im, chest(of, t), W / 2 + shake, 1050, 1.25)
    if of > 0.3:  # coins burst
        tt = t - 3.2
        for vx, vy, ph in COINS:
            x = W / 2 + vx * 520 * tt; y = 900 - vy * 900 * tt + 700 * tt * tt
            if -100 < y < H: paste(im, emoji("🪙", 70), x, y, 1.0, 1.0, rot=int((ph + tt * 8) * 60) % 360)
        for k, e in enumerate(["💎", "🍀", "✨"]):
            paste(im, emoji(e, 120), W / 2 + (k - 1) * 220, 760 - 160 * ease_back((t - 3.4 - k * 0.15) / 0.5), ease_back((t - 3.4 - k * 0.15) / 0.5))
    Sparks(50, (0, 400, W, 1600), seed=5).draw(im, t)
    caption(im, "Under the last palm, a cave. A chest. Meera held her breath... and it OPENED!", t, y=1520)
    return im

FINAL1 = gold_text("YOUR LUCK\nIS UNLOCKED", F("anton", 160))
NOTE = parchment(900, 520, seed=8)
@scene(8.0)
def s_final(t, i):
    im = vgrad((60, 20, 80), (10, 0, 20)); paste(im, RAYS, W / 2, 860, 1.2, 0.9, rot=-t * 15)
    paste(im, glow(1000, (255, 200, 80), 2), W / 2, 860, 1.0, 0.8)
    for k in range(26):  # coin rain
        r = random.Random(k); x = r.uniform(40, W - 40); y = (r.uniform(-H, 0) + t * r.uniform(300, 520)) % (H + 200) - 100
        paste(im, emoji(r.choice(["🪙", "🍀", "✨", "💰"]), r.randint(60, 100)), x, y, 1.0, 0.85)
    note = NOTE.copy(); nd = ImageDraw.Draw(note)
    for j, l in enumerate(wrap("Inside was a note: \"The real treasure is the good luck you share.\"", F("lora", 54), 760)):
        nd.text((450, 120 + j * 76), l, font=F("lora", 54), fill=(70, 35, 10), anchor="mm")
    paste(im, note, W / 2, 1050, ease_back(t / 0.6) * 0.95, 1.0, rot=-3)
    paste(im, FINAL1, W / 2, 380, ease_back((t - 1.6) / 0.5) * (1 + 0.03 * math.sin(t * 5)))
    a = ease_back((t - 2.8) / 0.5)
    if a > 0:
        b = Image.new("RGBA", (900, 150)); bd = ImageDraw.Draw(b); bd.rounded_rectangle((0, 0, 899, 149), 75, fill=(230, 30, 70, 255), outline=(255, 255, 255, 255), width=6)
        bd.text((450, 75), "Type YES to claim yours!", font=F("pop", 62), fill=(255, 255, 255), anchor="mm")
        paste(im, b, W / 2, 1500, a * (1 + 0.04 * math.sin(t * 7)))
    d = ImageDraw.Draw(im)
    d.text((W / 2, 1800), "@hemender187Official", font=F("pop", 44), fill=(255, 255, 255, 230), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    Sparks(40, (0, 0, W, H), seed=6).draw(im, t)
    if t > 7.3: im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (t - 7.3) / 0.7))))
    return im

# ---------- audio ----------
SR = 48000
def make_audio(path, cuts, dur):
    n = int(SR * dur); tt = np.arange(n) / SR; mix = np.zeros(n); nf = lambda m: 440 * 2 ** ((m - 69) / 12)
    def env(st, d, a=0.02, rel=0.5):
        e = np.zeros(n); s0 = int(st * SR); s1 = min(n, int((st + d + rel) * SR))
        if s0 >= n: return e
        x = (np.arange(s0, s1) - s0) / SR; e[s0:s1] = np.minimum(1, x / a) * np.where(x < d, 1, np.exp(-(x - d) * 5)); return e
    prog = [[57, 60, 64], [53, 57, 60], [55, 59, 62], [52, 55, 59]]  # Am F G Em  (adventure, minor)
    bright = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
    bar = 2.0; k = 0; reveal = cuts[4] + 2.8
    while k * bar < dur:
        st = k * bar; ch = (bright if st >= reveal - 0.8 else prog)[k % 4]
        for m in ch: f = nf(m - 12); mix += 0.045 * env(st, bar, 0.4, 0.6) * (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 2 * f * tt))
        mix += 0.09 * env(st, bar * 0.9, 0.02, 0.3) * np.sin(2 * np.pi * nf(ch[0] - 24) * tt)
        for j in range(8):  # pluck arpeggio
            s = st + j * bar / 8
            if s >= dur: break
            m = (ch + [ch[0] + 12, ch[1] + 12])[[0, 1, 2, 3, 4, 3, 2, 1][j]]
            s0 = int(s * SR); x = tt[s0:] - s; f = nf(m + 12)
            mix[s0:] += 0.05 * np.exp(-x * 6) * (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(2 * np.pi * 3 * f * x) * np.exp(-x * 10))
        # drum: soft kick on beats
        for b in range(4):
            s = st + b * 0.5
            if s >= dur: break
            s0 = int(s * SR); x = tt[s0:s0 + SR // 4] - s
            mix[s0:s0 + len(x)] += 0.18 * np.exp(-x * 25) * np.sin(2 * np.pi * (50 + 90 * np.exp(-x * 30)) * x)
        k += 1
    rn = np.random.default_rng(1)
    for c in cuts[1:]:  # whoosh at cuts
        mix += 0.05 * rn.standard_normal(n) * np.exp(-((tt - c) ** 2) / 0.01)
    # rumble + chime burst at chest
    r0 = cuts[4] + 2.0; rs = (tt > r0) & (tt < r0 + 0.9); mix[rs] += 0.12 * np.sin(2 * np.pi * 45 * tt[rs]) * rn.uniform(0.6, 1, rs.sum())
    for j, m in enumerate([84, 88, 91, 96, 100, 103]):
        s = reveal + j * 0.06; s0 = int(s * SR); x = tt[s0:] - s; mix[s0:] += 0.08 * np.exp(-x * 2.5) * np.sin(2 * np.pi * nf(m) * x)
    fade = np.clip(np.minimum(tt / 0.05, (dur - tt) / 1.0), 0, 1); mix *= fade
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.85
    st = np.stack([mix, np.roll(mix, 300)], 1)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((st * 32767).astype(np.int16).tobytes())

# ---------- render ----------
def render_scene(idx, dur, fn):
    final = os.path.join(TMP, f"s{idx}.mp4"); part = os.path.join(TMP, f"s{idx}.part.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0", part], stdin=subprocess.PIPE)
    N = int(dur * FPS)
    for i in range(N):
        t = i / FPS; im = fn(t, i)
        if idx > 0 and t < 0.25: im = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), im, t / 0.25)
        p.stdin.write(im.convert("RGB").tobytes())
    p.stdin.close(); assert p.wait() == 0; os.replace(part, final); return final

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "preview":
        for idx, (dur, fn) in enumerate(scenes):
            for tt in (dur * 0.5, dur * 0.85): fn(tt, 0).convert("RGB").save(os.path.join(TMP, f"p{idx}_{tt:.1f}.jpg"), quality=80)
        sys.exit()
    files = [render_scene(k, d, fn) for k, (d, fn) in enumerate(scenes)]
    cuts = np.cumsum([0] + [d for d, _ in scenes])[:-1].tolist(); dur = sum(d for d, _ in scenes)
    lst = os.path.join(TMP, "list.txt"); open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    wav = os.path.join(TMP, "a.wav"); make_audio(wav, cuts, dur)
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav, "-map", "0:v", "-map", "1:a",
                           "-c:v", "copy", "-c:a", "aac", "-ar", "48000", "-b:a", "160k", "-movflags", "+faststart", "-shortest", OUT])
    print("wrote", OUT, dur, "s")
