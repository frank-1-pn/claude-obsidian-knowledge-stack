# 09 — Multi-platform fetching via agent-reach (Bilibili, RSS, podcasts, social)

`05-wechat-mcp.md` covers WeChat articles. This page adds **everything else**:
one skill that gives Claude a routing table over ~17 platforms — web/code
search, Bilibili & YouTube subtitles, podcasts (with local transcription), RSS,
V2EX, and the socials (Twitter needs a user-supplied token; Reddit is
logged in via `rdt login`; Xiaohongshu is cookie-gated). Each fetched
source lands in `.raw/` per the vault's archive-first rule, ready to ingest.

Upstream: **Agent-Reach** (<https://github.com/Panniantong/Agent-Reach>).

## The model: one skill, a routing table, per-channel state

agent-reach is a **Claude Code skill** (a `SKILL.md` + `references/*.md` +
helper scripts). Claude reads the routing table, picks the channel for the
user's intent, and runs the matching CLI/MCP/curl command. Two files matter:

- The skill itself, discovered from `~/.claude/skills/agent-reach/`.
- A **machine-local state file**, `~/.agent-reach/local-state.md`, that records
  which channels are logged in, which need a cookie, and any local substitutes.
  This file lives **outside** the package so reinstalling the skill never wipes
  it. The skill's description tells Claude to read it first. A sanitized
  template is in `config/agent-reach-local-state.template.md`.

> Why a state file: the same skill behaves differently per machine (logged in
> here, cookie-gated there, GPU transcription available or not). Encoding that
> in one read-first file keeps Claude from blindly trying a channel that isn't
> wired up on this box.

## Install

agent-reach ships its CLIs as a Python package; install with `pipx` so each CLI
is on PATH in its own venv:

```bash
pipx install agent-reach        # or: pipx install git+https://github.com/Panniantong/Agent-Reach
```

Then make the skill visible to Claude Code: place (or symlink) the skill folder
under `~/.claude/skills/agent-reach/`. New Claude Code sessions auto-discover it.

External CLIs some channels lean on (install as needed):
- `yt-dlp` — YouTube/Bilibili subtitles + audio (`pipx install yt-dlp`)
- `bilibili-api-python` — Bilibili guest-API audio/download-URL resolution,
  the actual fix for the 412 gotcha below (`pip install bilibili-api-python`)
- `ffmpeg` — audio extraction for transcription
  (`winget install ffmpeg` on Windows — **not** macOS `brew`)
- `gh` — GitHub search/read (from `01-prereqs.md`, already authenticated)

## Channel status — what works out of the box vs needs a key/cookie

This mirrors the layout of `~/.agent-reach/local-state.md`. "Zero-config"
channels work immediately; the rest need a one-time credential.

| Channel | Out of the box? | Notes |
| --- | --- | --- |
| Exa web search | ✅ | general web search |
| Jina reader (`r.jina.ai/<url>`) | ✅ | any URL → clean markdown |
| GitHub (`gh`) | ✅ (after `gh auth login`) | repos / issues / PRs |
| YouTube (`yt-dlp`) | ⚠️ needs cookie + EJS solver | not zero-config — needs a cookie snapshot + `--remote-components ejs:github`; see "YouTube" section below |
| V2EX | ✅ | community threads |
| RSS / Atom | ✅ automated | daily scheduled task (`KnowledgeVault-RSSFetch` → `fetch_rss.py`), ~10 sources, incremental, zero-LLM, lands in `.raw/rss/` — see below |
| WeChat official accounts | ✅ cross-platform | see `05-wechat-mcp.md` — hosted MCP (any OS) / Camoufox (any OS) / Windows-only wechatDownload. agent-reach's own channel is the Windows-only wechatDownload local MCP, falling back to Camoufox on macOS/Linux |
| Bilibili | ✅ guest API, no login | `yt-dlp` 412s the playurl endpoint unconditionally (stale signing) — the fix is `bilibili-api-python`'s guest API, not cookies/login; see "Bilibili" section below. `bili-cli` demoted to metadata/search only |
| Podcasts (Xiaoyuzhou etc.) | ✅ local transcription | see below — uses local GPU whisper, not a cloud API |
| Twitter / X | ❌ needs user-supplied token | user provides `auth_token` + `ct0` (from a logged-in browser session) → `setx TWITTER_AUTH_TOKEN <value>` / `setx TWITTER_CT0 <value>` |
| Reddit | ✅ logged in | `rdt login` extracts cookies from a logged-in Chrome profile (close Chrome first); re-run if the cookie expires |
| Xiaohongshu (RED) | ❌ needs cookie | same as before — cookie-gated |

## Zero-config quick commands

```bash
# Web search (Exa via MCP)
mcporter call 'exa.web_search_exa(query: "your query", numResults: 5)'

# Read any web page as markdown
curl -s "https://r.jina.ai/https://example.com/article"

# GitHub repo search
gh search repos "your query" --sort stars --limit 10

# Bilibili guest-API audio URL (see "Bilibili" section below — not yt-dlp)
python config/bili_audio_url.py <BVID>
```

## Bilibili: the 412 gotcha (and the actual fix)

`yt-dlp`'s Bilibili extractor returns HTTP 412 on the playurl endpoint —
**unconditionally**, even from a domestic IP with a full Chrome cookie
export. This is not IP-based risk control and not a login problem; it's
stale `gaia`/`w_webid` request signing inside yt-dlp's Bilibili extractor.
`--cookies-from-browser chrome` does **not** fix it.

The path that actually works is the guest API — no login required:

```bash
pip install bilibili-api-python

# 1) resolve the best-bandwidth dash audio URL as a guest
python config/bili_audio_url.py <BVID>

# 2) download it (the CDN requires this exact Referer or it 403s)
curl -H "Referer: https://www.bilibili.com" -o audio.m4a "<baseUrl-from-step-1>"

# 3) transcribe locally
python ~/.claude/scripts/transcribe.py audio.m4a
```

Under the hood, `config/bili_audio_url.py` calls
`bilibili_api.video.Video(bvid=...).get_download_url(0)`, which returns a
`dash.audio[]` list even for an anonymous guest; pick the highest-bandwidth
entry's `baseUrl`.

`bili-cli` (`pipx install bilibili-cli && bili login`) still has a role —
metadata and search (`bili video`, `bili search`) — but it's demoted for
downloads: it needs a login QR and doesn't touch the playurl 412 at all. If
a video has subtitles (check `bili video`'s `subtitle.available`), use those
instead of transcribing audio.

## YouTube: needs a cookie snapshot + EJS solver (not zero-config)

Plain `yt-dlp` against YouTube is not reliably zero-config anymore. Export a
cookie snapshot once, and pass a remote EJS (signature-solving) component on
every call:

```bash
# one-time: export a cookie snapshot from a logged-in browser
yt-dlp --cookies-from-browser chrome --cookies ~/.agent-reach/yt-cookies.txt "<any-video-url>"

# every call after: reuse the snapshot + the EJS solver
yt-dlp --cookies ~/.agent-reach/yt-cookies.txt --remote-components ejs:github \
  --write-sub --skip-download -o "/tmp/%(id)s" "<video-url>"
```

- `--remote-components ejs:github` fetches the EJS signature solver that
  current YouTube player challenges require; omit it and calls fail
  intermittently.
- Re-export the snapshot if it expires (symptom: renewed 403s).
- If the video has no captions, fall back to audio: `yt-dlp -x` then
  `python ~/.claude/scripts/transcribe.py <audio_file>` — the same local
  transcription path podcasts use (below).

## Podcasts / audio: transcribe locally, not via a cloud API

agent-reach's default podcast path uses a cloud transcription API (needs a key).
On a machine with a GPU, prefer a local whisper pipeline — offline, no key, fast:

```bash
# 1) extract audio only (no video) with yt-dlp
yt-dlp -x --audio-format m4a -o "/tmp/%(id)s.%(ext)s" "<podcast-or-video-url>"

# 2) transcribe locally
python <USER_HOME_POSIX>/.claude/scripts/transcribe.py <audio_or_video_path> [--lang zh]
```

A `faster-whisper` GPU script (~10× realtime on a mid-range card) is the
substitute we use; note it in the state file so Claude reaches for it instead of
the cloud default. This is the same audio→`transcribe.py` route used for
Bilibili and no-subtitle YouTube videos above.

## Where fetched sources land (archive-first)

Every fetch is archived under the vault's `.raw/` before any note is written
(vault rule §8). Channel → folder:

| Source | `.raw/` subfolder |
| --- | --- |
| YouTube / Bilibili / podcast transcripts | `.raw/transcripts/` |
| V2EX / Reddit / Xiaohongshu posts | `.raw/social/` |
| RSS articles | `.raw/rss/` |
| WeChat articles | `.raw/wechat/` |
| arbitrary web page snapshots | `.raw/webfetch/` |

## Use from Claude

```
You: "read this bilibili video and file it: <url>"
Claude:
  1. Reads ~/.agent-reach/local-state.md (confirms the guest-API path is what works here)
  2. bili-cli checks metadata / subtitle availability
  3. If subtitled: pull the subtitle directly
  4. If not: bili_audio_url.py → dash audio baseUrl → curl (with Referer) → transcribe.py → text
  5. Archives transcript to .raw/transcripts/YYYY-MM-DD_bilibili_<slug>.md
  6. Writes the source note per note-generation-rules.md, updates notes-graph + log
```

## Failure modes that bit us

| Symptom | Cause | Fix |
| --- | --- | --- |
| Bilibili returns 412 via yt-dlp | Stale `gaia`/`w_webid` signing in yt-dlp's extractor — happens even domestic + full cookies, it's not IP risk control | Don't fight it with cookies — use the `bilibili-api-python` guest API (`bili_audio_url.py`) instead of yt-dlp for Bilibili |
| YouTube subtitle pull fails intermittently | Missing EJS solver or expired/missing cookie snapshot | Pass `--cookies <snapshot>` + `--remote-components ejs:github`; re-export the snapshot if expired |
| Transcription wants a cloud key | Using the default Groq-style path | Point Claude at the local `transcribe.py` (record it in the state file) |
| Twitter/RED return nothing | No cookie/token configured | Twitter needs a user-supplied `auth_token`+`ct0`; RED needs a cookie — flip the channel to ✅ in the state file once set |
| Reinstalling agent-reach "forgot" my setup | Expected — package is stateless | Your state lives in `~/.agent-reach/local-state.md`, which is preserved |
| `ffmpeg`/`yt-dlp` not found | External CLI missing | Install per the list above (Windows `winget`, not `brew`) |

## Don't do these

- **Don't put cookies or API keys in the skill folder or this repo.** They go in
  your machine-local state / browser profile. This repo's template uses
  placeholders only.
- **Don't assume a channel works** — read `~/.agent-reach/local-state.md` first;
  a channel marked ❌ will waste a turn if you try it blind.

## Done when

- A test fetch on a zero-config channel (e.g. an RSS item or a Jina page
  fetch) archives into the right `.raw/` subfolder, and your machine-local
  state file accurately reflects which gated channels you've enabled.

Back to `README.md`, or revisit `05-wechat-mcp.md` for the WeChat specifics.
