#!/usr/bin/env python3
"""Turn a 16:9 Gemini clip into a 9:16 Amrit-Chakra reel with Hindi+English captions, title, badge and end card.
usage: reel_from_clip.py <in.mp4> <out.mp4> <config.json>
config: {"part":1,"captions":[[start,end,"hindi","english"],...],"next_hi":"...","next_en":"...","end_secs":4}
"""
import json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlib import W, H, FPS, GF, F, clamp, ease, ease_back, wrap, gold_text, glow, paste, Sparks

src, out, cfgp = sys.argv[1:4]
cfg = json.load(open(cfgp)); PART = cfg["part"]; END = cfg.get("end_secs", 4.0)
PB = GF + "Poppins-Bold.ttf"; PM = GF + "Poppins-Medium.ttf"
def P(s, b=True): return ImageFont.truetype(PB if b else PM, s)
dur_src = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]).decode())
DUR = dur_src + END; N = int(DUR * FPS)
VY, VH = 600, 608  # video slot

# ffmpeg: blurred bg + centered video, last frame frozen for end card, at 30fps
fc = (f"[0:v]fps={FPS},tpad=stop_mode=clone:stop_duration={END},split[a][b];"
      f"[a]scale=-2:{H},crop={W}:{H},boxblur=30:3,eq=brightness=-0.25:saturation=1.2[bg];"
      f"[b]scale={W}:{VH}[fg];[bg][fg]overlay=0:{VY},format=rgb24")
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-filter_complex", fc, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
tmp = out + ".part.mp4"; wav = out + ".wav"

# audio: original + soft drone tail under end card
SR = 48000
raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", src, "-f", "s16le", "-ac", "2", "-ar", str(SR), "-"])
a = np.frombuffer(raw, np.int16).reshape(-1, 2).astype(float) / 32768
n = int(DUR * SR); mix = np.zeros((n, 2)); mix[:len(a)] = a[:n]
tt = np.arange(n) / SR; t0 = dur_src - 1.0; m = tt > t0; x = tt[m] - t0
nf = lambda k: 440 * 2 ** ((k - 69) / 12)
tail = sum(np.sin(2 * np.pi * nf(k) * x) for k in (50, 57, 62, 65)) * 0.05 * np.minimum(1, x / 0.8)
for j, k in enumerate([74, 77, 81, 86]):
    s = 1.6 + j * 0.25; xx = np.clip(x - s, 0, None); tail += 0.07 * (x > s) * np.exp(-xx * 2.5) * np.sin(2 * np.pi * nf(k) * xx)
mix[m] += tail[:, None]
ss = int(dur_src * SR); fade_src = np.ones(n); fade_src[ss - SR // 2:ss] = np.linspace(1, 0.3, SR // 2)
fade = np.clip((DUR - tt) / 1.2, 0, 1); mix *= fade[:, None]
mix = mix / max(1e-9, np.abs(mix).max()) * 0.9
with wave.open(wav, "wb") as wf:
    wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((mix * 32767).astype(np.int16).tobytes())

enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0",
                        "-c:a", "aac", "-ar", "48000", "-b:a", "160k", "-movflags", "+faststart", "-shortest", tmp], stdin=subprocess.PIPE)

TITLE = gold_text("अमृत-चक्र", P(150)); SUB = gold_text("THE DIVINE MYSTERY", F("anton", 70), (255, 255, 255), (220, 210, 255), 5, (150, 100, 255))
badge = Image.new("RGBA", (420, 84)); bd = ImageDraw.Draw(badge)
bd.rounded_rectangle((0, 0, 419, 83), 42, fill=(200, 25, 50, 240), outline=(255, 220, 120, 255), width=4)
bd.text((210, 44), f"भाग {PART} · Part {PART}", font=P(40), fill=(255, 255, 255), anchor="mm")
HI_F, EN_F = P(52), P(36, False)

