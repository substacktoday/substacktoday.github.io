#!/usr/bin/env python3
"""Shared: rewrite ONLY the tile grid (<nav class="g">...</nav>) of index.html from feed.json (newest 9).
Everything else in index.html (Brooke's title, button, styles) is left byte-for-byte alone."""
import json, html, re, os
def render(feed_path="feed.json", index="index.html", n=9):
    feed=json.load(open(feed_path))["posts"][:n]
    rows="".join(f'<a class="t" href="{html.escape(p["link"],quote=True)}" aria-label="Read: {html.escape(p["title"])}">'
                 f'<img src="{html.escape(p["image"],quote=True)}" alt="{html.escape(p["title"])}" loading="lazy"></a>\n' for p in feed)
    page=open(index).read()
    new=re.sub(r'(<nav class="g">\n).*?(</nav>)', lambda m: m.group(1)+rows+m.group(2), page, count=1, flags=re.S)
    if new!=page: open(index,"w").write(new); return True
    return False
if __name__=="__main__": print("changed" if render() else "no change")
