from collections.abc import Awaitable, Callable
import json
import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from observability.tracing.context import init_trace_context

logger = logging.getLogger("observability.middleware")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 1. Extract IDs from headers or generate new ones
        correlation_id = request.headers.get("x-correlation-id") or request.headers.get(
            "X-Correlation-ID"
        )
        session_id = request.headers.get("x-session-id") or request.headers.get("X-Session-ID")

        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        if not session_id:
            # Fall back to query parameters if present, otherwise generate
            session_id = request.query_params.get("session_id") or str(uuid.uuid4())

        request_id = str(uuid.uuid4())
        workflow_id = str(uuid.uuid4())

        # 2. Try to parse doc_id from JSON request body safely (skip streaming endpoints to preserve ASGI body stream)
        doc_id = None
        content_type = request.headers.get("content-type", "")
        if (
            request.method == "POST"
            and "application/json" in content_type
            and not request.url.path.endswith("/stream-ask")
        ):
            try:
                body = await request.body()
                if body:
                    data = json.loads(body)
                    doc_id = data.get("doc_id")
            except Exception as e:
                logger.warning(f"Failed to parse doc_id from request body: {e}")

        # 3. Initialize trace context in contextvars
        init_trace_context(
            session_id=session_id,
            request_id=request_id,
            correlation_id=correlation_id,
            workflow_id=workflow_id,
            doc_id=doc_id,
        )

        # 4. Process the request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception(f"Request failed with unhandled exception: {e}")
            raise e

        # 5. Inject trace metadata headers in response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Session-ID"] = session_id
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Workflow-ID"] = workflow_id

        return response
