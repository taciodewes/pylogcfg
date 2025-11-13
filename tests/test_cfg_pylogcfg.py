import json
import logging
import os
from pathlib import Path

import pytest

from pylogcfg import cfg_pylogcfg as cfg


def test_create_default_config_creates_file(tmp_path: Path, monkeypatch):
    # Point the module config paths to tempdir
    tmp_file = tmp_path / "pylogconfig.json"
    tmp_logs = tmp_path / "logs"
    monkeypatch.setattr(cfg, "config_file", tmp_file)
    monkeypatch.setattr(cfg, "logs_dir", tmp_logs)

    # Ensure file does not exist
    if tmp_file.exists():
        tmp_file.unlink()

    cfg.create_default_config()
    assert tmp_file.exists()
    data = json.loads(tmp_file.read_text(encoding="utf-8"))
    assert "environment" in data
    assert "timezone" in data or "timezone" in data.keys()


def test_load_configs_creates_default_when_missing(tmp_path: Path, monkeypatch):
    tmp_file = tmp_path / "pylogconfig.json"
    monkeypatch.setattr(cfg, "config_file", tmp_file)
    # remove if present, call load_configs -> should create
    if tmp_file.exists():
        tmp_file.unlink()

    cfg.load_configs()
    assert tmp_file.exists()


def test_json_formatter_invalid_timezone_fallbacks_to_local(monkeypatch):
    # Use a config with invalid timezone
    bad_cfg = {"timezone": "No/Such_Zone", "date_format": "%Y-%m-%dT%H:%M:%S%z"}
    fmt = cfg.JSONLogFormatter(bad_cfg)
    # formatTime should not raise
    record = logging.LogRecord("t", logging.INFO, "", 0, "msg", (), None)
    out = fmt.format(record)
    assert "message" in out  # basic check that format returned a JSON string


def test_json_formatter_includes_extras(tmp_path: Path):
    cfg_dict = {"include_extras": True, "included_keys": {}, "date_format": "%Y-%m-%d"}
    fmt = cfg.JSONLogFormatter(cfg_dict)
    record = logging.LogRecord("t", logging.INFO, "", 0, "hello", (), None)
    # add an extra attribute
    record.my_extra = "value_x"
    out = fmt.format(record)
    assert "my_extra" in out
    assert "value_x" in out
