"""Choose OS integration without importing other platforms' native libraries."""
import sys


class UnsupportedPlatformError(RuntimeError):
    """A platform has no implemented runtime yet."""


def get_platform_adapter(platform: str | None = None):
    platform = sys.platform if platform is None else platform
    if platform == "win32":
        from platform_adapters.windows import WindowsPlatformAdapter
        return WindowsPlatformAdapter()
    if platform.startswith("linux"):
        from platform_adapters.linux.adapter import LinuxPlatformAdapter
        return LinuxPlatformAdapter()
    if platform == "darwin":
        from platform_adapters.macos.adapter import MacOSPlatformAdapter
        return MacOSPlatformAdapter()
    raise UnsupportedPlatformError(f"Unsupported operating system: {platform}")
