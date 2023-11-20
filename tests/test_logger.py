from northy.logger import setup_logger
import logging

def test_logger():
    logger = logging.getLogger(__name__)
    assert setup_logger() == None
    logger.debug("Test logger")
    logger.info("Test logger")
    logger.warning("Test logger")
    logger.error("Test logger")
    logger.critical("Test logger")
