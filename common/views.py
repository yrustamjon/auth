from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from .models import *
from django.contrib.auth.decorators import login_required


def sender_about_user(view_func):
    def wrapper(request, *args, **kwargs):
        data = {
            "username": request.user.username,
            "organization": request.user.organization.name if request.user.organization else None,
            "is_superadmin": request.user.is_superadmin,
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
    return render(request, "dashboard.html", data)

@login_required
@sender_about_user
def users_page(request, data):
    print("Data in users_page:", data)
    return render(request, "users.html", data)

@login_required
@sender_about_user
def roles_page(request, data):
    return render(request, "roles.html", data)


@login_required
@sender_about_user
def devices_page(request, data):
    return render(request, "devices.html", data)

@login_required
@sender_about_user
def logs_page(request, data):
    return render(request, "logs.html", data)




from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.utils import timezone

class AdminLogin(APIView):
    permission_classes = [AllowAny]


    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        print("User", user is not None, "logged in")

        if not user:
            return Response({"detail": "Invalid credentials"}, status=401)

        active_sessions = Session.objects.filter(
            expire_date__gte=timezone.now()
        )
        
        print("Active sessions:", active_sessions.count())
        user_sessions = list(
            filter(
                lambda s: s.get_decoded().get("_auth_user_id") == str(user.id), 
                active_sessions
                )
            )
        
        if user_sessions:
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
