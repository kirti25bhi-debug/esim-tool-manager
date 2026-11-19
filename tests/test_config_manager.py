"""Unit tests for ConfigManager."""

import tempfile
import unittest
from pathlib import Path
from esim_tool_manager.core.config_manager import ConfigManager
from esim_tool_manager.core.registry import ToolRegistry
from esim_tool_manager.platforms import get_platform_manager


class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)
        self.registry = ToolRegistry()
        self.platform_mgr = get_platform_manager(mock_mode=True)
        self.cfg_mgr = ConfigManager(self.registry, self.platform_mgr, config_dir=self.config_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_configuration(self):
        payload = self.cfg_mgr.save_configuration()
        self.assertIn("environment_variables", payload)
        self.assertIn("tools", payload)

        # Check generated files exist
        self.assertTrue((self.config_dir / "esim_config.json").exists())
        self.assertTrue((self.config_dir / "esim_env.sh").exists())
        self.assertTrue((self.config_dir / "esim_env.bat").exists())
        self.assertTrue((self.config_dir / ".env").exists())

    def test_user_overrides(self):
        self.cfg_mgr.set_user_override("CUSTOM_VAR", "TEST_VAL")
        overrides = self.cfg_mgr.get_user_overrides()
        self.assertEqual(overrides.get("CUSTOM_VAR"), "TEST_VAL")

        env = self.cfg_mgr.generate_active_environment()
        self.assertEqual(env.get("CUSTOM_VAR"), "TEST_VAL")


if __name__ == "__main__":
    unittest.main()
