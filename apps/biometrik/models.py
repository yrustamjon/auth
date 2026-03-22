import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta

from apps.common.models import *



class FingerprintSession(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("expired", "Expired"),
    ]

    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="fingerprint_sessions"
    )

    session_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=2)
        super().save(*args, **kwargs)
    
    @classmethod
    def cleanup_expired(cls):
        cls.objects.filter(
            expires_at__lt=timezone.now(),
        ).delete()
    def __str__(self):
        return f"{self.user} - {self.session_id}"
