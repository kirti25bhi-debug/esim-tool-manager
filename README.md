# eSim Automated Tool Manager

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS%20%7C%20Windows-green.svg)](https://esim.fossee.in)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-18%20passed%20%28100%25%29-brightgreen.svg)]()

An automated tool manager for **[eSim](https://esim.fossee.in)** (an open-source EDA tool for circuit design, simulation, analysis, and PCB design developed by FOSSEE, IIT Bombay).

This manager automates the **installation**, **configuration**, **update**, and **management** of external EDA tools and libraries (Ngspice, KiCad, GHDL, Verilator, GTKWave, OpenModelica, and scientific Python dependencies).

---

## 🌟 Key Features

* **📦 Cross-Platform Tool Installation:** Automatically downloads and installs required external tools across Linux (`apt`/`dnf`/`pacman`), macOS (`brew` formula & cask), and Windows (`winget`/`choco`).
* **🩺 eSim Doctor (Diagnostic Dependency Checker):** Multi-layer diagnostic health checker inspired by `flutter doctor` that inspects the OS, package managers, EDA binaries, and Python libraries, providing actionable remediation advice.
* **🔄 Update & Upgrade System:** Checks remote package feeds and GitHub releases for upstream updates and safely upgrades tools with minimal intervention.
* **⚙️ Automated Configuration & Path Management:** Automatically locates installed binaries and generates:
  * `esim_config.json`: Structured configuration file for eSim.
  * `esim_env.sh`: One-line POSIX shell script exporting environment variables and updating `PATH`.
  * `esim_env.bat`: Batch script for Windows Command Prompt.
  * `.env`: Environment variable file for developers.
* **🖥️ Dual User Interface (CLI + GUI):**
  * **CLI (`esim-tools`):** Fast, color-coded terminal interface with rich tables.
  * **GUI:** Modern, multi-threaded desktop interface built with pure Python `tkinter` (zero external dependencies required!).
* **🧩 Manifest-Driven Architecture:** All tools, version regexes, and packaging commands are defined in `tools_manifest.json`. Adding new tools or PDKs requires zero code modifications.

---

## 📁 Project Directory Structure

```text
esim-tool-manager/
├── README.md                      # Complete user guide and execution instructions
├── DESIGN_DOCUMENT.md             # In-depth architectural design specification
├── PRESENTATION.md                # 5-10 min video presentation script & slide deck
├── setup.py                       # Standard Python packaging setup
├── pyproject.toml                 # Modern Python build configuration
├── demo.py                        # Self-contained end-to-end evaluation demo script
├── esim_tool_manager/             # Core package
│   ├── __init__.py                # Package metadata
│   ├── cli.py                     # CLI entrypoint (doctor, list, install, update, config, gui)
│   ├── gui.py                     # Non-blocking Tkinter desktop application
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py              # Tool models, VersionSpec constraint matcher, action results
│   │   ├── registry.py            # Manifest loader and binary inspection engine
│   │   ├── installer.py           # Cross-platform installation and verification orchestrator
│   │   ├── updater.py             # Version delta inspector and update runner
│   │   ├── config_manager.py      # Environment generator (JSON, sh, bat, .env) & user overrides
│   │   ├── dependency_checker.py  # 'eSim Doctor' multi-layer health inspection engine
│   │   └── logger.py              # Centralized color console, rotating file, and UI log handler
│   ├── platforms/
│   │   ├── __init__.py            # Platform factory
│   │   ├── base.py                # Abstract BasePlatformManager interface
│   │   ├── linux.py               # Linux adapter (apt, dnf, pacman, sudo detection)
│   │   ├── macos.py               # macOS adapter (brew formula & cask, /Applications search)
│   │   └── windows.py             # Windows adapter (winget, choco, ProgramFiles path search)
│   └── data/
│       └── tools_manifest.json    # Catalog of eSim tools, version rules, and package recipes
└── tests/                         # Comprehensive unit test suite
    ├── __init__.py
    ├── test_models.py             # VersionSpec comparison and constraint tests
    ├── test_registry.py           # Manifest loading and version regex parsing tests
    ├── test_dependency_checker.py # Dependency and diagnostic health check tests
    ├── test_installer.py          # Installer & updater mock execution tests
    ├── test_config_manager.py     # Configuration & environment export tests
    └── test_cli.py                # CLI subcommand tests
```

---

## 🚀 Instructions for Execution

### Prerequisites
* **Python 3.8+** (Works on Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13+)
* **Zero external Python libraries required** for core functionality and GUI! Everything is built on the Python standard library (`urllib`, `subprocess`, `argparse`, `json`, `pathlib`, `shutil`, `logging`, `dataclasses`, `tkinter`).

---

### Step 1: Run the Automated Screening Demo (Recommended)
To see an end-to-end demonstration of all 5 requirements in seconds:

```bash
python3 demo.py
```

This runs a guided walkthrough:
1. Loads the manifest catalog.
2. Runs **eSim Doctor** diagnostics on the host machine.
3. Simulates **cross-platform tool installation** across Linux (`apt`), macOS (`brew`), and Windows (`winget`).
4. Simulates **update checks & upgrades**.
5. Automatically generates **`esim_config.json`**, **`esim_env.sh`**, and **`esim_env.bat`**.

---

### Step 2: Run the Unit Test Suite
To verify code correctness, version comparison logic, and platform abstractions:

```bash
python3 -m unittest discover tests
```

Expected output:
```text
..................
----------------------------------------------------------------------
Ran 18 tests in 0.020s

OK
```

---

### Step 3: Using the Command Line Interface (CLI)

You can invoke the CLI directly using `python3 -m esim_tool_manager.cli` (or install it via `pip install -e .` to enable the `esim-tools` shortcut command).

#### 1. Diagnostic Health Check ("eSim Doctor")
Audits your operating system, installed EDA tools, and Python dependencies:
```bash
python3 -m esim_tool_manager.cli doctor
```

#### 2. View Catalog & Installed Status
Lists all registered tools, their categories, installed versions, and compatibility:
```bash
python3 -m esim_tool_manager.cli list
```

#### 3. Install Tools
Installs a specific tool (e.g. `ngspice`, `kicad`, `ghdl`, `verilator`) or all missing tools:
```bash
# Install a single tool
python3 -m esim_tool_manager.cli install ngspice

# Install all missing tools
python3 -m esim_tool_manager.cli install all

# Test installation in dry-run mode (safe preview)
python3 -m esim_tool_manager.cli --dry-run install kicad

# Simulate installation for another OS (e.g., Linux on a Mac/Windows machine)
python3 -m esim_tool_manager.cli --platform linux --dry-run install ngspice
```

#### 4. Update & Upgrade Tools
Checks for newer versions and upgrades them:
```bash
# Check and update a specific tool
python3 -m esim_tool_manager.cli update ngspice

# Check and update all installed tools
python3 -m esim_tool_manager.cli update all
```

#### 5. Configuration & Environment Management
Generates and inspects eSim configuration files and shell environment wrappers:
```bash
# Generate esim_config.json, esim_env.sh, and esim_env.bat
python3 -m esim_tool_manager.cli config generate

# Show active environment variables
python3 -m esim_tool_manager.cli config show

# Set custom user override (e.g., custom model or PDK directory)
python3 -m esim_tool_manager.cli config set CUSTOM_MODEL_PATH /opt/models/sky130
```

To activate the generated environment in your terminal:
* **Linux / macOS:**
  ```bash
  source ~/.esim/esim_env.sh
  ```
* **Windows (CMD):**
  ```cmd
  call %USERPROFILE%\.esim\esim_env.bat
  ```

---

### Step 4: Launching the Graphical User Interface (GUI)

To launch the desktop GUI:

```bash
python3 -m esim_tool_manager.cli gui
```

#### GUI Capabilities:
* **Tools & Status Tab:** Browse the full EDA catalog with status badges, and trigger one-click "Install All Missing" or "Upgrade Outdated".
* **eSim Doctor Tab:** Runs diagnostics asynchronously in a background thread (no UI freezing) and displays remediation steps.
* **Configuration Tab:** Inspects active environment paths and exports shell/batch wrappers.
* **Action Logs Tab:** Real-time stream of all installation, update, and configuration events.

---

## ⚙️ Testing Flags & Simulation Options

For automated testing or evaluation in environments without root/admin permissions:
* `--mock`: Simulates successful installations and updates without modifying host system packages.
* `--dry-run`: Prints the exact commands that would be executed by the package manager without executing them.
* `--platform <linux|darwin|windows>`: Simulates package manager behavior for a specific operating system.
* `--verbose` / `-v`: Enables debug logging.

Example:
```bash
python3 -m esim_tool_manager.cli --mock --platform windows install kicad
```

---

## 📖 Deliverables Summary

1. **Design Document:** Full architectural design specification in [`DESIGN_DOCUMENT.md`](DESIGN_DOCUMENT.md).
2. **Presentation Deck & Video Script:** 5-10 minute presentation deck & script in [`PRESENTATION.md`](PRESENTATION.md).
3. **Working Code Implementation:** Complete Python prototype in `esim_tool_manager/` covering all 5 requirements.
4. **Execution Instructions:** Clear, step-by-step instructions in this `README.md`.
