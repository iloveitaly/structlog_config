"""Test structlog_config."""

from importlib.resources import files

import structlog_config


def test_import() -> None:
    """Test that the  can be imported."""
    assert isinstance(structlog_config.__name__, str)


def test_py_typed_marker_is_installed() -> None:
    """PEP 561 marker so mypy uses inline types instead of ignore_missing_imports."""
    marker = files("structlog_config").joinpath("py.typed")
    assert marker.is_file()
