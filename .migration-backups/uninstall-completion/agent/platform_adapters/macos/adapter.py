"""macOS integration is deliberately unavailable until implemented."""
from platform_adapters.factory import UnsupportedPlatformError


class MacOSPlatformAdapter:
    def __init__(self):
        raise UnsupportedPlatformError("macOS agent integration is not implemented")
