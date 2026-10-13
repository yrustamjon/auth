import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock
from django.test import SimpleTestCase


class RemovalGenerationMigrationTests(SimpleTestCase):
    def run_migration(self, columns):
        migration = importlib.import_module('apps.device.migrations.0006_removal_code_generation')
        apps, editor = MagicMock(), MagicMock()
        model = apps.get_model.return_value
        editor.connection.introspection.get_table_description.return_value = [
            SimpleNamespace(name=name) for name in columns]
        migration.ensure_generation_column(apps, editor)
        return model, editor

    def test_already_created_generation_column_is_not_added_twice(self):
        _, editor = self.run_migration(['id', 'certificate_generation'])
        editor.add_field.assert_not_called()

    def test_original_applied_schema_gets_generation_field(self):
        model, editor = self.run_migration(['id', 'code_digest'])
        editor.add_field.assert_called_once()
        args = editor.add_field.call_args.args
        self.assertIs(args[0], model)
        self.assertEqual(args[1].name, 'certificate_generation')
        self.assertEqual(args[1].max_length, 255)
