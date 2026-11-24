#!/usr/bin/env python3
"""अमृत-चक्र — Part 2 (Chapters 4-6): गणेश गुफा. Drawn scenes, Hindi + English captions."""
import math, os, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else "part02.mp4"
_argv = sys.argv[:]; sys.argv = [sys.argv[0], OUT]
import part01 as p1
sys.argv = _argv
from vlib import *
P, bi_caption, chakra, gold_text_ = p1.P, p1.bi_caption, p1.chakra, gold_text
p1.PART = 2
TMP = os.path.join(os.path.dirname(os.path.abspath(OUT)), ".tmp02"); os.makedirs(TMP, exist_ok=True)

def header(base):
    ImageDraw.Draw(base).text((W / 2, 70), "अमृत-चक्र · भाग 2", font=P(38), fill=(255, 215, 120, 235), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))

# ---------- characters ----------
def person(d, x, y, s, kind, t, walk=True, bow=0.0, col=(8, 8, 14, 255)):
    st = math.sin(t * 6) if walk else 0
    hy = y - 300 * s + bow * 60 * s; hx = x + bow * 40 * s
    if kind == "meera":
        d.polygon([(hx - 42 * s, hy + 45 * s), (hx + 42 * s, hy + 45 * s), (x + 75 * s, y - 70 * s), (x - 75 * s, y - 70 * s)], fill=col)  # kurta
        d.line([(hx - 20 * s, hy - 10 * s), (hx - 38 * s, hy + 110 * s)], fill=col, width=int(14 * s))  # braid
        d.ellipse((hx - 34 * s, hy - 34 * s, hx + 34 * s, hy + 34 * s), fill=col)
    else:  # aryan
        hy -= 25 * s
        d.polygon([(hx - 55 * s, hy + 45 * s), (hx + 55 * s, hy + 45 * s), (x + 50 * s, y - 120 * s), (x - 50 * s, y - 120 * s)], fill=col)
        d.ellipse((hx - 36 * s, hy - 36 * s, hx + 36 * s, hy + 36 * s), fill=col)
        d.polygon([(hx - 38 * s, hy - 10 * s), (hx - 30 * s, hy - 45 * s), (hx + 30 * s, hy - 48 * s), (hx + 40 * s, hy - 15 * s)], fill=col)  # hair
    d.line([(x - 22 * s, y - 100 * s), (x - 22 * s + 30 * s * st, y)], fill=col, width=int(24 * s))
    d.line([(x + 22 * s, y - 100 * s), (x + 22 * s - 30 * s * st, y)], fill=col, width=int(24 * s))

def robot(t, s=1.0):
    S = int(320 * s); im = Image.new("RGBA", (S, S)); c = S / 2; d = ImageDraw.Draw(im)
    paste(im, glow(S, (90, 200, 255), 2.2), c, c, 1.0, 0.6)
    r = S * 0.28
    d.ellipse((c - r, c - r * 0.95, c + r, c + r * 0.95), fill=(235, 240, 245, 255), outline=(150, 160, 175, 255), width=max(2, int(4 * s)))
    vr = r * 0.72; d.rounded_rectangle((c - vr, c - vr * 0.55, c + vr, c + vr * 0.45), int(vr * 0.4), fill=(20, 26, 40, 255))
    blink = 0.15 if (t % 3.1) < 0.12 else 1.0
    for ex in (-vr * 0.42, vr * 0.42):
        er = vr * 0.24; d.ellipse((c + ex - er, c - 0.05 * vr - er * blink, c + ex + er, c - 0.05 * vr + er * blink), fill=(110, 220, 255, 255))
    d.ellipse((c - r * 0.25, c + r * 0.95, c + r * 0.25, c + r * 1.15), fill=(110, 200, 255, 200))  # thruster
    return im

