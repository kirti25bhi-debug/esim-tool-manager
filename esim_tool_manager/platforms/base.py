"""Base platform manager interface for executing system package operations."""

import os
import platform
import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from esim_tool_manager.core.logger import get_logger
from esim_tool_manager.core.models import ActionResult, PlatformPackageConfig


class BasePlatformManager(ABC):
    """Abstract interface defining platform-specific tool installation and environment management."""

    def __init__(self, dry_run: bool = False, mock_mode: bool = False):
        self.dry_run = dry_run
        self.mock_mode = mock_mode
        self.logger = get_logger()
        self.mock_installed_tools: Dict[str, str] = {}

    @abstractmethod
    def get_platform_key(self) -> str:
        """Returns platform identifier: 'linux', 'darwin', or 'windows'."""
        pass

    @abstractmethod
    def detect_available_package_managers(self) -> List[str]:
        """Detect which package managers exist on this host system (e.g. ['apt'], ['brew'])."""
        pass

    @abstractmethod
    def install_package(
        self, pkg_config: PlatformPackageConfig, tool_id: str
    ) -> ActionResult:
        """Installs package using platform-specific installer."""
        pass

    @abstractmethod
    def update_package(
        self, pkg_config: PlatformPackageConfig, tool_id: str
    ) -> ActionResult:
        """Updates package to latest version."""
        pass

    @abstractmethod
    def query_online_version(
        self, pkg_config: PlatformPackageConfig, tool_id: str
    ) -> Optional[str]:
        """Queries the package manager or repository for the latest available remote version."""
        pass

    def which(self, binary_name: str) -> Optional[str]:
        """Finds executable on system PATH."""
        if self.mock_mode and binary_name in self.mock_installed_tools:
            return f"/mock/bin/{binary_name}"
        return shutil.which(binary_name)

    def execute_command(
        self, cmd: List[str], timeout: int = 180, env: Optional[Dict[str, str]] = None
    ) -> Tuple[int, str, str]:
        """Executes a subprocess safely with timeout and captured output."""
        if self.dry_run:
            self.logger.info(f"[DRY-RUN] Would execute: {' '.join(cmd)}")
            return 0, f"[DRY-RUN] Success for: {' '.join(cmd)}", ""

        full_env = os.environ.copy()
        if env:
            full_env.update(env)

        try:
            self.logger.debug(f"Executing: {' '.join(cmd)}")
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                env=full_env,
            )
            return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
            return 124, "", f"Command timed out after {timeout} seconds"
        except FileNotFoundError:
            self.logger.warning(f"Command not found on system: {cmd[0]}")
            return 127, "", f"Executable '{cmd[0]}' not found"
        except Exception as e:
            self.logger.error(f"Failed to execute '{cmd[0]}': {e}")
            return 1, "", str(e)
