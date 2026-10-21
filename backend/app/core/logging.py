import logging
from logging.handlers import RotatingFileHandler

from app.core.config import BACKEND_DIR, get_settings


def configure_logging():
    folder = BACKEND_DIR / "data" / "logs"
    folder.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(folder / "app.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger = logging.getLogger("app")
    logger.setLevel(get_settings().log_level.upper())
    for previous in logger.handlers[:]:
        previous.close()
        logger.removeHandler(previous)
    logger.addHandler(handler)
