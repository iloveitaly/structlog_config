"""
Warning setup functionality to redirect Python warnings to structlog.
"""

import warnings
from typing import Any, TextIO

import structlog

_original_warnings_showwarning: Any = None


def _showwarning(
    message: Warning | str,
    category: type[Warning],
    filename: str,
    lineno: int,
    file: TextIO | None = None,
    line: str | None = None,
) -> Any:
    """
    Redirects warnings to structlog so they appear in task logs etc.

    Implementation of showwarnings which redirects to logging, which will first
    check to see if the file parameter is None. If a file is specified, it will
    delegate to the original warnings implementation of showwarning. Otherwise,
    it will call warnings.formatwarning and will log the resulting string to a
    warnings logger named "py.warnings" with level logging.WARNING.
    """
    if file is not None:
        if _original_warnings_showwarning is not None:
            _original_warnings_showwarning(
                message, category, filename, lineno, file, line
            )
    else:
        log = structlog.get_logger(logger_name="py.warnings")
        log.warning(
            str(message), category=category.__name__, filename=filename, lineno=lineno
        )


def redirect_showwarnings():
    """
    Redirect Python warnings to use structlog for logging.
    """
    global _original_warnings_showwarning

    if _original_warnings_showwarning is None:
        _original_warnings_showwarning = warnings.showwarning
        # Capture warnings and show them via structlog
        warnings.showwarning = _showwarning
