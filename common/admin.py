# common/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
from .forms import AdminUserCreationForm, AdminUserChangeForm

class AdminUserAdmin(BaseUserAdmin):
    form = AdminUserChangeForm
    add_form = AdminUserCreationForm

    list_display = ("username", "is_active", "is_staff", "is_superadmin")
    list_filter = ("is_active", "is_staff", "is_superadmin")

    fieldsets = (
        (None, {"fields": ("username", "organization", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_superadmin", "is_active")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username","organization", "password1", "password2"),
        }),
    )

    search_fields = ("username",)
    ordering = ("username",)
    filter_horizontal = ()

admin.site.register(AdminUser, AdminUserAdmin)
admin.site.register(Organization)
