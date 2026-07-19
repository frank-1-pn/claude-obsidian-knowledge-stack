#!/usr/bin/env python
"""Image-to-image / style transfer via OpenAI-compatible /v1/images/edits (gpt-image-2).
Usage: python genimg_edit.py <out.png> <input_image> --prompt-file <p.txt> [size]
Key + base URL resolution mirrors genimg.py. Never echoes the key."""
import sys, os, json, time, base64, urllib.request, urllib.error, mimetypes
from pathlib import Path

_KEY_CANDIDATES = [os.environ.get("GENIMG_KEY_FILE"),
                   str(Path.home() / ".secrets" / "vectorengine_key.txt"),
                   str(Path.home() / "Desktop" / "openai_api.txt")]
BASE_URL = os.environ.get("GENIMG_BASE_URL", "https://api.your-relay.example")
ENDPOINT = f"{BASE_URL}/v1/images/edits"
urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))

def key():
    for c in _KEY_CANDIDATES:
        if c and Path(c).exists():
            return Path(c).read_text(encoding="utf-8").splitlines()[0].strip()
    print("no key file", file=sys.stderr); sys.exit(1)

def multipart(fields, files):
    b = "----genimgedit" + str(int(time.time()))
    body = bytearray()
    for k, v in fields.items():
        body += f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for k, path in files.items():
        fn = os.path.basename(path)
        ct = mimetypes.guess_type(fn)[0] or "application/octet-stream"
        body += f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{fn}\"\r\n".encode()
        body += f"Content-Type: {ct}\r\n\r\n".encode()
        body += Path(path).read_bytes() + b"\r\n"
    body += f"--{b}--\r\n".encode()
    return bytes(body), b

def main():
    a = list(sys.argv[1:])
    pf = None
    if "--prompt-file" in a:
        i = a.index("--prompt-file"); pf = a[i+1]; del a[i:i+2]
    out, img = Path(a[0]), a[1]
    size = a[2] if len(a) > 2 else "1536x1024"
    prompt = Path(pf).read_text(encoding="utf-8").strip()
    fields = {"model": "gpt-image-2", "prompt": prompt, "size": size, "n": "1"}
    data, boundary = multipart(fields, {"image": img})
    req = urllib.request.Request(ENDPOINT, data=data, method="POST", headers={
        "Authorization": f"Bearer {key()}",
        "Content-Type": f"multipart/form-data; boundary={boundary}"})
    print(f"[edit] {out.name} <- {os.path.basename(img)} (size={size})...", file=sys.stderr)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                body = json.loads(r.read().decode())
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode()[:600]
            if e.code in (429,500,502,503,504) and attempt < 2:
                print(f"[edit] HTTP {e.code} retry in {(2**attempt)*3}s", file=sys.stderr); time.sleep((2**attempt)*3); continue
            print(f"[edit] API error {e.code}: {msg}", file=sys.stderr); sys.exit(2)
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 2:
                print(f"[edit] net err retry: {getattr(e,'reason',e)}", file=sys.stderr); time.sleep((2**attempt)*3); continue
            print(f"[edit] net error: {getattr(e,'reason',e)}", file=sys.stderr); sys.exit(2)
    item = (body.get("data") or [{}])[0]
    if item.get("b64_json"):
        out.write_bytes(base64.b64decode(item["b64_json"]))
    elif item.get("url"):
        with urllib.request.urlopen(item["url"], timeout=120) as rr:
            out.write_bytes(rr.read())
    else:
        print("[edit] no image in resp: " + json.dumps(body)[:400], file=sys.stderr); sys.exit(3)
    print(f"[edit] saved {out} ({out.stat().st_size} bytes)", file=sys.stderr); print(str(out))

if __name__ == "__main__":
    main()
