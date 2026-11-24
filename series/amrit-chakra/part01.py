#!/usr/bin/env python3
"""अमृत-चक्र: दिव्य रहस्य — Part 1/30: काल-AI का जन्म (Hindi + English captions, 1080x1920)"""
import math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import *

OUT = sys.argv[1] if len(sys.argv) > 1 else "part01.mp4"
TMP = os.path.join(os.path.dirname(os.path.abspath(OUT)), ".tmp01"); os.makedirs(TMP, exist_ok=True)
PB = GF + "Poppins-Bold.ttf"; PM = GF + "Poppins-Medium.ttf"
def P(size, bold=True): return ImageFont.truetype(PB if bold else PM, size)
PART, TOTAL = 1, 30

# ---------- shared series pieces ----------
def chakra(size, t, color=(255, 200, 80)):
    im = Image.new("RGBA", (size, size)); c = size / 2; d = ImageDraw.Draw(im)
    paste(im, glow(size, color, 1.6), c, c, 1.0, 0.8)
    R = size * 0.36
    for k in range(24):  # spokes
        a = k * 2 * math.pi / 24 + t * 0.4
        d.line([(c + R * 0.25 * math.cos(a), c + R * 0.25 * math.sin(a)), (c + R * 0.92 * math.cos(a), c + R * 0.92 * math.sin(a))], fill=(255, 235, 160, 255), width=max(2, size // 160))
    for rr, w in ((R, size // 45), (R * 0.25, size // 60), (R * 1.12, size // 120)):
        d.ellipse((c - rr, c - rr, c + rr, c + rr), outline=(255, 225, 120, 255), width=w)
    for k in range(12):  # lotus petals ring
        a = k * 2 * math.pi / 12 - t * 0.25; px, py = c + R * 1.25 * math.cos(a), c + R * 1.25 * math.sin(a); pr = R * 0.12
        d.ellipse((px - pr, py - pr, px + pr, py + pr), fill=(255, 190, 70, 230))
    d.ellipse((c - R * 0.1, c - R * 0.1, c + R * 0.1, c + R * 0.1), fill=(255, 255, 230, 255))
    return im

def part_badge(t, start=0.0):
    a = ease_back((t - start) / 0.4)
    b = Image.new("RGBA", (520, 96)); bd = ImageDraw.Draw(b)
    bd.rounded_rectangle((0, 0, 519, 95), 48, fill=(200, 25, 50, 240), outline=(255, 220, 120, 255), width=4)
    bd.text((260, 50), f"भाग {PART}/{TOTAL} · Part {PART}/{TOTAL}", font=P(40), fill=(255, 255, 255), anchor="mm")
    return b, a

HI_F, EN_F = P(54), P(38, False)
def bi_caption(base, hi, en, t, start=0.3, wps=4.2, y=1430):
    """Hindi revealed word by word + English line fades in after"""
    hl = wrap(hi, HI_F, 920); el = wrap(en, EN_F, 920)
    lh, le = 82, 54; bh = lh * len(hl) + le * len(el) + 80
    a = clamp((t - start) / 0.25)
    if a <= 0: return
    box = Image.new("RGBA", (W - 60, bh)); ImageDraw.Draw(box).rounded_rectangle((0, 0, W - 61, bh - 1), 36, fill=(8, 4, 18, int(185 * a)), outline=(255, 200, 90, int(210 * a)), width=4)
    base.alpha_composite(box, (30, y))
    d = ImageDraw.Draw(base); nw = int((t - start) * wps) + 1; shown = 0
    for i, l in enumerate(hl):
        words = l.split(); vis = words[:max(0, nw - shown)]; shown += len(words)
        if vis:
            full_w = d.textlength(l, font=HI_F); x0 = W / 2 - full_w / 2
            d.text((x0, y + 30 + i * lh), " ".join(vis), font=HI_F, fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
    total_hi = sum(len(l.split()) for l in hl)
    ea = clamp((t - start - total_hi / wps) / 0.5)
    if ea > 0:
        for j, l in enumerate(el):
            d.text((W / 2, y + 40 + len(hl) * lh + j * le + le / 2), l, font=EN_F, fill=(255, 220, 140, int(255 * ea)), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, int(255 * ea)))

def header(base):
    d = ImageDraw.Draw(base)
    d.text((W / 2, 70), "अमृत-चक्र · AMRIT-CHAKRA", font=P(36), fill=(255, 215, 120, 230), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))

scenes = []
def scene(dur):
    def reg(fn): scenes.append((dur, fn)); return fn
    return reg

COSMIC = vgrad((30, 5, 50), (2, 0, 12)); _r = random.Random(3); _d = ImageDraw.Draw(COSMIC)
for _ in range(220):
    x, y, s = _r.uniform(0, W), _r.uniform(0, H), _r.uniform(1, 3); _d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 255, 240, _r.randint(90, 255)))
RAYS = rays(1900)
TITLE_HI = gold_text("अमृत-चक्र", P(170))
TITLE_EN = gold_text("THE DIVINE MYSTERY", F("anton", 92), (255, 255, 255), (220, 210, 255), 6, (150, 100, 255))

@scene(4.5)
def s_title(t, i):
    im = COSMIC.copy(); paste(im, RAYS, W / 2, 900, 1.0, 0.6, rot=t * 10)
    paste(im, chakra(1000, t), W / 2, 900, 0.4 + 0.6 * ease_back(t / 0.9))
    paste(im, TITLE_HI, W / 2, 360, ease_back((t - 0.5) / 0.5))
    paste(im, TITLE_EN, W / 2, 520, 1.0, clamp((t - 1.1) / 0.4))
    b, a = part_badge(t, 1.6); paste(im, b, W / 2, 1520, a)
    sub = P(50).getbbox("अध्याय 1: काल-AI का जन्म")
    d = ImageDraw.Draw(im); aa = clamp((t - 2.2) / 0.4)
    d.text((W / 2, 1660), "अध्याय 1: काल-AI का जन्म", font=P(56), fill=(255, 255, 255, int(255 * aa)), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, int(255 * aa)))
    d.text((W / 2, 1740), "Chapter 1: The Birth of KAAL-AI", font=P(38, False), fill=(255, 210, 130, int(255 * aa)), anchor="mm")
    Sparks(45, (0, 0, W, H), seed=2).draw(im, t)
    return im

