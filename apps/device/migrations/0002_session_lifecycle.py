import hashlib

from django.db import migrations, models
from django.utils import timezone
import django.db.models.deletion


def close_legacy_pending_sessions(apps, schema_editor):
    Session = apps.get_model("device", "BrowserEnrollmentSession")
    now = timezone.now()
    for session in Session.objects.all().iterator():
        session.display_code_hash = hashlib.sha256(session.display_code.encode("utf-8")).hexdigest()
        if session.status == "pending":
            session.status = "expired"
            session.resolved_at = now
        session.save(update_fields=["display_code_hash", "status", "resolved_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("device", "0001_browser_enrollment"),
        ("common", "0012_device_neutral_lifecycle"),
    ]

    operations = [
        migrations.AddField(
            model_name="browserenrollmentsession", name="display_code_hash",
            field=models.CharField(max_length=64, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="browserenrollmentsession", name="claimed_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="browserenrollmentsession", name="approved_by",
            field=models.ForeignKey(
                to="common.adminuser", null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="approved_browser_sessions",
            ),
        ),
        migrations.AddField(
            model_name="browserenrollmentsession", name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.RunPython(close_legacy_pending_sessions, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="browserenrollmentsession", name="display_code",
        ),
        migrations.AlterField(
            model_name="browserenrollmentsession", name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
