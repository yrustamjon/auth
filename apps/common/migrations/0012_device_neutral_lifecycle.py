from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("common", "0011_device_browser_approved_status")]

    operations = [
        migrations.AddField(
            model_name="device", name="attestation_status",
            field=models.CharField(
                max_length=32, default="not_provided",
                choices=[("not_provided", "Not provided"), ("verified", "Verified")],
            ),
        ),
        migrations.AddField(
            model_name="device", name="enrolled_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="device", name="revoked_at",
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name="device", name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="device", name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterField(
            model_name="device", name="enrollment_status",
            field=models.CharField(
                max_length=32, default="manual_registered",
                choices=[
                    ("manual_registered", "Manual registration"),
                    ("browser_approved", "Browser approved"),
                    ("agent_enrolled", "Agent enrolled"),
                ],
            ),
        ),
    ]
