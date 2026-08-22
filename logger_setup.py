import logging
import os
from datetime import datetime

def setup_logger(name="trading_engine", log_dir="logs"):
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # The root captures everything

    # The Format: [2026-08-21 11:15:00] [INFO] [main.py] - Starting...
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. The Console (Terminal Screen) - Clean, INFO only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 2. The Hard Drive (The Black Box) - Granular, DEBUG level
    log_file = os.path.join(log_dir, f"execution_{datetime.now().strftime('%Y-%m-%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Attach them to the logger
    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
