"""Serve published agent packages from the existing release archive."""
import json
import re
from pathlib import Path
from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.views.decorators.http import require_GET

PLATFORMS=('windows','macos','linux')
PACKAGE_SUFFIXES=('.exe','.msi','.dmg','.pkg','.zip','.tar.gz','.deb','.rpm','.AppImage')

def latest(platform):
    root=Path(settings.AGENT_RELEASE_DIR).resolve()
    row={'platform':platform,'version':None,'available':False}
    try:
        version=(root/platform/'VERSION').read_text(encoding='utf-8-sig').strip()
        row['version']=version
        if not re.fullmatch(r'\d+\.\d+\.\d+',version) or version=='0.0.0':return row,None
        directory=(root/platform/version).resolve()
        if not directory.is_relative_to(root):return row,None
        for manifest in sorted(directory.glob('*/manifest.json'),reverse=True):
            if not manifest.resolve().is_relative_to(root):continue
            try:
                data=json.loads(manifest.read_text(encoding='utf-8'))
                if data.get('os')!=platform or data.get('version')!=version:continue
                for entry in data.get('files',[]):
                    name=entry.get('name','')
                    if not isinstance(name,str) or '/' in name or '\\' in name or not name.endswith(PACKAGE_SUFFIXES):continue
                    package=(manifest.parent/name).resolve()
                    if not package.is_relative_to(root) or not package.is_file():continue
                    size=package.stat().st_size
                    if size!=entry.get('size') or not re.fullmatch(r'[a-fA-F0-9]{64}',str(entry.get('sha256',''))):continue
                    row.update(available=True,filename=name,size=size,sha256=entry['sha256'],
                        prerelease=bool(data.get('prerelease',True)),created_at=data.get('created_at'),
                        download_url=f'/api/downloads/{platform}/')
                    return row,package
            except (ValueError,TypeError,AttributeError,OSError):continue
    except OSError:pass
    return row,None

@require_GET
def catalog(request):
    return JsonResponse({'releases':[latest(platform)[0] for platform in PLATFORMS]})

@require_GET
def download(request,platform):
    if platform not in PLATFORMS:return JsonResponse({'detail':'NOT_FOUND'},status=404)
    row,package=latest(platform)
    if not package:return JsonResponse({'detail':'PACKAGE_NOT_AVAILABLE'},status=404)
    try:
        response=FileResponse(package.open('rb'),as_attachment=True,filename=row['filename'],content_type='application/octet-stream')
    except OSError:return JsonResponse({'detail':'PACKAGE_NOT_AVAILABLE'},status=404)
    response['X-Content-SHA256']=row['sha256']
    response['Cache-Control']='no-cache'
    return response
