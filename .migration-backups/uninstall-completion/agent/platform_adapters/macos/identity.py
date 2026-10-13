"""Reserved macOS device identity."""
from platform_adapters.factory import UnsupportedPlatformError


def get_device_uuid():
    raise UnsupportedPlatformError("macOS device identity is not implemented")
