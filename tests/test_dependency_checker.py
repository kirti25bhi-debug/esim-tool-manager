"""Unit tests for DependencyChecker."""

import unittest
from esim_tool_manager.core.dependency_checker import DependencyChecker
from esim_tool_manager.core.models import ToolStatus
from esim_tool_manager.core.registry import ToolRegistry
from esim_tool_manager.platforms import get_platform_manager


class TestDependencyChecker(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.platform_mgr = get_platform_manager(mock_mode=True)
        self.checker = DependencyChecker(self.registry, self.platform_mgr)

    def test_check_python_library(self):
        # numpy or sys should be detectable
        info = self.checker.check_python_library("pip")
        # In standard python, pip is either installed or not, but it shouldn't crash
        self.assertIn(info.status, [ToolStatus.INSTALLED_OK, ToolStatus.NOT_INSTALLED])

    def test_run_diagnostics(self):
        report = self.checker.run_diagnostics()
        self.assertIsNotNone(report.os_name)
        self.assertIsNotNone(report.python_version)
        self.assertGreaterEqual(len(report.tools), 5)


if __name__ == "__main__":
    unittest.main()
