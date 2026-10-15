from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA_VERSION = "1.0"
ALLOWED_SAMESITE = {None, "Strict", "Lax", "None"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_partition_key(value: Any) -> Any:
    if value in (None, "", {}):
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        top = value.get("topLevelSite") or value.get("top_level_site")
        cross = value.get("hasCrossSiteAncestor", value.get("has_cross_site_ancestor"))
        out: dict[str, Any] = {}
        if top:
            out["topLevelSite"] = str(top)
        if cross is not None:
            out["hasCrossSiteAncestor"] = bool(cross)
        return out or None
    return str(value)


def normalize_cookie(raw: Mapping[str, Any]) -> dict[str, Any]:
    expires_raw = raw.get("expires", raw.get("expirationDate"))
    try:
        expires = float(expires_raw) if expires_raw not in (None, "", -1, 0) else None
    except (TypeError, ValueError):
        expires = None
    if expires is not None and expires <= 0:
        expires = None

    same_site = raw.get("sameSite", raw.get("same_site"))
    if isinstance(same_site, str):
        same_site = {"strict": "Strict", "lax": "Lax", "none": "None"}.get(same_site.lower(), same_site)

    return {
        "name": str(raw.get("name") or ""),
        "value": str(raw.get("value") or ""),
        "domain": str(raw.get("domain") or "").lower(),
        "path": str(raw.get("path") or "/"),
        "expires": expires,
        "httpOnly": bool(raw.get("httpOnly", raw.get("http_only", False))),
        "secure": bool(raw.get("secure", False)),
        "sameSite": same_site if same_site in ALLOWED_SAMESITE else None,
        "session": expires is None,
        "partitionKey": normalize_partition_key(raw.get("partitionKey", raw.get("partition_key"))),
    }


def _partition_text(value: Any) -> str:
    if value is None:
        return ""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def cookie_key(cookie: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(cookie.get("name") or ""),
        str(cookie.get("domain") or "").lower(),
        str(cookie.get("path") or "/"),
        _partition_text(cookie.get("partitionKey")),
    )


def normalize_cookies(cookies: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out = [normalize_cookie(cookie) for cookie in cookies]
    out.sort(key=cookie_key)
    return out


def make_snapshot(url: str, cookies: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "sourceUrl": url,
        "capturedAt": now_iso(),
        "cookies": normalize_cookies(cookies),
    }


def validate_snapshot(snapshot: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if snapshot.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if not isinstance(snapshot.get("sourceUrl"), str) or not snapshot.get("sourceUrl"):
        errors.append("sourceUrl is required")
    cookies = snapshot.get("cookies")
    if not isinstance(cookies, list):
        return errors + ["cookies must be an array"]

    seen: set[tuple[str, str, str, str]] = set()
    for i, raw in enumerate(cookies):
        if not isinstance(raw, Mapping):
            errors.append(f"cookies[{i}] must be an object")
            continue
        cookie = normalize_cookie(raw)
        if not cookie["name"]:
            errors.append(f"cookies[{i}].name is required")
        if not cookie["domain"]:
            errors.append(f"cookies[{i}].domain is required")
        if not cookie["path"].startswith("/"):
            errors.append(f"cookies[{i}].path must start with /")
        if raw.get("sameSite") not in ALLOWED_SAMESITE:
            errors.append(f"cookies[{i}].sameSite is invalid")
        key = cookie_key(cookie)
        if key in seen:
            errors.append(f"duplicate cookie identity at cookies[{i}]")
        seen.add(key)
    return errors


def load_snapshot(path: str | os.PathLike[str]) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("snapshot must be a JSON object")
    errors = validate_snapshot(data)
    if errors:
        raise ValueError("invalid snapshot: " + "; ".join(errors))
    data = dict(data)
    data["cookies"] = normalize_cookies(data["cookies"])
    return data


def atomic_write_json(path: str | os.PathLike[str], data: Mapping[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        if os.name != "nt":
            os.chmod(tmp_name, 0o600)
        os.replace(tmp_name, target)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def diff_cookies(old: Iterable[Mapping[str, Any]], new: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    old_map = {cookie_key(c): normalize_cookie(c) for c in old}
    new_map = {cookie_key(c): normalize_cookie(c) for c in new}
    old_keys, new_keys = set(old_map), set(new_map)
    added = new_keys - old_keys
    removed = old_keys - new_keys
    updated = {k for k in old_keys & new_keys if old_map[k] != new_map[k]}
    unchanged = len((old_keys & new_keys) - updated)
    return {
        "added": len(added),
        "updated": len(updated),
        "removed": len(removed),
        "unchanged": unchanged,
        "changed": bool(added or updated or removed),
    }


def mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "***"
    return value[:3] + "…" + value[-2:]
