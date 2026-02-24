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
            if not request.user.is_authenticated :
                if not request.user.is_superadmin:
                    return redirect('login')
                return redirect('system/login')

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
    else:
        if request.session.get("panel") == "superadmin":
            return redirect('system/login')
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
            if user.is_superadmin and user.organizations.count() == 1 and user.organizations.first().slug == "system":
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
        print("Login attempt data:", request.data)
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
                "fio": user.fio,
                "lavozim": user.lavozim,
                "username": user.username,
                "role": {
                    "id": user.role.id if user.role else None,
                    "name": user.role.name if user.role else None,
                },
                "creted_at": user.creted_at,
                "is_locked": user.is_locked(),
            }
            for user in users
        ]
        return Response({"users": users_data})
    
    def post(self, request):
        organization=Organization.objects.filter(id=request.session.get("current_org_id")).first()
        role= Roles.objects.filter(id=request.data.get("role_id"), organization=organization).first()
        print(request.data, organization)
        new_user = Users.objects.create(
            role=role,
            fio=request.data.get("fio"),
            username=request.data.get("username"),
            lavozim=request.data.get("lavozim"),
            organization=organization,
        )
        

        return Response({
            "id": new_user.id,
            "username": new_user.username,
            "fio": new_user.fio,
            "lavozim": new_user.lavozim,
            "role": {
                "id": role.id,
                "name": role.name,
            },
            "creted_at": new_user.created_at,
        })
    
    def patch(self, request, id):
        status=request.data.get("status")
        user=Users.objects.filter(id=id).first()
        # {'fio': 'Rustamjon Yolchiyev', 'lavozim': 'IT manager', 'username': 'coder05', 'role_id': 1, 'status': False}
        if (
            'fio' not in request.data
            and 'lavozim' not in request.data
            and 'username' not in request.data
            and 'role_id' not in request.data
            and 'status' not in request.data
        ):
            user.status=not user.status
            user.save()
            return Response({"ok": True})

        print(request.data)
        return Response({"ok": True})

class Super_AdminLogin(AdminLogin):
    allow_superadmin = True


class Super_AdminLogout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"ok": True})
    
class Admin(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        org_id = request.query_params.get("organization_id")
        if org_id:
            admins = AdminUser.objects.filter(organizations__id=org_id)
        else:
            admins = AdminUser.objects.all()
        

        admin_data = [
            {
                "id": admin.id,
                "username": admin.username,
                "superadmin": admin.is_superadmin,
                "is_active": admin.is_active,
                "locked": admin.is_locked(),
                "failed_attempts": admin.failed_attempts,
                "organization": [org.name for org in admin.organizations.all() if not org.slug == "system"],
                "created_at": admin.created_at,
            }for admin in admins
        ]
        return Response(admin_data)
    

    def post(self, request,id=None,reset_attempts=None):
        print(request.data)
        new_admin = AdminUser.objects.create_superuser(
            username=request.data.get("username"),
            password=request.data.get("password"),
            is_superadmin=request.data.get("is_superuser", False)
        )
        if request.data.get("organization_id"):
            new_admin.organizations.add(Organization.objects.filter(id=request.data.get("organization_id")).first())
        
        
        return Response({
            "id": new_admin.id,
            "username": new_admin.username,
            "superadmin": new_admin.is_superadmin,
            "locked": new_admin.is_locked(),
            "is_active": new_admin.is_active,
        })

    
    def patch(self, request, id):
        print(f"Received PATCH request for admin id {id} with data:", request.data)
        
            
            
        org_id = request.query_params.get("organization_id")
        print(f"Updating admin with id {id} for organization_id: {org_id}")
        admin = AdminUser.objects.filter(id=id).first()
        if not admin:
            return Response({"detail": "Admin not found"}, status=404)

        if 'username' in request.data or 'is_superuser' in request.data:
            username = request.data.get("username")
            is_superadmin = request.data.get("is_superuser")
            
            if username:
                admin.username = username
            if is_superadmin is not None:
                admin.is_superadmin = is_superadmin
            
            admin.save()
            return Response({"ok": True})
        
        if passsword := request.data.get("password"):
            admin.set_password(passsword)
            admin.save()
            return Response({"ok": True})

        if org_id:
            org = Organization.objects.filter(id=org_id).first()
            if not org:
                return Response({"detail": "Organization not found"}, status=404)
            if org in admin.organizations.all():
                admin.organizations.remove(org)
                action = "removed from"
            else:
                admin.organizations.add(org)
                action = "added to"
            return Response({"ok": True, "detail": f"Admin {action} organization"})

        try:
            if request.data['locked'] is not None:
                print(f"Locking admin {admin.username} until {admin.locked_until}")
                if request.data['locked'] is True and not admin.is_locked():
                    admin.locked_until = timezone.now() + timezone.timedelta(minutes=15)
                elif request.data['locked'] is False:
                    admin.locked_until = None
                admin.save()
                return Response({"ok": True})
        except KeyError:
            print("No 'locked' field in request data")
        return Response({"detail": "Invalid data"}, status=400)
    

    def delete(self, request, id):
        admin = AdminUser.objects.filter(id=id).first()
        org_id = request.query_params.get("organization_id")
        print(f"Attempting to delete admin with id {id} from organization_id: {org_id}")
        if org_id:
            admin.organizations.remove(Organization.objects.filter(id=org_id).first())
            return Response({"ok": True})
        print(f"Attempting to delete admin with id {id}: {'Found' if admin else 'Not found'}")
        if admin:
            admin.delete()
            return Response({"ok": True})
        return Response({"detail": "Admin not found"}, status=404)