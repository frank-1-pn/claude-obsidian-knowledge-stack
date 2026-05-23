"""Generate images via gpt-image-2 through an OpenAI-compatible API proxy.

Drop this at ~/.claude/scripts/genimg.py and Claude can invoke it during note
generation when a section deserves a diagram.

Usage:
    python genimg.py <out.png> "<prompt>" [size] [model]

Defaults:
    size  = 1024x1024  (also 1024x1536 / 1536x1024 / auto)
    model = gpt-image-2 (fallback: dall-e-3 — pass explicitly)

API key:
    Reads the first line of ~/Desktop/openai_api.txt
    (or override with GENIMG_KEY_FILE env var).

Base URL:
    Default: set BASE_URL constant below to your proxy.
    Override per-call with GENIMG_BASE_URL env var.

Known gotchas:
    1. Windows system proxy (HTTPS_PROXY=http://127.0.0.1:<port>) intercepts
       the proxy call. We explicitly install a no-op ProxyHandler so urllib
       bypasses the system proxy.
    2. gpt-image-2 single image generation takes 60-90 seconds. Default
       urllib timeout (120s) is too tight on first call; we set 300s.

This is a template. Replace BASE_URL with your actual proxy endpoint, and
remove the trailing /v1 if your proxy already includes it.
"""
import base64
import json
import os
import sys
import urllib.request
from urllib.request import ProxyHandler, build_opener, install_opener

# Bypass any system HTTP/HTTPS proxy that would intercept this call
install_opener(build_opener(ProxyHandler({})))

# === REPLACE THESE BEFORE USE =====================================
DEFAULT_BASE_URL = "https://api.<your-proxy-here>.com"
DEFAULT_KEY_FILE = os.path.join(
    os.environ.get("USERPROFILE", os.path.expanduser("~")),
    "Desktop",
    "openai_api.txt",
)
# ==================================================================

BASE_URL = os.environ.get("GENIMG_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
KEY_FILE = os.environ.get("GENIMG_KEY_FILE", DEFAULT_KEY_FILE)
TIMEOUT = 300


def load_key():
    """Read API key from first line of the key file."""
    with open(KEY_FILE, "r", encoding="utf-8") as f:
        return f.readline().strip()


def generate(out_path, prompt, size, model):
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "size": size,
        "n": 1,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/v1/images/generations",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {load_key()}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )

    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    data = (body.get("data") or [{}])[0]

    if "b64_json" in data:
        with open(out_path, "wb") as f:
            f.write(base64.b64decode(data["b64_json"]))
    elif "url" in data:
        with urllib.request.urlopen(data["url"], timeout=60) as r:
            with open(out_path, "wb") as f:
                f.write(r.read())
    else:
        raise SystemExit(
            f"unexpected response shape: {json.dumps(body, ensure_ascii=False)[:500]}"
        )


def main():
    if len(sys.argv) < 3:
        print("usage: genimg.py <out.png> '<prompt>' [size] [model]", file=sys.stderr)
        sys.exit(2)

    out = sys.argv[1]
    prompt = sys.argv[2]
    size = sys.argv[3] if len(sys.argv) > 3 else "1024x1024"
    # Default model name depends on your proxy's aliasing. OpenAI canonical
    # as of 2025 is "gpt-image-1"; some aggregators alias to "gpt-image-2"
    # or other names. Set the default below to whatever your provider
    # actually accepts on /v1/images/generations.
    model = sys.argv[4] if len(sys.argv) > 4 else "gpt-image-1"

    generate(out, prompt, size, model)
    print(out)


if __name__ == "__main__":
    main()
