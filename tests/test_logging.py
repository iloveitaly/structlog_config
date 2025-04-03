import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import pytest
import structlog

from structlog_config import configure_logger


@pytest.fixture
def capture_logs():
    """Fixture to capture log output to a string buffer"""
    string_io = io.StringIO()

    with redirect_stdout(string_io):
        # Mock production environment check to test dev formatter
        with (
            mock.patch(
                "structlog_config.environments.is_production", return_value=False
            ),
            mock.patch("structlog_config.environments.is_staging", return_value=False),
        ):
            log = configure_logger()
            yield log, string_io


@pytest.fixture
def capture_prod_logs():
    """Fixture to capture log output in production mode"""
    string_io = io.StringIO()

    with redirect_stdout(string_io):
        # Force production mode
        with (
            mock.patch(
                "structlog_config.environments.is_production", return_value=True
            ),
            mock.patch("structlog_config.environments.is_staging", return_value=False),
        ):
            log = configure_logger()
            yield log, string_io


def test_basic_logging(capsys):
    """Test that basic logging works and includes expected fields"""
    log = configure_logger()
    log.info("Test message", test_key="test_value")

    log_output = capsys.readouterr()

    assert "Test message" in log_output.out
    assert "test_key=test_value" in log_output.out


def test_context_manager(capture_logs):
    """Test that the context manager binds and clears context"""
    log, output = capture_logs

    # Test context manager
    with log.context(request_id="abc123"):
        log.info("Within context")

    log.info("Outside context")

    log_output = output.getvalue()
    assert "Within context" in log_output
    assert "request_id" in log_output
    assert "abc123" in log_output
    assert "Outside context" in log_output
    # Verify context was cleared
    assert "request_id" not in log_output.split("Outside context")[1]


def test_local_and_clear(capture_logs):
    """Test that local binding and clearing work properly"""
    log, output = capture_logs

    # Test local binding
    log.local(user_id="user123")
    log.info("With local context")

    # Test clear
    log.clear()
    log.info("After clear")

    log_output = output.getvalue()
    assert "With local context" in log_output
    assert "user_id" in log_output
    assert "user123" in log_output
    assert "After clear" in log_output
    # Verify context was cleared
    assert "user_id" not in log_output.split("After clear")[1]


def test_json_logging(capture_prod_logs):
    """Test that JSON logging works in production environment"""
    log, output = capture_prod_logs

    log.info("JSON test", key="value")

    log_output = output.getvalue()
    # Parse the JSON output
    log_data = json.loads(log_output)

    assert log_data["event"] == "JSON test"
    assert log_data["key"] == "value"
    assert "timestamp" in log_data  # Check that timestamp was added


def test_path_prettifier(capture_logs):
    """Test that Path objects are correctly formatted"""
    log, output = capture_logs

    test_path = Path.cwd() / "test" / "file.txt"
    log.info("Path test", file_path=test_path)

    log_output = output.getvalue()
    # Path should be relative to CWD
    assert "PosixPath" not in log_output
    assert "test/file.txt" in log_output


def test_exception_formatting(capture_logs):
    """Test that exceptions are properly formatted"""
    log, output = capture_logs

    try:
        raise ValueError("Test exception")
    except ValueError:
        log.exception("An error occurred")

    log_output = output.getvalue()
    assert "An error occurred" in log_output
    assert "ValueError" in log_output
    assert "Test exception" in log_output


def test_log_level_filtering():
    """Test that log level filtering works as expected"""
    string_io = io.StringIO()

    with redirect_stdout(string_io):
        with (
            mock.patch(
                "structlog_config.stdlib_logging._get_log_level", return_value=20
            ),
            mock.patch(
                "structlog_config.environments.is_production", return_value=False
            ),
        ):
            log = configure_logger()

            # log.debug("Debug message")  # Should be filtered out
            log.info("Info message")  # Should appear

    log_output = string_io.getvalue()
    assert "Info message" in log_output
    # assert "Debug message" not in log_output


def test_logger_name(capture_logs):
    """Test that logger_name processor works"""
    log, output = capture_logs

    named_log = structlog.get_logger(logger_name="custom_logger")
    named_log.info("Named logger test")

    log_output = output.getvalue()
    assert "Named logger test" in log_output
    assert "custom_logger" in log_output


def test_nested_context(capture_logs):
    """Test that nested contexts work as expected"""
    log, output = capture_logs

    with log.context(outer="value"):
        log.info("Outer context")
        with log.context(inner="nested"):
            log.info("Nested context")
        log.info("Back to outer")

    log_output = output.getvalue()

    # Check outer context
    assert "Outer context" in log_output
    assert "outer=value" in log_output

    # Check nested context
    nested_part = log_output.split("Nested context")[0]
    assert "inner=nested" in nested_part
    assert "outer=value" in nested_part

    # Check back to outer
    outer_part = log_output.split("Back to outer")[0]
    assert "outer=value" in outer_part
    assert "inner" not in outer_part.split("Nested context")[1]
