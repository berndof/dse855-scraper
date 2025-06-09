import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler

load_dotenv()
console = Console(soft_wrap=True)

console_handler = RichHandler(
    console=console,
    markup=True,
    rich_tracebacks=True,
    show_time=True,
    show_level=True,
    show_path=True
)

console_formatter = logging.Formatter("%(message)s")
console_handler.setFormatter(console_formatter)

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_file_path = "logs/scraper.log"
log_file_max_mb = 5
log_file_backup = 3

if not os.path.exists(os.path.dirname(log_file_path)):
    os.makedirs(os.path.dirname(log_file_path))

file_handler = RotatingFileHandler(
    filename=log_file_path,
    maxBytes=log_file_max_mb * 1024 * 1024,
    backupCount=log_file_backup,
    encoding="utf-8"
)
file_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(file_formatter)


def setup_logs() -> None:
    file_handler.setLevel(log_level)
    console_handler.setLevel(log_level)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler],
    # force=True  # Garante que sobrescreva handlers anteriores
    )

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    return logger