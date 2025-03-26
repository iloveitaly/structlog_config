import os

from decouple import config

LOG_LEVEL = config("LOG_LEVEL", default="INFO", cast=str).upper()
PYTHON_LOG_PATH = config("PYTHON_LOG_PATH", default=None)
PYTHONASYNCIODEBUG = config("PYTHONASYNCIODEBUG", default=False, cast=bool)
NO_COLOR = "NO_COLOR" in os.environ
