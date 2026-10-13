"""Reserved Linux runtime."""
from platform_adapters.factory import UnsupportedPlatformError


def main():
    raise UnsupportedPlatformError("Linux runtime is not implemented")
