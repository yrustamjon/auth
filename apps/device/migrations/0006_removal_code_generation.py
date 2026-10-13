from django.db import migrations, models


def ensure_generation_column(apps, schema_editor):
    """Repair both original and briefly shipped expanded 0005 schemas."""
    model = apps.get_model('device', 'DeviceRemovalCode')
    with schema_editor.connection.cursor() as cursor:
        columns = schema_editor.connection.introspection.get_table_description(cursor, model._meta.db_table)
    if any(column.name == 'certificate_generation' for column in columns):
        return
    field = models.CharField(max_length=255, blank=True)
    field.set_attributes_from_name('certificate_generation')
    schema_editor.add_field(model, field)


class Migration(migrations.Migration):
    dependencies = [('device', '0005_device_removal')]
    operations = [migrations.SeparateDatabaseAndState(
        database_operations=[migrations.RunPython(ensure_generation_column, migrations.RunPython.noop)],
        state_operations=[migrations.AddField(model_name='deviceremovalcode',
            name='certificate_generation', field=models.CharField(max_length=255, blank=True))],
    )]
