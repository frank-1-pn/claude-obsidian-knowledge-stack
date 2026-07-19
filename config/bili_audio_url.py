#!/usr/bin/env python
"""Fetch a Bilibili video's best audio dash URL as a GUEST (no login).

Why this exists: yt-dlp's Bilibili extractor returns HTTP 412 on the playurl
endpoint (stale gaia/w_webid signing) — this happens even from a clean
domestic IP with a full Chrome cookie export. bilibili-api-python carries
current signing and works as a plain guest. Prints the best-bandwidth audio
baseUrl to stdout.

Usage:
    python bili_audio_url.py <BVID>
Then download (the CDN requires a Referer header or it 403s):
    curl -H "Referer: https://www.bilibili.com" -o a.m4a "<url>"
    python ~/.claude/scripts/transcribe.py a.m4a
Requires: pip install bilibili-api-python
"""
import asyncio
import sys

from bilibili_api import video


async def main(bvid: str) -> int:
    v = video.Video(bvid=bvid)
    data = await v.get_download_url(0)
    dash = data.get("dash")
    if not dash or not dash.get("audio"):
        print("NO_DASH_AUDIO", file=sys.stderr)
        return 1
    best = max(dash["audio"], key=lambda a: a.get("bandwidth", 0))
    print(best.get("baseUrl") or best.get("base_url"))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: bili_audio_url.py <BVID>", file=sys.stderr)
        sys.exit(2)
    sys.exit(asyncio.run(main(sys.argv[1])))
