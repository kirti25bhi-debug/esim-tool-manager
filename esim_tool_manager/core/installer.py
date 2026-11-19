"""Installation engine for eSim external tools."""

import time
from typing import Dict, List, Optional

from esim_tool_manager.core.logger import get_logger
from esim_tool_manager.core.models import ActionResult, ToolDefinition, ToolStatus
from esim_tool_manager.core.registry import ToolRegistry
from esim_tool_manager.platforms.base import BasePlatformManager


class ToolInstaller:
    """Orchestrates downloading, installation, and verification of external EDA tools."""

    def __init__(self, registry: ToolRegistry, platform_mgr: BasePlatformManager):
        self.logger = get_logger()
        self.registry = registry
        self.platform_mgr = platform_mgr

    def install_tool(self, tool_id: str) -> ActionResult:
        """Installs a specific tool by ID."""
        tool_def = self.registry.get_tool(tool_id)
        if not tool_def:
            return ActionResult(
                success=False,
                tool_id=tool_id,
                action="install",
                message=f"Tool '{tool_id}' is not recognized in eSim catalog.",
            )

        plat_key = self.platform_mgr.get_platform_key()
        pkg_config = tool_def.platform_packages.get(plat_key)

        if not pkg_config:
            return ActionResult(
                success=False,
                tool_id=tool_id,
                action="install",
                message=f"No automated installation recipe configured for platform '{plat_key}'.",
                error=f"Please visit: {tool_def.doc_url}",
            )

        self.logger.info(f"Starting installation for '{tool_def.name}'...")
        res = self.platform_mgr.install_package(pkg_config, tool_id)

        if res.success:
            # Re-inspect to verify installation
            inspect_info = self.registry.inspect_tool(tool_def, self.platform_mgr)
            if inspect_info.installed:
                self.logger.info(f"Successfully verified installation of '{tool_def.name}' at: {inspect_info.executable_path}")
            else:
                self.logger.warning(f"Installer reported success, but '{tool_def.id}' was not found in PATH yet.")

        return res

    def install_all(self, required_only: bool = True) -> Dict[str, ActionResult]:
        """Installs all missing tools."""
        results = {}
        for tool_def in self.registry.get_all_tools():
            if required_only and not tool_def.is_required:
                continue

            info = self.registry.inspect_tool(tool_def, self.platform_mgr)
            if not info.installed or not info.is_compatible:
                self.logger.info(f"Triggering install for missing/incompatible tool: {tool_def.id}")
                results[tool_def.id] = self.install_tool(tool_def.id)
            else:
                self.logger.info(f"Tool '{tool_def.name}' is already installed and compatible.")
        return results
