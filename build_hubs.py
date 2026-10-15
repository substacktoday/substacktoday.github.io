#!/usr/bin/env python3
"""Build the three hub pages (static HTML, no JS) from JSON data.
  /reels/index.html  <- data/reels.json
  /notes/index.html  <- data/notes.json
  /posts/index.html  <- data/posts-hub.json (refresh from Substack with --refresh-posts)
Usage (run from anywhere):
  python3 build_hubs.py                  # rebuild pages from the JSON files
  python3 build_hubs.py --refresh-posts  # re-fetch Brooke's Substack archive first, then rebuild
  python3 build_hubs.py --thumb <cover.png> <reel-id>   # make img/reels/<reel-id>.jpg (360x640) from a 1080x1920 cover
Never touches index.html (the home page grid is owned by grid.py / log_post.py / update.py)."""
import json, os, sys, html, datetime, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
ARCH = "https://brookekaylee.substack.com/api/v1/archive?sort=new&limit=50"
E = lambda s: html.escape(str(s), quote=True)

CSS = """*{box-sizing:border-box;margin:0}body{background:#1C3AD6;color:#FAF6EC;font-family:-apple-system,"Helvetica Neue",Arial,sans-serif;min-height:100vh;-webkit-text-size-adjust:100%}
a{color:inherit}.w{max-width:560px;margin:0 auto;padding:22px 14px 40px}
.k{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#C6F028}
h1{font-family:Impact,"Anton","Arial Narrow Bold",sans-serif;font-weight:900;text-transform:uppercase;font-size:44px;line-height:.98;margin:10px 0 8px;letter-spacing:.01em}
h1 span{color:#C6F028}p.s{font-size:15px;line-height:1.4;max-width:36ch;margin-bottom:18px}
.tabs{display:flex;gap:6px;margin-bottom:22px}.tabs a{flex:1;text-align:center;text-decoration:none;font-family:Impact,"Arial Black",sans-serif;text-transform:uppercase;font-size:15px;letter-spacing:.05em;padding:10px 4px;border:3px solid #121212;background:#FAF6EC;color:#121212;box-shadow:3px 3px 0 #121212}
.tabs a.on{background:#C6F028}.tabs a:active{transform:translate(2px,2px);box-shadow:1px 1px 0 #121212}
.cards{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}.card{background:#FAF6EC;color:#121212;border:3px solid #121212;box-shadow:5px 5px 0 #121212;display:flex;flex-direction:column}
.th{position:relative;display:block;background:#121212}.th img{display:block;width:100%;height:auto;aspect-ratio:9/16;object-fit:cover}
.bd{position:absolute;left:6px;top:6px;font-size:10px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;background:#C6F028;color:#121212;border:2px solid #121212;padding:3px 6px}.bd.soon{background:#FFD60A}
.cb{padding:10px 10px 12px;display:flex;flex-direction:column;gap:8px;flex:1}
.ct{font-family:Impact,"Anton","Arial Narrow Bold",sans-serif;text-transform:uppercase;font-size:19px;line-height:1.05;letter-spacing:.01em}
.cw{font-size:12px;line-height:1.3;opacity:.8}.bt{display:block;text-align:center;text-decoration:none;font-family:Impact,"Arial Black",sans-serif;text-transform:uppercase;letter-spacing:.04em;font-size:13px;padding:9px 6px;border:2px solid #121212;box-shadow:3px 3px 0 #121212;color:#FAF6EC;background:#FF3EA5;line-height:1.1}
.bt.rd{background:#121212;color:#C6F028}.bt:active{transform:translate(2px,2px);box-shadow:1px 1px 0 #121212}.bs{margin-top:auto;display:flex;flex-direction:column;gap:8px}
.list{display:flex;flex-direction:column;gap:14px}.list .card{padding:14px 14px 16px;gap:8px}
.dt{font-size:11px;letter-spacing:.1em;text-transform:uppercase;opacity:.65}.nt{font-size:16px;line-height:1.45}.ab{font-size:12px;opacity:.7}
.pt{font-family:Impact,"Anton","Arial Narrow Bold",sans-serif;text-transform:uppercase;font-size:26px;line-height:1.02}.ph{font-size:15px;line-height:1.4}
.lk{font-weight:800;font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:#1C3AD6;text-decoration:none;margin-top:2px}.lk+.lk{margin-left:14px}
.f{display:flex;justify-content:space-between;font-size:11px;letter-spacing:.1em;text-transform:uppercase;margin-top:24px;opacity:.85}
@media(min-width:760px){.w{max-width:900px}.cards{grid-template-columns:repeat(3,1fr)}}"""

TABS = [("", "Home"), ("reels/", "Reels"), ("posts/", "Posts"), ("notes/", "Notes")]

def page(slug, title, kicker, h1, sub, body):
    up = "../"
    tabs = "".join(f'<a href="{up}{p}"{" class=on" if p == slug else ""}>{n}</a>' for p, n in TABS)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)} · Substack today</title><meta name="description" content="{E(sub)}">
