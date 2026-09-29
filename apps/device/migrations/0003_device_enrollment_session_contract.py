from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("device", "0002_session_lifecycle")]

    operations = [
        migrations.RenameModel(
            old_name="BrowserEnrollmentSession",
            new_name="DeviceEnrollmentSession",
        ),
    ]
