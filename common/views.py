from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from .models import *
from django.contrib.auth.decorators import login_required

def login_page(request):
    print(request.user.is_authenticated)
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, "login.html")

@login_required
def dashboard(request):
    return render(request, "dashboard.html")


def users_page(request):
    return render(request, "users.html")

def roles_page(request):
    return render(request, "roles.html")


def devices_page(request):
    return render(request, "devices.html")


def logs_page(request):
    return render(request, "logs.html")




from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import logout

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

        # 🔥 MANA ENG MUHIM QATOR
        login(request, user)

        # 🔍 DEBUG (xohlasang vaqtincha)
        print("SESSION KEY:", request.session.session_key)

        return Response({"ok": True})

class AdminLogout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"ok": True})