def mountains(seed, col, base, hgt, w=W + 300):
    im = Image.new("RGBA", (w, H)); d = ImageDraw.Draw(im); r = random.Random(seed); pts = [(0, H)]; x = -50
    while x < w + 100:
        pts.append((x, base - r.uniform(0.5, 1) * hgt)); x += r.uniform(180, 320); pts.append((x, base - r.uniform(0.1, 0.4) * hgt)); x += r.uniform(100, 200)
    pts.append((w, H)); d.polygon(pts, fill=col); return im

def mist(seed, y, a=90):
    im = Image.new("RGBA", (W + 600, 400)); d = ImageDraw.Draw(im); r = random.Random(seed)
    for _ in range(14):
        x = r.uniform(0, W + 600); rr = r.uniform(150, 300); d.ellipse((x - rr, 200 - rr * 0.4, x + rr, 200 + rr * 0.4), fill=(255, 235, 220, a))
    return im.filter(ImageFilter.GaussianBlur(40)), y

scenes = []
def scene(dur):
    def reg(fn): scenes.append((dur, fn)); return fn
    return reg

TITLE = gold_text("गणेश गुफा", P(150)); TITLE_EN = gold_text("THE GANESH CAVE", F("anton", 90), (255, 255, 255), (220, 210, 255), 6, (150, 100, 255))
@scene(4.5)
def s_title(t, i):
    im = p1.COSMIC.copy(); paste(im, p1.RAYS, W / 2, 900, 1.0, 0.6, rot=t * 10)
    paste(im, chakra(1000, t), W / 2, 900, 0.4 + 0.6 * ease_back(t / 0.9))
    paste(im, gold_text("अमृत-चक्र", P(110)), W / 2, 175, ease_back((t - 0.2) / 0.5))
    paste(im, TITLE, W / 2, 410, ease_back((t - 0.6) / 0.5)); paste(im, TITLE_EN, W / 2, 565, 1.0, clamp((t - 1.0) / 0.4))
    b, a = p1.part_badge(t, 1.4); bd = ImageDraw.Draw(b); bd.rounded_rectangle((4, 4, 515, 91), 44, fill=(200, 25, 50, 255)); bd.text((260, 50), "भाग 2 · Part 2", font=P(42), fill=(255, 255, 255), anchor="mm")
    paste(im, b, W / 2, 1520, a)
    d = ImageDraw.Draw(im); aa = clamp((t - 2.0) / 0.4)
    d.text((W / 2, 1660), "अध्याय 4 · 5 · 6", font=P(56), fill=(255, 255, 255, int(255 * aa)), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, int(255 * aa)))
    d.text((W / 2, 1740), "Chapters 4 · 5 · 6", font=P(38, False), fill=(255, 210, 130, int(255 * aa)), anchor="mm")
    Sparks(45, (0, 0, W, H), seed=2).draw(im, t)
    return im

SKY = vgrad((255, 150, 90), (120, 170, 200)); _d = ImageDraw.Draw(SKY)
paste(SKY, glow(900, (255, 230, 150), 1.8), 700, 820, 1.0, 1.0); _d.ellipse((620, 740, 780, 900), fill=(255, 245, 210, 255))
M1 = mountains(1, (110, 120, 140, 255), 1000, 450); M2 = mountains(2, (60, 95, 80, 255), 1250, 500); M3 = mountains(3, (25, 50, 35, 255), 1550, 380)
MI1 = mist(4, 820); MI2 = mist(5, 1120, 110)
@scene(7.0)
def s_sahyadri(t, i):
    im = SKY.copy()
    im.alpha_composite(M1.crop((int(10 * t), 0, int(10 * t) + W, H)))
    im.alpha_composite(MI1[0].crop((int(40 * t), 0, int(40 * t) + W, 400)), (0, MI1[1]))
    im.alpha_composite(M2.crop((int(25 * t), 0, int(25 * t) + W, H)))
    im.alpha_composite(MI2[0].crop((int(70 * t), 0, int(70 * t) + W, 400)), (0, MI2[1]))
    im.alpha_composite(M3.crop((int(45 * t), 0, int(45 * t) + W, H)))
    d = ImageDraw.Draw(im); gx = 260 + 40 * t
    person(d, gx, 1600, 0.75, "aryan", t); person(d, gx + 150, 1610, 0.7, "meera", t + 0.4)
    paste(im, robot(t, 0.6), gx + 330, 1330 + 15 * math.sin(t * 2.5))
    header(im)
    bi_caption(im, "नक्शे का पहला संकेत उन्हें सह्याद्री पर्वतों की एक गुप्त गुफा तक ले आया।", "The first clue led them to a secret cave in the Sahyadri mountains.", t, start=0.5, y=200)
    return im

