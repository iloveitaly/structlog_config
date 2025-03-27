import logging

import orjson
import structlog
import structlog.dev
from structlog.processors import ExceptionRenderer
from structlog.tracebacks import ExceptionDictTransformer

from structlog_config.formatters import (
    PathPrettifier,
    add_fastapi_context,
    logger_name,
    pretty_traceback_exception_formatter,
    simplify_activemodel_objects,
)

from . import packages
from .constants import LOG_LEVEL, NO_COLOR, PYTHON_LOG_PATH
from .environments import is_production, is_pytest, is_staging
from .stdlib_logging import (
    _get_log_level,
    redirect_stdlib_loggers,
    silence_loud_loggers,
)
from .warnings import redirect_showwarnings

logging.basicConfig(
    level=LOG_LEVEL,
)

package_logger = logging.getLogger(__name__)


def log_processors_for_environment() -> list[structlog.types.Processor]:
    if is_production() or is_staging():

        def orjson_dumps_sorted(value, *args, **kwargs):
            "sort_keys=True is not supported, so we do it manually"
            # kwargs includes a default fallback json formatter
            return orjson.dumps(
                # starlette-context includes non-string keys (enums)
                value,
                option=orjson.OPT_SORT_KEYS | orjson.OPT_NON_STR_KEYS,
                **kwargs,
            )

        return [
            # add exc_info=True to a log and get a full stack trace attached to it
            structlog.processors.format_exc_info,
            # simple, short exception rendering in prod since sentry is in place
            # https://www.structlog.org/en/stable/exceptions.html this is a customized version of dict_tracebacks
            ExceptionRenderer(
                ExceptionDictTransformer(
                    show_locals=False,
                    use_rich=False,
                    # number of frames is completely arbitrary
                    max_frames=5,
                    # TODO `suppress`?
                )
            ),
            # in prod, we want logs to be rendered as JSON payloads
            structlog.processors.JSONRenderer(serializer=orjson_dumps_sorted),
        ]

    return [
        structlog.dev.ConsoleRenderer(
            colors=not NO_COLOR,
            exception_formatter=pretty_traceback_exception_formatter
            if packages.pretty_traceback
            else structlog.dev.default_exception_formatter,
        )
    ]


def get_default_processors() -> list[structlog.types.Processor]:
    """
    Return the default list of processors for structlog configuration.
    """
    processors = [
        # although this is stdlib, it's needed, although I'm not sure entirely why
        structlog.stdlib.add_log_level,
        structlog.contextvars.merge_contextvars,
        logger_name,
        add_fastapi_context if packages.starlette_context else None,
        simplify_activemodel_objects
        if packages.activemodel and packages.typeid
        else None,
        PathPrettifier(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        # add `stack_info=True` to a log and get a `stack` attached to the log
        structlog.processors.StackInfoRenderer(),
        *log_processors_for_environment(),
    ]

    return [processor for processor in processors if processor is not None]


# Use the function to get the processors
PROCESSORS: list[structlog.types.Processor] = get_default_processors()


def _logger_factory():
    """
    Allow dev users to redirect logs to a file using PYTHON_LOG_PATH

    In production, optimized for speed (https://www.structlog.org/en/stable/performance.html)
    """

    if is_production() or is_staging():
        return structlog.BytesLoggerFactory()

    if PYTHON_LOG_PATH:
        python_log = open(PYTHON_LOG_PATH, "a", encoding="utf-8")
        return structlog.PrintLoggerFactory(file=python_log)

    else:
        return structlog.PrintLoggerFactory()


def configure_logger():
    """
    Create a struct logger with some special additions:

    >>> with log.context(key=value):
    >>>    log.info("some message")

    >>> log.local(key=value)
    >>> log.info("some message")
    >>> log.clear()
    """

    redirect_stdlib_loggers()
    redirect_showwarnings()
    silence_loud_loggers()

    structlog.configure(
        # Don't cache the loggers during tests, it make it hard to capture them
        cache_logger_on_first_use=not is_pytest(),
        wrapper_class=structlog.make_filtering_bound_logger(_get_log_level()),
        # structlog.stdlib.LoggerFactory is the default, which supports `structlog.stdlib.add_logger_name`
        logger_factory=_logger_factory(),
        processors=PROCESSORS,
    )

    log = structlog.get_logger()

    # context manager to auto-clear context
    log.context = structlog.contextvars.bound_contextvars
    # set thread-local context
    log.local = structlog.contextvars.bind_contextvars
    # clear thread-local context
    log.clear = structlog.contextvars.clear_contextvars

    return log
