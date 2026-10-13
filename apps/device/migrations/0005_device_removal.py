import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('device', '0004_alter_deviceenrollmentsession_table'), ('common', '0015_device_removal_state'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='DeviceRemovalCode', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('code_digest', models.CharField(max_length=64, unique=True)),
            ('expires_at', models.DateTimeField()), ('created_at', models.DateTimeField(auto_now_add=True)),
            ('used_at', models.DateTimeField(blank=True, null=True)), ('invalidated_at', models.DateTimeField(blank=True, null=True)),
            ('device', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='removal_codes', to='common.device')),
            ('issuer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.CreateModel(name='DeviceRemoval', fields=[
            ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ('old_certificate', models.CharField(blank=True, max_length=255)), ('old_public_key', models.TextField(blank=True)),
            ('recovery_public_key', models.TextField()),
            ('state', models.CharField(max_length=24, default='removal_pending', choices=[('removal_pending', 'Removal pending'), ('removed', 'Removed')])),
            ('started_at', models.DateTimeField()), ('completed_at', models.DateTimeField(blank=True, null=True)),
            ('device', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='removal_operations', to='common.device')),
            ('issuer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
        ]),
    ]
