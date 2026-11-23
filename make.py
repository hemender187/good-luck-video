import sys, math, random, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,DUR=1080,1920,30,15
msg=sys.argv[1].replace("\\n","\n") if len(sys.argv)>1 else "Today, good luck is on your side.\nNew doors will open for you."
out=sys.argv[2] if len(sys.argv)>2 else "out.mp4"
F="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
big=ImageFont.truetype(F,110); mid=ImageFont.truetype(F,58); sm=ImageFont.truetype(F,44)
random.seed(hash(msg)%1000)
stars=[(random.random()*W,random.random()*H,random.random()*3+1,random.random()*6.28) for _ in range(120)]
def bg(t):
    im=Image.new("RGB",(W,H)); d=ImageDraw.Draw(im)
    for y in range(0,H,4):
        k=y/H; s=0.5+0.5*math.sin(t*0.4)
        c=(int(60+120*k*s+40),int(20+60*k),int(90-40*k+30*s))
        d.rectangle([0,y,W,y+4],fill=c)
    return im
def centered(d,y,text,font,fill,alpha=255):
    for line in text.split("\n"):
        w=d.textlength(line,font=font); d.text(((W-w)/2,y),line,font=font,fill=fill+(alpha,)); y+=font.size*1.35
    return y
p=subprocess.Popen(["ffmpeg","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
 "-f","lavfi","-i",f"sine=frequency=528:duration={DUR},volume=0.15","-f","lavfi","-i",f"sine=frequency=396:duration={DUR},volume=0.1",
 "-filter_complex","[1][2]amix=inputs=2,afade=t=in:d=2,afade=t=out:st=13:d=2[a]","-map","0:v","-map","[a]",
 "-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p","-c:a","aac","-ar","48000","-b:a","128k","-profile:v","high","-level","4.0","-r","30","-movflags","+faststart","-shortest",out],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
for i in range(FPS*DUR):
    t=i/FPS; im=bg(t).convert("RGBA"); ov=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(ov)
    for x,y,r,ph in stars:
        a=int(120+120*math.sin(t*2+ph)); yy=(y-t*20*r)%H; d.ellipse([x-r,yy-r,x+r,yy+r],fill=(255,230,150,max(0,a)))
    cx,cy=W/2,520; R=150+10*math.sin(t*2)
    glow=Image.new("RGBA",(W,H),(0,0,0,0)); g=ImageDraw.Draw(glow); g.ellipse([cx-R-60,cy-R-60,cx+R+60,cy+R+60],fill=(255,200,80,90)); glow=glow.filter(ImageFilter.GaussianBlur(40))
    im=Image.alpha_composite(im,glow); im=Image.alpha_composite(im,ov); d=ImageDraw.Draw(im)
    d.ellipse([cx-R,cy-R,cx+R,cy+R],fill=(255,210,90,255))
    d.text((cx-d.textlength("★",font=big)/2,cy-70),"★",font=big,fill=(180,90,20,255))
    a1=int(255*min(1,max(0,(t-0.5)/1.0)))
    centered(d,800,"GOOD LUCK",big,(255,240,200),a1)
    a2=int(255*min(1,max(0,(t-2)/1.5)))
    centered(d,1020,msg,mid,(255,255,255),a2)
    a3=int(255*min(1,max(0,(t-6)/1.5)))
    centered(d,1500,"Type 'YES' in comments\nto accept your luck ★",sm,(255,225,140),a3)
    centered(d,1780,"@hemender187Official",sm,(230,220,255),200)
    p.stdin.write(im.convert("RGB").tobytes())
p.stdin.close(); p.wait()
