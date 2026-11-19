"""Unit tests for ToolInstaller and ToolUpdater."""

import unittest
from esim_tool_manager.core.installer import ToolInstaller
from esim_tool_manager.core.registry import ToolRegistry
from esim_tool_manager.core.updater import ToolUpdater
from esim_tool_manager.platforms import get_platform_manager


class TestInstallerAndUpdater(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.platform_mgr = get_platform_manager(mock_mode=True)
        self.installer = ToolInstaller(self.registry, self.platform_mgr)
        self.updater = ToolUpdater(self.registry, self.platform_mgr)

    def test_mock_install_tool(self):
        res = self.installer.install_tool("ngspice")
        self.assertTrue(res.success)
        self.assertEqual(res.tool_id, "ngspice")
        self.assertEqual(res.action, "install")

    def test_install_unknown_tool(self):
        res = self.installer.install_tool("nonexistent_tool_123")
        self.assertFalse(res.success)

    def test_mock_update_tool(self):
        # Install first so mock knows it
        self.installer.install_tool("ngspice")
        res = self.updater.update_tool("ngspice")
        self.assertTrue(res.success)


if __name__ == "__main__":
    unittest.main()
