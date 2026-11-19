"""ToolRegistry module for loading manifests and inspecting tool status."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from esim_tool_manager.core.logger import get_logger
from esim_tool_manager.core.models import (
    InstalledToolInfo,
    PlatformPackageConfig,
    ToolCategory,
    ToolDefinition,
    ToolStatus,
    VersionSpec,
)
from esim_tool_manager.platforms.base import BasePlatformManager

DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "tools_manifest.json"
)


class ToolRegistry:
    """Manages eSim tool metadata catalog and discovers host installation states."""

    def __init__(self, manifest_path: Optional[Path] = None):
        self.logger = get_logger()
        self.manifest_path = manifest_path or DEFAULT_MANIFEST_PATH
        self.tools: Dict[str, ToolDefinition] = {}
        self.python_dependencies: List[Dict[str, str]] = []
        self._load_manifest()

    def _load_manifest(self):
        """Loads and parses tools_manifest.json."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Tools manifest not found at: {self.manifest_path}")

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data.get("tools", []):
                # Parse platform packages
                packages: Dict[str, PlatformPackageConfig] = {}
                for plat, pdata in item.get("platform_packages", {}).items():
                    packages[plat] = PlatformPackageConfig(
                        package_name=pdata.get("package_name", ""),
                        package_manager=pdata.get("package_manager", ""),
                        install_args=pdata.get("install_args", []),
                        download_url=pdata.get("download_url"),
                        archive_type=pdata.get("archive_type"),
                        binary_relative_path=pdata.get("binary_relative_path"),
                    )

                tool_def = ToolDefinition(
                    id=item["id"],
                    name=item["name"],
                    category=ToolCategory(item.get("category", "Simulation")),
                    description=item.get("description", ""),
                    binary_name=item.get("binary_name", {}),
                    version_command=item.get("version_command", {}),
                    version_regex=item.get("version_regex", r"(\d+(\.\d+)*)"),
                    min_version=item.get("min_version"),
                    max_version=item.get("max_version"),
                    recommended_version=item.get("recommended_version", "latest"),
                    dependencies=item.get("dependencies", []),
                    env_vars=item.get("env_vars", {}),
                    platform_packages=packages,
                    verification_command=item.get("verification_command"),
                    is_required=item.get("is_required", True),
                    doc_url=item.get("doc_url", ""),
                )
                self.tools[tool_def.id] = tool_def

            self.python_dependencies = data.get("python_dependencies", [])
            self.logger.debug(f"Loaded {len(self.tools)} tools from manifest.")
        except Exception as e:
            self.logger.error(f"Failed to load tools manifest: {e}")
            raise

    def get_tool(self, tool_id: str) -> Optional[ToolDefinition]:
        """Lookup tool definition by ID."""
        return self.tools.get(tool_id)

    def get_all_tools(self) -> List[ToolDefinition]:
        """Returns list of all registered tool definitions."""
        return list(self.tools.values())

    def inspect_tool(
        self, tool_def: ToolDefinition, platform_mgr: BasePlatformManager
    ) -> InstalledToolInfo:
        """Inspects whether a tool is installed on the host and checks its version and health."""
        plat_key = platform_mgr.get_platform_key()
        binary_name = tool_def.get_binary_name(plat_key)

        info = InstalledToolInfo(
            tool_id=tool_def.id,
            name=tool_def.name,
            category=tool_def.category,
        )

        executable_path = platform_mgr.which(binary_name)
        if not executable_path:
            info.installed = False
            info.status = ToolStatus.NOT_INSTALLED
            info.status_message = f"Executable '{binary_name}' not found on system PATH."
            return info

        info.installed = True
        info.executable_path = executable_path

        # If in mock mode, return predefined version
        if platform_mgr.mock_mode and tool_def.id in platform_mgr.mock_installed_tools:
            detected_ver = platform_mgr.mock_installed_tools[tool_def.id]
        else:
            # Detect version by executing version command
            cmd = tool_def.get_version_command(plat_key)
            # Replace placeholder command if executable path is full path
            if cmd and cmd[0] == binary_name:
                cmd = [executable_path] + cmd[1:]

            code, stdout, stderr = platform_mgr.execute_command(cmd, timeout=10)
            combined_output = f"{stdout}\n{stderr}"
            detected_ver = self._extract_version(combined_output, tool_def.version_regex)

        info.detected_version = detected_ver

        if not detected_ver:
            info.status = ToolStatus.INSTALLED_OK
            info.status_message = "Installed, but could not parse exact version string."
            info.is_compatible = True
            return info

        # Verify compatibility against version constraints
        current_spec = VersionSpec(detected_ver)
        is_compatible = True
        incompat_reasons = []

        if tool_def.min_version:
            if current_spec < VersionSpec(tool_def.min_version):
                is_compatible = False
                incompat_reasons.append(f"Requires >= {tool_def.min_version}")

        if tool_def.max_version:
            if current_spec >= VersionSpec(tool_def.max_version):
                is_compatible = False
                incompat_reasons.append(f"Requires < {tool_def.max_version}")

        info.is_compatible = is_compatible

        if not is_compatible:
            info.status = ToolStatus.INCOMPATIBLE
            info.status_message = f"Incompatible: {', '.join(incompat_reasons)}"
        else:
            info.status = ToolStatus.INSTALLED_OK
            info.status_message = f"Compatible (detected v{detected_ver})"

        # Populate environment variables
        exec_dir = str(Path(executable_path).parent)
        for var_name, var_template in tool_def.env_vars.items():
            resolved = var_template.format(
                executable_path=executable_path, executable_dir=exec_dir
            )
            info.env_vars[var_name] = resolved

        return info

    @staticmethod
    def _extract_version(text: str, regex_pattern: str) -> Optional[str]:
        """Extracts version using specified regex pattern."""
        match = re.search(regex_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
        # Fallback to standard semver search
        fallback = re.search(r"\b(\d+\.\d+(?:\.\d+)?)\b", text)
        if fallback:
            return fallback.group(1)
        return None
