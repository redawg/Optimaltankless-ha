#!/usr/bin/env python3
"""Summarize URLs and auth headers from HTTP Toolkit / mitmproxy HAR exports.

Usage:
  python tools/analyze_har.py captures/session.har
  python tools/analyze_har.py captures/*.har
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse


def analyze_har(path: Path) -> None:
    """Print a concise summary of one HAR file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("log", {}).get("entries", [])

    hosts: dict[str, int] = defaultdict(int)
    endpoints: list[tuple[str, str, int]] = []

    for entry in entries:
        req = entry.get("request", {})
        url = req.get("url", "")
        method = req.get("method", "?")
        status = entry.get("response", {}).get("status", 0)
        parsed = urlparse(url)
        hosts[parsed.netloc] += 1
        if any(
            token in parsed.netloc
            for token in ("itsoptimal", "optimal", "amazonaws", "firebase", "googleapis")
        ) or "/api" in parsed.path:
            endpoints.append((method, url, status))

    print(f"\n=== {path.name} ({len(entries)} requests) ===")
    print("\nTop hosts:")
    for host, count in sorted(hosts.items(), key=lambda x: -x[1])[:20]:
        print(f"  {count:4d}  {host}")

    if endpoints:
        print("\nLikely API calls:")
        for method, url, status in endpoints:
            print(f"  {status} {method} {url}")
    else:
        print("\nNo obvious API hosts matched — review full HAR manually.")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 1

    for arg in argv[1:]:
        for path in sorted(Path(".").glob(arg)) if "*" in arg else [Path(arg)]:
            if path.is_file():
                analyze_har(path)
            else:
                print(f"Skip missing file: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
