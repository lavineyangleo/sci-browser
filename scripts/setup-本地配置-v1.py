"""Initialize machine-local settings without shipping credentials."""
import json
from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parents[1]


def main():
    service = ROOT / 'services/mihomo'
    for folder in ['config', 'profiles', 'services/mihomo/core', 'services/mihomo/runtime']:
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    path = service / 'settings.json'
    settings = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if not settings.get('token'):
        settings['token'] = secrets.token_urlsafe(32)
    settings['core'] = str(service / 'core/mihomo.exe')
    path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding='utf-8')
    state = service / 'state.json'
    if not state.exists():
        state.write_text(json.dumps({'enabled': False, 'profile': {
            'host': '', 'port': 1080, 'username': '', 'password': ''
        }}, indent=2), encoding='utf-8')
    token = ROOT / 'extensions/sci-proxy/local-token.js'
    token.parent.mkdir(parents=True, exist_ok=True)
    token.write_text('export const TOKEN = ' + json.dumps(settings['token']) + ';\n', encoding='utf-8')
    print('Local settings initialized. Existing proxy state and token preserved.')
    print('Configure your real SOCKS5 server in sci-proxy options before enabling proxy.')


if __name__ == '__main__':
    main()
