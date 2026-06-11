#!/usr/bin/env python3
"""Deploy Optimaltankless to Forest Home via HACS WebSocket + config flow."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HA_URL = os.environ.get("HA_URL", "http://172.16.255.250:8123").rstrip("/")
HA_WS = os.environ.get("HA_WS", HA_URL.replace("http://", "ws://").replace("https://", "wss://") + "/api/websocket")
HA_TOKEN = os.environ.get("HA_TOKEN", "")
REPO = os.environ.get("HACS_REPO", "redawg/Optimaltankless-ha")
SERIAL = os.environ.get("OPTIMAL_SERIAL", "1212230005")
DEVICE_NAME = os.environ.get("OPTIMAL_DEVICE_NAME", "Main water heater")


def api_request(method: str, path: str, data: dict | None = None) -> tuple[int, object]:
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(HA_URL + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        return exc.code, parsed


async def ws_call(ws, msg_id: int, payload: dict) -> dict:
    """Send a WS command and wait for the matching response id."""
    await ws.send_json({"id": msg_id, **payload})
    while True:
        msg = await ws.receive_json()
        if msg.get("id") == msg_id:
            return msg


async def hacs_deploy() -> bool:
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(HA_WS, timeout=30) as ws:
            msg = await ws.receive_json()
            if msg.get("type") != "auth_required":
                print("Unexpected WS hello:", msg)
                return False

            await ws.send_json({"type": "auth", "access_token": HA_TOKEN})
            msg = await ws.receive_json()
            if msg.get("type") != "auth_ok":
                print("WS auth failed:", msg)
                return False

            msg_id = 1
            msg = await ws_call(
                ws,
                msg_id,
                {
                    "type": "hacs/repositories/add",
                    "repository": REPO,
                    "category": "integration",
                },
            )
            print(f"HACS add repo: success={msg.get('success')} error={msg.get('error')}")

            msg_id += 1
            msg = await ws_call(ws, msg_id, {"type": "hacs/repositories/list"})
            repos = msg.get("result") or []
            target = next(
                (
                    r
                    for r in repos
                    if r.get("full_name") == REPO
                    or REPO.lower() in str(r.get("full_name", "")).lower()
                ),
                None,
            )
            if not target:
                print("Repository not found in HACS after add")
                return False

            repo_id = str(target["id"])
            print(f"Found HACS repo id={repo_id} installed={target.get('installed')}")

            msg_id += 1
            msg = await ws_call(
                ws,
                msg_id,
                {
                    "type": "hacs/repository/download",
                    "repository": repo_id,
                },
            )
            print(f"HACS download: success={msg.get('success')} error={msg.get('error')}")
            if not msg.get("success"):
                return False

            msg_id += 1
            await ws_call(
                ws,
                msg_id,
                {
                    "type": "call_service",
                    "domain": "homeassistant",
                    "service": "restart",
                    "service_data": {},
                },
            )
            print("HA restart requested")
            return True


def wait_for_ha(timeout: int = 180) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            code, data = api_request("GET", "/api/")
            if code == 200:
                print("HA is back online:", data)
                return True
        except Exception:
            pass
        time.sleep(5)
    return False


def configure_integration() -> str | None:
    code, entries = api_request("GET", "/api/config/config_entries/entry")
    if code != 200 or not isinstance(entries, list):
        print("Failed listing entries:", code, entries)
        return None

    for entry in entries:
        if entry.get("domain") == "optimaltankless":
            print("Already configured:", entry.get("entry_id"), entry.get("title"))
            return entry["entry_id"]

    code, flow = api_request(
        "POST",
        "/api/config/config_entries/flow",
        {"handler": "optimaltankless", "show_advanced_options": False},
    )
    print("Start flow:", code, json.dumps(flow, indent=2)[:1500])
    if code not in (200, 201) or not isinstance(flow, dict):
        return None

    flow_id = flow["flow_id"]
    code, flow = api_request(
        "POST",
        f"/api/config/config_entries/flow/{flow_id}",
        {"serial_number": SERIAL, "device_name": DEVICE_NAME},
    )
    print("Submit serial:", code, json.dumps(flow, indent=2)[:1500])
    if code not in (200, 201) or not isinstance(flow, dict):
        return None

    if flow.get("type") == "create_entry":
        return flow.get("result", {}).get("entry_id")

    print("Unexpected flow result")
    return None


def list_entities() -> None:
    code, states = api_request("GET", "/api/states")
    if code != 200 or not isinstance(states, list):
        print("Failed to list states:", code, states)
        return
    entities = sorted(s["entity_id"] for s in states if "optimaltankless" in s["entity_id"] or "opti" in s["entity_id"].lower())
    print(f"Entities ({len(entities)}):")
    for entity in entities:
        print(" ", entity)


def main() -> int:
    if not HA_TOKEN:
        print("Set HA_TOKEN to a Forest Home long-lived access token.", file=sys.stderr)
        return 1

    print(f"Deploying {REPO} to {HA_URL}")
    if not asyncio.run(hacs_deploy()):
        print("HACS deploy failed")
        return 1

    print("Waiting for HA restart...")
    if not wait_for_ha():
        print("HA did not come back in time")
        return 1

    entry_id = configure_integration()
    if not entry_id:
        print("Integration setup failed")
        return 1

    print("Configured entry:", entry_id)
    time.sleep(10)
    list_entities()
    print("DEPLOY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
