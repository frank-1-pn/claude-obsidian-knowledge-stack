# 06 — Image generation for diagrams

When a section of a note is genuinely hard to read without a diagram, Claude
generates one. The defaults: `gpt-image-2 (or your proxy's equivalent)` via an API proxy, all in-image
text in Chinese (for cross-device, no-OCR readability).

## Why this configuration

- **gpt-image-2 (or your proxy's equivalent) over DALL-E 3**: instruction following is much stronger,
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

## Install the helper scripts

Drop `config/genimg.py` from this repo at `~/.claude/scripts/genimg.py`. It's
a ~200-line OpenAI-compatible `/v1/images/generations` caller: it resolves
the API key (see below), retries transient failures (429/5xx, timeouts,
connection errors) with exponential backoff, saves the PNG, and — on
success — writes a `<output>.prompt.json` sidecar next to the image
recording `{prompt, model, size, base_url, ts}` so the image can be
regenerated later without hunting for the original prompt. The sidecar never
contains the API key. See the file directly for the implementation.

For editing an existing image instead of generating a new one, also install
`config/genimg_edit.py` (img2img / style transfer) and `config/editimg.py`
(masked edits) — see the dedicated sections below.

## API key file

The helper resolves the key file in this order (first that exists wins, and
the key is never echoed to logs or the sidecar):

1. `$GENIMG_KEY_FILE` env var — explicit override, highest priority
2. `~/.secrets/vectorengine_key.txt` — recommended user-only location
3. `~/Desktop/openai_api.txt` — legacy fallback, kept only for migration

Whichever path you use, it's a one-line file:

```
sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Additional notes after the first line are fine — the script only reads line
1.

## Configure your relay/proxy URL

Set the `GENIMG_BASE_URL` env var to your own OpenAI-compatible relay or
aggregator (do NOT include a trailing `/v1`; the script appends
`/v1/images/generations` or `/v1/images/edits` itself):

- Any OpenAI-compatible aggregator: `https://api.<your-host>`
- OneAPI self-hosted: `https://<your-host>` (same — no `/v1`)
- Direct OpenAI: `https://api.openai.com`

If `GENIMG_BASE_URL` is unset, the script falls back to an obviously-fake
placeholder host that will error out — you must set it to a relay you
actually hold a key for. Pick whichever proxy you actually pay for; the
request shape is identical across OpenAI-compatible endpoints.

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

This "all in-image text must be Chinese" rule is not just for fresh
generations — it applies equally to edits (both `genimg_edit.py` and
`editimg.py` below). Include the same Chinese-labeling preamble in the edit
prompt, or an edit can silently reintroduce English text into a previously
all-Chinese diagram.

## Editing an existing image (img2img / style transfer)

For turning an existing image into a new one — style transfer, "redraw this
diagram in a different visual style," compositing a reference photo into an
illustration — use `config/genimg_edit.py` instead of generating from
scratch. Drop it at `~/.claude/scripts/genimg_edit.py`; key and base-URL
resolution mirror `genimg.py` exactly (same env vars, same never-echoed
key).

```
python genimg_edit.py <out.png> <input_image> --prompt-file <p.txt> [size]
```

Notes:

- **Argument order is out-before-input**: `<out.png>` comes first, then
  `<input_image>` — easy to get backwards if you're used to `editimg.py`'s
  input-before-output order (see below).
- `size` defaults to `1536x1024` if omitted.
- Internally this does a multipart upload of the input image plus the
  prompt to `/v1/images/edits` using `gpt-image-2` — there is no mask
  parameter; the whole image is subject to restyling. For "change only this
  region" edits, use `editimg.py`'s `--mask` support instead.
- Same retry-on-429/5xx behavior as `genimg.py`.

## Masked edits (editimg.py)

`config/editimg.py` handles the other edit shape: change one region of an
image while leaving the rest untouched. Pass `--mask <mask.png>` where the
mask's **transparent** area marks what's allowed to change (opaque = frozen):

```
python editimg.py <input.png> <output.png> "<edit-prompt>" --mask <mask.png> [size]
```

Note the argument order here is input-before-output — the reverse of
`genimg_edit.py` above. Without `--mask`, `editimg.py` behaves like a
whole-image edit. It also writes a `<out>.prompt.json` sidecar recording the
edit chain (`edit_prompt`, `input`, `mask`, `model`, `size`, `base_url`,
`ts` — never the key) so the edit can be reproduced later.

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
| HTTP 401 / 403 | API key wrong or proxy auth misconfigured | Re-check whichever key file resolved (`GENIMG_KEY_FILE` > `~/.secrets/vectorengine_key.txt` > `~/Desktop/openai_api.txt`); test with a `curl` to your proxy's `/v1/models` |
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
