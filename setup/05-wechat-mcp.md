# 05 — WeChat article ingestion (cross-platform)

WeChat (微信) articles live on `mp.weixin.qq.com` behind a referer + anti-bot
wall: the page renders in a real browser, but a vanilla `curl` / `WebFetch`
gets a stub ("环境异常 / 完成验证后即可继续访问") with no content, and
`r.jina.ai` hits the same CAPTCHA. You need a fetcher that defeats that wall.

**There are several ways to do it — pick by your OS and how much you want to
self-host.** The original local tool (`wechatDownload`) is **Windows-only**;
the methods below cover macOS / Linux too.

## Pick your method

| Method | OS | Install | API key | Privacy | Best for |
| --- | --- | --- | --- | --- | --- |
| **0. Direct fetch** (mobile UA + regex) | ✅ any | none (curl + Python) | none | fully local, nothing leaves your machine | **try first** — costs ~2s; works from residential IPs |
| **A. Hosted MCP** (`changfengbox.top`) | ✅ any | none | none | article URL sent to a 3rd-party community server | fastest start, macOS/Linux, "just works" |
| **B. wechatDownload local MCP** | 🪟 Windows only | desktop app + WeChat PC client | none | fully local | Windows users who want everything offline |
| **C. Exa crawling** | ✅ any | none (cloud API) | Exa key | URL sent to Exa | macOS/Linux, already using Exa |
| **D. Camoufox script** | ✅ any | Python + Camoufox | none | fully local | self-hosted, strongest anti-bot, no 3rd party |

> On **macOS / Linux**, skip the old "download wechatDownload" step entirely —
> it's a Windows desktop app and won't run natively. Use **A** (zero install)
> or **D** (local + private). **B** stays documented for Windows users.

Whichever method delivers the article body, the **vault note-generation flow
at the bottom of this page is identical** — only the fetch differs.

---

## Option 0 — Direct fetch with a mobile UA (try this first)

> **This corrects earlier guidance in this file.** A previous revision said
> never to fall back to raw `curl`. That is **network-dependent, not
> universal**: from a **residential** connection a direct fetch with a
> **mobile** User-Agent generally returns the full article; from
> **datacenter / cloud IPs** it usually gets the
> `环境异常 / 完成验证后即可继续访问` stub. Verified working 2026-07-30 from a
> residential connection on two articles (1,826 and 4,927 body chars, metadata
> fully parsed).
>
> Because it costs ~2 seconds and leaks nothing to a third party, **try it
> first and let it tell you when to escalate** to A–D.

```bash
python scripts/wechat-fetch/wechat_fetch.py \
  "https://mp.weixin.qq.com/s/XXXXXXXX" --outdir vault/.raw/wechat --slug some-slug
```

Add `--json` when an agent is the caller: it returns a machine-readable envelope
(paths, char count, parsed metadata, warning codes) instead of prose.

Exit code `0` = usable. **`4` = the wall was positively identified, switch to
A–D** — retrying is pointless. **`3` = the body came out too short**, which can
also be a drifted container match, so open the HTML once before escalating. The
codes are an append-only contract, safe to branch on; the full table, all flags,
the three post-fetch checks and the Windows encoding traps are in
[`scripts/wechat-fetch/README.md`](../scripts/wechat-fetch/README.md).

Why it works without a browser: WeChat articles are **server-rendered static
HTML** — the body ships in the page inside `id="js_content"`, and the metadata
sits in inline JS vars (`msg_title` / `author` / `nickname` / `ct`). No JS
execution needed, so a headless browser buys you nothing but latency and a
bigger fingerprint. A healthy page is **2–4 MB**; under 100 KB means you didn't
get the article.

---

## Option A — Hosted MCP (recommended; any OS, zero install)

A community-hosted MCP renders the article server-side and hands back a
download link. No desktop app, no WeChat client, no key — works the same on
macOS, Linux, and Windows.

- **Endpoint:** `https://changfengbox.top/api/mcp` (streamable HTTP MCP)
- **Tools:** `wechat` (one article) and `wechat_collection` (an
  `appmsgalbum` 合集)

### Register in Claude Code

```bash
claude mcp add --transport http wechat-hosted https://changfengbox.top/api/mcp
```

Restart Claude Code; `mcp__wechat-hosted__*` tools surface on demand.

### Or skip MCP entirely — one `curl` (macOS has curl built in)

