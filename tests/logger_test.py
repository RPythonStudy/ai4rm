# tests/logger_test.py
from logger.logger import get_logger

import time

def main():
    logger = get_logger("test_logger")
    logger.critical("This is CRITICAL log")
    logger.error("This is ERROR log")
    logger.warning("This is WARNING log")
    logger.info("This is INFO log")
    logger.debug("This is DEBUG log")
    logger.trace("This is TRACE log")
    # 예외 로그 확인
    try:
        1/0
    except Exception:
        logger.exception("예외 발생!")

if __name__ == "__main__":
    main()
