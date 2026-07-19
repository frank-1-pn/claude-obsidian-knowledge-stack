#!/usr/bin/env python
"""
Edit an existing image via OpenAI-compatible /v1/images/edits (gpt-image-2).

Usage:
    python editimg.py <input.png> <output.png> "<edit-prompt>" [size] [model]
    size:  1024x1024 (default) | 1024x1536 | 1536x1024 | auto
    model: gpt-image-2 (default)

Optional: for masked edits, pass --mask <mask.png> (透明区域 = 允许改的部分)
    python editimg.py <in.png> <out.png> "<prompt>" --mask <mask.png> [size]

On success, also writes a sidecar <out>.prompt.json recording the edit chain
{edit_prompt, input, mask, model, size, base_url, ts} so the edit can be
reproduced. The sidecar NEVER contains the API key.

API key resolution (first that exists, never echoed):
    env GENIMG_KEY_FILE  >  ~/.secrets/vectorengine_key.txt  >  legacy ~/Desktop/openai_api.txt
Base URL: set via env GENIMG_BASE_URL — point this at your own OpenAI-compatible
relay/aggregator. Falls back to a placeholder host if unset.
"""
import sys
import os
import json
import time
import base64
import urllib.request
import urllib.error
from pathlib import Path
from email.generator import BytesGenerator
from io import BytesIO
import uuid

# Key path: env override > user-only .secrets dir > legacy Desktop (migration fallback).
KEY_FILE = next(
    (Path(c) for c in (
        os.environ.get("GENIMG_KEY_FILE"),
        str(Path.home() / ".secrets" / "vectorengine_key.txt"),
        str(Path.home() / "Desktop" / "openai_api.txt"),
    ) if c and Path(c).exists()),
    Path.home() / ".secrets" / "vectorengine_key.txt",
)
BASE_URL = os.environ.get("GENIMG_BASE_URL", "https://api.your-relay.example")
ENDPOINT = f"{BASE_URL}/v1/images/edits"

# Force no proxy (system proxy blocks vectorengine)
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
urllib.request.install_opener(_opener)


def build_multipart(fields: dict, files: dict):
    """Build multipart/form-data body manually (stdlib only)."""
    boundary = f"----genimg{uuid.uuid4().hex}"
    body = BytesIO()
    for name, value in fields.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        body.write(str(value).encode("utf-8"))
        body.write(b"\r\n")
    for name, (filename, content, ctype) in files.items():
        body.write(f"--{boundary}\r\n".encode())
        body.write(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        body.write(f"Content-Type: {ctype}\r\n\r\n".encode())
        body.write(content)
        body.write(b"\r\n")
    body.write(f"--{boundary}--\r\n".encode())
    return body.getvalue(), f"multipart/form-data; boundary={boundary}"


def main():
    args = list(sys.argv[1:])
    if len(args) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    mask_path = None
    if "--mask" in args:
        i = args.index("--mask")
        mask_path = Path(args[i + 1])
        del args[i : i + 2]

    src = Path(args[0])
    out = Path(args[1])
    prompt = args[2]
    size = args[3] if len(args) > 3 else "1024x1024"
    model = args[4] if len(args) > 4 else "gpt-image-2"

    if not src.exists():
        print(f"input not found: {src}", file=sys.stderr)
        sys.exit(1)
    if not KEY_FILE.exists():
        print(f"API key file not found: {KEY_FILE}", file=sys.stderr)
        sys.exit(1)

    key = KEY_FILE.read_text(encoding="utf-8").splitlines()[0].strip()
    out.parent.mkdir(parents=True, exist_ok=True)

    fields = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "n": 1,
    }
    files = {"image": (src.name, src.read_bytes(), "image/png")}
    if mask_path:
        if not mask_path.exists():
            print(f"mask not found: {mask_path}", file=sys.stderr)
            sys.exit(1)
        files["mask"] = (mask_path.name, mask_path.read_bytes(), "image/png")

    body, ctype = build_multipart(fields, files)

    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": ctype},
        method="POST",
    )

    print(
        f"[editimg] editing {src.name} -> {out.name} "
        f"(model={model}, size={size}, mask={'yes' if mask_path else 'no'}, base={BASE_URL})...",
        file=sys.stderr,
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            resp_body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8"))
            print(f"[editimg] API error ({e.code}):", file=sys.stderr)
            print(json.dumps(err.get("error", err), indent=2, ensure_ascii=False), file=sys.stderr)
        except Exception:
            print(f"[editimg] HTTPError {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(2)

    if "data" not in resp_body or not resp_body["data"]:
        print("[editimg] no image data in response:", file=sys.stderr)
        print(json.dumps(resp_body, indent=2, ensure_ascii=False)[:500], file=sys.stderr)
        sys.exit(3)

    item = resp_body["data"][0]
    if item.get("b64_json"):
        out.write_bytes(base64.b64decode(item["b64_json"]))
    elif item.get("url"):
        with urllib.request.urlopen(item["url"], timeout=60) as r:
            out.write_bytes(r.read())
    else:
        print("[editimg] no b64_json or url in data item", file=sys.stderr)
        sys.exit(4)

    size_bytes = out.stat().st_size
    print(f"[editimg] saved {out} ({size_bytes} bytes)", file=sys.stderr)

    # Sidecar: record the edit chain (input + edit prompt) so it can be
    # reproduced later. NEVER contains the API key.
    sidecar = out.with_suffix(".prompt.json")
    try:
        sidecar.write_text(
            json.dumps(
                {
                    "edit_prompt": prompt,
                    "input": str(src),
                    "mask": str(mask_path) if mask_path else None,
                    "model": model,
                    "size": size,
                    "base_url": BASE_URL,
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"[editimg] wrote sidecar {sidecar.name}", file=sys.stderr)
    except OSError as e:
        print(f"[editimg] WARN: could not write sidecar: {e}", file=sys.stderr)

    print(str(out))


if __name__ == "__main__":
    main()
