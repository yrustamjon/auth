from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import *
from functools import wraps

from functools import wraps
from django.shortcuts import redirect

from functools import wraps
from django.shortcuts import redirect

def role_required(role):
    """
    role = 'admin' | 'superadmin'
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            # login yo‘q
            if not request.user.is_authenticated:
                return redirect('login')

            is_super = getattr(request.user, "is_superadmin", False)

            # superadmin panel
            if role == "superadmin" and not is_super:
                return redirect('dashboard')

            # admin panel
            if role == "admin" and is_super:
                return redirect('system_dashboard')

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator



def sender_about_user(view_func):
    def wrapper(request, *args, **kwargs):
        data = {
            "username": request.user.username,
            "organization": request.user.organization.name if request.user.organization else None,
            "is_superadmin": request.user.is_superadmin,
            "created_at": request.user.created_at,
        }
        kwargs["data"] = data
        return view_func(request, *args, **kwargs)
    return wrapper



def login_page(request):
    if request.user.is_authenticated:
        if request.user.is_superadmin:
            return redirect('system_dashboard')
        else:
            return redirect('dashboard')
    return render(request, "login.html")

@login_required
@role_required("admin")
@sender_about_user
def dashboard(request, data):
    data["page_title"]="Dashboard"
    data["page_icon"]="fas fa-tachometer-alt"
    return render(request, "dashboard.html", data)

@login_required
@role_required("admin")
@sender_about_user
def users_page(request, data):
    print("Data in users_page:", data)
    data["page_title"]="User Management"
    data["page_icon"]="fas fa-users"
    return render(request, "users.html",data)
@login_required
@role_required("admin")
@sender_about_user
def roles_page(request, data):
    data["page_title"]="Role Management"
    data["page_icon"]="fas fa-user-tag"
    return render(request, "roles.html", data)

@login_required
@role_required("admin")
@sender_about_user
def devices_page(request, data):
    data["page_title"]="Device Management"
    data["page_icon"]="fas fa-desktop"
    return render(request, "devices.html", data)



@login_required
@role_required("admin")
@sender_about_user
def logs_page(request, data):
    data["page_title"]="Logs"
    data["page_icon"]="fas fa-clipboard-list"
    return render(request, "logs.html", data)

def System_Login(request):
    if request.user.is_authenticated:
        if request.user.is_superadmin:
            return redirect('system_dashboard')
        else:
            return redirect('dashboard')
    return render(request, "superadmin/login.html")

@login_required
@role_required("superadmin")
def System_Dashboard(request):
    if not request.user.is_superadmin:
        return redirect('dashboard')
    return render(request, "superadmin/dashboard.html")



class AdminLogin(APIView):
    permission_classes = [AllowAny]
    allow_superadmin = False  

    def get_user(self, username):
        return AdminUser.objects.filter(username=username).first()

    def validate(self, request):

        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return None, Response({"detail": "Username and password required"}, status=400)

        user = self.get_user(username)

        if not user:
            return None, Response({"detail": "User not found"}, status=401)


        if user.is_superadmin and not self.allow_superadmin:
            return None, Response(
                {"detail": "System users must use system login"},
                status=403
            )

        if not user.is_superadmin and self.allow_superadmin:
            return None, Response(
                {"detail": "Only system users can use this login. Please use Admin login."},
                status=403
            )


        if user.is_locked():
            seconds = int((user.locked_until - timezone.now()).total_seconds())
            return None, Response(
                {"detail": f"Account locked {seconds//60}:{seconds%60}"},
                status=403
            )

        auth_user = authenticate(request, username=username, password=password)

        if not auth_user:
            user.register_failed_attempt()
            return None, Response({"detail": "Password incorrect"}, status=401)

        return auth_user, None


    def clear_sessions(self, user):
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for s in sessions:
            if s.get_decoded().get("_auth_user_id") == str(user.id):
                s.delete()


    def post(self, request):

        user, error = self.validate(request)

        if error:
            return error

        self.clear_sessions(user)
        login(request, user)

        return Response({
            "ok": True,
            "redirect": self.get_redirect_url(user)
        })

    def get_redirect_url(self, user):
        return "/dashboard/"


class AdminLogout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"ok": True})


class Admin_Users(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        admin=AdminUser.objects.get(id=request.user.id)
        users=Users.objects.filter(organization=admin.organization)
        print("Admin's organization:", admin.organization)
        print("Users in organization:", users)
        
        users_data = [
            {
                "id": user.id,
                "username": user.username,
                "is_superadmin": user.is_superadmin,
                "created_at": user.created_at,
                "is_locked": user.is_locked(),
            }
            for user in users
        ]
        return Response({"users": users_data})
    
    def post(self, request):
        admin=AdminUser.objects.get(id=request.user.id)
        organization=admin.organization
        print(request.data, organization)
        # new_user = Users.objects.create_user(
        #     role=request.data.get("role"),
        #     fio=request.data.get("fio"),
        #     username=request.data.get("username"),
        #     lavozim=request.data.get("lavozim"),
        #     organization=organization,
        # )
        

        # return Response({
        #     "id": new_user.id,
        #     "username": new_user.username,
        #     "fio": new_user.fio,
        #     "lavozim": new_user.lavozim,
        #     "role": new_user.role,
        #     "created_at": new_user.created_at,
        # })
        return Response({"users": "User creation endpoint is under development."})
        

class Super_AdminLogin(AdminLogin):
    allow_superadmin = True
    

class Super_AdminLogout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        

