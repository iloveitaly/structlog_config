# Structlog Configuration

Logging is really important:

* High performance JSON logging in production
* All loggers, even plugin or system loggers, should route through the same formatter
* Structured logging everywhere
* Ability to easily set thread-local log context

## Stdib Log Management

Note that `{LOGGER_NAME}` is the name of the system logger assigned via `logging.getLogger(__name__)`:

* `OPENAI_LOG_LEVEL`
* `OPENAI_LOG_PATH`. Ignored in production.

## Related Projects

* https://github.com/underyx/structlog-pretty

## References

- https://github.com/replicate/cog/blob/2e57549e18e044982bd100e286a1929f50880383/python/cog/logging.py#L20
- https://github.com/apache/airflow/blob/4280b83977cd5a53c2b24143f3c9a6a63e298acc/task_sdk/src/airflow/sdk/log.py#L187
- https://github.com/kiwicom/structlog-sentry
- https://github.com/jeremyh/datacube-explorer/blob/b289b0cde0973a38a9d50233fe0fff00e8eb2c8e/cubedash/logs.py#L40C21-L40C42
