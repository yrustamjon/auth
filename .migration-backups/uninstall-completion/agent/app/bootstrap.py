"""Assemble shared components and select concrete OS integration lazily."""
from platform_adapters.factory import get_platform_adapter


def create_controller(window, *, platform_adapter=None, api_client=None):
    from app.controller import BioGuardAPI
    adapter = platform_adapter or get_platform_adapter()
    from services.disable_manager import configure_platform
    configure_platform(adapter)
    return BioGuardAPI(window, platform_adapter=adapter, api_client=api_client)


def run():
    adapter = get_platform_adapter()
    if adapter.platform_name == "windows":
        from platform_adapters.windows.runtime import main
        main()
