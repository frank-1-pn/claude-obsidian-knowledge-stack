# 06 — Image generation for diagrams

When a section of a note is genuinely hard to read without a diagram, Claude
generates one. The defaults: `gpt-image-1 (or your proxy's equivalent)` via an API proxy, all in-image
text in Chinese (for cross-device, no-OCR readability).

## Why this configuration

- **gpt-image-1 (or your proxy's equivalent) over DALL-E 3**: instruction following is much stronger,
  text rendering inside the image is accurate, style suits technical
  diagrams. DALL-E 3 is the fallback.
- **Through an API proxy** (e.g. `a similar OpenAI-compatible API aggregator`, `oneapi`, or any
  OpenAI-compatible aggregator): so you don't need to deal with OpenAI's
  organization verification (face scan + card bind), which is painful from
  some regions.
- **Chinese text in images by default**: titles, axis labels, callouts,
  arrows, table headers — all Chinese. This is so the operator can read on
  phone without OCR, share with non-English-speaking colleagues, etc.
  Proper-noun model names / commands / paper titles may stay English.

You can swap any of these (direct OpenAI, English text, DALL-E 3) by changing
the helper script. Defaults are the production-tested choice.

## Install the helper script

Drop `config/genimg.py` from this repo at `~/.claude/scripts/genimg.py`.
The script is short (~80 lines, OpenAI-compatible `/v1/images/generations`
caller); see the file directly for the implementation. Adapt the
`DEFAULT_BASE_URL` constant near the top to match your proxy.

## API key file

One-line file at `~/Desktop/openai_api.txt`:

```
sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Additional notes after the first line are fine — the script only reads line
1.

## Configure your proxy URL

Edit the constant `BASE_URL` in the helper to match your proxy:

- Any OpenAI-compatible aggregator: `https://api.<your-host>` (do NOT include
  trailing `/v1`; the script appends it on the request path)
- OneAPI self-hosted: `https://<your-host>` (same — no `/v1`)
- Direct OpenAI: `https://api.openai.com`

Pick whichever proxy you actually pay for; the request shape is identical
across OpenAI-compatible endpoints.

## Prompt template Claude should use

Embed this in the per-image prompt to enforce Chinese labeling:

```
高质量信息图。
- 标题、坐标轴、标签、箭头注释、图例文字必须使用简体中文。
- 风格：clean, modern, technical — 像 Stripe 或 Linear 的官方架构图。
- 配色：低饱和、对比清晰、暗色背景或白色背景任选。
- 不要加水印，不要二维码，不要无关装饰。

主题：<你这里写一句话讲图要表达什么>
要素：<列 3-5 个元素>
布局：<横向/纵向/四象限/时间线 等>
```

If the proxy returns a primarily-English image despite the Chinese
instruction, retry once with a sharper "all text must be in Simplified
Chinese — English text is unacceptable" preamble. If that fails too, fall
back to DALL-E 3 (lower quality but more reliable Chinese rendering).

## Where the image lands

Per vault rule §7 + §9:

```
<vault>/wiki/_attachments/<note-slug>/<descriptive-name>.png
```

Reference from the note via Obsidian wikilink:

```markdown
![[<note-slug>/<descriptive-name>.png]]
```

Or relative path if you prefer Markdown standard:

```markdown
![描述](../../_attachments/<note-slug>/<descriptive-name>.png)
```

## Add this to your note-generation flow

After writing the body of any source note, Claude should self-ask:

> "Which section of this note is the hardest to follow without a diagram?"

If the answer is non-trivial, generate one figure (one per note is plenty;
two is fine; more than two is over-generation). Save under
`_attachments/<note-slug>/`, embed, and add the path to the `Output:` line
of the matching `log.md` entry.

## Failure-mode retries

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `urllib.error.URLError: <urlopen error timed out>` | First call after long idle | Retry once; if still failing, raise timeout to 600s |
| HTTP 401 / 403 | API key wrong or proxy auth misconfigured | Re-check `~/Desktop/openai_api.txt`; test with a `curl` to your proxy's `/v1/models` |
| HTTP 400 with "prompt rejected" | Content moderation tripped | Rephrase: remove anything that might look like violence / NSFW / political content |
| All-English image | Prompt didn't enforce hard enough | Retry with `--all-chinese-text-mandatory` style preamble; if 2 retries fail, fall back to DALL-E 3 |
| Out of credit / quota | Proxy account out of balance | Top up; or use `model=dall-e-3` (cheaper fallback) |

## When NOT to generate an image

- The section is already clear from text + tables
- The note is short (< 800 chars body) — adding an image throws off ratio
- The note is a command reference / API doc — diagrams add nothing
- You've already generated 2 images for this note — stop, it's enough

## Done when

- `python ~/.claude/scripts/genimg.py /tmp/test.png "中文测试：一个齿轮咬合三个齿轮的信息图，标注：核心机制 / 输入 / 输出 / 反馈" 1024x1024` produces an image with legible Chinese labels in under 3 minutes.
- That image embeds in an Obsidian preview correctly.

Move on to `07-memory-plugins.md`.
