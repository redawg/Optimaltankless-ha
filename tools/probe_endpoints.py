#!/usr/bin/env python3
"""Probe Optimal HWBE/BFF auth and client endpoints."""

from __future__ import annotations

import asyncio
import json
import os
import sys

import aiohttp

HWBE = "https://hwbe.itsoptimal.com"
BFF = "https://bff.itsoptimal.com"


async def probe_login(base: str, username: str, password: str) -> None:
    url = f"{base}/auth/login"
    payload = {"username": username, "password": password}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            text = await resp.text()
            print(f"\nPOST {url}")
            print(f"Status: {resp.status}")
            print(text[:2000])


async def probe_authed(base: str, token: str) -> None:
    headers = {"Authorization": f"Bearer {token}"}
    paths = [
        "/auth/profile",
        "/client/device/registry",
        "/admin/device/registry",
    ]
    async with aiohttp.ClientSession(headers=headers) as session:
        for path in paths:
            for method in ("GET", "POST"):
                if method == "POST" and path != "/client/device/registry":
                    continue
                async with session.request(method, f"{base}{path}") as resp:
                    text = await resp.text()
                    print(f"\n{method} {base}{path} -> {resp.status}")
                    print(text[:1000])


async def main() -> None:
    username = os.environ.get("OPTIMAL_USERNAME") or os.environ.get("OPTIMAL_EMAIL", "")
    password = os.environ.get("OPTIMAL_PASSWORD", "")
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        if not username or not password:
            raise SystemExit("Set OPTIMAL_USERNAME/OPTIMAL_EMAIL and OPTIMAL_PASSWORD")
        await probe_login(HWBE, username, password)
        await probe_login(BFF, username, password)
        return

    token = os.environ.get("OPTIMAL_TOKEN", "")
    if not token:
        raise SystemExit("Set OPTIMAL_TOKEN or run: probe_endpoints.py login")
    await probe_authed(HWBE, token)
    await probe_authed(BFF, token)


if __name__ == "__main__":
    asyncio.run(main())