def door_layer(open_f=0.0):
    im = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, H), fill=(70, 62, 55, 255))
    r = random.Random(9)
    for _ in range(120):  # rock texture
        x, y, s = r.uniform(0, W), r.uniform(0, H), r.uniform(20, 90); c = r.randint(45, 85); d.ellipse((x - s, y - s * 0.6, x + s, y + s * 0.6), fill=(c, c - 6, c - 12, 255))
    # arch
    d.rounded_rectangle((150, 380, 930, 1620), 380, fill=(40, 34, 30, 255), outline=(150, 130, 100, 255), width=14)
    half = 370 * open_f
    if open_f > 0:
        paste(im, glow(1200, (255, 210, 120), 1.4), W / 2, 1050, 1.0, open_f)
    for side in (-1, 1):  # two door halves
        x0 = W / 2 + side * half
        box = (x0 - 370, 400, x0, 1600) if side < 0 else (x0, 400, x0 + 370, 1600)
        d.rectangle(box, fill=(105, 92, 78, 255), outline=(60, 50, 40, 255), width=8)
        for k in range(5):
            yy = 520 + k * 210; d.line([(box[0] + 40, yy), (box[2] - 40, yy)], fill=(80, 68, 56, 255), width=6)
            d.ellipse(((box[0] + box[2]) / 2 - 30, yy + 70, (box[0] + box[2]) / 2 + 30, yy + 130), outline=(80, 68, 56, 255), width=6)
    if open_f < 0.05:  # modak emblem on the seam
        cx, cy = W / 2, 760; d.polygon([(cx, cy - 90), (cx - 75, cy + 40), (cx + 75, cy + 40)], fill=(190, 160, 90, 255))
        d.ellipse((cx - 85, cy - 10, cx + 85, cy + 80), fill=(190, 160, 90, 255))
        for k in range(-2, 3): d.line([(cx, cy - 85), (cx + k * 38, cy + 60)], fill=(140, 110, 60, 255), width=5)
    return im
DOOR = door_layer()
@scene(7.0)
def s_door(t, i):
    im = DOOR.copy(); d = ImageDraw.Draw(im)
    if 1.2 < t < 4.6:  # laser attempt
        ox, oy = 180, 1700; tx, ty = W / 2 + 20 * math.sin(t * 9), 1000 + 30 * math.sin(t * 7)
        for wdt, a in ((26, 70), (12, 160), (5, 255)): d.line([(ox, oy), (tx, ty)], fill=(90, 200, 255, a), width=wdt)
        paste(im, glow(260, (150, 230, 255), 1.5), tx, ty, 1.0, 0.9)
        r = random.Random(int(t * 30))
        for _ in range(14):
            a = r.uniform(0, 6.28); L = r.uniform(20, 90); d.line([(tx, ty), (tx + L * math.cos(a), ty + L * math.sin(a))], fill=(255, 230, 150, 255), width=4)
    if t > 4.6:
        lb = Image.new("RGBA", (640, 110)); ld = ImageDraw.Draw(lb); ld.rounded_rectangle((0, 0, 639, 109), 26, fill=(70, 0, 0, 230), outline=(255, 70, 70, 255), width=4)
        ld.text((320, 55), "द्वार नहीं खुला!", font=P(52), fill=(255, 220, 220), anchor="mm"); paste(im, lb, W / 2, 1000, ease_back((t - 4.6) / 0.4))
    person(d, 150, 1900, 0.95, "aryan", t, walk=False); person(d, 900, 1920, 0.85, "meera", t, walk=False)
    out = kenburns(im, t / 7, 1.05, 1.0); header(out)
    bi_caption(out, "विशाल पत्थर का द्वार — न लेज़र से खुला, न विस्फोटक से!", "A giant stone door: no laser, no explosive could open it!", t, start=0.4, y=170)
    return out

