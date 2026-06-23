# agent-reach local state (template)

Copy this to `~/.agent-reach/local-state.md` and edit for your machine. The
agent-reach skill is told to **read this first** so Claude knows which channels
are live, which need a credential, and what local substitutes exist. This file
lives outside the package, so reinstalling the skill never overwrites it.

> Keep real cookies / API keys OUT of this file. Cookies belong in your browser
> profile or a path referenced here, not pasted inline. This template is
> placeholders only.

## Channel status

| Channel | Status | Notes / local substitute |
| --- | --- | --- |
| Exa search | ✅ no login | general web search |
| Jina reader | ✅ no login | any URL → markdown |
| GitHub (gh) | ✅ logged in | `gh auth status` to confirm |
| YouTube (yt-dlp) | ✅ no login | subtitles + metadata |
| V2EX | ✅ no login | community threads |
| RSS / Atom | ✅ no login | feed fetch |
| WeChat official accts | ✅ local MCP | wechatDownload MCP @ `http://127.0.0.1:4545` (see setup/05) |
| Bilibili | ⚠️ region-dependent | domestic IP usually direct; overseas trips **412** → `--cookies-from-browser chrome`; search/trending needs `bili login` |
| Podcasts (Xiaoyuzhou…) | ✅ local transcription | use local whisper, not a cloud API (see below) |
| Twitter / X | ❌ needs cookie | enable after dropping in a logged-in cookie |
| Reddit | ❌ needs cookie | same |
| Xiaohongshu (RED) | ❌ needs cookie | same |

## Local audio/video transcription (substitute for cloud API)

If this machine has a GPU, prefer a local whisper pipeline — offline, no key:

```bash
python <USER_HOME_POSIX>/.claude/scripts/transcribe.py <audio_or_video_path> [--lang zh]
```

- Download podcast/Bilibili/YouTube audio with `yt-dlp` first, then transcribe.
- `ffmpeg` required: Windows `winget install ffmpeg` (not macOS `brew`).

## Archive landing (vault rule §8)

Fetched sources are archived before noting:
transcripts → `.raw/transcripts/` · social → `.raw/social/` · RSS → `.raw/rss/`
· WeChat → `.raw/wechat/` · web snapshots → `.raw/webfetch/`.

## TODO (per machine)

- [ ] Twitter / Reddit / Xiaohongshu: add cookies to enable.
- [ ] Confirm Bilibili path (direct vs cookie) for your network.
