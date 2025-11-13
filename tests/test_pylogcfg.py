import logging

from pylogcfg.pylogcfg import get_logger


def test_logger_initialization(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    logger.info("Test message")
