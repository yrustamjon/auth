from django.db import models
from django.utils import timezone
from datetime import timedelta
import secrets

from apps.common.models import Organization


class OrgToken(models.Model):
    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='org_tokens'
    )
    token = models.CharField(max_length=255, unique=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)

        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)

        super().save(*args, **kwargs)

    @classmethod
    def cleanup_expired(cls):
        cls.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()

    def __str__(self):
        return f"{self.org} - {self.token}"