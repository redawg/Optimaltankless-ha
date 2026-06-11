#!/usr/bin/env python3
"""Probe Optimal auth endpoints (password + social)."""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

import aiohttp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components"))

HWBE = "https://hwbe.itsoptimal.com"
BFF = "https://bff.itsoptimal.com"

USERNAME = os.environ.get("OPTIMAL_USERNAME", "")
PASSWORD = os.environ.get("OPTIMAL_PASSWORD", "")


async def try_post(session: aiohttp.ClientSession, base: str, path: str, payload: dict) -> None:
    url = f"{base}{path}"
    async with session.post(url, json=payload) as resp:
        text = await resp.text()
        print(f"\nPOST {url}")
        print(f"  status={resp.status}")
        print(f"  body={text[:1500]}")


async def try_get(session: aiohttp.ClientSession, base: str, path: str, token: str | None = None) -> None:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{base}{path}"
    async with session.get(url, headers=headers) as resp:
        text = await resp.text()
        print(f"\nGET {url}")
        print(f"  status={resp.status}")
        print(f"  body={text[:1500]}")


async def main() -> None:
    if not USERNAME or not PASSWORD:
        raise SystemExit("Set OPTIMAL_USERNAME and OPTIMAL_PASSWORD")

    async with aiohttp.ClientSession() as session:
        for base in (HWBE, BFF):
            await try_post(
                session,
                base,
                "/auth/login",
                {"username": USERNAME, "password": PASSWORD},
            )
            await try_post(
                session,
                base,
                "/auth/sign-in/social",
                {"email": USERNAME, "provider": "google"},
            )
            await try_post(
                session,
                base,
                "/auth/sign-in/social",
                {"username": USERNAME, "provider": "google"},
            )

        # Probe BFF paths that appeared in the mobile bundle
        for path in (
            "/auth/sign-in/social",
            "/client/device/registry/authenticateDevice",
        ):
            await try_get(session, BFF, path)


def scan_bundle() -> None:
    bundle = ROOT / "tools" / "apk" / "apk_unpacked" / "assets" / "index.android.bundle"
    if not bundle.exists():
        print("Bundle not found")
        return
    data = bundle.read_bytes()
    patterns = [
        b"sign-in/social",
        b"signInWithGoogle",
        b"GoogleSignin",
        b"idToken",
        b"firebase",
        b"identitytoolkit",
        b"securetoken",
        b"/auth/",
    ]
    print("\n=== Bundle auth strings ===")
    for pat in patterns:
        print(f"{pat.decode()}: {data.count(pat)}")
    for m in re.finditer(rb"/auth/[a-zA-Z0-9_/-]{3,60}", data):
        s = m.group(0).decode("utf-8", "ignore")
        if "sign" in s or "social" in s or "login" in s or "google" in s.lower():
            print(" path:", s)


if __name__ == "__main__":
    scan_bundle()
    asyncio.run(main())
