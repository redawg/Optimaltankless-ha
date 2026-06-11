#!/usr/bin/env python3
"""Extract URLs, API paths, and cloud config from the Optimal Android APK."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APK_DIR = ROOT / "tools" / "apk"
BASE_APK = APK_DIR / "xapk_extracted" / "com.itsoptimal.optimalapp.apk"
OUT = ROOT / "tools" / "apk" / "extracted_strings.txt"

URL_RE = re.compile(
    rb"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]{4,200}"
)
HOST_RE = re.compile(
    rb"(?:api|auth|cloud|iot|mqtt|firebase|amazonaws|azure|googleapis)[A-Za-z0-9._-]{0,80}"
)
PATH_RE = re.compile(rb"/(?:api|v1|v2|auth|devices|users|login|refresh)[A-Za-z0-9/_-]{0,120}")


def read_zip_strings(path: Path) -> bytes:
    data = b""
    with zipfile.ZipFile(path, "r") as zf:
        for name in zf.namelist():
            if name.endswith(
                (
                    ".dex",
                    ".xml",
                    ".json",
                    ".properties",
                    ".txt",
                    ".html",
                    ".js",
                    ".kotlin_module",
                )
            ) or "assets" in name:
                try:
                    data += zf.read(name)
                except Exception:
                    pass
    return data


def unique_sorted(items: set[str]) -> list[str]:
    return sorted(items, key=str.lower)


def main() -> None:
    if not BASE_APK.exists():
        raise SystemExit(f"Missing APK: {BASE_APK}")

    blobs = [read_zip_strings(BASE_APK)]
    for split in (APK_DIR / "xapk_extracted").glob("config.*.apk"):
        blobs.append(read_zip_strings(split))

    data = b"".join(blobs)
    urls = {m.group(0).decode("utf-8", "ignore") for m in URL_RE.finditer(data)}
    hosts = {m.group(0).decode("utf-8", "ignore") for m in HOST_RE.finditer(data)}
    paths = {m.group(0).decode("utf-8", "ignore") for m in PATH_RE.finditer(data)}

    # Also pull readable ASCII runs that mention optimal/itsoptimal
    keyword_lines: set[str] = set()
    for match in re.finditer(rb"[ -~]{8,200}", data):
        s = match.group(0).decode("utf-8", "ignore")
        lower = s.lower()
        if any(k in lower for k in ("itsoptimal", "optimal", "vacation", "firebase", "cognito", "mqtt", "graphql")):
            keyword_lines.add(s)

    lines: list[str] = []
    lines.append("=== URLs ===")
    lines.extend(unique_sorted(urls))
    lines.append("\n=== Host-like tokens ===")
    lines.extend(unique_sorted(hosts))
    lines.append("\n=== API-like paths ===")
    lines.extend(unique_sorted(paths))
    lines.append("\n=== Keyword strings ===")
    lines.extend(unique_sorted(keyword_lines))

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} ({len(lines)} lines)")
    print("\nTop URLs:")
    for url in unique_sorted(urls)[:40]:
        print(f"  {url}")


if __name__ == "__main__":
    main()
