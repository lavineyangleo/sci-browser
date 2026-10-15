"""Shared capture protocol with the sci-cookie browser extension."""
from pathlib import Path
import json


def capture(page, root: Path, options):
    source = next((root / 'extensions/web-cookie-skill/browser-extension/core').glob('environment-*-v2.js'))
    function = source.read_text(encoding='utf-8').removeprefix('export default ')
    return page.evaluate('(' + function + ')', options)


def compare(previous, current):
    old, new = previous.get('environment'), current.get('environment')
    if not old or not new or old.get('version') != new.get('version') or any(k not in old for k in new):
        return {'status': 'unknown', 'changed': [], 'reason': 'missing_or_incompatible_environment'}
    changed = [key for key in new if old[key] != new[key]]
    for key in ['origin', 'profileId']:
        if previous.get('session', {}).get(key) != current.get('session', {}).get(key):
            changed.append(key)
    return {'status': 'different' if changed else 'matching', 'changed': changed}


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)
