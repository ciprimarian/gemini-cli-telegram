import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gemini_telegram_bridge.config import load_config


class ConfigTests(unittest.TestCase):
    def test_load_config_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "TELEGRAM_BOT_TOKEN=test-token",
                        "ALLOWED_TELEGRAM_IDS=123,456",
                        f"WORKSPACE_ROOT={tmp_dir}",
                    ]
                ),
                encoding="utf-8",
            )
            config = load_config(env_path)
            self.assertEqual(config.telegram_bot_token, "test-token")
            self.assertEqual(config.allowed_telegram_ids, {123, 456})
            self.assertEqual(config.workspace_root, Path(tmp_dir).resolve())


if __name__ == "__main__":
    unittest.main()
