import logging
import sys

import structlog

from .constants import LOG_LEVEL, PYTHONASYNCIODEBUG
from .environments import is_production, is_staging


def _get_log_level():
    return logging.getLevelNamesMapping()[LOG_LEVEL]


def reset_stdlib_logger(
    logger_name: str, default_structlog_handler, level_override=None
):
    std_logger = logging.getLogger(logger_name)
    std_logger.propagate = False
    std_logger.handlers = []
    std_logger.addHandler(default_structlog_handler)

    if level_override:
        std_logger.setLevel(level_override)


def redirect_stdlib_loggers():
    """
    Redirect all standard logging module loggers to use the structlog configuration.

    Inspired by: https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e
    """
    from structlog.stdlib import ProcessorFormatter

    level = _get_log_level()

    # Create a handler for the root logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # TODO I don't understand why we can't use a processor stack as-is here. Need to investigate further.

    # Use ProcessorFormatter to format log records using structlog processors
    from .__init__ import PROCESSORS

    formatter = ProcessorFormatter(
        processors=[
            # required to strip extra keys that the structlog stdlib bindings add in
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            PROCESSORS[-1]
            if not is_production() and not is_staging()
            # don't use ORJSON here, as the stdlib formatter chain expects a str not a bytes
            else structlog.processors.JSONRenderer(sort_keys=True),
        ],
        # processors unique to stdlib logging
        foreign_pre_chain=[
            # logger names are not supported when not using structlog.stdlib.LoggerFactory
            # https://github.com/hynek/structlog/issues/254
            structlog.stdlib.add_logger_name,
            # omit the renderer so we can implement our own
            *PROCESSORS[:-1],
        ],
    )
    handler.setFormatter(formatter)

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]  # Replace existing handlers with our handler

    # Disable propagation to avoid duplicate logs
    root_logger.propagate = True

    # TODO there is a JSON-like format that can be used to configure loggers instead :/
    std_logging_configuration = {
        "httpcore": {},
        "httpx": {
            "levels": {
                "INFO": "WARNING",
            }
        },
        "azure.core.pipeline.policies.http_logging_policy": {
            "levels": {
                "INFO": "WARNING",
            }
        },
    }
    """
    These loggers either:

    1. Are way too chatty by default
    2. Setup before our logging is initialized

    This configuration allows us to easily override various loggers as we add additional complexity to the application
    """

    # now, let's handle some loggers that are probably already initialized with a handler
    for logger_name, logger_config in std_logging_configuration.items():
        reset_stdlib_logger(
            logger_name,
            handler,
            logger_config.get("levels", {}).get(logging.getLevelName(level)),
        )

    # TODO do i need to setup exception overrides as well?
    # https://gist.github.com/nymous/f138c7f06062b7c43c060bf03759c29e#file-custom_logging-py-L114-L128
    if sys.excepthook != sys.__excepthook__:
        logging.getLogger(__name__).warning("sys.excepthook has been overridden.")


def silence_loud_loggers():
    # unless we are explicitly debugging asyncio, I don't want to hear from it
    if not PYTHONASYNCIODEBUG:
        logging.getLogger("asyncio").setLevel(logging.WARNING)

    # TODO httpcore, httpx, urlconnection, etc