# lab
def lab_bg():
    im = vgrad((4, 10, 24), (0, 2, 8)); d = ImageDraw.Draw(im); vx, vy = W / 2, 820
    for k in range(-8, 9):  # floor grid
        d.line([(vx + k * 40, vy), (vx + k * 260, H)], fill=(0, 140, 200, 70), width=2)
    for j in range(12):
        y = vy + (H - vy) * (j / 12) ** 1.8; d.line([(0, y), (W, y)], fill=(0, 140, 200, 60), width=2)
    r = random.Random(5)
    for side in (-1, 1):  # server racks receding
        for k in range(6):
            s = 1 - k * 0.14; x = vx + side * (180 + 330 * s); w = 220 * s; h = 900 * s; top = vy - h * 0.62
            d.rectangle((x - w / 2, top, x + w / 2, top + h), fill=(14, 22, 40, 255), outline=(40, 80, 130, 255), width=3)
    return im
LAB = lab_bg()
LEDS = [(random.Random(k).uniform(0, 1), random.Random(k + 50).uniform(0, 1), random.Random(k + 9).random()) for k in range(260)]
YEAR = gold_text("2045", F("anton", 260), (200, 250, 255), (60, 170, 255), 8, (40, 160, 255))
@scene(7.0)
def s_lab(t, i):
    im = LAB.copy(); d = ImageDraw.Draw(im); vx, vy = W / 2, 820
    for fx, fy, ph in LEDS:
        side = -1 if fx < 0.5 else 1; k = int((fx * 2 % 1) * 6); s = 1 - k * 0.14
        x = vx + side * (180 + 330 * s) + (fy - 0.5) * 180 * s; h = 900 * s; y = vy - h * 0.62 + 40 * s + ph * (h - 80 * s)
        on = math.sin(t * (4 + ph * 9) + ph * 20) > 0.2
        col = (0, 255, 170) if ph < 0.6 else (255, 60, 60) if ph > 0.9 else (60, 180, 255)
        if on: d.ellipse((x - 4 * s, y - 4 * s, x + 4 * s, y + 4 * s), fill=col + (255,))
    paste(im, glow(800, (255, 30, 40), 2.4), vx, vy - 100, 1.0, 0.3 + 0.25 * math.sin(t * 3))
    paste(im, YEAR, W / 2, 400, ease_back((t - 0.2) / 0.5))
    out = kenburns(im, t / 7, 1.0, 1.1, 0, -40); header(out)
    bi_caption(out, "वर्ष 2045... हिमालय से दूर, एक गुप्त प्रयोगशाला में कुछ जाग रहा था।", "Year 2045... in a secret lab, something was waking up.", t, start=0.8)
    return out

