from django.urls import path
from . import views
from . import registration
from . import downloads
from .personal import PersonalProfile
from .account_profile import AccountProfile, AccountPassword

urlpatterns = [
    path('api/profile/', AccountProfile.as_view()),
    path('api/profile/password/', AccountPassword.as_view()),
    path('api/personal/',PersonalProfile.as_view()),
    path('api/downloads/',downloads.catalog),
    path('api/downloads/<str:platform>/',downloads.download),
    path('api/register/', registration.register),
    path('api/registration/status/', registration.registration_status),
    path('api/registration/applications/', registration.applications),
    path('api/registration/<int:org_id>/decision/', registration.decision),
    path('api/session/', views.frontend_session, name='frontend_session'),
    path("", views._, name="home"),
    path("login/", views.login_page, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("users/", views.users_page, name="users"),
    path("roles/", views.roles_page, name="roles"),
    path("devices/", views.devices_page, name="devices"),
    path("logs/", views.logs_page, name="logs"),

    path("system/login/", views.System_Login, name="system_login"),
    path("system/dashboard/", views.System_Dashboard, name="system_dashboard"),
    path("system/organizations/", views.system_orgag, name="system_organizations"),
    path("system/admins/", views.system_admins, name="system_admins"),

    path("api/admin/login", views.AdminLogin.as_view(), name="admin_login"),
    path("api/admin/logout", views.AdminLogout.as_view(), name="logout"),
    path("api/users/", views.Admin_Users.as_view(), name="admin_users"),
    path("api/users/<int:id>/", views.Admin_Users.as_view()),


    path("api/system/admins/", views.Admin.as_view(), name="system_admins_api"),
    path("api/system/admins/<int:id>/", views.Admin.as_view()),
    
    


    path("api/system/login", views.Super_AdminLogin.as_view()),
    path("api/system/logout", views.Super_AdminLogout.as_view(), name="system_logout"),

    path("api/system/admins/<int:id>/force-logout/", views.ForceLogoutAdmin.as_view()),
]
