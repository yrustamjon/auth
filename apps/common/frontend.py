"""Serve the built React site on the same origin as Django APIs."""
import mimetypes
import re
from pathlib import Path
from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.middleware.csrf import get_token

PAGES={
    'agent-events', 'personal/agent-events',
    'profile', 'personal/profile', 'system/profile',
    '', 'product','downloads','guide','login','dashboard','users','roles','devices','logs',
    'registration/status','personal/computer','personal/biometrics','personal/history',
    'system','system/login','system/dashboard','system/organizations','system/admins','system/applications',
    'device/scan','devices/scan-qr','devices/add/qr','device-enroll/approval',
}

class FrontendMiddleware:
    def __init__(self,get_response):self.get_response=get_response

    def __call__(self,request):
        if not settings.SERVE_FRONTEND or request.method not in ('GET','HEAD'):
            return self.get_response(request)
        path=request.path.strip('/')
        dist=Path(settings.FRONTEND_DIST_DIR).resolve()
        if path.startswith('assets/'):
            assets=(dist/'assets').resolve()
            file=(dist/path).resolve()
            if not file.is_relative_to(assets):return JsonResponse({'detail':'NOT_FOUND'},status=404)
            return self.file(file,cache=True)
        if path=='favicon.svg':return self.file(dist/'favicon.svg')
        if path not in PAGES and not re.fullmatch(r'device-enroll/[A-Za-z0-9_-]+|mobile/fingerprint/[0-9a-fA-F-]+',path):
            return self.get_response(request)
        index=dist/'index.html'
        if not index.is_file():return JsonResponse({'detail':'Sayt hozir tayyor emas. Frontend build talab qilinadi.'},status=503)
        get_token(request)
        return self.file(index)

    @staticmethod
    def file(path,cache=False):
        try:
            if not path.is_file():raise OSError
            response=FileResponse(path.open('rb'),content_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
        except OSError:return JsonResponse({'detail':'NOT_FOUND'},status=404)
        response['Cache-Control']='public, max-age=31536000, immutable' if cache else 'no-cache'
        return response
