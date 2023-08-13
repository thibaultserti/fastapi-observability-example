import os

APP_NAME = os.environ.get("APP_NAME", "app-a")
EXPOSE_PORT = os.environ.get("EXPOSE_PORT", 8000)
OTLP_GRPC_ENDPOINT = os.environ.get("OTLP_GRPC_ENDPOINT", "http://tempo.ayanides.cloud")
PYROSCOPE_ENDPOINT = os.environ.get("PYROSCOPE_ENDPOINT", "http://phlare.ayanides.cloud")

TARGET_ONE_HOST = os.environ.get("TARGET_ONE_HOST", "app-b")
TARGET_TWO_HOST = os.environ.get("TARGET_TWO_HOST", "app-c")
