from contextlib import contextmanager
import json
import msvcrt
from pathlib import Path
import re
import uuid

from playwright.sync_api import sync_playwright


@contextmanager
def session(root: Path, name: str, proxy=None):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,47}', name):
        raise ValueError('Profile name must contain 1-48 ASCII letters, digits, hyphens or underscores')
    folder = root / 'profiles/automation' / ('session-' + name)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'session.lock').open('a+b') as lock:
        lock.seek(0)
        if not lock.read(1):
            lock.write(b'0')
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise ValueError('This automation profile is already open') from exc
        metadata = folder / 'session.json'
        data = json.loads(metadata.read_text(encoding='utf-8')) if metadata.exists() else {'profileId': str(uuid.uuid4()), 'proxy': None}
        if proxy is not None:
            data['proxy'] = None if proxy == 'direct' else proxy
        metadata.write_text(json.dumps(data), encoding='utf-8')
        preferences = folder / 'Default/Preferences'
        preferences.parent.mkdir(exist_ok=True)
        prefs = json.loads(preferences.read_text(encoding='utf-8')) if preferences.exists() else {}
        prefs.setdefault('plugins', {})['always_open_pdf_externally'] = True
        preferences.write_text(json.dumps(prefs), encoding='utf-8')
        with sync_playwright() as pw:
            context = pw.chromium.launch_persistent_context(
                str(folder), executable_path=str(root / 'runtime/Chrome-bin-v4/chrome.exe'),
                headless=False, accept_downloads=True, no_viewport=True,
                proxy={'server': data['proxy']} if data['proxy'] else None,
                args=['--no-first-run', '--disable-quic'])
            try:
                page = context.pages[0] if context.pages else context.new_page()
                yield context, page, data
            finally:
                context.close()
