import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from cookie_core import atomic_write_json, cookie_key, diff_cookies, load_snapshot, make_snapshot, validate_snapshot


def c(name="sid", value="a", domain="example.com", path="/", partition=None):
    return {
        "name": name,
        "value": value,
        "domain": domain,
        "path": path,
        "expires": -1,
        "httpOnly": True,
        "secure": True,
        "sameSite": "Lax",
        "partitionKey": partition,
    }


def test_identity_includes_domain_path_partition():
    assert cookie_key(c()) != cookie_key(c(path="/admin"))
    assert cookie_key(c()) != cookie_key(c(domain="api.example.com"))
    assert cookie_key(c()) != cookie_key(c(partition="https://top.example"))


def test_diff_added_updated_removed():
    old = [c("a", "1"), c("b", "1"), c("gone", "1")]
    new = [c("a", "1"), c("b", "2"), c("new", "1")]
    d = diff_cookies(old, new)
    assert d == {"added": 1, "updated": 1, "removed": 1, "unchanged": 1, "changed": True}


def test_snapshot_roundtrip(tmp_path):
    snap = make_snapshot("https://example.com", [c()])
    assert validate_snapshot(snap) == []
    path = tmp_path / "cookies.json"
    atomic_write_json(path, snap)
    loaded = load_snapshot(path)
    assert loaded["sourceUrl"] == "https://example.com"
    assert loaded["cookies"][0]["name"] == "sid"


def test_duplicate_identity_rejected():
    snap = make_snapshot("https://example.com", [c(), c(value="2")])
    assert any("duplicate" in e for e in validate_snapshot(snap))
