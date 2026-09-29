import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [("common", "0011_device_browser_approved_status")]

    operations = [
        migrations.CreateModel(
            name="BrowserEnrollmentAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creator_session_hash", models.CharField(max_length=64)),
                ("source_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="BrowserEnrollmentAudit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("session_id", models.UUIDField()),
                ("event", models.CharField(max_length=32)),
                ("reason", models.CharField(blank=True, max_length=64)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="common.adminuser")),
                ("organization", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="common.organization")),
            ],
        ),
        migrations.CreateModel(
            name="BrowserEnrollmentSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("scan_token_hash", models.CharField(blank=True, max_length=64)),
                ("creator_session_hash", models.CharField(max_length=64)),
                ("claimant_session_hash", models.CharField(blank=True, max_length=64)),
                ("browser_device_id", models.UUIDField(default=uuid.uuid4, unique=True)),
                ("requested_device_id", models.CharField(blank=True, max_length=255)),
                ("identifiers", models.JSONField(blank=True, default=dict)),
                ("hostname", models.CharField(blank=True, max_length=255)),
                ("platform", models.CharField(blank=True, choices=[("windows", "Windows"), ("macos", "macOS"), ("linux", "Linux")], default="", max_length=16)),
                ("location", models.CharField(max_length=255)),
                ("display_code", models.CharField(max_length=6)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected"), ("expired", "Expired"), ("cancelled", "Cancelled")], default="pending", max_length=16)),
                ("expires_at", models.DateTimeField()),
                ("identity_received_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("claimed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="claimed_browser_sessions", to="common.adminuser")),
                ("device", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="common.device")),
                ("organization", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="common.organization")),
            ],
        ),
    ]