WALL = Image.new("RGBA", (W, H), (28, 22, 18, 255)); _wd = ImageDraw.Draw(WALL); _r = random.Random(12)
for _ in range(160):
    x, y, s = _r.uniform(0, W), _r.uniform(0, H), _r.uniform(20, 80); c = _r.randint(30, 55); _wd.ellipse((x - s, y - s * 0.6, x + s, y + s * 0.6), fill=(c, c - 5, c - 10, 255))
RIDDLE = ["वक्रतुण्ड महाकाय", "बुद्धिः विनयेन शोभते", "अहंकारं त्यज", "द्वारं तदा उद्घाटितम्"]
@scene(7.0)
def s_scan(t, i):
    im = WALL.copy(); d = ImageDraw.Draw(im)
    sy = 420 + (t * 260) % 900
    for j, l in enumerate(RIDDLE):
        y = 520 + j * 210; lit = clamp((sy - y + 60) / 120) if t < 6 else 1
        col = (int(120 + 135 * lit), int(95 + 120 * lit), int(60 + 20 * lit), 255)
        if lit > 0.3: paste(im, glow(700, (255, 190, 80), 3), W / 2, y, 1.0, 0.35 * lit)
        d.text((W / 2, y), l, font=P(70), fill=col, anchor="mm")
    rx, ry = 860 + 20 * math.sin(t * 1.5), 1420 + 20 * math.sin(t * 2.2)
    beam = Image.new("RGBA", (W, H)); bd = ImageDraw.Draw(beam)
    bd.polygon([(rx - 30, ry - 10), (80, sy - 50), (1000, sy + 50)], fill=(90, 210, 255, 55)); bd.line([(80, sy), (1000, sy)], fill=(140, 230, 255, 220), width=5)
    im.alpha_composite(beam); paste(im, robot(t, 0.9), rx, ry)
    header(im)
    bi_caption(im, "वायु-09 ने गुफा की दीवारों पर उकेरी संस्कृत पहेलियाँ स्कैन कीं...", "VAYU-09 scanned the Sanskrit riddles carved on the cave walls...", t, start=0.4, y=1560)
    return im

QUOTE = gold_text("“बुद्धि और विनम्रता ही\nहर बाधा की कुंजी है”", P(76), (255, 252, 230), (255, 175, 40), 7, (255, 200, 90))
SHRI = gold_text("श्री गणेश", P(120), (255, 255, 240), (255, 160, 30), 8, (255, 220, 120))
GOLDRAYS = rays(2000, 24, (255, 200, 90))
@scene(7.0)
def s_ganesh(t, i):
    im = vgrad((70, 25, 5), (15, 5, 0)); paste(im, GOLDRAYS, W / 2, 820, 1.0, clamp(t / 1.2), rot=t * 8)
    paste(im, glow(1300, (255, 200, 90), 1.4), W / 2, 820, 1.0, clamp(t / 1.0))
    pulse = 1 + 0.04 * math.sin(t * 3)
    paste(im, chakra(900, t * 0.5, (255, 180, 60)), W / 2, 820, 0.9 * ease((t - 0.2) / 1.0) * pulse, 0.7)
    paste(im, emoji("🪔", 150), W / 2 - 260, 1180, ease_back((t - 1.2) / 0.5)); paste(im, emoji("🪷", 150), W / 2 + 260, 1180, ease_back((t - 1.4) / 0.5))
    paste(im, SHRI, W / 2, 820, ease_back((t - 0.6) / 0.6) * pulse)
    paste(im, QUOTE, W / 2, 360, ease_back((t - 2.2) / 0.6))
    Sparks(70, (0, 200, W, 1700), (255, 230, 150), seed=8).draw(im, t, rise=60)
    header(im)
    bi_caption(im, "गुफा दिव्य प्रकाश से भर गई — विघ्नहर्ता का संदेश गूँजा।", "Divine light filled the cave: a message from Vighnaharta, the remover of obstacles.", t, start=1.0, y=1420)
    return im

