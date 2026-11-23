#!/usr/bin/env python3
"""Make an eye-catching 15s vertical "good luck" video.

Usage: python3 make.py 'line one\nline two' out.mp4 [theme]
Themes: gold, emerald, sunrise, royal, pink (picked from the message if omitted).
"""
import sys, math, random, subprocess, os, tempfile, wave, zlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 1080, 1920, 30, 15
N = FPS * DUR
msg = (sys.argv[1] if len(sys.argv) > 1 else "Today, good luck is on your side.\\nNew doors will open for you.").replace("\\n", "\n")
out = sys.argv[2] if len(sys.argv) > 2 else "out.mp4"
seed = zlib.crc32(msg.encode())
rnd = random.Random(seed)

GF = "/usr/share/fonts/truetype/google-fonts/"
def font(paths, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
ANTON = [GF + "ofl/anton/Anton-Regular.ttf", GF + "ofl/archivoblack/ArchivoBlack-Regular.ttf"]
POP = [GF + "Poppins-Bold.ttf", GF + "ofl/firasans/FiraSans-ExtraBold.ttf"]
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

THEMES = {
    "gold":    dict(c=(255, 196, 70), e=(48, 8, 70), hero="🌟", rain=["💰", "✨", "🪙"]),
    "emerald": dict(c=(70, 230, 150), e=(0, 36, 30), hero="🍀", rain=["🍀", "💵", "✨"]),
    "sunrise": dict(c=(255, 150, 70), e=(110, 0, 55), hero="⭐", rain=["✨", "🌟", "💫"]),
    "royal":   dict(c=(110, 160, 255), e=(8, 8, 55), hero="💎", rain=["💎", "✨", "💫"]),
    "pink":    dict(c=(255, 125, 195), e=(70, 0, 60), hero="🌸", rain=["🌸", "✨", "💖"]),
}
theme_name = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] in THEMES else list(THEMES)[seed % len(THEMES)]
TH = THEMES[theme_name]
HOOKS = ["DON'T SKIP\nTHIS", "THIS LUCK IS\nFOR YOU", "YOU WERE MEANT\nTO SEE THIS", "STOP!\nREAD THIS"]
hook = HOOKS[(seed >> 3) % len(HOOKS)]

# ---------- helpers ----------
def ease_back(x):  # overshoot pop
    x = min(1, max(0, x)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def clamp(x): return min(1.0, max(0.0, x))

_emoji_cache = {}
def emoji(ch, size):
    key = (ch, size)
    if key not in _emoji_cache:
        try:
            f = ImageFont.truetype(EMOJI_FONT, 109)
            im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
            im = im.crop(im.getbbox() or (0, 0, 160, 160))
        except Exception:
            im = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
            ImageDraw.Draw(im).ellipse([10, 10, 90, 90], fill=(255, 215, 0, 255))
        r = size / max(im.size)
        _emoji_cache[key] = im.resize((max(1, int(im.width * r)), max(1, int(im.height * r))), Image.LANCZOS)
    return _emoji_cache[key]

def gradient_text(text, fnt, top, bot, stroke=8, glow=None, spacing=1.1):
    lines = text.split("\n")
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    widths = [d0.textlength(l, font=fnt) for l in lines]
    lh = int(fnt.size * spacing)
    pad = 60
    w, h = int(max(widths)) + pad * 2, lh * len(lines) + pad * 2
    mask = Image.new("L", (w, h), 0); smask = Image.new("L", (w, h), 0)
    dm, ds = ImageDraw.Draw(mask), ImageDraw.Draw(smask)
    for i, l in enumerate(lines):
        x = (w - widths[i]) / 2; y = pad + i * lh
        dm.text((x, y), l, font=fnt, fill=255)
        ds.text((x, y), l, font=fnt, fill=255, stroke_width=stroke, stroke_fill=255)
    g = np.linspace(0, 1, h)[:, None, None]
    fill = (np.array(top)[None, None, :] * (1 - g) + np.array(bot)[None, None, :] * g).astype(np.uint8)
    fill = Image.fromarray(np.repeat(fill, w, axis=1), "RGB").convert("RGBA")
    out_im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if glow:
        gl = Image.new("RGBA", (w, h), glow + (0,)); gl.putalpha(smask.filter(ImageFilter.GaussianBlur(22)).point(lambda v: min(255, v * 2)))
        out_im = Image.alpha_composite(out_im, gl)
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0)); sh.putalpha(smask.filter(ImageFilter.GaussianBlur(4)).point(lambda v: v * 0.6))
    out_im.alpha_composite(sh, (6, 10))
    st = Image.new("RGBA", (w, h), (40, 15, 0, 255)); st.putalpha(smask)
    out_im = Image.alpha_composite(out_im, st)
    fill.putalpha(mask)
    return Image.alpha_composite(out_im, fill)