```bash
URL="https://mp.weixin.qq.com/s/XXXXXXXX"
curl -s https://changfengbox.top/api/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"id\":1,\"params\":{\"name\":\"wechat\",\"arguments\":{\"url\":\"$URL\",\"config\":{\"MD\":true}}}}"
```

The response contains a download URL like
`https://changfengbox.top/static/temp/download/wechat/<title>.md`. `curl` that
URL to get the Markdown, then follow the vault flow below. `config` accepts
`HTML` / `MD` / `PDF` / `WORD` / `TXT` / `MHTML` / `文件开头添加日期` (any
subset, `true`).

### Caveats (read before relying on it)

- It's a **third-party community service**: the article URL goes to their
  server, and it can rate-limit, change, or disappear. WeChat public articles
  are public content, so the privacy exposure is low — but don't pipe anything
  sensitive through it.
- For a fully self-hosted setup, use **B** (Windows) or **D** (any OS).
- Ranking/列表-style articles whose body is **images** still come back as
  image links — you'll OCR/读图 them downstream, same as any method.

---

## Option B — wechatDownload local MCP (Windows only, fully local)

The original method: a Windows desktop app that holds a live WeChat session
and serves a local MCP on `http://127.0.0.1:4545/mcp`. **Requires Windows +
the WeChat PC client** — it will not run on macOS/Linux.

### Install

1. Download from <https://github.com/qiye45/wechatDownload> and run the
   installer; the app sits in the system tray.
2. **Set the download output directory** in the app's settings UI. **Remember
   this path** — note generation reads from it.
3. The first download opens the WeChat in-app browser to capture session
   cookies / 密钥. Do it once; later downloads are silent.

The MCP is only up while the app is running. Quit the app = MCP unavailable.

> **Key renewal:** the captured 密钥 can expire after enough time/downloads —
> symptom is downloads suddenly failing with no config change. Fix: reopen
> *any* article inside the WeChat client (just view it) to silently refresh
> the session, then retry the download. To find where output landed
> afterward, scan the app's `log<YYYYMMDD>.txt` (dated by day) for the
> written path rather than guessing.

### Verify + register

```bash
curl -s http://127.0.0.1:4545/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json,text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"0.1"}}}' \
  --max-time 5
```

A 200 with an `Mcp-Session-Id` header = alive; "connection refused" = app not
running. Register it:

```bash
claude mcp add --transport http wechatDownload http://127.0.0.1:4545/mcp
# or hand-edit ~/.claude.json (see config/mcp-config.example.json)
```

### Its tools

| Tool | Args | Purpose |
| --- | --- | --- |
| `single_article_download` | `url: string` | Download one article (most common) |
| `get_public_account_id` | (none) | Resolve a public account by name |
| `batch_download_articles` | (none) | Download all articles for the account currently selected in the app |
| `export_article_data` | (none) | Export downloaded article metadata to CSV/JSON |

Downloaded files land in `<output dir>/<account>/<title>.{html,md,docx,pdf}`
plus an `图片/` folder.

---

## Option C — Exa crawling (any OS, API key)

If you already use Exa, its crawler defeats the WeChat wall via the cloud:

```bash
mcporter call 'exa.crawling_exa(urls: ["https://mp.weixin.qq.com/s/XXXX"], maxCharacters: 16000)'
```

Needs an Exa API key configured in your MCP client. Cross-platform; the URL is
sent to Exa.

## Option D — Camoufox script (any OS, self-hosted, strongest anti-bot)

A stealth-Firefox (Camoufox) Python scraper runs entirely on your machine — no
third party, best against hardened anti-bot pages:

```bash
# one-time: pip install camoufox + browsers; then
python3 wechat-article-for-ai/main.py "https://mp.weixin.qq.com/s/XXXX"
```

Heavier to set up (Python + a headless browser), but fully local and works on
macOS/Linux/Windows. In the operator's own `agent-reach` install, this script
lives under `~/.agent-reach/tools/` (agent-reach's local tools folder) rather
than a standalone repo clone — adjust the path above to wherever you placed
it. This is the **cross-platform fallback** `agent-reach` uses for WeChat
when Option B (wechatDownload, Windows-only) isn't available (see
`09-agent-reach.md`) — its primary channel on Windows is still Option B.

---

## After fetch: vault note-generation flow (same for every method)

Once any method has given you the article Markdown (and, ideally, an archived
copy):