<style>{CSS}</style></head><body><main class="w">
<div class="k">{E(kicker)}</div>
<h1>{h1}</h1><p class="s">{E(sub)}</p>
<nav class="tabs" aria-label="Sections">{tabs}</nav>
{body}
<div class="f"><span>Substack today</span><a href="https://brookekaylee.substack.com/?utm_source=instagram&amp;utm_medium=bio">Read on Substack →</a></div>
</main></body></html>
"""

def fdate(s):
    return datetime.date.fromisoformat(s[:10]).strftime("%b %-d, %Y")

def reels():
    d = json.load(open("data/reels.json"))["reels"]; cards = []
    for r in d:
        if r.get("hidden"): continue
        posted = r.get("status") == "posted" and r.get("ig")
        badge = '<span class="bd">Live</span>' if posted else '<span class="bd soon">Coming soon</span>'
        who = r["writer"] + (" · " + r["publication"] if r.get("publication") and r["publication"] != r["writer"] else "")
        btns = ""
        if posted: btns += f'<a class="bt" href="{E(r["ig"])}" rel="noopener">Watch on Instagram</a>'
        for a in r["articles"]: btns += f'<a class="bt rd" href="{E(a["url"])}" rel="noopener">{E(a.get("label") or "Read the article")}</a>'
        first = r["ig"] if posted else r["articles"][0]["url"]
        cards.append(f'<article class="card"><a class="th" href="{E(first)}" rel="noopener"><img src="../{E(r["cover"])}" width="360" height="640" alt="{E(r["title"])}" loading="lazy" decoding="async">{badge}</a>'
                     f'<div class="cb"><h2 class="ct">{E(r["title"])}</h2><div class="cw">Writer: {E(who)}</div><div class="bs">{btns}</div></div></article>')
    return page("reels/", "Reels", "@substacktoday · short reels", "Reels <span>on Substack</span>",
                "Quick reels on the best of Substack. Watch the reel, then read the full article.",
                '<div class="cards">' + "\n".join(cards) + "</div>")

def notes():
    d = sorted(json.load(open("data/notes.json"))["notes"], key=lambda n: (n["date"], n["url"]), reverse=True); cards = []
    for n in d:
        if n.get("hidden"): continue
        ab = f'<div class="ab">{E(n["about"])}</div>' if n.get("about") else ""
        links = f'<a class="lk" href="{E(n["url"])}" rel="noopener">View the Note →</a>'
        if n.get("read_url"): links += f'<a class="lk" href="{E(n["read_url"])}" rel="noopener">Read the essay →</a>'
        cards.append(f'<article class="card"><div class="dt">{fdate(n["date"])}{" · Restack" if n.get("kind") == "restack" else ""}</div>{ab}<p class="nt">{E(n["text"])}</p><div>{links}</div></article>')
    return page("notes/", "Notes", "Material Girl, Immaterial World · Notes", "Quick <span>Notes</span>",
                "Short takes from Brooke on Substack Notes. Tap one to see it and join the conversation.",
                '<div class="list">' + "\n".join(cards) + "</div>")

def posts():
    d = sorted(json.load(open("data/posts-hub.json"))["posts"], key=lambda p: p["date"], reverse=True); cards = []
    for p in d:
        cards.append(f'<article class="card"><div class="dt">{fdate(p["date"])}</div><h2 class="pt">{E(p["title"])}</h2><p class="ph">{E(p["hook"])}</p>'
                     f'<div><a class="lk" href="{E(p["url"])}" rel="noopener">Read on Substack →</a></div></article>')
    return page("posts/", "Posts", "Material Girl, Immaterial World · essays", "My <span>Substack</span> posts",
                "Brooke's essays, newest first. One idea per post, no filler.",
                '<div class="list">' + "\n".join(cards) + "</div>")

def refresh_posts():
    req = urllib.request.Request(ARCH, headers={"User-Agent": "Mozilla/5.0"})
    arch = json.loads(urllib.request.urlopen(req, timeout=30).read())
    ps = [dict(title=p["title"], hook=(p.get("subtitle") or p.get("description") or "").strip(), date=p["post_date"][:10], url=p["canonical_url"], slug=p["slug"])
          for p in arch if p.get("audience") == "everyone" and p.get("type") == "newsletter"]
    if not ps: raise SystemExit("refresh-posts: archive returned nothing, keeping existing data")
    os.makedirs("data", exist_ok=True); json.dump({"posts": ps}, open("data/posts-hub.json", "w"), indent=1, ensure_ascii=False)
    print("posts refreshed:", len(ps))

def build():
    for slug, fn in (("reels", reels), ("notes", notes), ("posts", posts)):
        os.makedirs(slug, exist_ok=True); out = fn()
        old = open(f"{slug}/index.html").read() if os.path.exists(f"{slug}/index.html") else None
        if out != old: open(f"{slug}/index.html", "w").write(out); print("wrote", slug + "/index.html")

def thumb(src, rid):
    from PIL import Image
    os.makedirs("img/reels", exist_ok=True)
    Image.open(src).convert("RGB").resize((360, 640)).save(f"img/reels/{rid}.jpg", quality=80, optimize=True, progressive=True); print("img/reels/%s.jpg" % rid)

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--thumb"]: thumb(a[1], a[2]); sys.exit()
    if "--refresh-posts" in a:
        try: refresh_posts()
        except Exception as e: print("posts refresh skipped:", e)
    build()
