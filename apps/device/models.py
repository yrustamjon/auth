import uuid

from django.db import models


class DeviceEnrollmentSession(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token_hash = models.CharField(max_length=64, unique=True)
    scan_token_hash = models.CharField(max_length=64, blank=True)
    creator_session_hash = models.CharField(max_length=64)
    claimant_session_hash = models.CharField(max_length=64, blank=True)
    browser_device_id = models.UUIDField(default=uuid.uuid4, unique=True)
    requested_device_id = models.CharField(max_length=255, blank=True)
    identifiers = models.JSONField(default=dict, blank=True)
    hostname = models.CharField(max_length=255, blank=True)
    platform = models.CharField(max_length=16, blank=True, default="", choices=[
        ("windows", "Windows"), ("macos", "macOS"), ("linux", "Linux")
    ])
    location = models.CharField(max_length=255)
    display_code_hash = models.CharField(max_length=64)
    organization = models.ForeignKey(
        "common.Organization", null=True, blank=True, on_delete=models.SET_NULL
    )
    claimed_by = models.ForeignKey(
        "common.AdminUser", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="claimed_browser_sessions",
    )
    approved_by = models.ForeignKey(
        "common.AdminUser", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="approved_browser_sessions",
    )
    device = models.OneToOneField(
        "common.Device", null=True, blank=True, on_delete=models.SET_NULL
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    expires_at = models.DateTimeField()
    identity_received_at = models.DateTimeField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "device_deviceenrollmentsession"

    @property
    def session_id(self):
        return self.id

    @property
    def browser_session_hash(self):
        return self.creator_session_hash

    @property
    def platform_claimed(self):
        return self.platform

    @property
    def device_metadata(self):
        return {
            "device_id": self.requested_device_id,
            "identifiers": self.identifiers,
            "hostname": self.hostname,
            "location": self.location,
        }


# Compatibility import for code written before the canonical model name.
BrowserEnrollmentSession = DeviceEnrollmentSession


class BrowserEnrollmentAudit(models.Model):
    session_id = models.UUIDField()
    organization = models.ForeignKey(
        "common.Organization", null=True, blank=True, on_delete=models.SET_NULL
    )
    actor = models.ForeignKey(
        "common.AdminUser", null=True, blank=True, on_delete=models.SET_NULL
    )
    event = models.CharField(max_length=32)
    reason = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class BrowserEnrollmentAttempt(models.Model):
    creator_session_hash = models.CharField(max_length=64)
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
