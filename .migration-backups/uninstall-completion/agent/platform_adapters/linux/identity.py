"""Reserved Linux device identity."""
from platform_adapters.factory import UnsupportedPlatformError


def get_device_uuid():
    raise UnsupportedPlatformError("Linux device identity is not implemented")
