"""Reproduce the curated immutable upstream snapshot; no runtime credentials."""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
from pathlib import Path
import time
import urllib.request
import urllib.parse

REVISION = "b4efe3ddf237a97a42880164759162f8e2412f2f"
REPO = "https://github.com/hugohe3/ppt-master"
TREE_SHA = "b6a78cdb638468dfe7406c78f6bb6c42c1dec4d2"
ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "vendor/ppt-master/skills/ppt-master"
OMITTED = ["templates/icons/** SVG assets", "templates/sounds/** audio assets", "references/ai-image-comparison/** image examples", "scripts/tests/**", "scripts/source_to_md/web_to_md.py (WorkBuddy connector owns web/WeChat capture)", ".env.example (configure only required features locally)"]

def fetch(url: str) -> bytes:
    error = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=45) as response:
                return response.read()
        except Exception as exc:
            error = exc
            time.sleep(attempt + 1)
    raise RuntimeError(f"Failed to fetch {url}") from error

def selected(path: str) -> bool:
    if path.startswith("scripts/tests/") or path == "scripts/source_to_md/web_to_md.py" or path == ".env.example":
        return False
    if path.startswith("templates/icons/"):
        return path.endswith((".md", ".json", "LICENSE", "LICENSE.txt"))
    if path.startswith("templates/sounds/"):
        return path.endswith((".md", ".json", ".txt"))
    if path.startswith("references/ai-image-comparison/"):
        return path.endswith(".md")
    return True

def main() -> None:
    tree = json.loads(fetch(f"https://api.github.com/repos/hugohe3/ppt-master/git/trees/{TREE_SHA}?recursive=1"))
    if tree.get("truncated"):
        raise RuntimeError("GitHub returned a truncated source tree")
    files = [row for row in tree["tree"] if row["type"] == "blob" and selected(row["path"])]
    DEST.mkdir(parents=True, exist_ok=True)

    def copy(row: dict) -> tuple[str, str]:
        path = DEST / row["path"]
        if path.is_file():
            data = path.read_bytes()
            blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
            if blob == row["sha"]:
                return row["path"], hashlib.sha256(data).hexdigest()
            raise RuntimeError(f"Existing snapshot differs: {path}")
        encoded_path = urllib.parse.quote(row['path'], safe='/')
        data = fetch(f"https://raw.githubusercontent.com/hugohe3/ppt-master/{REVISION}/skills/ppt-master/{encoded_path}")
        blob = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if blob != row["sha"]:
            raise RuntimeError(f"Upstream blob integrity mismatch: {row['path']}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return row["path"], hashlib.sha256(data).hexdigest()

    hashes = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        for index, (path, digest) in enumerate(pool.map(copy, files), start=1):
            hashes[f"skills/ppt-master/{path}"] = digest
            if index % 100 == 0:
                print(f"Verified {index}/{len(files)} files", flush=True)
    vendor = DEST.parents[1]
    for filename in ["LICENSE", "README.md", "README_CN.md", "requirements.txt"]:
        path = vendor / filename
        if not path.exists():
            path.write_bytes(fetch(f"https://raw.githubusercontent.com/hugohe3/ppt-master/{REVISION}/{filename}"))
        hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    (vendor / "snapshot.json").write_text(json.dumps({"repository": REPO, "revision": REVISION, "captured": "2026-10-09", "license": "MIT", "selection": "Skill text, all runtime scripts except connector-owned web capture, templates and charts; optional assets omitted", "omitted": OMITTED, "files_sha256": dict(sorted(hashes.items()))}, indent=2) + "\n", encoding="utf-8")
    print(f"Snapshot complete: {len(hashes)} immutable files", flush=True)

if __name__ == "__main__":
    main()
