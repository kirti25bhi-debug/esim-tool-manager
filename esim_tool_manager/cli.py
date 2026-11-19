"""Command Line Interface for eSim Automated Tool Manager."""

import argparse
import json
import logging
import sys
from typing import List, Optional

from esim_tool_manager.core.config_manager import ConfigManager
from esim_tool_manager.core.dependency_checker import DependencyChecker
from esim_tool_manager.core.installer import ToolInstaller
from esim_tool_manager.core.logger import TerminalColor, setup_logger
from esim_tool_manager.core.models import ToolStatus
from esim_tool_manager.core.registry import ToolRegistry
from esim_tool_manager.core.updater import ToolUpdater
from esim_tool_manager.platforms import get_platform_manager


def format_table(headers: List[str], rows: List[List[str]]) -> str:
    """Formats ASCII table with column width calculation."""
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))

    sep = "+-" + "-+-".join(["-" * w for w in widths]) + "-+"
    header_str = (
        "| "
        + " | ".join([f"{headers[i]:<{widths[i]}}" for i in range(len(headers))])
        + " |"
    )

    out = [sep, header_str, sep]
    for row in rows:
        row_str = (
            "| "
            + " | ".join([f"{str(row[i]):<{widths[i]}}" for i in range(len(row))])
            + " |"
        )
        out.append(row_str)
    out.append(sep)
    return "\n".join(out)


def cmd_list(args, registry, platform_mgr):
    """Lists all tools and current status."""
    tools = registry.get_all_tools()
    rows = []

    for t in tools:
        info = registry.inspect_tool(t, platform_mgr)
        status_color = TerminalColor.GREEN if info.status == ToolStatus.INSTALLED_OK else (
            TerminalColor.YELLOW if info.status == ToolStatus.OUTDATED else TerminalColor.RED
        )
        status_text = f"{status_color}{info.status.value}{TerminalColor.RESET}"
        rows.append([
            t.id,
            t.name,
            t.category.value,
            info.detected_version or "-",
            t.recommended_version,
            status_text,
        ])

    headers = ["ID", "Name", "Category", "Installed Ver", "Recommended", "Status"]
    print("\n" + TerminalColor.BOLD + "eSim External Tools Catalog:" + TerminalColor.RESET)
    print(format_table(headers, rows))
    print()


def cmd_doctor(args, registry, platform_mgr):
    """Runs diagnostics across OS, tools, and Python dependencies."""
    checker = DependencyChecker(registry, platform_mgr)
    report = checker.run_diagnostics()

    print("\n" + TerminalColor.BOLD + "=" * 60 + TerminalColor.RESET)
    print(TerminalColor.BOLD + f"  eSim Tool Manager Doctor (Health Check)" + TerminalColor.RESET)
    print(TerminalColor.BOLD + "=" * 60 + TerminalColor.RESET)

    print(f"  OS:              {report.os_name} {report.os_version} ({report.architecture})")
    print(f"  Python:          {report.python_version}")
    print(f"  Package Manager: {report.package_manager or 'None detected'}")
    print(f"  Platform Key:    {platform_mgr.get_platform_key()}")
    print("-" * 60)

    rows = []
    for item in report.tools:
        status_color = TerminalColor.GREEN if item.is_compatible else TerminalColor.RED
        status_str = f"{status_color}{item.status.value}{TerminalColor.RESET}"
        rows.append([
            item.name,
            item.category.value,
            "Yes" if item.installed else "No",
            item.detected_version or "-",
            status_str,
        ])

    headers = ["Component", "Category", "Installed", "Version", "Health"]
    print(format_table(headers, rows))

    if report.issues:
        print("\n" + TerminalColor.RED + TerminalColor.BOLD + "Issues Found:" + TerminalColor.RESET)
        for issue in report.issues:
            print(f"  [!] {issue}")

        print("\n" + TerminalColor.CYAN + TerminalColor.BOLD + "Recommended Actions:" + TerminalColor.RESET)
        for rec in report.recommendations:
            print(f"  -> {rec}")
    else:
        print("\n" + TerminalColor.GREEN + TerminalColor.BOLD + "[SUCCESS] All eSim tools and dependencies are properly configured!" + TerminalColor.RESET)

    print()


def cmd_install(args, registry, platform_mgr):
    """Installs tools."""
    installer = ToolInstaller(registry, platform_mgr)

    if args.tool_id.lower() == "all":
        print(TerminalColor.BOLD + "Installing all missing/incompatible eSim tools..." + TerminalColor.RESET)
        results = installer.install_all(required_only=not args.all)
        for tid, res in results.items():
            color = TerminalColor.GREEN if res.success else TerminalColor.RED
            print(f"{color}[{ 'OK' if res.success else 'FAILED' }]{TerminalColor.RESET} {tid}: {res.message}")
    else:
        print(TerminalColor.BOLD + f"Installing tool '{args.tool_id}'..." + TerminalColor.RESET)
        res = installer.install_tool(args.tool_id)
        color = TerminalColor.GREEN if res.success else TerminalColor.RED
        print(f"{color}[{ 'OK' if res.success else 'FAILED' }]{TerminalColor.RESET} {res.message}")
        if res.error:
            print(f"Error details: {res.error}")