def paste_scaled(base, im, cx, cy, s, alpha=1.0):
    if s <= 0.01 or alpha <= 0.01: return
    if abs(s - 1) > 0.01:
        im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
    if alpha < 0.99:
        a = im.getchannel("A").point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

# ---------- precomputed layers ----------
yy, xx = np.mgrid[0:H, 0:W]
r = np.sqrt((xx - W / 2) ** 2 + ((yy - 560) * 0.8) ** 2) / 1300
r = np.clip(r, 0, 1)[..., None]
c, e = np.array(TH["c"]), np.array(TH["e"])
bg_arr = (c * (1 - r) ** 1.6 + e * (1 - (1 - r) ** 1.6)).astype(np.uint8)
BG = Image.fromarray(bg_arr, "RGB").convert("RGBA")
HOOK_BG = Image.fromarray((np.array(TH["e"]) * 0.6 * (1 - r * 0.5) + 10).astype(np.uint8), "RGB").convert("RGBA")

# light rays
R = 2400
rays = Image.new("L", (R, R), 0); dr = ImageDraw.Draw(rays)
for k in range(18):
    a0 = k * 20; a1 = a0 + 8
    dr.pieslice([0, 0, R, R], a0, a1, fill=70)
rays = rays.filter(ImageFilter.GaussianBlur(14))
rmask = Image.fromarray((np.clip(1 - np.sqrt((np.mgrid[0:R, 0:R][0] - R / 2) ** 2 + (np.mgrid[0:R, 0:R][1] - R / 2) ** 2) / (R / 2), 0, 1) * 255).astype(np.uint8))
rays = Image.fromarray((np.array(rays, dtype=np.float32) * np.array(rmask) / 255).astype(np.uint8))
RAYCOL = Image.new("RGBA", (R, R), (255, 245, 200, 0))

# vignette
v = np.clip((np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) - 0.6) / 0.8, 0, 1)
VIGN = Image.new("RGBA", (W, H), (0, 0, 0, 0)); VIGN.putalpha(Image.fromarray((v * 190).astype(np.uint8)))

# glow orb behind hero
orb = Image.new("RGBA", (900, 900), (0, 0, 0, 0))
ImageDraw.Draw(orb).ellipse([150, 150, 750, 750], fill=(255, 240, 190, 170))
orb = orb.filter(ImageFilter.GaussianBlur(90))

title = gradient_text("GOOD LUCK", font(ANTON, 230), (255, 252, 215), (255, 168, 20), stroke=10, glow=(255, 200, 80))
hook_img = gradient_text(hook, font(ANTON, 150), (255, 255, 255), (255, 215, 90), stroke=9, glow=(255, 60, 60))
dtmp = ImageDraw.Draw(Image.new("L", (1, 1)))
msz = 72
while msz > 40 and max(dtmp.textlength(l, font=font(POP, msz)) for l in msg.split("\n")) > 920:
    msz -= 2
