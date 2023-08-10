from northy.logger import setup_logger
import logging

def test_():
    logger = logging.getLogger(__name__)
    assert setup_logger() == None
    logger.debug("Test logger")
    logger.info("Test logger")
    logger.warning("Test logger")
    logger.error("Test logger")
    logger.critical("Test logger")

if __name__ == "__main__":
    test_()
