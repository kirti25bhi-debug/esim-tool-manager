import unittest
from esim_tool_manager.core.models import VersionSpec, ToolStatus, ToolCategory


class TestVersionSpec(unittest.TestCase):
    def test_version_equality(self):
        v1 = VersionSpec("38")
        v2 = VersionSpec("38.0")
        v3 = VersionSpec("v38")
        self.assertEqual(v1, v2)
        self.assertEqual(v1, v3)

    def test_version_comparisons(self):
        self.assertTrue(VersionSpec("38") < VersionSpec("42"))
        self.assertTrue(VersionSpec("7.0.1") > VersionSpec("6.0.9"))
        self.assertTrue(VersionSpec("1.0.0") <= VersionSpec("1.0.0"))
        self.assertTrue(VersionSpec("43") >= VersionSpec("38"))

    def test_constraint_matching(self):
        v = VersionSpec("7.0.2")
        self.assertTrue(v.matches_constraint(">= 6.0"))
        self.assertTrue(v.matches_constraint("< 8.0"))
        self.assertTrue(v.matches_constraint(">= 6.0, < 8.0"))
        self.assertFalse(v.matches_constraint(">= 8.0"))
        self.assertTrue(v.matches_constraint("== 7.0.2"))
        self.assertFalse(v.matches_constraint("!= 7.0.2"))

    def test_tilde_constraint(self):
        v1 = VersionSpec("6.0.4")
        self.assertTrue(v1.matches_constraint("~= 6.0"))
        v2 = VersionSpec("7.0.0")
        self.assertFalse(v2.matches_constraint("~= 6.0"))


if __name__ == "__main__":
    unittest.main()
