from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.contrib.auth.models import BaseUserManager
from datetime import timedelta
from django.utils import timezone


from utils.crypto import encrypt_data, decrypt_data



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
    username = models.CharField(max_length=150, unique=True)  # unique_together orqali tekshiramiz

    is_superadmin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    failed_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField( null=True, blank=True)

    objects = AdminUserManager()

    USERNAME_FIELD = 'username'


    def is_locked(self):
        
        return bool(self.locked_until and self.locked_until > timezone.now())
    

    def register_failed_attempt(self,max_attempts=5, lock_duration_minutes=15):
        if self.is_locked():
            return
    
        self.failed_attempts +=1

        if self.failed_attempts >= max_attempts: # 5 ta xato urinishdan keyin bloklash
            self.locked_until = timezone.now() + timedelta(minutes=lock_duration_minutes) # 15 daqiqa bloklash
            self.failed_attempts = 0 # urinishlarni reset qilish
        
        self.save(update_fields=['failed_attempts', 'locked_until'])

    def reset_failed_attempts(self):
        if self.failed_attempts > 0 or self.locked_until:
            self.failed_attempts = 0
            self.locked_until = None
            self.save(update_fields=['failed_attempts', 'locked_until'])


    def __str__(self):
        return self.username



class Users(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="users")
    role = models.ForeignKey('Roles', on_delete=models.SET_NULL, null=True, related_name="users")
    fio=models.CharField(max_length=255)
    lavozim=models.CharField(max_length=255) # lavozim
    username=models.CharField(max_length=255)
    status=models.BooleanField(default=True) # true - active, false - inactive(bloklangan hardoim atkaz)

    failed_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)


    def is_locked(self):
        return bool(self.locked_until and self.locked_until > timezone.now())
    

    def register_failed_attempt(self,max_attempts=5, lock_duration_minutes=5):
        if self.is_locked():
            return
    
        self.failed_attempts +=1

        if self.failed_attempts >= max_attempts: # 5 ta xato urinishdan keyin bloklash
            self.locked_until = timezone.now() + timedelta(minutes=lock_duration_minutes) # 15 daqiqa bloklash
            self.failed_attempts = 0 # urinishlarni reset qilish
        
        self.save(update_fields=['failed_attempts', 'locked_until'])

    def reset_failed_attempts(self):
        if self.failed_attempts > 0 or self.locked_until:
            self.failed_attempts = 0
            self.locked_until = None
            self.save(update_fields=['failed_attempts', 'locked_until'])
    
    class Meta:
        unique_together = ('organization', 'username')
    def __str__(self):
        return self.fio

class Roles(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="roles")
    name=models.CharField(max_length=255) # Admin, User, etc.
    def __str__(self):
        return self.name



class Devices(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="devices")
    pc_id=models.CharField(max_length=255)
    location=models.CharField(max_length=255)
    is_active=models.BooleanField(default=True)
    last_seen=models.DateTimeField(auto_now=True)
    revoked=models.BooleanField(default=False)
    registered_at = models.DateTimeField(auto_now_add=True, null=True)
    device_public_key=models.TextField(blank=True, null=True) # agar kerak bo'lsa, qurilmaning public key sini saqlash uchun

    class Meta:
        unique_together = ('organization', 'pc_id')


    def __str__(self):
        return self.pc_id

class BiometricFace(models.Model):
    user = models.OneToOneField(
        Users,
        on_delete=models.CASCADE,
        related_name="face"
    )
    embedding = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def  set_embedding(self, raw_embedding):
        self.embedding = encrypt_data(raw_embedding)
        
    def get_embedding(self):
        if not self.embedding:
            return None
        return decrypt_data(self.embedding)

    def __str__(self):
            return f"BiometricFace: {self.user}"


class BiometricFingerprint(models.Model):
    user = models.OneToOneField(
        Users,
        on_delete=models.CASCADE,
        related_name="fingerprint"
    )
    embedding = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_embedding(self, raw_embedding):
        self.embedding = encrypt_data(raw_embedding)

    def get_embedding(self):
        if not self.embedding:
            return None
        return decrypt_data(self.embedding)

    def __str__(self):
            return f"BiometricFingerprint: {self.user}"

class AccessLogs(models.Model):
    timestamp=models.DateTimeField(auto_now_add=True)
    user=models.ForeignKey(Users,on_delete=models.CASCADE)
    device=models.ForeignKey(Devices,on_delete=models.CASCADE)
    success=models.BooleanField(default=False)
    cause=models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['device', '-timestamp']),
        ]

    def __str__(self):
        return f"AccessLog: {self.user} - {self.device} - {'Success' if self.success else 'Failure'}"