import logging

import pytest

from pylogcfg import pylogcfg as pcfg
from pylogcfg.pylogcfg import get_logger


def test_stop_listener_handles_missing_queue(monkeypatch):
    # Simulate missing globals
    monkeypatch.setattr(pcfg, "_listener", None)
    monkeypatch.setattr(pcfg, "_log_queue", None)
    # Should not raise
    pcfg._stop_listener()


def test_get_logger_initialization_fails_raises_runtime(monkeypatch):
    def fake_init(cfg):
        raise RuntimeError("boom")

    monkeypatch.setattr(pcfg, "initialize_logging", fake_init)
    with pytest.raises(RuntimeError):
        get_logger("something")
