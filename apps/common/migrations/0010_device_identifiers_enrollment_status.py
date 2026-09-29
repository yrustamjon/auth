from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("common", "0009_device_platform")]

    operations = [
        migrations.AddField(
            model_name="device",
            name="identifiers",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="device",
            name="enrollment_status",
            field=models.CharField(
                choices=[("manual_registered", "Manual registration")],
                default="manual_registered",
                max_length=32,
            ),
        ),
    ]
