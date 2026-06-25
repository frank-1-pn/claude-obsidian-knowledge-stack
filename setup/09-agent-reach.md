# 09 — Multi-platform fetching via agent-reach (Bilibili, RSS, podcasts, social)

`05-wechat-mcp.md` covers WeChat articles. This page adds **everything else**:
one skill that gives Claude a routing table over ~17 platforms — web/code
search, Bilibili & YouTube subtitles, podcasts (with local transcription), RSS,
V2EX, and the login-gated socials (Twitter/Reddit/Xiaohongshu). Each fetched
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
| YouTube (`yt-dlp`) | ✅ | subtitles + metadata |
| V2EX | ✅ | community threads |
| RSS / Atom | ✅ | feed fetch |
| WeChat official accounts | ✅ cross-platform | see `05-wechat-mcp.md` — hosted MCP (any OS) / Camoufox (any OS) / Windows-only wechatDownload. agent-reach's own channel uses Camoufox, so it works on macOS/Linux without the Windows app |
| Bilibili | ⚠️ region-dependent | domestic IP usually direct; **overseas IP trips 412 risk control** — pass `--cookies-from-browser chrome` (or a cookie file). Search/trending via `bili-cli` needs `bili login` (QR), `pipx install bilibili-cli` |
| Podcasts (Xiaoyuzhou etc.) | ✅ local transcription | see below — uses local GPU whisper, not a cloud API |
| Twitter / X | ❌ needs cookie | enable after dropping in a logged-in cookie |
| Reddit | ❌ needs cookie | same |
| Xiaohongshu (RED) | ❌ needs cookie | same |

## Zero-config quick commands

```bash
# Web search (Exa via MCP)
mcporter call 'exa.web_search_exa(query: "your query", numResults: 5)'

# Read any web page as markdown
curl -s "https://r.jina.ai/https://example.com/article"

# GitHub repo search
gh search repos "your query" --sort stars --limit 10

# YouTube / Bilibili subtitles
yt-dlp --write-sub --skip-download -o "/tmp/%(id)s" "<video-url>"
```

## Bilibili: the 412 gotcha

From an overseas IP, Bilibili returns HTTP 412 (risk control) to anonymous
requests. Two fixes:

```bash
# A) reuse your browser's logged-in session for subtitle/video pulls
yt-dlp --cookies-from-browser chrome --write-sub --skip-download "<bilibili-url>"

# B) for search / trending, log into bili-cli once (QR scan)
pipx install bilibili-cli && bili login
```

Record which one you wired up in `~/.agent-reach/local-state.md` so Claude
doesn't retry the anonymous path.

## Podcasts / audio: transcribe locally, not via a cloud API

agent-reach's default podcast path uses a cloud transcription API (needs a key).
On a machine with a GPU, prefer a local whisper pipeline — offline, no key, fast:

```bash
# download the audio with yt-dlp, then:
python <USER_HOME_POSIX>/.claude/scripts/transcribe.py <audio_or_video_path> [--lang zh]
```

A `faster-whisper` GPU script (~10× realtime on a mid-range card) is the
substitute we use; note it in the state file so Claude reaches for it instead of
the cloud default.

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
  1. Reads ~/.agent-reach/local-state.md (sees Bilibili needs cookies on this box)
  2. yt-dlp --cookies-from-browser chrome --write-sub ... → subtitle file
  3. (if no subtitles) yt-dlp audio → transcribe.py → text
  4. Archives transcript to .raw/transcripts/YYYY-MM-DD_bilibili_<slug>.md
  5. Writes the source note per note-generation-rules.md, updates notes-graph + log
```

## Failure modes that bit us

| Symptom | Cause | Fix |
| --- | --- | --- |
| Bilibili returns 412 | Overseas IP, anonymous request | `--cookies-from-browser chrome`, or `bili login` for bili-cli |
| Transcription wants a cloud key | Using the default Groq-style path | Point Claude at the local `transcribe.py` (record it in the state file) |
| Twitter/Reddit/RED return nothing | No cookie configured | Drop in a logged-in cookie; flip the channel to ✅ in the state file |
| Reinstalling agent-reach "forgot" my setup | Expected — package is stateless | Your state lives in `~/.agent-reach/local-state.md`, which is preserved |
| `ffmpeg`/`yt-dlp` not found | External CLI missing | Install per the list above (Windows `winget`, not `brew`) |

## Don't do these

- **Don't put cookies or API keys in the skill folder or this repo.** They go in
  your machine-local state / browser profile. This repo's template uses
  placeholders only.
- **Don't assume a channel works** — read `~/.agent-reach/local-state.md` first;
  a channel marked ❌ will waste a turn if you try it blind.

## Done when

- A test fetch on a zero-config channel (e.g. a YouTube subtitle or an RSS item)
  archives into the right `.raw/` subfolder, and your machine-local state file
  accurately reflects which gated channels you've enabled.

Back to `README.md`, or revisit `05-wechat-mcp.md` for the WeChat specifics.