f_msg = font(POP, msz)
msg_words = []
ytop = 1150
for li, line in enumerate(msg.split("\n")):
    words = line.split()
    ws = [dtmp.textlength(w + " ", font=f_msg) for w in words]
    x = (W - sum(ws) + dtmp.textlength(" ", font=f_msg)) / 2
    for w, wd in zip(words, ws):
        im = Image.new("RGBA", (int(wd) + 60, 140), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((30, 30), w, font=f_msg, fill=(255, 255, 255, 255), stroke_width=5, stroke_fill=(30, 10, 40, 255))
        msg_words.append((im, x - 30 + im.width / 2, ytop + li * int(msz * 1.4) + 70))
        x += wd
cta_f = font(POP, 50)
cta_txt = "Type  YES  to claim your luck"
cw = int(dtmp.textlength(cta_txt, font=cta_f)) + 110
cta = Image.new("RGBA", (cw + 40, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(cta)
d.rounded_rectangle([20, 25, cw + 20, 125], 50, fill=(255, 255, 255, 255))
d.text(((cw + 40) / 2, 75), cta_txt, font=cta_f, fill=(200, 20, 60, 255), anchor="mm")
cta_glow = cta.filter(ImageFilter.GaussianBlur(18))
handle_f = font(POP, 40)

# particles
sparks = [(rnd.random() * W, rnd.random() * H, rnd.uniform(4, 11), rnd.random() * 6.28, rnd.uniform(1.5, 4)) for _ in range(70)]
rain = [(rnd.random() * W, rnd.uniform(-H, H), rnd.uniform(40, 80), rnd.uniform(180, 380), rnd.choice(TH["rain"]), rnd.uniform(-40, 40)) for _ in range(22)]
orbit = [(i * 2 * math.pi / 8, rnd.choice(TH["rain"])) for i in range(8)]

def draw_spark(d, x, y, s, a):
    col = (255, 250, 220, int(a))
    d.polygon([(x, y - s * 2.2), (x + s * 0.5, y), (x, y + s * 2.2), (x - s * 0.5, y)], fill=col)
    d.polygon([(x - s * 2.2, y), (x, y - s * 0.5), (x + s * 2.2, y), (x, y + s * 0.5)], fill=col)

HOOK_END = 2.2
def frame(i):
    t = i / FPS
    if t < HOOK_END:
        im = HOOK_BG.copy()
        p = t / 0.45
        s = ease_back(p) * (1 + 0.03 * math.sin(t * 18))
        shake = 8 * math.sin(t * 50) * clamp(1 - t)
        paste_scaled(im, hook_img, W / 2 + shake, H / 2 - 60, s)
        paste_scaled(im, emoji(TH["hero"], 200), W / 2, H / 2 - 420, ease_back((t - 0.2) / 0.4) * (1 + 0.12 * math.sin(t * 10)))
        hand = emoji("👇", 170)
        paste_scaled(im, hand, W / 2, H / 2 + 330 + 25 * math.sin(t * 9), ease_back((t - 0.5) / 0.4))
        if t > HOOK_END - 0.15:
            fl = Image.new("RGBA", (W, H), (255, 255, 255, int(255 * (t - (HOOK_END - 0.15)) / 0.15)))
            im = Image.alpha_composite(im, fl)
        return im.convert("RGB")
    tm = t - HOOK_END
    im = BG.copy()
    # rays
    rot = rays.rotate(tm * 12, resample=Image.BILINEAR)
    rc = RAYCOL.copy(); rc.putalpha(rot.point(lambda q: int(q * (0.8 + 0.2 * math.sin(tm * 2)))))
    im.alpha_composite(rc, (int(W / 2 - R / 2), int(560 - R / 2)))
    d = ImageDraw.Draw(im)
    for x, y, s, ph, sp in sparks:
        a = 255 * (0.5 + 0.5 * math.sin(t * sp + ph))
        draw_spark(d, x, (y - tm * 30 * sp) % H, s * (0.6 + 0.4 * a / 255), a)
    # rain
    for x, y0, size, sp, ch, rotv in rain:
        y = (y0 + tm * sp) % (H + 200) - 100
        em = emoji(ch, int(size))
        paste_scaled(im, em.rotate(rotv * math.sin(tm * 2), expand=True), x + 20 * math.sin(tm + y0), y, 1, 0.85)
    # hero
    hs = ease_back(tm / 0.6) * (1 + 0.06 * math.sin(tm * 4))
    paste_scaled(im, orb, W / 2, 560, hs * (1 + 0.1 * math.sin(tm * 3)))
    for ang, ch in orbit:
        a = ang + tm * 1.2
        paste_scaled(im, emoji(ch, 70), W / 2 + 290 * math.cos(a), 560 + 120 * math.sin(a), clamp(tm / 0.8))
    paste_scaled(im, emoji(TH["hero"], 330), W / 2, 560 + 12 * math.sin(tm * 3), hs)
    # title
    ts = ease_back((tm - 0.35) / 0.5) * (1 + 0.025 * math.sin(tm * 5))
    paste_scaled(im, title, W / 2, 960, ts)
    # glass panel behind message
    pa = clamp((tm - 1.0) / 0.4)
    if pa > 0:
        nl = len(msg.split("\n"))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ov).rounded_rectangle([40, ytop + 10, W - 40, ytop + 130 + (nl - 1) * int(msz * 1.4)], 40, fill=(20, 0, 30, int(120 * pa)), outline=(255, 220, 140, int(200 * pa)), width=4)
        im = Image.alpha_composite(im, ov)
    # message words pop one by one
    for k, (wim, cx, cy) in enumerate(msg_words):
        st = 1.2 + k * 0.22
        paste_scaled(im, wim, cx, cy, ease_back((tm - st) / 0.35), clamp((tm - st) / 0.2))
    # CTA
    cstart = 1.6 + len(msg_words) * 0.22 + 0.6
    if tm > cstart:
        pulse = 1 + 0.06 * math.sin((tm - cstart) * 7)
        s = ease_back((tm - cstart) / 0.4) * pulse
        paste_scaled(im, cta_glow, W / 2, 1520, s * 1.05)
        paste_scaled(im, cta, W / 2, 1520, s)
        paste_scaled(im, emoji("👆", 110), W / 2 + cw / 2 - 30, 1630 + 18 * math.sin(tm * 8), clamp((tm - cstart - 0.3) / 0.2))
    im = Image.alpha_composite(im, VIGN)
    d = ImageDraw.Draw(im)
    d.text((W / 2, 1800), "@hemender187Official", font=handle_f, fill=(255, 255, 255, 220), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, 160))
    if tm < 0.35:  # flash out of transition
        im = Image.alpha_composite(im, Image.new("RGBA", (W, H), (255, 255, 255, int(255 * (1 - tm / 0.35)))))
    if t > DUR - 0.6:
        im = Image.alpha_composite(im, Image.new("RGBA", (W, H), (0, 0, 0, int(255 * (t - (DUR - 0.6)) / 0.6))))
    return im.convert("RGB")

# ---------- music ----------
SR = 48000
def make_audio(path):
    n = SR * DUR; tt = np.arange(n) / SR
    mix = np.zeros(n)
    nf = lambda m: 440 * 2 ** ((m - 69) / 12)
    prog = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]  # C G Am F
    bar = 2.0
    def env(start, dur, a=0.02, rel=0.5):
        e = np.zeros(n); s0 = int(start * SR); s1 = min(n, int((start + dur + rel) * SR))
        if s0 >= n: return e
        x = (np.arange(s0, s1) - s0) / SR
        e[s0:s1] = np.minimum(1, x / a) * np.where(x < dur, 1, np.exp(-(x - dur) * 6))
        return e
    # soft riser during hook
    rs = tt < HOOK_END
    mix[rs] += 0.12 * np.sin(2 * np.pi * (300 + 500 * (tt[rs] / HOOK_END) ** 2) * tt[rs]) * (tt[rs] / HOOK_END)
    mix += 0.04 * np.random.default_rng(seed).standard_normal(n) * np.exp(-((tt - HOOK_END) ** 2) / 0.02)  # whoosh
    t0 = HOOK_END
    k = 0
    while t0 + k * bar < DUR:
        ch = prog[k % 4]; st = t0 + k * bar
        for m in ch:  # pad
            f = nf(m - 12)
            mix += 0.05 * env(st, bar, 0.3, 0.6) * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt))
        mix += 0.08 * env(st, bar * 0.9, 0.02, 0.3) * np.sin(2 * np.pi * nf(ch[0] - 24) * tt)  # bass
        arp = ch + [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12, ch[0] + 12]
        for j, m in enumerate(arp):  # bell arpeggio (8ths)
            s = st + j * bar / 8
            if s >= DUR: break
            s0 = int(s * SR); x = tt[s0:] - s
            f = nf(m + 12)
            mix[s0:] += 0.07 * np.exp(-x * 5) * (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(2 * np.pi * 2.76 * f * x) * np.exp(-x * 8))
        k += 1
    # chime glissando at reveal
    for j, m in enumerate([84, 88, 91, 96]):
        s = HOOK_END + 0.35 + j * 0.07; s0 = int(s * SR); x = tt[s0:] - s
        mix[s0:] += 0.08 * np.exp(-x * 3) * np.sin(2 * np.pi * nf(m) * x)
    fade = np.minimum(1, np.minimum(tt / 0.05, (DUR - tt) / 0.8))
    mix *= np.clip(fade, 0, 1)
    mix = mix / (np.abs(mix).max() + 1e-9) * 0.8
    st = np.stack([mix, np.roll(mix, 240)], 1)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((st * 32767).astype(np.int16).tobytes())

tmpd = tempfile.mkdtemp()
wav = os.path.join(tmpd, "a.wav"); make_audio(wav)
p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                      "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                      "-profile:v", "high", "-level", "4.0", "-r", "30", "-c:a", "aac", "-ar", "48000", "-b:a", "160k",
                      "-movflags", "+faststart", "-shortest", out], stdin=subprocess.PIPE)
for i in range(N):
    p.stdin.write(frame(i).tobytes())
p.stdin.close(); p.wait()
print(f"wrote {out} (theme={theme_name})")