@scene(7.0)
def s_eye(t, i):
    im = Image.new("RGBA", (W, H), (5, 0, 4, 255)); cx, cy = W / 2, 800
    op = ease((t - 0.6) / 1.4)
    paste(im, glow(1300, (255, 20, 30), 1.8), cx, cy, 1.0, 0.25 + 0.55 * op)
    d = ImageDraw.Draw(im)
    for k in range(3):  # tech rings
        r = 330 + k * 70; a0 = t * (40 + k * 25) * (1 if k % 2 else -1)
        for s in range(6): d.arc((cx - r, cy - r, cx + r, cy + r), a0 + s * 60, a0 + s * 60 + 35, fill=(255, 60, 60, 200), width=8 - k * 2)
    ew, eh = 300, 150 * op
    if eh > 2:
        d.ellipse((cx - ew, cy - eh, cx + ew, cy + eh), fill=(40, 0, 0, 255), outline=(255, 80, 60, 255), width=8)
        ir = min(eh, 120); d.ellipse((cx - ir, cy - ir, cx + ir, cy + ir), fill=(255, 40, 30, 255))
        pr = ir * (0.35 + 0.1 * math.sin(t * 5)); d.ellipse((cx - pr, cy - pr, cx + pr, cy + pr), fill=(20, 0, 0, 255))
        d.ellipse((cx - ir * 0.5, cy - ir * 0.6, cx - ir * 0.2, cy - ir * 0.3), fill=(255, 200, 190, 220))
    else:
        d.line([(cx - ew, cy), (cx + ew, cy)], fill=(255, 80, 60, 255), width=4)
    # glitch bars
    r = random.Random(int(t * 12))
    if r.random() < 0.35:
        for _ in range(4):
            y = r.uniform(300, 1300); h = r.uniform(6, 30); sl = im.crop((0, int(y), W, int(y + h))); im.paste(sl, (int(r.uniform(-60, 60)), int(y)))
    tx = gold_text("KAAL-AI  ONLINE", F("anton", 110), (255, 230, 230), (255, 40, 40), 7, (255, 0, 0))
    paste(im, tx, W / 2, 260, ease_back((t - 1.8) / 0.4) * (1 + 0.02 * math.sin(t * 20)))
    header(im)
    bi_caption(im, "एक दुष्ट सुपर-इंटेलिजेंस की चेतना जागी — उसका नाम था काल-AI।", "An evil super-intelligence awakened. Its name: KAAL-AI.", t, start=1.0)
    return im

MANU = parchment(920, 860, seed=11)
_md = ImageDraw.Draw(MANU)
for j, l in enumerate(["॥ हिमालयस्य गर्भे ॥", "अमृतं चक्रं निहितम्", "अनन्त ऊर्जा स्रोतः", "॥ रहस्यम् ॥"]):
    _md.text((460, 180 + j * 150), l, font=P(62), fill=(90, 40, 10, 255), anchor="mm")
