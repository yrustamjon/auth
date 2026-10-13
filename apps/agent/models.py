import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta

from apps.common.models import *


class AgentSession(models.Model):
    request_context = models.JSONField(default=dict, blank=True)
    fingerprint_challenge = models.BinaryField(null=True, blank=True)
    fingerprint_challenge_expires = models.DateTimeField(null=True, blank=True)
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("expired", "Expired"),
    ]

    device = models.ForeignKey('common.Device', on_delete=models.CASCADE, null=True, blank=True)

    user = models.ForeignKey(
        Users,
        on_delete=models.CASCADE,
        related_name="agent_sessions"
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
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)
    
    @classmethod
    def cleanup_expired(cls):
        cls.objects.filter(
            expires_at__lt=timezone.now(),
        ).delete()
    def __str__(self):
        return f"{self.user} - {self.session_id}"



class RequestNonce(models.Model):
    certificate_id = models.CharField(max_length=255)
    nonce = models.CharField(max_length=128)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['certificate_id', 'nonce'], name='unique_device_request_nonce')]


class AgentHealth(models.Model):
    device=models.OneToOneField(Device,on_delete=models.CASCADE,related_name='agent_health')
    last_heartbeat=models.DateTimeField()
    last_ip=models.GenericIPAddressField(null=True,blank=True)
    state=models.CharField(max_length=16,default='running')
    loss_reported=models.BooleanField(default=False)
    pause_until=models.DateTimeField(null=True,blank=True)


class AgentEvent(models.Model):
    organization=models.ForeignKey(Organization,on_delete=models.CASCADE)
    device=models.ForeignKey(Device,on_delete=models.SET_NULL,null=True,blank=True)
    device_key=models.PositiveBigIntegerField()
    event_id=models.UUIDField(default=uuid.uuid4)
    kind=models.CharField(max_length=40)
    severity=models.CharField(max_length=16,default='info')
    timestamp=models.DateTimeField(auto_now_add=True)
    reported_at=models.DateTimeField(null=True,blank=True)
    ip_address=models.GenericIPAddressField(null=True,blank=True)
    device_snapshot=models.JSONField(default=dict)
    details=models.JSONField(default=dict)
    actor=models.CharField(max_length=255,blank=True,default='')

    class Meta:
        constraints=[models.UniqueConstraint(fields=['device_key','event_id'],name='unique_agent_event')]
        indexes=[models.Index(fields=['organization','-timestamp'])]
