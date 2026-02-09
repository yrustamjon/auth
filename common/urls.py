from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_page, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("users/", views.users_page, name="users"),
    path("roles/", views.roles_page, name="roles"),
    path("devices/", views.devices_page, name="devices"),
    path("logs/", views.logs_page, name="logs"),
    path("api/admin/login", views.AdminLogin.as_view(), name="admin_login"),
    path("api/admin/logout", views.AdminLogout.as_view(), name="logout"),
]
