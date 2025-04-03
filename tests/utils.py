import os
from contextlib import contextmanager
from typing import Dict


@contextmanager
def temp_env_var(env_vars: Dict[str, str]):
    """
    Temporarily set environment variables and restore them afterward.

    Args:
        env_vars: A dict mapping variable names to values

    Example:
        # Set multiple environment variables temporarily
        with temp_env_var({"DEBUG": "1", "LOG_LEVEL": "DEBUG"}):
            # Code that needs multiple env vars
    """
    # Store original state
    original_values = {}
    for name in env_vars:
        original_values[name] = (name in os.environ, os.environ.get(name))

    try:
        # Set new values
        for name, value in env_vars.items():
            os.environ[name] = value
        yield
    finally:
        # Restore original state
        for name, (existed, value) in original_values.items():
            if existed:
                os.environ[name] = value
            else:
                os.environ.pop(name, None)
