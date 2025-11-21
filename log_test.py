import logging
from app.logger_config import configure_logger

logger = logging.getLogger()

def some_func(x, y):
    logger.info(f"start func: %s, with args: x=%s, y=%s", some_func.__name__, x, y)
    logger.warning('be careful')
    res = x + y
    print(res)
    logger.info(f"end func: %s", some_func.__name__)
    return res


def main():
    configure_logger()
    some_func(1, 2)

main()