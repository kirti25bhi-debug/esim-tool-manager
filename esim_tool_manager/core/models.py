"""Data models and abstractions for eSim Automated Tool Manager."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ToolCategory(str, Enum):
    SIMULATION = "Simulation"
    SCHEMATIC_PCB = "Schematic & PCB"
    DIGITAL = "Digital Design"
    MODELING = "Multi-Domain Modeling"
    SYSTEM_DEPENDENCY = "System Dependency"
    PYTHON_LIBRARY = "Python Library"


class ToolStatus(str, Enum):
    NOT_INSTALLED = "Not Installed"
    INSTALLED_OK = "Installed & Compatible"
    OUTDATED = "Update Available"
    INCOMPATIBLE = "Incompatible Version"
    MISSING_DEPENDENCY = "Missing Dependencies"
    ERROR = "Error / Broken"


class VersionSpec:
    """Handles semantic and standard software version comparisons.

    Supports versions like '38', '38.2', '7.0.10', 'v0.9.1' and constraints
    like '>=38', '<8.0', '==7.0.2', '~=6.0'.
    """

    def __init__(self, version_str: str):
        self.raw = version_str.strip()
        self.parsed = self._parse(self.raw)

    @staticmethod
    def _parse(v_str: str) -> Tuple[int, ...]:
        clean = re.sub(r"^[vV]", "", v_str.strip())
        # extract numeric components
        parts = re.split(r"[-_+.]", clean)
        nums = []
        for p in parts:
            m = re.match(r"^(\d+)", p)
            if m:
                nums.append(int(m.group(1)))
            else:
                break
        return tuple(nums) if nums else (0,)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, VersionSpec):
            other = VersionSpec(str(other))
        return self._compare(other) == 0

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, VersionSpec):
            other = VersionSpec(str(other))
        return self._compare(other) < 0

    def __le__(self, other: Any) -> bool:
        return self == other or self < other

    def __gt__(self, other: Any) -> bool:
        return not (self <= other)

    def __ge__(self, other: Any) -> bool:
        return not (self < other)

    def _compare(self, other: "VersionSpec") -> int:
        len_diff = len(self.parsed) - len(other.parsed)
        p1 = self.parsed + (0,) * max(0, -len_diff)
        p2 = other.parsed + (0,) * max(0, len_diff)
        if p1 < p2:
            return -1
        elif p1 > p2:
            return 1
        return 0

    def matches_constraint(self, constraint: str) -> bool:
        """Check if this version matches a constraint string (e.g. '>=38', '<8.0')."""
        constraint = constraint.strip()
        if not constraint or constraint == "*":
            return True

        # Handle compound constraints like ">=6.0, <8.0"
        if "," in constraint:
            sub_constraints = [c.strip() for c in constraint.split(",")]
            return all(self.matches_constraint(sc) for sc in sub_constraints)

        m = re.match(r"^(>=|<=|>|<|==|!=|~=)?\s*(.*)$", constraint)
        if not m:
            return True
        op, target_v_str = m.group(1) or "==", m.group(2)
        target = VersionSpec(target_v_str)

        if op == "==":
            return self == target
        elif op == "!=":
            return self != target
        elif op == ">=":
            return self >= target
        elif op == "<=":
            return self <= target
        elif op == ">":
            return self > target
        elif op == "<":
            return self < target
        elif op == "~=":
            # Compatible release clause (~= 6.0 allows >= 6.0 and < 7.0)
            if len(target.parsed) >= 2:
                next_major = target.parsed[0] + 1
                upper_bound = VersionSpec(f"{next_major}.0")
                return self >= target and self < upper_bound
            return self >= target

        return True

    def __str__(self) -> str:
        return self.raw

    def __repr__(self) -> str:
        return f"VersionSpec('{self.raw}')"


@dataclass
class PlatformPackageConfig:
    """Platform-specific installation packaging config."""

    package_name: str
    package_manager: str  # e.g., 'apt', 'brew', 'winget', 'choco', 'pip', 'direct'
    install_args: List[str] = field(default_factory=list)
    download_url: Optional[str] = None
    archive_type: Optional[str] = None  # e.g., 'tar.gz', 'zip', 'dmg', 'exe'
    binary_relative_path: Optional[str] = None


@dataclass
class ToolDefinition:
    """Metadata specification for a tool managed by eSim."""

    id: str
    name: str
    category: ToolCategory
    description: str
    binary_name: Dict[str, str]  # platform_key -> binary filename
    version_command: Dict[str, List[str]]  # platform_key -> command to check version
    version_regex: str
    min_version: Optional[str] = None
    max_version: Optional[str] = None
    recommended_version: str = "latest"
    dependencies: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    platform_packages: Dict[str, PlatformPackageConfig] = field(default_factory=dict)
    verification_command: Optional[List[str]] = None
    is_required: bool = True
    doc_url: str = ""

    def get_binary_name(self, platform_key: str) -> str:
        return self.binary_name.get(platform_key, self.binary_name.get("default", self.id))

    def get_version_command(self, platform_key: str) -> List[str]:
        return self.version_command.get(
            platform_key,
            self.version_command.get("default", [self.get_binary_name(platform_key), "--version"]),
        )


@dataclass
class InstalledToolInfo:
    """Current state and diagnostic info of a tool on the host system."""

    tool_id: str
    name: str
    category: ToolCategory
    installed: bool = False
    executable_path: Optional[str] = None
    detected_version: Optional[str] = None
    latest_version: Optional[str] = None
    status: ToolStatus = ToolStatus.NOT_INSTALLED
    status_message: str = ""
    is_compatible: bool = False
    update_available: bool = False
    missing_dependencies: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)


@dataclass
class ActionResult:
    """Result of an installation, update, or configuration action."""

    success: bool
    tool_id: str
    action: str  # 'install', 'update', 'configure', 'check'
    message: str
    output: str = ""
    error: str = ""
    duration_seconds: float = 0.0


@dataclass
class SystemDoctorReport:
    """Holistic health report of eSim toolchain."""

    os_name: str
    os_version: str
    architecture: str
    python_version: str
    package_manager: Optional[str]
    tools: List[InstalledToolInfo] = field(default_factory=list)
    all_healthy: bool = True
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
