#!/usr/bin/env python3
"""Download and parse the Optimal HWBE Swagger spec."""

from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "tools" / "apk" / "hwbe_swagger_init.js"
OUT_PATH = ROOT / "docs" / "openapi.json"


def main() -> None:
    if not JS_PATH.exists():
        JS_PATH.write_text(
            urllib.request.urlopen(
                "https://hwbe.itsoptimal.com/api/swagger-ui-init.js"
            ).read().decode(),
            encoding="utf-8",
        )

    text = JS_PATH.read_text(encoding="utf-8")
    match = re.search(
        r'"swaggerDoc":\s*(\{.*\})\s*,\s*"customOptions"',
        text,
        re.DOTALL,
    )
    if not match:
        raise SystemExit("Could not parse swaggerDoc from init JS")

    spec = json.loads(match.group(1))
    OUT_PATH.write_text(json.dumps(spec, indent=2), encoding="utf-8")

    print(f"Wrote {OUT_PATH}")
    print(f"Paths: {len(spec['paths'])}")
    for path in sorted(spec["paths"]):
        methods = ",".join(spec["paths"][path].keys())
        print(f"  {methods:12} {path}")

    print("\nSchemas:")
    for name in sorted(spec.get("components", {}).get("schemas", {})):
        print(f"  {name}")


if __name__ == "__main__":
    main()
