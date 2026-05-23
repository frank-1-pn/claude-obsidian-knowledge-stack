# Claude Code plugins — recommended set

Install via Claude Code's `/plugins` command. Each plugin pulls from a
marketplace. The ones below are the minimum useful set for this stack.

| Plugin | Marketplace | Purpose |
| --- | --- | --- |
| `claude-obsidian` | `claude-obsidian-marketplace` (`github:<author>/claude-obsidian`) | Vault scaffold + ingest / lint / save / autoresearch / canvas / wiki-query / defuddle skills |
| `claude-mem` | `thedotmack` (`github:thedotmack/claude-mem`) | Cross-session memory (observations + summaries in SQLite) |
| `commit-commands` | `claude-plugins-official` | `/commit`, `/commit-push-pr`, `/clean_gone` — git QoL when vault is tracked |
| `example-skills` | `anthropic-agent-skills` | Reference skills (pptx, docx, pdf, xlsx, mcp-builder, etc.) you can call or crib from |
| `context7` (MCP) | `claude-plugins-official` | Library doc lookup when working in code |
| `playwright` (MCP) | `claude-plugins-official` | Browser automation — occasionally useful for source capture |
| `claude-md-management` | `claude-plugins-official` | `/claude-md-improver` — sanity-check your CLAUDE.md files |
| `skill-creator` | `claude-plugins-official` | Author your own skills as needs emerge |
| `superpowers` | `claude-plugins-official` | Optional discipline skills (brainstorming, debugging, etc.) — opinionated; skip if you don't like the style |
| `frontend-design` | `claude-plugins-official` | Distinctive frontend code generation — only if you build UIs |
| `code-review` | `claude-plugins-official` | `/code-review` — useful before merging PRs in code projects |
| `code-simplifier` | `claude-plugins-official` | Refactor for clarity; opinionated, use case-by-case |

## Marketplaces to add

```json
{
  "extraKnownMarketplaces": {
    "claude-obsidian-marketplace": {
      "source": {
        "source": "github",
        "repo": "<author>/claude-obsidian"
      }
    }
  }
}
```

Built-in marketplaces (no config needed):
- `claude-plugins-official` (Anthropic-curated)
- `anthropic-agent-skills` (Anthropic's "example-skills")
- `thedotmack` (community memory plugin author)

Add to `~/.claude/settings.json` under `extraKnownMarketplaces`. Then in
Claude Code, `/plugins` will list them.

## Plugins to think twice about

- **`hindsight-memory`** — Vectorize.io's competing memory plugin. We
  tried it and uninstalled. Reasons: 3 days, 0 banks (it didn't ingest);
  upstream had two blocking bugs; on Windows, its daemon launches `uv.exe`
  via `subprocess.Popen` without `creationflags=CREATE_NO_WINDOW`, so every
  daemon (re)start pops a visible Windows Terminal window. If you want a
  second memory layer alongside `claude-mem`, evaluate carefully and watch
  upstream issues.
- **Anything that auto-edits files outside the project you're in** — read
  the plugin's docs carefully before enabling.
- **Anything with a hook that emits to a third party** without a rate
  limiter. See `setup/03-feishu-bot.md` linked lesson on the SessionEnd loop.

## Plugin update hygiene

Claude Code auto-updates plugins from their marketplaces. This means **any
patches you applied to plugin internals will be overwritten on the next
auto-update**.

Two examples in this stack:

1. **`claude-mem`** — URL rewrites (e.g., OpenRouter → DeepSeek) get
   overwritten. Solution: `~/.claude/scripts/claude-mem-autopatch.ps1` re-
   applies the patch idempotently on every SessionStart.
2. **`claude_agent_sdk`** (Python; not a CC plugin but installs via pip) —
   subprocess Popen without `CREATE_NO_WINDOW` makes subagents flash console
   windows on Windows. Solution: `claude-agent-sdk-autopatch.ps1` patches
   the SDK on SessionStart.

If you have to patch a plugin, write the patch as an idempotent script
under `~/.claude/scripts/` and wire it into the `SessionStart` hook chain.

## How to add a new plugin

1. In Claude Code: `/plugins`
2. Browse, install
3. Restart session
4. The plugin appears in `~/.claude/plugins/cache/<author>/<plugin>/<ver>/`
5. Its skills auto-appear in the `Skill` tool surface
6. Optionally enable / disable in `~/.claude/settings.json` under
   `enabledPlugins`
