from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

from cookie_core import atomic_write_json, diff_cookies, load_snapshot, make_snapshot, mask


def add_browser_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--user-data-dir", help="Dedicated Chromium profile directory")
    parser.add_argument("--headed", action="store_true", help="Show browser window")
    parser.add_argument("--executable-path", help="Specific Chrome/Chromium executable")
    parser.add_argument("--no-navigate", action="store_true", help="Read existing profile cookies without loading URL")
    parser.add_argument("--wait-ms", type=int, default=800, help="Wait after navigation before reading cookies")


def open_client(args: argparse.Namespace):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Playwright is not installed. Run: pip install -r requirements/requirements.txt") from exc

    class Client:
        def __enter__(self):
            self.cm = sync_playwright()
            self.pw = self.cm.__enter__()
            launch: dict[str, Any] = {"headless": not args.headed}
            if args.executable_path:
                launch["executable_path"] = args.executable_path
            if args.user_data_dir:
                Path(args.user_data_dir).mkdir(parents=True, exist_ok=True)
                self.context = self.pw.chromium.launch_persistent_context(args.user_data_dir, **launch)
                self.browser = None
            else:
                self.browser = self.pw.chromium.launch(**launch)
                self.context = self.browser.new_context()
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            return self

        def __exit__(self, exc_type, exc, tb):
            try:
                self.context.close()
                if self.browser:
                    self.browser.close()
            finally:
                self.cm.__exit__(exc_type, exc, tb)

        def cookies(self, url: str) -> list[dict[str, Any]]:
            if not args.no_navigate:
                self.page.goto(url, wait_until="domcontentloaded")
                if args.wait_ms > 0:
                    self.page.wait_for_timeout(args.wait_ms)
            return self.context.cookies([url])

    return Client()


def scan_once(args: argparse.Namespace, client=None) -> list[dict[str, Any]]:
    if client is not None:
        return client.cookies(args.url)
    with open_client(args) as c:
        return c.cookies(args.url)


def print_scan(cookies: list[dict[str, Any]], show_values: bool) -> None:
    print(f"cookies={len(cookies)}")
    for c in cookies:
        value = str(c.get("value", "")) if show_values else mask(str(c.get("value", "")))
        session = c.get("expires") in (None, -1, 0)
        print(
            f"- {c.get('name','')}={value} domain={c.get('domain','')} path={c.get('path','/')} "
            f"httpOnly={bool(c.get('httpOnly'))} secure={bool(c.get('secure'))} "
            f"sameSite={c.get('sameSite')} session={session}"
        )


def cmd_scan(args: argparse.Namespace) -> int:
    print_scan(scan_once(args), args.show_values)
    return 0


def cmd_save(args: argparse.Namespace) -> int:
    snapshot = make_snapshot(args.url, scan_once(args))
    atomic_write_json(args.output, snapshot)
    print(f"saved={len(snapshot['cookies'])} file={args.output}")
    return 0


def sync_once(args: argparse.Namespace, client=None, *, write: bool = True) -> dict[str, Any]:
    old = load_snapshot(args.snapshot)
    args.url = args.url or old["sourceUrl"]
    current = scan_once(args, client=client)
    new = make_snapshot(args.url, current)
    diff = diff_cookies(old["cookies"], new["cookies"])
    if write and diff["changed"]:
        atomic_write_json(args.snapshot, new)
    return diff


def print_diff(diff: dict[str, Any], prefix: str = "") -> None:
    print(
        f"{prefix}added={diff['added']} updated={diff['updated']} "
        f"removed={diff['removed']} unchanged={diff['unchanged']}"
    )


def cmd_sync(args: argparse.Namespace) -> int:
    diff = sync_once(args, write=not args.dry_run)
    print_diff(diff)
    if args.dry_run:
        print("dry_run=true")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    old = load_snapshot(args.snapshot)
    args.url = args.url or old["sourceUrl"]
    iteration = 0
    with open_client(args) as client:
        if not args.no_navigate:
            client.page.goto(args.url, wait_until="domcontentloaded")
            if args.wait_ms > 0:
                client.page.wait_for_timeout(args.wait_ms)
            args.no_navigate = True
        while True:
            iteration += 1
            diff = sync_once(args, client=client, write=True)
            if diff["changed"]:
                print_diff(diff, prefix=f"[{iteration}] ")
            if args.iterations and iteration >= args.iterations:
                break
            time.sleep(args.interval)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Identify, save, and automatically update webpage cookies.")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Identify cookies for a webpage")
    scan.add_argument("--url", required=True)
    scan.add_argument("--show-values", action="store_true")
    add_browser_args(scan)
    scan.set_defaults(func=cmd_scan)

    save = sub.add_parser("save", help="Save webpage cookies to a JSON snapshot")
    save.add_argument("--url", required=True)
    save.add_argument("--output", required=True)
    add_browser_args(save)
    save.set_defaults(func=cmd_save)

    sync = sub.add_parser("sync", help="Update a saved snapshot from current browser cookies")
    sync.add_argument("snapshot")
    sync.add_argument("--url", help="Override sourceUrl in the snapshot")
    sync.add_argument("--dry-run", action="store_true")
    add_browser_args(sync)
    sync.set_defaults(func=cmd_sync)

    watch = sub.add_parser("watch", help="Continuously keep a snapshot updated")
    watch.add_argument("snapshot")
    watch.add_argument("--url", help="Override sourceUrl in the snapshot")
    watch.add_argument("--interval", type=float, default=10.0)
    watch.add_argument("--iterations", type=int, default=0, help="0 means keep running")
    add_browser_args(watch)
    watch.set_defaults(func=cmd_watch)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.func(args) or 0)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
