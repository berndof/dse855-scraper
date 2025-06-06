import logging
import os

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler

load_dotenv()
console = Console(soft_wrap=True)

handler = RichHandler(
    console=console,
    markup=True,
    rich_tracebacks=True,
    show_time=True,
    show_level=True,
    show_path=True
)

formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)

log_level = os.getenv("LOG_LEVEL", "INFO").upper()

def setup_logs() -> None:

    handler.setLevel(log_level)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler],
    # force=True  # Garante que sobrescreva handlers anteriores
    )



def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    return logger