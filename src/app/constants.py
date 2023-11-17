import os

APP_HOST = os.environ.get("APP_HOST", "0.0.0.0")
APP_PORT = os.environ.get("APP_PORT", 8000)

REDIS_HOST = os.environ.get("REDIS_HOST", "")
REDIS_PORT = os.environ.get("REDIS_PORT", 6379)

ENABLE_METRICS = os.environ.get("ENABLE_METRICS", "True").lower() == "true"

ENABLE_TRACING = os.environ.get("ENABLE_TRACING", "True").lower() == "true"
OTEL_EXPORTER_OTLP_ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "otel-collector.monitoring:4318")
OTEL_SERVICE_NAME = os.environ.get("OTEL_SERVICE_NAME", "fastapi-observability-example")


ENABLE_PROFILING = os.environ.get("ENABLE_PROFILING", "True").lower() == "true"
PYROSCOPE_ENDPOINT = os.environ.get("PYROSCOPE_ENDPOINT", "http://pyroscope.monitoring:4040")
APP_NAME = os.environ.get("APP_NAME", "fastapi-observability-example")
