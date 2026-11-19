"""Unit tests for ToolRegistry."""

import unittest
from esim_tool_manager.core.registry import ToolRegistry
from esim_tool_manager.platforms import get_platform_manager


class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ToolRegistry()
        self.platform_mgr = get_platform_manager(mock_mode=True)

    def test_load_manifest(self):
        tools = self.registry.get_all_tools()
        self.assertGreaterEqual(len(tools), 5)
        tool_ids = [t.id for t in tools]
        self.assertIn("ngspice", tool_ids)
        self.assertIn("kicad", tool_ids)
        self.assertIn("ghdl", tool_ids)

    def test_get_tool(self):
        ngspice = self.registry.get_tool("ngspice")
        self.assertIsNotNone(ngspice)
        self.assertEqual(ngspice.name, "Ngspice Circuit Simulator")
        self.assertIn("libngspice", ngspice.dependencies)

    def test_version_extraction(self):
        text_ngspice = "ngspice-43: circuit simulation engine"
        ver = self.registry._extract_version(text_ngspice, r"(?:ngspice-|Ngspice\s+)(\d+(?:\.\d+)*)")
        self.assertEqual(ver, "43")

        text_kicad = "kicad-cli 7.0.11"
        ver_kicad = self.registry._extract_version(text_kicad, r"(\d+\.\d+(?:\.\d+)?)")
        self.assertEqual(ver_kicad, "7.0.11")


if __name__ == "__main__":
    unittest.main()
