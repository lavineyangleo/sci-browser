"""Windows persistent-browser adapter; keeps the upstream queue format."""
import argparse
import json
import msvcrt
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright, Error, TimeoutError

PROJECT = Path(__file__).resolve().parents[3]


def safe_name(value):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', str(value)).strip(' .')[:140]
    if not name or name.upper().split('.')[0] in {'CON', 'PRN', 'AUX', 'NUL', *[f'COM{i}' for i in range(10)], *[f'LPT{i}' for i in range(10)]}:
        name = '_' + name
    return name


def pdf(path):
    if not path.is_file():
        return False
    with path.open('rb') as stream:
        return stream.read(5) == b'%PDF-'


def main():
    ap = argparse.ArgumentParser(description='sci-browser Windows paper downloader')
    ap.add_argument('action', choices=['setup', 'download'])
    ap.add_argument('--queue', type=Path)
    ap.add_argument('--dest', type=Path, default=PROJECT / 'papers')
    ap.add_argument('--profile', type=Path, default=PROJECT / 'profiles/paper-download-v1')
    ap.add_argument('--timeout', type=int, default=90)
    ap.add_argument('--proxy', help='Optional HTTP/SOCKS proxy URL; omit for direct connection')
    args = ap.parse_args()
    if args.action == 'download' and not args.queue:
        ap.error('download requires --queue')
    queue = json.loads(args.queue.read_text(encoding='utf-8-sig')) if args.queue else []
    if not isinstance(queue, list):
        ap.error('queue must be a JSON array')
    args.profile.mkdir(parents=True, exist_ok=True)
    profile_lock = (args.profile / 'paper-tool.lock').open('a+b')
    profile_lock.seek(0)
    if not profile_lock.read(1):
        profile_lock.write(b'0')
        profile_lock.flush()
    profile_lock.seek(0)
    try:
        msvcrt.locking(profile_lock.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        ap.error('The paper downloader profile is already in use')
    # This profile is owned exclusively by this tool. Set PDF downloads before launch.
    prefs_path = args.profile / 'Default/Preferences'
    if (args.profile / 'SingletonLock').exists():
        ap.error('Close the paper downloader browser first')
    prefs = json.loads(prefs_path.read_text(encoding='utf-8')) if prefs_path.exists() else {}
    prefs.setdefault('plugins', {})['always_open_pdf_externally'] = True
    prefs_path.parent.mkdir(parents=True, exist_ok=True)
    prefs_path.write_text(json.dumps(prefs), encoding='utf-8')
    results = []
    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            str(args.profile), executable_path=str(PROJECT / 'runtime/Chrome-bin-v4/chrome.exe'),
            headless=False, accept_downloads=True,
            proxy={'server': args.proxy} if args.proxy else None,
            args=['--no-first-run', '--disable-quic'])
        try:
            page = context.pages[0] if context.pages else context.new_page()
            if args.action == 'setup':
                page.goto('about:blank')
                input('Log in to your institution in this browser, then press Enter here to save and close: ')
                return 0
            args.dest.mkdir(parents=True, exist_ok=True)
            used = set()
            for index, item in enumerate(queue):
                name = safe_name(item.get('name') or f'paper_{index}')
                folder = safe_name(item['folder']) if item.get('folder') else ''
                target = args.dest / folder / (name + '.pdf')
                result = {'index': index, 'name': name}
                key = str(target.resolve()).casefold()
                if key in used:
                    result['status'] = 'DUPLICATE_TARGET'
                elif pdf(target):
                    result['status'] = 'SKIP_EXISTING_PDF'
                elif target.exists():
                    result['status'] = 'TARGET_EXISTS_NOT_PDF'
                else:
                    url = item.get('url', '')
                    parsed = urlsplit(url)
                    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username:
                        result['status'] = 'INVALID_URL'
                    else:
                        try:
                            with page.expect_download(timeout=args.timeout * 1000) as event:
                                try:
                                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                                except Error:
                                    # Navigation may abort because a download has started.
                                    pass
                            download = event.value
                            temporary = download.path()
                            if temporary and pdf(Path(temporary)):
                                target.parent.mkdir(parents=True, exist_ok=True)
                                download.save_as(str(target))
                                result.update(status='DOWNLOADED', path=str(target.resolve()))
                            else:
                                result['status'] = 'NOT_PDF'
                        except TimeoutError:
                            result['status'] = 'NO_DOWNLOAD_NEEDS_USER_CHECK'
                        except Error:
                            result['status'] = 'DOWNLOAD_FAILED'
                used.add(key)
                results.append(result)
                print(json.dumps(result, ensure_ascii=True), flush=True)
                (args.dest / 'download-report.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
                page.wait_for_timeout(1500)
        finally:
            context.close()
    return int(any(r['status'] not in ('DOWNLOADED', 'SKIP_EXISTING_PDF') for r in results))


if __name__ == '__main__':
    sys.exit(main())
