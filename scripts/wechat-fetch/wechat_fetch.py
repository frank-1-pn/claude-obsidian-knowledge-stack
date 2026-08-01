#!/usr/bin/env python3
"""
wechat_fetch.py - fetch one WeChat (mp.weixin.qq.com) article and extract it
to structured Markdown.

This is "Option 0" of setup/05-wechat-mcp.md: a direct fetch with a mobile
User-Agent. It costs ~2 seconds, needs no API key and no third party. It works
from residential networks; from datacenter IPs it usually hits the anti-bot
wall, in which case this script exits 4 and you fall through to Options A-D.

Designed **for agents**. Three things are deliberate because of that:
  1. Exit codes are a stable, append-only contract (see EXIT CODES), so callers
     can hardcode branches on them
  2. --json emits a machine-readable envelope, so nothing has to parse prose
  3. Failures are differentiated: hit-a-wall / got-nothing / got-something-but-
     maybe-mis-extracted all call for different handling

Usage:
    python wechat_fetch.py <url> [options]

    --outdir DIR      output directory, default cwd
    --slug SLUG       lowercase-hyphen ASCII; derived from the title if omitted,
                      falls back to the wxid when the title yields nothing
    --min-chars N     body shorter than this counts as failure, default 500
    --timeout SEC     per-attempt curl timeout, default 60
    --retries N       retries on fetch failure, exponential backoff, default 2
    --force           allow overwriting an existing archive (refused by default,
                      so archives stay immutable)
    --json            emit a JSON result envelope (human output suppressed)

Produces three files sharing one stem:
    <date>_<slug>_<wxid>.html   raw HTML archive (never modify it)
    <date>_<slug>_<wxid>.md     extracted body + metadata header
    <date>_<slug>_<wxid>.imgs   image URLs referenced in the body, one per line

EXIT CODES - contract: **a published code never changes meaning and is never
removed**; new codes are only ever appended.
    0  OK              success; still run the fact checks in README section 4
    2  ERR_FETCH       fetch failed: network / HTTP / response too small. Retryable
    3  ERR_TOO_SHORT   page fetched, but body is under --min-chars. Mis-extraction
                       or a wall - inspect the HTML before trusting anything
    4  ERR_BLOCKED     **anti-bot wall positively identified** (CAPTCHA
                       interstitial). Retrying will not help - switch network or
                       channel
    5  ERR_NO_CONTENT  no js_content container at all (not an article URL?)
    6  ERR_EXISTS      archive of the same name exists and --force was not passed

Design notes and the three pre-delivery checks live in README.md next to this file.
"""

import argparse
import datetime
import html as html_mod
import io
import json
import os
import re
import subprocess
import sys
import time

OK, ERR_FETCH, ERR_TOO_SHORT, ERR_BLOCKED, ERR_NO_CONTENT, ERR_EXISTS = 0, 2, 3, 4, 5, 6

# A mobile UA is the load-bearing detail: desktop UAs are far more likely to
# get a degraded/stub page.
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)

# Signatures of the anti-bot interstitial ("abnormal environment" / "complete
# the verification"). Any hit means blocked - more precise than "the body is
# short", and it calls for different handling.
BLOCK_MARKERS = ("环境异常", "完成验证",
                 "去验证", "当前环境异常")


def fetch(url, out_html, timeout=60, retries=2):
    """curl rather than requests: identical to reproducing it by hand, one less
    dependency. Exponential backoff between attempts."""
    for attempt in range(retries + 1):
        subprocess.run(
            ["curl", "-s", "-L", "--max-time", str(timeout), "-A", MOBILE_UA, url, "-o", out_html]
        )
        if os.path.exists(out_html) and os.path.getsize(out_html) >= 10_000:
            return True
        if attempt < retries:
            time.sleep(2 ** attempt)  # 1s, 2s, 4s...
    return False


