"""macOS platform manager supporting Homebrew formula, cask, and direct application bundles."""

import json
import os
import shutil
import time
from typing import List, Optional

from esim_tool_manager.core.models import ActionResult, PlatformPackageConfig
from esim_tool_manager.platforms.base import BasePlatformManager


class MacOSPlatformManager(BasePlatformManager):
    """Platform manager for macOS systems."""

    def get_platform_key(self) -> str:
        return "darwin"

    def detect_available_package_managers(self) -> List[str]:
        managers = []
        if shutil.which("brew"):
            managers.append("brew")
        if shutil.which("port"):
            managers.append("macports")
        return managers

    def which(self, binary_name: str) -> Optional[str]:
        # Check standard PATH
        found = super().which(binary_name)
        if found:
            return found

        # Special macOS locations (e.g., Homebrew, KiCad in /Applications)
        special_paths = [
            f"/opt/homebrew/bin/{binary_name}",
            f"/usr/local/bin/{binary_name}",
            f"/Applications/KiCad/KiCad.app/Contents/MacOS/{binary_name}",
            f"/Applications/GtkWave.app/Contents/Resources/bin/{binary_name}",
        ]
        for p in special_paths:
            if os.path.exists(p) and os.access(p, os.X_OK):
                return p

        return None

    def install_package(
        self, pkg_config: PlatformPackageConfig, tool_id: str
    ) -> ActionResult:
        start_time = time.time()
        self.logger.info(f"Installing {tool_id} on macOS via Homebrew...")

        if self.mock_mode:
            self.mock_installed_tools[tool_id] = "1.0.0"
            return ActionResult(
                success=True,
                tool_id=tool_id,
                action="install",
                message=f"[MOCK] Successfully installed {tool_id} via Homebrew",
                output=f"Simulated brew install of {pkg_config.package_name}",
                duration_seconds=round(time.time() - start_time, 2),
            )

        args = pkg_config.install_args if pkg_config.install_args else ["install", pkg_config.package_name]
        cmd = ["brew"] + args

        if self.dry_run:
            code, out, err = self.execute_command(cmd)
            return ActionResult(
                success=True,
                tool_id=tool_id,
                action="install",
                message=f"[DRY-RUN] Simulated installation of {pkg_config.package_name}",
                output=out,
                duration_seconds=0.0,
            )

        brew_path = shutil.which("brew")
        if not brew_path:
            return ActionResult(
                success=False,
                tool_id=tool_id,
                action="install",
                message="Homebrew ('brew') is not installed on this Mac.",
                error="Please install Homebrew from https://brew.sh or download tool manually.",
                duration_seconds=round(time.time() - start_time, 2),
            )

        # Build command from install_args
        args = pkg_config.install_args if pkg_config.install_args else ["install", pkg_config.package_name]
        cmd = [brew_path] + args

        code, out, err = self.execute_command(cmd, timeout=300)
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
        self.logger.info(f"Updating {tool_id} on macOS via Homebrew...")

        if self.mock_mode:
            return ActionResult(
                success=True,
                tool_id=tool_id,
                action="update",
                message=f"[MOCK] Successfully upgraded {tool_id}",
                output="Mock brew upgrade successful",
                duration_seconds=0.1,
            )

        brew_path = shutil.which("brew")
        if not brew_path:
            return ActionResult(
                success=False,
                tool_id=tool_id,
                action="update",
                message="Homebrew not installed.",
                duration_seconds=0.0,
            )

        cmd = [brew_path, "upgrade", pkg_config.package_name]
        code, out, err = self.execute_command(cmd, timeout=300)
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

        brew_path = shutil.which("brew")
        if not brew_path:
            return None

        code, out, _ = self.execute_command([brew_path, "info", "--json=v2", pkg_config.package_name])
        if code == 0 and out:
            try:
                data = json.loads(out)
                formulae = data.get("formulae", [])
                if formulae:
                    return formulae[0].get("versions", {}).get("stable")
                casks = data.get("casks", [])
                if casks:
                    return casks[0].get("version")
            except Exception:
                pass
        return None
