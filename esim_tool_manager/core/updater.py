"""Update and upgrade engine for eSim tools."""

from typing import Dict, List, Optional, Tuple

from esim_tool_manager.core.logger import get_logger
from esim_tool_manager.core.models import ActionResult, InstalledToolInfo, ToolStatus, VersionSpec
from esim_tool_manager.core.registry import ToolRegistry
from esim_tool_manager.platforms.base import BasePlatformManager


class ToolUpdater:
    """Manages update checks and automated upgrades for installed EDA tools."""

    def __init__(self, registry: ToolRegistry, platform_mgr: BasePlatformManager):
        self.logger = get_logger()
        self.registry = registry
        self.platform_mgr = platform_mgr

    def check_updates(self, tool_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Checks if an update is available for tool. Returns (has_update, current_ver, latest_ver)."""
        tool_def = self.registry.get_tool(tool_id)
        if not tool_def:
            return False, None, None

        info = self.registry.inspect_tool(tool_def, self.platform_mgr)
        if not info.installed or not info.detected_version:
            return False, None, None

        plat_key = self.platform_mgr.get_platform_key()
        pkg_config = tool_def.platform_packages.get(plat_key)
        if not pkg_config:
            return False, info.detected_version, None

        latest_ver = self.platform_mgr.query_online_version(pkg_config, tool_id)
        if not latest_ver:
            # Fallback to recommended version if higher
            if tool_def.recommended_version and tool_def.recommended_version != "latest":
                if VersionSpec(tool_def.recommended_version) > VersionSpec(info.detected_version):
                    latest_ver = tool_def.recommended_version

        if latest_ver and VersionSpec(latest_ver) > VersionSpec(info.detected_version):
            return True, info.detected_version, latest_ver

        return False, info.detected_version, latest_ver or info.detected_version

    def update_tool(self, tool_id: str) -> ActionResult:
        """Updates a specific tool to the latest available version."""
        tool_def = self.registry.get_tool(tool_id)
        if not tool_def:
            return ActionResult(
                success=False,
                tool_id=tool_id,
                action="update",
                message=f"Tool '{tool_id}' not found.",
            )

        plat_key = self.platform_mgr.get_platform_key()
        pkg_config = tool_def.platform_packages.get(plat_key)
        if not pkg_config:
            return ActionResult(
                success=False,
                tool_id=tool_id,
                action="update",
                message=f"No package configuration for {plat_key}.",
            )

        self.logger.info(f"Triggering update for '{tool_def.name}'...")
        res = self.platform_mgr.update_package(pkg_config, tool_id)
        return res

    def update_all(self) -> Dict[str, ActionResult]:
        """Checks and updates all installed tools that have updates available."""
        results = {}
        for tool_def in self.registry.get_all_tools():
            has_update, curr, latest = self.check_updates(tool_def.id)
            if has_update:
                self.logger.info(f"Update found for {tool_def.id}: v{curr} -> v{latest}")
                results[tool_def.id] = self.update_tool(tool_def.id)
            else:
                self.logger.debug(f"{tool_def.id} is already up to date (v{curr}).")
        return results
