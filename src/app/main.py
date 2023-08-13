import logging
import random
import time
from typing import Optional, Dict

import httpx
import uvicorn
from fastapi import FastAPI, Response
from opentelemetry.propagate import inject

from utils import PrometheusMiddleware, metrics, setting_otlp
import constants



app = FastAPI()

# Setting metrics middleware
app.add_middleware(PrometheusMiddleware, app_name=constants.APP_NAME)
app.add_route("/metrics", metrics)

# Setting OpenTelemetry exporter
setting_otlp(app, constants.APP_NAME, constants.OTLP_GRPC_ENDPOINT)


class EndpointFilter(logging.Filter):
    # Uvicorn endpoint access log filter
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /metrics") == -1


# Filter out /endpoint
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())


@app.get("/")
async def read_root():
    logging.error("Hello World")
    return {"Hello": "World"}


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Optional[str] = None):
    logging.error("items")
    return {"item_id": item_id, "q": q}


@app.get("/io_task")
async def io_task():
    time.sleep(1)
    logging.error("io task")
    return "IO bound task finish!"


@app.get("/cpu_task")
async def cpu_task():
    for i in range(1000):
        _ = i*i*i
    logging.error("cpu task")
    return "CPU bound task finish!"


@app.get("/random_status")
async def random_status(response: Response):
    response.status_code = random.choice([200, 200, 300, 400, 500])
    logging.error("random status")
    return {"path": "/random_status"}


@app.get("/random_sleep")
async def random_sleep(response: Response):
    time.sleep(random.randint(0, 5))
    logging.error("random sleep")
    return {"path": "/random_sleep"}


@app.get("/error_test")
async def error_test(response: Response):
    logging.error("got error!!!!")
    raise ValueError("value error")


@app.get("/chain")
async def chain(response: Response):

    headers: Dict[str, str] = {}
    inject(headers)  # inject trace info to header
    logging.critical(headers)

    async with httpx.AsyncClient() as client:
        await client.get("http://localhost:8000/", headers=headers,)
    async with httpx.AsyncClient() as client:
        await client.get(f"http://{constants.TARGET_ONE_HOST}:8000/io_task", headers=headers,)
    async with httpx.AsyncClient() as client:
        await client.get(f"http://{constants.TARGET_TWO_HOST}:8000/cpu_task", headers=headers,)
    logging.info("Chain Finished")
    return {"path": "/chain"}

if __name__ == "__main__":
    # update uvicorn access logger format
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s"
    uvicorn.run(app, host="0.0.0.0", port=constants.EXPOSE_PORT, log_config=log_config)