"""Configuration and environment management for eSim."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from esim_tool_manager.core.logger import get_logger
from esim_tool_manager.core.registry import ToolRegistry
from esim_tool_manager.platforms.base import BasePlatformManager

def get_default_config_dir() -> Path:
    """Resolves config directory respecting ESIM_HOME, ~/.esim, or local directory fallback."""
    env_dir = os.environ.get("ESIM_HOME")
    if env_dir:
        return Path(env_dir)

    home_dir = Path.home() / ".esim"
    try:
        home_dir.mkdir(parents=True, exist_ok=True)
        return home_dir
    except (PermissionError, OSError):
        local_dir = Path.cwd() / ".esim"
        local_dir.mkdir(parents=True, exist_ok=True)
        return local_dir


class ConfigManager:
    """Manages eSim configuration files, path resolution, and environment scripts."""

    def __init__(
        self,
        registry: ToolRegistry,
        platform_mgr: BasePlatformManager,
        config_dir: Optional[Path] = None,
    ):
        self.logger = get_logger()
        self.registry = registry
        self.platform_mgr = platform_mgr
        self.config_dir = config_dir or get_default_config_dir()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.overrides_file = self.config_dir / "user_overrides.json"
        self.config_file = self.config_dir / "esim_config.json"

    def get_user_overrides(self) -> Dict[str, str]:
        """Loads user-specified path and setting overrides."""
        if self.overrides_file.exists():
            try:
                with open(self.overrides_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not read user overrides: {e}")
        return {}

    def set_user_override(self, key: str, value: str):
        """Sets a custom user path or environment variable override."""
        overrides = self.get_user_overrides()
        overrides[key] = value
        with open(self.overrides_file, "w", encoding="utf-8") as f:
            json.dump(overrides, f, indent=2)
        self.logger.info(f"Saved configuration override: {key} = {value}")

    def generate_active_environment(self) -> Dict[str, str]:
        """Inspects all installed tools and compiles the full eSim environment variables."""
        env_vars: Dict[str, str] = {
            "ESIM_HOME": str(self.config_dir),
            "ESIM_CONFIG_PATH": str(self.config_file),
        }

        bin_dirs = set()

        for tool_def in self.registry.get_all_tools():
            info = self.registry.inspect_tool(tool_def, self.platform_mgr)
            if info.installed and info.executable_path:
                tool_bin_dir = str(Path(info.executable_path).parent)
                bin_dirs.add(tool_bin_dir)

                for k, v in info.env_vars.items():
                    env_vars[k] = v

        # Apply user overrides
        overrides = self.get_user_overrides()
        env_vars.update(overrides)

        # Include tool binary directories in updated PATH
        current_path = os.environ.get("PATH", "")
        path_sep = ";" if self.platform_mgr.get_platform_key() == "windows" else ":"
        additional_paths = path_sep.join([p for p in bin_dirs if p not in current_path])

        if additional_paths:
            env_vars["PATH"] = f"{additional_paths}{path_sep}{current_path}"
        else:
            env_vars["PATH"] = current_path

        return env_vars

    def save_configuration(self) -> Dict[str, Any]:
        """Generates and writes esim_config.json, esim_env.sh, and esim_env.bat."""
        env_vars = self.generate_active_environment()

        # Build structured JSON configuration for eSim
        tool_status_map = {}
        for tool_def in self.registry.get_all_tools():
            info = self.registry.inspect_tool(tool_def, self.platform_mgr)
            tool_status_map[tool_def.id] = {
                "name": tool_def.name,
                "installed": info.installed,
                "path": info.executable_path,
                "version": info.detected_version,
                "compatible": info.is_compatible,
                "status": info.status.value,
            }

        config_payload = {
            "generated_at": datetime.now().isoformat(),
            "platform": self.platform_mgr.get_platform_key(),
            "environment_variables": env_vars,
            "tools": tool_status_map,
            "version": "1.0",
        }

        # Backup existing config if present
        if self.config_file.exists():
            backup_path = self.config_dir / f"esim_config.json.bak"
            try:
                shutil.copy2(self.config_file, backup_path)
            except Exception:
                pass

        # Write esim_config.json
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config_payload, f, indent=2)
        self.logger.info(f"Wrote configuration to: {self.config_file}")

        # Write esim_env.sh (POSIX shell wrapper)
        sh_file = self.config_dir / "esim_env.sh"
        with open(sh_file, "w", encoding="utf-8") as f:
            f.write("#!/bin/sh\n")
            f.write("# Automated eSim environment configuration\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            for k, v in env_vars.items():
                if k != "PATH":
                    f.write(f'export {k}="{v}"\n')
            # PATH export
            f.write(f'export PATH="{env_vars.get("PATH", "$PATH")}"\n')
        try:
            sh_file.chmod(0o755)
        except Exception:
            pass
        self.logger.info(f"Wrote POSIX environment script: {sh_file}")

        # Write esim_env.bat (Windows CMD wrapper)
        bat_file = self.config_dir / "esim_env.bat"
        with open(bat_file, "w", encoding="utf-8") as f:
            f.write("@echo off\n")
            f.write("REM Automated eSim environment configuration\n\n")
            for k, v in env_vars.items():
                if k != "PATH":
                    f.write(f'set "{k}={v}"\n')
            f.write(f'set "PATH={env_vars.get("PATH", "%PATH%")}"\n')
        self.logger.info(f"Wrote Windows environment batch script: {bat_file}")

        # Write .env file
        dotenv_file = self.config_dir / ".env"
        with open(dotenv_file, "w", encoding="utf-8") as f:
            for k, v in env_vars.items():
                f.write(f'{k}="{v}"\n')

        return config_payload
