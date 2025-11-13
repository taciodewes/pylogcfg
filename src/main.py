"""
Main module
"""

from pylogcfg.pylogcfg import get_logger

if __name__ == "__main__":
    logger = get_logger("demo")
    logger.debug("Init debug")
    logger.info("Ready system")
    logger.warning("Warning test")

    try:
        raise ValueError("simulated error")
    except Exception:
        logger.exception("Captured error!")

    logger.error("Stack error", stack_info=True)
