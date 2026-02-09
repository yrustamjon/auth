# common/models.py
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
# common/models.py
from django.contrib.auth.models import BaseUserManager

class AdminUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")

        user = self.model(username=username, **extra_fields)
        user.set_password(password)   # 🔐 HASH
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_superadmin', True)

        return self.create_user(username, password, **extra_fields)


class AdminUser(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)

    is_superadmin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = AdminUserManager()  # 👈 ENG MUHIM QATOR

    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username



class Users(models.Model):
    fio=models.CharField(max_length=255)
    lavozim=models.CharField(max_length=255) # lavozim
    username=models.CharField(max_length=255, unique=True)
    status=models.BooleanField(default=True) # true - active, false - inactive(bloklangan hardoim atkaz)

    def __str__(self):
        return self.fio

class Roles(models.Model):
    name=models.CharField(max_length=255) # Admin, User, etc.
    def __str__(self):
        return self.name

class UserRoles(models.Model):
    user=models.ForeignKey(Users,on_delete=models.CASCADE)
    role=models.ForeignKey(Roles,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} - {self.role}"

class Devices(models.Model):
    pc_id=models.CharField(max_length=255)
    location=models.CharField(max_length=255)

    def __str__(self):
        return self.pc_id

class BiometricFace(models.Model):
    user=models.ForeignKey(Users,on_delete=models.CASCADE)
    embedding=models.TextField()

    def __str__(self):
        return f"BiometricFace: {self.user}"

class BiometricFingerprint(models.Model):
    user=models.ForeignKey(Users,on_delete=models.CASCADE)
    embedding=models.TextField()

    def __str__(self):
        return f"BiometricFingerprint: {self.user}"

class AccessLogs(models.Model):
    timestamp=models.DateTimeField(auto_now_add=True)
    user=models.ForeignKey(Users,on_delete=models.CASCADE)
    device=models.ForeignKey(Devices,on_delete=models.CASCADE)
    success=models.BooleanField(default=False)
    cause=models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"AccessLog: {self.user} - {self.device} - {'Success' if self.success else 'Failure'}"