# 02 — Claude Code

Install the operator that drives this whole stack.

## Install

```powershell
npm install -g @anthropic-ai/claude-code
claude --version
```

Sign in on first run:

```powershell
claude
# follow the device-code flow in your browser
```

## Where the config lives

| Path | What |
| --- | --- |
| `~/.claude/CLAUDE.md` | Global preferences read every session start |
| `~/.claude/settings.json` | Hooks, enabled plugins, theme, permissions |
| `~/.claude/settings.local.json` | Per-machine permission allowlist (don't commit) |
| `~/.claude/scripts/` | Helper scripts referenced by hooks |
| `~/.claude/plugins/cache/<author>/<plugin>/<version>/` | Installed plugins |
| `~/.claude.json` | MCP server registrations + cached config |

## Drop in the global CLAUDE.md

Copy `config/global-claude-md.template.md` from this repo to
`~/.claude/CLAUDE.md`. Fill in the placeholders for any Feishu bots you
register later. The template explains every section.

## Drop in the hook fragment

If you plan to use the Feishu bridge, also pull the `hooks.PostCompact` and
`hooks.SessionStart` entries from `config/settings-json.template.json` into
your `~/.claude/settings.json`. Keep whatever else you already have in that
file (theme, enabledPlugins, etc.) — only merge `hooks`.

## Recommended plugins

A minimal useful set for this stack — install via Claude Code's `/plugins` UI
or the plugin marketplace URLs in `config/enabled-plugins.md`:

| Plugin | Why for this stack |
| --- | --- |
| `claude-obsidian` | The vault scaffolder + ingest / lint / save / autoresearch / canvas skills |
| `claude-mem` | Cross-session memory (see `07-memory-plugins.md`) |
| `commit-commands` | `/commit`, `/commit-push-pr` — useful when the vault is in git |
| `example-skills` | Reference skills (docx, pdf, xlsx, mcp-builder, etc.) you can crib from |
| `context7` (MCP) | Library doc lookup when working in code |
| `playwright` (MCP) | Browser automation; the vault occasionally needs it for source capture |

The exact marketplace slugs and an extended list (with a few "think twice
before enabling" entries) are in `config/enabled-plugins.md`.

Skip these unless you have a specific use:

- Anything that wants to write outside your vault (some agents)
- Any "memory" plugin you can't audit; you already have `claude-mem`

## Windows-specific gotcha: subagent windows pop a console

`claude_agent_sdk` (the Python SDK that Claude Code uses internally when you
delegate to a subagent) launches `claude.exe` via `anyio.open_process` without
passing `creationflags=CREATE_NO_WINDOW`. On Windows, every subagent spawn
flashes a Windows Terminal window titled "claude".

**Fix:** patch the two `anyio.open_process` call sites in
`%APPDATA%\Python\Python<X>\site-packages\claude_agent_sdk\_internal\transport\subprocess_cli.py`
to add `creationflags=0x08000000` on Windows. The patch script
`config/claude-agent-sdk-autopatch.ps1` (port of the one we run live) does
this idempotently. Wire it into your `SessionStart` hook chain — the example
in `config/settings-json.template.json` already includes the wiring.

Once patched, restart any running claude.exe processes so they re-import the
SDK from disk. Subagent spawns will then be silent.

## First sanity ping

In an empty folder:

```powershell
claude
# > help me list 3 numbers
```

If you see a reply within a few seconds, you're good.

## Session permissions you'll want

In `~/.claude/settings.local.json` add an `allow` list for the Bash / Read /
Edit calls you don't want to be prompted on every session. A reasonable
starter set:

```json
{
  "permissions": {
    "allow": [
      "Bash(git:*)",
      "Bash(gh:*)",
      "Bash(npm:*)",
      "Bash(node:*)",
      "Bash(python:*)",
      "Bash(powershell.exe:*)",
      "Bash(lark-cli:*)",
      "Bash(ls:*)",
      "Bash(cat:*)",
      "Bash(grep:*)",
      "Bash(head:*)",
      "Bash(tail:*)",
      "Bash(echo:*)",
      "Bash(mkdir:*)",
      "Bash(cp:*)",
      "Bash(mv:*)",
      "Bash(pwd)",
      "Read",
      "Edit(C:\\Users\\<you>\\.claude\\**)",
      "Write(C:\\Users\\<you>\\.claude\\**)"
    ],
    "deny": [
      "Bash(rm -rf:*)",
      "Bash(git push --force:*)",
      "Bash(format:*)"
    ]
  }
}
```

Tighten or loosen as you wish.

## Move on

Once Claude Code answers, jump to `04-obsidian.md` to set up the vault.

The recommended order from here (matches `README.md`):
`02 → 04 (Obsidian + vault) → 07 (memory) → 03 (Feishu, optional) →
05 (WeChat MCP, optional) → 06 (image gen, optional)`.
