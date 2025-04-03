import os

from decouple import config

PYTHON_LOG_PATH = config("PYTHON_LOG_PATH", default=None)
PYTHONASYNCIODEBUG = config("PYTHONASYNCIODEBUG", default=False, cast=bool)

NO_COLOR = "NO_COLOR" in os.environ
"support NO_COLOR standard https://no-color.org"
