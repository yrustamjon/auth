from django.db import migrations, models


def occupied(apps, schema_editor):
    Device = apps.get_model('common', 'Device')
    Device.objects.filter(enrollment_status='agent_enrolled', cert__isnull=False).exclude(cert='').update(agent_allocation_active=True)


class Migration(migrations.Migration):
    dependencies = [('common', '0014_organization_approval_status_organization_kind_and_more')]
    operations = [
        migrations.AddField(model_name='device', name='removal_state', field=models.CharField(max_length=24, default='active', choices=[('active', 'Active'), ('removal_pending', 'Removal pending'), ('removed', 'Removed')])),
        migrations.AddField(model_name='device', name='agent_allocation_active', field=models.BooleanField(default=False)),
        migrations.RunPython(occupied, migrations.RunPython.noop),
    ]
