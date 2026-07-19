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
| YouTube (yt-dlp) | ⚠️ needs cookie + EJS solver | not zero-config — needs a cookie snapshot (`yt-cookies.txt`) + `--remote-components ejs:github`; no-subtitle videos fall back to audio + `transcribe.py` |
| V2EX | ✅ no login | community threads |
| RSS / Atom | ✅ automated | daily scheduled task (`KnowledgeVault-RSSFetch` → `fetch_rss.py`), ~10 sources, incremental, zero-LLM, into `.raw/rss/` |
| WeChat official accts | ✅ local MCP | wechatDownload MCP @ `http://127.0.0.1:4545` (see setup/05) |
| Bilibili | ✅ guest API, no login | `yt-dlp` 412s the playurl endpoint unconditionally (stale signing) — even domestic IP + full cookies. Fix: `pip install bilibili-api-python` → `video.Video(bvid=...).get_download_url(0)` → dash audio baseUrl → `curl -H "Referer: https://www.bilibili.com"` → `transcribe.py`. `bili-cli` demoted to metadata/search only |
| Podcasts (Xiaoyuzhou…) | ✅ local transcription | use local whisper, not a cloud API (see below) |
| Twitter / X | ❌ needs user-supplied token | user provides `auth_token` + `ct0` → `setx TWITTER_AUTH_TOKEN <value>` / `setx TWITTER_CT0 <value>` |
| Reddit | ✅ logged in | `rdt login` extracts cookies from a logged-in Chrome profile (close Chrome first); re-run if the cookie expires |
| Xiaohongshu (RED) | ❌ needs cookie | same |

## Local audio/video transcription (substitute for cloud API)

If this machine has a GPU, prefer a local whisper pipeline — offline, no key:

```bash
python <USER_HOME_POSIX>/.claude/scripts/transcribe.py <audio_or_video_path> [--lang zh]
```

- Podcast/YouTube: extract audio with `yt-dlp -x` first, then transcribe.
- Bilibili: audio comes from `bili_audio_url.py` (guest API) + `curl` with a
  `Referer` header, NOT `yt-dlp` (see the Bilibili row above) — then transcribe.
- `ffmpeg` required: Windows `winget install ffmpeg` (not macOS `brew`).

## Archive landing (vault rule §8)

Fetched sources are archived before noting:
transcripts → `.raw/transcripts/` · social → `.raw/social/` · RSS → `.raw/rss/`
· WeChat → `.raw/wechat/` · web snapshots → `.raw/webfetch/`.

## TODO (per machine)

- [ ] Twitter: add a user-supplied `auth_token` + `ct0` to enable.
- [ ] Xiaohongshu: add cookies to enable.
- [ ] YouTube: export a cookie snapshot (`yt-cookies.txt`) if you haven't yet.