def cmd_update(args, registry, platform_mgr):
    """Updates tools."""
    updater = ToolUpdater(registry, platform_mgr)

    if args.tool_id.lower() == "all":
        print(TerminalColor.BOLD + "Checking and updating all tools..." + TerminalColor.RESET)
        results = updater.update_all()
        if not results:
            print(TerminalColor.GREEN + "All installed tools are up to date!" + TerminalColor.RESET)
        for tid, res in results.items():
            color = TerminalColor.GREEN if res.success else TerminalColor.RED
            print(f"{color}[{ 'OK' if res.success else 'FAILED' }]{TerminalColor.RESET} {tid}: {res.message}")
    else:
        print(TerminalColor.BOLD + f"Checking updates for '{args.tool_id}'..." + TerminalColor.RESET)
        has_update, curr, latest = updater.check_updates(args.tool_id)
        if has_update:
            print(f"Update available: v{curr} -> v{latest}. Applying update...")
            res = updater.update_tool(args.tool_id)
            color = TerminalColor.GREEN if res.success else TerminalColor.RED
            print(f"{color}[{ 'OK' if res.success else 'FAILED' }]{TerminalColor.RESET} {res.message}")
        else:
            print(TerminalColor.GREEN + f"'{args.tool_id}' is already at latest version (v{curr})." + TerminalColor.RESET)


def cmd_config(args, registry, platform_mgr):
    """Manages environment configuration."""
    cfg_mgr = ConfigManager(registry, platform_mgr)

    if args.config_action == "generate":
        payload = cfg_mgr.save_configuration()
        print(TerminalColor.GREEN + f"Configuration successfully generated at: {cfg_mgr.config_file}" + TerminalColor.RESET)
        print(f"  POSIX Shell script:   {cfg_mgr.config_dir / 'esim_env.sh'}")
        print(f"  Windows Batch script: {cfg_mgr.config_dir / 'esim_env.bat'}")
        print(f"  Dotenv file:          {cfg_mgr.config_dir / '.env'}")
    elif args.config_action == "show":
        env = cfg_mgr.generate_active_environment()
        print("\n" + TerminalColor.BOLD + "Active eSim Environment Variables:" + TerminalColor.RESET)
        for k, v in env.items():
            print(f"  {k} = {v}")
        print()
    elif args.config_action == "set":
        if not args.key or not args.value:
            print(TerminalColor.RED + "Error: Must specify KEY and VALUE." + TerminalColor.RESET)
            return
        cfg_mgr.set_user_override(args.key, args.value)
        cfg_mgr.save_configuration()
        print(TerminalColor.GREEN + f"Set {args.key}={args.value} and updated configuration." + TerminalColor.RESET)


def cmd_gui(args, registry, platform_mgr):
    """Launches the graphical user interface."""
    from esim_tool_manager.gui import launch_gui
    launch_gui(registry, platform_mgr)


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="esim-tools",
        description="eSim Automated Tool Manager - Manage external EDA tools & dependencies.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Simulate commands without executing them.")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode for cross-platform simulation.")
    parser.add_argument("--platform", choices=["linux", "darwin", "windows"], help="Force specific platform mode.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose debug logging.")

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # list
    subparsers.add_parser("list", help="List all registered eSim tools and their install status.")

    # doctor
    subparsers.add_parser("doctor", help="Run comprehensive health check on tools and dependencies.")

    # install
    p_install = subparsers.add_parser("install", help="Install a tool or all tools.")
    p_install.add_argument("tool_id", help="Tool ID (e.g. ngspice, kicad, ghdl, verilator, or 'all').")
    p_install.add_argument("--all", action="store_true", help="Include optional tools when installing 'all'.")

    # update
    p_update = subparsers.add_parser("update", help="Update a tool or all tools.")
    p_update.add_argument("tool_id", help="Tool ID or 'all'.")

    # config
    p_config = subparsers.add_parser("config", help="Manage eSim configuration and environment scripts.")
    p_config.add_argument("config_action", choices=["generate", "show", "set"], help="Action to perform.")
    p_config.add_argument("key", nargs="?", help="Variable name (for 'set').")
    p_config.add_argument("value", nargs="?", help="Variable value (for 'set').")

    # gui
    subparsers.add_parser("gui", help="Launch interactive graphical user interface.")

    args = parser.parse_args()

    # Setup logger
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logger(level=log_level)

    # Initialize components
    registry = ToolRegistry()
    platform_mgr = get_platform_manager(
        force_platform=args.platform, dry_run=args.dry_run, mock_mode=args.mock
    )

    if not args.subcommand or args.subcommand == "doctor":
        cmd_doctor(args, registry, platform_mgr)
    elif args.subcommand == "list":
        cmd_list(args, registry, platform_mgr)
    elif args.subcommand == "install":
        cmd_install(args, registry, platform_mgr)
    elif args.subcommand == "update":
        cmd_update(args, registry, platform_mgr)
    elif args.subcommand == "config":
        cmd_config(args, registry, platform_mgr)
    elif args.subcommand == "gui":
        cmd_gui(args, registry, platform_mgr)


if __name__ == "__main__":
    main()
