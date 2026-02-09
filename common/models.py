from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.contrib.auth.models import BaseUserManager

class AdminUserManager(BaseUserManager):
    def _get_default_org(self):
        from .models import Organization
        return Organization.objects.filter(is_default=True).first()

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Username is required")

        # agar createsuperuser bilan yaratilsa — default beramiz
        if "organization" not in extra_fields or extra_fields["organization"] is None:
            default_org = self._get_default_org()
            if not default_org:
                raise ValueError("Default organization is not configured")
            extra_fields["organization"] = default_org

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_superadmin", True)

        return self.create_user(username, password, **extra_fields)


class Organization(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)   # for system ex: "org1", "org2"
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    




class AdminUser(AbstractBaseUser, PermissionsMixin):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="admin_users")
    username = models.CharField(max_length=150, unique=True)

    is_superadmin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = AdminUserManager()

    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username



class Users(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="users")
    fio=models.CharField(max_length=255)
    lavozim=models.CharField(max_length=255) # lavozim
    username=models.CharField(max_length=255, unique=True)
    status=models.BooleanField(default=True) # true - active, false - inactive(bloklangan hardoim atkaz)

    def __str__(self):
        return self.fio

class Roles(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="roles")
    name=models.CharField(max_length=255) # Admin, User, etc.
    def __str__(self):
        return self.name

class UserRoles(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="user_roles")
    user=models.ForeignKey(Users,on_delete=models.CASCADE)
    role=models.ForeignKey(Roles,on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user} - {self.role}"

class Devices(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="devices")
    pc_id=models.CharField(max_length=255)
    location=models.CharField(max_length=255)

    def __str__(self):
        return self.pc_id

class BiometricFace(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="biometric_faces")
    user=models.ForeignKey(Users,on_delete=models.CASCADE)
    embedding=models.TextField()

    def __str__(self):
        return f"BiometricFace: {self.user}"

class BiometricFingerprint(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="biometric_fingerprints")
    user=models.ForeignKey(Users,on_delete=models.CASCADE)
    embedding=models.TextField()

    def __str__(self):
        return f"BiometricFingerprint: {self.user}"

class AccessLogs(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="access_logs")
    timestamp=models.DateTimeField(auto_now_add=True)
    user=models.ForeignKey(Users,on_delete=models.CASCADE)
    device=models.ForeignKey(Devices,on_delete=models.CASCADE)
    success=models.BooleanField(default=False)
    cause=models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"AccessLog: {self.user} - {self.device} - {'Success' if self.success else 'Failure'}"