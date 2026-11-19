"""Dependency checking and diagnostic engine for eSim ('eSim Doctor')."""

import importlib.metadata
import platform
import shutil
import sys
from typing import Dict, List, Optional

from esim_tool_manager.core.logger import get_logger
from esim_tool_manager.core.models import (
    InstalledToolInfo,
    SystemDoctorReport,
    ToolCategory,
    ToolStatus,
    VersionSpec,
)
from esim_tool_manager.core.registry import ToolRegistry
from esim_tool_manager.platforms.base import BasePlatformManager


class DependencyChecker:
    """Verifies operating system, package managers, EDA tools, and Python library dependencies."""

    def __init__(self, registry: ToolRegistry, platform_mgr: BasePlatformManager):
        self.logger = get_logger()
        self.registry = registry
        self.platform_mgr = platform_mgr

    def check_python_library(self, pkg_name: str, min_version: Optional[str] = None) -> InstalledToolInfo:
        """Inspects an installed Python library dependency."""
        info = InstalledToolInfo(
            tool_id=pkg_name,
            name=f"Python package: {pkg_name}",
            category=ToolCategory.PYTHON_LIBRARY,
        )

        try:
            installed_ver = importlib.metadata.version(pkg_name)
            info.installed = True
            info.detected_version = installed_ver

            if min_version:
                if VersionSpec(installed_ver) >= VersionSpec(min_version):
                    info.status = ToolStatus.INSTALLED_OK
                    info.is_compatible = True
                    info.status_message = f"v{installed_ver} (>= {min_version})"
                else:
                    info.status = ToolStatus.INCOMPATIBLE
                    info.is_compatible = False
                    info.status_message = (
                        f"Outdated v{installed_ver}; requires >= {min_version}"
                    )
            else:
                info.status = ToolStatus.INSTALLED_OK
                info.is_compatible = True
                info.status_message = f"Installed v{installed_ver}"
        except importlib.metadata.PackageNotFoundError:
            info.installed = False
            info.status = ToolStatus.NOT_INSTALLED
            info.status_message = f"Package '{pkg_name}' not installed in active Python environment."

        return info

    def run_diagnostics(self) -> SystemDoctorReport:
        """Executes a full diagnostic health check across system, tools, and libraries."""
        self.logger.info("Running eSim Tool Doctor diagnostics...")

        issues: List[str] = []
        recommendations: List[str] = []
        all_tools_info: List[InstalledToolInfo] = []

        # 1. Host OS & Package Manager checks
        avail_pkg_mgrs = self.platform_mgr.detect_available_package_managers()
        primary_pkg_mgr = avail_pkg_mgrs[0] if avail_pkg_mgrs else None

        if not primary_pkg_mgr and not self.platform_mgr.mock_mode:
            issues.append("No native package manager detected (e.g. apt, brew, winget).")
            if self.platform_mgr.get_platform_key() == "darwin":
                recommendations.append("Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            elif self.platform_mgr.get_platform_key() == "linux":
                recommendations.append("Ensure apt-get or dnf is available in your PATH.")
            elif self.platform_mgr.get_platform_key() == "windows":
                recommendations.append("Install winget or Chocolatey for automated package management.")

        # 2. Check external EDA tools
        for tool_def in self.registry.get_all_tools():
            tool_info = self.registry.inspect_tool(tool_def, self.platform_mgr)
            all_tools_info.append(tool_info)

            if not tool_info.installed:
                if tool_def.is_required:
                    issues.append(f"Required tool '{tool_def.name}' ({tool_def.id}) is NOT installed.")
                    recommendations.append(f"Run 'esim-tools install {tool_def.id}' to automatically install it.")
            elif not tool_info.is_compatible:
                issues.append(f"Tool '{tool_def.name}' version incompatible: {tool_info.status_message}")
                recommendations.append(f"Run 'esim-tools update {tool_def.id}' to upgrade to a supported release.")

        # 3. Check Python libraries
        for py_dep in self.registry.python_dependencies:
            dep_id = py_dep.get("id", "")
            min_v = py_dep.get("min_version")
            py_info = self.check_python_library(dep_id, min_v)
            all_tools_info.append(py_info)

            if not py_info.installed:
                issues.append(f"Python dependency '{dep_id}' is missing.")
                recommendations.append(f"Run 'pip install {dep_id}>={min_v or ''}'")
            elif not py_info.is_compatible:
                issues.append(f"Python dependency '{dep_id}' is incompatible: {py_info.status_message}")
                recommendations.append(f"Run 'pip install --upgrade {dep_id}'")

        all_healthy = (len(issues) == 0)

        report = SystemDoctorReport(
            os_name=platform.system(),
            os_version=platform.release(),
            architecture=platform.machine(),
            python_version=platform.python_version(),
            package_manager=primary_pkg_mgr,
            tools=all_tools_info,
            all_healthy=all_healthy,
            issues=issues,
            recommendations=recommendations,
        )

        return report
