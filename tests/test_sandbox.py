import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gemini_telegram_bridge.sandbox import WorkspaceSandbox


class SandboxTests(unittest.TestCase):
    def test_blocks_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            sandbox = WorkspaceSandbox(Path(tmp_dir))
            with self.assertRaises(PermissionError):
                sandbox.resolve("../escape")

    def test_resolves_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            (root / "project").mkdir()
            sandbox = WorkspaceSandbox(root)
            resolved = sandbox.resolve("project")
            self.assertEqual(resolved, (root / "project").resolve())


if __name__ == "__main__":
    unittest.main()
