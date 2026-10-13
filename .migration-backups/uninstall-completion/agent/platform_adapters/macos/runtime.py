"""Reserved macOS runtime."""
from platform_adapters.factory import UnsupportedPlatformError


def main():
    raise UnsupportedPlatformError("macOS runtime is not implemented")