def grab(pattern, text, default=None):
    m = re.search(pattern, text)
    return m.group(1).strip() if m else default


def extract_meta(h):
    """Metadata lives in a cluster of inline JS vars near the top of the page;
    og: tags back it up."""
    ct = grab(r'var ct\s*=\s*"(\d+)"', h)
    return {
        "title": (grab(r"var msg_title\s*=\s*['\"](.*?)['\"]\s*\.html", h)
                  or grab(r'<meta property="og:title" content="(.*?)"', h)),
        "author": grab(r"var author\s*=\s*['\"](.*?)['\"]", h),
        "account": (grab(r"var nickname\s*=\s*['\"](.*?)['\"]", h)
                    or grab(r'var user_name\s*=\s*"(.*?)"', h)),
        "published": (datetime.datetime.fromtimestamp(int(ct)).strftime("%Y-%m-%d %H:%M")
                      if ct else None),
        "ct": ct,
    }


def extract_body(h):
    """
    Take the HTML inside the js_content container.
    Returns (body, used_fallback). The closing anchor has several candidates
    because WeChat's template changes; matching the first </div> truncates
    mid-article, since the body is wall-to-wall nested div/section.
    """
    m = re.search(
        r'id="js_content"[^>]*>(.*?)</div>\s*'
        r'(?:<script|<div id="js_tags|<div class="rich_media_tool)',
        h, re.S,
    )
    if m:
        return m.group(1), False
    # Fallback: grab a large slice from js_content onward. Better to include a
    # little trailing chrome than to cut half the article.
    # Reaching here means the template moved, so the output is lower-confidence
    # and the caller must be told.
    m = re.search(r'id="js_content"[^>]*>(.*)', h, re.S)
    if m:
        return m.group(1)[:600_000], True
    return "", False


