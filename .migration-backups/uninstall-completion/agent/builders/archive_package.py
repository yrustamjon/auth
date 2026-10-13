"""Archive a built agent in OS/version/time directories without overwriting."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SYSTEMS = ('windows', 'linux', 'macos')
UZT = timezone(timedelta(hours=5), 'UZT')


def read_version(system, root=ROOT):
    if system not in SYSTEMS:
        raise ValueError('Unsupported OS')
    version = (root / 'releases' / system / 'VERSION').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version):
        raise ValueError('VERSION must contain major.minor.patch')
    return version


def archive_package(system, package, root=ROOT, now=None, commit=None):
    version = read_version(system, root)
    package = Path(package)
    if not package.is_file() or package.name in ('manifest.json', 'SHA256SUMS.txt', 'README.md'):
        raise ValueError('Provide an existing agent package')
    created = now or datetime.now(UZT)
    if created.tzinfo is None:
        raise ValueError('Timestamp must have a timezone')
    created = created.astimezone(UZT)
    if commit is None:
        commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root,
                                check=True, capture_output=True, text=True).stdout.strip()
    destination = root / 'releases' / system / version / created.strftime('%Y-%m-%d_%H-%M-%S-%f_UZT')
    destination.mkdir(parents=True, exist_ok=False)
    try:
        target = destination / package.name
        shutil.copyfile(package, target)
        digest = hashlib.sha256()
        with target.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        manifest = {'os': system, 'version': version, 'created_at': created.isoformat(),
                    'timezone': 'Asia/Tashkent', 'commit': commit, 'prerelease': True,
                    'files': [{'name': target.name, 'size': target.stat().st_size,
                               'sha256': digest.hexdigest()}]}
        (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        (destination / 'SHA256SUMS.txt').write_text(digest.hexdigest() + '  ' + target.name + '\n', encoding='utf-8')
        (destination / 'README.md').write_text(
            f'# {system.title()} v{version}\n\nCreated: {created.isoformat()} (UZT)\n\n'
            f'[Download installer]({target.name}) · [SHA-256](SHA256SUMS.txt) · [Manifest](manifest.json)\n\n'
            'Development / pre-release; SIMULATE and EXIT remain enabled.\n', encoding='utf-8')
    except Exception:
        # Only remove this newly created archive; never touch the input package.
        shutil.rmtree(destination)
        raise
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--os', required=True, choices=SYSTEMS)
    parser.add_argument('--file', required=True, type=Path)
    args = parser.parse_args()
    print(archive_package(args.os, args.file))


if __name__ == '__main__':
    main()
