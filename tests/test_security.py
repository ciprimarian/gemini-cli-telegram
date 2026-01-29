import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gemini_telegram_bridge.security import AccessController, SecurityMode


class SecurityTests(unittest.TestCase):
    def test_power_mode_requires_admin(self) -> None:
        access = AccessController({1}, {99}, SecurityMode.BALANCED)
        with self.assertRaises(PermissionError):
            access.resolve_mode(1, "power")

    def test_admin_can_use_power_mode(self) -> None:
        access = AccessController({1}, {99}, SecurityMode.BALANCED)
        self.assertEqual(access.resolve_mode(99, "power"), SecurityMode.POWER)


if __name__ == "__main__":
    unittest.main()
