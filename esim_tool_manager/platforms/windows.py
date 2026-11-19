"""Windows platform manager supporting winget, chocolatey, and portable zip archives."""

import os
import shutil
import time
from pathlib import Path
from typing import List, Optional

from esim_tool_manager.core.models import ActionResult, PlatformPackageConfig
from esim_tool_manager.platforms.base import BasePlatformManager


class WindowsPlatformManager(BasePlatformManager):
    """Platform manager for Microsoft Windows systems."""

    def get_platform_key(self) -> str:
        return "windows"

    def detect_available_package_managers(self) -> List[str]:
        managers = []
        if shutil.which("winget.exe") or shutil.which("winget"):
            managers.append("winget")
        if shutil.which("choco.exe") or shutil.which("choco"):
            managers.append("choco")
        if shutil.which("scoop.cmd") or shutil.which("scoop"):
            managers.append("scoop")
        return managers

    def which(self, binary_name: str) -> Optional[str]:
        # Handle .exe extension
        if not binary_name.lower().endswith(".exe"):
            exe_name = f"{binary_name}.exe"
        else:
            exe_name = binary_name

        found = super().which(exe_name)
        if found:
            return found

        # Standard Windows install locations for EDA tools
        program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        user_profile = os.environ.get("USERPROFILE", r"C:\Users\Default")

        search_locations = [
            Path(program_files) / "KiCad" / "bin" / exe_name,
            Path(program_files) / "KiCad" / "7.0" / "bin" / exe_name,
            Path(program_files) / "KiCad" / "8.0" / "bin" / exe_name,
            Path(program_files) / "Spice64" / "bin" / exe_name,
            Path(user_profile) / ".esim" / "tools" / binary_name / exe_name,
            Path(r"C:\eSim") / "tools" / binary_name / exe_name,
        ]

        for p in search_locations:
            if p.exists() and os.access(str(p), os.X_OK):
                return str(p)

        return None

    def install_package(
        self, pkg_config: PlatformPackageConfig, tool_id: str
    ) -> ActionResult:
        start_time = time.time()
        self.logger.info(f"Installing {tool_id} on Windows...")

        if self.mock_mode:
            self.mock_installed_tools[tool_id] = "1.0.0"
            return ActionResult(
                success=True,
                tool_id=tool_id,
                action="install",
                message=f"[MOCK] Successfully installed {tool_id} on Windows",
                output=f"Simulated winget/choco install of {pkg_config.package_name}",
                duration_seconds=round(time.time() - start_time, 2),
            )

        if self.dry_run:
            cmd = ["winget", "install", "--id", pkg_config.package_name, "-e"]
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
        cmd: List[str] = []

        if "winget" in avail_mgrs:
            cmd = ["winget", "install", "--id", pkg_config.package_name, "-e", "--accept-source-agreements", "--accept-package-agreements"]
        elif "choco" in avail_mgrs:
            cmd = ["choco", "install", pkg_config.package_name, "-y"]
        else:
            return ActionResult(
                success=False,
                tool_id=tool_id,
                action="install",
                message="Neither winget nor chocolatey was found on this Windows system.",
                error=f"Download installer manually from: {pkg_config.download_url}",
                duration_seconds=round(time.time() - start_time, 2),
            )

        code, out, err = self.execute_command(cmd, timeout=360)
        duration = round(time.time() - start_time, 2)
        success = (code == 0)

        return ActionResult(
            success=success,
            tool_id=tool_id,
            action="install",
            message=f"Windows installation {'succeeded' if success else 'failed'}",
            output=out,
            error=err if not success else "",
            duration_seconds=duration,
        )

    def update_package(
        self, pkg_config: PlatformPackageConfig, tool_id: str
    ) -> ActionResult:
        start_time = time.time()
        if self.mock_mode:
            return ActionResult(
                success=True,
                tool_id=tool_id,
                action="update",
                message=f"[MOCK] Updated {tool_id}",
                duration_seconds=0.1,
            )

        avail_mgrs = self.detect_available_package_managers()
        if "winget" in avail_mgrs:
            cmd = ["winget", "upgrade", "--id", pkg_config.package_name]
        elif "choco" in avail_mgrs:
            cmd = ["choco", "upgrade", pkg_config.package_name, "-y"]
        else:
            return ActionResult(
                success=False,
                tool_id=tool_id,
                action="update",
                message="No Windows package manager available.",
                duration_seconds=0.0,
            )

        code, out, err = self.execute_command(cmd, timeout=360)
        return ActionResult(
            success=(code == 0),
            tool_id=tool_id,
            action="update",
            message=f"Update {'succeeded' if code == 0 else 'failed'}",
            output=out,
            error=err if code != 0 else "",
            duration_seconds=round(time.time() - start_time, 2),
        )

    def query_online_version(
        self, pkg_config: PlatformPackageConfig, tool_id: str
    ) -> Optional[str]:
        if self.mock_mode:
            return "43.0"
        return None
