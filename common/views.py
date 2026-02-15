from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.sessions.models import Session
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import *

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
    print(request.user.is_authenticated)
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, "login.html")

@login_required
@sender_about_user
def dashboard(request, data):
    data["page_title"]="Dashboard"
    data["page_icon"]="fas fa-tachometer-alt"
    return render(request, "dashboard.html", data)

@login_required
@sender_about_user
def users_page(request, data):
    print("Data in users_page:", data)
    data["page_title"]="User Management"
    data["page_icon"]="fas fa-users"
    return render(request, "users.html",data)

@login_required
@sender_about_user
def roles_page(request, data):
    data["page_title"]="Role Management"
    data["page_icon"]="fas fa-user-tag"
    return render(request, "roles.html", data)


@login_required
@sender_about_user
def devices_page(request, data):
    data["page_title"]="Device Management"
    data["page_icon"]="fas fa-desktop"
    return render(request, "devices.html", data)

@login_required
@sender_about_user
def logs_page(request, data):
    data["page_title"]="Logs"
    data["page_icon"]="fas fa-clipboard-list"
    return render(request, "logs.html", data)


class AdminLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print(AdminUser.objects.filter(username=request.data.get("username")).first())
        user=AdminUser.objects.filter(username=request.data.get("username")).first()
        print("User found:", user.is_locked() )
        if user and user.is_locked():

            print("Failed attempts after reset:", user.locked_until - timezone.now())
            return Response({"detail": f"Account is locked.Try again {int((user.locked_until - timezone.now()).total_seconds() // 60)}:{int((user.locked_until - timezone.now()).total_seconds() % 60)} later."}, status=403)

        user = authenticate(
            request,
            username=request.data.get("username"),
            password=request.data.get("password")
        )

        print("User", user is not None, "logged in")

        if not user:
            user = AdminUser.objects.filter(username=request.data.get("username")).first()
            if user:
                user.register_failed_attempt()

            return Response({"detail": "Invalid credentials"}, status=401)

        active_sessions = Session.objects.filter(
            expire_date__gte=timezone.now()
        )

        print("Active sessions:", active_sessions.count())
        if user_sessions := list(
            filter(
                lambda s: s.get_decoded().get("_auth_user_id") == str(user.id),
                active_sessions,
            )
        ):
            print(f"User {user.username} has {len(user_sessions)} active sessions. Deleting them.")
            for session in user_sessions:
                session.delete()




        login(request, user)

        return Response({"ok": True})


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
        return Response({"detail": "User creation endpoint is not implemented yet."}, status=501)
        


