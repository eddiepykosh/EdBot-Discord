# common/logger.py
import logging
import os

def get_logger(name: str, log_dir: str = "logs", level: int = logging.INFO) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding multiple handlers if logger already has them
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler(os.path.join(log_dir, f"{name}.log"), mode='a')
        file_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console handler (prints to stdout)
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("%(name)s %(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger
