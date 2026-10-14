#!/usr/bin/env python3
"""Add a tile to the top of the link-in-bio grid for every new Substack post, then commit and push.
Run from anywhere:  python3 /workspace/substack-writer/growth/ig-pop/linkinbio/update.py  [--no-push]"""
import json, os, re, sys, io, random, subprocess, urllib.request, html
from PIL import Image, ImageDraw, ImageFont, ImageOps
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
ARCH="https://brookekaylee.substack.com/api/v1/archive?sort=new&limit=50"
G="/usr/share/fonts/truetype/sand-box/google/"
_F=os.path.join(os.path.dirname(os.path.abspath(__file__)),"fonts")
ANTON=os.path.join(_F,"Anton-Regular.ttf"); SG=os.path.join(_F,"SpaceGrotesk.ttf")
W,H,M=1080,1350,80
PAL=[((22,58,214),(198,240,40),(250,246,236)),((255,62,165),(255,214,10),(250,246,236)),((198,240,40),(22,58,214),(18,18,18)),
     ((240,64,40),(255,214,10),(250,246,236)),((255,214,10),(240,64,40),(18,18,18)),((0,150,70),(255,214,10),(250,246,236)),((255,122,0),(22,58,214),(18,18,18))]
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0"}),timeout=30).read()
def wrap(d,t,f,w):
    out=[];l=""
    for wd in t.split():
        tr=(l+" "+wd).strip()
        if d.textlength(tr,font=f)<=w: l=tr
        else: out.append(l); l=wd
    return out+[l]
def grainy(img):
    g=ImageOps.autocontrast(img.convert("L"),cutoff=2).point(lambda v:max(0,min(255,int((v-128)*1.6+128))))
    a=np.clip(np.asarray(g).astype(float)+np.random.normal(0,22,(g.height,g.width)),0,255).astype("uint8")
    g=Image.fromarray(a); w,h=g.size
    return g.resize((w//2,h//2)).convert("1").resize((w,h),Image.NEAREST).convert("RGB")
def torn(base,img,xy,angle,seed):
    rnd=random.Random(seed); b=18; w,h=img.size; W2,H2=w+2*b,h+2*b
    card=Image.new("RGB",(W2,H2),(250,246,236)); card.paste(img,(b,b)); pts=[]
    for x in range(0,W2,10): pts.append((x,rnd.randint(0,16)))
    for y in range(0,H2,10): pts.append((W2-rnd.randint(0,16),y))
    for x in range(W2,0,-10): pts.append((x,H2-rnd.randint(0,16)))
    for y in range(H2,0,-10): pts.append((rnd.randint(0,16),y))
    m=Image.new("L",(W2,H2),0); ImageDraw.Draw(m).polygon(pts,fill=255)
    c=card.convert("RGBA"); c.putalpha(m); r=c.rotate(angle,expand=True,resample=Image.BICUBIC)
    base.paste(r,xy,r)
def crop_fill(im,size):
    tw,th=size; s=max(tw/im.width,th/im.height); im=im.resize((int(im.width*s)+1,int(im.height*s)+1))
    l=(im.width-tw)//2;t=(im.height-th)//2; return im.crop((l,t,l+tw,t+th))
def hook(title):
    # main hook = title; the last word gets the accent color
    return title.strip()
def make_tile(post,idx,out):
    bg,acc,fg=PAL[idx%len(PAL)]
    im=Image.new("RGB",(W,H),bg); d=ImageDraw.Draw(im)
    d.text((M,M),"NEW ON MY SUBSTACK",font=ImageFont.truetype(SG,30),fill=acc)
    cover=post.get("cover_image")
    words=hook(post["title"]).upper()
    size=150
    while size>70:
        f=ImageFont.truetype(ANTON,size); lines=wrap(d,words,f,W-2*M)
        if len(lines)*size*1.02 < (560 if cover else 820): break
        size-=8
    y=210
    for i,l in enumerate(lines):
        d.text((M,y),l,font=f,fill=acc if i==len(lines)-1 else fg); y+=int(size*1.02)
    sub=re.split(r"(?<=[.!?])\s",(post.get("subtitle") or "").strip())[0]
    if sub:
        sf=ImageFont.truetype(SG,36)
        for l in wrap(d,sub,sf,560 if cover else W-2*M)[:4]: d.text((M,y+30),l,font=sf,fill=fg); y+=46
    if cover:
        try:
            ci=Image.open(io.BytesIO(get(cover))).convert("RGB")
            torn(im,grainy(crop_fill(ci,(330,400))),(W-M-380,H-M-520),-5,idx)
        except Exception as e: print("cover skipped:",e)
    d=ImageDraw.Draw(im); ff=ImageFont.truetype(SG,24)
    d.text((M,H-M-70),("FROM: "+post["title"]).upper()[:60],font=ff,fill=fg)
    d.text((M,H-M-34),"MATERIAL GIRL, IMMATERIAL WORLD",font=ff,fill=fg)
    t="READ ON SUBSTACK →"; d.text((W-M-d.textlength(t,font=ff),H-M-34),t,font=ff,fill=fg)
    im.resize((720,900)).save(out,quality=85)
def main():
    state=json.load(open("posts.json")); known=set(state["known_slugs"])
    posts=json.loads(get(ARCH)); new=[p for p in posts if p["slug"] not in known and p.get("audience")=="everyone"]
    if not new: print("no new posts"); return
    # Shared source of truth: feed.json (also written by log_post.py after IG posts); grid.py renders it.
    import grid, datetime
    feed=json.load(open("feed.json")) if os.path.exists("feed.json") else {"source":"shared","posts":[]}
    for p in reversed(new):   # oldest first, so the newest ends up on top
        fn=f"img/post-{p['slug']}.jpg"; make_tile(p,len(known),fn)
        url=p["canonical_url"]+"?utm_source=instagram&utm_medium=bio"
        feed["posts"]=[x for x in feed["posts"] if x.get("link")!=url]
        feed["posts"].insert(0,dict(title=p["title"],image=fn,link=url,ig="",time=datetime.datetime.now().isoformat(timespec="minutes")))
        known.add(p["slug"]); state["known_slugs"].insert(0,p["slug"]); print("added",p["title"])
    json.dump(feed,open("feed.json","w"),indent=1,ensure_ascii=False); grid.render()
    json.dump(state,open("posts.json","w"),indent=1)
    if os.path.isdir(".git"): subprocess.run(["git","add","feed.json"])  # CI workflow stages index/posts/img only
    # CI owns its commit and push; --no-push only writes the site files.
    if os.path.isdir(".git") and "--no-push" not in sys.argv:
        subprocess.run(["git","add","index.html","posts.json","feed.json","img"],check=True)
        subprocess.run(["git","commit","-m","Add tiles: "+", ".join(p["title"] for p in new)],check=True)
        subprocess.run(["git","push","origin","main"],check=True)
if __name__=="__main__": main()