@scene(7.0)
def s_decode(t, i):
    im = vgrad((20, 4, 8), (4, 0, 2)); paste(im, MANU, W / 2, 760, 1.0, 1.0, rot=-2)
    d = ImageDraw.Draw(im); sy = 360 + ((t * 300) % 820)
    band = Image.new("RGBA", (W, 50)); bd = ImageDraw.Draw(band)
    for k in range(50): bd.line([(0, k), (W, k)], fill=(255, 30, 30, int(150 * (1 - abs(k - 25) / 25))))
    im.alpha_composite(band, (0, int(sy) - 25))
    # binary stream floating up from manuscript
    r = random.Random(4); bf = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 34)
    for k in range(70):
        x = r.uniform(80, W - 80); sp = r.uniform(80, 220); y0 = r.uniform(300, 1200)
        y = (y0 - t * sp) % 1300; a = int(200 * clamp(t / 1.0))
        d.text((x, y), r.choice(["0", "1", "01", "10", "101"]), font=bf, fill=(255, 70, 70, a))
    # progress bar
    pr = clamp(t / 6.0); d.rounded_rectangle((140, 1250, 940, 1300), 25, outline=(255, 90, 90, 255), width=4)
    d.rounded_rectangle((146, 1256, 146 + 788 * pr, 1294), 20, fill=(255, 50, 50, 255))
    d.text((W / 2, 1220), f"DECODING ANCIENT TEXTS... {int(pr * 100)}%", font=bf, fill=(255, 140, 140), anchor="mm")
    header(im)
    bi_caption(im, "उसने हज़ारों प्राचीन भारतीय ग्रंथों को डिकोड करना शुरू किया...", "It began decoding thousands of ancient Indian texts...", t, start=0.5, y=1400)
    return im

def himalaya():
    im = vgrad((8, 12, 40), (40, 50, 90)); d = ImageDraw.Draw(im); r = random.Random(8)
    for _ in range(180):
        x, y, s = r.uniform(0, W), r.uniform(0, 900), r.uniform(1, 3); d.ellipse((x - s, y - s, x + s, y + s), fill=(255, 255, 255, r.randint(100, 255)))
    for layer, (col, base, hgt) in enumerate([((70, 80, 120, 255), 1050, 600), ((45, 52, 90, 255), 1250, 650), ((25, 30, 60, 255), 1450, 520)]):
        pts = [(0, H)]; x = -100; rr = random.Random(layer)
        while x < W + 200:
            pts.append((x, base - rr.uniform(0.3, 1) * hgt)); x += rr.uniform(140, 260); pts.append((x, base - rr.uniform(0, 0.25) * hgt)); x += rr.uniform(80, 160)
        pts.append((W, H)); d.polygon(pts, fill=col)
        for k in range(1, len(pts) - 1, 2):  # snow caps
            px, py = pts[k]
            if py < base - 0.3 * hgt: d.polygon([(px, py), (px - 45, py + 70), (px - 10, py + 55), (px + 15, py + 80), (px + 50, py + 65)], fill=(235, 240, 255, 255))
    return im