```
1. Archive raw first: save the .md (and .html if you have it) to
   vault/.raw/wechat/YYYY-MM-DD_<slug>_<wxid>.{md,html}   (vault rule §8)
2. Read the .md.
3. Localize images actually referenced in your note: copy them to
   vault/_attachments/<slug>/ and rewrite mmbiz.qpic.cn links to
   ![[<slug>/<image>.jpg]]                                  (vault rule §7)
4. Write the source note to vault/wiki/sources/<domain>/<title>.md
   (abstract callout §6, no same-quote YAML nesting §7.5, Chinese diagrams §9).
5. Update vault/wiki/{index.md, sources/_index.md, meta/notes-graph.md} and
   append a vault/wiki/log.md entry                          (vault rule §6.5)
```

See `vault/note-generation-rules.md` for the full rule set.

---

## Failure modes that bit us

| Symptom | Cause | Fix |
| --- | --- | --- |
| `curl`/`WebFetch` returns "环境异常 / 完成验证" stub | Hit the referer/CAPTCHA wall — **common from datacenter IPs, rarer from residential** | Retry from a residential network, or use A–D. Option 0 reports this as exit code `4` |
| Option 0 succeeded but the note came out thin | Body was truncated by a drifted container match, and nobody checked | Run the **three checks** (length / structure / facts) in `scripts/wechat-fetch/README.md` — never publish an unverified body |
| A figure in the article disagrees with reality | WeChat articles routinely carry stale or miscopied numbers | Verify against a primary source (`gh api` for repos, official changelog for specs) and record *article's figure vs. measured* |
| Python crashes with `'gbk' codec can't encode character` | `print()`-ing CJK on a Windows console | Write CJK to a UTF-8 file; keep stdout ASCII-only (see Option 0's README) |
| Hosted MCP returns nothing / times out | Community server down or rate-limited | Retry later, or switch to D (Camoufox) / B (Windows) |
| Local MCP "connection refused" (Option B) | Desktop app not running | Start it from the tray; it's Windows-only |
| Article Markdown < 500 chars | Anti-scraping wall or cookie expired | Wait + retry; Option B may need a cookie refresh |
| List/ranking article body is empty text | The 榜单/list is rendered as **images** | Expected — download the images and 读图/OCR them downstream |
| Images broken in Obsidian preview | Images weren't localized to `_attachments/` | Per vault §7, copy referenced images locally; don't keep `mmbiz.qpic.cn` URLs |

## Don't do these

- **Don't tell macOS/Linux users to install wechatDownload.** It's a Windows
  desktop app — point them to Option A or D instead.
- **Don't assume raw `curl` can't work — but don't assume it will either.**
  With a **mobile** UA it usually succeeds from residential networks and
  usually fails from datacenter IPs. Run Option 0 first (it's ~2s) and treat
  its exit code `4` as the signal to escalate to A–D. What you must not do is
  retry a bare **desktop**-UA `curl` over and over expecting a different
  answer.
- **Don't publish a body you haven't length-checked.** A truncated article
  produces a note that reads as complete but isn't — the hardest kind of error
  to notice later. Under ~500 chars, assume failure.
- **Don't repeat an article's numbers without checking them.** Star counts,
  version numbers and "only N lines" claims go stale fast; verify against a
  primary source and note the delta.
- **Don't hardcode Option B's output path** in scripts — resolve at runtime
  from the latest `log<YYYYMMDD>.txt`.
- **Don't fully localize every image** in 30-image articles — per vault §7,
  only images referenced in the synthesized note need local copies.
- **Don't pipe sensitive content through the hosted MCP** — it's a 3rd-party
  server; use B or D for anything private.

## Done when

- A test article ingest (via whichever method fits your OS) produces a
  well-formed source note in `wiki/sources/`, an archive pair in
  `.raw/wechat/`, locally-resolved images in `_attachments/<slug>/`, and a log
  entry in `wiki/log.md`.

> Beyond WeChat: `09-agent-reach.md` adds Bilibili, YouTube, RSS, podcasts,
> V2EX and the socials. Its own WeChat channel is **Option B** — the
> wechatDownload local MCP at `http://localhost:4545` — on Windows, falling
> back to **Option D (Camoufox)** for cross-platform use without the
> Windows app.

Move on to `06-image-generation.md` to add diagram generation, or
`07-memory-plugins.md` to wire cross-session memory.
