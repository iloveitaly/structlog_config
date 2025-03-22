import logging
from typing import Any, MutableMapping, TextIO

from structlog.typing import EventDict, ExcInfo


def simplify_activemodel_objects(
    logger: logging.Logger,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """
    Make the following transformations to the logs:

    - Convert keys ('object') whose value inherit from activemodel's BaseModel to object_id=str(object.id)
    - Convert TypeIDs to their string representation object=str(object)

    What's tricky about this method, and other structlog processors, is they are run *after* a response
    is returned to the user. So, they don't error out in tests and it doesn't impact users. They do show up in Sentry.
    """
    for key, value in list(event_dict.items()):
        if isinstance(value, BaseModel):

            def get_field_no_refresh(instance, field_name):
                """
                This was a hard-won little bit of code: in fastapi, this action happens *after* the
                db session dependency has finished, which means the session is closed.

                If a DB operation within the session causes the model to be marked as stale, then this will trigger
                a `sqlalchemy.orm.exc.DetachedInstanceError` error. This logic pulls the cached value from the object
                which is better for performance *and* avoids the error.
                """
                return str(object_state(instance).dict.get(field_name))

            # TODO this will break as soon as a model doesn't have `id` as pk
            event_dict[f"{key}_id"] = get_field_no_refresh(value, "id")
            del event_dict[key]

        elif isinstance(value, TypeID):
            event_dict[key] = str(value)

    return event_dict


def logger_name(logger: Any, method_name: Any, event_dict: EventDict) -> EventDict:
    """
    structlog does not have named loggers, so we roll our own

    >>> structlog.get_logger(logger_name="my_logger_name")
    """

    if logger_name := event_dict.pop("logger_name", None):
        # `logger` is a special key that structlog treats as the logger name
        # look at `structlog.stdlib.add_logger_name` for more information
        event_dict.setdefault("logger", logger_name)

    return event_dict


def pretty_traceback_exception_formatter(sio: TextIO, exc_info: ExcInfo) -> None:
    """
    By default, rich and then better-exceptions is used to render exceptions when a ConsoleRenderer is used.

    I prefer pretty-traceback, so I've added a custom processor to use it.

    https://github.com/hynek/structlog/blob/66e22d261bf493ad2084009ec97c51832fdbb0b9/src/structlog/dev.py#L412
    """

    # only available in dev
    from pretty_traceback.formatting import exc_to_traceback_str

    _, exc_value, traceback = exc_info
    formatted_exception = exc_to_traceback_str(exc_value, traceback, color=not NO_COLOR)
    sio.write("\n" + formatted_exception)
