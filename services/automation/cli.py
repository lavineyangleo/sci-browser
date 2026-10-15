import argparse
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import Error
from .browser import session
from .environment import capture, compare, write_json

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description='sci-browser Playwright automation and session inspection')
    parser.add_argument('action', choices=['open', 'collect', 'snapshot', 'check', 'download'])
    parser.add_argument('--url', required=True)
    parser.add_argument('--profile', default='default')
    parser.add_argument('--proxy', help='Persist proxy URL for this profile; direct resets it')
    parser.add_argument('--selector', help='CSS selector for collection')
    parser.add_argument('--authenticated-selector')
    parser.add_argument('--unauthenticated-selector')
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--timeout', type=int, default=90)
    args = parser.parse_args()
    url = urlsplit(args.url)
    if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password:
        parser.error('An HTTP(S) URL without embedded credentials is required')
    if args.action == 'collect' and not args.selector:
        parser.error('collect requires --selector')
    if args.action in ('collect', 'snapshot', 'download') and not args.out:
        parser.error('This action requires --out')
    if args.action == 'download' and args.out.exists():
        parser.error('Output already exists; choose another path')
    with session(ROOT, args.profile, args.proxy) as (context, page, metadata):
        if args.action == 'download':
            with page.expect_download(timeout=args.timeout * 1000) as pending:
                try:
                    page.goto(args.url, wait_until='domcontentloaded', timeout=args.timeout * 1000)
                except Error:
                    pass  # Chromium may abort navigation when a download begins.
            item = pending.value
            temporary = item.path()
            if not temporary:
                raise ValueError('Download failed')
            with Path(temporary).open('rb') as stream:
                if stream.read(5) != b'%PDF-':
                    raise ValueError('Downloaded file is not a PDF')
            args.out.parent.mkdir(parents=True, exist_ok=True)
            item.save_as(str(args.out))
            print(json.dumps({'status':'downloaded', 'bytes':args.out.stat().st_size}))
            return 0
        page.goto(args.url, wait_until='domcontentloaded', timeout=args.timeout * 1000)
        if args.action == 'open':
            input('Complete browser operations or login, then press Enter to save and close: ')
            return 0
        if args.action == 'collect':
            page.locator(args.selector).first.wait_for(state='attached', timeout=args.timeout * 1000)
            records = page.locator(args.selector).evaluate_all('(nodes)=>nodes.map(n=>({text:n.innerText||n.textContent,href:n.href||null}))')
            write_json(args.out, {'sourceUrl':page.url, 'records':records})
            print(json.dumps({'status':'collected', 'count':len(records)}))
            return 0
        current_url = page.url
        info = capture(page, ROOT, {'profileId':metadata['profileId'],
            'authenticatedSelector':args.authenticated_selector,
            'unauthenticatedSelector':args.unauthenticated_selector})
        cookies = context.cookies([current_url])
        if page.url != current_url:
            raise ValueError('Page changed during snapshot; retry')
        snapshot = {'schemaVersion':'1.0', 'sourceUrl':current_url,
            'capturedAt':datetime.now(timezone.utc).isoformat(), 'cookies':[
                dict(c, expires=None if c.get('expires', -1) <= 0 else c['expires'],
                     session=c.get('expires', -1) <= 0, partitionKey=c.get('partitionKey')) for c in cookies], **info}
        summary = {'status':info['loginEvidence']['status'], 'cookieCount':len(cookies),
                   'fingerprint':info['fingerprint'], 'profileId':metadata['profileId']}
        if args.baseline:
            summary['comparison'] = compare(json.loads(args.baseline.read_text(encoding='utf-8-sig')), snapshot)
        if args.action == 'snapshot':
            write_json(args.out, snapshot)
        elif args.out:
            write_json(args.out, summary)
        print(json.dumps(summary))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (Error, OSError, ValueError) as error:
        # Browser errors may contain URLs or page content; avoid leaking them to logs.
        print(json.dumps({'status':'failed', 'errorType':type(error).__name__,
                          'hint':'Check the browser, URL, selector, output path and profile availability.'}), file=sys.stderr)
        raise SystemExit(1)
