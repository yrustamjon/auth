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
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            panel = request.session.get("panel")  # ← sessiondan o'qiymiz

            if role == "superadmin" and panel != "superadmin":
                return redirect('dashboard')

            if role == "admin" and panel != "admin":
                return redirect('system_dashboard')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def sender_about_user(view_func):
    def wrapper(request, *args, **kwargs):
        orgs = request.user.organizations.all()
        
        # Sessiondan joriy org
        current_org_id = request.session.get("current_org_id")
        current_org = orgs.filter(id=current_org_id).first() or orgs.exclude(slug="system").first()

        data = {
            "username": request.user.username,
            "organizations": list(orgs.exclude(slug="system").values("id", "name")),
            "current_org_id": current_org.id if current_org else None,
            "organization": current_org.name if current_org else None,
            "is_superadmin": request.user.is_superadmin,
            "created_at": request.user.created_at,
        }
        kwargs["data"] = data
        return view_func(request, *args, **kwargs)
    return wrapper

def _(request):
    return redirect('login')

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
    print("Data in dashboard:", data)
    print("Request user:", request.session.get("current_org_id"))
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
     return render(request, 'superadmin/dashboard.html', {'active_page': 'dashboard'})


@login_required
@role_required("superadmin")
def system_orgag(request):
    return render(request, "superadmin/organizations.html", {'active_page': 'organizations'})


@login_required
@role_required("superadmin")
def system_admins(request):
    return render(request, "superadmin/admins.html", {'active_page': 'admins'})

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


        # validate metodida:
        if self.allow_superadmin:
            if not user.is_superadmin:
                return None, Response({"detail": "Only system users..."}, status=403)
        else:
            if not user.is_admin:
                return None, Response({"detail": "System users must use system login"}, status=403)


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

    def get_redirect_url(self):
        if self.allow_superadmin:
            return "/system/dashboard/"
        return "/dashboard/"

    def post(self, request):
        user, error = self.validate(request)
        if error:
            return error

        self.clear_sessions(user)
        login(request, user)

        # Session ga panel turini yozamiz
        request.session["panel"] = "superadmin" if self.allow_superadmin else "admin"
        default_org = user.organizations.exclude(slug="system").first()
        request.session["current_org_id"] = default_org.id if default_org else None
        request.session.save()

        return Response({
            "ok": True,
            "redirect": self.get_redirect_url()
        })


class AdminLogout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"ok": True})


class Admin_Users(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        admin=AdminUser.objects.get(id=request.user.id)
        users=Users.objects.filter(organization=request.session.get("current_org_id"))
        print("Admin's organization:", admin.organizations)
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
        organization=admin.organizations.filter(id=request.session.get("current_org_id")).first()
        role= Role.objects.filter(id=request.data.get("role_id"), organization=organization).first()
        print(request.data, organization)
        # new_user = Users.objects.create_user(
        #     role=role,
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
        return Response({"users": "User creation endpoint is under development."}, status=200)
        

class Super_AdminLogin(AdminLogin):
    allow_superadmin = True
    

class Super_AdminLogout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        



