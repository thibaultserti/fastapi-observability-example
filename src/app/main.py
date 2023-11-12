import logging
import random

import httpx
import pyroscope
import uvicorn

from constants import (
    APP_HOST,
    APP_PORT,
    ENABLE_METRICS,
    ENABLE_TRACING,
    ENABLE_PROFILING,
    PYROSCOPE_ENDPOINT,
    APP_NAME,
    OTEL_EXPORTER_OTLP_ENDPOINT,
    OTEL_SERVICE_NAME,
    REDIS_HOST,
    REDIS_PORT,
)
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.trace.status import Status, StatusCode
from prometheus_fastapi_instrumentator import Instrumentator
from redis import Redis


app = FastAPI()

redis = Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
tracer_provider = trace.get_tracer_provider()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if ENABLE_METRICS:
    Instrumentator().instrument(app).expose(app, include_in_schema=False)

if ENABLE_PROFILING:
    pyroscope.configure(
        application_name    = APP_NAME,
        server_address      = PYROSCOPE_ENDPOINT,
        sample_rate         = 100,
        detect_subprocesses = False,
        oncpu               = False,
        gil_only            = False,
        tags                = {
        }
    )

if ENABLE_TRACING:
    resource = Resource(attributes={
        SERVICE_NAME: OTEL_SERVICE_NAME
    })

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{OTEL_EXPORTER_OTLP_ENDPOINT}/v1/traces"))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider, excluded_urls="/,/metrics")
    RedisInstrumentor().instrument(tracer_provider=tracer_provider)

@app.get("/", include_in_schema=False)
async def health_check():
    with pyroscope.tag_wrapper({ "endpoint": "/" }):
        return JSONResponse(content={"status": "OK"})

@app.get("/read/{key}")
async def read_from_redis(request: Request, key: str):
    context = TraceContextTextMapPropagator().extract(carrier=request.headers)
    with tracer_provider.get_tracer(__name__).start_as_current_span("read_from_redis", context=context):
        with pyroscope.tag_wrapper({ "endpoint": "/read" }):
            value = redis.get(key)
            if value is not None:
                return JSONResponse(content={"key": key, "value": value.decode("utf-8")})
            else:
                raise HTTPException(status_code=404, detail="Key not found in Redis")

@app.post("/write/{key}")
async def write_to_redis(request: Request, key: str, value: str, expiration: int):
    context = TraceContextTextMapPropagator().extract(carrier=request.headers)
    with tracer_provider.get_tracer(__name__).start_as_current_span("write_to_redis", context=context):
        with pyroscope.tag_wrapper({ "endpoint": "/write" }):
            redis.setex(key, expiration, value)
            return JSONResponse(content={"message": "Data written to Redis"})

@app.get("/call")
async def call_external_api(request: Request):
    context = TraceContextTextMapPropagator().extract(carrier=request.headers)
    with tracer_provider.get_tracer(__name__).start_as_current_span("call_external_api", context=context):
        with pyroscope.tag_wrapper({ "endpoint": "/call" }):
            async with httpx.AsyncClient() as client:
                response = await client.get("https://restcountries.com/v3.1/name/france?fullText=true")
                return JSONResponse(content={"status_code": response.status_code, "content": response.text})


@app.get("/exception")
async def exception(request: Request):
    context = TraceContextTextMapPropagator().extract(carrier=request.headers)
    with tracer_provider.get_tracer(__name__).start_as_current_span("exception", context=context):
        with pyroscope.tag_wrapper({ "endpoint": "/exception" }):
            try:
                raise ValueError("sadness")
            except Exception as ex:
                logger.error(ex, exc_info=True)
                span = trace.get_current_span()

                # generate random number
                seconds = random.uniform(0, 30)

                # record_exception converts the exception into a span event.
                exception = IOError("Failed at " + str(seconds))
                span.record_exception(exception)
                span.set_attributes({'error': True})
                # Update the span status to failed.
                span.set_status(Status(StatusCode.ERROR, "internal error"))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error")

if __name__ == "__main__":
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
