import importlib
import os
import sys
import tempfile
import unittest
from unittest.mock import patch


def load_config(environment: dict[str, str]):
    """Import config with isolated runtime storage and supplied environment."""
    with tempfile.TemporaryDirectory() as app_data:
        values = {"APPDATA": app_data, **environment}
        with patch.dict(os.environ, values, clear=False):
            sys.modules.pop("core.config", None)
            return importlib.import_module("core.config")


class ConfigurationDefaultsTests(unittest.TestCase):
    def test_prerelease_controls_cannot_be_hidden_by_environment(self):
        config = load_config({"ADBIOGUARD_ENV": "production"})
        for environment in ("production", "development", "testing"):
            with self.subTest(environment=environment):
                settings = config.get_settings({
                    "ADBIOGUARD_ENV": environment,
                    "ADBIOGUARD_DEMO_MODE": "false",
                    "ADBIOGUARD_DEV_MODE": "false",
                })
                self.assertTrue(settings.demo_mode)

    def test_local_http_backend_works_with_default_environment(self):
        config = load_config({"ADBIOGUARD_ENV": "production"})
        for url in ("http://localhost:8000", "http://127.0.0.1:8000", "http://[::1]:8000"):
            with self.subTest(url=url):
                self.assertEqual(config.get_settings({"ADBIOGUARD_API_BASE": url}).api_base, url)

    def test_backend_url_is_trimmed(self):
        config = load_config({"ADBIOGUARD_ENV": "production"})
        self.assertEqual(config.get_settings({
            "ADBIOGUARD_API_BASE": "  https://adauth.tech/  ",
        }).api_base, "https://adauth.tech")

    def test_remote_http_still_requires_development_mode(self):
        config = load_config({"ADBIOGUARD_ENV": "production"})
        with self.assertRaises(ValueError):
            config.get_settings({"ADBIOGUARD_API_BASE": "http://adauth.tech"})

    def test_demo_mode_is_enabled_by_default(self):
        """The desktop agent should expose demo escape controls by default."""
        config = load_config({"ADBIOGUARD_ENV": "production"})

        self.assertTrue(config.DEMO_MODE)

    def test_demo_mode_keeps_native_lockdown_enabled(self):
        """Demo mode adds controls without weakening the real lock behavior."""
        config = load_config({"ADBIOGUARD_ENV": "production"})

        settings = config.get_settings({
            "ADBIOGUARD_ENV": "production",
            "ADBIOGUARD_DEMO_MODE": "true",
        })

        self.assertTrue(getattr(settings, "lockdown_enabled", False))

    def test_disabling_demo_also_keeps_native_lockdown_enabled(self):
        """Native lock behavior is independent from the demo control bar."""
        config = load_config({"ADBIOGUARD_ENV": "production"})

        settings = config.get_settings({
            "ADBIOGUARD_ENV": "production",
            "ADBIOGUARD_DEMO_MODE": "false",
        })

        self.assertTrue(getattr(settings, "lockdown_enabled", False))

    def test_prerelease_ui_exposes_simulate_and_exit_controls_unconditionally(self):
        """Pre-release escape controls must not depend on environment mode flags."""
        root = __import__("pathlib").Path(__file__).parents[1]
        app_source = (root / "ui" / "app.js").read_text(encoding="utf-8")
        self.assertIn(
            "    document.getElementById('dev-bar').style.display = 'flex';",
            app_source,
        )
        self.assertNotIn("config.dev_mode || config.demo_mode", app_source)

    def test_production_defaults_disable_developer_controls(self):
        """Would fail if an installation exposes developer unlocking by default."""
        config = load_config({"ADBIOGUARD_ENV": "production"})

        self.assertFalse(config.DEV_MODE)

    def test_explicit_development_environment_enables_developer_controls(self):
        """Would fail if environment-based deployment settings are ignored."""
        config = load_config({"ADBIOGUARD_ENV": "production"})

        settings = config.get_settings({
            "ADBIOGUARD_ENV": "development",
            "ADBIOGUARD_API_BASE": "https://sibilantly-penanceless-young.ngrok-free.dev",
            "ADBIOGUARD_DEV_MODE": "true",
            "ADBIOGUARD_DEMO_MODE": "true",
        })

        self.assertEqual(settings.environment, "development")
        self.assertEqual(settings.api_base, "https://sibilantly-penanceless-young.ngrok-free.dev")
        self.assertTrue(settings.dev_mode)
        self.assertTrue(settings.demo_mode)


if __name__ == "__main__":
    unittest.main()
