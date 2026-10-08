#!/usr/bin/env python3
"""Cross-session lock for knowledge-vault note jobs.

The lock lives in Git's common directory, so all worktrees for this repository
observe the same owner. It is intentionally logical (not process-held): the
orchestrator keeps the returned token and releases it after final validation.
Stale or malformed locks are never removed automatically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


LOCK_NAME = "codex-note-integrator.lock"
META_NAME = "owner.json"
PHASES = ("verify-local", "graph-index", "log", "hot-latest", "validate", "manifest")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def emit(payload: dict, exit_code: int = 0) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    raise SystemExit(exit_code)


def git_common_dir(repo: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "not a git repository")
    return Path(result.stdout.strip()).resolve()


def paths(repo: Path) -> tuple[Path, Path]:
    lock_dir = git_common_dir(repo) / LOCK_NAME
    return lock_dir, lock_dir / META_NAME


def read_meta(meta_path: Path) -> dict | None:
    try:
        value = json.loads(meta_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, json.JSONDecodeError) as exc:
        return {"malformed": True, "error": str(exc)}
    return value if isinstance(value, dict) else {"malformed": True, "error": "metadata is not an object"}


def public_meta(metadata: dict | None) -> dict | None:
    if not metadata:
        return metadata
    return {key: value for key, value in metadata.items() if key not in {"token", "token_sha256"}}


def atomic_write(meta_path: Path, payload: dict) -> None:
    temp_path = meta_path.with_name(f"{META_NAME}.tmp-{uuid.uuid4().hex}")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp_path, meta_path)


def acquire(repo: Path, owner: str, job_id: str) -> None:
    lock_dir, meta_path = paths(repo)
    try:
        lock_dir.mkdir()
    except FileExistsError:
        emit({"ok": False, "error": "lock-held", "lock_path": str(lock_dir), "holder": public_meta(read_meta(meta_path))}, 2)

    token = uuid.uuid4().hex
    timestamp = now_iso()
    metadata = {
        "schema": "v1",
        "token_sha256": hashlib.sha256(token.encode("ascii")).hexdigest(),
        "owner": owner,
        "job_id": job_id,
        "acquired_at": timestamp,
        "heartbeat_at": timestamp,
        "items": {},
    }
    try:
        atomic_write(meta_path, metadata)
    except Exception:
        try:
            lock_dir.rmdir()
        except OSError:
            pass
        raise
    emit({"ok": True, "token": token, "lock_path": str(lock_dir), "owner": owner, "job_id": job_id})


def require_token(meta_path: Path, token: str) -> dict:
    metadata = read_meta(meta_path)
    if not metadata:
        emit({"ok": False, "error": "lock-not-found", "lock_path": str(meta_path.parent)}, 2)
    if metadata.get("malformed"):
        emit({"ok": False, "error": "lock-malformed", "lock_path": str(meta_path.parent), "holder": public_meta(metadata)}, 2)
    token_hash = hashlib.sha256(token.encode("ascii")).hexdigest()
    if metadata.get("token_sha256") != token_hash:
        emit({"ok": False, "error": "token-mismatch", "lock_path": str(meta_path.parent), "holder": public_meta(metadata)}, 2)
    return metadata


def refresh(repo: Path, token: str) -> None:
    lock_dir, meta_path = paths(repo)
    metadata = require_token(meta_path, token)
    metadata["heartbeat_at"] = now_iso()
    atomic_write(meta_path, metadata)
    emit({"ok": True, "lock_path": str(lock_dir), "heartbeat_at": metadata["heartbeat_at"]})


def expect_item(repo: Path, token: str, item_id: str) -> None:
    lock_dir, meta_path = paths(repo)
    metadata = require_token(meta_path, token)
    items = metadata.setdefault("items", {})
    if item_id in items:
        emit({"ok": False, "error": "item-already-expected", "item_id": item_id}, 2)
    timestamp = now_iso()
    items[item_id] = {"registered_at": timestamp, "phases": {}}
    metadata["heartbeat_at"] = timestamp
    atomic_write(meta_path, metadata)
    emit({"ok": True, "lock_path": str(lock_dir), "item_id": item_id, "registered_at": timestamp})


def close_item(repo: Path, token: str, item_id: str, outcome: str, detail: str) -> None:
    lock_dir, meta_path = paths(repo)
    metadata = require_token(meta_path, token)
    item = metadata.setdefault("items", {}).get(item_id)
    if not item:
        emit({"ok": False, "error": "item-not-expected", "item_id": item_id}, 2)
    if item.get("phases"):
        emit({"ok": False, "error": "integration-already-started", "item_id": item_id}, 2)
    timestamp = now_iso()
    item["terminal_outcome"] = outcome
    item["terminal_detail"] = detail
    item["updated_at"] = timestamp
    metadata["heartbeat_at"] = timestamp
    atomic_write(meta_path, metadata)
    emit({"ok": True, "lock_path": str(lock_dir), "item_id": item_id, "outcome": outcome, "updated_at": timestamp})


def checkpoint(repo: Path, token: str, item_id: str, phase: str, state: str, detail: str | None) -> None:
    lock_dir, meta_path = paths(repo)
    metadata = require_token(meta_path, token)
    items = metadata.setdefault("items", {})
    item = items.get(item_id)
    if not item:
        emit({"ok": False, "error": "item-not-expected", "item_id": item_id}, 2)
    if item.get("terminal_outcome"):
        emit({"ok": False, "error": "item-already-closed", "item_id": item_id}, 2)
    if not isinstance(item, dict) or not isinstance(item.get("phases"), dict):
        emit({"ok": False, "error": "invalid-checkpoint-history", "item_id": item_id}, 2)
    phases = item["phases"]
    phase_index = PHASES.index(phase)
    for previous in PHASES[:phase_index]:
        if phases.get(previous, {}).get("state") != "done":
            emit({"ok": False, "error": "previous-phase-not-done", "item_id": item_id, "phase": phase, "previous": previous}, 2)
    if any(later in phases for later in PHASES[phase_index + 1 :]):
        emit({"ok": False, "error": "later-phase-already-recorded", "item_id": item_id, "phase": phase}, 2)

    timestamp = now_iso()
    current = phases.get(phase)
    if state == "started":
        if current and current.get("state") == "done":
            emit({"ok": False, "error": "phase-already-done", "item_id": item_id, "phase": phase}, 2)
        phases[phase] = {"state": "started", "started_at": current.get("started_at", timestamp) if current else timestamp}
    else:
        if not current or current.get("state") != "started":
            emit({"ok": False, "error": "phase-not-started", "item_id": item_id, "phase": phase}, 2)
        current["state"] = "done"
        current["done_at"] = timestamp
        phases[phase] = current
    if detail:
        phases[phase]["detail"] = detail
    item["last_phase"] = phase
    item["last_state"] = state
    item["updated_at"] = timestamp
    metadata["heartbeat_at"] = timestamp
    atomic_write(meta_path, metadata)
    emit({"ok": True, "lock_path": str(lock_dir), "item_id": item_id, "phase": phase, "state": state, "updated_at": timestamp})


def release(repo: Path, token: str) -> None:
    lock_dir, meta_path = paths(repo)
    metadata = require_token(meta_path, token)
    incomplete = []
    for item_id, item in metadata.get("items", {}).items():
        if isinstance(item, dict) and item.get("terminal_outcome") in {"duplicate", "blocked", "cancelled"}:
            continue
        manifest = item.get("phases", {}).get("manifest", {}) if isinstance(item, dict) else {}
        if manifest.get("state") != "done":
            incomplete.append(item_id)
    if incomplete:
        emit({"ok": False, "error": "integration-items-incomplete", "lock_path": str(lock_dir), "items": incomplete}, 2)
    unexpected = []
    temporary = []
    for entry in lock_dir.iterdir():
        if entry == meta_path:
            continue
        if entry.is_file() and entry.name.startswith(f"{META_NAME}.tmp-"):
            temporary.append(entry)
        else:
            unexpected.append(entry.name)
    if unexpected:
        emit({"ok": False, "error": "lock-directory-has-unexpected-entries", "lock_path": str(lock_dir), "entries": unexpected}, 2)
    for entry in temporary:
        entry.unlink()
    meta_path.unlink()
    try:
        lock_dir.rmdir()
    except OSError as exc:
        if not meta_path.exists():
            atomic_write(meta_path, metadata)
        emit({"ok": False, "error": "lock-directory-not-empty", "lock_path": str(lock_dir), "detail": str(exc)}, 2)
    emit({"ok": True, "released": True, "owner": metadata.get("owner"), "job_id": metadata.get("job_id")})


def status(repo: Path) -> None:
    lock_dir, meta_path = paths(repo)
    if not lock_dir.exists():
        emit({"ok": True, "locked": False, "lock_path": str(lock_dir)})
    emit({"ok": True, "locked": True, "lock_path": str(lock_dir), "holder": public_meta(read_meta(meta_path))})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="Any path inside the target Git worktree")
    subparsers = parser.add_subparsers(dest="command", required=True)

    acquire_parser = subparsers.add_parser("acquire")
    acquire_parser.add_argument("--owner", required=True)
    acquire_parser.add_argument("--job-id", required=True)

    refresh_parser = subparsers.add_parser("refresh")
    refresh_parser.add_argument("--token", required=True)

    expect_parser = subparsers.add_parser("expect")
    expect_parser.add_argument("--token", required=True)
    expect_parser.add_argument("--item-id", required=True)

    close_parser = subparsers.add_parser("close-item")
    close_parser.add_argument("--token", required=True)
    close_parser.add_argument("--item-id", required=True)
    close_parser.add_argument("--outcome", required=True, choices=["duplicate", "blocked", "cancelled"])
    close_parser.add_argument("--detail", required=True)

    release_parser = subparsers.add_parser("release")
    release_parser.add_argument("--token", required=True)

    checkpoint_parser = subparsers.add_parser("checkpoint")
    checkpoint_parser.add_argument("--token", required=True)
    checkpoint_parser.add_argument("--item-id", required=True)
    checkpoint_parser.add_argument(
        "--phase",
        required=True,
        choices=PHASES,
    )
    checkpoint_parser.add_argument("--state", required=True, choices=["started", "done"])
    checkpoint_parser.add_argument("--detail")

    subparsers.add_parser("status")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    repo = Path(args.repo).resolve()
    try:
        if args.command == "acquire":
            acquire(repo, args.owner, args.job_id)
        if args.command == "refresh":
            refresh(repo, args.token)
        if args.command == "expect":
            expect_item(repo, args.token, args.item_id)
        if args.command == "close-item":
            close_item(repo, args.token, args.item_id, args.outcome, args.detail)
        if args.command == "release":
            release(repo, args.token)
        if args.command == "checkpoint":
            checkpoint(repo, args.token, args.item_id, args.phase, args.state, args.detail)
        if args.command == "status":
            status(repo)
    except RuntimeError as exc:
        emit({"ok": False, "error": str(exc)}, 1)


if __name__ == "__main__":
    main()
