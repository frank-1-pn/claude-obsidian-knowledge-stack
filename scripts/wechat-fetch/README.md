# `wechat_fetch.py` — direct WeChat article fetch (Option 0)

A runnable fetcher for `mp.weixin.qq.com` articles: one `curl` with a mobile
User-Agent plus a regex extraction pass. No API key, no third party, no
headless browser.

This is **Option 0** in [`../../setup/05-wechat-mcp.md`](../../setup/05-wechat-mcp.md):
try it first because it costs ~2 seconds, and fall through to Options A–D when
it reports the anti-bot wall.

## Usage

```bash
python wechat_fetch.py "https://mp.weixin.qq.com/s/XXXXXXXX" \
  --outdir ./out --slug some-english-slug
```

Three files, one stem:

| File | Purpose |
| --- | --- |
| `<date>_<slug>_<wxid>.html` | raw HTML archive — **never modify it** |
| `<date>_<slug>_<wxid>.md` | extracted body with a metadata header |
| `<date>_<slug>_<wxid>.imgs` | image URLs referenced in the body, one per line |

**Read the exit code — don't just check that files exist:**

| Code | Meaning | What to do |
| --- | --- | --- |
| `0` | fetched | continue, but run the three checks below |
| `2` | fetch failed (network / HTTP / response < 10 KB) | retry; if it keeps failing, switch method |
| `3` | **body shorter than `--min-chars`** → anti-bot wall | **write nothing from this.** Refetch, or use Option A–D |

## Why it works at all

WeChat articles are **server-rendered static HTML** — the body ships in the
page, no JS execution required. So you need neither Playwright nor a headless
browser; a headless browser is only slower and easier to fingerprint.

Two details carry the whole thing:

- **A mobile UA.** Desktop UAs are much more likely to receive a degraded or
  stub page.
- **The body lives in `id="js_content"`**, and the metadata lives in inline JS
  vars (`msg_title`, `author`, `nickname`, `ct`) near the top of the page.

A healthy article is **2–4 MB of HTML** (mostly inline styles and base64
thumbnails). Under 100 KB means you did not get the article.

## Where it fails

**Network-dependent.** From residential connections the direct fetch generally
succeeds; from datacenter / cloud IPs it usually gets the
`环境异常 / 完成验证后即可继续访问` CAPTCHA stub. That is exactly what exit
code `3` reports — it is a routing signal, not a bug.

Verified working 2026-07-30 from a residential connection on two articles
(1,826 and 4,927 body chars, metadata fully parsed). Both the success path and
the `--min-chars` failure path were exercised.

## The three checks before you trust the output

Fetching is the easy half. These three are what keep bad content out, and each
one exists because it was learned the hard way.

### 1. Length (automated)

A body under ~500 chars is almost never a genuinely short article — it is the
wall, or a broken extraction. The script enforces this via `--min-chars` and
exit code `3`.

This one matters most because **a truncated body produces output that looks
complete but isn't**, and that class of error is very hard to catch later.

### 2. Structure (eyeball it)

Open the `.md` and confirm:

- title / account / author / published are **not** `?`
- the body **ends on a sentence**, not mid-clause
- the body **doesn't start with navigation or promo text** (if it does, the
  container match drifted)

### 3. Facts (mandatory when the article describes external things)

**Numbers in WeChat articles are routinely stale or miscopied.** Whenever the
article makes a checkable claim, check it against a primary source.

Real cases from using this pipeline:

- A GitHub roundup where **all four** projects' star counts disagreed with the
  API — every one of them undercounted.
- An article about a protocol release that **omitted three changes more
  consequential than the ones it covered**, and rendered a spec `SHOULD` as
  "mandatory".
- An article quoting a file as "only five lines" — the file had since been
  refactored and now holds a single line.

How to check, by claim type:

| Claim is about | Check with |
| --- | --- |
| a GitHub repo | `gh api repos/<owner>/<repo>` for stars / language / license / created & pushed dates; `gh api repos/<o>/<r>/license` for the license specifically; `git/trees` for structure |
| a spec or release | pull the official changelog and compare item by item — don't trust a second-hand summary's categories |
| "the file is only N lines" | `gh api .../contents/<path>` and count it yourself |

**Write the deltas into your note**, labelled *article's figure vs. measured*.
For second-hand material this is the single largest thing you add.

## Windows / encoding traps

These will crash a naive script:

1. **Never `print()` CJK.** The Windows console is GBK; printing Chinese raises
   `UnicodeEncodeError: 'gbk' codec can't encode character ...` and kills the
   run. Write CJK to a UTF-8 file and keep stdout ASCII-only.
2. **Always pass `encoding="utf-8"` when reading.** Bare `open(p)` uses the
   local codepage → `UnicodeDecodeError`. Same for
   `json.load(open(p))` → use `json.load(io.open(p, encoding="utf-8"))`.
3. **Parse with `errors="ignore"`.** Pages can carry stray invalid bytes. Keep
   the archive byte-exact; be lenient only while parsing.
4. **Watch filename length.** Long CJK names plus deep directories hit the
   Windows path limit; the symptom is `cp: File name too long`. Copy artefacts
   with Python's `shutil.copyfile` rather than shell `cp`, or stage them under
   a short ASCII name first.

## Images

Extracted with `data-src` (not `src` — WeChat lazy-loads).

WeChat images are **referer-protected**: pasting `mmbiz.qpic.cn` URLs into
Markdown renders nothing in Obsidian. Per vault rule §7, download only the
images your note actually references into `_attachments/<slug>/`; fully
localizing a 30-image article bloats the repo for no benefit.

## Archive discipline

**Archive before you write.** Reversing the order is how you end up with a
finished note whose source material is gone.

- First action on new material: store the `.html` and extracted `.md` **as a
  pair** under `vault/.raw/wechat/`.
- Naming: `YYYY-MM-DD_<slug>_<wxid>.html` + matching `.md`, where `<wxid>` is
  the first 8 chars after `/s/` in the URL.
- **Archived files are never modified.** The original can 404 or be silently
  edited by its author; the archive is the only ground truth.
