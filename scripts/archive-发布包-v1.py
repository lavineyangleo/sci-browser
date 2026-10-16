"""Archive a portable build using an explicit release allowlist."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    stage = args.stage.resolve()
    names = set(filter(None, subprocess.check_output(
        ['git','ls-files','--cached','--others','--exclude-standard','-z'], cwd=ROOT).decode('utf-8').split('\0')))
    names.update(p.relative_to(stage).as_posix() for p in (stage/'runtime').rglob('*')
                 if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    names.update({'sci-browser.exe', 'services/mihomo/core/mihomo.exe', 'BUILD-INFO.json'})
    for name in names:
        assert not name.startswith(('profiles/', 'papers/'))
        assert name not in {'services/mihomo/settings.json', 'services/mihomo/state.json',
                            'extensions/sci-proxy/local-token.js'}
        assert '.local.' not in name
        assert (stage/name).is_file(), name
    manifest = {name:hashlib.file_digest((stage/name).open('rb'), 'sha256').hexdigest() for name in sorted(names)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in sorted(names):
            archive.write(stage/name, stage.name+'/'+name)
        archive.writestr(stage.name+'/FILE-SHA256.json', json.dumps(manifest,indent=2))
    with zipfile.ZipFile(args.out) as archive:
        assert archive.testzip() is None
    print('Verified archive:', args.out.name, 'files:',len(names), 'bytes:',args.out.stat().st_size)


if __name__ == '__main__':
    main()
