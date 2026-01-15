from .app import run_bot
from .config import load_config


def run() -> None:
    config = load_config()
    config.validate_for_run()
    run_bot(config)
