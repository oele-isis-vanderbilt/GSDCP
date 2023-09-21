#! /usr/bin/env python3


import logging
import random
import time
from pathlib import Path

from faker import Faker

WATCH_DIR = Path(__file__).parent.parent / "watch_dir"


def setup_loggers():
    logger1 = logging.getLogger("LOG FILE 1")
    logger1.setLevel(logging.DEBUG)
    h1 = logging.FileHandler(WATCH_DIR / "log_file_1.log", mode="w")
    h2 = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    h1.setFormatter(formatter)
    h2.setFormatter(formatter)

    logger2 = logging.getLogger("LOG FILE 2")
    logger2.setLevel(logging.DEBUG)
    h3 = logging.FileHandler(WATCH_DIR / "log_file_2.log", mode="w")
    h4 = logging.StreamHandler()

    h3.setFormatter(formatter)
    h4.setFormatter(formatter)
    logger1.addHandler(h1)
    logger1.addHandler(h2)
    logger2.addHandler(h3)
    logger2.addHandler(h4)

    return logger1, logger2


def main():
    faker = Faker()
    logger1, logger2 = setup_loggers()

    while True:
        logger = random.choice([logger1, logger2])
        level = random.choice(
            [
                logging.DEBUG,
                logging.INFO,
                logging.WARNING,
                logging.ERROR,
                logging.CRITICAL,
            ]
        )
        logger.log(level, faker.sentence(20))
        time.sleep(random.random())


if __name__ == "__main__":
    main()
