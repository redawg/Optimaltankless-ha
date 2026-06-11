#!/usr/bin/env python3
"""Extract Firebase and auth-related strings from Optimal APK."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APK = ROOT / "tools" / "apk" / "xapk_extracted" / "com.itsoptimal.optimalapp.apk"
BUNDLE = ROOT / "tools" / "apk" / "apk_unpacked" / "assets" / "index.android.bundle"


def strings_from(data: bytes, min_len: int = 6) -> list[str]:
    out: list[str] = []
    cur = bytearray()
    for b in data:
        if 32 <= b < 127:
            cur.append(b)
        else:
            if len(cur) >= min_len:
                out.append(cur.decode("ascii", "ignore"))
            cur.clear()
    if len(cur) >= min_len:
        out.append(cur.decode("ascii", "ignore"))
    return out


def main() -> None:
    blobs: list[bytes] = []
    if BUNDLE.exists():
        blobs.append(BUNDLE.read_bytes())
    if APK.exists():
        with zipfile.ZipFile(APK) as zf:
            for name in zf.namelist():
                if name.endswith((".xml", ".json", ".properties")) or "google-services" in name:
                    blobs.append(zf.read(name))

    data = b"".join(blobs)
    all_strings = strings_from(data)

    keywords = (
        "firebase",
        "google",
        "idToken",
        "id_token",
        "sign-in",
        "signIn",
        "social",
        "oauth",
        "apiKey",
        "projectId",
        "authDomain",
        "securetoken",
        "identitytoolkit",
        "bff",
        "hwbe",
        "provider",
        "credential",
    )

    print("=== Matching strings ===")
    seen: set[str] = set()
    for s in all_strings:
        low = s.lower()
        if any(k.lower() in low for k in keywords) and s not in seen and len(s) < 200:
            seen.add(s)
            print(s)

    print("\n=== google-services.json ===")
    if APK.exists():
        with zipfile.ZipFile(APK) as zf:
            for name in zf.namelist():
                if "google-services" in name:
                    print(name)
                    print(zf.read(name).decode("utf-8", "ignore")[:4000])


if __name__ == "__main__":
    main()
