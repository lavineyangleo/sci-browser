from __future__ import annotations

import json
import sys
from pathlib import Path

from cookie_core import validate_snapshot


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/validate.py <snapshot.json>")
        return 2
    try:
        data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    errors = validate_snapshot(data) if isinstance(data, dict) else ["snapshot must be a JSON object"]
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
