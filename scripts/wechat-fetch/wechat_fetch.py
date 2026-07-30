#!/usr/bin/env python3
"""
wechat_fetch.py - fetch one WeChat (mp.weixin.qq.com) article and extract it
to structured Markdown.

This is "Option 0" of setup/05-wechat-mcp.md: a direct fetch with a mobile
User-Agent. It costs ~2 seconds, needs no API key and no third party. It works
from residential networks; from datacenter IPs it usually hits the anti-bot
wall, in which case this script exits 3 and you fall through to Options A-D.

Usage:
    python wechat_fetch.py <url> [--outdir DIR] [--slug SLUG] [--min-chars N]

Produces three files sharing one stem:
    <date>_<slug>_<wxid>.html   raw HTML archive (never modify it)
    <date>_<slug>_<wxid>.md     extracted body + metadata header
    <date>_<slug>_<wxid>.imgs   image URLs referenced in the body, one per line

Exit codes:
    0  success (still run the three checks in README.md before you trust it)
    2  fetch failed (network / HTTP / response too small)
    3  body missing or shorter than --min-chars -> almost certainly the
       anti-bot wall. DO NOT write anything from this result. Refetch, or
       switch to Option A-D.
"""

import argparse
import datetime
import html as html_mod
import io
import os
import re
import subprocess
import sys

# A mobile UA is the load-bearing detail: desktop UAs are far more likely to
# get a degraded/stub page.
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


def fetch(url: str, out_html: str, timeout: int = 60) -> None:
    """Fetch with curl - same thing you would do by hand, one less dependency."""
    cmd = [
        "curl", "-s", "-L", "--max-time", str(timeout),
        "-A", MOBILE_UA, url, "-o", out_html,
    ]
    r = subprocess.run(cmd)
    if r.returncode != 0 or not os.path.exists(out_html) or os.path.getsize(out_html) < 10_000:
        sys.exit(2)


def grab(pattern: str, text: str, default=None):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else default


def extract_meta(h: str) -> dict:
    """Metadata lives in inline JS vars near the top; og: tags are the fallback."""
    ct = grab(r'var ct\s*=\s*"(\d+)"', h)
    return {
        "title": (
            grab(r"var msg_title\s*=\s*['\"](.*?)['\"]\s*\.html", h)
            or grab(r'<meta property="og:title" content="(.*?)"', h)
        ),
        "author": grab(r"var author\s*=\s*['\"](.*?)['\"]", h),
        "account": (
            grab(r"var nickname\s*=\s*['\"](.*?)['\"]", h)
            or grab(r'var user_name\s*=\s*"(.*?)"', h)
        ),
        "published": (
            datetime.datetime.fromtimestamp(int(ct)).strftime("%Y-%m-%d %H:%M")
            if ct else None
        ),
        "ct": ct,
    }


def extract_body(h: str) -> str:
    """
    Grab the HTML inside the js_content container.

    The closing anchor has several candidates on purpose: WeChat's template
    changes, and matching the first </div> truncates mid-article because the
    body is full of nested <div>/<section>.
    """
    m = re.search(
        r'id="js_content"[^>]*>(.*?)</div>\s*'
        r'(?:<script|<div id="js_tags|<div class="rich_media_tool)',
        h, re.S,
    )
    if m:
        return m.group(1)
    # Fallback: take a large slice. Better to include some trailing junk than
    # to silently cut off half the article.
    m = re.search(r'id="js_content"[^>]*>(.*)', h, re.S)
    return m.group(1)[:600_000] if m else ""


def html_to_text(body: str) -> str:
    """Order matters here; get it wrong and lines run together."""
    t = re.sub(r"<br\s*/?>", "\n", body)
    t = re.sub(r"</p>|</section>|</h\d>|</li>|</blockquote>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html_mod.unescape(t)
    # \xa0 is &nbsp; after unescaping - collapse it explicitly or every later
    # whitespace check misbehaves.
    t = re.sub(r"[ \t\xa0]+", " ", t)
    t = re.sub(r"\n\s*\n\s*\n+", "\n\n", t)
    return t.strip()


def slugify(title: str, fallback: str) -> str:
    if not title:
        return fallback
    s = re.sub(r"[^\w一-鿿]+", "-", title).strip("-").lower()
    return s[:60] or fallback


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--slug", default=None,
                    help="lowercase-hyphenated; derived from the title if omitted")
    ap.add_argument("--min-chars", type=int, default=500,
                    help="treat a shorter body as a failed fetch (default 500)")
    a = ap.parse_args()

    wxid = (re.search(r"/s/([A-Za-z0-9_-]+)", a.url) or [None, "unknown"])[1][:8]
    os.makedirs(a.outdir, exist_ok=True)

    tmp_html = os.path.join(a.outdir, f"_tmp_{wxid}.html")
    fetch(a.url, tmp_html)

    # errors="ignore" on parse: pages can carry stray invalid byte sequences.
    # The archive keeps the bytes as-is; only parsing is lenient.
    h = io.open(tmp_html, encoding="utf-8", errors="ignore").read()
    meta = extract_meta(h)
    body = extract_body(h)
    text = html_to_text(body)
    # data-src, not src - WeChat lazy-loads images.
    imgs = re.findall(r'data-src="(https?://mmbiz[^"]+)"', body)

    date = (meta["published"] or datetime.date.today().isoformat())[:10]
    slug = a.slug or slugify(meta["title"], wxid)
    stem = os.path.join(a.outdir, f"{date}_{slug}_{wxid}")

    os.replace(tmp_html, stem + ".html")

    header = (
        f"# {meta['title']}\n\n"
        f"- account: {meta['account'] or '?'}\n"
        f"- author: {meta['author'] or '?'}\n"
        f"- published: {meta['published'] or '?'}\n"
        f"- url: {a.url}\n"
        f"- fetched: curl + mobile UA, js_content extraction, "
        f"{datetime.date.today().isoformat()}\n"
        f"- body chars: {len(text)}\n"
        f"- images: {len(imgs)}\n\n---\n\n"
    )
    # Always write CJK to a UTF-8 file; never print it. On Windows the console
    # is GBK and print() of Chinese raises UnicodeEncodeError, killing the run.
    io.open(stem + ".md", "w", encoding="utf-8").write(header + text + "\n")
    io.open(stem + ".imgs", "w", encoding="utf-8").write("\n".join(imgs))

    # stdout stays ASCII-only - safe on any console codepage.
    print(f"html  = {stem}.html")
    print(f"md    = {stem}.md")
    print(f"imgs  = {stem}.imgs  ({len(imgs)} urls)")
    print(f"chars = {len(text)}")

    if len(text) < a.min_chars:
        print(f"FAIL: body too short (<{a.min_chars}) - likely blocked, refetch "
              f"or use Option A-D", file=sys.stderr)
        sys.exit(3)
    print("OK")


if __name__ == "__main__":
    main()
