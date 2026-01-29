import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gemini_telegram_bridge.cli import build_parser


class CliTests(unittest.TestCase):
    def test_parser_accepts_check(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["check"])
        self.assertEqual(args.command, "check")

    def test_parser_accepts_init_path(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["init", "--path", "sample.env"])
        self.assertEqual(args.command, "init")
        self.assertEqual(args.path, "sample.env")


if __name__ == "__main__":
    unittest.main()