@scene(7.0)
def s_open(t, i):
    of = ease((t - 2.6) / 2.2)
    im = door_layer(of); d = ImageDraw.Draw(im)
    bow = ease((t - 0.3) / 1.0) * (1 - ease((t - 2.4) / 0.6))
    person(d, 430, 1900, 0.95, "aryan", t, walk=False, bow=bow); person(d, 700, 1920, 0.85, "meera", t, walk=False)
    if bow > 0.3:
        m = gold_text("ॐ गं गणपतये नमः", P(70), (255, 255, 240), (255, 180, 50), 6); paste(im, m, W / 2, 1300, 1.0, clamp(bow))
    paste(im, robot(t, 0.55), 870, 1480 + 15 * math.sin(t * 2))
    if of > 0.2: Sparks(50, (200, 400, 880, 1600), seed=4).draw(im, t, rise=50)
    header(im)
    bi_caption(im, "आर्यन ने अहंकार त्यागा, सही मंत्र बोला — और द्वार खुल गया!", "Aryan let go of his ego, spoke the right mantra, and the door opened!", t, start=0.4, y=150)
    return im

def gem(t, s=1.0):
    S = int(500 * s); im = Image.new("RGBA", (S, S)); c = S / 2; d = ImageDraw.Draw(im)
    paste(im, glow(S, (255, 210, 90), 1.6), c, c, 1.0, 0.9)
    r = S * 0.22; sq = abs(math.cos(t * 1.5))
    pts = [(c, c - r * 1.4), (c + r * sq, c - r * 0.3), (c + r * 0.7 * sq, c + r * 1.1), (c, c + r * 1.4), (c - r * 0.7 * sq, c + r * 1.1), (c - r * sq, c - r * 0.3)]
    d.polygon(pts, fill=(255, 210, 70, 255), outline=(255, 250, 200, 255)); d.line([(c, c - r * 1.4), (c, c + r * 1.4)], fill=(255, 250, 210, 200), width=4)
    d.polygon([(c, c - r * 1.4), (c + r * sq * 0.5, c - r * 0.3), (c, c + r * 0.2), (c - r * sq * 0.5, c - r * 0.3)], fill=(255, 245, 190, 200))
    return im

def soldier(d, x, y, s, t, ph):
    col = (20, 20, 28, 255)
    d.rounded_rectangle((x - 50 * s, y - 360 * s, x + 50 * s, y - 250 * s), int(30 * s), fill=col)
    d.polygon([(x - 80 * s, y - 250 * s), (x + 80 * s, y - 250 * s), (x + 60 * s, y - 110 * s), (x - 60 * s, y - 110 * s)], fill=col)
    d.rectangle((x - 50 * s, y - 115 * s, x - 15 * s, y), fill=col); d.rectangle((x + 15 * s, y - 115 * s, x + 50 * s, y), fill=col)
    on = 0.7 + 0.3 * math.sin(t * 6 + ph)
    d.rectangle((x - 38 * s, y - 320 * s, x + 38 * s, y - 300 * s), fill=(255, 30, 30, int(255 * on)))