def html_to_text(body):
    """Order matters; get it wrong and lines run together."""
    t = re.sub(r"<br\s*/?>", "\n", body)
    t = re.sub(r"</p>|</section>|</h\d>|</li>|</blockquote>", "\n", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html_mod.unescape(t)
    t = re.sub(r"[ \t\xa0]+", " ", t)        # \xa0 is &nbsp; after unescaping
    t = re.sub(r"\n\s*\n\s*\n+", "\n\n", t)
    return t.strip()


def slugify(title, fallback):
    """Emit an ASCII-safe slug; an all-CJK title yields nothing, so use the wxid."""
    if not title:
        return fallback
    s = re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-").lower()
    s = re.sub(r"-{2,}", "-", s)
    return s[:60] if len(s) >= 3 else fallback


def structure_warnings(meta, text, used_fallback):
    """
    Automate the machine-checkable half of README section 4's structure check.
    Returns **pure-ASCII machine codes** - see the "warning codes" table there.
    Deliberately not localized: stdout must be safe under any console codepage.
    """
    w = []
    for k in ("title", "account", "author", "published"):
        if not meta.get(k):
            w.append("missing_meta:" + k)
    if used_fallback:
        w.append("fallback_extraction")
    # A body should end on sentence-final punctuation; CJK and ASCII both count
    if text and not re.search(r"[。．！？!?…”』」）)\]】]\s*$", text):
        w.append("abrupt_ending")
    return w


def _dumps(payload):
    # ensure_ascii=True: CJK becomes \uXXXX. Still valid JSON and machine-readable,
    # and it cannot be mangled by a GBK console - the exact trap this tool's
    # README warns about.
    return json.dumps(payload, ensure_ascii=True, indent=2)


def emit(as_json, payload, human_lines):
    if as_json:
        print(_dumps(payload))
    else:
        for l in human_lines:
            print(l)


def die(as_json, code, name, msg, extra=None):
    payload = {"ok": False, "exit_code": code, "error": name, "message": msg}
    if extra:
        payload.update(extra)
    if as_json:
        print(_dumps(payload))
    else:
        print(f"FAIL[{code}] {name}: {msg}", file=sys.stderr)
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("url")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--slug", default=None)
    ap.add_argument("--min-chars", type=int, default=500)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--json", dest="as_json", action="store_true")
    a = ap.parse_args()

    wxid = (re.search(r"/s/([A-Za-z0-9_-]+)", a.url) or [None, "unknown"])[1][:8]
    os.makedirs(a.outdir, exist_ok=True)
    tmp_html = os.path.join(a.outdir, f"_tmp_{wxid}.html")

    try:
        if not fetch(a.url, tmp_html, a.timeout, a.retries):
            die(a.as_json, ERR_FETCH, "ERR_FETCH",
                f"curl failed or response < 10KB after {a.retries + 1} attempt(s)")

        h = io.open(tmp_html, encoding="utf-8", errors="ignore").read()

        # Check for the wall first: more precise than "short body", and the
        # remedy differs (retrying is useless; change network or channel)
        if any(mk in h for mk in BLOCK_MARKERS) and 'id="js_content"' not in h:
            die(a.as_json, ERR_BLOCKED, "ERR_BLOCKED",
                "anti-bot wall detected (CAPTCHA interstitial). Retrying will NOT help - "
                "switch network (residential IP usually works) or use another channel.")

        if 'id="js_content"' not in h:
            die(a.as_json, ERR_NO_CONTENT, "ERR_NO_CONTENT",
                "no js_content container - is this actually an article URL?")

        meta = extract_meta(h)
        body, used_fallback = extract_body(h)
        text = html_to_text(body)
        imgs = re.findall(r'data-src="(https?://mmbiz[^"]+)"', body)  # data-src: WeChat lazy-loads

        date = (meta["published"] or datetime.date.today().isoformat())[:10]
        slug = a.slug or slugify(meta["title"], wxid)
        stem = os.path.join(a.outdir, f"{date}_{slug}_{wxid}").replace("\\", "/")

        if os.path.exists(stem + ".html") and not a.force:
            die(a.as_json, ERR_EXISTS, "ERR_EXISTS",
                f"archive already exists: {stem}.html (use --force to overwrite)")

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
            f"- body images: {len(imgs)}\n\n---\n\n"
        )
        # CJK always goes to a UTF-8 file, never to print() - the Windows console
        # is GBK and printing CJK kills the run
        io.open(stem + ".md", "w", encoding="utf-8").write(header + text + "\n")
        io.open(stem + ".imgs", "w", encoding="utf-8").write("\n".join(imgs))

        warnings = structure_warnings(meta, text, used_fallback)
        too_short = len(text) < a.min_chars
        code = ERR_TOO_SHORT if too_short else OK

        payload = {
            "ok": not too_short,
            "exit_code": code,
            "html": stem + ".html",
            "md": stem + ".md",
            "imgs_file": stem + ".imgs",
            "chars": len(text),
            "images": len(imgs),
            "meta": meta,
            "warnings": warnings,
            "used_fallback_extraction": used_fallback,
        }
        # stdout stays ASCII-only, safe under any console codepage
        human = [
            f"html  = {stem}.html",
            f"md    = {stem}.md",
            f"imgs  = {stem}.imgs  ({len(imgs)} urls)",
            f"chars = {len(text)}",
        ] + [f"WARN  {w}" for w in warnings]
        emit(a.as_json, payload, human)

        if too_short:
            if not a.as_json:
                print(f"FAIL[{ERR_TOO_SHORT}] ERR_TOO_SHORT: body < {a.min_chars} chars - "
                      f"likely blocked or mis-extracted. Do NOT write anything from this.",
                      file=sys.stderr)
            sys.exit(ERR_TOO_SHORT)
        if not a.as_json:
            print("OK")

    finally:
        # No failure path leaves a temp file behind
        if os.path.exists(tmp_html):
            try:
                os.remove(tmp_html)
            except OSError:
                pass


if __name__ == "__main__":
    main()