def cap(base, hi, en, lt, ld):
    hl, el = wrap(hi, HI_F, 960), wrap(en, EN_F, 960); lh, le = 78, 50
    a = clamp(lt / 0.3) * clamp((ld - lt) / 0.3); y = VY + VH + 50
    if a <= 0: return
    bh = lh * len(hl) + le * len(el) + 70
    box = Image.new("RGBA", (W - 50, bh)); ImageDraw.Draw(box).rounded_rectangle((0, 0, W - 51, bh - 1), 34, fill=(8, 4, 18, int(200 * a)), outline=(255, 200, 90, int(220 * a)), width=4)
    base.alpha_composite(box, (25, y)); d = ImageDraw.Draw(base); A = int(255 * a)
    for i, l in enumerate(hl): d.text((W / 2, y + 30 + i * lh + lh / 2 - 6), l, font=HI_F, fill=(255, 255, 255, A), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0, A))
    for j, l in enumerate(el): d.text((W / 2, y + 35 + len(hl) * lh + j * le + le / 2), l, font=EN_F, fill=(255, 220, 140, A), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, A))

sp = Sparks(30, (0, 0, W, 560), seed=3)
for i in range(N):
    buf = dec.stdout.read(W * H * 3)
    if len(buf) < W * H * 3: break
    t = i / FPS; im = Image.frombytes("RGB", (W, H), buf).convert("RGBA"); d = ImageDraw.Draw(im)
    d.rectangle((0, VY - 4, W, VY), fill=(255, 200, 90, 255)); d.rectangle((0, VY + VH, W, VY + VH + 4), fill=(255, 200, 90, 255))
    sp.draw(im, t, rise=10)
    paste(im, TITLE, W / 2, 200, ease_back(t / 0.5) * (1 + 0.015 * math.sin(t * 3)))
    paste(im, SUB, W / 2, 345, 1.0, clamp((t - 0.3) / 0.4))
    paste(im, badge, W / 2, 470, ease_back((t - 0.6) / 0.4))
    if t < dur_src:
        for s, e, hi, en in cfg["captions"]:
            if s <= t < e: cap(im, hi, en, t - s, e - s)
    else:
        te = t - dur_src
        im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(150 * clamp(te / 0.4)))))
        a2 = ease_back(te / 0.5)
        if a2 > 0:
            nb = Image.new("RGBA", (980, 240)); nd = ImageDraw.Draw(nb); nd.rounded_rectangle((0, 0, 979, 239), 40, fill=(15, 10, 40, 235), outline=(255, 200, 90, 255), width=5)
            nd.text((490, 75), cfg["next_hi"], font=P(50), fill=(255, 255, 255), anchor="mm"); nd.text((490, 160), cfg["next_en"], font=P(38, False), fill=(255, 210, 130), anchor="mm")
            paste(im, nb, W / 2, 900, a2)
        a3 = ease_back((te - 0.6) / 0.5)
        if a3 > 0:
            b = Image.new("RGBA", (880, 140)); bb = ImageDraw.Draw(b); bb.rounded_rectangle((0, 0, 879, 139), 70, fill=(230, 30, 70, 255), outline=(255, 255, 255, 255), width=6)
            bb.text((440, 70), f"Follow करें — Part {PART + 1} के लिए!", font=P(50), fill=(255, 255, 255), anchor="mm")
            paste(im, b, W / 2, 1450, a3 * (1 + 0.04 * math.sin(t * 7)))
        if te > END - 0.7: im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * clamp((te - END + 0.7) / 0.7)))))
    d = ImageDraw.Draw(im)
    d.text((W / 2, 1830), "@hemender187Official", font=P(42), fill=(255, 255, 255, 230), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    if len(sys.argv) > 4 and i % int(sys.argv[4]) == 0: im.convert("RGB").resize((540, 960)).save(f"{out}.f{i:04d}.jpg", quality=80)
    enc.stdin.write(im.convert("RGB").tobytes())
enc.stdin.close(); dec.wait(); assert enc.wait() == 0
os.replace(tmp, out); os.remove(wav); print("wrote", out, DUR)
