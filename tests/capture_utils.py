import io
import sys
from contextlib import contextmanager


class CaptureStdout:
    """Context manager that captures stdout and provides access to the captured content."""

    def __init__(self):
        self._stringio = io.StringIO()
        self._original_stdout = None

    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = self._stringio
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self._original_stdout

    def getvalue(self):
        """Get the current captured content without ending the capture."""
        return self._stringio.getvalue()

    def clear(self):
        """Clear captured content but continue capturing."""
        self._stringio.seek(0)
        self._stringio.truncate()


@contextmanager
def capture_logger_output():
    """
    Context manager to capture structlog output.

    Returns a tuple of (capture_object, output_file) where output_file can be passed
    to configure_logger and capture_object can be used to get the captured content.

    Example:
        with capture_logger_output() as (capture, output_file):
            log = configure_logger(logger_factory=structlog.PrintLoggerFactory(file=output_file))
            log.info("Hello")
            assert "Hello" in capture.getvalue()
    """
    capture = CaptureStdout()
    file = io.StringIO()

    try:
        with capture:
            yield capture, file
    finally:
        # Any cleanup if needed
        pass
