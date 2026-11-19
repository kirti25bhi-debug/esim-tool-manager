"""Unit tests for CLI execution."""

import sys
import unittest
from io import StringIO
from unittest.mock import patch

from esim_tool_manager.cli import main


class TestCLI(unittest.TestCase):
    def test_cli_list(self):
        with patch.object(sys, "argv", ["esim-tools", "list"]):
            with patch("sys.stdout", new_callable=StringIO) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("eSim External Tools Catalog", output)
                self.assertIn("ngspice", output)
                self.assertIn("kicad", output)

    def test_cli_doctor(self):
        with patch.object(sys, "argv", ["esim-tools", "doctor"]):
            with patch("sys.stdout", new_callable=StringIO) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("eSim Tool Manager Doctor", output)
                self.assertIn("Health Check", output)

    def test_cli_config_show(self):
        with patch.object(sys, "argv", ["esim-tools", "config", "show"]):
            with patch("sys.stdout", new_callable=StringIO) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("Active eSim Environment Variables", output)
                self.assertIn("ESIM_HOME", output)

    def test_cli_mock_install(self):
        with patch.object(sys, "argv", ["esim-tools", "--mock", "install", "ngspice"]):
            with patch("sys.stdout", new_callable=StringIO) as fake_out:
                main()
                output = fake_out.getvalue()
                self.assertIn("[OK]", output)
                self.assertIn("ngspice", output)


if __name__ == "__main__":
    unittest.main()
