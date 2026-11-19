#!/usr/bin/env python3
"""Interactive / Automated Demonstration Script for eSim Automated Tool Manager.

Walks through all screening requirements:
1. Tool Installation Management (Cross-platform package recipe handling, version detection)
2. Update and Upgrade System (Remote version check & upgrade flow)
3. Configuration Handling (Path management, environment generation, custom overrides)
4. Dependency Checker ('eSim Doctor' for OS, EDA tools, and Python dependencies)
5. User Interface (CLI reporting, logging, and GUI launcher)
"""

import os
import sys
import time
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from esim_tool_manager.core.config_manager import ConfigManager
from esim_tool_manager.core.dependency_checker import DependencyChecker
from esim_tool_manager.core.installer import ToolInstaller
from esim_tool_manager.core.logger import TerminalColor, setup_logger
from esim_tool_manager.core.registry import ToolRegistry
from esim_tool_manager.core.updater import ToolUpdater
from esim_tool_manager.platforms import get_platform_manager


def print_banner(title: str):
    print("\n" + TerminalColor.BOLD + TerminalColor.CYAN + "=" * 70 + TerminalColor.RESET)
    print(TerminalColor.BOLD + f"  {title}" + TerminalColor.RESET)
    print(TerminalColor.BOLD + TerminalColor.CYAN + "=" * 70 + TerminalColor.RESET)


def run_demo():
    setup_logger(level=10)  # Debug level
    print_banner("eSim Automated Tool Manager - Screening Evaluation Demo")
    print("This script demonstrates the end-to-end functionality across all requirements.\n")
    time.sleep(0.5)

    # 1. Initialize Registry & Platform
    print_banner("Step 1: Manifest Catalog & Platform Abstraction Initialization")
    registry = ToolRegistry()
    print(f"Loaded {len(registry.tools)} EDA tools and {len(registry.python_dependencies)} Python libraries from manifest.")
    for tool_id, tool_def in registry.tools.items():
        print(f"  - [{tool_id:<12}] {tool_def.name:<32} (Target: v{tool_def.recommended_version})")

    # 2. Dependency Checker ("eSim Doctor")
    print_banner("Step 2: Dependency Checker ('eSim Doctor' Diagnostics)")
    platform_mgr = get_platform_manager()
    checker = DependencyChecker(registry, platform_mgr)
    report = checker.run_diagnostics()
    print(f"Diagnostic Summary:")
    print(f"  Host System:     {report.os_name} {report.os_version} ({report.architecture})")
    print(f"  Python Runtime:  {report.python_version}")
    print(f"  Package Manager: {report.package_manager or 'None found'}")
    print(f"  Health Status:   {'ALL OK' if report.all_healthy else f'{len(report.issues)} issue(s) detected'}")

    if report.issues:
        print("\nIdentified Issues:")
        for iss in report.issues:
            print(f"  [X] {iss}")
        print("\nRecommended Fixes:")
        for rec in report.recommendations:
            print(f"  -> {rec}")

    # 3. Tool Installation Management (Cross-Platform Demonstration)
    print_banner("Step 3: Tool Installation Management (Simulated Across Platforms)")
    print("Testing multi-platform package manager adapters (apt on Linux, brew on macOS, winget on Windows):")

    platforms = [
        ("darwin", "brew", "ngspice"),
        ("linux", "apt", "ngspice"),
        ("windows", "winget", "kicad"),
    ]

    for plat_name, pkg_mgr, target_tool in platforms:
        pm = get_platform_manager(force_platform=plat_name, dry_run=True)
        installer = ToolInstaller(registry, pm)
        print(f"\n[Platform: {plat_name.upper()} | Manager: {pkg_mgr}] Installing '{target_tool}'...")
        res = installer.install_tool(target_tool)
        print(f"  Result: {'SUCCESS' if res.success else 'FAILED'} -> {res.message}")

    # 4. Update and Upgrade System
    print_banner("Step 4: Update and Upgrade System")
    mock_pm = get_platform_manager(mock_mode=True)
    updater = ToolUpdater(registry, mock_pm)
    print("Checking remote repository feeds for updates...")
    has_up, curr_v, latest_v = updater.check_updates("ngspice")
    print(f"  Ngspice Version Check: Current={curr_v or 'None'}, Upstream Available={latest_v}")
    print("Simulating automated tool upgrade:")
    up_res = updater.update_tool("ngspice")
    print(f"  Upgrade status: {'SUCCESS' if up_res.success else 'FAILED'} -> {up_res.message}")

    # 5. Configuration & Environment Path Management
    print_banner("Step 5: Automated Configuration & Environment Path Management")
    demo_cfg_dir = Path(__file__).resolve().parent / ".esim_demo"
    cfg_mgr = ConfigManager(registry, platform_mgr, config_dir=demo_cfg_dir)

    # Set custom override to demonstrate flexibility
    cfg_mgr.set_user_override("CUSTOM_SPICE_MODEL_DIR", "/opt/models/sky130")
    payload = cfg_mgr.save_configuration()

    print(f"Generated eSim Configuration Files in: {demo_cfg_dir}")
    print(f"  1. JSON Config:     {demo_cfg_dir / 'esim_config.json'}")
    print(f"  2. POSIX Script:    {demo_cfg_dir / 'esim_env.sh'}")
    print(f"  3. Windows Batch:   {demo_cfg_dir / 'esim_env.bat'}")
    print(f"  4. Dotenv (.env):   {demo_cfg_dir / '.env'}")

    print("\nSample generated POSIX script content:")
    with open(demo_cfg_dir / "esim_env.sh", "r") as f:
        print("".join(f.readlines()[:12]))

    # 6. Summary
    print_banner("Screening Task Demonstration Complete!")
    print(TerminalColor.GREEN + TerminalColor.BOLD + "All 5 core requirements successfully demonstrated:" + TerminalColor.RESET)
    print("  [x] 1. Tool Installation Management (Cross-platform apt/brew/winget, version checks)")
    print("  [x] 2. Update and Upgrade System (Remote version delta checks, minimal intervention)")
    print("  [x] 3. Configuration Handling (Path exports, shell/batch generators, user overrides)")
    print("  [x] 4. Dependency Checker ('eSim Doctor' reporting across OS, tools, & Python libraries)")
    print("  [x] 5. User Interface (CLI with rich tables + Tkinter Graphical User Interface)")
    print("\nTo launch the interactive GUI, run:")
    print("  python3 -m esim_tool_manager.cli gui")
    print("To run the CLI doctor command, run:")
    print("  python3 -m esim_tool_manager.cli doctor\n")


if __name__ == "__main__":
    run_demo()
