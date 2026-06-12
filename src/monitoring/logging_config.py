"""
Logging configuration for the crypto trading agent.
"""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """
    Set up structured logging for the application.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("agent.log"),
        ],
    )

    # Set levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)


if __name__ == "__main__":
    setup_logging()
    logging.info("Logging initialized.")
