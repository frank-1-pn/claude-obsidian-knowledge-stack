#!/usr/bin/env python
"""
Generate image via OpenAI-compatible API (relay or official) and save to PNG.

Usage:
    python genimg.py <output-path.png> "<prompt>" [size] [model]
    size:  1024x1024 (default) | 1024x1536 | 1536x1024 | auto
    model: gpt-image-2 (default, via vectorengine relay)

API key resolution (first that exists, never echoed):
    env GENIMG_KEY_FILE  >  %USERPROFILE%\\.secrets\\vectorengine_key.txt  >  legacy Desktop\\openai_api.txt
Base URL: https://api.vectorengine.cn (中转，绕过 OpenAI org verify); override with env GENIMG_BASE_URL.
Transient failures (429/5xx, timeouts, connection errors) are retried with backoff.
"""
import sys
import os
import json
import time
import base64
import urllib.request
import urllib.error
from pathlib import Path

# Key path resolution: env override > user-only .secrets dir > legacy Desktop (migration fallback).
_KEY_CANDIDATES = [
    os.environ.get("GENIMG_KEY_FILE"),
    str(Path.home() / ".secrets" / "vectorengine_key.txt"),
    r"C:\Users\ke\Desktop\openai_api.txt",
]
BASE_URL = os.environ.get("GENIMG_BASE_URL", "https://api.vectorengine.cn")
ENDPOINT = f"{BASE_URL}/v1/images/generations"

# Disable system proxies entirely — vectorengine relay is direct, proxy intercepts TLS.
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
urllib.request.install_opener(_opener)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def resolve_key_file():
    for c in _KEY_CANDIDATES:
        if c and Path(c).exists():
            return Path(c)
    return None


def _retry_after(err):
    try:
        return int(err.headers.get("Retry-After"))
    except (TypeError, ValueError, AttributeError):
        return None


def urlopen_retry(req, timeout, attempts=3):
    """urlopen with backoff on 429/5xx and network errors. Non-retryable HTTP
    errors (4xx other than 429) and the final attempt re-raise immediately."""
    last = None
    for i in range(attempts):
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code not in RETRYABLE_STATUS or i == attempts - 1:
                raise
            wait = _retry_after(e) or (2 ** i) * 3
            print(f"[genimg] HTTP {e.code}; retry {i + 1}/{attempts - 1} in {wait}s...", file=sys.stderr)
            time.sleep(wait)
            last = e
        except (urllib.error.URLError, TimeoutError) as e:
            if i == attempts - 1:
                raise
            wait = (2 ** i) * 3
            reason = getattr(e, "reason", e)
            print(f"[genimg] network error ({reason}); retry {i + 1}/{attempts - 1} in {wait}s...", file=sys.stderr)
            time.sleep(wait)
            last = e
    if last:
        raise last
    raise RuntimeError("urlopen_retry exhausted without result")


def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    out = Path(sys.argv[1])
    prompt = sys.argv[2]
    size = sys.argv[3] if len(sys.argv) > 3 else "1024x1024"
    model = sys.argv[4] if len(sys.argv) > 4 else "gpt-image-2"

    key_file = resolve_key_file()
    if not key_file:
        print(f"API key file not found in any of: {[c for c in _KEY_CANDIDATES if c]}", file=sys.stderr)
        sys.exit(1)

    # Key is on line 1 of the file (rest is documentation).
    key = key_file.read_text(encoding="utf-8").splitlines()[0].strip()

    out.parent.mkdir(parents=True, exist_ok=True)

    payload = {"model": model, "prompt": prompt, "size": size, "n": 1}
    if model == "dall-e-3":
        payload["quality"] = "standard"
        payload["response_format"] = "b64_json"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    print(f"[genimg] generating {out.name} (model={model}, size={size}, base={BASE_URL})...", file=sys.stderr)
    try:
        with urlopen_retry(req, timeout=300) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8"))
            print(f"[genimg] API error ({e.code}) after retries:", file=sys.stderr)
            print(json.dumps(err.get("error", err), indent=2, ensure_ascii=False), file=sys.stderr)
        except Exception:
            print(f"[genimg] HTTPError {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(2)
    except (urllib.error.URLError, TimeoutError) as e:
        reason = getattr(e, "reason", e)
        print(f"[genimg] network error after retries: {reason}", file=sys.stderr)
        sys.exit(2)

    if "data" not in body or not body["data"]:
        print("[genimg] no image data in response:", file=sys.stderr)
        print(json.dumps(body, indent=2, ensure_ascii=False)[:500], file=sys.stderr)
        sys.exit(3)

    item = body["data"][0]
    if item.get("b64_json"):
        out.write_bytes(base64.b64decode(item["b64_json"]))
    elif item.get("url"):
        with urlopen_retry(urllib.request.Request(item["url"]), timeout=60) as r:
            out.write_bytes(r.read())
    else:
        print("[genimg] no b64_json or url in data item", file=sys.stderr)
        sys.exit(4)

    size_bytes = out.stat().st_size
    print(f"[genimg] saved {out} ({size_bytes} bytes)", file=sys.stderr)
    print(str(out))


if __name__ == "__main__":
    main()
