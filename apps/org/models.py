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
    def _org_filter_kwargs(cls, org):
        if isinstance(org, Organization):
            return {"org": org}
        return {"org_id": org}

    @classmethod
    def cleanup_expired(cls):
        cls.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()

    @classmethod
    def get_active_for_org(cls, org):
        cls.cleanup_expired()
        org_filter = cls._org_filter_kwargs(org)

        tokens = cls.objects.filter(
            is_used=False,
            expires_at__gt=timezone.now(),
            **org_filter,
        ).order_by("-expires_at", "-id")

        token = tokens.first()
        if not token:
            return None

        tokens.exclude(id=token.id).update(is_used=True)
        return token

    @classmethod
    def get_or_create_active_for_org(cls, org):
        token = cls.get_active_for_org(org)
        if token:
            return token

        org_filter = cls._org_filter_kwargs(org)
        cls.objects.filter(is_used=False, **org_filter).update(is_used=True)
        return cls.objects.create(**org_filter)

    @classmethod
    def rotate_daily_for_org(cls, org):
        org_filter = cls._org_filter_kwargs(org)
        cls.objects.filter(is_used=False, **org_filter).update(is_used=True)
        cls.cleanup_expired()
        return cls.objects.create(**org_filter)

    def __str__(self):
        return f"{self.org} - {self.token}"
