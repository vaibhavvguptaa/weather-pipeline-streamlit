"""
Tests for src/logger.py — logging configuration and rotation.
"""

import inspect
from logging.handlers import RotatingFileHandler

import pytest

from src.config import config
from src.logger import get_logger


class TestLogRotation:
    def test_has_rotating_file_handler(self):
        test_logger = get_logger("test_rotation_check")
        file_handlers = [h for h in test_logger.handlers if isinstance(h, RotatingFileHandler)]
        assert len(file_handlers) >= 1

    def test_max_bytes_is_5mb(self):
        test_logger = get_logger("test_rotation_bytes")
        for h in test_logger.handlers:
            if isinstance(h, RotatingFileHandler):
                assert h.maxBytes == 5 * 1024 * 1024
                break
        else:
            pytest.fail("No RotatingFileHandler found")

    def test_backup_count_is_5(self):
        test_logger = get_logger("test_rotation_backup")
        for h in test_logger.handlers:
            if isinstance(h, RotatingFileHandler):
                assert h.backupCount == 5
                break
        else:
            pytest.fail("No RotatingFileHandler found")


class TestConfigurableLogDir:
    def test_get_logger_accepts_log_dir(self):
        sig = inspect.signature(get_logger)
        assert "log_dir" in sig.parameters

    def test_config_has_log_dir(self):
        assert hasattr(config, "log_dir")
        assert config.log_dir == "logs" or isinstance(config.log_dir, str)

