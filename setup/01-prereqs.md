# 01 — Prerequisites

Target environment: Windows 10/11 (the rest of this stack is tuned for it).
Adaptable to macOS/Linux with minor path changes.

## Required software

| Tool | Min version | Why |
| --- | --- | --- |
| Windows 10/11 | 21H2+ | Foreground/SendKeys APIs assumed by the Feishu bridge |
| Node.js | 20.x LTS | Claude Code runtime, lark-cli, MCP servers |
| Python | 3.12+ | `claude_agent_sdk`, the image-gen helper, any Python MCPs |
| Git | 2.40+ | Vault history, repo clones |
| PowerShell | 7.x preferred (5.1 works for most scripts) | Most helper scripts target pwsh syntax that also works in 5.1 |
| Git Bash / MSYS2 | latest from git-scm.com | The bridge's `monitor-bot.sh` is bash |

## Install order

1. **Git** — installer from <https://git-scm.com/download/win>. During the
   installer, accept the bundled "Git Bash" and choose "Use Git from the Windows
   Command Prompt".
2. **Node.js 20 LTS** — installer from <https://nodejs.org>. Confirm:
   ```powershell
   node -v   # v20.x.x or later
   npm -v    # 10.x or later
   ```
3. **Python 3.12+** — installer from <https://python.org>. Tick "Add python.exe
   to PATH" during install.
4. **PowerShell 7** (optional but recommended) — installer from
   <https://github.com/PowerShell/PowerShell/releases>. Some scripts assume
   pwsh, but most of this stack also works with Windows PowerShell 5.1.
5. **Windows Terminal** — from Microsoft Store. The Feishu /compact macro flow
   sends keys into the foreground terminal window, and Windows Terminal is
   what the foreground-detector locator expects to find.

## PATH sanity

Add the npm global bin to PATH so `lark-cli` and other globally-installed CLIs
resolve. Default location:

```powershell
[Environment]::GetEnvironmentVariable('Path', 'User')   # check
[Environment]::SetEnvironmentVariable('Path',
    [Environment]::GetEnvironmentVariable('Path', 'User') + ';' + $env:APPDATA + '\npm',
    'User')                                              # add if missing
```

Verify after a fresh shell:

```powershell
where lark-cli   # once installed in setup/03
```

## Local proxy (optional)

If you run a local HTTP proxy (clash/v2ray) on `127.0.0.1`, set the env vars
once at User scope:

```powershell
[Environment]::SetEnvironmentVariable('HTTPS_PROXY', 'http://127.0.0.1:<port>', 'User')
[Environment]::SetEnvironmentVariable('HTTP_PROXY',  'http://127.0.0.1:<port>', 'User')
```

The Feishu bridge explicitly sets `LARK_CLI_NO_PROXY=1` per call to keep bot
secrets out of the proxy lane. You don't have to do that yourself if you
follow that repo's setup.

## Disk layout convention

We will create these directories during the setup. Lock them in now so other
paths in this repo make sense:

```
%USERPROFILE%\.claude\                  # Claude Code config (auto-created)
%USERPROFILE%\.claude-mem\              # claude-mem state (auto-created)
%USERPROFILE%\.lark-cli\                # Feishu CLI config (auto-created)
%USERPROFILE%\Documents\<vault-name>\   # Obsidian vault (you create)
%USERPROFILE%\Desktop\<openai-key.txt>  # one-line OpenAI/proxy key file
```

You can put the vault elsewhere (e.g. on D:\) — just be consistent.

## Sanity check

After everything above, this should all succeed:

```powershell
node -v
npm -v
python --version
git --version
pwsh --version    # or  $PSVersionTable.PSVersion  in Windows PowerShell
```

Move on to `02-claude-code.md`.
