"""Behavior checks for the approved platform migration."""
import importlib
import subprocess
import sys
import unittest
import tempfile
import json
from unittest.mock import patch
from unittest.mock import MagicMock
import types
import runpy
from pathlib import Path


class PlatformLayoutTests(unittest.TestCase):
    def test_shared_entrypoint_import_has_no_windows_side_effects(self):
        root = Path(__file__).resolve().parents[1]
        code = "import sys; sys.path.insert(0, '.'); import main; assert 'webview' not in sys.modules; assert 'win32gui' not in sys.modules"
        result = subprocess.run([sys.executable, "-c", code], cwd=root,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_factory_selects_windows_without_loading_native_runtime(self):
        factory = importlib.import_module("platform_adapters.factory")
        adapter = factory.get_platform_adapter("win32")
        self.assertEqual(adapter.platform_name, "windows")

    def test_unsupported_platforms_fail_explicitly(self):
        factory = importlib.import_module("platform_adapters.factory")
        for platform in ("linux", "darwin", "unknown"):
            with self.subTest(platform=platform):
                with self.assertRaises(factory.UnsupportedPlatformError):
                    factory.get_platform_adapter(platform)

    def test_assets_resolve_from_application_root(self):
        paths = importlib.import_module("app.paths")
        self.assertTrue((paths.application_root() / "ui" / "index.html").is_file())

    def test_protected_certificate_storage_roundtrip(self):
        storage = importlib.import_module("storage.legacy_windows_cert")
        with tempfile.TemporaryDirectory() as root:
            with (
                patch.object(storage, "CERT_DIR", root),
                patch.object(storage, "CERT_FILE", str(Path(root) / "cert.json")),
                patch.object(storage, "KEY_FILE", str(Path(root) / "private.pem")),
                patch.object(storage, "KEY_FILE_ENC", str(Path(root) / "private.pem.dpapi")),
                patch.object(storage, "_dpapi_encrypt", side_effect=lambda b: b"protected:"+b),
                patch.object(storage, "_dpapi_decrypt", side_effect=lambda b: b.removeprefix(b"protected:")),
            ):
                storage.save_cert({"cert_id": "test-cert", "pc_id": "unchanged"}, "test-key")
                self.assertEqual(storage.load_cert(), {"cert_id": "test-cert", "pc_id": "unchanged"})
                self.assertEqual(storage._load_private_key_bytes(), b"test-key")

    def test_legacy_json_storage_roundtrip(self):
        storage = importlib.import_module("storage.legacy_files")
        with tempfile.TemporaryDirectory() as root:
            path = str(Path(root) / "nested" / "offline.json")
            self.assertFalse(storage.exists(path))
            data = {"username": "test", "hash": "unchanged", "salt": "unchanged"}
            storage.write_json(path, data)
            self.assertEqual(storage.read_json(path), data)

    def test_legacy_certificate_paths_still_control_storage(self):
        """Existing callers patch core.cert paths; extraction must respect them."""
        crypto_modules = {}
        for name in ("cryptography", "cryptography.hazmat", "cryptography.hazmat.primitives",
                     "cryptography.hazmat.primitives.asymmetric", "cryptography.hazmat.primitives.serialization",
                     "cryptography.hazmat.primitives.hashes", "cryptography.hazmat.primitives.asymmetric.rsa",
                     "cryptography.hazmat.primitives.asymmetric.padding", "cryptography.hazmat.backends"):
            crypto_modules[name] = types.ModuleType(name)
        crypto_modules["cryptography.hazmat.backends"].default_backend = lambda: None
        namespace = {"__name__": "core.cert", "__file__": str(Path(__file__).resolve().parents[1] / "core/cert.py")}
        module = types.ModuleType("core.cert")
        module.__dict__.update(namespace)
        with patch.dict(sys.modules, {**crypto_modules, "core.cert": module}):
            exec(compile(Path(namespace["__file__"]).read_text(encoding="utf-8"), namespace["__file__"], "exec"), module.__dict__)
            with tempfile.TemporaryDirectory() as root:
                path = str(Path(root) / "cert.json")
                Path(path).write_text('{"cert_id":"existing-cert"}')
                with patch.object(module, "CERT_FILE", path):
                    self.assertIsNone(module.load_cert())  # A certificate without a protected key is not activation.

    def test_frozen_assets_resolve_from_bundle(self):
        paths = importlib.import_module("app.paths")
        with patch.object(sys, "_MEIPASS", "/bundle", create=True):
            self.assertEqual(paths.application_root(), Path("/bundle"))

    def test_windows_startup_resolves_ui_after_runtime_move(self):
        """Exercise runtime wiring without locking the workstation or opening a GUI."""
        root = Path(__file__).resolve().parents[1]
        modules = {}
        def stub(name, **attributes):
            module = types.ModuleType(name)
            module.__dict__.update(attributes)
            modules[name] = module
            return module
        window = MagicMock()
        webview = stub("webview", create_window=MagicMock(return_value=window), start=MagicMock())
        api = MagicMock()
        stub("app.bootstrap", create_controller=MagicMock(return_value=api))
        stub("core.config", DEV_MODE=False, USERNAME="test-user")
        stub("services.lan_server", start_lan_server=MagicMock())
        stub("services.disable_manager", set_lock_state=MagicMock())
        for name, functions in {
            "dpi": ["set_dpi_awareness"],
            "keyboard": ["start_keyboard_block", "stop_keyboard_block"],
            "taskbar": ["hide_taskbar", "show_taskbar"],
            "monitors": ["get_all_monitors", "start_fullscreen_monitor", "stop_fullscreen_monitor"],
            "camera": ["write_chromium_camera_pref"],
            "overlay": ["create_overlays", "destroy_overlays"],
            "display_mode": ["switch_extend", "switch_internal"],
        }.items():
            stub("platform_adapters.windows." + name,
                 **{function: MagicMock() for function in functions})
        modules["platform_adapters.windows.monitors"].get_all_monitors.return_value = [(0, 0, 1920, 1080)]
        stub("platform_adapters.windows.session_monitor", MAIN_WINDOW=None, MAIN_API=None)
        windll = MagicMock()
        windll.kernel32.GetLastError.return_value = 0
        with patch.dict(sys.modules, modules), patch("ctypes.windll", windll, create=True):
            runtime = runpy.run_path(str(root / "platform_adapters/windows/runtime.py"))
            with patch.object(runtime["os"], "makedirs"):
                runtime["main"]()
        url = webview.create_window.call_args.kwargs["url"]
        self.assertEqual(url, "file:///" + str(root / "ui/index.html").replace("\\", "/"))
        self.assertEqual(webview.start.call_args.kwargs["gui"], "edgechromium")

    def test_windows_packaging_resolves_project_paths(self):
        root = Path(__file__).resolve().parents[1]
        utils = types.ModuleType("PyInstaller.utils.hooks")
        utils.collect_data_files = lambda name: []
        utils.collect_dynamic_libs = lambda name: []
        captured = {}
        def analysis(scripts, **kwargs):
            captured.update(scripts=scripts, **kwargs)
            return types.SimpleNamespace(pure=[], zipped_data=[], scripts=[], binaries=[], zipfiles=[], datas=[])
        with patch.dict(sys.modules, {"PyInstaller.utils.hooks": utils}):
            for spec in (root / "builders/windows/bioguard.spec",):
                runpy.run_path(str(spec), init_globals={
                    "SPECPATH": str(spec.parent), "Analysis": analysis,
                    "PYZ": lambda *a, **k: None, "EXE": lambda *a, **k: None,
                    "COLLECT": lambda *a, **k: None,
                })
                self.assertEqual(captured["scripts"], [str(root / "main.py")])
                self.assertEqual(captured["datas"][0], (str(root / "ui/index.html"), "ui"))
