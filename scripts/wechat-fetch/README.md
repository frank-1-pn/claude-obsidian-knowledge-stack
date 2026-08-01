# `wechat_fetch.py` — direct WeChat article fetch (Option 0)

A runnable fetcher for `mp.weixin.qq.com` articles: one `curl` with a mobile
User-Agent plus a regex extraction pass. No API key, no third party, no
headless browser.

This is **Option 0** in [`../../setup/05-wechat-mcp.md`](../../setup/05-wechat-mcp.md):
try it first because it costs ~2 seconds, and fall through to Options A–D when
it reports the anti-bot wall.

**The script is written for agents to call**, so three things are deliberate:

- **Exit codes are a stable, append-only contract** — you can hardcode branches
- **`--json` emits a machine-readable envelope** — nothing has to parse prose
- **Failures are differentiated** — hit-a-wall, got-nothing, and
  got-something-but-maybe-mis-extracted need different handling

---

## 0. The thirty-second version

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

When an agent calls it, add `--json`:

```bash
python wechat_fetch.py "<url>" --outdir ./out --json
```

```json
{
  "ok": true,
  "exit_code": 0,
  "html": "./out/2026-07-29_some-slug_0kEtbf3b.html",
  "md":   "./out/2026-07-29_some-slug_0kEtbf3b.md",
  "imgs_file": "./out/2026-07-29_some-slug_0kEtbf3b.imgs",
  "chars": 1826,
  "images": 8,
  "meta": { "title": "...", "author": "...", "account": "...", "published": "2026-07-29 16:30" },
  "warnings": ["abrupt_ending"],
  "used_fallback_extraction": false
}
```

> CJK inside that JSON is `\uXXXX`-escaped, and **that is on purpose**: still
> valid JSON, still machine-readable, and immune to a GBK console mangling it
> (see §5.1).

---

## 1. Exit codes (the contract)

**A published code never changes meaning and is never removed**; new codes are
only ever appended. Branch on them freely.

| Code | Name | Meaning | What to do |
| --- | --- | --- | --- |
| `0` | `OK` | fetched | continue — but still run the **fact check** in §4.3 |
| `2` | `ERR_FETCH` | network / HTTP failure, or response < 10 KB | **retryable** (the script already backs off and retries) |
| `3` | `ERR_TOO_SHORT` | page fetched, but body is under `--min-chars` | **write nothing from this.** Mis-extraction or a wall — open the HTML and look |
| `4` | `ERR_BLOCKED` | **anti-bot wall positively identified** (CAPTCHA page) | **retrying will not help** — change network (residential usually works) or use a channel from §6 |
| `5` | `ERR_NO_CONTENT` | no `js_content` container in the page | probably not an article URL; check the link |
| `6` | `ERR_EXISTS` | an archive of that name exists and `--force` was not passed | protects archive immutability; confirm before overwriting |

> **The 3-vs-4 split is the point.** `4` means the script *confirmed* the wall
> (CAPTCHA signatures are present), so retrying just burns time. `3` only means
> the body came out short — which can equally be a template change that broke
> extraction, and that is worth one look at the `.html` before you give up.

---

## 2. All flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--outdir DIR` | `.` | output directory |
| `--slug SLUG` | derived from title | lowercase-hyphen ASCII. An all-CJK title yields nothing usable, so it **falls back to the wxid** |
| `--min-chars N` | `500` | body below this counts as failure |
| `--timeout SEC` | `60` | per-attempt `curl` timeout |
| `--retries N` | `2` | retries on fetch failure, **exponential backoff** (1s / 2s / 4s) |
| `--force` | off | allow overwriting an existing archive. **Refused by default** — archives are meant to be immutable |
| `--json` | off | emit the machine-readable envelope |

---

## 3. Why it works at all

WeChat articles are **server-rendered static HTML** — the body ships in the
page, no JS execution required. So you need neither Playwright nor a headless
browser; a headless browser is only slower and easier to fingerprint.

Two details carry the whole thing:

- **A mobile UA.** Desktop UAs are much more likely to receive a degraded or
  stub page.
