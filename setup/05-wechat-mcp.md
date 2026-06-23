# 05 — WeChat article ingestion via wechatDownload MCP

WeChat (微信) articles live on `mp.weixin.qq.com` and ship with a referer
wall: the article HTML loads in a browser, but images and the full HTML
won't deliver to a vanilla `curl` or `WebFetch`. The community tool
`wechatDownload` solves this by running a desktop app that holds a valid
session and serves a local MCP endpoint.

## What you'll install

- **wechatDownload** desktop app (Windows tray app)
- (Already installed if you followed `01-prereqs.md`:) Node + npm
- (Already configured if you followed `02-claude-code.md`:) Claude Code, which
  reads `~/.claude.json` for MCP server registrations

## Install the desktop app

1. Download from the project repo: <https://github.com/qiye45/wechatDownload>
2. Run installer. On first launch the app sits in the system tray.
3. **Configure the download output directory** in the app's settings UI to
   wherever you want articles to land. We use `%USERPROFILE%\Desktop\下载\`,
   but any folder works. **Remember this path** — you'll need it below.
4. Authenticate. The first time you try to download an article, the app will
   open the WeChat in-app browser to capture session cookies. Follow the
   in-app instructions once; subsequent downloads are silent.

The app exposes a local MCP server on `http://127.0.0.1:4545/mcp` as long as
it's running. Quit the app = MCP unavailable.

## Verify MCP is alive

```bash
curl -s http://127.0.0.1:4545/mcp -X POST \
  -H "Content-Type: application/json" \
  -H "Accept: application/json,text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1,"params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"probe","version":"0.1"}}}' \
  --max-time 5
```

You should see a 200 response with an `Mcp-Session-Id` header. If you get
"Connection refused", the app isn't running.

## Register the MCP in Claude Code

Add to `~/.claude.json` under `mcpServers`:

```json
{
  "mcpServers": {
    "wechatDownload": {
      "type": "http",
      "url": "http://127.0.0.1:4545/mcp"
    }
  }
}
```

This is the only MCP config you strictly need for this stack. The full
template in `config/mcp-config.example.json` shows other useful MCPs you can
add.

Restart Claude Code. New sessions will surface `mcp__wechatDownload__*` tools
on demand via the deferred-tool loader.

## The four MCP tools

| Tool | Args | Purpose |
| --- | --- | --- |
| `single_article_download` | `url: string` | Download one article (most common) |
| `get_public_account_id` | (none) | Resolve a public account by name (manual flow uses this) |
| `batch_download_articles` | (none) | Download all articles for whatever account the desktop app currently has selected |
| `export_article_data` | (none) | Export already-downloaded article metadata to CSV/JSON |

## Use from Claude

In a session, after the MCP is registered:

```
You: "ingest this WeChat article: https://mp.weixin.qq.com/s/xxxxx"
Claude:
  1. (Confirms wechatDownload MCP is alive via initialize probe)
  2. Calls mcp__wechatDownload__single_article_download(url)
  3. Waits 30s-2m for download to land in <download dir>/<account>/<title>.{html,md,docx,pdf,mhtml}
  4. Reads the .md (or .html if .md missing)
  5. Follows vault note-generation rules:
     - Copies referenced images from <download dir>/<account>/图片/ to vault/_attachments/<slug>/
     - Replaces mmbiz.qpic.cn external links with [[<slug>/<image.jpg>]]
     - Writes the source note to vault/wiki/sources/<domain>/<title>.md
     - Archives the .html + .md pair to vault/.raw/wechat/YYYY-MM-DD_<slug>_<wxid>.{html,md}
     - Adds a log entry to vault/wiki/log.md
```

## Failure modes that bit us

| Symptom | Cause | Fix |
| --- | --- | --- |
| `single_article_download` returns success but no files appear | App's output directory was reconfigured since last note | Re-check the app's settings UI; verify by `Get-ChildItem -Recurse -Filter "log<YYYYMMDD>.txt"` to find today's log location — that folder is the real output root |
| Article downloads but Markdown is < 500 chars | Hit the anti-scraping wall | Wait a few minutes and retry; if persistent, the app may need cookie refresh |
| Images in Obsidian preview as broken | Images weren't localized to `_attachments/` | Per vault rule §7, every referenced image must be copied locally; check Claude actually did this and not just kept the `mmbiz.qpic.cn` URL |
| MCP says "connection refused" | App not running | Start the desktop app from the tray |
| Cookie expired | Manual capture flow needed | Call `get_public_account_id`; it returns a clipboard verification link. Open in WeChat's in-app browser to refresh; then retry |

## Don't do these

- **Don't fall back to raw `curl` on `mp.weixin.qq.com`** when MCP is
  unavailable. You'll get a stub HTML without content, then waste an hour
  diagnosing. Just ask the user to start the app.
- **Don't hardcode the old output path** in any of your scripts. Always
  resolve at runtime by looking for the latest `log<YYYYMMDD>.txt`.
- **Don't try to fully localize every image** in articles with 30+ images.
  Per vault rule §7, only images actually referenced in the synthesized note
  need local copies. The rest stay as remote URLs (visible in the archived
  HTML, not in the Markdown).

## Done when

- A test article ingest produces a properly-formed source note in
  `wiki/sources/`, an archive pair in `.raw/wechat/`, locally-resolved
  images in `_attachments/<slug>/`, and a log entry in `wiki/log.md`.

> Beyond WeChat: `09-agent-reach.md` adds fetching for Bilibili, YouTube, RSS,
> podcasts, V2EX and the socials. Its WeChat-official-account channel reuses
> this exact wechatDownload MCP (`http://127.0.0.1:4545`) — so finishing this
> page also wires up WeChat inside agent-reach.

Move on to `06-image-generation.md` to add diagram generation, or
`07-memory-plugins.md` to wire cross-session memory.
