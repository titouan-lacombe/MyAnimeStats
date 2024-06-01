# Setup logging before anything else
from os import getenv
import logging
logging.basicConfig(
    level=getenv("LOG_LEVEL", "INFO"),
    format="[%(asctime)s] %(levelname)s-%(name)s: %(message)s"
)

# Patch verbose loggers
logging.getLogger("inotify").setLevel(logging.WARNING)

import time
from fastapi import FastAPI, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .api import api

logger = logging.getLogger("access")

app = FastAPI()

class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        t = time.time()
        response = await call_next(request)
        dt = time.time() - t

        logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} in {dt * 1000:.2f} ms"
        )

        return response

app.add_middleware(AccessLogMiddleware)

@app.get("/health")
async def home():
    return Response(content="OK")

app.include_router(api)