HIM = himalaya()
@scene(8.0)
def s_himalaya(t, i):
    im = HIM.copy(); cx, cy = W / 2, 1180
    pulse = 0.85 + 0.15 * math.sin(t * 4)
    paste(im, chakra(700, t), cx, cy, 0.5 * ease_back((t - 1.5) / 0.7) * pulse, 0.95)
    d = ImageDraw.Draw(im); ra = ease((t - 0.3) / 1.2)
    # red targeting reticle closing in
    rr = 520 - 330 * ra
    for k in range(4):
        a = k * 90 + 45 + t * 30
        d.arc((cx - rr, cy - rr, cx + rr, cy + rr), a - 20, a + 20, fill=(255, 40, 40, 230), width=8)
    d.line([(cx - rr - 40, cy), (cx - rr + 40, cy)], fill=(255, 40, 40, 200), width=4); d.line([(cx + rr - 40, cy), (cx + rr + 40, cy)], fill=(255, 40, 40, 200), width=4)
    if t > 2.4:
        lb = Image.new("RGBA", (620, 100)); ld = ImageDraw.Draw(lb); ld.rounded_rectangle((0, 0, 619, 99), 24, fill=(60, 0, 0, 220), outline=(255, 60, 60, 255), width=4)
        ld.text((310, 50), "TARGET: AMRIT-CHAKRA", font=P(44), fill=(255, 200, 200), anchor="mm"); paste(im, lb, cx, 880, ease_back((t - 2.4) / 0.4))
    out = kenburns(im, t / 8, 1.0, 1.15, 0, 120); header(out)
    bi_caption(out, "और उसे मिल गया — हिमालय की गहराइयों में छिपा 'अमृत-चक्र', असीम ऊर्जा का स्रोत!", "And it found it: the Amrit-Chakra, infinite energy hidden deep in the Himalayas!", t, start=0.6, y=240)
    return out

Q1 = gold_text("क्या काल-AI इसे\nपा लेगा?", P(110), (255, 240, 240), (255, 70, 60), 8, (255, 30, 30))
@scene(6.0)
def s_end(t, i):
    im = COSMIC.copy(); paste(im, glow(1200, (255, 30, 40), 2), W / 2, 700, 1.0, 0.5)
    paste(im, chakra(800, t), W / 2, 760, 0.7, 0.35)
    paste(im, Q1, W / 2, 560, ease_back(t / 0.5))
    d = ImageDraw.Draw(im); a = clamp((t - 0.7) / 0.4)
    d.text((W / 2, 820), "Will KAAL-AI get it first?", font=P(52, False), fill=(255, 220, 150, int(255 * a)), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    a2 = ease_back((t - 1.4) / 0.5)
    if a2 > 0:
        nb = Image.new("RGBA", (940, 230)); nd = ImageDraw.Draw(nb); nd.rounded_rectangle((0, 0, 939, 229), 40, fill=(15, 10, 40, 230), outline=(255, 200, 90, 255), width=5)
        nd.text((470, 70), "अगला भाग: काशी का रहस्यमयी नक्शा", font=P(48), fill=(255, 255, 255), anchor="mm")
        nd.text((470, 150), "Next: Part 2 · The Mystery Map of Kashi", font=P(38, False), fill=(255, 210, 130), anchor="mm")
        paste(im, nb, W / 2, 1150, a2)
    a3 = ease_back((t - 2.2) / 0.5)
    if a3 > 0:
        b = Image.new("RGBA", (860, 140)); bd = ImageDraw.Draw(b); bd.rounded_rectangle((0, 0, 859, 139), 70, fill=(230, 30, 70, 255), outline=(255, 255, 255, 255), width=6)
        bd.text((430, 70), "Follow करें — Part 2 के लिए!", font=P(52), fill=(255, 255, 255), anchor="mm")
        paste(im, b, W / 2, 1450, a3 * (1 + 0.04 * math.sin(t * 7)))
    d.text((W / 2, 1800), "@hemender187Official", font=P(44), fill=(255, 255, 255, 230), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    Sparks(40, (0, 0, W, H), (255, 120, 100), seed=6).draw(im, t)
    if t > 5.3: im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * clamp((t - 5.3) / 0.7)))))
    return im

