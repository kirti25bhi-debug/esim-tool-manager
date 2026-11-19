"""Logging module for eSim Automated Tool Manager.

Provides file, console, and in-memory logging with support for UI listeners.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional

def get_default_log_dir() -> Path:
    env_dir = os.environ.get("ESIM_HOME")
    if env_dir:
        return Path(env_dir) / "logs"
    try:
        p = Path.home() / ".esim" / "logs"
        p.mkdir(parents=True, exist_ok=True)
        return p
    except (PermissionError, OSError):
        p = Path.cwd() / ".esim" / "logs"
        try:
            p.mkdir(parents=True, exist_ok=True)
            return p
        except Exception:
            return Path.cwd()

DEFAULT_LOG_FILE = get_default_log_dir() / "tool_manager.log"

# ANSI Colors for terminal output
class TerminalColor:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"


class ColoredConsoleFormatter(logging.Formatter):
    """Custom formatter with ANSI color support for terminal logs."""

    LEVEL_COLORS = {
        logging.DEBUG: TerminalColor.GRAY,
        logging.INFO: TerminalColor.GREEN,
        logging.WARNING: TerminalColor.YELLOW,
        logging.ERROR: TerminalColor.RED,
        logging.CRITICAL: TerminalColor.RED + TerminalColor.BOLD,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, TerminalColor.RESET)
        time_str = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        prefix = f"[{time_str}] [{record.levelname:^7}]"
        if sys.stdout.isatty():
            return f"{color}{prefix}{TerminalColor.RESET} {record.getMessage()}"
        return f"{prefix} {record.getMessage()}"


class MemoryLogHandler(logging.Handler):
    """Stores logs in memory and notifies subscribers (e.g., GUI log viewer)."""

    def __init__(self, capacity: int = 1000):
        super().__init__()
        self.capacity = capacity
        self.records: List[str] = []
        self.listeners: List[Callable[[str], None]] = []

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.records.append(msg)
            if len(self.records) > self.capacity:
                self.records.pop(0)
            for listener in self.listeners:
                try:
                    listener(msg)
                except Exception:
                    pass
        except Exception:
            self.handleError(record)

    def subscribe(self, callback: Callable[[str], None]):
        self.listeners.append(callback)

    def unsubscribe(self, callback: Callable[[str], None]):
        if callback in self.listeners:
            self.listeners.remove(callback)


_memory_handler: Optional[MemoryLogHandler] = None
_logger_initialized = False


def setup_logger(
    name: str = "esim_tool_manager",
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    enable_console: bool = True,
) -> logging.Logger:
    """Configures and returns the central logger instance."""
    global _memory_handler, _logger_initialized

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if _logger_initialized:
        return logger

    # Ensure log directory exists
    target_log_file = log_file or DEFAULT_LOG_FILE
    try:
        target_log_file.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        target_log_file = Path("esim_tool_manager.log")

    # File Handler
    try:
        file_handler = logging.FileHandler(target_log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        sys.stderr.write(f"Warning: Could not create log file: {e}\n")

    # Console Handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(ColoredConsoleFormatter())
        logger.addHandler(console_handler)

    # In-memory Handler for GUI / live inspection
    _memory_handler = MemoryLogHandler()
    _memory_handler.setLevel(logging.DEBUG)
    _memory_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    )
    logger.addHandler(_memory_handler)

    _logger_initialized = True
    return logger


def get_logger(name: str = "esim_tool_manager") -> logging.Logger:
    """Retrieve the logger instance."""
    return logging.getLogger(name)


def get_memory_log_handler() -> Optional[MemoryLogHandler]:
    """Retrieve the in-memory log handler for GUI hooks."""
    return _memory_handler
