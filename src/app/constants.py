import os

APP_NAME = os.environ.get("APP_NAME", "fastapi-observability-example-a")
EXPOSE_PORT = os.environ.get("EXPOSE_PORT", 8000)
OTLP_GRPC_ENDPOINT = os.environ.get("OTLP_GRPC_ENDPOINT", "http://localhost:4317")
PYROSCOPE_ENDPOINT = os.environ.get("PYROSCOPE_ENDPOINT", "http://localhost:4040")

TARGET_ONE_HOST = os.environ.get("TARGET_ONE_HOST", "app-b")
TARGET_TWO_HOST = os.environ.get("TARGET_TWO_HOST", "app-c")
