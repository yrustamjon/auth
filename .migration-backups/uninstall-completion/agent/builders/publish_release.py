"""Publish one archived development installer and its manifest to GitHub Releases."""
import argparse
from datetime import datetime
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


def release_plan(folder):
    folder = Path(folder)
    manifest_path = folder / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    system, version, commit = manifest['os'], manifest['version'], manifest['commit']
    if system not in ('windows', 'linux', 'macos') or not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Invalid OS or version')
    if not re.fullmatch(r'[0-9a-f]{40}', commit) or manifest.get('prerelease') is not True:
        raise ValueError('Only commit-bound development packages may be published')
    created = datetime.fromisoformat(manifest['created_at'])
    if created.tzinfo is None:
        raise ValueError('Missing timestamp timezone')
    files = []
    for record in manifest['files']:
        name = record['name']
        if not isinstance(name, str) or '/' in name or '\\' in name or name in ('', '.', '..', 'manifest.json'):
            raise ValueError('Invalid package filename')
        path = folder / name
        digest = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(block)
        if path.stat().st_size != record['size'] or digest.hexdigest() != record['sha256']:
            raise ValueError('Package differs from its manifest')
        files.append(path)
    if not files or len({path.name for path in files}) != len(files):
        raise ValueError('Missing or duplicate packages')
    checksums = ''.join(record['sha256'] + '  ' + record['name'] + '\n' for record in manifest['files'])
    checksum_path = folder / 'SHA256SUMS.txt'
    if not checksum_path.is_file() or checksum_path.read_text(encoding='utf-8') != checksums:
        raise ValueError('SHA256SUMS.txt differs from the verified manifest')
    tag = f'{system}-v{version}-' + created.strftime('%Y%m%d-%H%M%S-%f')
    return {'tag_name': tag, 'target_commitish': commit,
            'name': f'{system.title()} v{version} — {created.isoformat()}',
            'body': 'Development / pre-release package. SIMULATE and EXIT remain enabled.\n\n'
                    'Download the installer from Assets. manifest.json includes creation time, '
                    'commit and SHA-256. Native OS enforcement is not production-ready.',
            'draft': True, 'prerelease': True, 'make_latest': 'false'}, [*files, manifest_path, checksum_path]


def _api(method, url, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = Request(url, data=data, method=method, headers={
        'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
        'Content-Type': 'application/json', 'User-Agent': 'BioGuard-release-builder',
        'X-GitHub-Api-Version': '2022-11-28'})
    with urlopen(request, timeout=60) as response:
        return json.load(response)


def _upload(upload_url, path, token):
    address = urlsplit(upload_url.split('{', 1)[0])
    if address.scheme != 'https' or address.hostname != 'uploads.github.com':
        raise ValueError('Unexpected GitHub upload endpoint')
    connection = http.client.HTTPSConnection(address.hostname, timeout=120)
    try:
        connection.putrequest('POST', address.path + '?' + urlencode({'name': path.name}))
        connection.putheader('Authorization', 'Bearer ' + token)
        connection.putheader('User-Agent', 'BioGuard-release-builder')
        connection.putheader('Content-Type', 'application/octet-stream')
        connection.putheader('Content-Length', str(path.stat().st_size))
        connection.endheaders()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b''):
                connection.send(block)
        response = connection.getresponse()
        result = json.loads(response.read())
        if response.status != 201:
            raise RuntimeError(f'GitHub asset upload failed: HTTP {response.status}')
        return result
    finally:
        connection.close()


def publish(folder, repository, token):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository) or not token:
        raise ValueError('Repository and GitHub token required')
    plan, files = release_plan(folder)
    base = 'https://api.github.com/repos/' + repository + '/releases'
    release = _api('POST', base, token, plan)
    # Keep the release a draft until EVERY asset has uploaded successfully.
    for path in files:
        _upload(release['upload_url'], path, token)
    released = _api('PATCH', base + '/' + str(release['id']), token,
                    {'draft': False, 'prerelease': True, 'make_latest': 'false'})
    return released['html_url']


def update_catalog(folder, repository, release_url):
    """Call only after successful publication; preserve all old release rows."""
    folder = Path(folder).resolve()
    plan, files = release_plan(folder)
    expected = 'https://github.com/' + repository + '/releases/tag/' + plan['tag_name']
    if release_url != expected:
        raise ValueError('Unexpected published release URL')
    root = folder.parents[3]
    manifest = json.loads((folder / 'manifest.json').read_text())
    system, version = manifest['os'], manifest['version']
    catalog = root / 'releases/README.md'
    text = catalog.read_text(encoding='utf-8')
    relative = folder.relative_to(root / 'releases').as_posix()
    if relative + '/' in text:
        return
    download = 'https://github.com/' + repository + '/releases/download/' + plan['tag_name'] + '/' + files[0].name
    current = (root / 'releases' / system / 'VERSION').read_text().strip()
    if current == version:
        text = re.sub(r'^\| ' + re.escape(system.title()) + r' \| \[' + re.escape(version) + r'\]\(' + re.escape(system) + r'/VERSION\) \|.*$',
            '| ' + system.title() + ' | [' + version + '](' + system + '/VERSION) | Development / pre-release; no native login enforcement | [Download installer](' + download + ') |', text, flags=re.MULTILINE)
    row = '| ' + system.title() + ' | ' + version + ' | ' + manifest['created_at'] + ' | [EXE and manifest](' + relative + '/) | [SHA-256](' + relative + '/SHA256SUMS.txt) |\n'
    separator = '| --- | --- | --- | --- | --- |\n'
    if separator not in text:
        raise ValueError('Release catalog history table missing')
    text = text.replace(separator, separator + row, 1)
    catalog.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', required=True, type=Path)
    parser.add_argument('--update-catalog', action='store_true')
    args = parser.parse_args()
    repository=os.environ['GITHUB_REPOSITORY']
    url=publish(args.folder,repository,os.environ['GH_TOKEN'])
    if args.update_catalog:
        update_catalog(args.folder,repository,url)
    print(url)
