from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("device", "0003_device_enrollment_session_contract")]

    operations = [
        migrations.AlterModelTable(
            name="deviceenrollmentsession",
            table="device_deviceenrollmentsession",
        ),
    ]
