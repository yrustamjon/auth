"""Linux integration is deliberately unavailable until implemented."""
from platform_adapters.factory import UnsupportedPlatformError


class LinuxPlatformAdapter:
    def __init__(self):
        raise UnsupportedPlatformError("Linux agent integration is not implemented")
