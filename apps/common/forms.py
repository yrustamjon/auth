# common/forms.py
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import AdminUser

class AdminUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    class Meta:
        model = AdminUser
        fields = ("username",)

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Passwords do not match")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # 🔥 HASH
        if commit:
            user.save()
        return user


class AdminUserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = AdminUser
        fields = ("username", "password", "is_active", "is_staff", "is_superadmin")

    def clean_password(self):
        return self.initial["password"]
