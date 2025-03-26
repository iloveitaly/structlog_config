import os
import typing as t

from decouple import config


def python_environment() -> str:
    return t.cast(str, config("PYTHON_ENV", default="development", cast=str)).lower()


def is_testing():
    return python_environment() == "test"


def is_production():
    return python_environment() == "production"


def is_staging():
    return python_environment() == "staging"


def is_development():
    return python_environment() == "development"


def is_pytest():
    """
    PYTEST_CURRENT_TEST is set by pytest to indicate the current test being run
    """
    return "PYTEST_CURRENT_TEST" in os.environ
