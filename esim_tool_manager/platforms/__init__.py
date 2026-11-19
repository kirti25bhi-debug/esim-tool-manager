"""Platform manager factory."""

import platform
import sys
from typing import Optional

from esim_tool_manager.platforms.base import BasePlatformManager
from esim_tool_manager.platforms.linux import LinuxPlatformManager
from esim_tool_manager.platforms.macos import MacOSPlatformManager
from esim_tool_manager.platforms.windows import WindowsPlatformManager


def get_platform_manager(
    force_platform: Optional[str] = None,
    dry_run: bool = False,
    mock_mode: bool = False,
) -> BasePlatformManager:
    """Instantiates the appropriate PlatformManager for host OS or requested platform."""
    plat_str = force_platform.lower() if force_platform else platform.system().lower()

    if "linux" in plat_str:
        return LinuxPlatformManager(dry_run=dry_run, mock_mode=mock_mode)
    elif "darwin" in plat_str or "mac" in plat_str:
        return MacOSPlatformManager(dry_run=dry_run, mock_mode=mock_mode)
    elif "windows" in plat_str:
        return WindowsPlatformManager(dry_run=dry_run, mock_mode=mock_mode)
    else:
        # Default to Linux fallback for other POSIX
        return LinuxPlatformManager(dry_run=dry_run, mock_mode=mock_mode)
