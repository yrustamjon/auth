from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("common", "0010_device_identifiers_enrollment_status")]

    operations = [
        migrations.AlterField(
            model_name="device",
            name="enrollment_status",
            field=models.CharField(
                choices=[
                    ("manual_registered", "Manual registration"),
                    ("browser_approved", "Browser approved"),
                ],
                default="manual_registered",
                max_length=32,
            ),
        ),
    ]
