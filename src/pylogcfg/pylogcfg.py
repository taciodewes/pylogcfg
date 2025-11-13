"""
Main module for managing asynchronous loggers and logging queues.
"""

from __future__ import annotations

import atexit
import logging
import logging.config
import logging.handlers
import queue
import threading
import time
from pathlib import Path
from typing import Any, Optional

from .cfg_pylogcfg import _LOGGER_NAME, JSONLogFormatter, setup

# Global objects controlling the logging system state
_listener: Optional[logging.handlers.QueueListener] = None
_logger: Optional[logging.Logger] = None
_log_queue: Optional[queue.Queue] = None
_init_lock = threading.Lock()


def initialize_logging(json_config: dict[str, Any]) -> logging.Logger:
    """
    Initializes the logging system with queue support and asynchronous JSON writing.

    Parameters
    ----------
    json_config : dict[str, Any]
        Configuration dictionary loaded from JSON.

    Returns
    -------
    logging.Logger
        The main system logger.
    """
    global _logger, _log_queue, _listener

    with _init_lock:
        if _logger is not None:
            return _logger

        # Create queue for asynchronous log processing
        _log_queue = queue.Queue()

        # FileHandler with rotation and JSON formatter
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(json_config.get("log_file")),
            maxBytes=int(json_config.get("max_log_size", 5_242_880)),
            backupCount=int(json_config.get("backup_count", 5)),
            encoding="utf-8",
            delay=True,
        )
        file_handler.namer = lambda name: Path(name).with_suffix(".jsonl").as_posix()
        file_handler.setFormatter(JSONLogFormatter(json_config))
        file_handler.setLevel(logging.DEBUG)

        # Listener that consumes the queue on a separate thread
        _listener = logging.handlers.QueueListener(_log_queue, file_handler)
        _listener.start()
        atexit.register(_stop_listener)

        # Base logging configuration (console + queue)
        log_config: dict[str, Any] = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "format": json_config.get("console_format"),
                    "datefmt": "[%X]",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "console",
                    "level": "DEBUG",
                    "stream": "ext://sys.stdout",
                },
                "queue": {
                    "class": "logging.handlers.QueueHandler",
                    "queue": _log_queue,
                    "level": "DEBUG",
                },
            },
            "loggers": {
                _LOGGER_NAME: {
                    "handlers": ["console", "queue"],
                    "level": "DEBUG",
                    "propagate": False,
                },
            },
            "root": {"handlers": ["console", "queue"], "level": "DEBUG"},
        }

        logging.config.dictConfig(log_config)
        _logger = logging.getLogger(_LOGGER_NAME)
        _logger.info("Logging configured: console + JSON via QueueListener")
        _logger.info("Log file: %s", file_handler.baseFilename)

        return _logger


def _stop_listener() -> None:
    """
    Gracefully and safely stops the logging queue listener.

    Note
    ----
    The qsize() method is only an estimate and may not accurately reflect
    the actual number of pending messages.
    """
    global _listener, _log_queue

    if _listener is None:
        return

    try:
        pending = _log_queue.qsize() if _log_queue else -1
    except Exception:
        pending = -1

    print(f"INFO:pylogcfg:Listener stopping ({pending} pending messages)...")

    # Wait until the queue is empty or until a timeout (2 seconds)
    timeout = time.monotonic() + 2.0
    while time.monotonic() < timeout:
        try:
            if not _log_queue or _log_queue.qsize() == 0:
                break
        except Exception:
            break
        time.sleep(0.05)

    try:
        _listener.stop()
        print("INFO:pylogcfg:Listener stopped successfully.")
    except Exception as exc:
        print(f"ERROR:pylogcfg:Failed to stop listener: {exc}")
    finally:
        _listener = None
        _log_queue = None


def get_logger(
    name: Optional[str] = None, level: Optional[str | int] = None
) -> logging.Logger:
    """
    Retrieves a ready-to-use logger, ensuring the logging system is initialized only once.

    Parameters
    ----------
    name : str, optional
        Custom logger name. Defaults to the name in configuration.
    level : str | int, optional
        Logging level. Defaults to "DEBUG".

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    json_config: dict[str, Any] = setup()
    logger_name: str = json_config.get("logger_name") if name is None else name

    try:
        logger = initialize_logging(json_config)
    except Exception as exc:
        raise RuntimeError("Failed to initialize logging.") from exc

    log_level: str | int = "DEBUG" if level is None else level
    new_logger = logging.getLogger(logger_name) if logger_name else logger
    new_logger.setLevel(log_level)

    return new_logger
