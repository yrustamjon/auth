# Generated manually for the Device platform metadata field.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0008_remove_biometricfingerprint_challenge_device_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="device",
            name="platform",
            field=models.CharField(
                choices=[
                    ("windows", "Windows"),
                    ("macos", "macOS"),
                    ("linux", "Linux"),
                ],
                db_index=True,
                default="windows",
                max_length=16,
            ),
        ),
    ]
