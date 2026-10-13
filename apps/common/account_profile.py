from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class AccountProfile(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        workspace = user.organizations.filter(pk=request.session.get('current_org_id')).first()
        account_type = 'superadmin' if request.session.get('panel') == 'superadmin' and user.is_superadmin else (
            'personal' if workspace and workspace.kind == 'personal' else 'admin')
        return Response({
            'username': user.username,
            'account_type': account_type,
            'created_at': user.created_at,
            'current_organization': {'id': workspace.id, 'name': workspace.name} if workspace else None,
            'organizations': list(user.organizations.exclude(slug='system').values('id', 'name')),
        })


class AccountPassword(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current = request.data.get('current_password')
        password = request.data.get('new_password')
        confirmation = request.data.get('confirm_password')
        if not all(isinstance(value, str) and value for value in (current, password, confirmation)):
            return Response({'detail': 'Barcha parol maydonlarini to‘ldiring.'}, status=400)
        if not request.user.check_password(current):
            return Response({'detail': 'Joriy parol noto‘g‘ri.'}, status=400)
        if password != confirmation:
            return Response({'detail': 'Yangi parollar mos kelmadi.'}, status=400)
        if password == current:
            return Response({'detail': 'Yangi parol joriy paroldan farq qilishi kerak.'}, status=400)
        try:
            validate_password(password, user=request.user)
        except ValidationError as error:
            return Response({'detail': ' '.join(error.messages)}, status=400)
        request.user.set_password(password)
        request.user.save(update_fields=['password'])
        update_session_auth_hash(request, request.user)
        return Response({'detail': 'Parol yangilandi.'})