- **The body lives in `id="js_content"`**, and the metadata lives in inline JS
  vars (`msg_title`, `author`, `nickname`, `ct`) near the top of the page.

One `curl` plus a handful of regexes is the whole solution. Fewest moving parts,
easiest to debug when it breaks.

A healthy article is **2–4 MB of HTML** (mostly inline styles and base64
thumbnails). Under 100 KB means you did not get the article; the script treats
10 KB as a hard failure line.

### 3.1 Extraction details that matter

| Field | Source | Note |
| --- | --- | --- |
| title | `var msg_title = '...'.html(` | falls back to `<meta property="og:title">` |
| author | `var author = '...'` | the bylined author, **not** the account name |
| account | `var nickname = '...'` | falls back to `var user_name`; **sometimes only yields an internal `gh_xxxxx` ID** |
| published | `var ct = "..."` | a **Unix timestamp** — convert it |

**The body container's closing anchor has several candidates** (`<script`,
`js_tags`, `rich_media_tool`). WeChat's template changes, and matching the first
`</div>` truncates mid-article, because the body is wall-to-wall nested
`div`/`section`. When no anchor matches, the script grabs a large slice instead
and sets **`used_fallback_extraction: true`** so the caller knows this result is
lower-confidence.

**The HTML→text order is load-bearing** — get it wrong and lines run together:
`<br>`→newline, then block-level closing tags→newline, then strip tags, then
`html.unescape()`, then collapse `[ \t\xa0]+`, then collapse blank lines.

> `\xa0` is the **non-breaking space** left behind when `&nbsp;` is unescaped.
> Handle it explicitly or every later whitespace test silently misfires.

**Images come from `data-src`, not `src`** — WeChat lazy-loads.

> ⚠️ **WeChat images are referer-protected.** Pasting `mmbiz.qpic.cn` URLs into
> Markdown renders nothing in Obsidian. Per vault rule §7, download only the
> images your note actually references into `_attachments/<slug>/`; fully
> localizing a 30-image article bloats the repo for no benefit.

---

## 4. The three checks before you trust the output

Fetching is the easy half. These three keep bad content out, and each exists
because it was learned the hard way. **Skip none of them.**

### 4.1 Length — automated

A body under ~500 chars is almost never a genuinely short article; it is the
wall, or a broken extraction. The script enforces this via `--min-chars` and
exit code `3`.

This one matters most because **a truncated body produces output that looks
complete but isn't**, and that class of error is very hard to catch later. It
has to be stopped at the source.

### 4.2 Structure — now **partly** automated

Everything machine-checkable is emitted as `warnings` (pure-ASCII machine codes):

| Warning code | Meaning | What to do |
| --- | --- | --- |
| `missing_meta:title` / `:account` / `:author` / `:published` | that field did not parse | one or two missing is tolerable (plenty of articles have no byline); **a missing title needs investigating** |
| `fallback_extraction` | no closing anchor matched, the fallback slice was used | **the template may have moved**; the body may carry trailing chrome — open it and look |
| `abrupt_ending` | body does not end on sentence-final punctuation | possibly truncated, possibly an article that just ends on a link — judge it |

**Still needs a human glance:** whether the body *starts* with navigation or
promo text. If it does, the container match drifted. This one does not automate
reliably.

### 4.3 Facts — mandatory when the article describes external things

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

---

## 5. Windows / encoding traps

These will crash a naive script. All have been hit for real — and **the first
one fired three separate times while building this tool.**

### 5.1 Never `print()` CJK

The Windows console is GBK; printing Chinese raises
`UnicodeEncodeError: 'gbk' codec can't encode character ...` and kills the run.
Even when it survives, the text arrives as `????`.

**Rule:** CJK goes to a UTF-8 file; stdout and stderr stay ASCII-only.

```python
io.open(path, "w", encoding="utf-8").write(chinese_text)   # OK
print(chinese_text)                                         # crashes
```

This script therefore does three things: `--json` uses `ensure_ascii=True` (CJK
becomes `\uXXXX`), `warnings` are ASCII machine codes, and **every error string
is pure ASCII down to using `-` instead of an em dash** (`—` mangles under GBK
too).

