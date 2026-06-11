#!/usr/bin/env python3
"""CLI for Optimal HWBE API (serial-number based)."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import aiohttp

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "optimaltankless"


def _load_api_module():
    pkg = types.ModuleType("optimaltankless")
    sys.modules["optimaltankless"] = pkg

    for name in ("const", "api"):
        path = COMPONENT / f"{name}.py"
        spec = importlib.util.spec_from_file_location(
            f"optimaltankless.{name}", path
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"optimaltankless.{name}"] = module
        spec.loader.exec_module(module)
        setattr(pkg, name, module)

    return sys.modules["optimaltankless.api"].OptimalTanklessAPI


OptimalTanklessAPI = _load_api_module()


async def run(command: str, serial: str | None, value: str | None) -> None:
    if not serial and command != "help":
        raise SystemExit("Serial number required")

    api = OptimalTanklessAPI(aiohttp.ClientSession())

    if command == "status":
        print(await api.async_get_device_status(serial))
        return

    if command == "command":
        print(await api.async_get_device_command(serial))
        return

    if command == "set-temp" and value:
        await api.async_set_temperature(serial, float(value))
        print("OK")
        return

    if command == "vacation-on":
        await api.async_set_vacation_mode(serial, True)
        print("OK")
        return

    if command == "vacation-off":
        await api.async_set_vacation_mode(serial, False)
        print("OK")
        return

    print("Usage: probe_api.py status|command|set-temp|vacation-on|vacation-off SERIAL [VALUE]")


async def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    serial = sys.argv[2] if len(sys.argv) > 2 else None
    value = sys.argv[3] if len(sys.argv) > 3 else None
    await run(command, serial, value)


if __name__ == "__main__":
    asyncio.run(main())
