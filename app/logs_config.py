import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger("attendance")
    logger.setLevel(logging.INFO)

    # Rotate logs: max size 5 MB, keep 5 backups
    handler = RotatingFileHandler(
        "app/logs/app.log", 
        maxBytes=5_000_000, 
        backupCount=5
    )
    
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
