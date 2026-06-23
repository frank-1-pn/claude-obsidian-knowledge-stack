# 08 — Automated AI daily briefing (cloud cron → Feishu)

A scheduled pipeline that, every morning, fetches AI news from many sources,
summarizes each item with an LLM, renders a categorized Chinese HTML report,
and pushes it to your Feishu chat — then archives it. It runs in **GitHub
Actions** (cloud), so it fires even when your desktop is off.

This is the one part of the stack that is **proactive** (it pushes to you on a
timer) rather than reactive. It's optional; skip if you only want on-demand
ingestion.

## What it's built on

- A fork of the open-source **Horizon** news-digest engine
  (<https://github.com/Thysrael/Horizon>, MIT). You keep it in your own
  private repo so your source list / threshold / push target are yours.
- **DeepSeek** (or any OpenAI-compatible provider) for the summaries — cheap
  enough to run daily (~¥0.9 / $0.12 per run at ~290K tokens).
- The same **Feishu bot** ("Bot1") from `03-feishu-bot.md` as the delivery
  channel — here used from CI with its app credentials, not the local daemon.

## What you'll set up

1. Fork Horizon into a private repo (e.g. `<YOU>/ai-daily-briefing`).
2. Configure the source list + model + score threshold.
3. Add four CI secrets (LLM key + Feishu app id/secret/chat id).
4. A GitHub Actions workflow on a daily cron + manual dispatch.
5. (Optional) A local Task Scheduler job that triggers the run on time when
   your machine is on (the GitHub cron is the fallback for when it's off).

## 1. Fork and clone

```bash
gh repo fork Thysrael/Horizon --fork-name ai-daily-briefing --clone
# or fork in the GitHub UI, then: git clone <your-fork-url>
```

Keep `upstream` pointed at Horizon so you can pull improvements:

```bash
git remote add upstream https://github.com/Thysrael/Horizon.git
```

## 2. Configure sources / model / threshold

Horizon reads a JSON config. Commit a CI-specific copy (CI copies it to the
runtime path on each run) — see `config/daily-briefing-config.example.json` in
this repo for a sanitized starting point. Key fields:

```jsonc
{
  "llm": { "provider": "deepseek", "model": "deepseek-chat",
           "api_key_env": "DEEPSEEK_API_KEY" },
  "languages": ["zh"],                 // summary language(s)
  "filtering": { "ai_score_threshold": 6.0 },  // 0-10; higher = fewer, higher-signal items
  "sources": {
    "hackernews": true,
    "rss": [ "<vendor + industry + hardware + supply-chain feeds>" ],
    "reddit": ["MachineLearning", "LocalLLaMA"],
    "ossinsight": true,                // GitHub trending
    "github_releases": ["vllm/vllm", "huggingface/transformers", "ggerganov/llama.cpp", "ollama/ollama"]
  }
}
```

Tuning notes learned in production:
- **Threshold** is the main volume knob. 6.0 ≈ a readable digest; drop to ~4.0
  on slow news days, raise if it's too noisy.
- Group GitHub items **by source** (trending vs releases) and put them near the
  top — they're the highest-signal section for a builder.
- A dedicated "AI supply chain" category (HBM/DRAM, optical/CPO, power/datacenter
  cooling, foundry/packaging) is worth adding if you track hardware.

## 3. CI secrets (never commit these)

Set four repository secrets. Values stay in GitHub; the code only reads env vars.

```bash
gh secret set DEEPSEEK_API_KEY -R <YOU>/ai-daily-briefing --body "<DEEPSEEK_API_KEY>"
gh secret set FEISHU_APP_ID    -R <YOU>/ai-daily-briefing --body "<APP_ID>"
gh secret set FEISHU_APP_SECRET -R <YOU>/ai-daily-briefing --body "<APP_SECRET>"   # plaintext from the Feishu open-platform console
gh secret set FEISHU_CHAT_ID   -R <YOU>/ai-daily-briefing --body "<CHAT_ID>"
```

> ⚠️ `FEISHU_APP_SECRET` must be the **plaintext** secret from the Feishu
> open-platform console. The local `~/.lark-cli/config.json` stores an
> *encrypted* object — that won't work in CI.
> ⚠️ Never echo a secret value to stdout / logs.

## 4. The workflow

`.github/workflows/daily-summary.yml`, roughly:

```yaml
name: Daily AI Briefing
on:
  schedule:
    - cron: "0 0 * * *"        # 00:00 UTC = 08:00 Beijing; pick your own
  workflow_dispatch:
    inputs:
      force: { type: boolean, default: false }   # re-run even if today's report exists
jobs:
  brief:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # 0. dedup: if reports/AI-briefing-<UTC-date>.html already on origin/main
      #    and not force → exit early (no paid LLM calls, no push)
      # 1. cp data/config.github.json config.json
      # 2. run Horizon: fetch → DeepSeek summarize → write zh markdown
      # 3. python scripts/render_html.py <md> out.html
      # 4. python scripts/push_file_feishu.py out.html <md>   # uploads HTML file + TOP5 text
      # 5. commit out.html to reports/ and push
```

Two robustness pieces worth copying:
- **Dedup first**: the first step checks whether
  `reports/AI-briefing-<date>.html` already exists on `origin/main`; if so (and
  not `force`), it skips every paid step. This makes "machine-trigger + cloud
  cron" safe to both fire — at most one report per day.
- **Deliver as an HTML file**, not as many chat cards. Pushing 20+ cards spams
  the chat; uploading one self-contained HTML file + a short TOP-5 text intro
  reads far better on mobile.

## 5. (Optional) on-time local trigger

GitHub's cron at `00:00 UTC` is the most congested slot and often runs hours
late. To get it on time when your machine is on, add a local Task Scheduler job
that dispatches the workflow at your target time; the cloud cron stays as the
when-the-machine-is-off fallback. Because of the dedup step, both firing is fine.

```powershell
# trigger script, run by Task Scheduler at 08:00 daily:
gh workflow run "Daily AI Briefing" -R <YOU>/ai-daily-briefing
```

Use `-Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable)` so a missed
run (machine asleep) catches up on wake.

## Manual run / re-push

```bash
# full run (fetches, spends LLM tokens, pushes):
gh workflow run "Daily AI Briefing" -R <YOU>/ai-daily-briefing
# force a second run the same day:
gh workflow run "Daily AI Briefing" -R <YOU>/ai-daily-briefing -f force=true
# watch it:
gh run watch $(gh run list -R <YOU>/ai-daily-briefing -L1 --json databaseId -q '.[0].databaseId') -R <YOU>/ai-daily-briefing --exit-status
```

To re-render/re-push without re-fetching (saves money): download the run's
artifact to get the summary markdown, run `render_html.py` locally, and push the
HTML with your local `lark-cli im +messages-send --file out.html`.

## Failure modes that bit us

| Symptom | Cause | Fix |
| --- | --- | --- |
| Feishu push fails, log shows auth error | `FEISHU_APP_SECRET` is the encrypted object, not plaintext | Re-set the secret with the console plaintext |
| File upload fails | Missing message-send permission / wrong file_type | Grant the bot `im:message` send; upload as `file_type=stream` |
| Report empty or very short | Few items cleared the threshold, or an RSS feed 404'd | Lower `ai_score_threshold` temporarily or widen the time window |
| Too many messages in chat | Used the per-card pusher | Use the single-HTML-file pusher instead |
| Schedule silently stopped | GitHub disables cron on repos inactive 60 days; cron only runs on the default branch | Push any commit / run manually; keep work on `main` |

## Cost

At ~290K tokens/run on DeepSeek ≈ ¥0.9 ($0.12)/day ≈ ¥27/month. GitHub Actions
~11 min/run, inside the free minutes for a private repo = ¥0.

## Done when

- A manual `workflow_dispatch` produces an HTML report in `reports/`, pushes the
  file + a TOP-5 intro to your Feishu chat, and a second same-day run is skipped
  by the dedup step.

Move on to `09-agent-reach.md` to add multi-platform source fetching
(Bilibili, RSS, podcasts, social), or back to `README.md`.
