from rest_framework.permissions import BasePermission

class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_active and request.user.is_superadmin)

class IsWorkspaceAdmin(BasePermission):
    def has_permission(self, request, view):
        user=request.user
        return bool(user.is_authenticated and user.is_active and (user.is_admin or user.is_superadmin)
            and user.organizations.filter(pk=request.session.get('current_org_id'),is_active=True,
                approval_status='approved').exists())
