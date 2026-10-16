"""Create a clean Windows portable folder from source and explicit runtimes."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime-source', type=Path, required=True)
    parser.add_argument('--python-source', type=Path, required=True)
    parser.add_argument('--site-packages', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    dest = args.output.resolve()
    if dest.exists():
        raise SystemExit('Output exists; use a fresh build directory')
    dest.mkdir(parents=True)
    names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT).decode('utf-8').split('\0')
    for name in filter(None, names):
        source = ROOT / name
        if not source.is_file():
            continue
        target = dest / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copytree(args.runtime_source / 'runtime/Chrome-bin-v4', dest / 'runtime/Chrome-bin-v4')
    shutil.copy2(args.runtime_source / 'services/mihomo/core/mihomo.exe', dest / 'services/mihomo/core/mihomo.exe')
    python = dest / 'runtime/python'
    python.mkdir()
    for source in args.python_source.iterdir():
        if source.is_file() and (source.suffix.lower() in {'.exe', '.dll'} or source.name == 'LICENSE.txt'):
            shutil.copy2(source, python / source.name)
    ignore = shutil.ignore_patterns('__pycache__', '*.pyc', 'site-packages')
    shutil.copytree(args.python_source / 'Lib', python / 'Lib', ignore=ignore)
    shutil.copytree(args.python_source / 'DLLs', python / 'DLLs', ignore=ignore)
    if (args.python_source / 'tcl').exists():
        shutil.copytree(args.python_source / 'tcl', python / 'tcl')
    shutil.copytree(args.site_packages, python / 'Lib/site-packages', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    # Isolate from globally installed packages and expose only bundled application modules.
    (python / 'python312._pth').write_text(
        '.\nLib\nDLLs\nLib/site-packages\n../../.\n../../extensions/web-cookie-skill/scripts\n', encoding='ascii')
    subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                    str(next((dest / 'scripts').glob('build-*-v6.ps1')))], check=True)
    subprocess.run([str(python / 'python.exe'), '-c', 'import ssl,sqlite3,playwright.sync_api,services.automation.cli'], check=True)
    (dest / 'BUILD-INFO.json').write_text(json.dumps({
        'version':'1.0.0', 'platform':'windows-x64', 'sciProxy':'19.0.0', 'sciCookie':'2.0.0',
        'chromium':'154.0.8037.58', 'mihomo':'1.19.30',
        'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    }, indent=2), encoding='utf-8')
    print('Portable folder created:', dest)


if __name__ == '__main__':
    main()