@scene(7.0)
def s_gem(t, i):
    im = vgrad((40, 20, 10), (10, 5, 2)); d = ImageDraw.Draw(im)
    d.ellipse((-200, 300, W + 200, 2300), fill=(25, 14, 8, 255))
    paste(im, gem(t), W / 2, 760 + 20 * math.sin(t * 2), ease_back(t / 0.7))
    if t < 3.0:
        lb = gold_text("बुद्धि-मणि", P(90)); paste(im, lb, W / 2, 1080, ease_back((t - 0.6) / 0.5))
    sa = ease((t - 3.0) / 0.8)
    if sa > 0:
        im.alpha_composite(Image.new("RGBA", (W, H), (120, 0, 0, int(70 * sa * (0.7 + 0.3 * math.sin(t * 10))))))
        d = ImageDraw.Draw(im)
        for k, (x, s) in enumerate([(90, 1.0), (300, 0.85), (520, 0.75), (760, 0.85), (980, 1.0)]):
            soldier(d, x, 1500 + (1 - sa) * 400 + (1 - s) * -150, s * 1.1, t, k)
        lb = Image.new("RGBA", (680, 100)); ld = ImageDraw.Draw(lb); ld.rounded_rectangle((0, 0, 679, 99), 24, fill=(70, 0, 0, 230), outline=(255, 70, 70, 255), width=4)
        ld.text((340, 50), "KAAL-AI CYBER-WARRIORS", font=P(42), fill=(255, 220, 220), anchor="mm"); paste(im, lb, W / 2, 1100, ease_back((t - 3.3) / 0.4))
    header(im)
    bi_caption(im, "पहला रत्न मिला — बुद्धि-मणि! पर तभी काल-AI के साइबर-योद्धाओं ने गुफा घेर ली।", "The first gem, the Buddhi-Mani! But KAAL-AI's cyber-warriors surrounded the cave.", t, start=0.4, y=150)
    return im

def holo_layer(x, y, s, kind, t, a):
    lay = Image.new("RGBA", (W, H)); person(ImageDraw.Draw(lay), x, y, s, kind, t, walk=False, col=(90, 200, 255, int(150 * a)))
    return lay
@scene(7.0)
def s_holo(t, i):
    im = vgrad((10, 15, 30), (3, 3, 8)); d = ImageDraw.Draw(im)
    ha = ease((t - 0.5) / 0.6)
    for k, (x, kind) in enumerate([(180, "aryan"), (380, "meera"), (700, "aryan"), (900, "meera"), (540, "meera")]):
        fl = 0.6 + 0.4 * abs(math.sin(t * 7 + k))
        im.alpha_composite(holo_layer(x, 1350 + (k % 2) * 40, 0.8, kind, t, ha * fl))
    for k, (x, s) in enumerate([(60, 1.1), (1020, 1.1)]): soldier(d, x, 1950, s, t, k)
    r = random.Random(int(t * 6))
    for k in range(3):  # lasers hitting holograms (pass through)
        if r.random() < 0.6 and t > 1.0:
            sx = 60 if k % 2 == 0 else 1020; tx = r.choice([180, 380, 700, 900, 540]); ty = r.uniform(1100, 1300)
            d.line([(sx, 1610), (tx, ty)], fill=(255, 40, 40, 220), width=6)
    paste(im, robot(t, 0.8), W / 2, 700 + 20 * math.sin(t * 3))
    for k in range(5):  # projection cones
        tx = [180, 380, 700, 900, 540][k]
        cone = Image.new("RGBA", (W, H)); ImageDraw.Draw(cone).polygon([(W / 2, 740), (tx - 70, 1050), (tx + 70, 1050)], fill=(90, 200, 255, int(35 * ha)))
        im.alpha_composite(cone)
    # the real three escaping (small, far right, running out)
    ex = 700 + 180 * ease((t - 3.5) / 3.0)
    if t > 3.5:
        dd = ImageDraw.Draw(im); person(dd, ex + 200, 1720, 0.35, "aryan", t * 2); person(dd, ex + 270, 1725, 0.32, "meera", t * 2 + 0.3)
    header(im)
    bi_caption(im, "वायु-09 के होलोग्राम ने दुश्मनों को भ्रमित किया — और तीनों बच निकले!", "VAYU-09's holograms fooled the enemy, and the three escaped!", t, start=0.4, y=170)
    return im

