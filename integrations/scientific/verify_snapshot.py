#!/usr/bin/env python3
"""Verify selected upstream bytes and license texts without network/dependencies."""
import ast
import hashlib
import json
from pathlib import Path


def verify() -> dict:
    root = Path(__file__).resolve().parent
    vendor = root.parents[1] / "vendor/scientific-agent-skills"
    lock = json.loads((root / "upstream-lock.json").read_text(encoding="utf-8"))
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    expected = lock["files"] + lock["additional_license_texts"]
    failures = []
    python_count = 0
    for entry in expected:
        path = (vendor / entry["path"]).resolve()
        if not path.is_relative_to(vendor.resolve()) or not path.is_file():
            failures.append(f"missing/invalid path: {entry['path']}")
            continue
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            failures.append(f"hash mismatch: {entry['path']}")
        if path.suffix == ".py":
            ast.parse(data.decode("utf-8"), filename=entry["path"])
            python_count += 1
    if catalog["count"] != len(catalog["skills"]) or set(lock["selection"]) != {row["name"] for row in catalog["skills"]}:
        failures.append("catalog/selection mismatch")
    for skill in catalog["skills"]:
        path = vendor / skill["upstream_path"]
        if not path.is_file() or f"name: {skill['name']}\n" not in path.read_text(encoding="utf-8"):
            failures.append(f"skill name/path mismatch: {skill['name']}")
    if failures:
        raise ValueError("\n".join(failures))
    return {"status": "verified", "skills": len(lock["selection"]),
            "hashed_files": len(expected), "python_ast_parsed": python_count,
            "upstream_revision": lock["revision"],
            "limits": "byte integrity and syntax only; not all skill/API scientific execution"}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
