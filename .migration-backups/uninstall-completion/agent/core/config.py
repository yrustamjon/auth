"""Runtime configuration with safe production defaults.

The legacy module constants remain available so the current UI/orchestration
can migrate incrementally. New code should receive :class:`Settings` instead
of importing mutable global configuration.
"""

from dataclasses import dataclass
import getpass
import os
import sys
from collections.abc import Mapping
from urllib.parse import urlparse


DEFAULT_API_BASE = "https://sibilantly-penanceless-young.ngrok-free.dev"
VALID_ENVIRONMENTS = frozenset({"development", "testing", "production"})
# User rule: SIMULATE and EXIT stay enabled until an explicitly approved release.
PRE_RELEASE = True


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError("Boolean settings must be true/false, yes/no, on/off, or 1/0")


@dataclass(frozen=True)
class Settings:
    """Deployment settings loaded from explicit ``ADBIOGUARD_*`` variables."""

    environment: str
    api_base: str
    dev_mode: bool
    demo_mode: bool

    @property
    def lockdown_enabled(self) -> bool:
        """Demo controls do not change the real workstation-lock behavior."""
        return True


def get_settings(environ: Mapping[str, str] | None = None) -> Settings:
    """Load settings without allowing development behavior in production by default."""
    source = os.environ if environ is None else environ
    environment = source.get("ADBIOGUARD_ENV", "production").strip().lower()
    if environment not in VALID_ENVIRONMENTS:
        raise ValueError(
            "ADBIOGUARD_ENV must be development, testing, or production"
        )

    api_base = source.get("ADBIOGUARD_API_BASE", DEFAULT_API_BASE).strip().rstrip("/")
    parsed = urlparse(api_base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("ADBIOGUARD_API_BASE must be an absolute HTTP(S) URL")
    is_local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if environment == "production" and parsed.scheme != "https" and not is_local:
        raise ValueError("Production ADBIOGUARD_API_BASE must use HTTPS")

    return Settings(
        environment=environment,
        api_base=api_base,
        dev_mode=_parse_bool(
            source.get("ADBIOGUARD_DEV_MODE"),
            default=False,
        ),
        demo_mode=PRE_RELEASE or _parse_bool(
            source.get("ADBIOGUARD_DEMO_MODE"),
            default=True,
        ),
    )


SETTINGS = get_settings()
API_BASE = SETTINGS.api_base
DEV_MODE = SETTINGS.dev_mode
DEMO_MODE = SETTINGS.demo_mode
USERNAME = getpass.getuser()


def get_device_uuid() -> str:
    if sys.platform == "win32":
        from platform_adapters.windows.identity import get_device_uuid as get_identity
        return get_identity()
    from storage.paths import persistent_device_uuid
    return persistent_device_uuid()


def _application_data_dir() -> str:
    from storage.paths import application_data_dir
    return application_data_dir()


def get_windows_license() -> str:
    if sys.platform == "win32":
        from platform_adapters.windows.identity import get_windows_license as get_license
        return get_license()
    return "UNKNOWN"


DEVICE_UUID     = get_device_uuid()
WINDOWS_LICENSE = get_windows_license()
