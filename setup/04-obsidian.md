# 04 — Obsidian + vault

The knowledge base lives here. Read `vault/structure.md` and
`vault/note-generation-rules.md` after this one — they describe the layout and
conventions that Claude will follow.

## Install Obsidian

- **Desktop**: <https://obsidian.md/download> — install the regular installer
  (not the legacy "ARM" one unless you're on Windows-on-ARM).
- **Mobile** (iOS / Android): App Store / Play Store. Same vendor.

Obsidian is free for personal use. Sync and Publish are paid add-ons. We use
**Sync** (we don't use Publish).

## Create the vault

In Obsidian on desktop, "Create new vault":

- Vault path: `%USERPROFILE%\Documents\knowledge-vault\` (or whatever you
  prefer — be consistent)
- Don't enable any of the optional starter sets

Inside the new vault, create the skeleton folder layout as documented in
`vault/structure.md`:

```
knowledge-vault/
  wiki/
    sources/
    meta/
    _attachments/
    .raw/             (hidden by Obsidian; you create it from a terminal)
    hot.md
    index.md
    log.md
    overview.md
  CLAUDE.md           (paste from config/vault-claude-md.template.md)
```

Drop `config/vault-claude-md.template.md` from this repo into
`<vault>/CLAUDE.md`. This is the ruleset Claude Code reads whenever a session
starts in the vault folder. It contains the ten note-generation rules and the
ingest workflow.

## Obsidian settings to change

Open **Settings (gear icon)** in Obsidian and apply:

| Section | Setting | Value | Why |
| --- | --- | --- | --- |
| Editor | Display readable line length | OFF | Wikilinks read better wide |
| Editor | Strict line breaks | OFF | Markdown soft-wraps |
| Files & links | Default location for new attachments | In subfolder under current → `_attachments/<note-slug>` | Per §7 of the vault CLAUDE.md |
| Files & links | New link format | Shortest path when possible | Stable wikilinks across folder moves |
| Files & links | Use [[Wikilinks]] | ON | The whole stack assumes wikilinks |
| Appearance | Theme | (your choice) | — |
| Core plugins | Daily notes | OFF | Not used |
| Core plugins | Templates | ON | For skeletons/ |
| Core plugins | Outgoing/Backlinks | ON | Used by lint |
| Core plugins | Graph view | ON | Nice for orientation |
| Core plugins | Properties view | ON | Reads YAML frontmatter |
| Community plugins | Dataview | optional — install if you like queries on metadata | |
| Community plugins | Templater | optional — install if you want JS templates | |
| Community plugins | Excalidraw | optional — for hand-drawn embeds | |

## Obsidian Sync

This is what makes the vault appear on your phone. Without Sync (or some
equivalent like iCloud Drive on the vault folder), the rest of this stack
still works on desktop, just not cross-device.

1. Open Settings → Sync. Sign in with your Obsidian account. Subscribe if you
   haven't (~ USD 4/mo / personal plan as of 2026).
2. Create a remote vault from the desktop client. Pick "End-to-end encrypted"
   if you want zero-knowledge.
3. Set the password (it's separate from your account password; **lose it and
   the vault is unrecoverable** — store in a password manager).
4. Pick what to sync. Recommended:
   - Sync all markdown
   - Sync images and PDFs (`_attachments/`)
   - **Do NOT sync `.obsidian/workspace.json`** (each device has its own
     pane layout)
   - **Do NOT sync `.raw/`** (large; keep desktop-only)
5. On your phone, install Obsidian, sign in, "Receive vault from sync", enter
   the password, wait for initial pull.

### Hard rule that bites everyone

**Obsidian Sync only runs while the desktop Obsidian app is running.** It is
not a daemon. If you close Obsidian, files written by Claude Code (or by `git
pull`, or by any external tool) will not propagate to your phone until you
open Obsidian again and wait ~5 seconds for it to scan + push.

This bit us multiple times during development. If your phone "isn't seeing"
a new note, the first thing to check is whether Obsidian Desktop is open and
the Sync icon (bottom-left) is green.

| Sync icon color | Meaning | What to do |
| --- | --- | --- |
| Green | All synced | Nothing |
| Yellow | Queue draining | Wait a few seconds |
| Red | Auth or network failure | Re-sign-in or check VPN/proxy |
| Missing | Desktop not running | Open it |

## Mobile-side conventions

On the phone you mostly READ. For capturing on the go, prefer:

1. Forward the article URL to your Feishu bot → desktop ingests it → vault
   updates → phone gets the synced note within seconds.
2. Or open the vault on your phone, hit New Note, jot 1-2 lines, sync. Claude
   will pick it up next session if you reference it.

Avoid creating long notes on the phone — wikilinks, callouts, and
frontmatter are painful on a touch keyboard.

## Vault-side rules go in `<vault>/CLAUDE.md`

The vault has its OWN `CLAUDE.md` separate from `~/.claude/CLAUDE.md`. That
file is the source of truth for the ten note-generation rules. The template
is in `config/vault-claude-md.template.md`. Drop it in, then read it
top-to-bottom — every rule has a "Why" that prevents a particular failure
mode.

Move on to `07-memory-plugins.md` next (per the README bootstrap order);
WeChat MCP (`05`), Feishu bridge (`03`), and image generation (`06`) are
each independent and can wait until you need them.
