"""Linux platform manager supporting apt, dnf, pacman, and direct archive installations."""

import os
import re
import shutil
import time
from typing import List, Optional

from esim_tool_manager.core.models import ActionResult, PlatformPackageConfig
from esim_tool_manager.platforms.base import BasePlatformManager


class LinuxPlatformManager(BasePlatformManager):
    """Platform manager for Linux distributions."""

    def get_platform_key(self) -> str:
        return "linux"

    def detect_available_package_managers(self) -> List[str]:
        managers = []
        for mgr in ["apt-get", "apt", "dnf", "pacman", "yum", "zypper"]:
            if shutil.which(mgr):
                managers.append(mgr)
        return managers

    def install_package(
        self, pkg_config: PlatformPackageConfig, tool_id: str
    ) -> ActionResult:
        start_time = time.time()
        self.logger.info(f"Installing {tool_id} on Linux via {pkg_config.package_manager}...")

        if self.mock_mode:
            self.mock_installed_tools[tool_id] = "1.0.0"
            return ActionResult(
                success=True,
                tool_id=tool_id,
                action="install",
                message=f"[MOCK] Successfully installed {tool_id}",
                output=f"Simulated installation of {pkg_config.package_name}",
                duration_seconds=round(time.time() - start_time, 2),
            )

        if self.dry_run:
            cmd = ["sudo", "apt-get", "install", "-y", pkg_config.package_name]
            code, out, err = self.execute_command(cmd)
            return ActionResult(
                success=True,
                tool_id=tool_id,
                action="install",
                message=f"[DRY-RUN] Simulated installation of {pkg_config.package_name}",
                output=out,
                duration_seconds=0.0,
            )

        avail_mgrs = self.detect_available_package_managers()
        primary_mgr = avail_mgrs[0] if avail_mgrs else None

        # Build install command
        cmd: List[str] = []
        is_root = os.geteuid() == 0 if hasattr(os, "geteuid") else False
        sudo_prefix = [] if is_root else ["sudo"]

        if "apt" in (primary_mgr or "") or "apt-get" in (primary_mgr or ""):
            cmd = sudo_prefix + ["apt-get", "install", "-y", pkg_config.package_name]
        elif "dnf" in (primary_mgr or ""):
            cmd = sudo_prefix + ["dnf", "install", "-y", pkg_config.package_name]
        elif "pacman" in (primary_mgr or ""):
            cmd = sudo_prefix + ["pacman", "-S", "--noconfirm", pkg_config.package_name]
        else:
            return ActionResult(
                success=False,
                tool_id=tool_id,
                action="install",
                message="No supported Linux package manager (apt, dnf, pacman) found.",
                error="Please install tool manually or via download URL.",
                duration_seconds=round(time.time() - start_time, 2),
            )

        code, out, err = self.execute_command(cmd)
        duration = round(time.time() - start_time, 2)
        success = (code == 0)

        return ActionResult(
            success=success,
            tool_id=tool_id,
            action="install",
            message=f"Installation {'succeeded' if success else 'failed'}",
            output=out,
            error=err if not success else "",
            duration_seconds=duration,
        )

    def update_package(
        self, pkg_config: PlatformPackageConfig, tool_id: str
    ) -> ActionResult:
        start_time = time.time()
        self.logger.info(f"Updating {tool_id} on Linux...")

        if self.mock_mode:
            return ActionResult(
                success=True,
                tool_id=tool_id,
                action="update",
                message=f"[MOCK] Successfully updated {tool_id}",
                output="Mock package upgraded to latest version",
                duration_seconds=0.1,
            )

        avail_mgrs = self.detect_available_package_managers()
        primary_mgr = avail_mgrs[0] if avail_mgrs else None
        is_root = os.geteuid() == 0 if hasattr(os, "geteuid") else False
        sudo_prefix = [] if is_root else ["sudo"]

        if "apt" in (primary_mgr or ""):
            cmd = sudo_prefix + ["apt-get", "install", "--only-upgrade", "-y", pkg_config.package_name]
        elif "dnf" in (primary_mgr or ""):
            cmd = sudo_prefix + ["dnf", "upgrade", "-y", pkg_config.package_name]
        elif "pacman" in (primary_mgr or ""):
            cmd = sudo_prefix + ["pacman", "-S", "--noconfirm", pkg_config.package_name]
        else:
            return ActionResult(
                success=False,
                tool_id=tool_id,
                action="update",
                message="No supported package manager found.",
                duration_seconds=0.0,
            )

        code, out, err = self.execute_command(cmd)
        duration = round(time.time() - start_time, 2)
        return ActionResult(
            success=(code == 0),
            tool_id=tool_id,
            action="update",
            message=f"Update {'succeeded' if code == 0 else 'failed'}",
            output=out,
            error=err if code != 0 else "",
            duration_seconds=duration,
        )

    def query_online_version(
        self, pkg_config: PlatformPackageConfig, tool_id: str
    ) -> Optional[str]:
        if self.mock_mode:
            return "43.0"

        avail_mgrs = self.detect_available_package_managers()
        if "apt-cache" in str(shutil.which("apt-cache")):
            code, out, _ = self.execute_command(["apt-cache", "policy", pkg_config.package_name])
            if code == 0:
                m = re.search(r"Candidate:\s*([^\s]+)", out)
                if m:
                    return m.group(1)
        return None