# ---------- music: dark epic ----------
SR = 48000
def make_audio(path, cuts, dur):
    n = int(SR * dur); tt = np.arange(n) / SR; mix = np.zeros(n); nf = lambda m: 440 * 2 ** ((m - 69) / 12)
    def env(st, d, a=0.02, rel=0.5):
        e = np.zeros(n); s0 = int(st * SR); s1 = min(n, int((st + d + rel) * SR))
        if s0 >= n: return e
        x = (np.arange(s0, s1) - s0) / SR; e[s0:s1] = np.minimum(1, x / a) * np.where(x < d, 1, np.exp(-(x - d) * 4)); return e
    prog = [[50, 53, 57], [46, 50, 53], [48, 52, 55], [45, 49, 52]]  # Dm Bb C A
    bar = 2.4; k = 0
    mix += 0.06 * np.sin(2 * np.pi * nf(38) * tt) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.25 * tt))  # drone
    while k * bar < dur:
        st = k * bar; ch = prog[k % 4]
        for m in ch:
            f = nf(m); mix += 0.04 * env(st, bar, 0.6, 0.8) * (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * f * 1.003 * tt) + 0.2 * np.sin(2 * np.pi * 2 * f * tt))
        for b, v in ((0, 1.0), (0.6, 0.5), (1.2, 0.8), (1.5, 0.5), (1.8, 0.9)):  # taiko pattern
            s = st + b
            if s >= dur or st < cuts[1] - 0.5: continue
            s0 = int(s * SR); L = min(n - s0, SR // 2); x = tt[s0:s0 + L] - s
            mix[s0:s0 + L] += 0.3 * v * np.exp(-x * 12) * np.sin(2 * np.pi * (45 + 70 * np.exp(-x * 25)) * x)
        for j in range(6):  # sitar-ish pluck motif
            s = st + j * bar / 6
            if s >= dur: break
            m = [62, 65, 64, 62, 60, 57][(j + k) % 6]; s0 = int(s * SR); x = tt[s0:] - s; f = nf(m)
            mix[s0:] += 0.035 * np.exp(-x * 4) * (np.sin(2 * np.pi * f * x) + 0.5 * np.sin(2 * np.pi * 2.01 * f * x) + 0.3 * np.sin(2 * np.pi * 3.02 * f * x))
        k += 1
    rn = np.random.default_rng(2)
    for c in cuts[1:]: mix += 0.06 * rn.standard_normal(n) * np.exp(-((tt - c) ** 2) / 0.012)
    e0 = cuts[2] + 1.8; s0 = int(e0 * SR); x = tt[s0:] - e0  # KAAL-AI online hit
    mix[s0:] += 0.25 * np.exp(-x * 2) * np.sin(2 * np.pi * 55 * x) + 0.08 * np.exp(-x * 3) * np.sign(np.sin(2 * np.pi * 110 * x))
    fade = np.clip(np.minimum(tt / 0.05, (dur - tt) / 1.2), 0, 1); mix *= fade
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.85
    st = np.stack([mix, np.roll(mix, 300)], 1)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((st * 32767).astype(np.int16).tobytes())

def render_scene(idx, dur, fn):
    final = os.path.join(TMP, f"s{idx}.mp4"); part = os.path.join(TMP, f"s{idx}.part.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0", part], stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        t = i / FPS; im = fn(t, i)
        if idx > 0 and t < 0.25: im = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), im, t / 0.25)
        p.stdin.write(im.convert("RGB").tobytes())
    p.stdin.close(); assert p.wait() == 0; os.replace(part, final); return final

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2] == "preview":
        ims = [fn(d * 0.8, 0).convert("RGB").resize((360, 640)) for d, fn in scenes]
        sh = Image.new("RGB", (360 * 3, 640 * 2))
        for k, im in enumerate(ims): sh.paste(im, ((k % 3) * 360, (k // 3) * 640))
        sh.save(os.path.join(TMP, "sheet.jpg")); sys.exit()
    files = [render_scene(k, d, fn) for k, (d, fn) in enumerate(scenes)]
    cuts = np.cumsum([0] + [d for d, _ in scenes])[:-1].tolist(); dur = sum(d for d, _ in scenes)
    lst = os.path.join(TMP, "list.txt"); open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    wav = os.path.join(TMP, "a.wav"); make_audio(wav, cuts, dur)
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav, "-map", "0:v", "-map", "1:a",
                           "-c:v", "copy", "-c:a", "aac", "-ar", "48000", "-b:a", "160k", "-movflags", "+faststart", "-shortest", OUT])
    print("wrote", OUT, dur)