> The same trap applies **to the patch scripts you write**: feeding a shell
> heredoc some Python that contains CJK or `—` gets the content eaten before
> Python ever sees it. To edit a file, **write your script out as a UTF-8 file
> and then execute it** — don't inline it in a heredoc.

### 5.2 Always pass `encoding="utf-8"` when reading

Bare `open(p)` uses the local codepage → `UnicodeDecodeError`. Same for
`json.load(open(p))` → use `json.load(io.open(p, encoding="utf-8"))`.

### 5.3 Parse with `errors="ignore"`

Pages can carry stray invalid bytes. **Keep the archive byte-exact; be lenient
only while parsing.**

### 5.4 Watch filename length

Long CJK names plus deep directories hit the Windows path limit; the symptom is
`cp: File name too long`. Copy artefacts with Python's `shutil.copyfile` rather
than shell `cp`, or stage them under a short ASCII name first.

---

## 6. Fallback channels

When the direct fetch reports `ERR_BLOCKED`, in priority order:

1. **Change network.** Datacenter and cloud IPs are routinely stopped by the
   CAPTCHA wall; **residential connections generally get through.** Cheapest
   fix, try it first.
2. **A local fetcher exposing MCP** (a desktop WeChat-downloader app that runs
   an MCP server on the machine). Its output directory is configurable in the
   UI, so **don't hardcode a path you saw once** — read its `log<YYYYMMDD>.txt`
   to find where it is writing today.
3. **A community-hosted scraping MCP.** Zero install, cross-platform, but **the
   article URL passes through a third-party server** — not for sensitive material.
4. **Self-hosted RSS** (something like we-mp-rss). Good for subscriptions and as
   a backstop; overkill for grabbing one article.

### Where the direct fetch fails

**Network-dependent.** From residential connections it generally succeeds; from
datacenter / cloud IPs it usually gets the CAPTCHA stub, which is exactly what
exit code `4` reports — a routing signal, not a bug.

Verified working 2026-07-30 from a residential connection on two articles
(1,826 and 4,927 body chars, metadata fully parsed).

---

## 7. Archive discipline

**Archive before you write.** Reversing the order is how you end up with a
finished note whose source material is gone.

- First action on new material: store the `.html` and extracted `.md` **as a
  pair** under `vault/.raw/wechat/`.
- Naming: `YYYY-MM-DD_<slug>_<wxid>.html` + matching `.md`, where `<wxid>` is
  the first 8 chars after `/s/` in the URL.
- **Archived files are never modified.** The original can 404 or be silently
  edited by its author; the archive is the only ground truth. The script refuses
  to overwrite an existing archive (`ERR_EXISTS`) precisely to enforce this.
- Record the archive path in the finished note so the chain stays traceable.

---

## 8. Full checklist

```
1. python wechat_fetch.py <url> --outdir <archive dir> --json
2. Branch on the exit code:
     0 continue / 2 retry / 3 don't use it / 4 change network
     5 check the link / 6 confirm before overwriting
3. Read warnings: fallback_extraction or abrupt_ending -> open the .md and check
4. Confirm by eye that the body doesn't start with navigation or promo text
5. Fact-check every repo, version and number against a primary source
6. Write the note, label "article's figure vs. measured", record the archive path
```

---

## 9. In one sentence

> WeChat articles are static pages: **one `curl` with a mobile UA plus a few
> regexes** is enough — don't reach for a headless browser.
>
> What actually determines quality is not the fetch but the **three checks**:
> **length** (against truncation), **structure** (against mis-extraction), and
> **facts** (against repeating someone's error). The script now does most of the
> first two; the third is yours.
>
> And **archive before you write** — originals disappear, archives don't.

---

## Files here

| File | Notes |
| --- | --- |
| `README.md` | this document |
| `wechat_fetch.py` | the runnable fetcher. Verified paths: success (both `--json` and human output), `ERR_TOO_SHORT`, `ERR_NO_CONTENT`, `ERR_EXISTS`, temp-file cleanup, all-ASCII console output. `ERR_FETCH` and `ERR_BLOCKED` were code-reviewed but could not be triggered reproducibly on a residential connection |
