import time
import logging
import os
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("adhd.request")

DEBUG_REQUESTS = os.environ.get("DEBUG_REQUESTS", "").lower() in ("1", "true", "yes")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()

        if DEBUG_REQUESTS:
            body = await request.body()
            print(f"\n>>> {request.method} {request.url}", flush=True)
            print(f"Body: {body.decode('utf-8', errors='replace')}", flush=True)
            # Starlette consumes the body stream — patch it back so the route still reads it
            async def receive():
                return {"type": "http.request", "body": body}
            request._receive = receive

        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if DEBUG_REQUESTS:
            # Buffer response body so we can log it
            resp_body = b""
            async for chunk in response.body_iterator:
                resp_body += chunk
            print(f"<<< {response.status_code} {elapsed_ms:.1f}ms", flush=True)
            print(f"Body: {resp_body.decode('utf-8', errors='replace')}", flush=True)
            return Response(
                content=resp_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        logger.info(
            "%s %s %d %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
