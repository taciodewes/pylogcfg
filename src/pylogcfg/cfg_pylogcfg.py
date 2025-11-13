"""
pylogcfg configuration module with support for structured JSON formatting.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

_LOGGER_NAME: str = "pylogcfg"

config_file: Path = Path(__file__).resolve().parent.parent.parent / "pylogconfig.json"
logs_dir: Path = Path(__file__).resolve().parent.parent.parent / "data" / "logs"

# Recognized keys from the standard Python LogRecord
LOG_RECORD_KEYS: list[str] = [
    "asctime",
    "created",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "message",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskname",
]


def create_default_config() -> None:
    """
    Creates a default pylogcfg configuration file (JSON format)
    if none exists.
    """
    default_config: dict[str, Any] = {
        "environment": "development",
        "app": "my_system",
        "logs_dir": str(logs_dir),
        "console_format": logging.BASIC_FORMAT,
        "date_format": "%Y-%m-%dT%H:%M:%S%z",
        "include_extras": False,
        "level": "DEBUG",
        "logger_name": "mylogger",
        "backup_count": 5,
        "max_log_size": 5_242_880,
        "timezone": "America/Sao_Paulo",
        "included_keys": {k: True for k in LOG_RECORD_KEYS},
    }

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)

    print(f"INFO:pylogcfg:Default configuration file created at {config_file}")


def load_configs() -> dict[str, Any]:
    """
    Loads logging configuration from the JSON file.

    If the file does not exist, it creates a default one first.

    Returns
    -------
    dict[str, Any]
        Dictionary with all configuration parameters.
    """
    if not config_file.exists():
        create_default_config()

    with config_file.open(encoding="utf-8") as f:
        return json.load(f)


def setup() -> dict[str, Any]:
    """
    Reads JSON configurations and adds the 'log_file' key
    with the final log path. Ensures that the log directory exists.

    Returns
    -------
    dict[str, Any]
        Configuration dictionary including 'log_file'.
    """
    config = load_configs()
    logs_dir.mkdir(parents=True, exist_ok=True)
    config["log_file"] = logs_dir / "log.jsonl"
    return config


class JSONLogFormatter(logging.Formatter):
    """
    Formats log records into structured JSON according to the provided settings.
    """

    def __init__(self, json_config: Optional[dict[str, Any]] = None) -> None:
        """
        Initialize the JSON log formatter.

        Parameters
        ----------
        json_config : dict[str, Any], optional
            Custom configuration dictionary.
        """
        self.cfg: dict[str, Any] = json_config or {}
        super().__init__(datefmt=self.cfg.get("date_format"))

        active_keys: dict[str, bool] = self.cfg.get("included_keys", {})
        self.include_keys: list[str] = [
            key for key, active in active_keys.items() if active
        ]
        self.datefmt: str | None = self.cfg.get("date_format")

        try:
            self.tz: ZoneInfo = ZoneInfo(self.cfg.get("timezone", "America/Sao_Paulo"))
        except Exception:
            print("WARNING:pylogcfg:Invalid timezone. Using local timezone.")
            self.tz = datetime.now().astimezone().tzinfo or timezone.utc

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        """
        Format a LogRecord into a structured JSON string.

        Parameters
        ----------
        record : logging.LogRecord
            The log record to format.

        Returns
        -------
        str
            The JSON-formatted log string.
        """
        data: dict[str, Any] = {}

        for key in self.include_keys:
            if key in LOG_RECORD_KEYS:
                value = getattr(record, key, None)
                data[key] = value

        data["app"] = self.cfg.get("app")
        data["environment"] = self.cfg.get("environment")
        data["created"] = self.formatTime(record, self.datefmt)
        data["message"] = record.getMessage()

        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            if exc_text.strip() != "NoneType: None":
                data["exc_info"] = exc_text

        if record.stack_info:
            data["stack_info"] = self.formatStack(record.stack_info)

        # Include additional fields
        if self.cfg.get("include_extras", True):
            for key, value in vars(record).items():
                if key not in LOG_RECORD_KEYS:
                    data[key] = value

        return json.dumps(data, default=str, ensure_ascii=False)

    def formatTime(  # type: ignore[override]
        self, record: logging.LogRecord, datefmt: Optional[str] = None
    ) -> str:
        """
        Format the record creation time using the configured timezone.

        Parameters
        ----------
        record : logging.LogRecord
            The log record being formatted.
        datefmt : str, optional
            The datetime format string to use.

        Returns
        -------
        str
            Formatted timestamp string.
        """
        return datetime.fromtimestamp(record.created, tz=self.tz).strftime(
            datefmt or self.datefmt or "%Y-%m-%dT%H:%M:%S%z"
        )