@scene(5.5)
def s_end(t, i):
    im = p1.COSMIC.copy(); paste(im, glow(1200, (255, 200, 80), 2), W / 2, 700, 1.0, 0.5)
    paste(im, gem(t, 1.2), W / 2, 560, ease_back(t / 0.5))
    d = ImageDraw.Draw(im); a = clamp((t - 0.5) / 0.4)
    d.text((W / 2, 870), "1 मणि मिली… 2 बाकी!", font=P(70), fill=(255, 255, 255, int(255 * a)), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    d.text((W / 2, 950), "1 gem found… 2 to go!", font=P(44, False), fill=(255, 220, 150, int(255 * a)), anchor="mm")
    a2 = ease_back((t - 1.0) / 0.5)
    if a2 > 0:
        nb = Image.new("RGBA", (960, 230)); nd = ImageDraw.Draw(nb); nd.rounded_rectangle((0, 0, 959, 229), 40, fill=(15, 10, 40, 235), outline=(255, 200, 90, 255), width=5)
        nd.text((480, 72), "अगला भाग: ज्ञान की नदी", font=P(52), fill=(255, 255, 255), anchor="mm"); nd.text((480, 152), "Next: Part 3 · The River of Knowledge", font=P(38, False), fill=(255, 210, 130), anchor="mm")
        paste(im, nb, W / 2, 1200, a2)
    a3 = ease_back((t - 1.7) / 0.5)
    if a3 > 0:
        b = Image.new("RGBA", (860, 140)); bd = ImageDraw.Draw(b); bd.rounded_rectangle((0, 0, 859, 139), 70, fill=(230, 30, 70, 255), outline=(255, 255, 255, 255), width=6)
        bd.text((430, 70), "Follow करें — Part 3 के लिए!", font=P(52), fill=(255, 255, 255), anchor="mm"); paste(im, b, W / 2, 1480, a3 * (1 + 0.04 * math.sin(t * 7)))
    d.text((W / 2, 1800), "@hemender187Official", font=P(44), fill=(255, 255, 255, 230), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    Sparks(40, (0, 0, W, H), seed=6).draw(im, t)
    if t > 4.8: im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * clamp((t - 4.8) / 0.7)))))
    return im

if __name__ == "__main__":
    p1.TMP = TMP
    if len(sys.argv) > 2 and sys.argv[2] == "preview":
        ims = [fn(d * 0.75, 0).convert("RGB").resize((270, 480)) for d, fn in scenes]
        sh = Image.new("RGB", (270 * 5, 480 * 2))
        for k, im in enumerate(ims): sh.paste(im, ((k % 5) * 270, (k // 5) * 480))
        sh.save(os.path.join(TMP, "sheet.jpg")); sys.exit()
    files = [p1.render_scene(k, d, fn) for k, (d, fn) in enumerate(scenes)]
    cuts = np.cumsum([0] + [d for d, _ in scenes])[:-1].tolist(); dur = sum(d for d, _ in scenes)
    lst = os.path.join(TMP, "list.txt"); open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    wav = os.path.join(TMP, "a.wav"); p1.make_audio(wav, cuts, dur)
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", wav, "-map", "0:v", "-map", "1:a",
                           "-c:v", "copy", "-c:a", "aac", "-ar", "48000", "-b:a", "160k", "-movflags", "+faststart", "-shortest", OUT])
    print("wrote", OUT, dur)
